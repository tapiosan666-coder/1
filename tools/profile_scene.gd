extends SceneTree
func _initialize() -> void: call_deferred("measure")
func measure() -> void:
	var started := Time.get_ticks_usec()
	var game = load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	game.start_run(180,912)
	game.player.set_physics_process(false)
	game.crowd.frozen = true
	var fixture_path := "/tmp/fy08-profile-fixture.json"
	if "--save-fixture" in OS.get_cmdline_user_args():
		var actors: Array = []
		for id in game.run.population:
			var at: Vector3 = game.crowd.positions[id]
			actors.append([at.x,at.y,at.z,game.crowd.headings[id],game.crowd.roles[id],game.crowd.activities[id]])
		var file := FileAccess.open(fixture_path,FileAccess.WRITE); file.store_string(JSON.stringify(actors)); file.close()
	elif FileAccess.file_exists(fixture_path):
		var actors: Array = JSON.parse_string(FileAccess.get_file_as_string(fixture_path))
		for id in actors.size():
			var actor: Array = actors[id]
			game.crowd.positions[id] = Vector3(actor[0],actor[1],actor[2]); game.crowd.headings[id] = actor[3]
			game.crowd.roles[id] = actor[4]; game.crowd.activities[id] = actor[5]
			game.crowd._set_body_pose(id,actor[4] in ["seated","reading"])
	root.msaa_3d = Viewport.MSAA_DISABLED
	root.scaling_3d_scale = 1.0
	for light in game.get_children():
		if light is DirectionalLight3D: light.shadow_enabled = true; light.directional_shadow_max_distance = 85
	var startup := (Time.get_ticks_usec()-started)/1000.0
	var report := {"startup_ms":startup,"viewport":str(root.size),"cases":[]}
	for shot in [["entrance",Vector3(-82,.1,0),Vector3(-25,1.7,0)],["atrium",Vector3(-25,.1,0),Vector3(33,7,0)],["parking",Vector3(-125,.1,-5.5),Vector3(-151,1,-20)]]:
		game.player.position = MallCurve.world(shot[1]); game.player.camera.look_at(MallCurve.world(shot[2]))
		for frame in 2: await process_frame
		var frames: Array[float] = []; var draws := 0.0; var tris := 0.0
		for frame in 8:
			var before := Time.get_ticks_usec(); await process_frame
			frames.append((Time.get_ticks_usec()-before)/1000.0)
			draws += Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
			tris += Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)
		frames.sort()
		print("PROFILE_CASE: ",shot[0]," median_ms=",frames[4]," draws=",draws/8," primitives=",tris/8)
		report.cases.append({"name":shot[0],"median_frame_ms":frames[4],"p90_frame_ms":frames[7],"draw_calls":draws/8,"primitives":tris/8})
	print("PROFILE_JSON: ",JSON.stringify(report))
	quit()
