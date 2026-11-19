extends SceneTree
## Rebuild the cell-specific wall resources without repacking the prepared scene.
## Run from v35 and pass -- --original=<unmodified v34 project root>.
const SOURCE_MESH := "res://assets/v30/world/meshes/clipped_637.res"
const SOURCE_FINISH := "res://assets/v30/world/meshes/f991970bd773c6de5098f546ef6a057aefb5b0a4ba151623334b6129d0346305.res"
# The m1045 coat groups its faces by material and centroid. The same seam
# crosses the aperture in both the local finish group and its north neighbor.
const SOURCE_FINISH_NEIGHBOR := "res://assets/v30/world/meshes/4fcb7403970c18747111ee1a31bbe0f9c172613ea0dfd5ad2ce84d85d5c2d936.res"
const SOURCE_OCCLUSION := "res://assets/v30/occlusion/shell_-9_6_-2.res"
const SOURCE_SHAPE := "res://assets/v30/world/shapes/world3540.res"
const WEST := 305.68
const EAST := 305.92
const SOUTH := -56.35
const NORTH := -59.65
const Y_TOP := 3.18

func _initialize() -> void:
	call_deferred("run")

func targeted(triangle: Array) -> bool:
	var a: Vector3 = triangle[0].p
	var b: Vector3 = triangle[1].p
	var c: Vector3 = triangle[2].p
	if absf(a.x-WEST) > .005 and absf(a.x-EAST) > .005:
		return false
	if absf(a.x-b.x) > .005 or absf(a.x-c.x) > .005:
		return false
	var lowest := a.min(b).min(c)
	var highest := a.max(b).max(c)
	return lowest.y >= -.005 and highest.y <= 5.15 		and lowest.z < SOUTH and highest.z > NORTH

func split_triangle(triangle: Array) -> Array:
	var left := clip(triangle, 2, NORTH, false)
	var right := clip(triangle, 2, SOUTH, true)
	var center := clip(clip(triangle, 2, NORTH, true), 2, SOUTH, false)
	var lintel := clip(center, 1, Y_TOP, true)
	var result: Array = []
	for poly: Array in [left,right,lintel]:
		for i: int in range(1,poly.size()-1):
			result.append_array([poly[0],poly[i],poly[i+1]])
	return result

func clip(poly: Array, axis: int, edge: float, keep_above: bool) -> Array:
	var result: Array = []
	for i: int in poly.size():
		var a: Dictionary = poly[i]
		var b: Dictionary = poly[(i+1)%poly.size()]
		var pa: Vector3 = a.p
		var pb: Vector3 = b.p
		var fa: float = pa[axis]-edge
		var fb: float = pb[axis]-edge
		var a_in := fa >= 0. if keep_above else fa <= 0.
		var b_in := fb >= 0. if keep_above else fb <= 0.
		if a_in:
			result.append(a)
		if a_in != b_in:
			var t := fa/(fa-fb)
			var point := {"p":pa.lerp(pb,t)}
			if a.has("normal"):
				point.normal = a.normal.lerp(b.normal,t).normalized()
				point.tangent = a.tangent.lerp(b.tangent,t)
			if a.has("uv"):
				point.uv = a.uv.lerp(b.uv,t)
			if a.has("color"):
				point.color = a.color.lerp(b.color,t)
			result.append(point)
	return result

func reveal(points: Array[Vector3], normal: Vector3, tangent: Vector3) -> Array:
	var out: Array = []
	var order: Array = [0,1,2,0,2,3]
	var winding := (points[1]-points[0]).cross(points[2]-points[0]).dot(normal)
	if winding > 0.:
		order = [0,2,1,0,3,2]
	for index: int in order:
		var point := points[index]
		out.append({"p":point,"normal":normal,
			"uv":Vector2(point.x-WEST, point.y if absf(normal.y)<.5 else point.z-NORTH),
			"color":Color.WHITE, "tangent":Vector4(tangent.x,tangent.y,tangent.z,1.)})
	return out

