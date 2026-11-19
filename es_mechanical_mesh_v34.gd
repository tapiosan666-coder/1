extends RefCounted
## Compact machine meshes in local coordinates. All flights of the same rise and run
## share the rail, side panels and comb plates; the moving tread meshes are shared sitewide.
const TRACK_HALF_WIDTH := .655
const CASE_HALF_WIDTH := .775
const COMB_DEPTH := .28
const RIB_COUNT := 32
const NEWEL_FLAT := 1.01
const RETURN_RADIUS := .40
const GRIP_HEIGHT := 1.02
const PANE_BASE := .323

static func height(s: float, rise: float, run: float) -> float:
	return rise * clampf(s / run + .5, 0.0, 1.0)

static func face(st: SurfaceTool, points: Array[Vector3], uvs: Array[Vector2]) -> void:
	for index: int in [0, 2, 1, 0, 3, 2]:
		st.set_uv(uvs[index])
		st.add_vertex(points[index])

static func basic_face(st: SurfaceTool, points: Array[Vector3]) -> void:
	face(st, points, [Vector2.ZERO, Vector2.RIGHT, Vector2.ONE, Vector2.DOWN])

static func box(st: SurfaceTool, center: Vector3, size: Vector3) -> void:
	var half := size * .5
	var a := center + Vector3(-half.x, -half.y, -half.z)
	var b := center + Vector3(half.x, -half.y, -half.z)
	var c := center + Vector3(half.x, half.y, -half.z)
	var d := center + Vector3(-half.x, half.y, -half.z)
	var e := center + Vector3(-half.x, -half.y, half.z)
	var f := center + Vector3(half.x, -half.y, half.z)
	var g := center + Vector3(half.x, half.y, half.z)
	var h := center + Vector3(-half.x, half.y, half.z)
	# The SurfaceTool remains entirely unindexed until add_surface() completes.
	basic_face(st, [a, d, c, b])
	basic_face(st, [e, f, g, h])
	basic_face(st, [a, e, h, d])
	basic_face(st, [b, c, g, f])
	basic_face(st, [d, h, g, c])
	basic_face(st, [a, b, f, e])

static func material(color: Color, metal: float, roughness: float) -> StandardMaterial3D:
	var result := StandardMaterial3D.new()
	result.albedo_color = color
	result.metallic = metal
	result.roughness = roughness
	result.cull_mode = BaseMaterial3D.CULL_DISABLED
	return result

static func add_surface(st: SurfaceTool, mesh: ArrayMesh, mat: Material) -> void:
	st.set_material(mat)
	st.generate_normals()
	st.index()
	st.commit(mesh)

static func tread(antislip: Material, yellow: Material) -> ArrayMesh:
	var mesh := ArrayMesh.new()
	var tread_surface := SurfaceTool.new()
	tread_surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	box(tread_surface, Vector3(0., -.025, 0.), Vector3(1.30, .042, .396))
	box(tread_surface, Vector3(0., -.101, -.19), Vector3(1.30, .19, .014))
	# Continuous ridged extrusion across the tread. The two inclined faces of each
	# rib give real specular highlights, using four triangles instead of a closed box.
	var pitch: float = 1.254 / RIB_COUNT
	for i: int in RIB_COUNT:
		var x: float = -.627 + (i + .5) * pitch
		for direction: float in [-1., 1.]:
			var side: float = x + .0085 * direction
			var points: Array[Vector3] = [Vector3(side, -.003, -.192), Vector3(side, -.003, .192), Vector3(x, .0038, .192), Vector3(x, .0038, -.192)]
			if direction > 0.:
				points.reverse()
			basic_face(tread_surface, points)
	add_surface(tread_surface, mesh, antislip)
	var trim := SurfaceTool.new()
	trim.begin(Mesh.PRIMITIVE_TRIANGLES)
	basic_face(trim, [Vector3(-.65, .006, -.198), Vector3(.65, .006, -.198), Vector3(.65, .006, -.18), Vector3(-.65, .006, -.18)])
	for x: float in [-.642, .642]:
		basic_face(trim, [Vector3(x - .006, .006, -.18), Vector3(x + .006, .006, -.18), Vector3(x + .006, .006, .196), Vector3(x - .006, .006, .196)])
	add_surface(trim, mesh, yellow)
	return mesh

# Ease the handhold through the horizontal/inclined transitions. The authored
# floor and tread transport retain their exact levels at both comb plates.
static func eased_positive(t: float) -> float:
	const EASE := .48
	if t <= -EASE:
		return 0.
	if t >= EASE:
		return t
	return (t + EASE) * (t + EASE) / (4.0 * EASE)

static func handhold_height(s: float, rise: float, run: float) -> float:
	return GRIP_HEIGHT + rise / run * (eased_positive(s + run * .5) - eased_positive(s - run * .5))

