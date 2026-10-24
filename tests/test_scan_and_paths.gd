extends SceneTree
var checks := 0
var failures := 0
func expect(ok: bool,message: String) -> void:
	checks += 1
	if not ok: failures += 1; push_error(message)
func _initialize() -> void: call_deferred("verify")
func verify() -> void:
	var run := IdentityRun.new(3,912); run.ap = 1000
	expect(run.handheld_seconds() == 2.0,"Initial reader remains two seconds")
	for level in 3:
		expect(run.purchase("handheld_speed") and is_equal_approx(run.handheld_seconds(),[1.5,1.0,.6][level]),"Reader speed is purchasable without a gun, level %d" % level)
	expect(run.ap == 640 and not run.purchase("handheld_speed") and run.upgrades.gun == 0,"Three speed upgrades cost 60/120/180 AP, stop at max and do not unlock the gun")
	var reader := HandheldScan.new()
	expect(reader.tick(.59,0,true,.6) == -1 and reader.tick(.011,0,true,.6) == 0,"Upgraded completion still requires the full continuous duration")
	reader.tick(.4,0,true,.6); reader.tick(.01,1,true,.6)
	expect(reader.seconds < .02 and reader.target_id == 1,"Switching people discards partial progress even with upgrades")
	reader.tick(.2,1,false,.6)
	expect(reader.target_id == -1 and reader.seconds == 0,"Release still cancels the lock")
	var game = load("res://scenes/main.tscn").instantiate(); root.add_child(game)
	game.start_run(3,912); game.set_physics_process(false); game.player.set_physics_process(false); game.crowd.set_physics_process(false)
	game.run.ap = 1000; game.buy_skill("cat"); game.set_mode("play")
	var fake: int = (game.run.true_id+1)%3
	var other: int = (fake+1)%3
	var end := Vector3(-75,0,0)
	game.crowd.positions[fake] = end+Vector3(2.19,0,0); game.crowd.roles[fake] = "browsing"
	game.cat.position = end-Vector3(.04,0,0); game.cat_target = fake; game.cat_retarget = .5
	game.cat.set_meta("path",PackedVector3Array([end]))
	await physics_frame; await physics_frame
	var state: PhysicsDirectSpaceState3D = game.get_world_3d().direct_space_state
	expect(not CatSearch.can_scan(game.cat.position,game.crowd.positions[fake],false,state),"Reproduce stopping four centimetres short of a valid scan endpoint")
	game._tick_cat(.001)
	expect(game.cat.position.is_equal_approx(end) and CatSearch.can_scan(game.cat.position,game.crowd.positions[fake],false,state),"Reached waypoint snaps exactly into valid scan range instead of being discarded")
	game._tick_cat(20.01)
	expect(game.run.eliminated[fake] and game.run.ap == 910,"Formerly stalled endpoint finishes a real fake scan and awards AP once")
	game.run.eliminated[fake] = 0
	game.crowd.positions[fake] = end+Vector3(0,0,1); game.crowd.positions[other] = end+Vector3(20,0,0)
	game.crowd.positions[game.run.true_id] = end+Vector3(0,0,10)
	game.cat.position = end; game.cat_target = other; game.cat_retarget = 0; game.cat_scan_time = 0
	game._tick_cat(.1)
	expect(game.cat_target == fake and game.cat_scan_time > 0,"Cat scans a reachable nearby stationary shopper rather than passing toward a distant commitment")
	game.start_run(3,912); game.crowd.set_physics_process(false); game.set_physics_process(false)
	game.player.position = end+Vector3(0,0,.9)
	var behind := end+Vector3(0,0,1.8)
	await physics_frame; await physics_frame
	var player_ray := PhysicsRayQueryParameters3D.create(end+Vector3.UP*.55,behind+Vector3.UP,1)
	var player_hit := state.intersect_ray(player_ray)
	expect(not player_hit.is_empty() and player_hit.collider == game.player,"Reproduce the player standing in and blocking the cat's old analysis ray")
	expect(CatSearch.can_scan(end,behind,false,state),"The player alone no longer prevents cat analysis")
	var divider := Shapes.box(game,end+Vector3(0,1,1.3),Vector3(2,2,.1),Shapes.material(Color.WHITE),true)
	await physics_frame; await physics_frame
	expect(not CatSearch.can_scan(end,behind,false,state),"A real wall behind the player still blocks the cat after the recast")
	divider.queue_free(); await physics_frame; await physics_frame
	# Aim just outside the old radius and inside the new capsule.
	game.start_run(3,912); game.crowd.set_physics_process(false); game.set_physics_process(false)
	for id in 3:
		game.crowd.positions[id] = Vector3(-85,0,id*2)
		game.crowd.bodies[id].position = game.crowd.positions[id]+Vector3.UP*.95
	game.crowd.roles[fake] = "browsing"; game.crowd._set_body_pose(fake,false)
	game.crowd.positions[fake] = Vector3(-74.61,0,-4)
	game.crowd.bodies[fake].position = game.crowd.positions[fake]+Vector3.UP*.95
	game.player.position = Vector3(-75,.1,0); game.player.camera.look_at(Vector3(-75,1.3,-4))
	await physics_frame; await physics_frame
	var hit: Dictionary = game.ray_target()
	expect(not hit.is_empty() and hit.collider.has_meta("identity") and hit.collider.get_meta("identity") == fake,"A 39cm aim offset now catches the NPC; the previous 32cm capsule missed")
	# Enlarged capsule sticks in front of this wall, while the person is behind it.
	game.crowd.positions[fake] = Vector3(-75,0,-4.30); game.crowd.bodies[fake].position = game.crowd.positions[fake]+Vector3.UP*.95
	var wall := Shapes.box(game,Vector3(-75,1,-4),Vector3(4,2,.1),Shapes.material(Color.WHITE),true)
	await physics_frame; await physics_frame
	var from: Vector3 = game.player.camera.global_position
	var query := PhysicsRayQueryParameters3D.create(from,from-game.player.camera.global_basis.z*6,3,[game.player.get_rid()]); query.collide_with_areas = true
	var raw := state.intersect_ray(query)
	expect(not raw.is_empty() and raw.collider.has_meta("identity"),"Fixture exposes an enlarged capsule in front of the wall")
	hit = game.ray_target()
	expect(not hit.is_empty() and not hit.collider.has_meta("identity"),"Wall validation blocks the protruding hit capsule")
	game._tick_handheld(3,true)
	expect(not game.run.eliminated[fake] and not game.run.won,"Forgiving aim cannot complete a scan through a wall")
	wall.queue_free(); await physics_frame
	game.start_run(300,912); game.crowd.set_physics_process(false); game.set_physics_process(false)
	game.run.ap = 1000; game.buy_skill("cat"); game.set_mode("play"); game.crowd.render_clock = -100000
	game.crowd.rng.seed = 13013
	for id in game.run.population:
		if game.crowd.roles[id] == "walking": game.crowd.waits[id] = 0; game.crowd.paths[id] = PackedVector3Array()
	var search_max := 0; var walker_max := 0
	for tick in 2200:
		game.crowd._physics_process(.1)
		walker_max = maxi(walker_max,game.crowd.path_requests_last_tick)
		var previous := CatSearch.path_searches
		game._tick_cat(.1)
		search_max = maxi(search_max,CatSearch.path_searches-previous)
	expect(walker_max == 1,"Walker A* requests are limited to one per physics update")
	expect(search_max <= 2,"Cat approach planning is bounded to at most two A* searches per update")
	expect(game.run.cleared >= 3 and not game.run.won,"Cat autonomously scans multiple people while walking NPCs continue moving")
	game.queue_free(); await process_frame; await create_timer(.3).timeout
	print("SCAN/PATH RESULT: %d checks, %d failures" % [checks,failures]); quit(1 if failures else 0)
