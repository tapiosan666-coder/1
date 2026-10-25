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
	var japanese_font: Font = game.hud.font
	expect(japanese_font.resource_path == "res://assets/fonts/NotoSansCJKjp-Regular.otf", "UI uses the bundled Japanese font")
	var all_glyphs := true
	for path in ["hud", "main", "identity_run", "player", "mall", "npc_speech", "bookshop", "run_loot", "cache_field", "mall_annex", "b_wing", "c_wing", "graphics_options", "skill_panel"]:
		var source := FileAccess.get_file_as_string("res://scripts/%s.gd" % path)
		for character in source:
			var code := character.unicode_at(0)
			if code > 127 and not japanese_font.has_char(code):
				all_glyphs = false
	expect(all_glyphs, "Bundled font covers all Japanese and symbols used by the UI")
	expect(game.hud.skin_select.get_item_text(0) == "明るい肌", "Face selection opens in Japanese")
	expect(game.hud.skin_select.get_theme_font("font") == japanese_font and game.player.reader_screen.font == japanese_font, "Controls and 3D tool display share the bundled font")
	await _test_mall_upgrade(game)
	await _test_skill_limits(game)
	await _test_new_skills(game)
	game.start_run(120, 904)
	await physics_frame
	await physics_frame
	var counts: Dictionary = {}
	for role in game.crowd.roles:
		counts[role] = int(counts.get(role, 0)) + 1
	for expected in [["staff", 45], ["browsing", 37], ["reading",2], ["seated", 14], ["restroom", 6], ["conversation", 4], ["walking", 12]]:
		expect(counts.get(expected[0], 0) == expected[1], "Role population: %s" % expected[0])
	var sitter: int = game.crowd.roles.find("seated")
	var staff: int = game.crowd.roles.find("staff")
	var walker: int = game.crowd.roles.find("walking")
	var sitting_at: Vector3 = game.crowd.positions[sitter]
	var staff_at: Vector3 = game.crowd.positions[staff]
	var walking_from: Vector3 = game.crowd.positions[walker]
	var start_point: int = game.crowd.nav.get_closest_point(walking_from)
	game.crowd.paths[walker] = game.crowd.nav.get_point_path(start_point, (start_point + 10) % game.crowd.nav_ids.size())
	game.crowd.paths[walker].remove_at(0)
	game.crowd.waits[walker] = 0
	await create_timer(0.3).timeout
	expect(game.crowd.positions[sitter] == sitting_at and game.crowd.positions[staff] == staff_at, "Seated patrons and shop staff stay at their assigned stations")
	expect(game.crowd.positions[walker].distance_to(walking_from) > 0.1, "Walking shoppers still navigate the mall")
	game.crowd.set_physics_process(false)
	var reachable_scans := true
	for id in game.run.population:
		if game.crowd.roles[id] == "walking":
			continue
		var visible := false
		for point in game.mall.spawn_points:
			if point.distance_squared_to(game.crowd.positions[id]) > 5.2 * 5.2:
				continue
			var head: Vector3 = game.crowd.positions[id] + Vector3.UP * (1.2 if game.crowd.roles[id] == "seated" else 1.65)
			var query := PhysicsRayQueryParameters3D.create(point + Vector3.UP * 1.65, head, 1)
			if game.get_world_3d().direct_space_state.intersect_ray(query).is_empty():
				visible = true
				break
		if not visible:
			reachable_scans = false
			push_error("No reachable reader vantage for identity %d / %s" % [id, game.crowd.roles[id]])
	expect(reachable_scans, "Every stationary identity can be read from a reachable public point")
	expect(not game.using_gun and game.run.upgrades.gun == 0, "Start with handheld, no gun owned")
	expect(not game.equip(true), "Cannot equip locked gun")
	expect(game.player.handheld.visible and not game.player.gun.visible, "Correct initial tool model visible")
	expect(game.crowd.positions.size() == 120, "120 scene identities created")
	# A single graph traversal proves connectivity without tens of thousands
	# of independent long-distance A* queries after a larger map is authored.
	var connected:Dictionary={0:true};var pending:Array[int]=[0];var cursor:=0
	while cursor<pending.size():
		var point:=pending[cursor];cursor+=1
		for next in game.crowd.nav.get_point_connections(point):
			if not connected.has(next):connected[next]=true;pending.append(next)
	var reachable:bool=connected.size()==game.crowd.nav.get_point_count()
	expect(reachable, "NPC grid is connected")
	var start_x: float = game.player.position.x
	Input.action_press("forward")
	await create_timer(0.25).timeout
	Input.action_release("forward")
	expect(game.player.position.x > start_x + 0.5, "WASD moves character body")
	game.player.position = _world(89.1, 0.1, 7)
	game.player.rotation = Vector3(0,-MallCurve.angle(89.1),0)
	Input.action_press("right")
	await create_timer(0.3).timeout
	Input.action_release("right")
	expect(MallCurve.plan(game.player.position).x < 89.6, "Perimeter blocks movement")
	for part in game.crowd.parts:
		expect(part.instances.mesh != null, "Every instanced body part has geometry")
	var fake: int = (game.run.true_id + 1) % 120
	for body in game.crowd.bodies:
		body.collision_layer = 0
	game.crowd.positions[fake] = _world(11, 0, 2)
	game.crowd.bodies[fake].position = _world(11, 0.95, 2)
	game.crowd.bodies[fake].collision_layer = 2
	game.player.position = _world(11, 0.1, 5)
	game.player.velocity = Vector3.ZERO
	game.player.camera.look_at(_world(11, 1.2, 2))
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
	game.crowd.positions[other] = _world(11, 0, 2)
	game.crowd.bodies[other].position = _world(11, 0.95, 2)
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
	game.player.position = _world(87, 0.1, 7)
	game.crowd.positions[third] = _world(92, 0, 7)
	game.crowd.bodies[third].position = _world(92, 0.95, 7)
	game.crowd.bodies[third].collision_layer = 2
	game.player.camera.look_at(_world(92, 1.2, 7))
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
	var recorded := _world(92, 0, 7) + Vector3.UP * 1.1
	expect(snapshots.has(recorded), "Sonar sees through wall")
	game.crowd.positions[third] += Vector3(0,0,3)
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
	game.cat.position = _world(0, 0, 12)
	game.cat_target = game.run.true_id
	game.cat_scan_time = 19.99
	game.cat_retarget = 1
	game.cat.set_meta("path", PackedVector3Array())
	game.crowd.positions[game.run.true_id] = _world(35, 0, 25)
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
	game.crowd.positions[original] = _world(11, 0, 2)
	game.crowd.bodies[original].position = _world(11, 0.95, 2)
	game.crowd.bodies[original].collision_layer = 2
	game.player.position = _world(11, 0.1, 5)
	game.player.velocity = Vector3.ZERO
	game.player.camera.look_at(_world(11, 1.2, 2))
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