static func rail(rise: float, run: float) -> ArrayMesh:
	var half := run * .5
	var rail_end := half + NEWEL_FLAT
	var upper: Array[Vector2] = [Vector2(-rail_end, GRIP_HEIGHT)]
	for transition: float in [-half, half]:
		for sample_index: int in 7:
			var s := transition + lerpf(-.48, .48, sample_index / 6.0)
			upper.append(Vector2(s, handhold_height(s, rise, run)))
	upper.append(Vector2(rail_end, rise + GRIP_HEIGHT))
	var section: Array[Vector2] = upper.duplicate()
	# The lower return is hidden inside the stationary skirt, as on a real machine.
	for i: int in range(1, 13):
		var a := PI * float(i) / 12
		section.append(Vector2(rail_end + sin(a) * RETURN_RADIUS, GRIP_HEIGHT + rise - RETURN_RADIUS + cos(a) * RETURN_RADIUS))
	for i: int in range(upper.size() - 2, -1, -1):
		section.append(upper[i] - Vector2(0., 2. * RETURN_RADIUS))
	for i: int in range(1, 12):
		var a := PI * float(i) / 12
		section.append(Vector2(-rail_end - sin(a) * RETURN_RADIUS, GRIP_HEIGHT - RETURN_RADIUS - cos(a) * RETURN_RADIUS))
	var full_loop := section.duplicate()
	full_loop.append(section[0])
	var cumulative: PackedFloat32Array = [0.]
	for i: int in range(1, full_loop.size()):
		cumulative.append(cumulative[i - 1] + full_loop[i - 1].distance_to(full_loop[i]))
	var sides := 10
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var uv := PackedVector2Array()
	var indices := PackedInt32Array()
	for side: float in [-.94, .94]:
		var base := vertices.size()
		for i: int in full_loop.size():
			var ring: int = i % section.size()
			var tangent: Vector2 = (section[(ring + 1) % section.size()] - section[ring]).normalized() + (section[ring] - section[posmod(ring - 1, section.size())]).normalized()
			tangent = tangent.normalized()
			var radial := Vector3(0., tangent.x, -tangent.y)
			for j: int in range(sides + 1):
				var angle := TAU * float(j) / sides
				var cos_angle := cos(angle)
				var sin_angle := sin(angle)
				var offset := Vector3.RIGHT * cos_angle * .052 + radial * sin_angle * .035
				vertices.append(Vector3(side, full_loop[i].y, full_loop[i].x) + offset)
				normals.append((Vector3.RIGHT * cos_angle / .052 + radial * sin_angle / .035).normalized())
				uv.append(Vector2(float(j) / sides, cumulative[i]))
		for i: int in range(full_loop.size() - 1):
			for j: int in sides:
				var a := base + i * (sides + 1) + j
				var b := a + sides + 1
				indices.append_array(PackedInt32Array([a, b + 1, b, a, a + 1, b + 1]))
	var arrays: Array = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_TEX_UV] = uv
	arrays[Mesh.ARRAY_INDEX] = indices
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return mesh

# One transparent face per pane, rendered from both sides. A concealed shoe
# supports the lower edge. Gaps between the individual panes are 8 mm.
static func glazing_polygon(st: SurfaceTool, side: float, contour: PackedVector2Array) -> void:
	var indices := Geometry2D.triangulate_polygon(contour)
	for i: int in indices:
		var point := contour[i]
		st.set_normal(Vector3.RIGHT * side)
		st.set_uv(point)
		st.add_vertex(Vector3(side * .94, point.y, point.x))

static func glass_balustrades(mesh: ArrayMesh, rise: float, run: float, glass: Material) -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	st.set_material(glass)
	var half := run * .5
	var pane_count := ceili(run / 1.85)
	for side: float in [-1., 1.]:
		for i: int in pane_count:
			var a := lerpf(-half, half, float(i) / pane_count) + .004
			var b := lerpf(-half, half, float(i + 1) / pane_count) - .004
			var contour := PackedVector2Array([Vector2(a, height(a,rise,run) + PANE_BASE), Vector2(b, height(b,rise,run) + PANE_BASE)])
			for j: int in 6:
				var z := lerpf(b, a, j / 5.)
				contour.append(Vector2(z, handhold_height(z,rise,run) - .013))
			glazing_polygon(st,side,contour)
		for end_sign: float in [-1., 1.]:
			var level := rise if end_sign > 0. else 0.
			var root_z := end_sign * (half + .004)
			var end_z := end_sign * (half + NEWEL_FLAT)
			var contour := PackedVector2Array([Vector2(root_z,level + PANE_BASE)])
			for j: int in 5:
				var z := lerpf(root_z, end_z, j / 4.)
				contour.append(Vector2(z, handhold_height(z,rise,run) - .015))
			var inner_radius := RETURN_RADIUS - .022
			for j: int in range(1, 16):
				var angle := deg_to_rad(140.) * j / 15.
				contour.append(Vector2(end_z + end_sign * inner_radius * sin(angle), level + GRIP_HEIGHT - RETURN_RADIUS + inner_radius * cos(angle)))
			contour.append(Vector2(end_z + end_sign * .20, level + PANE_BASE))
			glazing_polygon(st,side,contour)
	st.index()
	st.commit(mesh)

