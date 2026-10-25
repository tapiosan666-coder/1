class_name Crowd
extends Node3D
## Shared meshes and a walkable grid keep identity data separate from visuals.
## Instancing reduces the crowd to a handful of mesh submissions.

var positions: Array[Vector3] = []
var headings: Array[float] = []
var paths: Array[PackedVector3Array] = []
var path_requests_last_tick := 0
var waits: Array[float] = []
var death_times: Array[float] = []
var bodies: Array[Area3D] = []
var parts: Array[Dictionary] = []
var continuous_body:CivilianBody
var clock := 0.0
var render_clock := 0.0
var detail_distance := 26.0
var draw_distance := 140.0
var rendered_ids: Array[int] = []
var detailed_ids: Array[int] = []
var lod_meshes: Array[MultiMesh] = []
var contact_shadows:MultiMesh
var clothing_palette: Array = []
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
		if WorldCache.navigation.get("hash",-1) == key:
			var data := WorldCache.navigation
			for i in data.positions.size(): nav.add_point(i,data.positions[i])
			for i in points.size(): nav_ids.append(i)
			for index in range(0,data.edges.size(),2): nav.connect_points(data.edges[index],data.edges[index+1])
			var one_way:PackedInt32Array=data.get("one_way",PackedInt32Array())
			for index in range(0,one_way.size(),2):nav.connect_points(one_way[index],one_way[index+1],false)
		else:
			for i in points.size():
				nav.add_point(i, points[i])
				nav_ids.append(i)
			var lookup: Dictionary = {}
			for i in points.size():
				lookup[Vector3i(roundi(MallCurve.plan(points[i]).x), Mall.level_at(points[i].y), roundi(MallCurve.plan(points[i]).z))] = i
			for i in points.size():
				var cell := Vector3i(roundi(MallCurve.plan(points[i]).x), Mall.level_at(points[i].y), roundi(MallCurve.plan(points[i]).z))
				for offset in [Vector3i(1,0,0),Vector3i(0,0,1),Vector3i(2,0,0),Vector3i(0,0,2),Vector3i(1,0,1),Vector3i(1,0,-1),Vector3i(2,0,2),Vector3i(2,0,-2),Vector3i(1,0,2),Vector3i(1,0,-2),Vector3i(2,0,1),Vector3i(2,0,-1)]:
					if lookup.has(cell + offset):
						var other: int = lookup[cell + offset]
						if Mall.plan_segment_walkable(Vector3(cell.x,Mall.floor_height(cell.y),cell.z),Vector3((cell+offset).x,Mall.floor_height(cell.y),(cell+offset).z)):
							nav.connect_points(i, other)
			# Explicit inclined links connect the same graph used by cats and item attraction.
			for flight in MallEscalators.all_flights():
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
					if previous >= 0 and id != previous:
						if flight.size()>4:
							if flight[4]>0:nav.connect_points(previous,id,false)
							else:nav.connect_points(id,previous,false)
						else:nav.connect_points(previous,id)
					previous = id
			for route in MallAnnex.core_routes()+CUpper.core_routes():
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
						assert(nearest < 4,"Stair route must connect to its floor landing")
					else: nav.add_point(id,p)
					if previous >= 0: nav.connect_points(previous,id)
					previous = id
		Mall.segment_probe_cache.clear()
		cached_nav = nav
		cached_nav_hash = key
		cached_nav_ids = nav_ids
	for point in nav_ids: floor_nav_ids[Mall.level_at(nav.get_point_position(point).y)].append(point)
	var palette := [Color("3b4149"), Color("8c363b"), Color("324c61"), Color("8b8f7d"), Color("b7ae9a"), Color("656374")]
	clothing_palette = palette
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
		capsule.radius = 0.44
		capsule.height = 1.9 if role not in ["seated","reading"] else 1.6
		collision.shape = capsule
		area.add_child(collision)
		add_child(area)
		area.position = p + Vector3.UP * (0.95 if role not in ["seated","reading"] else 0.8)
		bodies.append(area)
	var kit: Node3D = preload("res://assets/characters/civilian.glb").instantiate()
	# Only facial features and hands remain rigid attachments. Torso, sleeves,
	# hips and trousers are one connected, weighted garment renderer.
	var offsets:={"head":Vector3(0,1.7,0),"hair":Vector3(0,1.81,0),"eye_l":Vector3(-.3077*.12,1.7,-(1.2453-.45)*.105),"eye_r":Vector3(.3077*.12,1.7,-(1.2453-.45)*.105),"hand_l":Vector3(-.215,.85,0),"hand_r":Vector3(.215,.85,0)}
	for node in kit.find_children("*", "MeshInstance3D", true, false):
		var title: String = node.name
		if not offsets.has(title):
			continue
		var mesh: Mesh = node.mesh.duplicate()
		for surface in mesh.get_surface_count():
			var material: StandardMaterial3D = mesh.surface_get_material(surface).duplicate()
			var tag := material.resource_name
			var result: Material = material
			if tag.begins_with("Skin"):
				material.albedo_color = skin_color; material.roughness = .55; material.vertex_color_use_as_albedo=true
				if title in ["head","hand_l","hand_r"]:
					var skin := ShaderMaterial.new(); skin.shader = preload("res://assets/skin.gdshader")
					skin.set_shader_parameter("skin_tint",skin_color); _skin_textures(skin); result = skin
			elif tag.begins_with("Hair"):
				var hair := ShaderMaterial.new(); hair.shader = preload("res://assets/hair.gdshader")
				hair.set_shader_parameter("hair_tint",hair_color)
				hair.set_shader_parameter("strand_map",preload("res://assets/characters/textures/hair_strands.png"));hair.set_shader_parameter("strand_normal",preload("res://assets/characters/textures/hair_normal.png"));result = hair
			elif tag.begins_with("Cloth") or tag.begins_with("Trousers") or tag.begins_with("Shirt"):
				var fabric := ShaderMaterial.new(); fabric.shader = preload("res://assets/fabric.gdshader")
				fabric.set_shader_parameter("fabric_detail",preload("res://assets/characters/textures/fabric_detail.png"))
				fabric.set_shader_parameter("fabric_normal",preload("res://assets/characters/textures/fabric_normal.png"))
				if not tag.begins_with("Cloth"):
					fabric.set_shader_parameter("use_palette",false)
					fabric.set_shader_parameter("garment_tint",Color("35414b") if tag.begins_with("Trousers") else Color("d0ccc0"))
				result = fabric
			elif tag.begins_with("Lip"):
				var lip := ShaderMaterial.new(); lip.shader = preload("res://assets/skin.gdshader")
				lip.set_shader_parameter("skin_tint",skin_color.lerp(Color("a47569"),.10)); lip.set_shader_parameter("lip_surface",true); _skin_textures(lip); result = lip
			elif tag.begins_with("Eye") or tag.begins_with("Iris"):
				material.roughness = .8;material.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
			else: material.roughness = .75
			if title=="hair" or (title=="head" and tag.begins_with("Skin")):
				var ink:=ShaderMaterial.new();ink.shader=preload("res://assets/civilian_outline.gdshader")
				if title=="head":ink.set_shader_parameter("low_cut",-.105)
				result.next_pass=ink
			mesh.surface_set_material(surface,result)

		var size := Vector3(face_width, 1, 1) if title in ["head", "hair", "eye_l", "eye_r"] else Vector3.ONE
		_instance_part(title, mesh, offsets[title], size, palette)
	kit.free()
	continuous_body=CivilianBody.new(self,run.population,skin_color,face_width)
	_instance_part("apron",CivilianBody.apron_mesh(),Vector3.ZERO,Vector3.ONE,[])
	_add_part("badge", Vector3(.13,1.38,-.138), Vector3(.065,.032,.01), Color("e8e3d3"))
	_add_part("held_book",Vector3(0,1.16,-.36),Vector3(.27,.035,.19),Color("715947"))
	_add_part("held_pages",Vector3(0,1.182,-.36),Vector3(.25,.012,.17),Color("e6dcc2"))
	_add_part("held_product",Vector3(0,1.20,-.35),Vector3(.13,.16,.05),Color("536b71"))
	var cup := CylinderMesh.new(); cup.top_radius = .048; cup.bottom_radius = .037; cup.height = .10
	cup.material = Shapes.material(Color("ddd8c7"))
	_instance_part("held_cup",cup,Vector3.ZERO,Vector3.ONE,[])
	_make_lods()
	_make_contact_shadows()
	_render(true)

