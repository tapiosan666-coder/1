class_name Mall
extends Node3D
## Fictional, connected mall floor: long concourse, a second promenade,
## shop interiors, a food court and a restroom wing. Not a real-site replica.

const CATEGORIES := ["書店","服飾","靴・鞄","生活雑貨","家電","喫茶","家具","日用品","スポーツ"]
const SHOP_CENTERS := [-75.0, -57.0, -39.0, -21.0, -3.0, 15.0, 33.0, 51.0, 69.0]
const MAIN := Rect2(-90, -8, 180, 16)
const FOOD := Rect2(46, -62, 46, 30)
const RESTROOM := Rect2(-90, 26, 38, 30)
const PROMENADE := Rect2(-47, -36, 127, 8)
const MARKET := Rect2(6, 8, 36, 40)
const HUBS := {"中央入口": Vector3(-82,.1,0), "中央広場": Vector3(-39,.1,3), "食品スーパー": Vector3(24,.1,11), "フードコート": Vector3(69,.1,-34), "お手洗い前": Vector3(-73,.1,32)}
const ENTRANCE := Vector3(-82, 0.1, 0)
static var floor_regions: Array[Rect2] = []
static var obstacles: Array[Rect2] = []
var spawn_points: Array[Vector3] = []
var identity_slots: Array[Dictionary] = []
var outline := PackedVector2Array()
var chalk := Shapes.material(Color("d8d6cf"))
var dark := Shapes.material(Color("25363d"))
var stone := Shapes.material(Color("88918d"))
var wood := Shapes.timber()
var warm := Shapes.material(Color("ffe5ba"), 0.8)

static func has_shop(x: float, side: int) -> bool:
	return not (side == -1 and x in [-39.0, 69.0]) and not (side == 1 and x in [-75.0,15.0,33.0])

static func prepare_plan() -> void:
	if not floor_regions.is_empty():
		return
	floor_regions.append(MAIN)
	# Retail units share a continuous building slab; partitions define shops.
	floor_regions.append(Rect2(-84, -24, 164, 16))
	# Add connecting pieces before their destination for polygon union.
	floor_regions.append(Rect2(60, -42, 20, 35))
	floor_regions.append(FOOD)
	floor_regions.append(Rect2(-48, -29, 18, 22))
	floor_regions.append(Rect2(-48, -29, 128, 5))
	floor_regions.append(PROMENADE)
	floor_regions.append(Rect2(-79, 7, 12, 23))
	floor_regions.append(RESTROOM)
	floor_regions.append(Rect2(6,7.9,36,40.1))
	for x in [12.0,22.0,32.0]:
		for z in [23.0,35.0]:
			obstacles.append(Rect2(x-1.2,z-3.5,2.4,7))
	for x in [12.0,36.0]:
		obstacles.append(Rect2(x-1.5,12.5,3,1.3))
	for fixture in [Rect2(6,8.3,3,.24),Rect2(15,8.3,18,.24),Rect2(39,8.3,3,.24)]:
		obstacles.append(fixture)
	for side in [-1, 1]:
		for x in SHOP_CENTERS:
			if not has_shop(x, side):
				continue
			floor_regions.append(Rect2(x - 9, -24 if side < 0 else 8, 18, 16))
			for wall_x in [x - 9, x + 9]:
				obstacles.append(Rect2(wall_x - 0.16, -24 if side < 0 else 8.8, 0.32, 15.2))
			# Two display windows frame a six-metre shop entrance.
			for dx in [-6.0,6.0]:
				obstacles.append(Rect2(x+dx-3, side*8.5-.12, 6,.24))
			obstacles.append(Rect2(x-9,side*23.6-.12,18,.24))
			for dx in [-4.5,4.5]:
				obstacles.append(Rect2(x+dx-1,side*13.5-1.4,2,2.8))
			obstacles.append(Rect2(x + 1.5, side * 18 - 0.65, 3, 1.3))
			obstacles.append(Rect2(x - 7.5, -22.5 if side < 0 else 21.2, 12, 1.3))
	for x in [53.0, 67.0, 81.0]:
		for z in [-39.0, -47.0, -54.0]:
			obstacles.append(Rect2(x - 1.3, z - 0.7, 2.6, 1.4))
			for d in [Vector2(-1.9, 0), Vector2(1.9, 0), Vector2(0, -1.6), Vector2(0, 1.6)]:
				obstacles.append(Rect2(Vector2(x, z) + d - Vector2(0.3, 0.3), Vector2(0.6, 0.6)))
	for x in [51.0, 62.0, 73.0, 84.0]:
		obstacles.append(Rect2(x - 4.5, -60, 9, 1))
	for side in [-1,1]:
		for x in [-57.0,-21.0,15.0,51.0]:
			obstacles.append(Rect2(x-1.5,side*3.4-.31,3,.62))
	for x in [-39.0, 33.0]:
		obstacles.append(Rect2(x - 1.5, -1.5, 3, 3))
	for x in range(-84, 90, 12):
		for z in [-7.4, 7.4]:
			obstacles.append(Rect2(x - 0.175, z - 0.175, 0.35, 0.35))
	# Basins and the rear partitions leave a continuous public aisle.
	obstacles.append(Rect2(-89, 39, 1.5, 14))
	for x in [-67.0, -62.0, -57.0]:
		obstacles.append(Rect2(x - 0.14, 46, 0.28, 9))
		obstacles.append(Rect2(x - 2.45, 51.85, 0.7, 0.7))
		obstacles.append(Rect2(x - 2.45, 54.2, 0.7, 0.4))