func _test_new_skills(game: Node3D) -> void:
	game.start_run(120, 904)
	game.crowd.set_physics_process(false)
	for id in 120:
		game.crowd.positions[id] = _world(500 + id * 10, 0, 500)
		game.crowd.bodies[id].collision_layer = 0
	var ids: Array[int] = []
	for id in 120:
		if id != game.run.true_id and ids.size() < 3:
			ids.append(id)
	game.run.ap = 10000
	expect(not game.run.purchase("pierce"), "Piercing requires the purchased gun")
	game.run.purchase("gun")
	game.run.purchase("pierce")
	game.equip(true)
	for index in 3:
		var id := ids[index]
		var x: float = [85.0, 87.0, 92.0][index]
		game.crowd.positions[id] = _world(x, 0, 7)
		game.crowd.bodies[id].position = _world(x, .95, 7)
		game.crowd.bodies[id].collision_layer = 2
	game.player.position = _world(83, .1, 7)
	game.player.camera.look_at(_world(92, 1.2, 7))
	await physics_frame
	await physics_frame
	game.fire()
	expect(game.run.hits[ids[0]] == 1 and game.run.hits[ids[1]] == 1, "One piercing bullet hits two aligned people")
	expect(game.run.hits[ids[2]] == 0 and game.ammo == 29, "Piercing stops at wall and spends one cartridge")
	game.run.purchase("chain")
	var original: int = game.run.true_id
	for index in 3:
		var id: int = ids[index] if index < 2 else original
		game.crowd.positions[id] = _world(11 + index * 3, 0, 7)
		game.crowd.bodies[id].position = _world(11 + index * 3, .95, 7)
		game.crowd.bodies[id].collision_layer = 2
	game.crowd.positions[ids[2]] = _world(500, 0, 500)
	game.crowd.bodies[ids[2]].collision_layer = 0
	game.player.position = _world(8, .1, 7)
	game.player.camera.look_at(_world(11, 1.2, 7))
	await physics_frame
	await physics_frame
	game.chain_scan()
	expect(game.run.cleared == 2 and game.run.located and not game.run.won, "Chain clears nearby fakes but only marks original")
	var cleared: int = game.run.cleared
	game.chain_scan()
	expect(game.chain_left > 19 and game.run.cleared == cleared, "Chain cooldown prevents repeated activation")
	game.chain_left = 0
	game.run.located = false
	game.crowd.positions[ids[2]] = _world(87, 0, 7)
	game.crowd.bodies[ids[2]].position = _world(87, .95, 7)
	game.crowd.bodies[ids[2]].collision_layer = 2
	game.crowd.positions[original] = _world(92, 0, 7)
	game.crowd.bodies[original].position = _world(92, .95, 7)
	game.player.position = _world(85, .1, 7)
	game.player.camera.look_at(_world(87, 1.2, 7))
	await physics_frame
	await physics_frame
	game.chain_scan()
	expect(not game.run.located and game.run.eliminated[ids[2]], "Chain cannot jump through the perimeter wall")
	game.player.position = _world(11, 3, 7)
	game.player.velocity = Vector3(0, -1, 0)
	await physics_frame
	Input.action_press("jump")
	await physics_frame
	await physics_frame
	Input.action_release("jump")
	expect(not game.player.air_jump_used and game.player.velocity.y < 0, "Air jump is unavailable before purchase")
	game.run.purchase("double_jump")
	await physics_frame
	game.player.position = _world(11, 3, 7)
	game.player.velocity = Vector3(0, -1, 0)
	await physics_frame
	Input.action_press("jump")
	await physics_frame
	await physics_frame
	Input.action_release("jump")
	expect(game.player.air_jump_used and game.player.velocity.y > 5, "Purchased double jump works once in midair")
	await physics_frame
	game.player.velocity.y = -1
	Input.action_press("jump")
	await physics_frame
	await physics_frame
	Input.action_release("jump")
	expect(game.player.velocity.y < 0, "Cannot jump a third time before landing")
	game.player.position = _world(11, .02, 7)
	game.player.velocity = Vector3(0, -1, 0)
	await physics_frame
	await physics_frame
	await physics_frame
	expect(not game.player.air_jump_used, "Landing restores the extra jump")