func _skin_textures(material: ShaderMaterial) -> void:
	material.set_shader_parameter("skin_detail",preload("res://assets/characters/textures/skin_detail.png"))
	material.set_shader_parameter("skin_normal",preload("res://assets/characters/textures/skin_normal.png"))

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
	instances.use_custom_data = true
	# Explicit sector bounds avoid camera-near clipping of animated instance groups.
	instances.custom_aabb = AABB(Vector3(-430,-12,-90),Vector3(590,45,230))
	instances.mesh = mesh
	instances.instance_count = run.population
	for id in run.population:
		instances.set_instance_color(id, palette[id % palette.size()] if not palette.is_empty() else Color.WHITE)
	var node := MultiMeshInstance3D.new()
	node.multimesh = instances
	add_child(node)
	parts.append({"name": title, "offset": offset, "scale": instance_scale, "instances": instances,"palette":palette})

func _physics_process(delta: float) -> void:
	if run == null:
		return
	if not frozen:
		clock += delta
		attraction_left = maxf(0,attraction_left-delta)
	var plans := 0
	path_requests_last_tick = 0
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
			# Spread path requests across physics ticks rather than one burst.
			if plans >= 1: continue
			plans += 1
			path_requests_last_tick += 1
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
	render_clock += delta
	if render_clock >= 1.0/30.0:
		render_clock = 0
		_render()