static func inside_floor(p: Vector2) -> bool:
	prepare_plan()
	for region in floor_regions:
		if region.has_point(p):
			return true
	return false

static func walkable(p: Vector3) -> bool:
	var v := Vector2(p.x, p.z)
	for offset in [Vector2.ZERO, Vector2(0.42, 0), Vector2(-0.42, 0), Vector2(0, 0.42), Vector2(0, -0.42)]:
		if not inside_floor(v + offset):
			return false
	for obstacle in obstacles:
		if obstacle.grow(0.35).has_point(v):
			return false
	return true

static func segment_walkable(a: Vector3, b: Vector3) -> bool:
	var steps := maxi(1,ceili(a.distance_to(b)/.2))
	for index in range(steps+1):
		if not walkable(a.lerp(b,float(index)/steps)):
			return false
	return true

static func zone_name(p: Vector3) -> String:
	var v := Vector2(p.x, p.z)
	if MARKET.has_point(v):
		return "A館1階 / 食品スーパー"
	if FOOD.has_point(v):
		return "A館1階 / フードコート"
	if RESTROOM.has_point(v) or Rect2(-79, 8, 12, 18).has_point(v):
		return "A館1階 / お手洗い方面"
	if PROMENADE.has_point(v):
		return "A館1階 / 北側連絡通路"
	return "A館1階 / ショッピングモール"

func _ready() -> void:
	prepare_plan()
	_build_floor_and_walls()
	_build_concourse()
	_build_architecture()
	_build_shops()
	_build_market()
	_build_food_court()
	_build_restroom()
	_build_conversations()
	for z in range(-61, 57, 2):
		for x in range(-89, 93, 2):
			var p := Vector3(x, 0, z)
			if walkable(p):
				spawn_points.append(p)

func _polygon(rect: Rect2) -> PackedVector2Array:
	return PackedVector2Array([rect.position, rect.position + Vector2(rect.size.x, 0), rect.end, rect.position + Vector2(0, rect.size.y)])

