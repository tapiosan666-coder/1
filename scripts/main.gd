extends Node3D

var run: IdentityRun
var mall: Mall
var crowd: Crowd
var player: ScannerPlayer
var hud: FindHUD
var audio: ScanAudio
var effects: Node3D
var ammo := 30
var shot_cooldown := 0.0
var reload_left := 0.0
var sonar_left := 0.0
var pulse_left := 0.0
var elapsed := 0.0
var combo := 0
var combo_left := 0.0
var target: Dictionary = {}
var handheld_scan := HandheldScan.new()
var using_gun := false
var cat: Node3D
var cat_target := -1
var cat_scan_time := 0.0
var cat_retarget := 0.0
var beacon: Node3D
var selected_skin := Color("cfaa89")
var selected_hair := Color("33312c")
var selected_width := 1.0

func _ready() -> void:
	_configure_input()
	_setup_environment()
	mall = Mall.new()
	add_child(mall)
	effects = Node3D.new()
	add_child(effects)
	audio = ScanAudio.new()
	add_child(audio)
	player = ScannerPlayer.new()
	add_child(player)
	player.position = Vector3(0, 0.1, 12)
	player.camera.rotation.x = -0.03
	player.fired.connect(fire)
	player.reload_requested.connect(reload_gun)
	var canvas := CanvasLayer.new()
	add_child(canvas)
	hud = FindHUD.new()
	canvas.add_child(hud)
	hud.play_pressed.connect(_from_title)
	hud.resume_pressed.connect(func(): set_mode("play"))
	hud.restart_pressed.connect(func(): start_run())
	hud.skill_pressed.connect(buy_skill)
	hud.exit_pressed.connect(func(): get_tree().quit())
	# A preview crowd shares the exact same identity model as a playable run.
	_create_run(120, 24)
	set_mode("title")
	if "--capture" in OS.get_cmdline_user_args():
		_capture.call_deferred()

func _from_title() -> void:
	selected_skin = [Color("cfaa89"), Color("815f49"), Color("d9b0a1")][hud.skin_select.selected]
	selected_hair = [Color("33312c"), Color("6c4735"), Color("bdc2bb")][hud.hair_select.selected]
	selected_width = hud.face_slider.value
	start_run()

func _create_run(count: int, run_seed: int = -1) -> void:
	if is_instance_valid(crowd):
		remove_child(crowd)
		crowd.queue_free()
	for child in effects.get_children():
		effects.remove_child(child)
		child.queue_free()
	cat = null
	beacon = null
	cat_target = -1
	cat_retarget = 0
	cat_scan_time = 0
	run = IdentityRun.new(count, run_seed)
	crowd = Crowd.new()
	crowd.skin_color = selected_skin
	crowd.hair_color = selected_hair
	crowd.face_width = selected_width
	add_child(crowd)
	crowd.process_mode = Node.PROCESS_MODE_PAUSABLE
	crowd.setup(run, mall.spawn_points)
	hud.run = run
	ammo = run.magazine_size()
	elapsed = 0
	combo = 0
	combo_left = 0
	reload_left = 0
	shot_cooldown = 0
	sonar_left = 0
	pulse_left = 0
	target = {}
	using_gun = false
	handheld_scan.reset()
	hud.combo = 0
	hud.notice_time = 0
	hud.hit_time = 0

func start_run(count: int = 120, run_seed: int = -1) -> void:
	_create_run(count, run_seed)
	player.position = Vector3(0, 0.1, 12)
	player.rotation = Vector3.ZERO
	player.camera.rotation = Vector3.ZERO
	set_mode("play")
	hud.message("Hold LMB on one person for 2 seconds. TAB: unlock equipment.")

