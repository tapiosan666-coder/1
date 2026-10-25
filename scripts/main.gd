extends Node3D

var loot: RunLoot
var caches: CacheField
var speech: NpcSpeech
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
var chain_left := 0.0
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
var cat_clock := 0.0
var cat_skipped: Dictionary = {}
var cat_planned_at := Vector3.ZERO
var cat_candidates: Array[int] = []
var frame_samples := PackedFloat32Array()
var last_frame_usec := 0
var frame_report_left := 0.0
var beacon: Node3D
var selected_skin := Color("cfaa89")
var selected_hair := Color("33312c")
var selected_width := 1.0
var graphics_choice := "balanced"
var doors: DoorField
var store_signs: StoreSigns

func _ready() -> void:
	_configure_input()
	_setup_environment()
	mall = Mall.new()
	add_child(mall)
	store_signs=StoreSigns.new();add_child(store_signs);store_signs.setup(mall)
	effects = Node3D.new()
	add_child(effects)
	audio = ScanAudio.new()
	add_child(audio)
	player = ScannerPlayer.new()
	add_child(player)
	player.position = Mall.ENTRANCE
	player.rotation.y = -PI / 2
	player.camera.rotation.x = -0.03
	player.fired.connect(fire)
	player.reload_requested.connect(reload_gun)
	doors=DoorField.new();add_child(doors);doors.setup(self)
	var canvas := CanvasLayer.new()
	add_child(canvas)
	hud = FindHUD.new()
	canvas.add_child(hud)
	hud.play_pressed.connect(_from_title)
	hud.resume_pressed.connect(func(): set_mode("play"))
	hud.restart_pressed.connect(func(): start_run(run.population))
	hud.skill_pressed.connect(buy_skill)
	hud.item_selected.connect(_select_item)
	hud.graphics_selected.connect(_select_graphics)
	hud.adapter_name = RenderingServer.get_video_adapter_name()
	if hud.adapter_name.is_empty(): hud.adapter_name = "取得できません"
	graphics_choice = GraphicsOptions.load_choice()
	hud.travel_pressed.connect(fast_travel)
	hud.exit_pressed.connect(func(): get_tree().quit())
	# A preview crowd shares the exact same identity model as a playable run.
	_create_run(300, 24)
	set_mode("title")
	if "--population-smoke" in OS.get_cmdline_user_args():
		start_run(1000,912)
		print("POPULATION_SMOKE identities=",run.population," fixed=",crowd.slots.size()," walking=",crowd.roles.count("walking"))
	if "--capture-realism" in OS.get_cmdline_user_args():
		_capture_realism.call_deferred()
	if "--capture-people" in OS.get_cmdline_user_args():
		_capture_people.call_deferred()
	if "--capture-interiors" in OS.get_cmdline_user_args():
		_capture_interiors.call_deferred()
	if "--capture-stores" in OS.get_cmdline_user_args():
		_capture_stores.call_deferred()
	if "--capture-art" in OS.get_cmdline_user_args():
		_capture_art.call_deferred()
	if "--capture-growth" in OS.get_cmdline_user_args():
		_capture_growth.call_deferred()
	if "--capture-c-wing" in OS.get_cmdline_user_args():
		_capture_c_wing.call_deferred()
	if "--capture-b-wing" in OS.get_cmdline_user_args():
		_capture_b_wing.call_deferred()
	if "--capture-annex" in OS.get_cmdline_user_args():
		_capture_annex.call_deferred()
	if "--capture-bag" in OS.get_cmdline_user_args():
		_capture_bag.call_deferred()
	if "--capture-mall" in OS.get_cmdline_user_args():
		_capture_mall.call_deferred()
	if "--capture-overview" in OS.get_cmdline_user_args():
		_capture_overview.call_deferred()
	if "--capture" in OS.get_cmdline_user_args():
		_capture.call_deferred()

func _from_title(population:int) -> void:
	selected_skin = [Color("cfaa89"), Color("815f49"), Color("d9b0a1")][hud.skin_select.selected]
	selected_hair = [Color("33312c"), Color("6c4735"), Color("bdc2bb")][hud.hair_select.selected]
	selected_width = hud.face_slider.value
	start_run(population)

func _create_run(count: int, run_seed: int = -1) -> void:
	frame_samples.clear(); last_frame_usec = 0; frame_report_left = 0
	if is_instance_valid(crowd):
		remove_child(crowd)
		crowd.queue_free()
	for child in effects.get_children():
		effects.remove_child(child)
		child.queue_free()
	cat = null
	hud.cat_status = ""
	beacon = null
	cat_target = -1
	cat_retarget = 0
	cat_clock = 0; cat_skipped.clear()
	cat_candidates.clear()
	cat_scan_time = 0
	run = IdentityRun.new(count, run_seed)
	if hud.debug_scan_skills:run.enable_debug_scan_skills()
	crowd = Crowd.new()
	crowd.skin_color = selected_skin
	crowd.hair_color = selected_hair
	crowd.face_width = selected_width
	crowd.slots = PopulationLayout.slots(mall,count)
	add_child(crowd)
	crowd.process_mode = Node.PROCESS_MODE_PAUSABLE
	crowd.setup(run, mall.spawn_points)
	NavigationPolicy.configure(crowd.nav)
	doors.reset()
	loot = RunLoot.new(mall.spawn_points,run_seed)
	caches = CacheField.new(); effects.add_child(caches); caches.setup(loot)
	speech = NpcSpeech.new(); effects.add_child(speech)
	hud.loot = loot
	GraphicsOptions.apply(self,graphics_choice,false)
	player.cart_boost = 1
	player.cart.visible = false
	hud.run = run
	ammo = run.magazine_size()
	elapsed = 0
	combo = 0
	combo_left = 0
	reload_left = 0
	shot_cooldown = 0
	sonar_left = 0
	chain_left = 0
	player.air_jump_used = false
	player.double_jump_enabled = false
	pulse_left = 0
	target = {}
	using_gun = false
	handheld_scan.reset()
	hud.combo = 0
	hud.notice_time = 0
	hud.hit_time = 0

