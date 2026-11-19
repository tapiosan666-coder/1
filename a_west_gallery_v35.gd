extends Node3D

# A1F west specialty walk, atrium edge and Orienne.
# The existing floor, glazing, door controls, shop colliders and shelf placements are retained.
const VICINITY := Vector3(328., 0., -60.)
const TREE_PATH := "res://assets/v17/models/atrium_ficus_dense.glb"
const SEAT_A := Vector3(330.0, 0., -54.2)
const SEAT_B := Vector3(353.8, 0., -53.25)
const BOOK_DISPLAY := Vector3(321.25, 0., -67.05)

var player: Node3D
var runtime: Node
var retired_sign_cell: int
var display_font: Font
var gallery: Node3D
var materials: Dictionary
var batches: Dictionary
var solids: Dictionary
var refresh_time: float

func setup(game: Node3D) -> void:
	name = "V35_A_West_Gallery"
	player = game.get("player")
	runtime = game.get_node_or_null("V30_Runtime")
	display_font = game.get("font")
	update_near()

func _process(delta: float) -> void:
	refresh_time += delta
	if refresh_time >= .35:
		refresh_time = 0.
		update_near()

func update_near() -> void:
	if not is_instance_valid(player):
		return
	var point := player.global_position
	var distance := Vector2(point.x - VICINITY.x, point.z - VICINITY.z).length()
	if is_instance_valid(gallery):
		retire_bookshop_sign()
		gallery.visible = absf(point.y) < 10.
		if distance > 119.:
			gallery.queue_free()
			gallery = null
		return
	if distance < 94. and absf(point.y) < 8.0:
		build_gallery()
		retire_bookshop_sign()

func retire_bookshop_sign() -> void:
	# This front-facing baked sign belongs to A1F-051. Keep its interior posters.
	if not is_instance_valid(runtime):
		return
	var cells: Dictionary = runtime.get("active")
	var cell: Node3D = cells.get("interior_0_6_-2")
	if cell == null or retired_sign_cell == cell.get_instance_id():
		return
	retired_sign_cell = cell.get_instance_id()
	for child: Node in cell.get_children():
		if not child is MultiMeshInstance3D or child.multimesh == null:
			continue
		var mesh: Mesh = child.multimesh.mesh
		if mesh == null or mesh.get_surface_count() != 1:
			continue
		if mesh.resource_path == "res://assets/v30/world/meshes/1e17fb7b850fac4cb78cd00196eaeb4051bb238f33f916c76cd604078743daf0.res":
			child.hide()

func finish(key: String, tint: String, gloss: float = .65, alloy: float = 0.,
		texture_path: String = "", emit: float = 0.) -> StandardMaterial3D:
	if materials.has(key):
		return materials[key]
	var material := StandardMaterial3D.new()
	material.resource_name = "A West " + key
	material.albedo_color = Color(tint)
	material.roughness = gloss
	material.metallic = alloy
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	if not texture_path.is_empty():
		material.albedo_texture = load(texture_path) as Texture2D
	if emit > 0.:
		material.emission_enabled = true
		material.emission = Color(tint)
		material.emission_energy_multiplier = emit
	materials[key] = material
	return material

func surface(material: Material) -> SurfaceTool:
	if batches.has(material):
		return batches[material]
	var tool := SurfaceTool.new()
	tool.begin(Mesh.PRIMITIVE_TRIANGLES)
	tool.set_material(material)
	batches[material] = tool
	return tool

func panel(points: Array[Vector3], normal: Vector3, material: Material, tile_scale: float = 1.) -> void:
	var tool := surface(material)
	var horizontal := absf(normal.y) > .65
	for i: int in [0, 1, 2, 0, 2, 3]:
		var p := points[i]
		tool.set_normal(normal)
		tool.set_uv(Vector2(p.x, p.z) / tile_scale if horizontal else Vector2(p.x + p.z, p.y) / tile_scale)
		tool.add_vertex(p)