func set_mode(mode: String) -> void:
	hud.show_mode(mode)
	player.enabled = mode == "play"
	_update_equipment()
	if mode != "play":
		handheld_scan.reset()
	# Pausing the tree preserves timers, NPC positions and ability snapshots.
	get_tree().paused = mode not in ["play", "title"]
	process_mode = Node.PROCESS_MODE_ALWAYS
	player.process_mode = Node.PROCESS_MODE_PAUSABLE
	effects.process_mode = Node.PROCESS_MODE_PAUSABLE
	hud.process_mode = Node.PROCESS_MODE_ALWAYS
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED if mode == "play" else Input.MOUSE_MODE_VISIBLE

func _input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed or event.echo:
		return
	if event.keycode == KEY_ESCAPE:
		if hud.mode == "play":
			set_mode("pause")
		elif hud.mode in ["pause", "skills", "map"]:
			set_mode("play")
	elif event.keycode == KEY_TAB:
		if hud.mode == "play":
			set_mode("skills")
		elif hud.mode == "skills":
			set_mode("play")
	elif event.keycode == KEY_M:
		if hud.mode == "play":
			set_mode("map")
		elif hud.mode == "map":
			set_mode("play")
	elif event.keycode == KEY_F and hud.mode == "play":
		sonar()
	elif event.keycode == KEY_Q and hud.mode == "play":
		pulse()
	elif event.keycode == KEY_1 and hud.mode == "play":
		equip(false)
	elif event.keycode == KEY_2 and hud.mode == "play":
		equip(true)

func _physics_process(delta: float) -> void:
	if hud.mode != "play":
		return
	elapsed += delta
	shot_cooldown = maxf(0, shot_cooldown - delta)
	sonar_left = maxf(0, sonar_left - delta)
	pulse_left = maxf(0, pulse_left - delta)
	combo_left -= delta
	if combo_left <= 0:
		combo = 0
	if reload_left > 0:
		reload_left = maxf(0, reload_left - delta)
		if reload_left <= 0:
			ammo = run.magazine_size()
	target = ray_target()
	hud.target_id = int(target.collider.get_meta("identity")) if not target.is_empty() and target.collider.has_meta("identity") else -1
	if not using_gun:
		_tick_handheld(delta, Input.is_action_pressed("fire"))
	hud.using_gun = using_gun
	hud.scan_progress = handheld_scan.seconds / IdentityRun.HANDHELD_SECONDS
	player.reader_screen.text = "READING\n%03d%%" % int(hud.scan_progress * 100) if hud.scan_progress > 0 else "IDENTITY\nREADER"
	hud.ammo = ammo
	hud.player_position = player.position
	hud.elapsed = elapsed
	hud.sonar_cooldown = sonar_left
	hud.pulse_cooldown = pulse_left
	hud.reload_progress = 1.0 - reload_left / run.reload_seconds() if reload_left > 0 else -1.0
	player.sprint_multiplier = 1.0 + run.upgrades.sprint * 0.25
	if run.located:
		hud.target_distance = player.position.distance_to(crowd.positions[run.true_id])
		if is_instance_valid(beacon):
			beacon.position = crowd.positions[run.true_id] + Vector3.UP * 2.6
	_tick_cat(delta)

func ray_target() -> Dictionary:
	var from := player.camera.global_position
	var reach := run.scan_range() if using_gun else IdentityRun.HANDHELD_RANGE
	var to := from - player.camera.global_transform.basis.z * reach
	var query := PhysicsRayQueryParameters3D.create(from, to, 3, [player.get_rid()])
	query.collide_with_areas = true
	return get_world_3d().direct_space_state.intersect_ray(query)

func fire() -> void:
	if not using_gun or run.upgrades.gun == 0 or hud.mode != "play" or reload_left > 0 or shot_cooldown > 0:
		return
	if ammo <= 0:
		reload_gun()
		return
	ammo -= 1
	shot_cooldown = 0.16
	player.recoil = 0.065
	audio.play("shot", randf_range(0.94, 1.06))
	var hit := ray_target()
	if hit.is_empty():
		return
	var at: Vector3 = hit.position
	_spark(at)
	if hit.collider.has_meta("identity"):
		resolve(int(hit.collider.get_meta("identity")), IdentityRun.Source.GUN)