func _build_floor_and_walls() -> void:
	outline = _polygon(floor_regions[0])
	for i in range(1, floor_regions.size()):
		var merged := Geometry2D.merge_polygons(outline, _polygon(floor_regions[i]))
		assert(merged.size() == 1, "All public floor regions must form one connected polygon")
		outline = merged[0]
	var floor_mat := ShaderMaterial.new()
	floor_mat.shader = load("res://assets/terrazzo.gdshader")
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	var triangles := Geometry2D.triangulate_polygon(outline)
	for i in range(0, triangles.size(), 3):
		for offset in [0, 1, 2]:
			var v := outline[triangles[i + offset]]
			surface.set_normal(Vector3.UP)
			surface.add_vertex(Vector3(v.x, 0, v.y))
	var mesh := surface.commit()
	var floor_node := MeshInstance3D.new()
	floor_node.mesh = mesh
	floor_node.material_override = floor_mat
	add_child(floor_node)
	var body := StaticBody3D.new()
	var collider := CollisionShape3D.new()
	collider.shape = mesh.create_trimesh_shape()
	body.add_child(collider)
	add_child(body)
	for i in outline.size():
		var a := outline[i]
		var b := outline[(i + 1) % outline.size()]
		var middle := (a + b) / 2
		var size := Vector3(absf(a.x - b.x) + 0.3, 5.2, absf(a.y - b.y) + 0.3)
		if is_equal_approx(a.x,92) and is_equal_approx(b.x,92) and middle.y < -30:
			Shapes.box(self,Vector3(middle.x,2.6,middle.y),size,_glass(),true)
			Shapes.box(self,Vector3(92,.55,middle.y),Vector3(.32,1.1,size.z),chalk)
			for z in range(-62,-30,6):
				Shapes.box(self,Vector3(92,2.6,z),Vector3(.35,5.2,.12),stone)
		else:
			Shapes.box(self, Vector3(middle.x, 2.6, middle.y), size, chalk, true)
		Shapes.box(self, Vector3(middle.x, 0.12, middle.y), Vector3(size.x + 0.04, 0.24, size.z + 0.04), stone)

func _build_concourse() -> void:
	for x in range(-84, 90, 12):
		for z in [-7.4, 7.4]:
			Shapes.box(self, Vector3(x, 2.7, z), Vector3(0.35, 5.4, 0.35), chalk, true)
	for x in [-39.0, 33.0]:
		Shapes.cylinder(self, Vector3(x, 0.35, 0), 1.45, 0.7, stone)
		_tree(Vector3(x, 0.7, 0))
	# Properly directed hanging wayfinding at junctions.
	_direction_sign(Vector3(-65, 3.6, 0), "お手洗い　→\nフードコート　直進", -PI / 2)
	_direction_sign(Vector3(57, 3.6, 0), "←　フードコート\n北側連絡通路", -PI / 2)
	_direction_sign(Vector3(72, 3.6, -29), "フードコート\nお食事・休憩", 0)
	_direction_sign(Vector3(-73, 3.1, 25), "お手洗い\n洗面・個室", PI)
	for x in range(-39, 73, 14):
		Shapes.box(self, Vector3(x, 4.5, -32), Vector3(3, 0.06, 0.2), warm)
	Shapes.box(self, Vector3(16, 5.0, -32), Vector3(127, 0.15, 8), chalk)
	_direction_sign(Vector3(0, 3.3, -32), "フードコート　→\n←　ショッピングエリア", 0)
	Shapes.sign_text(self, Vector3(-89.7, 2.5, 0), "FIND YOURSELF\nA館 / 中央入口", 80).rotation.y = PI / 2

func _direction_sign(at: Vector3, text: String, angle: float) -> void:
	var node := Node3D.new()
	add_child(node)
	node.position = at
	node.rotation.y = angle
	Shapes.box(node, Vector3.ZERO, Vector3(5, 1.05, 0.12), dark)
	Shapes.sign_text(node, Vector3(0, 0, 0.08), text, 42)