func slab(a: Vector2, b: Vector2, y: float, material: Material, repeat_size: float = 1.) -> void:
	panel([Vector3(a.x,y,a.y), Vector3(b.x,y,a.y), Vector3(b.x,y,b.y), Vector3(a.x,y,b.y)],
		Vector3.UP, material, repeat_size)

func solid(p: Vector3, size: Vector3, material: Material, angle: float = 0.) -> void:
	var source := BoxMesh.new()
	source.size = size
	if not solids.has(material):
		var tool := SurfaceTool.new()
		tool.begin(Mesh.PRIMITIVE_TRIANGLES)
		tool.set_material(material)
		solids[material] = tool
	var destination: SurfaceTool = solids[material]
	destination.append_from(source, 0, Transform3D(Basis(Vector3.UP, angle), p))

func cut_rect(width: float, depth: float, bevel: float, corners: int = 6) -> PackedVector2Array:
	var result := PackedVector2Array()
	var half := Vector2(width, depth) * .5
	for corner: Vector2 in [Vector2.ONE, Vector2(-1,1), -Vector2.ONE, Vector2(1,-1)]:
		var index := floori(float(result.size()) / float(corners))
		for sample: int in corners:
			var angle := (float(index) + float(sample) / (corners - 1)) * PI * .5
			result.append(corner * (half - Vector2.ONE * bevel) + Vector2(cos(angle), sin(angle)) * bevel)
	return result

func wide_edge(points: PackedVector2Array, p: Vector3, y_low: float, y_high: float,
		material: Material, foot_scale: float = 1.) -> void:
	for i: int in points.size():
		var a := points[i]
		var b := points[(i + 1) % points.size()]
		var normal_2d := Vector2((b-a).y, (a-b).x).normalized()
		panel([p+Vector3(a.x*foot_scale,y_low,a.y*foot_scale), p+Vector3(a.x,y_high,a.y),
			p+Vector3(b.x,y_high,b.y), p+Vector3(b.x*foot_scale,y_low,b.y*foot_scale)],
			Vector3(normal_2d.x, 0., normal_2d.y), material)

func fill(points: PackedVector2Array, p: Vector3, height: float, material: Material) -> void:
	var tool := surface(material)
	for i: int in points.size():
		var a := points[i]
		var b := points[(i+1)%points.size()]
		for v: Vector2 in [Vector2.ZERO, a, b]:
			tool.set_normal(Vector3.UP)
			tool.set_uv(v)
			tool.add_vertex(p+Vector3(v.x,height,v.y))

func caption(p: Vector3, facing: Vector3, copy: String, size: float, colour: Color) -> void:
	var label := Label3D.new()
	label.font = display_font
	label.text = copy
	label.font_size = 48
	label.pixel_size = size / 48.
	label.modulate = colour
	label.outline_size = 0
	label.no_depth_test = false
	label.double_sided = false
	label.basis = Basis(Vector3.UP.cross(facing), Vector3.UP, facing)
	label.position = p
	label.visibility_range_end = 54.
	label.visibility_range_end_margin = 6.
	gallery.add_child(label)

func collider(label: String, center: Vector3, hull: PackedVector2Array, height: float) -> void:
	var body := StaticBody3D.new()
	body.name = label
	body.position = center
	var points := PackedVector3Array()
	for vertex: Vector2 in hull:
		points.append(Vector3(vertex.x,0.,vertex.y))
		points.append(Vector3(vertex.x,height,vertex.y))
	var shape := ConvexPolygonShape3D.new()
	shape.points = points
	var hitbox := CollisionShape3D.new()
	hitbox.shape = shape
	body.add_child(hitbox)
	gallery.add_child(body)

