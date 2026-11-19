extends Node3D

# C1F southwest arcade. The local x axis follows the original three entrances.
# Local -Z faces the garden. World floors, storefront glazing and shop aisles remain authoritative.
const ORIGIN := Vector3(-90.9540358, 0., -213.058349)
const EAST := Vector3(.97618706, 0., .21693046)
const OUTSIDE := Vector3(.21693046, 0., -.97618706)
const FLOOR := .040
const BRICK := "res://assets/v8/brick.png"
const OAK := "res://assets/v8/oak.webp"
const LIMESTONE := "res://assets/v10/materials/limestone-albedo.webp"
const PAVERS := "res://assets/v10/materials/paving-albedo.webp"
const PLASTER := "res://assets/v10/materials/plaster-albedo.webp"
const SHRUB := "res://assets/v17/models/botanical_shrub_2.glb"
const FICUS := "res://assets/v17/models/atrium_ficus_dense.glb"

var player: Node3D
var display_font: Font
var promenade: Node3D
var materials: Dictionary
var faces: Dictionary
var solids: Dictionary

func setup(game: Node3D) -> void:
	name = "V35_C_Promenade"
	player = game.get("player")
	display_font = game.get("font")
	update_near()

func update_near() -> void:
	if not is_instance_valid(player):
		return
	var p := player.global_position
	var middle := ORIGIN + EAST * 22.
	var distance := Vector2(p.x - middle.x, p.z - middle.z).length()
	if is_instance_valid(promenade):
		promenade.visible = p.y > -1. and p.y < 8.
		if distance > 126.:
			promenade.queue_free()
			promenade = null
	elif distance < 100. and p.y > -1. and p.y < 8.:
		build_promenade()

func material(label: String, tint: String, roughness: float, texture: String = "",
		metallic: float = 0., emission: float = 0.) -> StandardMaterial3D:
	if materials.has(label):
		return materials[label]
	var result := StandardMaterial3D.new()
	result.resource_name = label
	result.albedo_color = Color(tint)
	result.roughness = roughness
	result.metallic = metallic
	result.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	if not texture.is_empty():
		result.albedo_texture = load(texture) as Texture2D
	if emission > 0.:
		result.emission_enabled = true
		result.emission = Color(tint)
		result.emission_energy_multiplier = emission
	materials[label] = result
	return result

func surface(collection: Dictionary, finish: Material) -> SurfaceTool:
	if not collection.has(finish):
		var tool := SurfaceTool.new()
		tool.begin(Mesh.PRIMITIVE_TRIANGLES)
		tool.set_material(finish)
		collection[finish] = tool
	return collection[finish]

func pos(x: float, y: float, out: float) -> Vector3:
	return Vector3(x, y, -out)

func block(x: float, y: float, out: float, width: float, height: float, depth: float,
		finish: Material, pitch: float = 0.) -> void:
	var mesh := BoxMesh.new()
	mesh.size = Vector3(width, height, depth)
	surface(solids, finish).append_from(mesh, 0, Transform3D(Basis(Vector3.RIGHT, pitch), pos(x,y,out)))

func panel(vertices: Array[Vector3], normal: Vector3, finish: Material, repeat: float = 1.) -> void:
	var tool := surface(faces, finish)
	var front := (vertices[1]-vertices[0]).cross(vertices[2]-vertices[0]).dot(normal) <= 0.
	var order := [0,1,2,0,2,3] if front else [0,2,1,0,3,2]
	for i: int in order:
		var p := vertices[i]
		tool.set_normal(normal)
		tool.set_uv(Vector2(p.x+p.z, p.y)/repeat if absf(normal.y) < .6 else Vector2(p.x, p.z)/repeat)
		tool.add_vertex(p)

func slab(x1: float, x2: float, out1: float, out2: float, y: float, finish: Material, repeat: float = 1.2) -> void:
	panel([pos(x1,y,out1),pos(x2,y,out1),pos(x2,y,out2),pos(x1,y,out2)], Vector3.UP, finish, repeat)

func drum(x: float, y: float, out: float, top_r: float, base_r: float, height: float,
		finish: Material, segments: int = 24) -> void:
	var mesh := CylinderMesh.new()
	mesh.top_radius = top_r
	mesh.bottom_radius = base_r
	mesh.height = height
	mesh.radial_segments = segments
	mesh.rings = 0
	surface(solids, finish).append_from(mesh, 0, Transform3D(Basis.IDENTITY, pos(x,y,out)))