func _make_contact_shadows() -> void:
	var mesh:=QuadMesh.new();mesh.size=Vector2(.9,.75)
	var material:=ShaderMaterial.new();material.shader=preload("res://assets/contact_shadow.gdshader");mesh.material=material
	contact_shadows=MultiMesh.new();contact_shadows.transform_format=MultiMesh.TRANSFORM_3D;contact_shadows.mesh=mesh;contact_shadows.instance_count=run.population
	var node:=MultiMeshInstance3D.new();node.name="CharacterContactShadows";node.multimesh=contact_shadows;node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(node)
func _render_contact_shadows(bounds:AABB) -> void:
	if contact_shadows==null:return
	contact_shadows.custom_aabb=bounds
	contact_shadows.visible_instance_count=rendered_ids.size()
	for i in rendered_ids.size():
		var id:=rendered_ids[i]
		var scale:=Vector3.ZERO if death_times[id]>=0 else Vector3.ONE
		var basis:=Basis(Vector3.UP,headings[id])*Basis(Vector3.RIGHT,-PI/2)
		contact_shadows.set_instance_transform(i,Transform3D(basis.scaled_local(scale),positions[id]+Vector3.UP*.028))

func _make_lods() -> void:
	for seated in [false,true]:
		var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.use_custom_data = true
		mm.mesh = CivilianLod.mesh_for(seated,skin_color,hair_color,face_width)
		mm.instance_count = run.population; mm.visible_instance_count = 0
		var node := MultiMeshInstance3D.new(); node.multimesh = mm; node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(node); lod_meshes.append(mm)