func floor_ribbon() -> void:
	var main := finish("shell terrazzo", "#d7cfbb", .52, .0, "res://assets/v10/materials/terrazzo-albedo.webp")
	var darker := finish("tobacco terrazzo", "#b89b81", .58, .0, "res://assets/v10/materials/terrazzo-albedo.webp")
	var shadow := finish("oxidised bronze inlay", "#775c45", .44, .3)
	for start: Vector2 in [Vector2(308.35,-64.67)]:
		var end := Vector2(374.65,-60.67)
		slab(start,end,.045,darker,1.52)
		# Three-metre modules with staggered large-format double slabs.
		for j: int in 22:
			var x := start.x + j*3.
			slab(Vector2(x+.009,-64.48),Vector2(x+2.991,-62.42),.048,main,1.52)
			var middle_end := minf(end.x-.18,x+3.0+1.5)
			if middle_end > x+1.51:
				slab(Vector2(x+1.51,-62.4),Vector2(middle_end-.009,-60.86),.048,main,1.52)
		slab(Vector2(start.x,-62.4),Vector2(start.x+1.49,-60.86),.048,main,1.52)
		for line: float in [-64.58,-60.77]:
			slab(Vector2(start.x+.01,line),Vector2(end.x-.01,line+.034),.05,shadow)
	# The two seating pockets sit on the public floor. No extension over the ES cutout x342..348.
	for bounds: Array in [[326.7,-57.0,335.9,-51.75],[350.9,-55.65,358.9,-51.15]]:
		var lower := Vector2(bounds[0],bounds[1])
		var upper := Vector2(bounds[2],bounds[3])
		slab(lower,upper,.045,darker,1.7)
		slab(lower+Vector2.ONE*.095,upper-Vector2.ONE*.095,.048,main,1.7)
		for i: int in range(1,5):
			var line := lerpf(lower.x, upper.x, i/5.)
			slab(Vector2(line,lower.y+.097),Vector2(line+.016,upper.y-.097),.05,darker)

func west_entry() -> void:
	# The owner-cell wall was rebuilt as a real opening. Its original floor and roof remain.
	var stone := finish("entry honed limestone", "#c2ae92",.61,0.,"res://assets/v10/materials/limestone-albedo.webp")
	var dark := finish("entry terrazzo joints","#6d6658",.56)
	var bronze := finish("entry bronze doorframe","#715a47",.49,.37)
	var lettering := Color("#ffedca")
	var warm := finish("opal linear light", "#fff0d0", .52, .0, "", .57)
	var enamel := finish("west directory enamel", "#203b36", .65)
	slab(Vector2(302.14,-59.55),Vector2(312.7,-56.45),.046,stone,1.08)
	for joint: float in [303.25,304.64,306.06,307.47,308.86,310.23,311.61]:
		slab(Vector2(joint,-59.539),Vector2(joint+.018,-56.461),.048,dark)
	for side: float in [-59.63,-56.37]:
		solid(Vector3(305.8,1.59,side),Vector3(.33,3.18,.045),bronze)
	solid(Vector3(305.80,3.168,-58.),Vector3(.33,.039,3.265),bronze)
	solid(Vector3(305.806,3.144,-58.),Vector3(.115,.017,3.21),warm)
	# Set the label on the wall itself, above headroom, with no new floor obstruction.
	solid(Vector3(305.63,3.53,-58.),Vector3(.11,.40,3.22),enamel)
	caption(Vector3(305.57,3.61,-58.),Vector3.LEFT,"A館  1F　 西入口",.165,lettering)
	caption(Vector3(305.569,3.43,-58.),Vector3.LEFT,"WEST ENTRANCE",.10,Color("#d6b989"))
	solid(Vector3(305.97,3.53,-58.),Vector3(.11,.40,3.22),enamel)
	caption(Vector3(306.03,3.58,-58.),Vector3.RIGHT,"西口",.16,lettering)
	caption(Vector3(306.032,3.43,-58.),Vector3.RIGHT,"WEST EXIT",.095,Color("#d6b989"))

