extends SceneTree
var checks := 0
var failures := 0
func expect(ok: bool,message: String) -> void:
	checks += 1
	if not ok: failures += 1; push_error(message)
func _initialize() -> void: call_deferred("run_tests")
func run_tests() -> void:
	var game = load("res://scenes/main.tscn").instantiate(); root.add_child(game)
	game.start_run(300,912); game.crowd.set_physics_process(false)
	await physics_frame; await physics_frame
	var original: int = game.run.true_id
	expect(game.run.population == 300 and game.crowd.positions.size() == 300,"All 300 identities exist before visiting B")
	expect(game.run.price("gun") == 1000,"Gun price retains the population formula for 300 identities")
	var people_in_b := 0
	for p in game.crowd.positions:
		if p.x < -190: people_in_b += 1
	expect(people_in_b >= 122,"B's shop staff, shoppers and cinema patrons are present from the start")
	expect(WorldCache.can_load() and game.mall.render_stats.source_meshes > game.mall.render_stats.sectors*10,"Prebuilt spatial rendering replaces thousands of individual static nodes")
	expect(WorldCache.navigation.positions.size() == game.crowd.nav.get_point_count(),"Precomputed navigation restores all points, including vertical links")
	var state: PhysicsDirectSpaceState3D = game.get_world_3d().direct_space_state
	for level in [0,1,2]:
		var y := Mall.floor_height(level)
		var floor_hit: Dictionary = state.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(-300,y+1,-5),Vector3(-300,y-1,-5),1))
		expect(not floor_hit.is_empty() and absf(floor_hit.position.y-y) < .05,"B gallery floor is physical on level %d" % level)
		var entrance := PhysicsRayQueryParameters3D.create(Vector3(-346,y+1.6,-6),Vector3(-346,y+1.6,-11),1)
		expect(state.intersect_ray(entrance).is_empty(),"B shop entrance is open on level %d" % level)
		if level > 0:
			var hole := PhysicsRayQueryParameters3D.create(Vector3(-300,y+.1,0),Vector3(-300,y-.5,0),1)
			expect(state.intersect_ray(hole).is_empty(),"B upper concourse keeps the open atrium")
	var accessible := true
	for id in range(145,267):
		var visible := false
		for point in game.mall.spawn_points:
			if point.distance_squared_to(game.crowd.positions[id]) > 5.5*5.5: continue
			var head: Vector3 = game.crowd.positions[id]+Vector3.UP*(1.2 if game.crowd.roles[id] == "seated" else 1.7)
			if state.intersect_ray(PhysicsRayQueryParameters3D.create(point+Vector3.UP*1.68,head,1)).is_empty(): visible = true; break
		if not visible: accessible = false; push_error("No scanner vantage for B identity %d" % id)
	expect(accessible,"Every stationary B identity can be reached with a handheld scanner, including cinema seats")
	game.player.position = Vector3(-106,5.575,-5); game.player.velocity = Vector3.ZERO
	expect(await walk_to(game,Vector3(-194,5.525,-5),15),"Walk from A's 2F landing across the entire skybridge into B")
	expect(absf(game.player.position.y-5.525) < .1,"Skybridge traversal preserves the actual 2F height")
	expect(await walk_to(game,Vector3(-222,5.525,-5),5),"Walk along B's long north gallery")
	expect(await walk_to(game,Vector3(-222,5.525,5.5),4),"Cross B's atrium bridge without a blocked railing")
	game.player.position = Vector3(-241.5,.05,7); game.player.velocity = Vector3.ZERO
	expect(await walk_to(game,Vector3(-241.5,5.525,23),5),"Walk up B's first escalator")
	expect(await walk_to(game,Vector3(-227,5.525,23),4),"Walk across B's 2F rear landing")
	expect(await walk_to(game,Vector3(-227,10.875,7.8),5),"Walk up B's second escalator onto 3F")
	expect(absf(game.player.position.y-10.875) < .12,"B's top landing has the expected height")
	expect(await walk_to(game,Vector3(-227,5.525,23),5),"Walk down B's second escalator")
	expect(await walk_to(game,Vector3(-241.5,5.525,23),4),"Return to the first escalator")
	expect(await walk_to(game,Vector3(-241.5,0,7),5),"Walk down to B's ground floor")
	game.player.position = Vector3(-194,.05,-5); game.player.velocity = Vector3.ZERO
	expect(await walk_to(game,Vector3(-170,0,-5),5),"Walk through the ground link and the opened parking fence")
	expect(game.run.true_id == original and not game.run.won,"Travelling between buildings never changes the selected original")
	game.run.ap = 1000; game.run.purchase("travel")
	game.set_mode("map"); await process_frame
	var before: Vector3 = game.player.position
	game.hud.set_map_floor(2)
	expect(game.hud.map_level == 2 and game.player.position == before,"Map floor selector changes the view without moving the player")
	var fit := true
	for button in game.hud.buttons.get_children():
		if button is Button and (button.position.x+button.size.x > 1440 or button.position.y+button.size.y > 900): fit = false
	expect(fit,"All fifteen travel buttons and five floor tabs fit on-screen")
	expect(not game.fast_travel("B館3階シネマ"),"Viewing B's map does not unlock an unvisited cinema")
	game.set_mode("play"); game.player.position = Mall.hub_position("B館3階シネマ"); game._visit_points()
	game.set_mode("map")
	expect(game.fast_travel("B館3階シネマ") and game.player.position == Mall.hub_position("B館3階シネマ"),"Visited B destination retains its building and floor")
	await test_cinema_original(game)
	test_rendering_and_quality(game)
	game.queue_free(); await process_frame
	await create_timer(.2).timeout
	print("WING B RESULT: %d checks, %d failures" % [checks,failures]); quit(1 if failures else 0)