static func machine_case(rise: float, run: float, brushed: Material, landing: Material, accent: Material, glass: Material) -> ArrayMesh:
	var half := run * .5
	var end := half + 1.45
	var knots: Array[float] = [-end, -half, half, end]
	var mesh := ArrayMesh.new()
	var metal := SurfaceTool.new()
	metal.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i: int in range(knots.size() - 1):
		var a := knots[i]
		var b := knots[i + 1]
		var ya := height(a, rise, run)
		var yb := height(b, rise, run)
		basic_face(metal, [Vector3(-CASE_HALF_WIDTH, ya - .84, a), Vector3(CASE_HALF_WIDTH, ya - .84, a), Vector3(CASE_HALF_WIDTH, yb - .84, b), Vector3(-CASE_HALF_WIDTH, yb - .84, b)])
		for side: float in [-1., 1.]:
			var edge := side * CASE_HALF_WIDTH
			basic_face(metal, [Vector3(edge, ya - .84, a), Vector3(edge, yb - .84, b), Vector3(edge, yb - .043, b), Vector3(edge, ya - .043, a)])
			# The deck slopes up from the inner anti-entrapment skirt to the glass
			# shoe, then folds down along the outer cheek. The rubber return runs
			# inside that channel, with no second black belt visible from the stair.
			var profile := PackedVector2Array([Vector2(.735,-.12),Vector2(.735,.238),Vector2(.76,.26),
				Vector2(.91,.31),Vector2(.924,PANE_BASE),Vector2(.955,PANE_BASE),Vector2(.98,.292),
				Vector2(.98,-.47),Vector2(.765,-.57)])
			for j: int in range(profile.size()-1):
				var p := profile[j]
				var q := profile[j+1]
				basic_face(metal,[Vector3(side*p.x,ya+p.y,a),Vector3(side*p.x,yb+p.y,b),
					Vector3(side*q.x,yb+q.y,b),Vector3(side*q.x,ya+q.y,a)])
			if i == 0 or i == knots.size()-2:
				var level := ya if i == 0 else yb
				var z := a if i == 0 else b
				for j: int in Geometry2D.triangulate_polygon(profile):
					var p := profile[j]
					metal.set_uv(p)
					metal.add_vertex(Vector3(side*p.x,level+p.y,z))
	for s: float in [-end, end]:
		var y := height(s, rise, run)
		basic_face(metal, [Vector3(-CASE_HALF_WIDTH, y - .84, s), Vector3(CASE_HALF_WIDTH, y - .84, s), Vector3(CASE_HALF_WIDTH, y - .043, s), Vector3(-CASE_HALF_WIDTH, y - .043, s)])
	add_surface(metal, mesh, brushed)
	var plates := SurfaceTool.new()
	plates.begin(Mesh.PRIMITIVE_TRIANGLES)
	var comb := SurfaceTool.new()
	comb.begin(Mesh.PRIMITIVE_TRIANGLES)
	for side: float in [-1., 1.]:
		var y := rise if side > 0. else 0.
		var plate_center: float = side * (end - COMB_DEPTH * .5)
		box(plates, Vector3(0., y - .012, plate_center), Vector3(1.46, .022, COMB_DEPTH))
		# Precisely spaced tooth fingers conceal the joint without covering the yellow tread lip.
		var comb_s: float = side * (end - COMB_DEPTH - .04)
		for i: int in RIB_COUNT:
			var x: float = -.627 + (i + .5) * (1.254 / RIB_COUNT)
			box(comb, Vector3(x, y + .006, comb_s), Vector3(.015, .012, .094))
	add_surface(plates, mesh, landing)
	add_surface(comb, mesh, accent)
	glass_balustrades(mesh, rise, run, glass)
	return mesh

static func housing_collision(rise: float, run: float) -> ConcavePolygonShape3D:
	# Preserve the original truss guard volume. Independently collidable baked
	# support, landings and opening barriers remain in their proven locations.
	var half := run * .5
	var end := half + 1.45
	var knots: Array[float] = [-end, -half, half, end]
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i: int in range(knots.size() - 1):
		var a := knots[i]
		var b := knots[i + 1]
		var ya := height(a, rise, run)
		var yb := height(b, rise, run)
		for side: float in [-1., 1.]:
			var x := side * .77
			basic_face(st, [Vector3(x, ya - .84, a), Vector3(x, yb - .84, b), Vector3(x, yb - .025, b), Vector3(x, ya - .025, a)])
		basic_face(st, [Vector3(-.77, ya - .84, a), Vector3(.77, ya - .84, a), Vector3(.77, yb - .84, b), Vector3(-.77, yb - .84, b)])
	for s: float in [-end, end]:
		var y := height(s, rise, run)
		basic_face(st, [Vector3(-.77, y - .84, s), Vector3(.77, y - .84, s), Vector3(.77, y - .025, s), Vector3(-.77, y - .025, s)])
	var shape := st.commit().create_trimesh_shape()
	shape.backface_collision = true
	return shape
