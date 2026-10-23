class_name Crowd
extends Node3D
## Shared meshes and a walkable grid keep identity data separate from visuals.
## Instancing reduces the crowd to a handful of mesh submissions.

var positions: Array[Vector3] = []
var headings: Array[float] = []
var paths: Array[PackedVector3Array] = []
var waits: Array[float] = []
var death_times: Array[float] = []
var bodies: Array[Area3D] = []
var parts: Array[Dictionary] = []
var clock := 0.0
var nav := AStar3D.new()
var nav_ids: Array[int] = []
var rng := RandomNumberGenerator.new()
var run: IdentityRun
var skin_color := Color("cfaa89")
var hair_color := Color("33312c")
var face_width := 1.0
var roles: Array[String] = []
var slots: Array[Dictionary] = []

func setup(state: IdentityRun, points: Array[Vector3]) -> void:
	run = state
	rng.randomize()
	for i in points.size():
		nav.add_point(i, points[i])
		nav_ids.append(i)
	var lookup: Dictionary = {}
	for i in points.size():
		lookup[Vector2i(roundi(points[i].x), roundi(points[i].z))] = i
	for i in points.size():
		var cell := Vector2i(roundi(points[i].x), roundi(points[i].z))
		for offset in [Vector2i(2, 0), Vector2i(0, 2)]:
			if lookup.has(cell + offset):
				var other: int = lookup[cell + offset]
				if Mall.walkable((points[i] + points[other]) / 2):
					nav.connect_points(i, other)
	var palette := [Color("c58a6b"), Color("bcc6b3"), Color("667e8a"), Color("d8c497"), Color("a78b91"), Color("4d6265")]
	for id in run.population:
		var p := points[rng.randi_range(0, points.size() - 1)]
		var heading := rng.randf_range(-PI, PI)
		var role := "walking"
		if id < slots.size():
			p = slots[id].pos
			heading = slots[id].yaw
			role = slots[id].role
		roles.append(role)
		positions.append(p)
		headings.append(heading)
		paths.append(PackedVector3Array())
		waits.append(rng.randf_range(0, 6))
		death_times.append(-1.0)
		var area := Area3D.new()
		area.collision_layer = 2
		area.collision_mask = 0
		area.monitoring = false
		area.set_meta("identity", id)
		var collision := CollisionShape3D.new()
		var capsule := CapsuleShape3D.new()
		capsule.radius = 0.32
		capsule.height = 1.9 if role != "seated" else 1.4
		collision.shape = capsule
		area.add_child(collision)
		add_child(area)
		area.position = p + Vector3.UP * (0.95 if role != "seated" else 0.7)
		bodies.append(area)
	_add_part("torso", Vector3(0, 1.13, 0), Vector3(0.5, 0.69, 0.31), Color.WHITE, palette)
	_add_part("leg_l", Vector3(-0.12, 0.62, 0), Vector3(0.19, 0.42, 0.2), Color("34434a"))
	_add_part("leg_r", Vector3(0.12, 0.62, 0), Vector3(0.19, 0.42, 0.2), Color("34434a"))
	_add_part("shin_l", Vector3(-0.12, 0.22, 0), Vector3(0.17, 0.44, 0.18), Color("34434a"))
	_add_part("shin_r", Vector3(0.12, 0.22, 0), Vector3(0.17, 0.44, 0.18), Color("34434a"))
	_add_part("arm_l", Vector3(-0.275, 1.27, 0), Vector3(0.155, 0.31, 0.17), Color.WHITE, palette)
	_add_part("arm_r", Vector3(0.275, 1.27, 0), Vector3(0.155, 0.31, 0.17), Color.WHITE, palette)
	_add_part("forearm_l", Vector3(-.275, .98, 0), Vector3(.125, .29, .14), Color.WHITE, palette)
	_add_part("forearm_r", Vector3(.275, .98, 0), Vector3(.125, .29, .14), Color.WHITE, palette)
	_add_part("hand_l", Vector3(-0.275, 0.79, 0), Vector3(0.09, 0.15, 0.075), skin_color)
	_add_part("hand_r", Vector3(0.275, 0.79, 0), Vector3(0.09, 0.15, 0.075), skin_color)
	_add_part("shoe_l", Vector3(-0.12, 0.08, -0.035), Vector3(0.14, 0.12, 0.28), Color("222a2c"))
	_add_part("shoe_r", Vector3(0.12, 0.08, -0.035), Vector3(0.14, 0.12, 0.28), Color("222a2c"))
	_add_part("neck", Vector3(0, 1.52, 0), Vector3(0.12, 0.16, 0.12), skin_color)
	_add_part("head", Vector3(0, 1.7, 0), Vector3(0.205 * face_width, 0.28, 0.22), skin_color)
	_add_part("hair", Vector3(0, 1.81, 0.015), Vector3(0.22 * face_width, 0.12, 0.23), hair_color)
	_add_part("ear_l", Vector3(-0.103 * face_width, 1.715, 0), Vector3(0.027, 0.05, 0.03), skin_color)
	_add_part("ear_r", Vector3(0.103 * face_width, 1.715, 0), Vector3(0.027, 0.05, 0.03), skin_color)
	_add_part("eye_l", Vector3(-0.04 * face_width, 1.73, -0.111), Vector3(0.039, 0.018, 0.012), Color("e5e0d5"))
	_add_part("eye_r", Vector3(0.04 * face_width, 1.73, -0.111), Vector3(0.039, 0.018, 0.012), Color("e5e0d5"))
	_add_part("pupil_l", Vector3(-0.04 * face_width, 1.73, -0.122), Vector3(0.014, 0.015, 0.006), Color("333c38"))
	_add_part("pupil_r", Vector3(0.04 * face_width, 1.73, -0.122), Vector3(0.014, 0.015, 0.006), Color("333c38"))
	_add_part("brow_l", Vector3(-0.04 * face_width, 1.753, -0.112), Vector3(0.035, 0.005, 0.01), hair_color)
	_add_part("brow_r", Vector3(0.04 * face_width, 1.753, -0.112), Vector3(0.035, 0.005, 0.01), hair_color)
	_add_part("nose", Vector3(0, 1.697, -0.124), Vector3(0.027, 0.045, 0.035), skin_color.darkened(0.05))
	_add_part("mouth", Vector3(0, 1.653, -0.100), Vector3(0.041, 0.006, 0.01), skin_color.darkened(0.28))
	_add_part("apron", Vector3(0, 1.02, -0.165), Vector3(0.34, 0.45, 0.02), Color("293d36"))
	_add_part("badge", Vector3(0.14, 1.32, -0.16), Vector3(0.08, 0.04, 0.015), Color("e8e3d3"))
	_add_part("shirt", Vector3(0, 1.36, -0.145), Vector3(.16, .19, .025), Color("e3ded1"))
	_add_part("collar_l", Vector3(-.07, 1.43, -.16), Vector3(.09, .065, .035), Color("f0ebdf"))
	_add_part("collar_r", Vector3(.07, 1.43, -.16), Vector3(.09, .065, .035), Color("f0ebdf"))
	_add_part("belt", Vector3(0, .84, -.015), Vector3(.32, .038, .23), Color("252c30"))
	for index in 3:
		_add_part("button%d" % index, Vector3(.025, 1.24 - index * .11, -.155), Vector3(.012, .012, .009), Color("262c31"))
	for index in 5:
		_add_part("fringe%d" % index, Vector3((index - 2) * .039 * face_width, 1.793 - (index % 2) * .019, -.085), Vector3(.06, .09 + (index % 2) * .025, .065), hair_color)
	_add_part("sideburn_l", Vector3(-.098 * face_width, 1.75, -.005), Vector3(.028, .09, .1), hair_color)
	_add_part("sideburn_r", Vector3(.098 * face_width, 1.75, -.005), Vector3(.028, .09, .1), hair_color)
	_render()