func test_cinema_original(game: Node3D) -> void:
	var seed_value := 0
	while true:
		var state := IdentityRun.new(300,seed_value)
		if state.true_id >= 241 and state.true_id <= 258: break
		seed_value += 1
		assert(seed_value < 2000)
	game.start_run(300,seed_value); game.crowd.set_physics_process(false)
	await physics_frame; await physics_frame
	var original: int = game.run.true_id
	expect(game.crowd.positions[original].x < -390 and game.crowd.activities[original] == "cinema","A cinema patron can naturally be selected before B is visited")
	var head: Vector3 = game.crowd.positions[original]+Vector3.UP*1.2
	var found := false
	for point in game.mall.spawn_points:
		if absf(point.y-10.875) > .1 or point.distance_to(game.crowd.positions[original]) > 5: continue
		game.player.position = point+Vector3.UP*.05; game.player.velocity = Vector3.ZERO; game.player.camera.look_at(head)
		var hit: Dictionary = game.ray_target()
		if not hit.is_empty() and hit.collider.get_meta("identity",-1) == original: found = true; break
	expect(found,"Handheld ray reaches the selected seated cinema patron")
	if found:
		game.resolve(original,IdentityRun.Source.SPECIAL)
		expect(game.run.located and not game.run.won,"Special scan of B's original only sends a location")
		Input.action_press("fire"); await create_timer(2.2).timeout; Input.action_release("fire")
		expect(game.run.won and game.run.true_id == original and game.run.cleared == 0,"Only the initial two-second scanner confirms B's original and keeps the other people")

func test_rendering_and_quality(game: Node3D) -> void:
	game.start_run(300,912); game.crowd.set_physics_process(false)
	for id in game.run.population:
		game.crowd.positions[id] = Vector3(1000+id*3,0,1000)
	game.crowd.positions[0] = Vector3(-75,0,0); game.crowd.positions[1] = Vector3(-40,0,0)
	game.crowd.positions[2] = Vector3(-80,0,-200)
	game.player.position = Vector3(-80,.05,0); game.player.camera.look_at(Vector3(-70,1.7,0))
	var selected: int = game.run.true_id
	var before: Array[Vector3] = game.crowd.positions.duplicate()
	game.crowd._render()
	expect(0 in game.crowd.detailed_ids,"Nearby visible NPC retains the full original model")
	expect(1 in game.crowd.rendered_ids and 1 not in game.crowd.detailed_ids,"Farther visible NPC uses the lightweight silhouette")
	expect(2 not in game.crowd.rendered_ids and game.crowd.bodies[2].collision_layer == 2,"Distant rendering is hidden while its identity and scan collider remain")
	expect(game.crowd.positions == before and game.run.true_id == selected and game.run.ap == 0 and game.run.cleared == 0,"LOD updates never move identities, change truth or award AP")
	GraphicsOptions.apply(game,"low",false)
	expect(is_equal_approx(game.get_viewport().scaling_3d_scale,.75) and game.crowd.detail_distance == 18,"Low quality lowers only rendering detail and 3D resolution")
	expect(game.run.true_id == selected and game.crowd.positions == before,"Graphics quality leaves gameplay identity state unchanged")
	GraphicsOptions.apply(game,"balanced",false)
	expect(is_equal_approx(game.get_viewport().scaling_3d_scale,1.0),"Balanced quality restores full 3D resolution")
	expect(not game.hud.adapter_name.is_empty(),"Pause screen can show the active graphics adapter")

func walk_to(game: Node3D,target: Vector3,seconds: float) -> bool:
	Input.action_press("sprint"); Input.action_press("forward")
	for frame in ceili(seconds*60):
		var difference: Vector3 = target-game.player.position; difference.y = 0
		if difference.length() < .22:
			Input.action_release("forward"); Input.action_release("sprint"); await physics_frame; return true
		game.player.rotation.y = atan2(-difference.x,-difference.z)
		await physics_frame
	Input.action_release("forward"); Input.action_release("sprint")
	push_error("B route stuck at %s wanted %s" % [game.player.position,target]); quit(1); return false
