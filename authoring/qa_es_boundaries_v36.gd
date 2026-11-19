extends SceneTree
## Installed flights use their ordinary streaming, controller, collisions and animation assets.
## Each compound trial starts on public floor, traverses its flight and turns on arrival.
var game: Node3D
var player: CharacterBody3D
var stream: Node
var eye_sphere := SphereShape3D.new()
var report: Dictionary
var exclusions: Array[RID] = []

func _initialize() -> void:
	call_deferred("run")

func arg(name: String, fallback: String) -> String:
	for value: String in OS.get_cmdline_user_args():
		if value.begins_with(name + "="):
			return value.trim_prefix(name + "=")
	return fallback

func xyz(p: Vector3) -> Array:
	return [p.x, p.y, p.z]

func key_w(held: bool) -> void:
	var event := InputEventKey.new()
	event.keycode = KEY_W
	event.physical_keycode = KEY_W
	event.pressed = held
	Input.parse_input_event(event)
	Input.flush_buffered_events()

func look_delta(yaw: float, pitch: float) -> void:
	var motion := InputEventMouseMotion.new()
	motion.screen_relative = Vector2(-yaw, -pitch) / .0022
	motion.relative = motion.screen_relative
	Input.parse_input_event(motion)
	Input.flush_buffered_events()

func eye_contact() -> String:
	var query := PhysicsShapeQueryParameters3D.new()
	query.shape = eye_sphere
	query.transform = Transform3D(Basis.IDENTITY, player.camera.global_position)
	query.collision_mask = 1
	query.exclude = exclusions
	var hit := player.get_world_3d().direct_space_state.intersect_shape(query, 1)
	return "" if hit.is_empty() else str(hit[0].collider.name)

func prepare(p: Vector3, dir: Vector3) -> void:
	key_w(false)
	player.input_enabled = false
	player.set_physics_process(false)
	player.reset_motion_state()
	player.global_position = p + .045 * Vector3.UP
	player.rotation = Vector3(0., atan2(-dir.x, -dir.z), 0.)
	player.camera.rotation = Vector3.ZERO
	stream.prepare_position(p)
	game.animator.ensure_near(p)
	player.reset_physics_interpolation()
	for n: int in 3:
		await physics_frame
	player.set_physics_process(true)
	player.input_enabled = true
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	for n: int in 12:
		await physics_frame

func turn_to(dir: Vector3, pitch: float = 0.) -> void:
	var yaw := atan2(-dir.x, -dir.z)
	look_delta(angle_difference(player.rotation.y, yaw), pitch - player.camera.rotation.x)