func reload_gun() -> void:
	if not using_gun or hud.mode != "play" or reload_left > 0 or ammo >= run.magazine_size():
		return
	reload_left = run.reload_seconds()
	audio.play("reload")

func resolve(id: int, source: IdentityRun.Source) -> IdentityRun.Result:
	var outcome := run.scan(id, source)
	if outcome == IdentityRun.Result.HIT:
		hud.hit_time = 0.12
		audio.play("hit", 0.8 + float(run.hits[id]) * 0.12)
	elif outcome == IdentityRun.Result.FAKE:
		crowd.fall(id)
		_hole(crowd.positions[id])
		combo += 1
		combo_left = 3.0
		hud.combo = combo
		hud.hit_time = 0.2
		hud.message("IMITATION CLEARED   +10 AP")
		audio.play("fall", minf(1.5, 1 + combo * 0.025))
	elif outcome == IdentityRun.Result.LOCATED:
		_mark_original()
		hud.message("ORIGINAL LOCATED. Press 1: finish with the original reader.")
	elif outcome == IdentityRun.Result.FOUND:
		audio.play("found")
		set_mode("win")
	return outcome

func equip(gun_selected: bool) -> bool:
	if gun_selected and run.upgrades.gun == 0:
		hud.message("Unlock SCAN PISTOL in TAB first / %d AP." % run.price("gun"))
		return false
	using_gun = gun_selected
	handheld_scan.reset()
	_update_equipment()
	return true

func _update_equipment() -> void:
	player.using_gun = using_gun
	player.gun.visible = hud.mode == "play" and using_gun
	player.handheld.visible = hud.mode == "play" and not using_gun

func _tick_handheld(delta: float, held: bool) -> void:
	if hud.mode != "play" or using_gun:
		handheld_scan.reset()
		return
	var hit := ray_target()
	var id := -1
	if not hit.is_empty() and hit.collider.has_meta("identity"):
		id = int(hit.collider.get_meta("identity"))
		if run.eliminated[id]:
			id = -1
	var finished := handheld_scan.tick(delta, id, held)
	if finished >= 0:
		resolve(finished, IdentityRun.Source.HANDHELD)
		audio.play("hit", 1.25)

func buy_skill(key: String) -> void:
	if run.purchase(key):
		audio.play("hit")
		if key == "cat":
			_make_cat()
		hud.show_mode("skills")

func sonar() -> Array[Vector3]:
	var snapshots: Array[Vector3] = []
	if run.upgrades.sonar <= 0:
		hud.message("Unlock ECHO SONAR in the skill panel [TAB].")
		return snapshots
	if sonar_left > 0:
		return snapshots
	sonar_left = 12
	var radius: float = [15, 30, 50, 80, 120][run.upgrades.sonar - 1]
	for id in crowd.live_positions_in_radius(player.position, radius):
		var p := crowd.positions[id] + Vector3.UP * 1.1
		snapshots.append(p)
		var mat := Shapes.material(Color("f4bf8d"), 1.0)
		mat.no_depth_test = true
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		var marker := Shapes.sphere(effects, p, 0.18, mat)
		get_tree().create_timer(4.0, false).timeout.connect(marker.queue_free)
	_ring(player.position, radius, Color("b2f09a"))
	audio.play("sonar")
	hud.message("ECHO CAPTURED / %d positions / 4 seconds / no tracking" % snapshots.size())
	return snapshots

func pulse() -> void:
	if run.upgrades.pulse <= 0:
		hud.message("Unlock RADIAL SCAN in the skill panel [TAB].")
		return
	if pulse_left > 0:
		return
	pulse_left = 25
	var radius: float = 4.0 + run.upgrades.pulse * 4.0
	var ids := crowd.live_positions_in_radius(player.position, radius)
	for id in ids:
		resolve(id, IdentityRun.Source.SPECIAL)
	_ring(player.position, radius, Color("f3b588"))
	audio.play("sonar", 0.65)