func _build_shops() -> void:
	var names := ["紙とことば", "SILHOUETTE", "STEP", "常緑生活", "AKARI", "喫茶 ひと休み", "ROOM & FORM", "暮らしの道具", "FIELD"]
	var colors := [Color("967356"), Color("63796a"), Color("777e8c")]
	for side in [-1, 1]:
		for index in SHOP_CENTERS.size():
			var x: float = SHOP_CENTERS[index]
			if not has_shop(x, side):
				continue
			var facade := Shapes.material(colors[index % colors.size()])
			Shapes.box(self, Vector3(x, 4.25, side * 8.5), Vector3(17.8, 0.9, 0.25), facade)
			var text := Shapes.sign_text(self, Vector3(x, 4.25, side * 8.31), names[index], 53)
			if side > 0:
				text.rotation.y = PI
			for wall_x in [x - 9, x + 9]:
				Shapes.box(self, Vector3(wall_x, 2.4, side * 16.4), Vector3(0.25, 4.8, 15.2), chalk, true)
			Shapes.box(self, Vector3(x, 4.95, side * 16), Vector3(18, 0.15, 16), chalk)
			# Cash desk and a staff member behind it.
			Shapes.box(self, Vector3(x + 3, 0.58, side * 18), Vector3(3, 1.16, 1.3), wood, true)
			Shapes.box(self, Vector3(x + 3, 1.28, side * 18), Vector3(0.5, 0.25, 0.35), dark)
			identity_slots.append({"pos": Vector3(x + 3, 0, side * 20), "yaw": 0.0 if side > 0 else PI, "role": "staff"})
			identity_slots.append({"pos": Vector3(x - 3, 0, side * 19.5), "yaw": PI if side > 0 else 0.0, "role": "browsing"})
			# Collision envelopes match the category-specific furniture.
			Shapes.box(self, Vector3(x - 1.5, 0.65, side * 21.85), Vector3(12, 1.3, 1.3), Shapes.material(Color(0,0,0,0)), true).visible = false
			MallFitout.new().build(self,x,side,index)
			_build_frontage(x,side,index)
			var light := OmniLight3D.new()
			add_child(light)
			light.position = Vector3(x, 3.4, side * 16)
			light.light_color = Color("ffdfbc")
			light.light_energy = 0.65
			light.omni_range = 11

func _build_food_court() -> void:
	for x in [53.0, 67.0, 81.0]:
		for z in [-39.0, -47.0, -54.0]:
			Shapes.box(self, Vector3(x, 0.78, z), Vector3(2.6, 0.1, 1.4), wood, true)
			Shapes.cylinder(self, Vector3(x, 0.35, z), 0.15, 0.7, stone)
			for offset in [Vector2(-1.9, 0), Vector2(1.9, 0), Vector2(0, -1.6), Vector2(0, 1.6)]:
				var p := Vector3(x + offset.x, 0, z + offset.y)
				var yaw := atan2(-(-offset.x), -(-offset.y))
				_chair(p, yaw)
				if _seated_slot_count() < 32:
					identity_slots.append({"pos": p, "yaw": yaw, "role": "seated"})
				var tray := Shapes.box(self, Vector3(x + offset.x * 0.38, 0.85, z + offset.y * 0.35), Vector3(0.5, 0.025, 0.35), dark)
				tray.rotation.y = yaw
				Shapes.cylinder(self, tray.position + Vector3(0.1, 0.08, 0), 0.055, 0.14, chalk)
	Shapes.box(self, Vector3(69, 4.9, -47), Vector3(46, 0.15, 30), chalk)
	var menus := ["うどん・そば", "定食・ごはん", "カレー", "飲みもの"]
	for index in 4:
		var x: float = [51.0, 62.0, 73.0, 84.0][index]
		Shapes.box(self, Vector3(x, 0.5, -59.5), Vector3(9, 1, 1), wood, true)
		Shapes.box(self, Vector3(x, 2.9, -61.7), Vector3(9, 1.0, 0.15), dark)
		Shapes.sign_text(self, Vector3(x, 2.9, -61.58), menus[index], 64)
		identity_slots.append({"pos": Vector3(x, 0, -61), "yaw": PI, "role": "staff"})
		for offset in [-2.0, 0.0, 2.0]:
			Shapes.cylinder(self, Vector3(x + offset, 1.06, -59.4), 0.24, 0.08, chalk)
	for x in [53.0, 67.0, 81.0]:
		Shapes.box(self, Vector3(x, 4.55, -47), Vector3(8, 0.07, 0.25), warm)
		var light := OmniLight3D.new()
		add_child(light)
		light.position = Vector3(x, 3.6, -47)
		light.light_energy = 1.0
		light.omni_range = 15