func returns() -> Array:
	var west_north := Vector3(WEST,0.,NORTH)
	var east_north := Vector3(EAST,0.,NORTH)
	var west_south := Vector3(WEST,0.,SOUTH)
	var east_south := Vector3(EAST,0.,SOUTH)
	var h := Vector3.UP*Y_TOP
	var sections := reveal([west_north,east_north,east_north+h,west_north+h],Vector3.BACK,Vector3.RIGHT)
	sections.append_array(reveal([west_south,east_south,east_south+h,west_south+h],Vector3.FORWARD,Vector3.RIGHT))
	sections.append_array(reveal([west_north+h,east_north+h,east_south+h,west_south+h],Vector3.DOWN,Vector3.RIGHT))
	return sections

func build_mesh(mesh: ArrayMesh, add_reveals: bool) -> ArrayMesh:
	var original := mesh.surface_get_arrays(0)
	var vertices: PackedVector3Array = original[Mesh.ARRAY_VERTEX]
	var normals: PackedVector3Array = original[Mesh.ARRAY_NORMAL]
	var tangents: PackedFloat32Array = original[Mesh.ARRAY_TANGENT]
	var colours: PackedColorArray = original[Mesh.ARRAY_COLOR] if original[Mesh.ARRAY_COLOR] != null else PackedColorArray()
	var uvs: PackedVector2Array = original[Mesh.ARRAY_TEX_UV] if original[Mesh.ARRAY_TEX_UV] != null else PackedVector2Array()
	assert(mesh.get_surface_count() == 1 and original[Mesh.ARRAY_INDEX] == null)
	var geometry: Array = []
	var edits := 0
	for i: int in range(0,vertices.size(),3):
		var triangle: Array = []
		for j: int in range(i,i+3):
			var v := {"p":vertices[j],"normal":normals[j],
				"tangent":Vector4(tangents[j*4],tangents[j*4+1],tangents[j*4+2],tangents[j*4+3])}
			if not colours.is_empty():
				v.color = colours[j]
			if not uvs.is_empty():
				v.uv = uvs[j]
			triangle.append(v)
		if targeted(triangle):
			edits += 1
			geometry.append_array(split_triangle(triangle))
		else:
			geometry.append_array(triangle)
	if edits != 4:
		push_error("A1F expected four render faces, found %d" % edits)
		return null
	if add_reveals:
		geometry.append_array(returns())
	var tool := SurfaceTool.new()
	tool.begin(Mesh.PRIMITIVE_TRIANGLES)
	tool.set_material(mesh.surface_get_material(0))
	for v: Dictionary in geometry:
		tool.set_normal(v.normal)
		tool.set_tangent(Plane(v.tangent.x,v.tangent.y,v.tangent.z,v.tangent.w))
		if v.has("color"):
			tool.set_color(v.color)
		if v.has("uv"):
			tool.set_uv(v.uv)
		tool.add_vertex(v.p)
	var replacement := tool.commit()
	replacement.resource_name = "A1F_Entry_Portal_with_Wall_Reveals"
	print("A_PORTAL_RENDER ", edits, " targeted; ", vertices.size()/3., " → ",geometry.size()/3., " faces")
	return replacement

func build_shape(original: ConcavePolygonShape3D) -> ConcavePolygonShape3D:
	var faces := original.get_faces()
	var result := PackedVector3Array()
	var edits := 0
	for i: int in range(0,faces.size(),3):
		var triangle: Array = [{"p":faces[i]},{"p":faces[i+1]},{"p":faces[i+2]}]
		if targeted(triangle):
			edits += 1
			for v: Dictionary in split_triangle(triangle):
				result.append(v.p)
		else:
			result.append(faces[i])
			result.append(faces[i+1])
			result.append(faces[i+2])
	if edits != 4:
		push_error("A1F expected four collision faces, found %d" % edits)
		return null
	for v: Dictionary in returns():
		result.append(v.p)
	var replacement := ConcavePolygonShape3D.new()
	replacement.set_faces(result)
	replacement.backface_collision = original.backface_collision
	replacement.resource_name = "A1F_Entry_Portal_with_Wall_Reveals"
	print("A_PORTAL_COLLISION ", edits, " targeted; ",faces.size()/3., " → ",result.size()/3., " faces")
	return replacement