func _add_part(title: String, offset: Vector3, size: Vector3, color: Color, palette: Array = []) -> void:
	var mesh: Mesh
	var instance_scale := size
	if title == "torso":
		mesh = HumanMesh.torso()
	elif title == "head":
		mesh = HumanMesh.face()
	elif title in ["arm_l", "arm_r", "forearm_l", "forearm_r", "leg_l", "leg_r", "shin_l", "shin_r"]:
		mesh = HumanMesh.limb()
	elif title in ["apron", "badge", "shirt", "collar_l", "collar_r", "belt"]:
		var box := BoxMesh.new()
		box.size = Vector3.ONE
		mesh = box
	else:
		var sphere := SphereMesh.new()
		sphere.radius = 0.5
		sphere.height = 1.0
		sphere.radial_segments = 16
		sphere.rings = 8
		mesh = sphere
	var mat := Shapes.material(color)
	mat.vertex_color_use_as_albedo = true
	mat.diffuse_mode = BaseMaterial3D.DIFFUSE_TOON
	mat.roughness = 0.9
	if mesh is ArrayMesh:
		mesh.surface_set_material(0, mat)
	else:
		mesh.set("material", mat)
	var instances := MultiMesh.new()
	instances.transform_format = MultiMesh.TRANSFORM_3D
	instances.use_colors = true
	# Explicit sector bounds avoid camera-near clipping of animated instance groups.
	instances.custom_aabb = AABB(Vector3(-100, -8, -72), Vector3(200, 20, 140))
	instances.mesh = mesh
	instances.instance_count = run.population
	for id in run.population:
		instances.set_instance_color(id, palette[id % palette.size()] if not palette.is_empty() else Color.WHITE)
	var node := MultiMeshInstance3D.new()
	node.multimesh = instances
	add_child(node)
	parts.append({"name": title, "offset": offset, "scale": instance_scale, "instances": instances})