func _seated_slot_count() -> int:
	var count := 0
	for slot in identity_slots:
		if slot.role == "seated":
			count += 1
	return count

func _chair(at: Vector3, yaw: float) -> void:
	var chair := Node3D.new()
	add_child(chair)
	chair.position = at
	chair.rotation.y = yaw
	Shapes.box(chair, Vector3(0, 0.47, 0), Vector3(0.6, 0.1, 0.6), wood, true)
	Shapes.box(chair, Vector3(0, 0.85, 0.27), Vector3(0.6, 0.7, 0.07), wood)
	for x in [-0.23, 0.23]:
		for z in [-0.23, 0.23]:
			Shapes.box(chair, Vector3(x, 0.22, z), Vector3(0.04, 0.44, 0.04), dark)

func _build_restroom() -> void:
	Shapes.box(self, Vector3(-88.25, 0.45, 46), Vector3(1.5, 0.9, 14), stone, true)
	for z in [40.5, 45.0, 49.5]:
		Shapes.sphere(self, Vector3(-88, 0.94, z), 0.35, chalk).scale.y = 0.15
		Shapes.box(self, Vector3(-88.4, 1.04, z), Vector3(0.1, 0.22, 0.06), dark)
		Shapes.box(self, Vector3(-89.75, 1.75, z), Vector3(0.04, 0.9, 1.7), Shapes.material(Color("8aadb5")))
		identity_slots.append({"pos": Vector3(-86.3, 0, z), "yaw": PI / 2, "role": "restroom"})
	for x in [-67.0, -62.0, -57.0]:
		Shapes.box(self, Vector3(x, 1.2, 50.5), Vector3(0.25, 2.4, 9), wood, true)
		identity_slots.append({"pos": Vector3(x - 1.6, 0, 42), "yaw": 0.0, "role": "restroom"})
		Shapes.cylinder(self, Vector3(x - 2.1, 0.27, 52.2), 0.3, 0.54, chalk)
		Shapes.box(self, Vector3(x - 2.1, 0.65, 54.4), Vector3(0.65, 0.9, 0.3), chalk)
		Shapes.sign_text(self, Vector3(x - 2.1, 2.6, 46.1), "個室", 32).rotation.y = PI
	Shapes.box(self, Vector3(-71, 4.9, 41), Vector3(38, 0.15, 30), chalk)
	Shapes.sign_text(self, Vector3(-71, 3.4, 55.7), "お手洗い", 90).rotation.y = PI
	for z in [31.0, 43.0, 51.0]:
		Shapes.box(self, Vector3(-72, 4.5, z), Vector3(13, 0.07, 0.2), warm)
		var light := OmniLight3D.new()
		add_child(light)
		light.position = Vector3(-72, 3.5, z)
		light.light_energy = 0.8
		light.omni_range = 13

func _build_conversations() -> void:
	for x in [-63.0, -45.0, -27.0, -9.0, 9.0, 27.0, 45.0, 63.0]:
		for offset in [-0.8, 0.8]:
			identity_slots.append({"pos": Vector3(x + offset, 0, 4.0), "yaw": -PI / 2 if offset < 0 else PI / 2, "role": "conversation"})

