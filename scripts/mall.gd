class_name Mall
extends Node3D
## Fictional, connected mall floor: long concourse, a second promenade,
## shop interiors, a food court and a restroom wing. Not a real-site replica.

const SHOP_CENTERS := [-75.0, -57.0, -39.0, -21.0, -3.0, 15.0, 33.0, 51.0, 69.0]
const MAIN := Rect2(-90, -8, 180, 16)
const FOOD := Rect2(46, -62, 46, 30)
const RESTROOM := Rect2(-90, 26, 38, 30)
const PROMENADE := Rect2(-47, -36, 127, 8)
const ENTRANCE := Vector3(-82, 0.1, 0)
static var floor_regions: Array[Rect2] = []
static var obstacles: Array[Rect2] = []
var spawn_points: Array[Vector3] = []
var identity_slots: Array[Dictionary] = []
var outline := PackedVector2Array()
var chalk := Shapes.material(Color("d8d6cf"))
var dark := Shapes.material(Color("25363d"))
var stone := Shapes.material(Color("88918d"))
var wood := Shapes.material(Color("967355"))
var warm := Shapes.material(Color("ffe5ba"), 0.8)

static func has_shop(x: float, side: int) -> bool:
	return not (side == -1 and x in [-39.0, 69.0]) and not (side == 1 and x == -75.0)

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
	for side in [-1, 1]:
		for x in SHOP_CENTERS:
			if not has_shop(x, side):
				continue
			floor_regions.append(Rect2(x - 9, -24 if side < 0 else 8, 18, 16))
			for wall_x in [x - 9, x + 9]:
				obstacles.append(Rect2(wall_x - 0.16, -24 if side < 0 else 8.8, 0.32, 15.2))
			obstacles.append(Rect2(x + 1.5, side * 18 - 0.65, 3, 1.3))
			obstacles.append(Rect2(x - 7.5, -22.5 if side < 0 else 21.2, 12, 1.3))
	for x in [53.0, 67.0, 81.0]:
		for z in [-39.0, -47.0, -54.0]:
			obstacles.append(Rect2(x - 1.3, z - 0.7, 2.6, 1.4))
			for d in [Vector2(-1.9, 0), Vector2(1.9, 0), Vector2(0, -1.6), Vector2(0, 1.6)]:
				obstacles.append(Rect2(Vector2(x, z) + d - Vector2(0.3, 0.3), Vector2(0.6, 0.6)))
	for x in [51.0, 62.0, 73.0, 84.0]:
		obstacles.append(Rect2(x - 4.5, -60, 9, 1))
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

static func zone_name(p: Vector3) -> String:
	var v := Vector2(p.x, p.z)
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
	_build_shops()
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
		Shapes.box(self, Vector3(middle.x, 2.6, middle.y), size, chalk, true)
		Shapes.box(self, Vector3(middle.x, 0.12, middle.y), Vector3(size.x + 0.04, 0.24, size.z + 0.04), stone)

func _build_concourse() -> void:
	for x in range(-84, 90, 12):
		Shapes.box(self, Vector3(x, 7.1, 0), Vector3(0.14, 0.24, 16), stone)
		for z in [-7.4, 7.4]:
			Shapes.box(self, Vector3(x, 2.7, z), Vector3(0.35, 5.4, 0.35), chalk, true)
	for z in [-7.5, 0.0, 7.5]:
		Shapes.box(self, Vector3(0, 7.1, z), Vector3(180, 0.16, 0.12), stone)
		Shapes.box(self, Vector3(0, 6.95, z), Vector3(176, 0.03, 0.045), warm)
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
	var names := ["書店 / 紙とことば", "服飾 / 静かな装い", "靴・かばん", "生活雑貨 / 常緑", "家電 / あかり", "喫茶 / ひと休み", "インテリア", "日用品 / 暮らし", "スポーツ用品"]
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
			Shapes.box(self, Vector3(x - 1.5, 0.7, side * 21.85), Vector3(12, 1.4, 1.3), wood, true)
			for row in range(9):
				Shapes.box(self, Vector3(x - 7 + row * 1.25, 1.62, side * 21.85), Vector3(0.7, 0.4, 0.45), facade)
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
