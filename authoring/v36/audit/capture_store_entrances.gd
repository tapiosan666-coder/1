extends SceneTree
var out: String
var batch: Array
var game
var count := 0
var near_field := false
var display_size := Vector2i(640,360)

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var cameras := ""
	var wing := ""
	for arg: String in OS.get_cmdline_user_args():
		if arg == "--near-field": near_field = true
		if arg.begins_with("--out="): out = arg.trim_prefix("--out=")
		if arg.begins_with("--shots="): cameras = arg.trim_prefix("--shots=")
		if arg.begins_with("--wing="): wing = arg.trim_prefix("--wing=")
		if arg.begins_with("--width="):
			display_size.x = int(arg.trim_prefix("--width="))
			display_size.y = roundi(display_size.x * 9.0 / 16.0)
	DirAccess.make_dir_recursive_absolute(out)
	batch = JSON.parse_string(FileAccess.get_file_as_string(cameras))
	var remaining := batch.filter(func(r): return (wing.is_empty() or r.wing == wing) and not FileAccess.file_exists(out.path_join(r.id+".json")))
	# Adjacent shop stacks share local render chunks. Pair same-XY upper floors
	# after one shot per as-yet unrepresented floor. Camera recipes remain fixed.
	var pivots: Array = []
	var floor_seen: Dictionary = {}
	for row: Dictionary in batch:
		if FileAccess.file_exists(out.path_join(row.id+".json")): floor_seen[row.wing+row.floor]=true
	for row: Dictionary in remaining:
		if not floor_seen.has(row.wing+row.floor):
			pivots.append(row)
			floor_seen[row.wing+row.floor]=true
	for row: Dictionary in pivots: remaining.erase(row)
	var ordered := pivots.duplicate()
	for wing_name: String in ["A","B","C"]:
		var wing_rows := remaining.filter(func(r):return r.wing==wing_name)
		var last := Vector3.ZERO
		while not wing_rows.is_empty():
			var best := 0
			var best_dist := INF
			for i in wing_rows.size():
				var q: Array = wing_rows[i].eye
				var p := Vector3(float(q[0]),float(q[1])*.7,float(q[2]))
				var distance := p.distance_squared_to(last)
				if distance<best_dist:
					best_dist=distance
					best=i
			var chosen: Dictionary=wing_rows.pop_at(best)
			ordered.append(chosen)
			last=Vector3(chosen.eye[0],chosen.eye[1]*.7,chosen.eye[2])
	remaining=ordered
	if remaining.is_empty():
		quit();return
	RenderingServer.set_render_loop_enabled(false)
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	while game.results.is_empty():
		await process_frame
	if game.results.get("startup_failed",false):
		print("SURVEY_BOOT_FAILURE ",game.results);quit(1);return
	root.size = display_size
	root.content_scale_size = display_size
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.scaling_3d_scale = 1.0
	RenderingServer.set_render_loop_enabled(false)
	game.player.physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF
	game.player.set_physics_process(false)
	game.player.input_enabled = false
	game.shoppers_v18.set_enabled(false,true)
	game.hud.get_parent().hide()
	game.animator.paused = true
	var vp := Camera3D.new()
	game.add_child(vp)
	vp.physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF
	vp.current = true
	if near_field:
		vp.far = 48.0
		for light: Light3D in game.find_children("*","Light3D",true,false):
			light.shadow_enabled = false
	var world = game.get_node("V30_Runtime")
	for shot: Dictionary in remaining:
		var start := Time.get_ticks_usec()
		var eye: Vector3 = game.v3(shot.eye)
		var entry: Vector3 = game.v3(shot.entry)
		var direction: Vector3 = game.v3(shot.inward)
		game.player.position = eye - Vector3.UP * 1.60
		game.player.rotation = Vector3.ZERO
		vp.global_position = eye
		vp.fov = shot.fov
		vp.look_at(game.v3(shot.look))
		game.player.reset_physics_interpolation()
		vp.reset_physics_interpolation()
		vp.force_update_transform()
		world.prepare_position(game.player.position)
		var prepared := Time.get_ticks_usec()
		game.get_node("V31_Sales").update_near()
		for name_: String in ["V34_Mall_Art","V35_Mall_Art","V36_Mall_Art","V36_Retail","V36_Commons"]:
			var art: Node = game.get_node_or_null(name_)
			if art != null and art.has_method("update_near"):
				art.update_near()
		game.animator.set_time(1.75)
		await physics_frame
		await process_frame
		var sync_time := Time.get_ticks_usec()
		var result := {"id":shot.id,"eye":shot.eye,"look":shot.look,"fov":shot.fov,"physics":probes(entry,direction),"zones":world.active.size()}
		# Synchronous force_draw captures current transform without spending renderer
		# time on the physics frames used to settle the retail and collision chunks.
		RenderingServer.camera_set_transform(vp.get_camera_rid(),vp.global_transform)
		RenderingServer.force_draw(true)
		var draw_time := Time.get_ticks_usec()
		if not near_field:
			RenderingServer.force_draw(true)
		var image := root.get_texture().get_image()
		result.timings_ms = [float(prepared-start)/1000., float(sync_time-prepared)/1000., float(draw_time-sync_time)/1000.,float(Time.get_ticks_usec()-draw_time)/1000.]
		var studios: Node = game.get_node_or_null("V35_Mall_Art/V36_Store_Studios") as Node
		if studios != null:
			var installed: Array = []
			for key: String in studios.resident:
				if key.begins_with(shot.id+"/"): installed.append(key.trim_prefix(shot.id+"/"))
			result.local_cases_at_camera = installed
			result.sales_loaded_for_this_store = game.get_node("V31_Sales").active.has(shot.id)
			result.v36_courts_system_present = game.has_node("V35_Mall_Art/V36_Public_Courts")
		var wall_editions: Node = game.get_node_or_null("V35_Mall_Art/V36_Wall_Editions")
		if wall_editions != null:
			result.local_wall_edition_at_camera = wall_editions.active.has(shot.id)
		result.image_size = [image.get_width(),image.get_height()]
		result.draw_calls = RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME)
		result.primitives = RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME)
		result.engine_static_bytes = Performance.get_monitor(Performance.MEMORY_STATIC)
		result.survey_profile = "near 48m, directional shadows off" if near_field else "full depth, default shadows"
		result.renderer = RenderingServer.get_current_rendering_method()
		result.adapter = RenderingServer.get_video_adapter_name()
		if image.save_jpg(out.path_join(shot.id+".jpg"),.86) != OK:
			print("SURVEY_SAVE_FAILURE ",shot.id);quit(1);return
		result.elapsed_including_stream_s = (Time.get_ticks_usec()-start)/1000000.
		FileAccess.open(out.path_join(shot.id+".json"),FileAccess.WRITE).store_string(JSON.stringify(result))
		count += 1
		print("SURVEY_STORE ",count," ",shot.id," ",result.image_size," ",result.draw_calls," ",snappedf(result.elapsed_including_stream_s,.01))
	game.queue_free()
	await process_frame
	await physics_frame
	quit()