func light_baffles() -> void:
	var oak := finish("gallery stained oak", "#7f5c41", .62, .0, "res://assets/v8/oak.webp")
	var trim := finish("gallery bronze", "#674b36", .39, .52)
	var diffuser := finish("opal linear light", "#fff0d0", .52, .0, "", .57)
	# The narrow run is immediately under the verified 1F slab, along the shop edge.
	# Cross ties land on two continuous rails, supported at 4.95m under the slab.
	for bay: float in [317.9, 328.9, 339.9, 350.9, 361.9]:
		var rail_z := -62.5
		for edge: float in [-1.43, 1.43]:
			solid(Vector3(bay,4.79,rail_z+edge),Vector3(8.10,.12,.09),trim)
			for pin: float in [-3.65, 3.65]:
				solid(Vector3(bay+pin,4.93,rail_z+edge),Vector3(.095,.27,.08),trim)
		for strip: int in 11:
			var x := bay + (float(strip)-5.)*.67
			solid(Vector3(x,4.72,rail_z),Vector3(.075,.20,2.94),oak)
			if strip in [1,5,9]:
				solid(Vector3(x,4.606,rail_z),Vector3(.059,.023,2.82),diffuser)
	# First bay identifies the galley after the vestibule. The existing route sign remains at x309.
	var blue := finish("west directory enamel", "#203b36", .65)
	var white := Color("#fff4df")
	var inward := Vector3.LEFT
	solid(Vector3(317.9,3.94,-61.1),Vector3(.12,.64,4.02),blue)
	for support_z: float in [-62.59, -59.61]:
		solid(Vector3(317.9,4.59,support_z),Vector3(.035,.69,.038),trim)
	caption(Vector3(317.83,4.025,-61.1),inward,"西アトリウム",.26,white)
	caption(Vector3(317.826,3.82,-61.1),inward,"WEST ATRIUM",.13,Color("#d9bd8f"))

func lounge() -> void:
	var mineral := finish("bench travertine", "#d2b697", .70, 0., "res://assets/v8/travertine.png")
	var linen := finish("forest upholstery", "#405b54", .87)
	var saddle := finish("russet upholstery", "#a46c47", .82)
	var metal := finish("dark plinth", "#302d2a", .54, .35)
	var earth := finish("planter soil", "#40312a", .96)
	var edge := finish("trim satin copper", "#aa7751", .39,.45)
	# Seating stays isolated from doors, kiosks, and the player spine.
	for config: Dictionary in [
		{"root":SEAT_A,"width":5.15,"depth":2.08,"leaf":.63,"seat":linen},
		{"root":SEAT_B,"width":4.10,"depth":1.82,"leaf":.53,"seat":saddle}]:
		var p: Vector3 = config.root
		var width: float = config.width
		var depth: float = config.depth
		var border := cut_rect(width,depth,.34,7)
		wide_edge(border,p,.039,.11,metal,.97)
		wide_edge(border,p,.11,.427,mineral,.97)
		wide_edge(border,p,.427,.451,edge)
		fill(border,p,.451,mineral)
		var planter := cut_rect(width*.48,depth*.82,.26,7)
		var planted_at := p+Vector3(width*.239,0.,.0)
		wide_edge(planter,planted_at,.451,.72,mineral,.95)
		wide_edge(planter,planted_at,.72,.77,edge)
		fill(planter,planted_at,.765,earth)
		var seat_width := width*.43
		var joining := cut_rect(seat_width,depth*.69,.19,7)
		var cushion_at := p-Vector3(width*.235,0,0)
		wide_edge(joining,cushion_at,.451,.515,config.seat,.98)
		fill(joining,cushion_at,.516,config.seat)
		solid(cushion_at+Vector3(0.,.71,depth*.23),Vector3(seat_width*.94,.40,.11),config.seat)
		collider("A35_Seating_Island",p,border,.451)
		collider("A35_Planter_Rim",planted_at,planter,.78)
		collider("A35_Seating_Back",cushion_at+Vector3(0.,.451,depth*.23),
			cut_rect(seat_width*.94,.11,.035,4),.46)
		var scene := load(TREE_PATH) as PackedScene
		if scene != null:
			var tree := scene.instantiate() as Node3D
			tree.scale = Vector3.ONE*float(config.leaf)
			tree.position = planted_at+Vector3.UP*.746
			tree.rotation.y = .45 if p == SEAT_A else 2.6
			gallery.add_child(tree)

