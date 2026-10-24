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
var activities: Array[String] = []
var frozen := false
var attraction_left := 0.0
var attracted: Dictionary = {}
var slots: Array[Dictionary] = []
static var cached_nav: AStar3D
static var cached_nav_hash := 0
static var cached_nav_ids: Array[int] = []
var floor_nav_ids: Dictionary = {-1:[],0:[],1:[],2:[],3:[]}

func setup(state: IdentityRun, points: Array[Vector3]) -> void:
	run = state
	rng.randomize()
	var key := hash(points)
	if cached_nav != null and cached_nav_hash == key:
		nav = cached_nav
		nav_ids = cached_nav_ids
	else:
		for i in points.size():
			nav.add_point(i, points[i])
			nav_ids.append(i)
		var lookup: Dictionary = {}
		for i in points.size():
			lookup[Vector3i(roundi(MallCurve.plan(points[i]).x), Mall.level_at(points[i].y), roundi(MallCurve.plan(points[i]).z))] = i
		for i in points.size():
			var cell := Vector3i(roundi(MallCurve.plan(points[i]).x), Mall.level_at(points[i].y), roundi(MallCurve.plan(points[i]).z))
			for offset in [Vector3i(2, 0, 0), Vector3i(0, 0, 2)]:
				if lookup.has(cell + offset):
					var other: int = lookup[cell + offset]
					if Mall.plan_segment_walkable(Vector3(cell.x,Mall.floor_height(cell.y),cell.z),Vector3((cell+offset).x,Mall.floor_height(cell.y),(cell+offset).z)):
						nav.connect_points(i, other)
		# Explicit inclined links connect the same graph used by cats and item attraction.
		for flight in [[-43.5,0,9.0,21.0],[-35.0,1,21.0,9.0]]:
			var previous := -1
			for step in range(14):
				var t := clampf((step-.5)/12,0,1)
				var p := MallCurve.world(Vector3(flight[0],lerpf(Mall.floor_height(flight[1]),Mall.floor_height(flight[1]+1),t),lerpf(flight[2],flight[3],t)))
				var id := nav.get_point_count()
				if step == 0 or step == 13:
					var nearest := INF
					for candidate in nav_ids:
						var at := nav.get_point_position(candidate)
						if Mall.level_at(at.y) != int(flight[1])+(1 if step == 13 else 0): continue
						# Landings extend beyond the ramp, never through its side glass.
						var plan := MallCurve.plan(at)
						if absf(plan.x-flight[0]) > .6: continue
						if (flight[3] > flight[2] and (plan.z < flight[3]+.4 if step == 13 else plan.z > flight[2]-.4)) or (flight[3] < flight[2] and (plan.z > flight[3]-.4 if step == 13 else plan.z < flight[2]+.4)): continue
						if at.distance_squared_to(p) < nearest: nearest = at.distance_squared_to(p); id = candidate
					assert(nearest < INF,"Escalator must meet a public landing")
				else: nav.add_point(id,p)
				if previous >= 0 and id != previous: nav.connect_points(previous,id)
				previous = id
		for route in MallAnnex.core_routes():
			var previous := -1
			for step in route.size():
				var p := MallCurve.world(route[step])
				var id := nav.get_point_count()
				if step == 0 or step == route.size()-1:
					var nearest := INF
					for candidate in nav_ids:
						var at := nav.get_point_position(candidate)
						if absf(at.y-p.y) > .1: continue
						if at.distance_squared_to(p) < nearest: nearest = at.distance_squared_to(p); id = candidate
					assert(nearest < 4,"West core route must connect to its floor landing")
				else: nav.add_point(id,p)
				if previous >= 0: nav.connect_points(previous,id)
				previous = id
		cached_nav = nav
		cached_nav_hash = key
		cached_nav_ids = nav_ids
	for point in nav_ids: floor_nav_ids[Mall.level_at(nav.get_point_position(point).y)].append(point)
	var palette := [Color("c58a6b"), Color("bcc6b3"), Color("667e8a"), Color("d8c497"), Color("a78b91"), Color("4d6265")]
	for id in run.population:
		var candidates: Array = floor_nav_ids[posmod(id-slots.size(),5)-1]
		var p := nav.get_point_position(candidates[rng.randi_range(0,candidates.size()-1)])
		var heading := rng.randf_range(-PI, PI)
		var role := "walking"
		if id < slots.size():
			p = slots[id].pos
			heading = slots[id].yaw
			role = slots[id].role
		roles.append(role)
		activities.append(str(slots[id].get("activity",role)) if id < slots.size() else role)
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
		capsule.height = 1.9 if role not in ["seated","reading"] else 1.4
		collision.shape = capsule
		area.add_child(collision)
		add_child(area)
		area.position = p + Vector3.UP * (0.95 if role not in ["seated","reading"] else 0.7)
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
	_add_part("held_book",Vector3(0,1.10,-.36),Vector3(.27,.035,.19),Color("715947"))
	_add_part("held_pages",Vector3(0,1.122,-.36),Vector3(.25,.012,.17),Color("e6dcc2"))
	_add_part("held_product",Vector3(0,1.14,-.35),Vector3(.13,.16,.05),Color("536b71"))
	var cup := CylinderMesh.new(); cup.top_radius = .048; cup.bottom_radius = .037; cup.height = .10
	cup.material = Shapes.material(Color("ddd8c7"))
	_instance_part("held_cup",cup,Vector3.ZERO,Vector3.ONE,[])
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
	instances.custom_aabb = AABB(Vector3(-180,-12,-90),Vector3(340,45,230))
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
	if not frozen:
		clock += delta
		attraction_left = maxf(0,attraction_left-delta)
	for id in run.population:
		if death_times[id] >= 0:
			death_times[id] += delta
			continue
		if frozen: continue
		if attracted.has(id):
			_tick_attracted(id,delta)
			continue
		if roles[id] != "walking":
			continue
		waits[id] -= delta
		if waits[id] > 0:
			continue
		if paths[id].is_empty():
			var start := nav.get_closest_point(positions[id])
			var candidates: Array = floor_nav_ids[Mall.level_at(positions[id].y)]
			var goal: int = candidates[rng.randi_range(0, candidates.size() - 1)]
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
	var motions: Array[Dictionary] = []
	for id in run.population:
		motions.append(CivilianMotion.sample("walking" if attracted.has(id) else roles[id],activities[id],clock,id))
	for part in parts:
		var instances: MultiMesh = part.instances
		for id in run.population:
			var role := "walking" if attracted.has(id) else roles[id]
			var motion: Dictionary = motions[id]
			var hidden: bool = death_times[id] > .8 or (part.name in ["apron","badge"] and role != "staff")
			hidden = hidden or (part.name in ["held_book","held_pages"] and not motion.book)
			hidden = hidden or (part.name == "held_product" and not motion.inspect)
			hidden = hidden or (part.name == "held_cup" and role != "seated")
			if hidden:
				instances.set_instance_transform(id,Transform3D(Basis().scaled(Vector3.ZERO),Vector3(0,-20,0)))
				continue
			var local_offset: Vector3 = part.offset
			var pose := Basis.IDENTITY
			if role in ["seated","reading"]:
				if part.name.begins_with("leg_"):
					local_offset = Vector3(local_offset.x,.91,-.2); pose = Basis(Vector3.RIGHT,-PI/2)
				elif part.name.begins_with("shin_"): local_offset = Vector3(local_offset.x,.65,-.4)
				elif part.name.begins_with("shoe_"): local_offset = Vector3(local_offset.x,.49,-.47)
			var moving: bool = role == "walking" and ((waits[id] <= 0 and not paths[id].is_empty()) or attracted.has(id)) and death_times[id] < 0
			if moving:
				var phase := clock*5.5+id
				var swing := sin(phase+(0 if str(part.name).ends_with("_l") else PI))*.35
				if part.name.begins_with("leg_"):
					pose = Basis(Vector3.RIGHT,swing); local_offset = Vector3(local_offset.x,.83,0)+pose*Vector3(0,-.21,0)
				elif part.name.begins_with("shin_") or part.name.begins_with("shoe_"):
					var hip := Basis(Vector3.RIGHT,swing)
					pose = hip*Basis(Vector3.RIGHT,-maxf(0,-sin(phase+(0 if str(part.name).ends_with("_l") else PI)))*.65)
					local_offset = Vector3(local_offset.x,.83,0)+hip*Vector3(0,-.42,0)+pose*Vector3(0,-.19 if part.name.begins_with("shin_") else -.33,-.035 if part.name.begins_with("shoe_") else 0)
			if str(part.name).begins_with("arm_") or str(part.name).begins_with("forearm_") or str(part.name).begins_with("hand_"):
				var side: String = "left" if str(part.name).ends_with("_l") else "right"
				var key: String = str(part.name).get_slice("_",0)
				var joint: Dictionary = motion[side][key]
				pose = joint.basis; local_offset = joint.pos
				if moving:
					var swing := sin(clock*5.5+id+(0 if side == "left" else PI))*.28
					pose = Basis(Vector3.RIGHT,-swing)
					local_offset = Vector3(local_offset.x,1.4,0)+pose*Vector3(0,-.15 if key == "arm" else -.44 if key == "forearm" else -.61,0)
			if part.name in ["head","hair"]:
				pose = motion.head
				local_offset = Vector3(0,1.5,0)+pose*(local_offset-Vector3(0,1.5,0))
			if part.name == "held_cup":
				local_offset = motion.right.wrist+Vector3(0,.04,-.035)
				pose = Basis(Vector3.RIGHT,motion.drink*.35)
			var base := positions[id]
			if role in ["seated","reading"]: base.y -= .42
			if part.name not in ["shoe_l","shoe_r","shin_l","shin_r"]: base.y += motion.breath
			if death_times[id] >= 0: base.y -= pow(death_times[id]/.8,2)*4
			var basis := Basis(Vector3.UP,headings[id])
			instances.set_instance_transform(id,Transform3D((basis*pose).scaled_local(part.scale),base+basis*local_offset))

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

