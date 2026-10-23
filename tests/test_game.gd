extends SceneTree
## Run with: godot --headless --path . --script res://tests/test_game.gd

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
	var game = load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	game.start_run(120, 904)
	game.crowd.set_physics_process(false)
	await physics_frame
	await physics_frame
	expect(game.crowd.positions.size() == 120, "120 scene identities created")
	var reachable := true
	for point in game.crowd.nav_ids:
		if game.crowd.nav.get_point_path(0, point).is_empty():
			reachable = false
	expect(reachable, "All NPC navigation points are reachable from the same connected grid")
	var start_z: float = game.player.position.z
	Input.action_press("forward")
	await create_timer(0.25).timeout
	Input.action_release("forward")
	expect(game.player.position.z < start_z - 0.5, "WASD moves the actual character body")
	game.player.position = Vector3(37.1, 0.1, 7)
	Input.action_press("right")
	await create_timer(0.3).timeout
	Input.action_release("right")
	expect(game.player.position.x < 37.6, "Player cannot walk through mall perimeter")
	for part in game.crowd.parts:
		expect(part.instances.mesh != null, "Crowd part has a renderable mesh")
	# Raycast the actual physics world and fire the real weapon, not a fake hit.
	var fake: int = (game.run.true_id + 1) % game.run.population
	for body in game.crowd.bodies:
		body.collision_layer = 0
	game.crowd.positions[fake] = Vector3(11, 0, 7)
	game.crowd.bodies[fake].position = Vector3(11, 0.95, 7)
	game.crowd.bodies[fake].collision_layer = 2
	game.player.position = Vector3(11, 0.1, 10)
	game.player.camera.look_at(Vector3(11, 1.2, 7))
	await physics_frame
	await physics_frame
	var hit: Dictionary = game.ray_target()
	expect(not hit.is_empty() and hit.collider.get_meta("identity", -1) == fake, "Crosshair ray hits intended identity")
	for i in 5:
		game.shot_cooldown = 0
		game.fire()
	expect(game.run.eliminated[fake] == 1, "Five actual shots clear a fake")
	expect(game.ammo == 25, "Weapon consumes five rounds")
	expect(game.run.ap == 10, "Five shots award exactly 10 AP")
	expect(game.crowd.death_times[fake] >= 0, "Scan starts the falling animation")
	expect(game.crowd.bodies[fake].collision_layer == 0, "Falling identity cannot block later scans")
	game.reload_gun()
	expect(game.reload_left > 0, "Reload starts")
	await create_timer(1.15).timeout
	expect(game.ammo == 30 and game.reload_left == 0, "Reload completes after one second")
	# Walls stop bullets; sonar sees through walls and stores stationary snapshots.
	var other: int = (fake + 1) % 120
	game.player.position = Vector3(35, 0.1, 7)
	game.crowd.positions[other] = Vector3(40, 0, 7)
	game.crowd.bodies[other].position = Vector3(40, 0.95, 7)
	game.crowd.bodies[other].collision_layer = 2
	game.player.camera.look_at(Vector3(40, 1.2, 7))
	await physics_frame
	await physics_frame
	hit = game.ray_target()
	expect(not hit.is_empty() and not hit.collider.has_meta("identity"), "Mall wall blocks scanner ray")
	game.run.upgrades.sonar = 1
	var snapshots: Array[Vector3] = game.sonar()
	var recorded := Vector3(40, 1.1, 7)
	expect(snapshots.has(recorded), "Sonar includes identity behind wall")
	game.crowd.positions[other] += Vector3(0, 0, 3)
	expect(snapshots.has(recorded), "Sonar snapshot does not follow a moving identity")
	expect(game.sonar().is_empty(), "Sonar cooldown prevents immediate reuse")
	# Special skills and cats never win; the normal gun is still required.
	game.resolve(game.run.true_id, false)
	expect(game.run.located and not game.run.won, "Special scan marks true identity without clearing")
	expect(is_instance_valid(game.beacon), "Located identity receives beacon")
	game.run.ap = 1000
	expect(game.run.purchase("cat"), "Cat can be purchased with earned AP")
	game._make_cat()
	game.run.located = false
	game.cat_target = game.run.true_id
	game.cat.position = game.crowd.positions[game.run.true_id]
	game.cat_scan_time = 19.99
	game._tick_cat(0.02)
	expect(game.run.located and not game.run.won, "Cat also marks true identity without winning")
	game.run.located = false
	game.cat.position = Vector3(0, 0, 12)
	game.cat_target = game.run.true_id
	game.cat_scan_time = 19.99
	game.cat_retarget = 1
	game.cat.set_meta("path", PackedVector3Array())
	game.crowd.positions[game.run.true_id] = Vector3(35, 0, 25)
	game._tick_cat(0.02)
	expect(not game.run.located, "Cat cannot scan a distant target when its route is empty")
	game.set_mode("pause")
	var before: float = game.elapsed
	await create_timer(0.1).timeout
	expect(game.elapsed == before, "Pause freezes game time")
	var escape := InputEventKey.new()
	escape.keycode = KEY_ESCAPE
	escape.pressed = true
	game._input(escape)
	expect(not paused and game.hud.mode == "play", "Escape resumes paused game")
	for i in 5:
		game.resolve(game.run.true_id, true)
	expect(game.run.won and game.hud.mode == "win", "Normal scanner finishes a located true identity")
	expect(game.run.cleared == 1, "Win preserves all other identities")
	game.start_run(120, 904)
	expect(game.run.cleared == 0 and game.run.ap == 0 and game.ammo == 30, "New run resets progression and ammunition")
	expect(not game.run.located and not game.run.won and game.cat == null, "New run resets target and companion")
	game.queue_free()
	await process_frame
	# Let the audio mixing thread release stopped stream playback resources.
	await create_timer(0.2).timeout
	print("RESULT: %d checks, %d failures" % [checks, failures])
	quit(0 if failures == 0 else 1)