func _mark_original() -> void:
	if is_instance_valid(beacon):
		return
	beacon = Node3D.new()
	effects.add_child(beacon)
	var mat := Shapes.material(Color("b6ff94"), 1)
	mat.no_depth_test = true
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	Shapes.sphere(beacon, Vector3.ZERO, 0.25, mat)
	var label := Shapes.sign_text(beacon, Vector3(0, 0.55, 0), "ORIGINAL\n[1] IDENTITY READER", 28, Color("b6ff94"))
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.no_depth_test = true
	audio.play("found", 1.3)

func _make_cat() -> void:
	cat = Node3D.new()
	effects.add_child(cat)
	cat.position = player.position + Vector3(1, 0, 1)
	var fur := Shapes.material(Color("c68c56"))
	var dark := Shapes.material(Color("34424a"))
	Shapes.box(cat, Vector3(0, 0.35, 0), Vector3(0.32, 0.35, 0.65), fur)
	Shapes.box(cat, Vector3(0, 0.55, -0.27), Vector3(0.34, 0.32, 0.3), fur)
	for x in [-0.12, 0.12]:
		Shapes.box(cat, Vector3(x, 0.77, -0.27), Vector3(0.1, 0.15, 0.12), fur)
		Shapes.box(cat, Vector3(x, 0.58, -0.425), Vector3(0.035, 0.055, 0.015), dark)
		for z in [-0.2, 0.2]:
			Shapes.box(cat, Vector3(x, 0.12, z), Vector3(0.08, 0.24, 0.08), fur)
	var tail := Shapes.box(cat, Vector3(0, 0.51, 0.44), Vector3(0.08, 0.5, 0.08), fur)
	tail.rotation.x = 0.5
	cat_scan_time = 0
	cat_target = -1

func _tick_cat(delta: float) -> void:
	if not is_instance_valid(cat):
		return
	if cat_target < 0 or run.eliminated[cat_target] or (cat_target == run.true_id and run.located):
		cat_target = -1
		var nearest := INF
		for id in run.population:
			if run.eliminated[id] or (id == run.true_id and run.located):
				continue
			var dist := cat.position.distance_squared_to(crowd.positions[id])
			if dist < nearest:
				nearest = dist
				cat_target = id
		cat_scan_time = 0
		cat_retarget = 0
	if cat_target < 0:
		return
	var destination := crowd.positions[cat_target]
	cat_retarget -= delta
	if cat_retarget <= 0:
		cat.set_meta("path", crowd.nav.get_point_path(crowd.nav.get_closest_point(cat.position), crowd.nav.get_closest_point(destination)))
		cat_retarget = 1.0
	var path: PackedVector3Array = cat.get_meta("path", PackedVector3Array())
	var distance := cat.position.distance_to(destination)
	if distance > 0.9:
		if path.is_empty():
			# Final short approach is allowed only inside the walkable region.
			var step := cat.position.move_toward(destination, delta * 4)
			if Mall.walkable(step):
				cat.position = step
		elif cat.position.distance_to(path[0]) < 0.15:
			path.remove_at(0)
			cat.set_meta("path", path)
		elif not path.is_empty():
			var direction := path[0] - cat.position
			cat.position = cat.position.move_toward(path[0], delta * 4)
			cat.rotation.y = atan2(-direction.x, -direction.z)
	else:
		cat_scan_time += delta
		cat.rotation.z = sin(cat_scan_time * 8) * 0.1
		var seconds: float = [20.0, 12.0, 6.0][run.upgrades.cat_speed]
		if cat_scan_time >= seconds:
			resolve(cat_target, IdentityRun.Source.SPECIAL)
			cat_target = -1
			cat.rotation.z = 0

func _spark(at: Vector3) -> void:
	var spark := Shapes.sphere(effects, at, 0.09, Shapes.material(Color("b6ff94"), 1))
	var tween := create_tween()
	tween.tween_property(spark, "scale", Vector3.ONE * 2.5, 0.06)
	tween.tween_property(spark, "scale", Vector3.ZERO, 0.12)
	tween.tween_callback(spark.queue_free)