func start_run(count: int = 1000, run_seed: int = -1) -> void:
	_create_run(count, run_seed)
	player.position = Mall.ENTRANCE
	player.rotation = Vector3(0, -PI / 2, 0)
	player.camera.rotation = Vector3.ZERO
	_visit_points(false)
	set_mode("play")
	hud.message("デバッグ：スキャン系スキル解放済み。1：初期スキャナー／2：銃。" if run.debug_scan_skills else "1人を狙って左クリックを2秒長押し。Tabでスキルを購入。")

func set_mode(mode: String) -> void:
	if is_instance_valid(speech): speech.dismiss()
	hud.player_position = player.position
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
		elif hud.mode in ["pause", "skills", "map", "inventory"]:
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
	elif event.keycode == KEY_I and hud.mode in ["play","inventory"]:
		set_mode("inventory" if hud.mode == "play" else "play")
	elif event.keycode == KEY_G and hud.mode == "play":
		open_cache()
	elif event.keycode == KEY_X and hud.mode == "play":
		use_item()
	elif event.keycode == KEY_F and hud.mode == "play":
		var interaction:=doors.interact(player.camera)
		if interaction==DoorField.Interaction.NONE:
			if MallGuide.targeted(player.camera):
				set_mode("map");hud.set_map_floor(Mall.level_at(player.position.y))
			else:sonar()
		elif interaction==DoorField.Interaction.BLOCKED:hud.message("扉の動く範囲を空けてください")
	elif event.keycode == KEY_E and hud.mode == "play":
		chain_scan()
	elif event.keycode == KEY_Q and hud.mode == "play":
		pulse()
	elif event.keycode == KEY_1 and hud.mode == "play":
		equip(false)
	elif event.keycode == KEY_2 and hud.mode == "play":
		equip(true)

func _process(delta: float) -> void:
	var now := Time.get_ticks_usec()
	if is_instance_valid(hud) and hud.mode == "play" and last_frame_usec > 0:
		frame_samples.append((now-last_frame_usec)/1000.0)
		if frame_samples.size() > 180: frame_samples.remove_at(0)
		frame_report_left -= delta
		if frame_report_left <= 0:
			var sorted := frame_samples.duplicate(); sorted.sort()
			var total := 0.0
			for sample in frame_samples: total += sample
			hud.play_fps = 1000.0*frame_samples.size()/maxf(.001,total)
			hud.play_worst_ms = sorted[-1]
			frame_report_left = .5
	last_frame_usec = now

func _physics_process(delta: float) -> void:
	if hud.mode != "play":
		return
	_visit_points()
	_tick_items(delta)
	hud.nearby_cache = caches.nearest(player.camera)
	hud.interaction_hint=doors.hint(player.camera)
	if hud.interaction_hint.is_empty() and MallGuide.targeted(player.camera):hud.interaction_hint="F：館内案内図を見る"
	speech.update_nearby(crowd,player.camera,not Input.is_action_pressed("fire"))
	elapsed += delta
	shot_cooldown = maxf(0, shot_cooldown - delta)
	sonar_left = maxf(0, sonar_left - delta)
	chain_left = maxf(0, chain_left - delta)
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
		_tick_handheld(delta, Input.is_action_pressed("fire"),target)
	hud.using_gun = using_gun
	hud.scan_progress = handheld_scan.seconds / run.handheld_seconds()
	player.reader_screen.text = "スキャン中\n%03d%%" % int(hud.scan_progress * 100) if hud.scan_progress > 0 else "個体識別\nスキャナー"
	hud.ammo = ammo
	hud.player_position = player.position
	hud.location_name = Mall.zone_name(player.position)
	hud.elapsed = elapsed
	hud.sonar_cooldown = sonar_left
	hud.pulse_cooldown = pulse_left
	hud.chain_cooldown = chain_left
	hud.reload_progress = 1.0 - reload_left / run.reload_seconds() if reload_left > 0 else -1.0
	player.double_jump_enabled = run.upgrades.double_jump > 0
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
	return ScanAim.ray(get_world_3d().direct_space_state,from,to,[player.get_rid()],crowd)

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
	var origin := player.camera.global_position
	var end := origin - player.camera.global_transform.basis.z * run.scan_range()
	var excluded: Array[RID] = [player.get_rid()]
	for step in (3 if run.upgrades.pierce > 0 else 1):
		var hit := ScanAim.ray(get_world_3d().direct_space_state,origin,end,excluded,crowd)
		if hit.is_empty():
			break
		_spark(hit.position)
		if not hit.collider.has_meta("identity"):
			break
		excluded.append(hit.collider.get_rid())
		resolve(int(hit.collider.get_meta("identity")), IdentityRun.Source.GUN)