func _tree(p: Vector3) -> void:
	Shapes.cylinder(self, p + Vector3(0, 1.3, 0), 0.12, 2.6, wood)
	var leaves := MultiMesh.new()
	leaves.transform_format = MultiMesh.TRANSFORM_3D
	leaves.use_colors = true
	var mesh := SphereMesh.new()
	mesh.radius = 0.65
	mesh.height = 1.3
	mesh.radial_segments = 12
	mesh.rings = 6
	var material := Shapes.material(Color("456d42"))
	material.vertex_color_use_as_albedo = true
	mesh.material = material
	leaves.mesh = mesh
	leaves.instance_count = 34
	var random := RandomNumberGenerator.new()
	random.seed = 7919
	for i in 34:
		var angle := random.randf_range(0, TAU)
		var radius := random.randf_range(0, 1.15)
		var at := p + Vector3(cos(angle) * radius, random.randf_range(2.7, 4.1), sin(angle) * radius)
		leaves.set_instance_transform(i, Transform3D(Basis().scaled(Vector3(1, 0.7, 0.8) * random.randf_range(0.6, 1.15)), at))
		leaves.set_instance_color(i, Color.WHITE * random.randf_range(0.8, 1.15))
	var canopy := MultiMeshInstance3D.new()
	canopy.multimesh = leaves
	add_child(canopy)

func _glass() -> StandardMaterial3D:
	var material := Shapes.material(Color(.64,.79,.82,.18))
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.roughness = .12
	material.metallic = .2
	return material

func _build_frontage(x: float, side: int, kind: int) -> void:
	var glass := _glass()
	var frame := Shapes.material(Color("454b4b"))
	for dx in [-6.0,6.0]:
		Shapes.box(self,Vector3(x+dx,1.9,side*8.5),Vector3(6,3.8,.12),glass,true)
		for edge in [-3.0,0.0,3.0]:
			Shapes.box(self,Vector3(x+dx+edge,1.9,side*8.5),Vector3(.045,3.8,.16),frame)
		Shapes.box(self,Vector3(x+dx,.18,side*8.5),Vector3(6,.36,.18),stone)
	Shapes.box(self,Vector3(x,2.4,side*23.6),Vector3(18,4.8,.24),chalk,true)
	for dx in [-4.5,4.5]:
		var collision := Shapes.box(self,Vector3(x+dx,.65,side*13.5),Vector3(2,1.3,2.8),chalk,true)
		collision.visible = false
	# Recessed soffit and an unambiguous open entry between the display windows.
	Shapes.box(self,Vector3(x,3.82,side*8.5),Vector3(17.9,.12,.7),frame)
	Shapes.box(self,Vector3(x,3.74,side*8.8),Vector3(5.7,.035,.10),warm)
	var tenant := Shapes.sign_text(self,Vector3(x,2.9,side*23.42),["BOOKS & STATIONERY","FITTING ROOM","SHOES & BAGS","HOME GOODS","DIGITAL LIFE","COFFEE & TEA","LIVING","DAILY GOODS","SPORTS"][kind],32,Color("454c48"))
	if side > 0: tenant.rotation.y = PI

