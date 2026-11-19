extends SceneTree

var output_dir := "user://v36-performance"
var limit := 4
var measure_walk := false
var game: Node3D
var testing_environment: Dictionary
var scan_start_usec: int

func _initialize() -> void:
	call_deferred("run")

func pipeline_info() -> Dictionary:
	return {
		"canvas": RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_PIPELINE_COMPILATIONS_CANVAS),
		"mesh": RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_PIPELINE_COMPILATIONS_MESH),
		"surface": RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_PIPELINE_COMPILATIONS_SURFACE),
		"draw": RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_PIPELINE_COMPILATIONS_DRAW),
		"specialization": RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_PIPELINE_COMPILATIONS_SPECIALIZATION),
		"video_memory_bytes": Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED),
	}

func now_ms() -> float:
	return (Time.get_ticks_usec() - scan_start_usec) / 1000.0

func stamp(value: Dictionary) -> void:
	var file := FileAccess.open(output_dir.path_join("native.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(value, " "))

func send_key(code: int, pressed: bool) -> void:
	var event := InputEventKey.new()
	event.physical_keycode = code
	event.keycode = code
	event.pressed = pressed
	Input.parse_input_event(event)

func capture(id: String) -> void:
	var image := root.get_texture().get_image()
	var err := image.save_jpg(output_dir.path_join(id + ".jpg"), 0.92)
	print("V34_VIEW ", id, " ", image.get_size(), " error=", err)

func frame() -> void:
	await process_frame
	await RenderingServer.frame_post_draw

func run() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("A rendered viewport is required. Launch this measurement without --headless.")
		quit(2)
		return
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--out="):
			output_dir = arg.trim_prefix("--out=")
		elif arg.begins_with("--frames="):
			limit = clampi(int(arg.trim_prefix("--frames=")), 1, 600)
		elif arg == "--walk":
			measure_walk = true
	output_dir = ProjectSettings.globalize_path(output_dir)
	if DirAccess.make_dir_recursive_absolute(output_dir) != OK:
		push_error("Cannot create the measurement directory: " + output_dir)
		quit(2)
		return
	var probe := FileAccess.open(output_dir.path_join("native.json"), FileAccess.WRITE)
	if probe == null:
		push_error("Cannot write the measurement: " + output_dir)
		quit(2)
		return
	probe.close()
	print("Measurement output: ", output_dir)
	scan_start_usec = Time.get_ticks_usec()
	var instance := load("res://main.tscn") as PackedScene
	game = instance.instantiate()
	root.add_child(game)
	while game.results.is_empty():
		await process_frame
	if game.results.get("startup_failed", false):
		stamp({"startup_failed": true, "startup": game.results})
		quit(1)
		return
	var ready_ms := now_ms()
	testing_environment = {
		"renderer": RenderingServer.get_current_rendering_method(),
		"adapter": RenderingServer.get_video_adapter_name(),
		"resolution": [root.size.x, root.size.y],
		"scene_began_ms_since_engine_boot": scan_start_usec / 1000.0,
		"scene_to_logical_ready_ms": ready_ms,
		"startup": game.results,
		"pipeline_at_ready": pipeline_info(),
		"reported_platform": OS.get_name(),
		"windows_hardware_confirmed": false,
		"human_playtest": false
	}
	stamp(testing_environment.merged({"finished":false,"last_completed_stage":"logical_ready"}))
	print("V34_READY ", ready_ms)
	await measure(ready_ms)
	game.queue_free()
	await process_frame
	await physics_frame
	quit()

func measure(ready_ms: float) -> void:
	await RenderingServer.frame_post_draw
	var first_draw_ms := now_ms()
	print("V36_FIRST_MALL_FRAME ", first_draw_ms)
	var first_pipeline := pipeline_info()
	var progress := testing_environment.merged({"scene_to_first_draw_ms":first_draw_ms,"pipeline_after_first_draw":first_pipeline,"finished":false,"last_completed_stage":"first_scene_draw"})
	stamp(progress)
	var entered_frame := first_draw_ms
	var intervals: Array = []
	for sample: int in limit:
		await frame()
		var current := now_ms()
		intervals.append(current - entered_frame)
		progress.frame_intervals_ms = intervals
		progress.last_completed_stage = "stationary_frame_%d" % (sample+1)
		stamp(progress)
		print("V36_STATIONARY_FRAME ",sample+1," delta_ms ",current-entered_frame)
		entered_frame = current
	var report := testing_environment.duplicate()
	report.scene_to_first_draw_ms = first_draw_ms
	report.logical_to_first_draw_ms = first_draw_ms - ready_ms
	report.pipeline_after_first_draw = first_pipeline
	report.pipeline_after_observation = pipeline_info()
	report.frame_intervals_ms = intervals
	report.static_memory_bytes = Performance.get_monitor(Performance.MEMORY_STATIC)
	report.draw_calls = Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
	report.primitives = Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)
	report.floor_supported = game.player.is_on_floor()
	report.settings = game.ui.settings.snapshot()
	report["last_completed_stage"]="stationary_complete"
	report["finished"]=false
	stamp(report)
	capture("boot")
	if measure_walk:
		report.walk = await walk_frames()
	report.finished = true
	stamp(report)
	print("V34_MEASURE_DONE ", JSON.stringify(report))

func walk_frames() -> Dictionary:
	var initial: Vector3 = game.player.position
	var previous := now_ms()
	var intervals: Array = []
	var floor_checks: Array = []
	send_key(KEY_W, true)
	for sample: int in 6:
		await frame()
		var current := now_ms()
		intervals.append(current - previous)
		floor_checks.append(game.player.is_on_floor())
		previous = current
	send_key(KEY_W, false)
	await process_frame
	return {
		"frame_intervals_ms": intervals,
		"on_floor": floor_checks,
		"moved_m": initial.distance_to(game.player.position)
	}