func chain_scan() -> void:
	if run.upgrades.chain == 0:
		hud.message("連鎖スキャンはTabから購入できます")
		return
	if chain_left > 0:
		hud.message("連鎖スキャン：あと%d秒" % ceili(chain_left))
		return
	var hit := ray_target()
	if hit.is_empty() or not hit.collider.has_meta("identity"):
		return
	chain_left = 20
	var current: int = hit.collider.get_meta("identity")
	var visited: Array[int] = []
	for step in 8:
		visited.append(current)
		var at := crowd.positions[current] + Vector3.UP
		resolve(current, IdentityRun.Source.SPECIAL)
		_ring(at, 0.7, Color("85cfff"))
		var next := -1
		var nearest := 25.0
		for id in crowd.live_positions_in_radius(crowd.positions[current], 5):
			if id in visited:
				continue
			var to := crowd.positions[id] + Vector3.UP
			var query := PhysicsRayQueryParameters3D.create(at, to, 1)
			if not get_world_3d().direct_space_state.intersect_ray(query).is_empty():
				continue
			var distance := at.distance_squared_to(to)
			if distance < nearest:
				nearest = distance
				next = id
		if next < 0:
			break
		current = next
	hud.message("連鎖スキャン：%d人を解析 ／ 再使用20秒" % visited.size())

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
		hud.message("偽物をスキャン完了　+10 AP")
		audio.play("fall", minf(1.5, 1 + combo * 0.025))
	elif outcome == IdentityRun.Result.LOCATED:
		_mark_original()
		hud.message("本物を発見！ 1キーで初期スキャナーに戻って確定しよう。")
	elif outcome == IdentityRun.Result.FOUND:
		audio.play("found")
		set_mode("win")
	return outcome

func equip(gun_selected: bool) -> bool:
	if gun_selected and run.upgrades.gun == 0:
		hud.message("Tabでスキャン銃を購入してください / %d AP" % run.price("gun"))
		return false
	using_gun = gun_selected
	handheld_scan.reset()
	_update_equipment()
	return true

func _update_equipment() -> void:
	player.using_gun = using_gun
	player.gun.visible = hud.mode == "play" and using_gun
	player.handheld.visible = hud.mode == "play" and not using_gun
	player.cart.visible = hud.mode == "play" and player.cart_boost > 1

func _tick_handheld(delta: float, held: bool,known_hit: Variant = null) -> void:
	if hud.mode != "play" or using_gun:
		handheld_scan.reset()
		return
	var hit: Dictionary = ray_target() if known_hit == null else known_hit
	var id := -1
	if not hit.is_empty() and hit.collider.has_meta("identity"):
		id = int(hit.collider.get_meta("identity"))
		if run.eliminated[id]:
			id = -1
	var finished := handheld_scan.tick(delta,id,held,run.handheld_seconds())
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
		hud.message("Tabで「瞬間ソナー」を解放してください。")
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
	hud.message("%d人の位置を記録 / 表示4秒 / 移動には追従しません" % snapshots.size())
	return snapshots

func pulse() -> void:
	if run.upgrades.pulse <= 0:
		hud.message("Tabで「範囲スキャン」を解放してください。")
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
	var label := Shapes.sign_text(beacon, Vector3(0, 0.55, 0), "本当の自分\n[1] 初期スキャナーで確定", 28, Color("b6ff94"))
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.no_depth_test = true
	audio.play("found", 1.3)

func _make_cat() -> void:
	cat = Node3D.new()
	effects.add_child(cat)
	cat.position = crowd.nav.get_point_position(crowd.nav.get_closest_point(player.position))
	var fur := Shapes.material(Color("c68c56"))
	var dark := Shapes.material(Color("34424a"))
	Shapes.box(cat, Vector3(0, 0.35, 0), Vector3(0.32, 0.35, 0.65), fur)
	Shapes.box(cat, Vector3(0, 0.55, -0.27), Vector3(0.34, 0.32, 0.3), fur)
	for x in [-0.12, 0.12]:
		Shapes.box(cat, Vector3(x, 0.77, -0.27), Vector3(0.1, 0.15, 0.12), fur)
		Shapes.box(cat, Vector3(x, 0.58, -0.425), Vector3(0.035, 0.055, 0.015), dark)
		for z in [-0.2, 0.2]:
			var paw := Shapes.box(cat, Vector3(x, 0.12, z), Vector3(0.08, 0.24, 0.08), fur)
			if z < 0: paw.name = "PawLeft" if x < 0 else "PawRight"
	var tail := Shapes.box(cat, Vector3(0, 0.51, 0.44), Vector3(0.08, 0.5, 0.08), fur)
	tail.rotation.x = 0.5
	cat_scan_time = 0
	cat_target = -1

