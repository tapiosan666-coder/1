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
	else:
		if not FileAccess.file_exists(fixture_path): fixture_path = "res://docs/render-profile-fixture-v013.json"
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
	var steady := "--steady-profile" in OS.get_cmdline_user_args()
	var warmup := 12 if steady else 2
	var samples := 30 if steady else 8
	var report := {"startup_ms":startup,"viewport":str(root.size),"warmup_frames":warmup,"sample_frames":samples,"cases":[]}
	for shot in [["entrance",Vector3(-82,.1,0),Vector3(-25,1.7,0)],["atrium",Vector3(-25,.1,0),Vector3(33,7,0)],["parking",Vector3(-125,.1,-5.5),Vector3(-151,1,-20)]]:
		game.player.position = MallCurve.world(shot[1]); game.player.camera.look_at(MallCurve.world(shot[2]))
		for frame in warmup: await process_frame
		var frames: Array[float] = []; var draws := 0.0; var tris := 0.0
		for frame in samples:
			var before := Time.get_ticks_usec(); await process_frame
			frames.append((Time.get_ticks_usec()-before)/1000.0)
			draws += Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
			tris += Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)
		frames.sort()
		var median := frames[samples/2]
		var p90 := frames[mini(samples-1,ceili(samples*.9)-1)]
		print("PROFILE_CASE: ",shot[0]," median_ms=",median," draws=",draws/samples," primitives=",tris/samples)
		report.cases.append({"name":shot[0],"median_frame_ms":median,"p90_frame_ms":p90,"draw_calls":draws/samples,"primitives":tris/samples})
	print("PROFILE_JSON: ",JSON.stringify(report))
	quit()