func label(x: float, y: float, out: float, copy: String, size: float, ink: String,
		inward: bool = false) -> void:
	var plaque := Label3D.new()
	plaque.font = display_font
	plaque.text = copy
	plaque.font_size = 64
	plaque.pixel_size = size / 64.
	plaque.modulate = Color(ink)
	plaque.outline_size = 0
	plaque.double_sided = false
	plaque.position = pos(x,y,out)
	plaque.rotation.y = 0. if inward else PI
	plaque.visibility_range_end = 55.
	plaque.visibility_range_end_margin = 7.
	promenade.add_child(plaque)

func wash(x: float, y: float, out: float, range_m: float, energy: float) -> void:
	var light := OmniLight3D.new()
	light.position = pos(x,y,out)
	light.omni_range = range_m
	light.light_color = Color("#ffecd5")
	light.light_energy = energy
	light.shadow_enabled = false
	light.distance_fade_enabled = true
	light.distance_fade_begin = 19.
	light.distance_fade_length = 11.
	promenade.add_child(light)

func path_and_thresholds() -> void:
	var central := material("C35 flamed stone field", "#b7ad9a", .78, PAVERS)
	var deep := material("C35 charcoal grout", "#6c6759", .84, PAVERS)
	var fine := material("C35 limestone edging", "#d8c8ad", .81, LIMESTONE)
	var brass := material("C35 weathered blade bronze", "#99795d", .63, "", .29)
	var pavers: Array[Material] = [
		material("C35 linen pavers", "#beb09a", .78, LIMESTONE),
		material("C35 amber pavers", "#b6a486", .83, LIMESTONE),
		material("C35 shell pavers", "#c6b9a3", .77, LIMESTONE),
	]
	# The porch ribbon stays inside the observed supported outer pavement; 1F deck is unchanged.
	slab(-11.4,54.7,.99,2.63,.046,deep)
	for row: int in 4:
		var out := 1.05 + float(row) * .377
		var offset := -.72 if row % 2 == 1 else 0.
		for index: int in range(47):
			var x := -11.3 + float(index)*1.45 + offset
			var low := maxf(x,-11.3)
			var high := minf(x+1.434,54.6)
			if high > low:
				slab(low,high,out,out+.363,.051,pavers[(index*7+row+floori(index*.2))%pavers.size()],1.56)
	for edge: float in [1.01,2.566]:
		slab(-11.4,54.7,edge,edge+.054,.053,fine)
	for t: Array in [[0.,2.35], [24.209,2.7], [46.375,2.5]]:
		var x: float = t[0]
		var half_width: float = t[1]
		slab(x-half_width,x+half_width,.45,2.51,.057,central,.83)
		for edge: float in [-1., 1.]:
			var mark := x+edge*(half_width-.20)
			slab(mark,mark+.029,.51,2.5,.059,brass)