func _build_architecture() -> void:
	var ivory := Shapes.material(Color("e4dfd4"))
	var bronze := Shapes.material(Color("77634e"))
	var light := Shapes.material(Color("fff1d9"),1.1)
	var glass := _glass()
	# A covered two-storey concourse with a central skylight and upper galleries.
	# Galleries are architectural scenery in the current one-floor development slice.
	for side in [-1,1]:
		Shapes.box(self,Vector3(0,5.35,side*6.5),Vector3(180,.35,3.0),ivory)
		Shapes.box(self,Vector3(0,5.1,side*5),Vector3(180,.18,.16),bronze)
		Shapes.box(self,Vector3(0,5.0,side*5.1),Vector3(178,.035,.06),light)
		Shapes.box(self,Vector3(0,6.0,side*4.95),Vector3(180,1.05,.045),glass)
		Shapes.box(self,Vector3(0,6.56,side*4.95),Vector3(180,.045,.055),bronze)
		Shapes.box(self,Vector3(0,7.5,side*8),Vector3(180,4,.28),ivory)
		Shapes.box(self,Vector3(0,10.4,side*5.5),Vector3(180,.24,5),ivory)
		for x in range(-84,90,12):
			Shapes.box(self,Vector3(x,6.0,side*4.95),Vector3(.045,1.15,.07),bronze)
			Shapes.box(self,Vector3(x,7.55,side*7.8),Vector3(8,2.2,.06),Shapes.material(Color("acb6b5")))
			Shapes.box(self,Vector3(x,10.1,side*5.5),Vector3(6,.035,.18),light)
	# Roof glazing is held by structural ribs; the hall no longer opens into the sky.
	Shapes.box(self,Vector3(0,10.55,0),Vector3(180,.08,6),Shapes.material(Color("b4cbd0"),.18))
	for x in range(-90,91,6):
		Shapes.box(self,Vector3(x,10.3,0),Vector3(.12,.38,16),ivory)
	for z in [-3.0,0.0,3.0]:
		Shapes.box(self,Vector3(0,10.4,z),Vector3(180,.12,.1),bronze)
	# Covered junctions keep indoor circulation enclosed between the larger rooms.
	Shapes.box(self,Vector3(-73,4.95,18.5),Vector3(12,.18,23),ivory)
	Shapes.box(self,Vector3(70,4.95,-24.5),Vector3(20,.18,35),ivory)
	for x in [-90.0,90.0]:
		Shapes.box(self,Vector3(x,7.8,0),Vector3(.30,5.2,16),ivory)
		Shapes.box(self,Vector3(x*.998,7.6,0),Vector3(.04,3.5,11),Shapes.material(Color("aabec2")))
	# Floor inlays clarify circulation, junctions and the connection to the dining wing.
	for side in [-1,1]:
		Shapes.box(self,Vector3(0,.018,side*4.7),Vector3(179,.025,.18),bronze)
		for x in [-57.0,-21.0,15.0,51.0]:
			Shapes.box(self,Vector3(x,.38,side*3.4),Vector3(3,.45,.62),wood,true)
			for dx in [-1.1,1.1]:
				Shapes.box(self,Vector3(x+dx,.17,side*3.4),Vector3(.12,.34,.5),stone)
	# A continuous, finished loop behind the north retail row.
	for z in [-35.8]:
		Shapes.box(self,Vector3(16,2.3,z),Vector3(127,4.6,.16),ivory, z < -35)
		Shapes.box(self,Vector3(16,.15,z),Vector3(127,.3,.20),stone)
	for x in range(-39,74,14):
		Shapes.box(self,Vector3(x,4.84,-32),Vector3(4,.04,.32),light)
	# A planted exterior court is visible through the food court's glazed east wall.
	Shapes.box(self,Vector3(105,-.1,-47),Vector3(26,.2,40),Shapes.material(Color("788569")))
	for z in [-59.0,-48.0,-37.0]:
		_tree(Vector3(102,0,z))
	# Dining identity: acoustic ceiling rafts, slats and a lit tenant fascia.
	for x in [53.0,67.0,81.0]:
		Shapes.box(self,Vector3(x,4.65,-47),Vector3(9,.18,21),Shapes.material(Color("b39572")))
		for dx in [-3.0,0.0,3.0]:
			Shapes.box(self,Vector3(x+dx,4.52,-47),Vector3(.10,.12,20),wood)
		Shapes.box(self,Vector3(x,4.40,-47),Vector3(6,.04,.18),light)
	Shapes.box(self,Vector3(69,3.9,-59.6),Vector3(45,.55,.2),wood)
	for x in [51.0,62.0,73.0,84.0]:
		Shapes.box(self,Vector3(x,1.8,-61.8),Vector3(8,.8,.15),Shapes.material(Color("8e9690")))
		Shapes.box(self,Vector3(x,2.25,-59.7),Vector3(8,.1,1.5),stone)
		for dx in [-2.4,0,2.4]:
			Shapes.box(self,Vector3(x+dx,3.45,-61.5),Vector3(2.1,.75,.08),Shapes.material(Color("e1d5b7"),.1))
	# Public information kiosk and distinct court signage.
	Shapes.box(self,Vector3(-82,1.1,-5.7),Vector3(1.5,2.2,.2),dark)
	Shapes.sign_text(self,Vector3(-82,1.45,-5.55),"A館  1F\n館内案内\n食品・生活・ファッション",24)