func attract(center: Vector3,radius: float,seconds: float) -> void:
	attraction_left = seconds
	var destination := nav.get_closest_point(center)
	for id in live_positions_in_radius(center,radius):
		if attracted.has(id): continue
		var start := nav.get_closest_point(positions[id])
		var query := PhysicsRayQueryParameters3D.create(positions[id]+Vector3.UP*.9,nav.get_point_position(start)+Vector3.UP*.9,1)
		if not get_world_3d().direct_space_state.intersect_ray(query).is_empty(): continue
		attracted[id] = {"home":positions[id],"yaw":headings[id],"path":nav.get_point_path(start,destination),"returning":false}
		_set_body_pose(id,false)

func _set_body_pose(id: int,seated: bool) -> void:
	var collision: CollisionShape3D = bodies[id].get_child(0)
	collision.shape.height = 1.4 if seated else 1.9
	bodies[id].position = positions[id]+Vector3.UP*(.7 if seated else .95)

func _tick_attracted(id: int,delta: float) -> void:
	var data: Dictionary = attracted[id]
	if attraction_left <= 0 and not data.returning:
		data.returning = true
		data.path = nav.get_point_path(nav.get_closest_point(positions[id]),nav.get_closest_point(data.home))
	if not data.path.is_empty():
		var direction: Vector3 = data.path[0]-positions[id]
		positions[id] = positions[id].move_toward(data.path[0],delta*3)
		if direction.length() > .05: headings[id] = atan2(-direction.x,-direction.z)
		if positions[id].distance_to(data.path[0]) < .06: data.path.remove_at(0)
	elif data.returning:
		positions[id] = positions[id].move_toward(data.home,delta*2)
		if positions[id].distance_to(data.home) < .05:
			positions[id] = data.home
			attracted.erase(id); paths[id].clear(); waits[id] = 2
			headings[id] = data.yaw
			_set_body_pose(id,roles[id] in ["seated","reading"])
			return
	bodies[id].position = positions[id]+Vector3.UP*.95