func bookshop() -> void:
	# The doorway and sign use the original entrance axis x325.5, outward +Z.
	var walnut := finish("Orienne blackened walnut", "#3c312a", .62, .0, "res://assets/v10/wood-walnut.png")
	var oak := finish("Orienne warm oak", "#b78459", .72, .0, "res://assets/v8/oak.webp")
	var blue := finish("Orienne dark green", "#283e36", .67)
	var silk := finish("Orienne frosted line", "#ffe1ac", .55, .0, "", .45)
	var paper := finish("Orienne threshold", "#af9c80", .73, .0, "res://assets/v10/materials/limestone-albedo.webp")
	var brass := finish("Orienne brass", "#b58848", .43, .38)
	# Wide timber sign header above pedestrian clearance. Cover the original sign behind on the same opening.
	solid(Vector3(325.5,3.57,-64.48),Vector3(6.37,1.09,.26),walnut)
	solid(Vector3(325.5,3.677,-64.33),Vector3(5.95,.52,.06),blue)
	solid(Vector3(325.5,3.414,-64.285),Vector3(5.72,.018,.021),brass)
	caption(Vector3(325.5,3.76,-64.29),Vector3.BACK,"ORIENNE BOOKS",.36,Color("#ffebc3"))
	caption(Vector3(325.5,3.522,-64.285),Vector3.BACK,"書籍・文具",.14,Color("#e2c697"))
	# Top-lit supported soffit slats mark a single shared storefront threshold.
	for leg: float in [322.44, 328.56]:
		solid(Vector3(leg,1.59,-64.64),Vector3(.14,3.10,.20),walnut)
		collider("A35_Orienne_Door_Post",Vector3(leg,.039,-64.64),cut_rect(.14,.20,.03,4),3.10)
		solid(Vector3(leg,3.17,-65.14),Vector3(.10,.18,1.42),walnut)
	for beam: int in 5:
		var z := -64.68 - float(beam)*.28
		solid(Vector3(325.5,3.195,z),Vector3(6.17,.095,.058),oak)
		if beam in [1,3]:
			solid(Vector3(325.5,3.14,z),Vector3(5.84,.015,.041),silk)
	slab(Vector2(322.8,-65.98),Vector2(328.2,-64.75),.045,paper,1.22)
	slab(Vector2(322.85,-64.79),Vector2(328.15,-64.767),.047,brass)
	# Suspended linear fittings accent the shop's inward reading route.
	for x: float in [322.4, 329.7]:
		solid(Vector3(x,4.29,-69.79),Vector3(.145,.15,5.4),walnut)
		solid(Vector3(x,4.206,-69.79),Vector3(.115,.015,5.18),silk)
		for z: float in [-67.44,-72.14]:
			solid(Vector3(x,4.706,z),Vector3(.029,.75,.029),walnut)
	var spot := OmniLight3D.new()
	spot.position = Vector3(325.5,3.05,-66.67)
	spot.light_color = Color("#fff0d8")
	spot.light_energy = .39
	spot.omni_range = 6.2
	spot.shadow_enabled = false
	spot.distance_fade_enabled = true
	spot.distance_fade_begin = 20.
	spot.distance_fade_length = 11.
	gallery.add_child(spot)
	book_display(walnut, brass, paper)

func printed_quad(points: Array[Vector3], normal: Vector3, material: Material, coords: Rect2) -> void:
	var atlas := surface(material)
	var uv: Array[Vector2] = [coords.position,Vector2(coords.end.x,coords.position.y),
		coords.end,Vector2(coords.position.x,coords.end.y)]
	for i: int in [0,1,2,0,2,3]:
		atlas.set_normal(normal)
		atlas.set_uv(uv[i])
		atlas.add_vertex(points[i])

func book_cover(index: int) -> Rect2:
	var pixel_origin := Vector2(6+index%3*297,6+floori(float(index)/3.)*442)
	var atlas_size := Vector2(891.,884.)
	return Rect2((pixel_origin+Vector2.ONE) / atlas_size,Vector2(283.,428.) / atlas_size)