func _build_market() -> void:
	var white := Shapes.material(Color("e8e5da"))
	var green := Shapes.material(Color("344d40"))
	Shapes.box(self,Vector3(24,.015,28),Vector3(35.7,.025,39.5),Shapes.material(Color("cfccc0")))
	Shapes.box(self,Vector3(24,4.0,8.4),Vector3(36,1,.28),green)
	Shapes.sign_text(self,Vector3(24,4.0,8.2),"LIFE MARKET  /  食品スーパー",50).rotation.y = PI
	for fixture in [Rect2(6,8.3,3,.24),Rect2(15,8.3,18,.24),Rect2(39,8.3,3,.24)]:
		Shapes.box(self,Vector3(fixture.get_center().x,1.7,8.4),Vector3(fixture.size.x,3.4,.18),_glass(),true)
	var label_transforms: Array[Array] = [[],[],[],[]]
	for x in [12.0,22.0,32.0]:
		for z in [23.0,35.0]:
			var collider := Shapes.box(self,Vector3(x,.8,z),Vector3(2.4,1.6,7),white,true)
			collider.visible = false
			Shapes.box(self,Vector3(x,.8,z),Vector3(.14,1.6,7),white)
			Shapes.box(self,Vector3(x,.08,z),Vector3(2.4,.16,7),white)
			for side in [-1,1]:
				for tier in 3:
					Shapes.box(self,Vector3(x+side*1.0,.4+tier*.48,z),Vector3(.5,.045,7),wood)
					for item in 9:
						var color := Color.from_hsv(fmod(item*.17+tier*.2,1),.4,.65)
						Shapes.box(self,Vector3(x+side*1.02,.55+tier*.48,z-2.8+item*.7),Vector3(.3,.25,.33),Shapes.material(color))
						label_transforms[(item+tier)%4].append(Transform3D(Basis(Vector3.UP,side*PI/2),Vector3(x+side*1.174,.55+tier*.48,z-2.8+item*.7)))
			Shapes.sign_text(self,Vector3(x,2.6,z),"%02d  /  食品・日用品" % int(x),28).rotation.y = PI
	# Package artwork is instanced in four batches, rather than one decal draw per item.
	for variant in 4:
		var mesh := QuadMesh.new()
		mesh.size = Vector2(.26,.21)
		var material := Shapes.material(Color.WHITE)
		material.albedo_texture = load("res://assets/products/label%d.png" % variant)
		mesh.material = material
		var instances := MultiMesh.new()
		instances.transform_format = MultiMesh.TRANSFORM_3D
		instances.mesh = mesh
		instances.instance_count = label_transforms[variant].size()
		for index in instances.instance_count:
			instances.set_instance_transform(index,label_transforms[variant][index])
		var node := MultiMeshInstance3D.new()
		node.multimesh = instances
		add_child(node)
	for x in [12.0,36.0]:
		Shapes.box(self,Vector3(x,.56,13.15),Vector3(3,1.12,1.3),green,true)
		Shapes.box(self,Vector3(x,1.18,13.15),Vector3(3.1,.08,1.4),dark)
		Shapes.box(self,Vector3(x+.6,1.43,13.15),Vector3(.4,.4,.08),dark)
		identity_slots.append({"pos":Vector3(x,0,15.3),"yaw":0.0,"role":"staff"})
	for x in [17.0,27.0]:
		for z in [24.0,35.0]:
			identity_slots.append({"pos":Vector3(x,0,z),"yaw":PI/2,"role":"browsing"})
	Shapes.box(self,Vector3(24,4.65,28),Vector3(36,.2,40),white)
	for x in [12.0,24.0,36.0]:
		for z in [17.0,29.0,41.0]:
			Shapes.box(self,Vector3(x,4.5,z),Vector3(5,.04,.24),warm)
		var light := OmniLight3D.new()
		add_child(light)
		light.position = Vector3(x,3.4,28)
		light.light_energy = .85
		light.omni_range = 21
	Shapes.sign_text(self,Vector3(24,3.0,47.7),"毎日の食卓に  /  FOOD & DAILY",46,Color("344d40"))