func _tick_cat(delta: float) -> void:
	if not is_instance_valid(cat):
		hud.cat_status = ""
		return
	cat_clock += delta; cat_retarget -= delta
	var state := get_world_3d().direct_space_state
	if cat_target >= 0 and (run.eliminated[cat_target] or (cat_target == run.true_id and run.located)):
		cat_target = -1; cat_retarget = 0
	if cat_target < 0:
		hud.cat_status = "猫 / 次の相手を探索中"
		if cat_retarget > 0: return
		if cat_candidates.is_empty():
			for id in run.population:
				if run.eliminated[id] or (id == run.true_id and run.located) or cat_skipped.get(id,0.0) > cat_clock: continue
				cat_candidates.append(id)
			cat_candidates.sort_custom(func(a: int,b: int): return _cat_target_cost(a) < _cat_target_cost(b))
		if not cat_candidates.is_empty():
			var id: int = cat_candidates.pop_front()
			var route := CatSearch.route(crowd,cat.position,id,state)
			if route.is_empty(): cat_skipped[id] = cat_clock+5
			else:
				cat_target = id; cat_scan_time = 0; cat_planned_at = crowd.positions[id]
				cat.set_meta("path",route); cat_retarget = 1; cat_candidates.clear()
		if cat_target < 0:
			cat_retarget = .05 if not cat_candidates.is_empty() else 1.0
			return
	var destination := crowd.positions[cat_target]
	var seated: bool = crowd.roles[cat_target] in ["seated","reading"]
	# A cat passing a reachable shopper may work on that person rather than
	# walking past everyone toward an obstructed or distant commitment.
	if cat_retarget <= 0 and not CatSearch.can_scan(cat.position,destination,seated,state):
		for id in run.population:
			if run.eliminated[id] or (id == run.true_id and run.located) or crowd.roles[id] == "walking": continue
			if not CatSearch.can_scan(cat.position,crowd.positions[id],crowd.roles[id] in ["seated","reading"],state): continue
			cat_target = id; destination = crowd.positions[id]; seated = crowd.roles[id] in ["seated","reading"]
			cat_scan_time = 0; cat.set_meta("path",PackedVector3Array()); break
	if CatSearch.can_scan(cat.position,destination,seated,state):
		cat_scan_time += delta
		cat.rotation.z = sin(cat_scan_time*8)*.1
		cat.rotation.y = atan2(cat.position.x-destination.x,cat.position.z-destination.z)
		cat.get_node("PawRight").position.z = -.2-absf(sin(cat_scan_time*8))*.25
		var seconds: float = [20.0,12.0,6.0][run.upgrades.cat_speed]
		hud.cat_status = "猫 / 相手 #%04d を解析中・あと %.1f秒" % [cat_target+1,maxf(0,seconds-cat_scan_time)]
		if cat_scan_time >= seconds:
			resolve(cat_target,IdentityRun.Source.SPECIAL)
			cat_target = -1; cat_retarget = 0; cat_scan_time = 0
		return
	cat.rotation.z = 0; cat.get_node("PawRight").position.z = -.2
	hud.cat_status = "猫 / 相手 #%04d へ移動中・%.1fm" % [cat_target+1,cat.position.distance_to(destination)]
	var path: PackedVector3Array = cat.get_meta("path",PackedVector3Array())
	if cat_retarget <= 0 and (path.is_empty() or destination.distance_to(cat_planned_at) > .75):
		path = CatSearch.route(crowd,cat.position,cat_target,state)
		cat_planned_at = destination; cat_retarget = 1
		if path.is_empty():
			cat_skipped[cat_target] = cat_clock+5; cat_target = -1; cat_scan_time = 0
			return
	# Consume all reached waypoints so repathing cannot pull the cat back each second.
	var remaining := delta*4
	while not path.is_empty() and remaining > 0:
		var distance := cat.position.distance_to(path[0])
		if distance < .05:
			cat.position = path[0]; path.remove_at(0); continue
		var direction := path[0]-cat.position
		var step := minf(remaining,distance)
		cat.position += direction.normalized()*step; remaining -= step
		cat.rotation.y = atan2(-direction.x,-direction.z)
		if step >= distance: path.remove_at(0)
	cat.set_meta("path",path)

func _cat_target_cost(id: int) -> float:
	var at: Vector3 = crowd.positions[id]
	var floor_penalty := 200.0 if absf(at.y-cat.position.y) > .6 else 0.0
	return cat.position.distance_squared_to(at)+floor_penalty+(8.0 if crowd.roles[id] == "walking" else 0.0)

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
	settings.ambient_light_color = Color("dde4ec")
	settings.ambient_light_energy = 0.38
	settings.tonemap_exposure = 1.0
	settings.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	environment.environment = settings
	add_child(environment)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-58, -24, 0)
	sun.light_color = Color("fff0d1")
	sun.light_energy = 0.8
	sun.shadow_enabled = true
	sun.shadow_bias = .1
	sun.shadow_normal_bias = 1.5
	sun.directional_shadow_max_distance = 85
	add_child(sun)
	for x in [-22.0, 0.0, 22.0]:
		var light := OmniLight3D.new()
		light.position = Vector3(x, 5, 0)
		light.omni_range = 27
		light.light_color = Color("fff1df")
		light.light_energy = 0.45
		add_child(light)