func storefronts() -> void:
	var cedar := material("C35 stained exterior cedar", "#866248", .68, OAK)
	var stone := material("C35 chiseled cream limestone", "#d4c3a5", .78, LIMESTONE)
	var cream := material("C35 grooved porcelain", "#dcd0b4", .64, PLASTER)
	var green := material("C35 patinated green iron", "#273f3a", .61, "", .17)
	var sienna := material("C35 baked terracotta", "#986149", .69, BRICK)
	var dark := material("C35 bitumen architectural metal", "#2d3030", .57, "", .38)
	var brass := material("C35 soft anodized brass", "#a97e57", .47, "", .40)
	var light := material("C35 warm acrylic diffuser", "#ffe7b2", .56, "", 0., .73)

	# The shop-specific overdoors attach to the frame above the original access span.
	# They differ in facade rhythm and finish. Common paving keeps the route spanned between them.
	for spec: Dictionary in [
		{"x":0.0,"width":8.8,"plate":green,"trim":cedar,"tag":"LUMEVA TABLE","sub":"ベーカリーと珈琲","ink":"#fff0d2","underside":2.18},
		{"x":24.209,"width":10.2,"plate":stone,"trim":dark,"tag":"CALMERA HOUSE","sub":"家具と暮らし","ink":"#332f29","underside":1.61},
		{"x":46.375,"width":8.0,"plate":sienna,"trim":brass,"tag":"RIVORA GOODS","sub":"日用品と工芸","ink":"#fff0d2","underside":1.45},
	]:
		var x: float = spec.x
		var w: float = spec.width
		var canopy: float = spec.underside
		var plate: Material = spec.plate
		var trim: Material = spec.trim
		# Fascia body, exposed shelf and termination flashing have real depth.
		block(x,3.61,.59,w,1.02,.62,plate)
		block(x,3.86,.53,w+.09,.085,.84,trim)
		block(x,3.135,canopy*.51,w+.08,.135,canopy,trim)
		block(x,3.02,canopy-.039,w+.10,.085,.085,dark)
		block(x,3.08,canopy*.73,w-.29,.017,.045,light)
		for half: float in [-1., 1.]:
			block(x+half*(w*.5-.09),3.559,canopy*.45,.12,.21,canopy*.90,trim)
			block(x+half*(w*.5-.11),4.51,.79,.086,1.27,.10,dark)
		# The name faces arrivals on the leading edge rather than under the deep canopy.
		var plaque_width := minf(w-.25,7.55)
		block(x,3.402,canopy,plaque_width,.52,.18,plate)
		block(x,3.664,canopy,plaque_width+.10,.025,.208,trim)
		block(x,3.143,canopy,plaque_width+.10,.024,.208,trim)
		label(x,3.468,canopy+.095,spec.tag,.33,spec.ink)
		label(x,3.256,canopy+.097,spec.sub,.127,spec.ink)
		# These supports finish against the slab y=5.145.
		if is_equal_approx(x,0.):
			for l: int in 15:
				var ux := x - w*.46 + float(l)*w*.0655
				block(ux,2.982,canopy*.52,.031,.043,canopy*.86,cedar)
			for edge: float in [-1.,1.]:
				var post := x+edge*4.22
				block(post,1.555,.315,.18,3.04,.10,green)
				block(post,1.56,.376,.09,2.84,.036,brass)
		elif x < 30.:
			for band: float in [3.30, 3.94]:
				block(x,band,.91,w-.19,.021,.028,brass)
			for divider: float in [-4.82,-4.51,4.51,4.82]:
				block(x+divider,1.66,.336,.105,3.20,.091,cream)
		else:
			for l: int in range(-8,9):
				if absi(l) < 4:
					continue
				var rib := x + float(l)*.432
				block(rib,3.61,.924,.018,.92,.035,brass)
			for edge: float in [-1., 1.]:
				block(x+edge*3.72,1.55,.333,.195,3.04,.118,sienna)
		wash(x,2.92,.86,4.5,.44)
	# Thin accent ribs are within the storefront plane. Each projecting door upright has a matching body.
	for upright: Array in [[-4.22,.315,.18,3.04,.10],[4.22,.315,.18,3.04,.10],
		[19.389,.336,.105,3.20,.091],[19.699,.336,.105,3.20,.091],
		[28.719,.336,.105,3.20,.091],[29.029,.336,.105,3.20,.091],
		[42.655,.333,.195,3.04,.118],[50.095,.333,.195,3.04,.118]]:
		add_post_collision(upright[0],upright[1],Vector3(upright[2],upright[3],upright[4]))
	# Retain open glazing. Corner spandrels have a timber cap, independent of the doors.
	for span: Array in [[-10.5,-5.15],[6.5,11.7], [13.4,18.8], [31.,34.95], [38.15,41.75], [50.85,54.65]]:
		var x1: float = span[0]
		var x2: float = span[1]
		var mid := (x1+x2)*.5
		block(mid,4.59,.288,x2-x1,.94,.078,stone)
		block(mid,4.124,.339,x2-x1,.064,.083,cedar)
		for i: int in floori((x2-x1)/.44):
			block(x1+.19+float(i)*.44,4.61,.343,.027,.82,.078,cedar)

func add_post_collision(x: float, v: float, size: Vector3) -> void:
	var body := StaticBody3D.new()
	body.name = "C35_Facade_Upright"
	body.position = pos(x,FLOOR+size.y*.5,v)
	var shape := BoxShape3D.new()
	shape.size = size
	var hit := CollisionShape3D.new()
	hit.shape = shape
	body.add_child(hit)
	promenade.add_child(body)

