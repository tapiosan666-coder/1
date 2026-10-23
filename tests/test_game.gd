extends SceneTree

var checks := 0
var failures := 0

func expect(condition: bool, description: String) -> void:
	checks += 1
	if not condition:
		failures += 1
		push_error(description)

func _initialize() -> void:
	call_deferred("run_tests")

func run_tests() -> void:
	_test_state()
	_test_lock()
	var game = load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	game.start_run(120, 904)
	game.crowd.set_physics_process(false)
	await physics_frame
	await physics_frame
	expect(not game.using_gun and game.run.upgrades.gun == 0, "Start with handheld, no gun owned")
	expect(not game.equip(true), "Cannot equip locked gun")
	expect(game.player.handheld.visible and not game.player.gun.visible, "Correct initial tool model visible")
	expect(game.crowd.positions.size() == 120, "120 scene identities created")
	var reachable := true
	for point in game.crowd.nav_ids:
		if game.crowd.nav.get_point_path(0, point).is_empty():
			reachable = false
	expect(reachable, "NPC grid is connected")
	var start_z: float = game.player.position.z
	Input.action_press("forward")
	await create_timer(0.25).timeout
	Input.action_release("forward")
	expect(game.player.position.z < start_z - 0.5, "WASD moves character body")
	game.player.position = Vector3(37.1, 0.1, 7)
	Input.action_press("right")
	await create_timer(0.3).timeout
	Input.action_release("right")
	expect(game.player.position.x < 37.6, "Perimeter blocks movement")
	for part in game.crowd.parts:
		expect(part.instances.mesh != null, "Every instanced body part has geometry")
	var fake: int = (game.run.true_id + 1) % 120
	for body in game.crowd.bodies:
		body.collision_layer = 0
	game.crowd.positions[fake] = Vector3(11, 0, 7)
	game.crowd.bodies[fake].position = Vector3(11, 0.95, 7)
	game.crowd.bodies[fake].collision_layer = 2
	game.player.position = Vector3(11, 0.1, 10)
	game.player.velocity = Vector3.ZERO
	game.player.camera.look_at(Vector3(11, 1.2, 7))
	await physics_frame
	await physics_frame
	var hit: Dictionary = game.ray_target()
	expect(not hit.is_empty() and hit.collider.get_meta("identity", -1) == fake, "Reader physics ray sees the intended identity")
	var ammo_before: int = game.ammo
	game.fire()
	expect(game.ammo == ammo_before and game.run.cleared == 0, "Handheld cannot shoot or instantly clear")
	Input.action_press("fire")
	await create_timer(1.8).timeout
	expect(not game.run.eliminated[fake], "1.8 seconds does not complete reader scan")
	await create_timer(0.35).timeout
	Input.action_release("fire")
	expect(game.run.eliminated[fake] == 1 and game.run.ap == 10, "Holding actual input for 2 seconds clears one fake and awards AP")
	expect(game.ammo == 30, "Reader uses no ammunition")
	expect(game.run.cleared == 1, "Reader clears only one person")
	expect(game.crowd.death_times[fake] >= 0 and game.crowd.bodies[fake].collision_layer == 0, "Fake falls and stops obstructing scans")
	game.run.ap = 400
	game.buy_skill("gun")
	expect(game.run.upgrades.gun == 1 and game.run.ap == 0, "Gun unlock costs 400 AP")
	game.set_mode("play")
	expect(game.equip(true), "Owned gun can be equipped")
	expect(game.player.gun.visible and not game.player.handheld.visible, "Equipment switch updates model")
	var other: int = (fake + 1) % 120
	game.crowd.positions[other] = Vector3(11, 0, 7)
	game.crowd.bodies[other].position = Vector3(11, 0.95, 7)
	game.crowd.bodies[other].collision_layer = 2
	await physics_frame
	await physics_frame
	for i in 5:
		game.shot_cooldown = 0
		game.fire()
	expect(game.run.eliminated[other] == 1 and game.ammo == 25, "Unlocked gun clears fake with five actual shots")
	game.reload_gun()
	await create_timer(1.15).timeout
	expect(game.ammo == 30 and game.reload_left == 0, "Gun reload remains one second")
	# A third identity behind the mall perimeter is neither readable nor shootable.
	var third: int = (other + 1) % 120
	game.player.position = Vector3(35, 0.1, 7)
	game.crowd.positions[third] = Vector3(40, 0, 7)
	game.crowd.bodies[third].position = Vector3(40, 0.95, 7)
	game.crowd.bodies[third].collision_layer = 2
	game.player.camera.look_at(Vector3(40, 1.2, 7))
	game.equip(false)
	await physics_frame
	await physics_frame
	hit = game.ray_target()
	expect(not hit.is_empty() and not hit.collider.has_meta("identity"), "Wall blocks handheld ray")
	game._tick_handheld(2.1, true)
	expect(not game.run.eliminated[third], "Cannot complete reader scan through wall")
	game.equip(true)
	hit = game.ray_target()
	expect(not hit.is_empty() and not hit.collider.has_meta("identity"), "Wall also blocks pistol")
	game.run.upgrades.sonar = 1
	var snapshots: Array[Vector3] = game.sonar()
	var recorded := Vector3(40, 1.1, 7)
	expect(snapshots.has(recorded), "Sonar sees through wall")
	game.crowd.positions[third] += Vector3(0, 0, 3)
	expect(snapshots.has(recorded), "Sonar retains snapshot position")
	expect(game.sonar().is_empty(), "Sonar cooldown enforced")
	game.resolve(game.run.true_id, IdentityRun.Source.SPECIAL)
	expect(game.run.located and not game.run.won, "Special scan marks true identity without winning")
	expect(is_instance_valid(game.beacon), "Original gets a beacon")
	for i in 8:
		game.resolve(game.run.true_id, IdentityRun.Source.GUN)
	expect(not game.run.won, "Even repeated gun scans cannot win")
	game.run.ap = 1000
	game.buy_skill("cat")
	game.set_mode("play")
	game.run.located = false
	game.cat_target = game.run.true_id
	game.cat.position = game.crowd.positions[game.run.true_id]
	game.cat_scan_time = 19.99
	game._tick_cat(0.02)
	expect(game.run.located and not game.run.won, "Cat only marks original")
	game.run.located = false
	game.cat.position = Vector3(0, 0, 12)
	game.cat_target = game.run.true_id
	game.cat_scan_time = 19.99
	game.cat_retarget = 1
	game.cat.set_meta("path", PackedVector3Array())
	game.crowd.positions[game.run.true_id] = Vector3(35, 0, 25)
	game._tick_cat(0.02)
	expect(not game.run.located, "Cat cannot scan distant target with empty route")
	game.handheld_scan.tick(1, fake, true)
	game.set_mode("pause")
	var before: float = game.elapsed
	await create_timer(0.1).timeout
	expect(game.elapsed == before and game.handheld_scan.seconds == 0, "Pause freezes time and cancels partial reader lock")
	var escape := InputEventKey.new()
	escape.keycode = KEY_ESCAPE
	escape.pressed = true
	game._input(escape)
	expect(not paused and game.hud.mode == "play", "Escape resumes game")
	# Approach the real person and finish with the original tool, via actual input.
	game.crowd.bodies[third].collision_layer = 0
	var original: int = game.run.true_id
	game.crowd.positions[original] = Vector3(11, 0, 7)
	game.crowd.bodies[original].position = Vector3(11, 0.95, 7)
	game.crowd.bodies[original].collision_layer = 2
	game.player.position = Vector3(11, 0.1, 10)
	game.player.velocity = Vector3.ZERO
	game.player.camera.look_at(Vector3(11, 1.2, 7))
	game.equip(false)
	game.cat.set_process(false)
	await physics_frame
	await physics_frame
	Input.action_press("fire")
	await create_timer(1.8).timeout
	expect(not game.run.won, "Prior gun hits do not shorten final reader verification")
	await create_timer(0.35).timeout
	Input.action_release("fire")
	expect(game.run.won and game.hud.mode == "win", "Original reader alone wins after two continuous seconds")
	expect(game.run.cleared == 2, "Victory preserves all remaining identities")
	game.start_run(120, 904)
	expect(not game.using_gun and game.run.upgrades.gun == 0 and game.run.ap == 0, "Restart resets equipment unlock and AP")
	expect(not game.run.located and not game.run.won and game.cat == null, "Restart resets original marker and companion")
	game.queue_free()
	await process_frame
	await create_timer(0.2).timeout
	print("RESULT: %d checks, %d failures" % [checks, failures])
	quit(0 if failures == 0 else 1)

