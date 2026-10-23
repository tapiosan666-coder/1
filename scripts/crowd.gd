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
				if Mall.segment_walkable(points[i], points[other]):
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
	var kit: Node3D = preload("res://assets/characters/civilian.glb").instantiate()
	var offsets := {"torso": Vector3(0,1.13,0), "head": Vector3(0,1.7,0), "hair": Vector3(0,1.81,0), "neck": Vector3(0,1.52,0)}
	for side in [-1, 1]:
		var suffix := "_l" if side < 0 else "_r"
		for item in [["arm",1.27], ["forearm",.98], ["hand",.79]]:
			offsets[item[0] + suffix] = Vector3(side * .255, item[1], 0)
		for item in [["leg",.62,0], ["shin",.22,0], ["shoe",.08,-.035]]:
			offsets[item[0] + suffix] = Vector3(side * .105, item[1], item[2])
	for node in kit.find_children("*", "MeshInstance3D", true, false):
		var title: String = node.name
		if not offsets.has(title):
			continue
		var mesh: Mesh = node.mesh.duplicate()
		for surface in mesh.get_surface_count():
			var material: StandardMaterial3D = mesh.surface_get_material(surface).duplicate()
			var tag := material.resource_name
			if tag.begins_with("Skin"):
				material.albedo_color = skin_color
			elif tag.begins_with("Hair"):
				material.albedo_color = hair_color
			elif tag.begins_with("Cloth"):
				material.albedo_color = Color.WHITE
				material.vertex_color_use_as_albedo = true
			material.roughness = .8
			mesh.surface_set_material(surface, material)
		var size := Vector3(face_width, 1, 1) if title in ["head", "hair"] else Vector3.ONE
		_instance_part(title, mesh, offsets[title], size, palette)
	kit.free()
	_add_part("apron", Vector3(0,1.00,-.132), Vector3(.29,.38,.018), Color("293d36"))
	_add_part("badge", Vector3(.13,1.32,-.128), Vector3(.065,.032,.01), Color("e8e3d3"))
	_render()

func _add_part(title: String, offset: Vector3, size: Vector3, color: Color, palette: Array = []) -> void:
	var mesh := BoxMesh.new()
	mesh.size = Vector3.ONE
	var instance_scale := size
	var mat := Shapes.material(color)
	mat.vertex_color_use_as_albedo = true
	mat.diffuse_mode = BaseMaterial3D.DIFFUSE_TOON
	mat.roughness = 0.9
	mesh.material = mat
	_instance_part(title, mesh, offset, instance_scale, palette)

func _instance_part(title: String, mesh: Mesh, offset: Vector3, instance_scale: Vector3, palette: Array) -> void:
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