func _capture() -> void:
	await get_tree().create_timer(2).timeout
	get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-title.png")
	start_run(120, 912)
	await get_tree().create_timer(2).timeout
	get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-play.png")
	player.position = MallCurve.world(Vector3(47, 0.1, -44))
	player.velocity = Vector3.ZERO
	player.camera.look_at(MallCurve.world(Vector3(68, 1.2, -47)))
	await get_tree().create_timer(0.5).timeout
	get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-food.png")
	player.position = MallCurve.world(Vector3(17,.1,17))
	player.camera.look_at(MallCurve.world(Vector3(26,1.5,36)))
	await get_tree().create_timer(.5).timeout
	get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-market.png")
	player.position = MallCurve.world(Vector3(-75,.1,-11))
	player.camera.look_at(MallCurve.world(Vector3(-79,1.4,-20)))
	await get_tree().create_timer(.5).timeout
	get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-bookshop.png")
	player.position = MallCurve.world(Vector3(-79, 0.1, 33))
	player.velocity = Vector3.ZERO
	player.camera.look_at(MallCurve.world(Vector3(-86, 1.5, 45)))
	await get_tree().create_timer(0.5).timeout
	get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-restroom.png")
	# A dedicated development capture exercises a partial original-reader lock.
	crowd.positions[0] = MallCurve.world(Vector3(11, 0, 2))
	crowd.bodies[0].position = MallCurve.world(Vector3(11, 0.95, 2))
	crowd.waits[0] = 30
	crowd.headings[0] = PI
	player.position = MallCurve.world(Vector3(11, 0.1, 5.4))
	player.velocity = Vector3.ZERO
	player.camera.look_at(MallCurve.world(Vector3(11, 1.55, 2)))
	await get_tree().physics_frame
	Input.action_press("fire")
	await get_tree().create_timer(0.9).timeout
	get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-reader.png")
	Input.action_release("fire")
	player.position = MallCurve.world(Vector3(11, .1, 3.4))
	player.camera.look_at(MallCurve.world(Vector3(11, 1.58, 2)))
	await get_tree().create_timer(.5).timeout
	get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-portrait.png")
	set_mode("skills")
	await get_tree().create_timer(0.5).timeout
	get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-skills.png")
	for screen in ["pause", "map", "win"]:
		set_mode(screen)
		await get_tree().create_timer(0.2).timeout
		get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-%s.png" % screen)
	get_tree().quit()

func _visit_points(announce: bool = true) -> void:
	for point in MallLayout.travel_points():
		var key: String = point.legacy_key
		if not run.visited.has(key) and player.position.distance_to(point.position) <= 2.0:
			run.visited[key] = true
			if announce:
				hud.message("案内ポイントを記録：%s ／ Mで確認" % key)

func fast_travel(key: String) -> bool:
	var point := MallLayout.travel_point(key)
	if hud.mode != "map" or point.is_empty() or not run.can_travel(point.legacy_key):
		return false
	player.position = point.position
	player.velocity = Vector3.ZERO
	player.air_jump_used = false
	handheld_scan.reset()
	set_mode("play")
	hud.message("%sへ移動しました" % point.legacy_key)
	return true

func _capture_overview() -> void:
	start_run(120,912)
	await get_tree().create_timer(1.0).timeout
	get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-play.png")
	player.position = MallCurve.world(Vector3(17,.1,17))
	player.camera.look_at(MallCurve.world(Vector3(26,1.5,36)))
	await get_tree().create_timer(.5).timeout
	get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-market.png")
	get_tree().quit()

func open_cache() -> bool:
	if hud.mode != "play": return false
	var index := caches.nearest(player.camera)
	if index < 0: return false
	var key := loot.open(index)
	if key.is_empty(): return false
	caches.opened(index)
	audio.play("hit",1.3)
	hud.message("%sを入手 / Xで使用、Iでバッグ" % RunLoot.ITEMS[key].name)
	return true

func _select_item(key: String) -> void:
	if RunLoot.ITEMS.has(key) and loot.inventory[key] > 0:
		loot.selected = key
		set_mode("play")

func use_item(key: String = "") -> bool:
	if hud.mode != "play" or run.won: return false
	if key.is_empty(): key = loot.selected
	if not loot.inventory.has(key) or loot.inventory[key] <= 0:
		hud.message("アイテムがありません / 宝箱を探そう")
		return false
	var from := player.camera.global_position
	var query := PhysicsRayQueryParameters3D.create(from,from-player.camera.global_basis.z*40,3,[player.get_rid()])
	query.collide_with_areas = true
	var hit := get_world_3d().direct_space_state.intersect_ray(query)
	if key == "chain" and (hit.is_empty() or not hit.collider.has_meta("identity")):
		hud.message("超連鎖弾：40m以内の人を狙ってください")
		return false
	if not loot.consume(key): return false
	match key:
		"magnet":
			var goal := crowd.nav.get_point_position(crowd.nav.get_closest_point(player.position-player.global_basis.z*4))
			crowd.attract(goal,18,10); _ring(goal,18,Color("b8d6f0"))
		"clock": loot.clock_left = 12; crowd.frozen = true
		"cart": loot.cart_left = 30; player.cart_boost = 1.7
		"sonar": _global_snapshot()
		"chain": _item_chain(int(hit.collider.get_meta("identity")))
		"hole":
			var goal := crowd.nav.get_point_position(crowd.nav.get_closest_point(player.position-player.global_basis.z*6))
			_scan_area(goal,18,200); _ring(goal,18,Color("c8a8ef"))
		"laser":
			var goal: Vector3 = hit.position if not hit.is_empty() else player.position-player.global_basis.z*8
			goal = crowd.nav.get_point_position(crowd.nav.get_closest_point(goal))
			_scan_area(goal,14,200)
			var laser := Shapes.cylinder(effects,goal+Vector3.UP*6,.25,12,Shapes.material(Color("c9f5ff"),1))
			var tween := laser.create_tween(); tween.tween_property(laser,"scale",Vector3.ZERO,.7); tween.tween_callback(laser.queue_free)
		"disco": loot.disco_left = 12; loot.disco_beat = 0
	audio.play("sonar",.85)
	hud.message("%sを使用 / 本物の確定は初期スキャナーで" % RunLoot.ITEMS[key].name)
	return true