func book_display(walnut: Material, brass: Material, paper: Material) -> void:
	var center := BOOK_DISPLAY
	var frame := cut_rect(1.82,.58,.052,5)
	var base := cut_rect(1.56,.47,.045,5)
	var book_atlas := finish("original illustrated book covers", "#ffffff", .76, 0.,
		"res://assets/v35/a_west/orienne_covers.webp")
	var poster := finish("seasonal reading list", "#ffffff", .81, 0.,
		"res://assets/v35/a_west/orienne_season.webp")
	var inside := finish("Orienne display forest green", "#333d34", .71)
	# The shop-front new release table is clear of both original aisle and stock shelving.
	wide_edge(base,center,.04,.12,walnut,.99)
	wide_edge(base,center,.12,.83,inside)
	wide_edge(frame,center,.83,.907,walnut,.99)
	wide_edge(frame,center,.883,.89,brass)
	fill(frame,center,.907,walnut)
	solid(center+Vector3(0.,.56,.234),Vector3(1.30,.42,.018),walnut)
	collider("A35_Orienne_New_Releases",center,frame,1.075)
	for index: int in 6:
		var x := -.69 + float(index)*.275
		var z := .077+sin(index*1.7)*.025
		var width := .185+sin(index*2.1)*.021
		var length := width*1.43
		var h := .912
		var layers := 2+(index%3)
		for layer: int in layers:
			var thickness := .016+float(index%2)*.004
			var layer_offset := (layer%2)*.006
			solid(center+Vector3(x+layer_offset,h+thickness*.5,z),Vector3(width-.008,thickness,length-.012),paper)
			h += thickness
			solid(center+Vector3(x+layer_offset,h+.002,z),Vector3(width,.004,length),inside)
			h += .004
		var a := center+Vector3(x-width*.5,h+.001,z-length*.5)
		var b := center+Vector3(x+width*.5,h+.001,z-length*.5)
		var c := center+Vector3(x+width*.5,h+.001,z+length*.5)
		var d := center+Vector3(x-width*.5,h+.001,z+length*.5)
		printed_quad([a,b,c,d],Vector3.UP,book_atlas,book_cover(index))
	# Three different covers face the approach on a slight slant behind the merchandise.
	for index: int in [0,2,4]:
		var x := -.57+float(index)*.191
		var bottom := center+Vector3(x,.914,-.097)
		var to_top := Vector3(0.,.238,-.089)
		var left := Vector3(-.084,0.,0.)
		var right := -left
		solid(bottom+Vector3(0.,.09,-.075),Vector3(.147,.174,.03),inside)
		printed_quad([bottom+to_top+left,bottom+to_top+right,bottom+right,bottom+left],
			Vector3(0.,.35,.94).normalized(),book_atlas,book_cover(index))
	var post := center+Vector3(.614,0.,-.214)
	solid(post+Vector3.UP*1.04,Vector3(.019,.28,.022),brass)
	solid(post+Vector3.UP*1.32,Vector3(.225,.306,.023),walnut)
	var offset := post+Vector3(0.,1.32,.013)
	printed_quad([offset+Vector3(-.105,.144,0.),offset+Vector3(.105,.144,0.),
		offset+Vector3(.105,-.144,0.),offset+Vector3(-.105,-.144,0.)],
		Vector3.BACK,poster,Rect2(.0,.0,1.,1.))

func build_gallery() -> void:
	batches.clear()
	gallery = Node3D.new()
	gallery.name = "A1F_West_Atrium_Gallery"
	add_child(gallery)
	floor_ribbon()
	west_entry()
	light_baffles()
	lounge()
	bookshop()
	for tool: SurfaceTool in batches.values() + solids.values():
		var element := MeshInstance3D.new()
		element.mesh = tool.commit()
		element.visibility_range_end = 100.
		element.visibility_range_end_margin = 12.
		gallery.add_child(element)
	batches.clear()
	solids.clear()