func probes(entry:Vector3,dir:Vector3) -> Dictionary:
	var space:PhysicsDirectSpaceState3D = game.get_world_3d().direct_space_state
	var shape := CapsuleShape3D.new()
	shape.radius = .32
	shape.height = 1.66
	var q := PhysicsShapeQueryParameters3D.new()
	q.shape = shape
	q.exclude = [game.player.get_rid()]
	q.collision_mask = game.player.collision_mask
	q.transform = Transform3D(Basis(),entry-dir*.85+Vector3.UP*.92)
	q.motion = dir*1.7
	var fractions := space.cast_motion(q)
	var origin_clear := space.intersect_shape(q,1).is_empty()
	var supports: Array = []
	var support_details: Array = []
	for depth:float in [-.85,0.,.85,2.]:
		var p := entry+dir*depth
		var ray := PhysicsRayQueryParameters3D.create(p+Vector3.UP*.5,p-Vector3.UP*.5,q.collision_mask,[game.player.get_rid()])
		var h := space.intersect_ray(ray)
		var passes: bool = not h.is_empty() and absf(h.position.y-entry.y)<.18 and h.normal.y>.60
		supports.append(passes)
		if passes:continue
		var diagnostic := {"distance":depth,"point":[p.x,p.y,p.z],"ray_hit":not h.is_empty(),"nearby_support":[]}
		if not h.is_empty():
			diagnostic.hit_height = h.position.y
			diagnostic.normal_y = h.normal.y
			diagnostic.collider = str(h.collider.name)
		# A ray precisely on a cell seam can miss despite a supported player
		# footprint. Also retain nearby hits so a true void can be distinguished.
		for radius:float in [.12,.32,.55]:
			var surrounding := 0
			for count in 8:
				var a := TAU*count/8.0
				var shift := Vector3(cos(a),0.,sin(a))*radius
				var local := PhysicsRayQueryParameters3D.create(p+shift+Vector3.UP*.5,p+shift-Vector3.UP*.5,q.collision_mask,[game.player.get_rid()])
				var result := space.intersect_ray(local)
				if not result.is_empty() and absf(result.position.y-entry.y)<.18 and result.normal.y>.60:surrounding+=1
			diagnostic.nearby_support.append({"radius":radius,"floor_contacts":surrounding,"rays":8})
		support_details.append(diagnostic)
	return {"floor_four_points":supports,"floor_exceptions":support_details,"threshold_sweep_fraction":fractions[0] if fractions.size() else null,"origin_clear":origin_clear}