func _physics_process(delta: float) -> void:
	if run == null:
		return
	clock += delta
	for id in run.population:
		if death_times[id] >= 0:
			death_times[id] += delta
			continue
		if roles[id] != "walking":
			continue
		waits[id] -= delta
		if waits[id] > 0:
			continue
		if paths[id].is_empty():
			var start := nav.get_closest_point(positions[id])
			var goal: int = nav_ids[rng.randi_range(0, nav_ids.size() - 1)]
			paths[id] = nav.get_point_path(start, goal)
			if not paths[id].is_empty():
				paths[id].remove_at(0)
			continue
		var difference := paths[id][0] - positions[id]
		var speed := 0.75 + (id % 7) * 0.07
		if difference.length() < speed * delta + 0.05:
			positions[id] = paths[id][0]
			paths[id].remove_at(0)
			if paths[id].is_empty():
				waits[id] = rng.randf_range(3.0, 10.0)
		else:
			positions[id] += difference.normalized() * speed * delta
			headings[id] = lerp_angle(headings[id], atan2(-difference.x, -difference.z), minf(1.0, delta * 6))
		bodies[id].position = positions[id] + Vector3.UP * 0.95
	_render()

func _render() -> void:
	for part in parts:
		var instances: MultiMesh = part.instances
		for id in run.population:
			if death_times[id] > 0.8 or (part.name in ["apron", "badge"] and roles[id] != "staff"):
				instances.set_instance_transform(id, Transform3D(Basis().scaled(Vector3.ZERO), Vector3(0, -20, 0)))
				continue
			var local_offset: Vector3 = part.offset
			var pose := Basis.IDENTITY
			if roles[id] == "seated":
				if part.name in ["leg_l", "leg_r"]:
					local_offset.y = 0.91
					local_offset.z = -0.2
					pose = Basis(Vector3.RIGHT, -PI / 2)
				elif part.name in ["shin_l", "shin_r"]:
					local_offset.y = 0.65
					local_offset.z = -0.4
				elif part.name in ["shoe_l", "shoe_r"]:
					local_offset.y = 0.49
					local_offset.z = -0.47
				elif part.name in ["arm_l", "arm_r"]:
					local_offset.y = 1.28
					local_offset.z = -.08
					pose = Basis(Vector3.RIGHT, -.5)
				elif part.name in ["forearm_l", "forearm_r"]:
					local_offset.y = 1.15
					local_offset.z = -.27
					pose = Basis(Vector3.RIGHT, -PI / 2)
				elif part.name in ["hand_l", "hand_r"]:
					local_offset.y = 1.15 + sin(clock * 0.8 + id) * 0.025
					local_offset.z = -0.46
			elif roles[id] == "conversation" and part.name == "arm_r":
				pose = Basis(Vector3.RIGHT, sin(clock * 0.9 + id) * 0.22 - 0.12)
			if roles[id] == "walking" and waits[id] <= 0 and death_times[id] < 0 and not paths[id].is_empty():
				var phase := clock * 5.5 + id
				var left: bool = part.name.ends_with("_l")
				var swing := sin(phase + (0 if left else PI)) * .35
				if part.name.begins_with("leg_"):
					pose = Basis(Vector3.RIGHT, swing)
					local_offset = Vector3(local_offset.x, .83, 0) + pose * Vector3(0, -.21, 0)
				elif part.name.begins_with("shin_") or part.name.begins_with("shoe_"):
					var hip := Basis(Vector3.RIGHT, swing)
					var knee := maxf(0, -sin(phase + (0 if left else PI))) * .65
					pose = hip * Basis(Vector3.RIGHT, -knee)
					local_offset = Vector3(local_offset.x, .83, 0) + hip * Vector3(0, -.42, 0) + pose * Vector3(0, -.19 if part.name.begins_with("shin_") else -.33, -.035 if part.name.begins_with("shoe_") else 0)
				elif part.name.begins_with("arm_") or part.name.begins_with("forearm_") or part.name.begins_with("hand_"):
					pose = Basis(Vector3.RIGHT, -swing * .7)
					local_offset = Vector3(local_offset.x, 1.42, 0) + pose * Vector3(0, -.15 if part.name.begins_with("arm_") else (-.44 if part.name.begins_with("forearm_") else -.63), 0)
			var base := positions[id]
			if roles[id] == "seated":
				base.y -= 0.42
			if death_times[id] >= 0:
				base.y -= pow(death_times[id] / 0.8, 2) * 4.0
			var basis := Basis(Vector3.UP, headings[id])
			instances.set_instance_transform(id, Transform3D((basis * pose).scaled_local(part.scale), base + basis * local_offset))

func fall(id: int) -> void:
	death_times[id] = 0
	bodies[id].collision_layer = 0
	bodies[id].position.y = -20

func live_positions_in_radius(center: Vector3, radius: float) -> Array[int]:
	var found: Array[int] = []
	for id in run.population:
		if not run.eliminated[id] and positions[id].distance_squared_to(center) <= radius * radius:
			found.append(id)
	return found