func _render(_force: bool = false) -> void:
	var camera := get_viewport().get_camera_3d()
	var motions: Dictionary = {}
	detailed_ids.clear(); rendered_ids.clear()
	var far: Array[Array] = [[],[]]
	var bounds := AABB(); var first := true
	for id in run.population:
		if death_times[id] > .8: continue
		var distance := positions[id].distance_squared_to(camera.global_position) if camera != null else 0.0
		if distance > draw_distance*draw_distance: continue
		var detail := distance < detail_distance*detail_distance
		if detail and camera != null:
			var center := positions[id]+Vector3.UP
			detail = camera.is_position_in_frustum(center) or camera.is_position_in_frustum(center+camera.global_basis.x*.7) or camera.is_position_in_frustum(center-camera.global_basis.x*.7) or camera.is_position_in_frustum(center+Vector3.UP)
		rendered_ids.append(id)
		var box := AABB(positions[id]-Vector3(1,5,1),Vector3(2,8,2))
		bounds = box if first else bounds.merge(box); first = false
		if detail:
			detailed_ids.append(id)
			var moving: bool = roles[id] == "walking" and waits[id] <= 0 and not paths[id].is_empty() or attracted.has(id)
			motions[id] = CivilianMotion.sample("walking" if attracted.has(id) else roles[id],activities[id],clock,id,moving)
		else: far[1 if roles[id] in ["seated","reading"] and not attracted.has(id) else 0].append(id)
	for group in 2:
		var mm := lod_meshes[group]
		mm.visible_instance_count = far[group].size(); mm.custom_aabb = bounds
		for index in far[group].size():
			var id: int = far[group][index]
			var at := positions[id]
			if death_times[id] >= 0: at.y -= pow(death_times[id]/.8,2)*4
			mm.set_instance_transform(index,Transform3D(Basis(Vector3.UP,headings[id]),at))
			mm.set_instance_custom_data(index,clothing_palette[id%clothing_palette.size()])
	if continuous_body!=null:continuous_body.render(self,detailed_ids,motions,bounds)
	_render_contact_shadows(bounds)
	for part in parts:
		var instances: MultiMesh = part.instances
		instances.visible_instance_count = detailed_ids.size(); instances.custom_aabb = bounds
		for slot in detailed_ids.size():
			var id := detailed_ids[slot]
			instances.set_instance_color(slot,Color.WHITE)
			instances.set_instance_custom_data(slot,Color(motions[id].blink,motions[id].expression,0,1) if part.name == "head" else part.palette[id%part.palette.size()] if not part.palette.is_empty() else Color.WHITE)
			var role := "walking" if attracted.has(id) else roles[id]
			var motion: Dictionary = motions[id]
			var hidden: bool = death_times[id] > .8 or (part.name in ["apron","badge"] and role != "staff")
			hidden = hidden or (part.name in ["held_book","held_pages"] and not motion.book)
			hidden = hidden or (part.name == "held_product" and not motion.inspect)
			hidden = hidden or (part.name == "held_cup" and (role != "seated" or activities[id] == "food_wait"))
			hidden = hidden or (part.name in ["eye_l","eye_r"] and motion.blink > .96)
			if hidden:
				instances.set_instance_transform(slot,Transform3D(Basis().scaled(Vector3.ZERO),Vector3(0,-20,0)))
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
			if part.name in ["head","hair","eye_l","eye_r"]:
				pose = motion.head
				if part.name in ["eye_l","eye_r"]:
					local_offset.x *= face_width
					pose = pose*Basis(Vector3.UP,motion.eyes.x)*Basis(Vector3.RIGHT,motion.eyes.y)*Basis().scaled(Vector3(1,maxf(.08,1.0-motion.blink),1))
				local_offset = Vector3(0,1.5,0)+motion.head*(local_offset-Vector3(0,1.5,0))
			if part.name == "held_cup":
				local_offset = motion.right.wrist+Vector3(0,.04,-.035)
				pose = Basis(Vector3.RIGHT,motion.drink*.35)
			if not (part.name.begins_with("leg_") or part.name.begins_with("shin_") or part.name.begins_with("shoe_")):
				local_offset = Vector3(0,CivilianRig.HIP_Y,0)+motion.body*(local_offset-Vector3(0,CivilianRig.HIP_Y,0)); pose = motion.body*pose
			var base := positions[id]
			if role in ["seated","reading"]: base.y -= CivilianRig.SEAT_DROP
			if part.name not in ["shoe_l","shoe_r","shin_l","shin_r"]: base.y += motion.breath
			if death_times[id] >= 0: base.y -= pow(death_times[id]/.8,2)*4
			var basis := Basis(Vector3.UP,headings[id])
			instances.set_instance_transform(slot,Transform3D((basis*pose).scaled_local(part.scale),base+basis*local_offset))

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
	collision.shape.height = 1.6 if seated else 1.9
	bodies[id].position = positions[id]+Vector3.UP*(.8 if seated else .95)

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