func _test_state() -> void:
	var full := IdentityRun.new(5000, 31337)
	expect(full.population == 5000 and full.true_id >= 0 and full.true_id < 5000, "Full population supports exactly one original")
	var fixed := full.true_id
	expect(full.scan(-1) == IdentityRun.Result.INVALID and full.scan(5000) == IdentityRun.Result.INVALID, "Invalid identity IDs are rejected")
	for id in 5000:
		if id == fixed:
			continue
		full.scan(id, false)
		full.scan(id, false)
	expect(full.true_id == fixed, "Original never moves between identities")
	expect(full.cleared == 4999 and full.ap == 49990, "No duplicate AP for repeated special scans")
	expect(full.scan(fixed, false) == IdentityRun.Result.LOCATED and not full.won, "Special scan cannot win even as final identity")
	for i in 4:
		expect(full.scan(fixed) == IdentityRun.Result.HIT, "True identity requires five normal hits")
	expect(full.scan(fixed) == IdentityRun.Result.FOUND, "Fifth normal hit wins")
	expect(full.eliminated[fixed] == 0 and full.cleared == 4999, "True identity is never eliminated")
	var first := IdentityRun.new(1, 19)
	for i in 5:
		first.scan(0)
	expect(first.won and first.cleared == 0, "Finding original first can win without eliminating anyone")
	var skills := IdentityRun.new(120, 42)
	expect(not skills.purchase("focus") and not skills.purchase("bogus"), "Cannot buy without AP or buy unknown skill")
	skills.ap = 10000
	expect(not skills.purchase("cat_speed"), "Cat speed requires a cat")
	for i in 4:
		expect(skills.purchase("focus"), "Focus levels are purchasable")
	expect(skills.required_hits() == 1 and not skills.purchase("focus"), "Focus caps at one required hit")
	expect(skills.ap == 9400, "Focus prices are 60 + 120 + 180 + 240")
	var total := 0
	for building in IdentityRun.DISTRIBUTION:
		for count in IdentityRun.DISTRIBUTION[building]:
			total += count
	expect(total == 5000, "Design distribution totals 5000 across 15 floors")
	# Statistical guard only: implementation is directly uniform randi_range.
	var buckets := PackedInt32Array()
	buckets.resize(10)
	for seed_value in 10000:
		var sample := IdentityRun.new(5000, seed_value)
		buckets[sample.true_id / 500] += 1
	for count in buckets:
		expect(count > 850 and count < 1150, "Uniform selection has no gross decile bias")