func build_occluder(original: ArrayOccluder3D) -> ArrayOccluder3D:
	var points := original.vertices
	var order := original.indices
	var replacement_points := PackedVector3Array()
	var replacement_order := PackedInt32Array()
	var edits := 0
	for i: int in range(0,order.size(),3):
		var triangle: Array = [{"p":points[order[i]]},{"p":points[order[i+1]]},{"p":points[order[i+2]]}]
		var converted: Array = triangle
		if targeted(triangle):
			edits += 1
			converted = split_triangle(triangle)
		for v: Dictionary in converted:
			replacement_points.append(v.p)
	if edits != 4:
		push_error("A1F expected four occlusion faces, found %d" % edits)
		return null
	for i: int in replacement_points.size():
		replacement_order.append(i)
	var occluder := ArrayOccluder3D.new()
	occluder.set_arrays(replacement_points,replacement_order)
	print("A_PORTAL_OCCLUSION ",edits," targeted; ",order.size()/3.," → ",replacement_order.size()/3.," faces")
	return occluder

func run() -> void:
	var version_root := ""
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--original="):
			version_root = arg.trim_prefix("--original=").trim_suffix("/")
	if version_root.is_empty():
		push_error("Provide unmodified v34 project root with --original.")
		quit(2)
		return
	var original_mesh := load(version_root+SOURCE_MESH.trim_prefix("res:/")) as ArrayMesh
	var original_finish := load(version_root+SOURCE_FINISH.trim_prefix("res:/")) as ArrayMesh
	var original_finish_neighbor := load(version_root+SOURCE_FINISH_NEIGHBOR.trim_prefix("res:/")) as ArrayMesh
	var original_shape := load(version_root+SOURCE_SHAPE.trim_prefix("res:/")) as ConcavePolygonShape3D
	var original_occlusion := load(version_root+SOURCE_OCCLUSION.trim_prefix("res:/")) as ArrayOccluder3D
	if original_mesh == null or original_finish == null or original_finish_neighbor == null or original_shape == null or original_occlusion == null:
		push_error("Original A1F resources not found.")
		quit(2)
		return
	var mesh := build_mesh(original_mesh,true)
	var finish := build_mesh(original_finish,false)
	var finish_neighbor := build_mesh(original_finish_neighbor,false)
	var shape := build_shape(original_shape)
	var occluder := build_occluder(original_occlusion)
	if mesh == null or finish == null or finish_neighbor == null or shape == null or occluder == null:
		quit(2)
		return
	var mesh_error := ResourceSaver.save(mesh,SOURCE_MESH,ResourceSaver.FLAG_COMPRESS)
	var shape_error := ResourceSaver.save(shape,SOURCE_SHAPE,ResourceSaver.FLAG_COMPRESS)
	var finish_error := ResourceSaver.save(finish,SOURCE_FINISH,ResourceSaver.FLAG_COMPRESS)
	var finish_neighbor_error := ResourceSaver.save(finish_neighbor,SOURCE_FINISH_NEIGHBOR,ResourceSaver.FLAG_COMPRESS)
	var occlusion_error := ResourceSaver.save(occluder,SOURCE_OCCLUSION,ResourceSaver.FLAG_COMPRESS)
	var success := mesh_error == OK and shape_error == OK and finish_error == OK and finish_neighbor_error == OK and occlusion_error == OK
	print("A_PORTAL_BAKED ", success)
	quit(0 if success else 1)
