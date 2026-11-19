extends SceneTree

var game: Node3D
var sound: Node
var rows: Array[Dictionary] = []

func _initialize() -> void:
	call_deferred("run")

func record(name: String, result: bool, detail = null) -> void:
	rows.append({"name": name, "pass": result, "detail": detail})
	print("V36_QA ", name, ": ", result)

func input_key(code: int, pressed: bool) -> void:
	var event := InputEventKey.new()
	event.keycode = code
	event.physical_keycode = code
	event.pressed = pressed
	Input.parse_input_event(event)

func key(code: int) -> void:
	input_key(code, true)
	await process_frame
	input_key(code, false)
	await process_frame

func run() -> void:
	RenderingServer.set_render_loop_enabled(false)
	game = (load("res://main.tscn") as PackedScene).instantiate()
	root.add_child(game)
	for tick in 2400:
		if not game.results.is_empty():
			break
		await process_frame
	record("Normal startup", not game.results.is_empty() and not game.results.get("startup_failed", false), game.results.get("version"))
	if game.results.is_empty():
		export_and_quit()
		return
	Engine.max_fps = 0
	for i in 8:
		await physics_frame
	sound = game.get_node_or_null("MallSound")
	record("Original audio assets loaded", sound != null and sound.tile_clips.size() == 5 and sound.paving_clips.size() == 5 and sound.interior.stream.loop and sound.courtyard.stream.loop)
	record("Location display", game.mall_presentation != null and String(game.hud.text).contains("A館"), game.hud.text)
	if sound != null:
		var initial: Vector3 = game.player.position
		var baseline_steps: int = sound.sequence
		input_key(KEY_W, true)
		for i in 70:
			await physics_frame
		input_key(KEY_W, false)
		for i in 14:
			await physics_frame
		record("Real walk produces footsteps", initial.distance_to(game.player.position) > 1.8 and sound.sequence > baseline_steps, [initial.distance_to(game.player.position), sound.sequence])
		var still: int = sound.sequence
		for i in 40:
			await physics_frame
		record("Standing produces no footsteps", sound.sequence == still)
		record("C atmosphere classifies courtyard and cafe", sound.is_outdoor(Vector3(-94.53, 0, -220)) and not sound.is_outdoor(Vector3(-91.28, 0, -211.6)))
	game.mall_presentation.controls_until = 0
	await key(KEY_H)
	record("H restores controls", game.mall_presentation.controls_until > Time.get_ticks_msec())
	await key(KEY_M)
	record("Map pauses walking", game.ui.overlay == "map" and not game.player.input_enabled)
	await key(KEY_ESCAPE)
	await key(KEY_ESCAPE)
	record("Settings open", game.ui.overlay == "settings")
	game.ui.settings.config_path = "user://v36-test-settings.cfg"
	game.ui.settings.sound_level = 0.21
	game.ui.settings.apply()
	var saved := ConfigFile.new()
	var save_ok := saved.load("user://v36-test-settings.cfg") == OK
	record("Audio level persisted", save_ok and is_equal_approx(float(saved.get_value("sound", "level", 0.0)), 0.21))
	await key(KEY_ESCAPE)
	record("Esc returns to walking", game.player.input_enabled and game.ui.overlay == "")
	var assets = game.get_node_or_null("V35_Mall_Art")
	record("A/B/C local art modules attached", assets != null and assets.designers.size() == 7, assets.designers.size() if assets != null else 0)
	export_and_quit()

func export_and_quit() -> void:
	var path := OS.get_cmdline_user_args()[-1].trim_prefix("--out=")
	var output := FileAccess.open(path, FileAccess.WRITE)
	if output != null:
		output.store_string(JSON.stringify({"rows": rows, "human_playtest": false}, "  "))
		output.close()
	var passed := rows.all(func(r): return r["pass"])
	game.queue_free()
	await process_frame
	await physics_frame
	quit(0 if passed else 1)