func _hole(at: Vector3) -> void:
	var hole := Shapes.cylinder(effects, at + Vector3.UP * 0.04, 0.58, 0.025, Shapes.material(Color("071016")))
	var tween := create_tween()
	tween.tween_interval(0.7)
	tween.tween_property(hole, "scale", Vector3.ZERO, 0.3)
	tween.tween_callback(hole.queue_free)

func _ring(at: Vector3, radius: float, color: Color) -> void:
	var mesh := TorusMesh.new()
	mesh.inner_radius = 0.95
	mesh.outer_radius = 1.0
	mesh.rings = 48
	mesh.ring_segments = 8
	var node := MeshInstance3D.new()
	node.mesh = mesh
	node.material_override = Shapes.material(color, 1)
	effects.add_child(node)
	node.position = at + Vector3.UP * 0.07
	var tween := create_tween()
	tween.tween_property(node, "scale", Vector3(radius, 1, radius), 0.8)
	tween.tween_callback(node.queue_free)

func _configure_input() -> void:
	var keys := {"forward": KEY_W, "back": KEY_S, "left": KEY_A, "right": KEY_D, "jump": KEY_SPACE, "sprint": KEY_SHIFT, "reload": KEY_R}
	for key in keys:
		if not InputMap.has_action(key):
			InputMap.add_action(key)
		var event := InputEventKey.new()
		event.physical_keycode = keys[key]
		InputMap.action_add_event(key, event)
	for action in ["fire", "aim"]:
		if not InputMap.has_action(action):
			InputMap.add_action(action)
		var event := InputEventMouseButton.new()
		event.button_index = MOUSE_BUTTON_LEFT if action == "fire" else MOUSE_BUTTON_RIGHT
		InputMap.action_add_event(action, event)

func _setup_environment() -> void:
	var environment := WorldEnvironment.new()
	var settings := Environment.new()
	settings.background_mode = Environment.BG_SKY
	var sky := Sky.new()
	var sky_material := ProceduralSkyMaterial.new()
	sky_material.sky_top_color = Color("8daebf")
	sky_material.sky_horizon_color = Color("e8e6d9")
	sky.sky_material = sky_material
	settings.sky = sky
	settings.background_color = Color("101f29")
	settings.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	settings.ambient_light_color = Color("e2e7d6")
	settings.ambient_light_energy = 0.32
	settings.tonemap_exposure = 0.85
	settings.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	environment.environment = settings
	add_child(environment)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-58, -24, 0)
	sun.light_color = Color("fff0d1")
	sun.light_energy = 0.8
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 85
	add_child(sun)
	for x in [-22.0, 0.0, 22.0]:
		var light := OmniLight3D.new()
		light.position = Vector3(x, 5, 0)
		light.omni_range = 27
		light.light_color = Color("cfe7d7")
		light.light_energy = 0.85
		add_child(light)

func _capture() -> void:
	await get_tree().create_timer(2).timeout
	get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-title.png")
	start_run(120, 912)
	await get_tree().create_timer(2).timeout
	get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-play.png")
	# A dedicated development capture exercises a partial original-reader lock.
	crowd.positions[0] = Vector3(11, 0, 7)
	crowd.bodies[0].position = Vector3(11, 0.95, 7)
	crowd.waits[0] = 30
	crowd.headings[0] = PI
	player.position = Vector3(11, 0.1, 10.4)
	player.velocity = Vector3.ZERO
	player.camera.look_at(Vector3(11, 1.55, 7))
	await get_tree().physics_frame
	Input.action_press("fire")
	await get_tree().create_timer(0.9).timeout
	get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-reader.png")
	Input.action_release("fire")
	set_mode("skills")
	await get_tree().create_timer(0.5).timeout
	get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-skills.png")
	get_tree().quit()