func _scan_area(center: Vector3,radius: float,limit: int) -> int:
	var count := 0
	for id in crowd.live_positions_in_radius(center,radius):
		var query := PhysicsRayQueryParameters3D.create(center+Vector3.UP,crowd.positions[id]+Vector3.UP,1)
		if not get_world_3d().direct_space_state.intersect_ray(query).is_empty(): continue
		if run.located and id == run.true_id: continue
		resolve(id,IdentityRun.Source.SPECIAL); count += 1
		if count >= limit: break
	return count

func _item_chain(start: int) -> void:
	var visited: Array[int] = []
	var current := start
	for step in 200:
		visited.append(current)
		var at := crowd.positions[current]
		resolve(current,IdentityRun.Source.SPECIAL)
		var next := -1
		var nearest := 64.1
		for id in crowd.live_positions_in_radius(at,8):
			if id in visited: continue
			var query := PhysicsRayQueryParameters3D.create(at+Vector3.UP,crowd.positions[id]+Vector3.UP,1)
			if not get_world_3d().direct_space_state.intersect_ray(query).is_empty(): continue
			var distance := at.distance_squared_to(crowd.positions[id])
			if distance < nearest: nearest = distance; next = id
		if next < 0: break
		current = next

func _global_snapshot() -> Array[Vector3]:
	var snapshots: Array[Vector3] = []
	var mat := Shapes.material(Color("e4bc87"),.7); mat.no_depth_test = true; mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	for id in run.population:
		if run.eliminated[id]: continue
		var at := crowd.positions[id]+Vector3.UP*1.1; snapshots.append(at)
		var marker := Shapes.sphere(effects,at,.14,mat)
		var tween := marker.create_tween(); tween.tween_interval(8); tween.tween_callback(marker.queue_free)
	return snapshots

func _tick_items(delta: float) -> void:
	# Test the beat before decrementing, so the last of six disco pulses is not lost.
	if loot.disco_left > 0 and loot.disco_beat <= 0:
		_scan_area(player.position,16,20)
		_ring(player.position,16,Color.from_hsv(fmod(elapsed*.13,1),.4,.9))
		loot.disco_beat = 2
	loot.tick(delta)
	crowd.frozen = loot.clock_left > 0
	player.cart_boost = 1.7 if loot.cart_left > 0 else 1.0

func _capture_mall() -> void:
	start_run(120,912)
	player.set_physics_process(false)
	for shot in [
		["atrium",Vector3(-25,.1,0),Vector3(33,7,0)],
		["third-floor",Vector3(-20,10.975,-6.5),Vector3(25,6,6.5)],
		["upper-bookshop",Vector3(-75,5.625,-10),Vector3(-79,6.9,-20)],
		["speech",Vector3(-72,5.625,-16.3),Vector3(-72,7.1,-19.15)],
		["reading",Vector3(-80,.1,-27),Vector3(-82,1.3,-31)],
		["curve",Vector3(10,5.625,-6.5),Vector3(65,6.8,-6.5)]
	]:
		player.position = MallCurve.world(shot[1]); player.camera.look_at(MallCurve.world(shot[2]))
		await get_tree().create_timer(.6).timeout
		hud.notice_time = 0
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-%s.png" % shot[0])
	loot.inventory.hole = 1; loot.inventory.sonar = 2
	set_mode("inventory")
	await get_tree().create_timer(.3).timeout
	get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-inventory.png")
	set_mode("map")
	await get_tree().create_timer(.3).timeout
	get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-upper-map.png")
	get_tree().quit()

func _capture_bag() -> void:
	start_run(120,912)
	loot.inventory.hole = 1; loot.inventory.sonar = 2
	set_mode("inventory")
	await get_tree().create_timer(.3).timeout
	get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-inventory.png")
	get_tree().quit()

func _capture_annex() -> void:
	start_run(180,912)
	player.set_physics_process(false)
	for shot in [
		["basement",Vector3(-82,-5.25,-6.5),Vector3(-45,-3.9,-17)],
		["garden",Vector3(-87,16.5,-12),Vector3(-64,17.5,-17)],
		["parking",Vector3(-125,.1,-5.5),Vector3(-151,1,-20)],
		["west-core",Vector3(-94,.1,-5.2),Vector3(-104,4,-15)]
	]:
		player.position = MallCurve.world(shot[1]); player.camera.look_at(MallCurve.world(shot[2]))
		await get_tree().create_timer(.6).timeout
		hud.notice_time = 0
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-%s.png" % shot[0])
	set_mode("map")
	await get_tree().create_timer(.3).timeout
	get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-parking-map.png")
	get_tree().quit()

func _select_graphics(choice: String) -> void:
	graphics_choice = choice
	GraphicsOptions.apply(self,choice)
	hud.show_mode("pause")

