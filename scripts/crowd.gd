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
		# Leave the entrance clear.
		if p.distance_to(Vector3(0, 0, 12)) < 3:
			p = Vector3(11, 0, 7)
		positions.append(p)
		headings.append(rng.randf_range(-PI, PI))
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
		capsule.height = 1.9
		collision.shape = capsule
		area.add_child(collision)
		add_child(area)
		area.position = p + Vector3.UP * 0.95
		bodies.append(area)
	_add_part("torso", Vector3(0, 1.12, 0), Vector3(0.54, 0.72, 0.32), Color.WHITE, palette)
	_add_part("leg_l", Vector3(-0.14, 0.4, 0), Vector3(0.19, 0.8, 0.22), Color("34434a"))
	_add_part("leg_r", Vector3(0.14, 0.4, 0), Vector3(0.19, 0.8, 0.22), Color("34434a"))
	_add_part("arm_l", Vector3(-0.35, 1.06, 0), Vector3(0.15, 0.66, 0.18), Color.WHITE, palette)
	_add_part("arm_r", Vector3(0.35, 1.06, 0), Vector3(0.15, 0.66, 0.18), Color.WHITE, palette)
	_add_part("head", Vector3(0, 1.7, 0), Vector3(0.42 * face_width, 0.48, 0.4), skin_color)
	_add_part("hair", Vector3(0, 1.89, 0.02), Vector3(0.44 * face_width, 0.14, 0.42), hair_color)
	_add_part("eye_l", Vector3(-0.095 * face_width, 1.74, -0.207), Vector3(0.045, 0.035, 0.018), Color("253237"))
	_add_part("eye_r", Vector3(0.095 * face_width, 1.74, -0.207), Vector3(0.045, 0.035, 0.018), Color("253237"))
	_add_part("nose", Vector3(0, 1.66, -0.22), Vector3(0.07, 0.08, 0.06), skin_color.darkened(0.1))
	_render()

func _add_part(title: String, offset: Vector3, size: Vector3, color: Color, palette: Array = []) -> void:
	var mesh := BoxMesh.new()
	mesh.size = size
	var mat := Shapes.material(color)
	mat.vertex_color_use_as_albedo = true
	mesh.material = mat
	var instances := MultiMesh.new()
	instances.transform_format = MultiMesh.TRANSFORM_3D
	instances.use_colors = true
	instances.mesh = mesh
	instances.instance_count = run.population
	for id in run.population:
		instances.set_instance_color(id, palette[id % palette.size()] if not palette.is_empty() else Color.WHITE)
	var node := MultiMeshInstance3D.new()
	node.multimesh = instances
	add_child(node)
	parts.append({"name": title, "offset": offset, "instances": instances})

func _physics_process(delta: float) -> void:
	if run == null:
		return
	clock += delta
	for id in run.population:
		if death_times[id] >= 0:
			death_times[id] += delta
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
			if death_times[id] > 0.8:
				instances.set_instance_transform(id, Transform3D(Basis().scaled(Vector3.ZERO), Vector3(0, -20, 0)))
				continue
			var local_offset: Vector3 = part.offset
			if waits[id] <= 0 and death_times[id] < 0 and not paths[id].is_empty():
				var sway := sin(clock * 6 + id) * 0.12
				if part.name == "leg_l" or part.name == "arm_r":
					local_offset.z += sway
				elif part.name == "leg_r" or part.name == "arm_l":
					local_offset.z -= sway
			var base := positions[id]
			if death_times[id] >= 0:
				base.y -= pow(death_times[id] / 0.8, 2) * 4.0
			var basis := Basis(Vector3.UP, headings[id])
			instances.set_instance_transform(id, Transform3D(basis, base + basis * local_offset))

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