func planter() -> void:
	var stone := material("C35 split-faced plinth", "#c9b89d", .88, LIMESTONE)
	var terra := material("C35 glazed garden ceramic", "#585c4f", .68, "", .11)
	var timber := material("C35 oiled bench cedar", "#9e6d49", .72, OAK)
	var soil := material("C35 growing medium", "#38322c", .96)
	var pad := material("C35 garden terrace setts", "#8a8275", .80, PAVERS)
	# The seating strip is offset to the garden side of the existing tracked pedestrian spine.
	var x := 12.1
	var v := 11.8
	# The terrace pad extends to the original pavement and seats on grade under the bed.
	slab(x-2.27,x+2.27,10.17,12.68,.014,pad,.5)
	for cell: int in 9:
		var u := x-2.20+float(cell)*.49
		slab(u,u+.461,10.27,12.55,.016,stone,.52)
	block(x,.16,v,3.73,.36,1.10,stone)
	block(x,.388,v,3.85,.083,1.17,terra)
	block(x,.42,v,3.58,.034,1.00,soil)
	var basin := x+1.37
	for r: int in 8:
		block(x-1.18+float(r)*.178,.462,v-.325,.143,.046,.48,timber)
	block(basin,.68,v,.59,.54,.88,terra)
	block(basin,.959,v,.53,.02,.83,soil)
	# The authored plant templates predate v35 and retain their original source licence.
	for planting: Array in [[FICUS,basin,.96,v,.48,.4], [SHRUB,x-.09,.425,v+.15,.35,1.7], [SHRUB,x-1.55,.425,v+.18,.33,3.2]]:
		var scene := load(planting[0]) as PackedScene
		var plant := scene.instantiate() as Node3D
		plant.position = pos(planting[1],planting[2],planting[3])
		plant.scale *= float(planting[4])
		plant.rotation.y = planting[5]
		promenade.add_child(plant)
	var body := StaticBody3D.new()
	body.name = "C35_Courtyard_Planter"
	body.position = pos(x,-.020,v)
	for bounds: Array in [[Vector3(0,.236,0),Vector3(3.85,.473,1.17)],
		[Vector3(basin-x,.70,0),Vector3(.59,.54,.88)]]:
		var shape := BoxShape3D.new()
		shape.size = bounds[1]
		var collision := CollisionShape3D.new()
		collision.position = bounds[0]
		collision.shape = shape
		body.add_child(collision)
	promenade.add_child(body)

func cafe_room() -> void:
	var wood := material("C35 cafe suspended oak raft", "#99785c", .66, OAK)
	var bone := material("C35 cafe spun bone enamel", "#d9b79a", .53)
	var red := material("C35 cafe burnt terracotta", "#986053", .61, "", .07)
	var forest := material("C35 cafe evergreen", "#303b36", .65)
	var bronze := material("C35 cafe patinated bronze", "#634e42", .51, "", .5)
	var opal := material("C35 cafe opal glass", "#ffefcf", .49, "", 0., .98)
	var linen := material("C35 cafe terracotta inlay", "#a38371", .83, LIMESTONE)
	var dark_sand := material("C35 cafe limestone aisle border", "#b5a28c", .82, LIMESTONE)
	# Left stripe leads from the opening to the real checkout. The central aisle stays at y=0.
	for side: float in [-1.,1.]:
		slab(side*1.96-.023,side*1.96+.023,-14.1,-.31,.027,dark_sand)
	slab(-10.6,-2.63,-13.78,-3.14,.025,linen,1.45)
	for i: int in 16:
		var out := -13.69 + i*.651
		slab(-10.5,-2.73,out,out+.021,.028,dark_sand)
	for edge: float in [-10.5,-2.75]:
		slab(edge,edge+.024,-13.69,-3.28,.029,dark_sand)
	# Ceiling raft follows the cashier and the next four seating bays and meets the existing 5.145 m soffit.
	for depth: float in [-.88,-4.13,-8.02,-13.55]:
		block(-4.88,4.30,depth,6.65,.16,.145,bronze)
		for x: float in [-7.67,-2.13]:
			block(x,4.76,depth,.047,.76,.047,bronze)
	for i: int in 28:
		var x := -7.96+float(i)*.232
		block(x,4.20,-7.216,.086,.151,12.73,wood)
		if i in [1,13,26]:
			block(x,4.116,-7.216,.048,.021,12.35,opal)
	# Spun conical shades in the café's existing seating pockets. The occupied circulation stays under 3m-clear.
	for fixture: Array in [[-4.50,-6.28,.34,3.25,red],[-4.47,-11.76,.43,3.1,bone],
		[-7.98,-4.08,.34,3.05,bone],[6.32,-4.58,.40,3.08,bone],
		[2.49,-8.45,.36,3.12,red],[5.43,-13.22,.38,3.06,bone],
		[-3.44,-15.13,.39,3.17,bone],[-5.04,-18.82,.33,3.18,red]]:
		var x: float = fixture[0]
		var out: float = fixture[1]
		var radius: float = fixture[2]
		var y: float = fixture[3]
		var mount := 4.12 if x < -2. and x > -8.01 and out > -13.55 else 5.145
		drum(x,(mount+y+.20)*.5,out,.018,.018,mount-y-.20,bronze,8)
		drum(x,y+.14,out,radius*.24,radius,.31,fixture[4])
		drum(x,y-.022,out,radius*.94,radius*.975,.020,bronze)
		drum(x,y-.036,out,radius*.82,radius*.82,.018,opal)
	for x: float in [-5.4,5.4]:
		wash(x,3.010,-9.0,6.4,.43)
	# Order-point marker hangs over the real cashier, joined to the overhead assembly.
	block(-3.81,2.98,-3.22,2.76,.50,.13,forest)
	for x: float in [-4.92,-2.70]:
		block(x,3.663,-3.22,.029,.875,.029,bronze)
	label(-3.81,3.027,-3.15,"お会計・ご注文",.211,"#fff0d2")
	label(-3.81,2.848,-3.145,"ORDER & PAY",.112,"#d4b590")
	bakery_menu(wood,forest,bronze,opal)
	cafe_order_zone(wood, forest, bronze, linen, dark_sand)
	cafe_rear_wall(wood,forest,bronze,opal)