func ride(e: Dictionary, side: int) -> Dictionary:
	var up: bool = e.direction == "UP"
	var sign_dir := 1. if up else -1.
	var forward := Vector3(e.u[0], 0., e.u[1]).normalized() * sign_dir
	var right := forward.cross(Vector3.UP)
	var half := float(e.run_m) * .5
	var base := Vector3(e.c[0], e.low_y if up else e.high_y, e.c[2])
	var target_y := float(e.high_y if up else e.low_y)
	var p := base - forward * (half + 3.05) + right * (.82 * side)
	var flat_entry := base - forward * (half + 1.52) + right * (.40 * side)
	var diagonal := (flat_entry - p).normalized()
	await prepare(p, diagonal)
	var start := player.global_position
	var row := {"id": e.id, "wing": e.get("wing","B"), "levels": e.levels, "direction": e.direction,
		"side": side, "approach_angle_degrees": rad_to_deg(diagonal.angle_to(forward)), "start": xyz(start),
		"start_on_floor": player.is_on_floor() and absf(start.y - p.y) < .15,
		"input_forward_seen": false, "boarded": false, "passed_middle": false, "exited": false, "exit_turn": false,
		"mouse_movement_delivered": false, "mouse_return_delivered": false, "no_input_distance_m": 0.,
		"min_no_input_progress_m": 1000., "max_no_input_progress_m": -1000., "lost_support_ticks": 0,
		"camera_overlap_samples": 0, "camera_contacts": [], "max_vertical_tick_m": 0., "wrong_flight": "",
		"nearby_shoppers_within_3m": [], "stages": [], "pass": false}
	if not row.start_on_floor:
		row.reason = "Approach lacks intended floor support"
		return row
	var phase := "approach"
	var corrected := false
	var previous := start
	var progress_mark := -1000.
	var last_motion := 0
	var turned_start := Vector3.ZERO
	var desired_exit_direction := forward.rotated(Vector3.UP, deg_to_rad(38. if side >= 0 else -38.))
	var forward_yaw := atan2(-forward.x, -forward.z)
	var look_yaw := deg_to_rad(43. if side >= 0 else -43.)
	var look_pitch := deg_to_rad(12.)
	var look_phase := 0
	key_w(true)
	for frame: int in 2700:
		await physics_frame
		var now := player.global_position
		var progress := (now - base).dot(forward)
		var lateral := (now - base).dot(right)
		row.max_vertical_tick_m = maxf(row.max_vertical_tick_m, absf(now.y - previous.y))
		previous = now
		if not player.is_on_floor():
			row.lost_support_ticks += 1
		if frame % 12 == 0:
			row.camera_overlap_samples += 1
			var obstruction := eye_contact()
			if not obstruction.is_empty() and not row.camera_contacts.has(obstruction):
				row.camera_contacts.append(obstruction)
		if frame % 120 == 0:
			if arg("--trace","") == "yes":
				print("ES36_TRACE ",frame," ",phase," ",progress)
			for obj in game.shoppers_v18.actors:
				if is_instance_valid(obj) and obj.global_position.distance_to(now) < 3. and not row.nearby_shoppers_within_3m.has(str(obj.name)):
					row.nearby_shoppers_within_3m.append(str(obj.name))
		if not player.belt_id.is_empty() and player.belt_id != e.id:
			row.wrong_flight = player.belt_id
			row.reason = "Activated adjacent flight"
			break
		if progress > progress_mark + .035:
			progress_mark = progress
			last_motion = frame
		if phase != "turn" and frame - last_motion > 150:
			row.reason = "No forward progress at " + phase
			break
		if now.y < float(e.low_y) - .18 or now.y > float(e.high_y) + .28:
			row.reason = "Outside flight floor range"
			break
		match phase:
			"approach":
				if not corrected and progress >= -half - 1.73:
					turn_to(forward)
					corrected = true
				if player.belt_id == e.id and progress >= -half - .78:
					row.enter_lateral_m = lateral
					row.input_forward_seen = Input.is_physical_key_pressed(KEY_W)
					row.boarded = true
					row.stages.append(["aboard", frame, xyz(now)])
					key_w(false)
					phase = "ride"
			"ride":
				if not Input.is_physical_key_pressed(KEY_W):
					row.min_no_input_progress_m = minf(row.min_no_input_progress_m, progress)
					row.max_no_input_progress_m = maxf(row.max_no_input_progress_m, progress)
				if look_phase == 0 and progress > -half * .55:
					look_delta(look_yaw, look_pitch)
					look_phase = 1
				if look_phase == 1 and progress > -half * .25:
					row.mouse_movement_delivered = absf(angle_difference(player.rotation.y, forward_yaw + look_yaw)) < .014 and absf(player.camera.rotation.x - look_pitch) < .01
					look_phase = 2
				if absf(progress) < .16 and player.belt_id == e.id:
					row.passed_middle = absf(now.y - (float(e.low_y) + float(e.rise_m) * .5)) < .19
					if not row.has("mid_lateral_m"):
						row.mid_lateral_m = lateral
				if look_phase == 2 and progress > half * .30:
					turn_to(forward)
					look_phase = 3
				if progress > half + .22 and absf(now.y - target_y) < .14:
					row.mouse_return_delivered = absf(angle_difference(player.rotation.y, forward_yaw)) < .014 and absf(player.camera.rotation.x) < .012
					phase = "exit"
					key_w(true)
			"exit":
				if progress > half + 2.25 and player.belt_id.is_empty() and absf(now.y - target_y) < .12 and player.is_on_floor():
					row.exited = true
					turned_start = now
					row.stages.append(["alighted", frame, xyz(now)])
					turn_to(desired_exit_direction)
					phase = "turn"
			"turn":
				var delta := now - turned_start
				if delta.dot(desired_exit_direction) > .78:
					row.exit_turn = absf(angle_difference(player.rotation.y, atan2(-desired_exit_direction.x,-desired_exit_direction.z))) < .014 and absf(now.y - target_y) < .14 and player.is_on_floor() and absf(delta.dot(right)) > .23
					row.stages.append(["walk_after_turn", frame, xyz(now)])
					break
	key_w(false)
	row.end = xyz(player.global_position)
	row.target_level_error_m = absf(player.global_position.y - target_y)
	row.no_input_distance_m = maxf(0., row.max_no_input_progress_m - row.min_no_input_progress_m)
	var edge_ok := side == 0 or (signf(float(row.get("enter_lateral_m", 0.))) == side and absf(float(row.get("enter_lateral_m", 0.))) >= .19)
	row.pass = row.boarded and row.input_forward_seen and edge_ok and row.passed_middle and row.exited and row.exit_turn and row.no_input_distance_m >= float(e.run_m) -.55 and row.mouse_movement_delivered and row.mouse_return_delivered and row.lost_support_ticks == 0 and row.camera_contacts.is_empty() and row.max_vertical_tick_m < .12 and row.wrong_flight.is_empty()
	if not row.pass and not row.has("reason"):
		row.reason = "One or more logged assertions failed"
	return row

