extends SceneTree
## CPU logic microbenchmark: simulated movement, no pose rendering, not game FPS.
func _initialize() -> void: call_deferred("measure")
func measure() -> void:
	var game = load("res://scenes/main.tscn").instantiate(); root.add_child(game)
	game.start_run(300,912); game.set_physics_process(false); game.player.set_physics_process(false); game.crowd.set_physics_process(false)
	var fixture := "/tmp/fy13-path-fixture.json"
	if "--save-fixture" in OS.get_cmdline_user_args():
		var people: Array = []
		for id in 300:
			var p: Vector3 = game.crowd.positions[id]
			people.append([p.x,p.y,p.z,game.crowd.headings[id],game.crowd.roles[id],game.crowd.activities[id],game.crowd.waits[id]])
		var file := FileAccess.open(fixture,FileAccess.WRITE); file.store_string(JSON.stringify(people)); file.close()
	else:
		if not FileAccess.file_exists(fixture): fixture = "res://docs/path-profile-fixture-v013.json"
		var people: Array = JSON.parse_string(FileAccess.get_file_as_string(fixture))
		for id in people.size():
			var p: Array = people[id]
			game.crowd.positions[id] = Vector3(p[0],p[1],p[2]); game.crowd.headings[id] = p[3]
			game.crowd.roles[id] = p[4]; game.crowd.activities[id] = p[5]; game.crowd.waits[id] = p[6]
	game.crowd.rng.seed = 13013; game.crowd.render_clock = -100000
	game.run.ap = 1000; game.buy_skill("cat"); game.set_mode("play")
	var cat_times: Array[float] = []; var crowd_times: Array[float] = []
	var cat_spikes := 0; var crowd_spikes := 0
	for tick in 2400:
		var before := Time.get_ticks_usec(); game.crowd._physics_process(.1)
		var duration := (Time.get_ticks_usec()-before)/1000.0; crowd_times.append(duration)
		if duration > 10: crowd_spikes += 1
		before = Time.get_ticks_usec(); game._tick_cat(.1)
		duration = (Time.get_ticks_usec()-before)/1000.0; cat_times.append(duration)
		if duration > 10: cat_spikes += 1
	cat_times.sort(); crowd_times.sort()
	var report := {"population":300,"simulated_seconds":240,"step_seconds":.1,"pose_rendering":false,"cleared":game.run.cleared,"won":game.run.won,"cat_max_ms":cat_times[-1],"cat_p95_ms":cat_times[2279],"cat_ticks_over_10ms":cat_spikes,"crowd_max_ms":crowd_times[-1],"crowd_p95_ms":crowd_times[2279],"crowd_ticks_over_10ms":crowd_spikes}
	print("PATH_PROFILE_JSON: ",JSON.stringify(report))
	game.queue_free(); await process_frame; await create_timer(.3).timeout; quit()