func _capture_b_wing() -> void:
	start_run(300,912)
	player.set_physics_process(false)
	for shot in [
		["skybridge",Vector3(-115,5.625,-5.5),Vector3(-180,6.8,-5.5)],
		["b-concourse",Vector3(-200,.1,0),Vector3(-260,8,0)],
		["b-court",Vector3(-234,.1,1),Vector3(-234,7.5,21)],
		["b-shop",Vector3(-302,.1,-10),Vector3(-302,1.5,-22)],
		["b-cinema",Vector3(-391,10.975,1),Vector3(-415.6,15.1,0)],
		["b-lounge",Vector3(-376,5.625,0),Vector3(-402,6.8,0)]
	]:
		player.position = shot[1]; player.camera.look_at(shot[2])
		await get_tree().create_timer(.5).timeout
		hud.notice_time = 0; hud.queue_redraw()
		await get_tree().process_frame; await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-%s.png" % shot[0])
	set_mode("map"); hud.set_map_floor(2)
	await get_tree().create_timer(.2).timeout
	get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-b-map.png")
	set_mode("pause")
	await get_tree().create_timer(.2).timeout
	get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-graphics.png")
	get_tree().quit()

func _capture_c_wing() -> void:
	start_run(300,912)
	player.set_physics_process(false)
	crowd.set_physics_process(false)
	for shot in [
		["c-link",Vector3(-370,.1,-30),Vector3(-370,2,-85)],
		["c-plaza",Vector3(-370,.1,-89),Vector3(-360,3,-140)],
		["c-terrace",Vector3(-338,.1,-97),Vector3(-338,1.6,-112)],
		["c-shop",Vector3(-400,.1,-147),Vector3(-400,1.8,-165)],
		["c-court",Vector3(-311,.1,-100),Vector3(-393,3,-139)]
	]:
		player.position = shot[1]; player.camera.look_at(shot[2]); crowd._render()
		await get_tree().create_timer(.5).timeout
		hud.notice_time = 0; hud.queue_redraw()
		await get_tree().process_frame; await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-%s.png" % shot[0])
		print("C_CAPTURE: ",shot[0]," draws=",Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))
	set_mode("map"); hud.set_map_floor(0)
	await get_tree().create_timer(.2).timeout
	get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-c-map.png")
	get_tree().quit()

func _capture_growth() -> void:
	start_run(300,912); set_physics_process(false); crowd.set_physics_process(false); player.set_physics_process(false)
	run.ap = 1200; hud.skill_branch = 0; hud.skill_selected = "focus"; set_mode("skills")
	await get_tree().process_frame; await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-skill-gun.png")
	buy_skill("gun"); buy_skill("cat"); buy_skill("cat_speed")
	hud.skill_branch = 1; hud.skill_selected = "cat_speed"; hud.show_mode("skills")
	await get_tree().process_frame; await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-skill-cat.png")
	hud.skill_branch = 2; hud.skill_selected = "sonar"; hud.show_mode("skills")
	await get_tree().process_frame; await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-skill-explore.png")
	set_mode("play")
	var state := get_world_3d().direct_space_state
	for id in run.population:
		if id == run.true_id or crowd.roles[id] == "walking": continue
		var approach := crowd.nav.get_point_position(crowd.nav.get_closest_point(crowd.positions[id]))
		if approach.distance_to(crowd.positions[id]) <= 1.12 or not CatSearch.can_scan(approach,crowd.positions[id],crowd.roles[id] == "seated",state): continue
		cat.position = approach; cat_target = id; _tick_cat(4)
		for point in mall.spawn_points:
			if point.distance_to(crowd.positions[id]) < 2.7 or point.distance_to(crowd.positions[id]) > 4 or absf(point.y-crowd.positions[id].y) > .1: continue
			if not state.intersect_ray(PhysicsRayQueryParameters3D.create(point+Vector3.UP*1.68,crowd.positions[id]+Vector3.UP,1)).is_empty(): continue
			player.position = point+Vector3.UP*.1; player.camera.look_at(crowd.positions[id]+Vector3.UP*.7); break
		break
	crowd._render(); hud.notice_time = 0; hud.queue_redraw()
	await get_tree().process_frame; await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("/tmp/find-yourself-cat-scan.png")
	get_tree().quit()

func _capture_interiors() -> void:
	start_run(300,912); set_physics_process(false); crowd.set_physics_process(false); player.set_physics_process(false)
	GraphicsOptions.apply(self,"balanced",false); crowd.clock = .4
	for shot in [["concourse",Vector3(-70,.1,0),Vector3(-10,7,0)],["fashion",Vector3(-57,.1,-4),Vector3(-57,2,-19)],["materials",Vector3(-55,.1,-7),Vector3(-57,.08,-11)],["upper",Vector3(-25,10.975,5.2),Vector3(35,5.5,-6)],["inside",Vector3(-57,.1,-10),Vector3(-57,2,-22)]]:
		player.position = MallCurve.world(shot[1]); player.camera.look_at(MallCurve.world(shot[2])); crowd._render()
		hud.player_position = player.position; hud.location_name = Mall.zone_name(player.position); hud.notice_time = 0; hud.queue_redraw()
		await get_tree().create_timer(.3).timeout; await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("/tmp/fy12-after-%s.png" % shot[0])
		print("INTERIOR_CAPTURE native ",shot[0]," draws=",Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))
	get_tree().quit()