func _test_skill_limits(game: Node3D) -> void:
	game.start_run(120, 904)
	game.crowd.set_physics_process(false)
	var ids: Array[int] = []
	for id in 120:
		game.crowd.positions[id] = _world(500 + id * 10, 0, 500)
		game.crowd.bodies[id].collision_layer = 0
		if id != game.run.true_id and ids.size() < 10:
			ids.append(id)
	for index in ids.size():
		var id := ids[index]
		game.crowd.positions[id] = _world(-81 + index * 2, 0, 7)
		game.crowd.bodies[id].position = game.crowd.positions[id] + Vector3.UP * .95
		game.crowd.bodies[id].collision_layer = 2
	game.run.ap = 10000
	for skill in ["gun", "pierce", "chain"]:
		game.run.purchase(skill)
	game.equip(true)
	game.player.position = _world(-83, .1, 7)
	game.player.camera.look_at(_world(-63, 1.5, 7))
	await physics_frame
	await physics_frame
	game.fire()
	expect(game.run.hits[ids[0]] == 1 and game.run.hits[ids[2]] == 1 and game.run.hits[ids[3]] == 0, "Piercing is capped at three people")
	game.chain_scan()
	expect(game.run.cleared == 8 and not game.run.eliminated[ids[8]], "Chain stops after eight people even in a dense line")