func cafe_order_zone(wood: Material, forest: Material, bronze: Material,
		linen: Material, stone: Material) -> void:
	# Flush floor order zone and the covered directional mark in front of the original POS.
	slab(-6.73,-2.31,-2.29,-.24,.028,linen,.54)
	for x: float in [-6.65,-2.4]:
		slab(x,x+.023,-2.19,-.36,.030,stone)
	for ledge: float in [-2.23,-.34]:
		slab(-6.63,-2.41,ledge,ledge+.020,.030,stone)
	# Counter sign and ceramic trays sit on the measured 0.965 m worktop.
	block(-3.4,1.019,-2.92,.39,.11,.30,wood)
	block(-3.4,1.17,-2.99,.40,.26,.040,forest,deg_to_rad(-12.))
	label(-3.4,1.168,-2.938,"ご注文口",.066,"#fff0d2")
	var porcelain := material("C35 ivory porcelain", "#f0dfc9", .33)
	for cup: Array in [[-4.12,-3.20],[-4.0,-3.25]]:
		drum(cup[0],.98,cup[1],.045,.039,.022,bronze)
		drum(cup[0],1.017,cup[1],.038,.028,.082,porcelain,16)

func cafe_rear_wall(wood: Material, forest: Material, bronze: Material, opal: Material) -> void:
	# Ray-verified rear room wall at out=-20.25. Keep the centre stock door and its path clear.
	for u: float in [-8.64,8.64]:
		block(u,2.46,-20.16,2.89,2.94,.18,wood)
		for i: int in 11:
			block(u-1.31+float(i)*.262,2.46,-20.048,.027,2.91,.032,bronze)
		block(u,3.96,-20.09,2.89,.11,.31,forest)
		block(u,3.896,-19.99,2.70,.017,.067,opal)
	block(4.32,2.64,-20.14,5.47,2.07,.20,wood)
	block(4.32,2.64,-20.025,5.32,1.94,.047,forest)
	image_board("lumeva-wall.jpg",Vector2(5.22,1.86),pos(4.32,2.64,-19.997),PI)

func bakery_menu(wood: Material, forest: Material, bronze: Material, opal: Material) -> void:
	# The menu belongs to the existing left-hand bakery and coffee counter, above the merchandise.
	# The checked shop perimeter here is x=-11.684 and y=5.145.
	block(-11.55,2.42,-7.42,.27,1.59,5.43,wood)
	block(-11.382,2.42,-7.42,.066,1.51,5.31,forest)
	block(-11.277,3.25,-7.42,.28,.10,5.44,bronze)
	block(-11.205,3.184,-7.42,.077,.022,5.15,opal)
	image_board("lumeva-menu.jpg",Vector2(5.20,1.4733),pos(-11.344,2.42,-7.42),PI*.5)

func image_board(texture: String, size: Vector2, anchor: Vector3, angle: float) -> void:
	var finish := StandardMaterial3D.new()
	finish.albedo_texture = load("res://assets/v35/c/"+texture) as Texture2D
	finish.roughness = .84
	finish.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	var panel_mesh := QuadMesh.new()
	panel_mesh.size = size
	panel_mesh.material = finish
	var graphic := MeshInstance3D.new()
	graphic.mesh = panel_mesh
	graphic.position = anchor
	graphic.rotation.y = angle
	promenade.add_child(graphic)

func build_promenade() -> void:
	promenade = Node3D.new()
	promenade.name = "C1F_South_Promenade"
	promenade.transform = Transform3D(Basis(EAST,Vector3.UP,-OUTSIDE),ORIGIN)
	add_child(promenade)
	path_and_thresholds()
	storefronts()
	planter()
	cafe_room()
	for batch: SurfaceTool in faces.values() + solids.values():
		var mesh := MeshInstance3D.new()
		mesh.mesh = batch.commit()
		mesh.visibility_range_end = 105.
		mesh.visibility_range_end_margin = 9.
		promenade.add_child(mesh)
	faces.clear()
	solids.clear()