func save(path: String) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	file.store_string(JSON.stringify(report))
	file.close()

func run() -> void:
	RenderingServer.set_render_loop_enabled(false)
	game = load("res://main.tscn").instantiate()
	game.mode = "es36-physical"
	root.add_child(game)
	while game.results.is_empty():
		await process_frame
	Engine.max_fps = 0
	Engine.max_physics_steps_per_frame = 24
	RenderingServer.set_render_loop_enabled(false)
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	player = game.player
	stream = game.get_node("V30_Runtime")
	game.elevators.set_physics_process(false)
	game.shoppers_v18.set_enabled(true, true)
	game.shoppers_v18.set_frozen(false)
	game.animator.paused = false
	# Tread/rail render-state time/direction is exercised separately; collision bodies stay enabled.
	game.animator.set_process(false)
	eye_sphere.radius = .08
	exclusions.assign([player.get_rid()])
	var selected := arg("--match", "")
	var out := arg("--out", "user://es-boundaries-v36.json")
	var flights: Array = game.manifest.escalators.duplicate()
	flights.sort_custom(func(a,b): return str(a.id) < str(b.id))
	report = {"complete": false, "method": "Godot x11, actual player and native relative mouse events. Start on public floor 3.05m before slope. Centre and +/-15 degree approaches from 0.82m lateral to near edges. W is released for full transport, real mouse look is rotated then restored, player turns 38 degrees and walks away. 8cm camera sphere sampled every 12 physics ticks. Shipped NPC traffic enabled; no crowd fabricated.", "NPC_enabled": game.shoppers_v18.enabled, "human_playtest": false,
		"display": DisplayServer.get_name(), "renderer":RenderingServer.get_current_rendering_method(), "native_screen_rendered": false, "sim_hz": Engine.physics_ticks_per_second, "rows": []}
	for e: Dictionary in flights:
		if not selected.is_empty() and not str(e.id).contains(selected):
			continue
		for side: int in [0,-1,1]:
			var row := await ride(e,side)
			report.rows.append(row)
			print("ES36_RIDE ",e.id," ",side, " ",row.pass," ",row.get("reason","")," ",row.get("enter_lateral_m",0.)," ",row.mouse_movement_delivered," ",row.mouse_return_delivered, " ",row.exit_turn," ",row.camera_contacts)
		save(out)
	report.complete = true
	report.passed = report.rows.filter(func(r): return r.pass).size()
	report.failed = report.rows.size() - report.passed
	save(out)
	print("ES36_END ",report.passed,"/",report.rows.size())
	game.queue_free()
	await process_frame
	await physics_frame
	quit(0 if report.failed == 0 else 1)