func _test_lock() -> void:
	var lock := HandheldScan.new()
	expect(lock.tick(1.99, 7, true) == -1, "Reader requires a full two seconds")
	expect(lock.tick(0.01, 7, true) == 7, "Reader completes at two seconds")
	lock.tick(1.9, 7, true)
	expect(lock.tick(0.2, 8, true) == -1 and lock.target_id == 8, "Changing identity discards old progress")
	lock.tick(0.0, -1, true)
	expect(lock.seconds == 0 and lock.target_id == -1, "Obstruction or range loss resets lock")
	lock.tick(1.9, 7, true)
	lock.tick(0.1, 7, false)
	expect(lock.seconds == 0, "Release cancels progress")

func _test_state() -> void:
	var full := IdentityRun.new(5000, 31337)
	expect(full.population == 5000 and full.true_id >= 0 and full.true_id < 5000, "Exactly one uniformly selected original")
	var fixed := full.true_id
	expect(full.scan(-1) == IdentityRun.Result.INVALID and full.scan(5000) == IdentityRun.Result.INVALID, "Invalid IDs rejected")
	for id in 5000:
		if id == fixed:
			continue
		full.scan(id, IdentityRun.Source.SPECIAL)
		full.scan(id, IdentityRun.Source.SPECIAL)
	expect(full.true_id == fixed and full.cleared == 4999 and full.ap == 49990, "Original is fixed; no duplicate AP")
	expect(full.scan(fixed, IdentityRun.Source.SPECIAL) == IdentityRun.Result.LOCATED and not full.won, "Special scan never wins")
	full.upgrades.gun = 1
	for i in 4:
		expect(full.scan(fixed, IdentityRun.Source.GUN) == IdentityRun.Result.HIT, "Gun requires five hits")
	expect(full.scan(fixed, IdentityRun.Source.GUN) == IdentityRun.Result.LOCATED and not full.won, "Gun locates, never verifies original")
	expect(full.scan(fixed) == IdentityRun.Result.FOUND, "Handheld completion verifies original")
	expect(full.eliminated[fixed] == 0 and full.cleared == 4999, "Original never falls")
	var first := IdentityRun.new(1, 19)
	first.scan(0)
	expect(first.won and first.cleared == 0, "Can find original first")
	var skills := IdentityRun.new(120, 42)
	expect(not skills.purchase("gun") and not skills.purchase("bogus"), "No free or unknown unlocks")
	skills.ap = 10000
	expect(not skills.purchase("focus"), "Gun upgrades require gun")
	expect(skills.purchase("gun"), "Gun can be unlocked")
	expect(not skills.purchase("gun"), "Gun can only be purchased once")
	expect(not skills.purchase("cat_speed"), "Cat speed requires cat")
	for i in 4:
		expect(skills.purchase("focus"), "Focus upgrade available after gun")
	expect(skills.required_hits() == 1 and not skills.purchase("focus"), "Focus capped")
	expect(skills.ap == 9000, "Gun and four focus levels cost 1000 AP total")
	var total := 0
	for building in IdentityRun.DISTRIBUTION:
		for count in IdentityRun.DISTRIBUTION[building]:
			total += count
	expect(total == 5000, "Design population remains 5000")
	var buckets := PackedInt32Array()
	buckets.resize(10)
	for seed_value in 10000:
		var sample := IdentityRun.new(5000, seed_value)
		buckets[sample.true_id / 500] += 1
	for count in buckets:
		expect(count > 850 and count < 1150, "No gross uniform-selection bias")