func _capture_stores() -> void:
	start_run(300,912); set_physics_process(false); crowd.set_physics_process(false); player.set_physics_process(false)
	GraphicsOptions.apply(self,"balanced",false); crowd.clock = .4
	for shot in [["fashion",Vector3(-57,.1,-9.5),Vector3(-57,1.6,-19)],["daily",Vector3(-21,.1,-10),Vector3(-21,1.5,-22)],["wares",Vector3(-27,.1,-19.4),Vector3(-27,1.8,-22.1)],["digital",Vector3(-3,.1,-11),Vector3(-7.5,1.25,-13.5)],["cafe",Vector3(15,.1,-11),Vector3(10.5,1,-13.5)],["b-clothes",Vector3(-346,.1,-10),Vector3(-346,1.6,-22)],["c-shoes",Vector3(-402,.1,-84),Vector3(-402,1.5,-77)]]:
		player.position = MallCurve.world(shot[1]); player.camera.look_at(MallCurve.world(shot[2])); crowd._render()
		hud.player_position = player.position; hud.location_name = Mall.zone_name(player.position); hud.notice_time = 0; hud.queue_redraw()
		await get_tree().create_timer(.3).timeout; await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("/tmp/fy13-after-%s.png" % shot[0])
		print("STOCK_CAPTURE native ",shot[0])
	hud.skill_branch = 0; hud.skill_selected = "handheld_speed"; set_mode("skills")
	await get_tree().create_timer(.2).timeout; await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("/tmp/fy13-reader-skill.png")
	get_tree().quit()

func _capture_art() -> void:
	start_run(300,912); set_physics_process(false); crowd.set_physics_process(false); player.set_physics_process(false)
	GraphicsOptions.apply(self,"balanced",false)
	# Development-only comparison subject; normal runs keep their original positions.
	crowd.positions[0] = MallCurve.world(Vector3(-57,0,-13)); crowd.headings[0] = PI; crowd.roles[0] = "walking"; crowd.waits[0] = 30
	for shot in [["close",Vector3(-57,.1,-12),Vector3(-57,1.69,-13)],["person",Vector3(-57,.1,-10.7),Vector3(-57,1.55,-13)],["atrium",Vector3(-70,.1,0),Vector3(-10,7,0)],["fashion",Vector3(-57,.1,-4),Vector3(-57,2,-19)],["upper",Vector3(-25,10.975,5.2),Vector3(35,5.5,-6)]]:
		player.position = MallCurve.world(shot[1]); player.camera.look_at(MallCurve.world(shot[2])); crowd._render()
		hud.player_position = player.position; hud.location_name = Mall.zone_name(player.position); hud.notice_time = 0; hud.queue_redraw()
		await get_tree().create_timer(.3).timeout; await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("/tmp/fy10-after-%s.png" % shot[0])
		print("ART_CAPTURE native ",shot[0]," draws=",Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))
	get_tree().quit()

func _capture_people() -> void:
	start_run(300,912); set_physics_process(false); crowd.set_physics_process(false); player.set_physics_process(false)
	GraphicsOptions.apply(self,"balanced",false)
	crowd.positions[0] = MallCurve.world(Vector3(-57,0,-13)); crowd.headings[0] = PI; crowd.roles[0] = "walking"; crowd.waits[0] = 30
	for shot in [["face",Vector3(-57,.1,-12),Vector3(-57,1.69,-13),.4],["closed",Vector3(-57,.1,-12),Vector3(-57,1.69,-13),.09],["body",Vector3(-57,.1,-10.7),Vector3(-57,1.4,-13),.4]]:
		player.position = MallCurve.world(shot[1]); player.camera.look_at(MallCurve.world(shot[2])); crowd.clock = shot[3]; crowd._render()
		hud.player_position = player.position; hud.location_name = Mall.zone_name(player.position); hud.notice_time = 0; hud.queue_redraw()
		await get_tree().create_timer(.3).timeout; await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("/tmp/fy11-after-%s.png" % shot[0])
		print("PEOPLE_CAPTURE native ",shot[0]," draws=",Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))
	if "--people-movie" in OS.get_cmdline_user_args():
		DirAccess.make_dir_recursive_absolute("/tmp/fy11-frames")
		for frame in 144:
			var walking := frame >= 48 and frame < 96
			var conversation := frame >= 96
			crowd.roles[0] = "conversation" if conversation else "walking"; crowd.waits[0] = 0 if walking else 30
			crowd.paths[0] = PackedVector3Array([crowd.positions[0]+Vector3.BACK*5]) if walking else PackedVector3Array()
			crowd.clock = (3.2 if frame < 48 else 7.0 if walking else 4.0)+float(frame%48)/24.0
			player.position = MallCurve.world(Vector3(-57,.1,-10.7 if walking else -12))
			player.camera.look_at(crowd.positions[0]+Vector3.UP*(1.4 if walking else 1.69)); crowd._render()
			hud.player_position = player.position; hud.queue_redraw()
			await get_tree().process_frame; await RenderingServer.frame_post_draw
			get_viewport().get_texture().get_image().save_png("/tmp/fy11-frames/%04d.png" % frame)
	get_tree().quit()

func _capture_realism()->void:
	await RealismCapture.capture(self)
	get_tree().quit()
