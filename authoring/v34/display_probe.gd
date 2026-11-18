extends SceneTree
var output_dir: String
var camera_file: String
var stage: String = "measure"
var limit: int = 8
var measure_travel: bool = false
var measure_walk: bool = false
var game: Node3D
var testing_environment: Dictionary
var scan_start_usec: int

func _initialize() -> void:
	call_deferred("run")

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
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--out="):
			output_dir = arg.trim_prefix("--out=")
		elif arg.begins_with("--shots="):
			camera_file = arg.trim_prefix("--shots=")
		elif arg.begins_with("--frames="):
			limit = int(arg.trim_prefix("--frames="))
		elif arg == "--travel":
			measure_travel = true
		elif arg == "--walk":
			measure_walk = true
		elif arg == "--capture":
			stage = "capture"
	DirAccess.make_dir_recursive_absolute(output_dir)
	scan_start_usec = Time.get_ticks_usec()
	if stage == "capture":
		RenderingServer.set_render_loop_enabled(false)
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
		"windows": false,
		"human_playtest": false
	}
	print("V34_READY ", ready_ms)
	if stage == "capture":
		await capture_shots()
	else:
		await measure(ready_ms)
	game.queue_free()
	await process_frame
	await physics_frame
	quit()

func measure(ready_ms: float) -> void:
	await RenderingServer.frame_post_draw
	var first_draw_ms := now_ms()
	var entered_frame := first_draw_ms
	var intervals: Array = []
	for sample: int in limit:
		await frame()
		var current := now_ms()
		intervals.append(current - entered_frame)
		entered_frame = current
	var report := testing_environment.duplicate()
	report.scene_to_first_draw_ms = first_draw_ms
	report.logical_to_first_draw_ms = first_draw_ms - ready_ms
	report.frame_intervals_ms = intervals
	report.static_memory_bytes = Performance.get_monitor(Performance.MEMORY_STATIC)
	report.draw_calls = Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
	report.primitives = Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)
	report.floor_supported = game.player.is_on_floor()
	report.settings = game.ui.settings.snapshot()
	capture("boot")
	if measure_walk:
		report.walk = await walk_frames()
	if measure_travel:
		report.wing_travel = await wing_travel()
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

func wing_travel() -> Array:
	var shots: Array = game.read_json("res://source/cameras-v8.json")
	var results: Array = []
	for index: int in [2, 4, 0]:
		var key := KEY_F1 + int(index / 2.0)
		var point: Vector3 = game.v3(shots[index].get("walk_eye", shots[index].eye)) - Vector3.UP * 1.65
		var t := now_ms()
		send_key(key, true)
		await process_frame
		send_key(key, false)
		var first := -1.0
		var playable := -1.0
		var end := t + 180000.0
		while now_ms() < end:
			await frame()
			if first < 0.0:
				first = now_ms() - t
			if game.player.position.distance_to(point) < 0.5 and game.player.is_on_floor() and game.player.input_enabled:
				playable = now_ms() - t
				break
		var result := {
			"key": key,
			"first_draw_ms": first,
			"at_destination_visible_and_supported_ms": playable,
			"position": [game.player.position.x, game.player.position.y, game.player.position.z],
			"pass": playable >= 0.0,
		}
		results.append(result)
		print("V34_TRAVEL ", JSON.stringify(result))
	return results

func capture_shots() -> void:
	game.player.set_physics_process(false)
	game.player.input_enabled = false
	game.shoppers_v18.set_enabled(false, true)
	game.animator.paused = true
	game.hud.get_parent().hide()
	var shots: Array = JSON.parse_string(FileAccess.get_file_as_string(camera_file))
	var rows: Array = []
	for shot: Dictionary in shots:
		RenderingServer.set_render_loop_enabled(false)
		game.player.position = game.v3(shot.eye) - Vector3.UP * 1.65
		game.player.rotation = Vector3.ZERO
		game.player.camera.position = Vector3.UP * 1.65
		game.player.camera.fov = float(shot.get("fov", 72.0))
		game.player.camera.look_at(game.v3(shot.look))
		game.player.reset_physics_interpolation()
		game.player.camera.force_update_transform()
		await game.get_node("V30_Runtime").settle()
		game.get_node("V31_Sales").update_near()
		var art := game.get_node_or_null("V34_Mall_Art")
		if art != null:
			art.update_near()
		game.animator.set_time(1.75)
		RenderingServer.set_render_loop_enabled(true)
		for i in 2:
			await frame()
		capture(shot.id)
		rows.append(shot)
		stamp({"complete": false, "conditions": testing_environment, "shots": rows})
	stamp({"complete": true, "conditions": testing_environment, "shots": rows})