func _test_mall_upgrade(game: Node3D) -> void:
	game.start_run(120,904)
	await physics_frame
	await physics_frame
	var head: Mesh
	var hand: Mesh
	var eyes := 0
	for part in game.crowd.parts:
		if part.name == "head": head = part.instances.mesh
		if part.name == "hand_l": hand = part.instances.mesh
		if part.name in ["eye_l","eye_r"] and part.instances.mesh.get_surface_count() >= 3: eyes += 1
	expect(head != null and head.get_surface_count() >= 3 and eyes == 2, "Civilian head and two independent eyes retain distinct skin, iris and pupil materials")
	expect(hand != null and hand.get_aabb().size.y > .10, "Imported human hand includes fingers below palm")
	var state := game.get_world_3d().direct_space_state
	var window := PhysicsRayQueryParameters3D.create(_world(-81,1.6,-6),_world(-81,1.6,-11),1)
	var door := PhysicsRayQueryParameters3D.create(_world(-75,1.6,-6),_world(-75,1.6,-11),1)
	expect(not state.intersect_ray(window).is_empty(), "Shop display glazing has a physical boundary")
	expect(state.intersect_ray(door).is_empty(), "Shop centre entrance stays open")
	var route: PackedVector3Array = game.crowd.nav.get_point_path(game.crowd.nav.get_closest_point(_world(-81,0,-7)),game.crowd.nav.get_closest_point(_world(-81,0,-11)))
	var distance := 0.0
	for index in range(1,route.size()):
		distance += route[index-1].distance_to(route[index])
	expect(distance > 8, "NPC route goes around display glass through the open entrance")
	for key in Mall.HUBS:
		expect(Mall.walkable(Mall.hub_position(key)), "Travel hub is on accessible floor: %s" % key)
	expect(Mall.MARKET.has_point(Vector2(17,24)) and Mall.walkable(_world(17,0,24)), "Large grocery anchor has traversable browsing aisles")
	expect(game.run.visited.has("中央入口") and game.run.visited.size() == 1, "New run records only the visited entrance")
	game.set_mode("map")
	expect(not game.fast_travel("中央入口"), "Travel requires purchased skill")
	game.run.ap = 1000
	game.run.purchase("travel")
	var fixed: int = game.run.true_id
	expect(not game.fast_travel("食品スーパー") and not game.fast_travel("unknown"), "Cannot travel to unvisited or unknown point")
	game.set_mode("play")
	game.player.position = _world(24,.1,7)
	game._visit_points()
	expect(not game.run.visited.has("食品スーパー"), "Standing outside the supermarket does not count as visiting its hub")
	game.player.position = Mall.hub_position("食品スーパー")
	game._visit_points()
	expect(game.run.visited.has("食品スーパー"), "Actually approaching a hub records it")
	game.handheld_scan.tick(1,0,true)
	game.set_mode("map")
	expect(game.fast_travel("中央入口") and game.player.position == Mall.ENTRANCE, "Visited point can be selected from map")
	expect(game.run.true_id == fixed and not game.run.won and game.handheld_scan.seconds == 0, "Travel preserves true identity and resets partial reader scan")
	game.start_run(120,904)
	expect(game.run.visited.size() == 1 and game.run.upgrades.travel == 0, "New run clears visited destinations and travel skill")

func _world(x: float,y: float,z: float) -> Vector3:
	return MallCurve.world(Vector3(x,y,z))
