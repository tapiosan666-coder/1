extends SceneTree
var checks := 0
var failures := 0
func expect(ok: bool,message: String) -> void:
	checks += 1
	if not ok: failures += 1; push_error(message)
func _initialize() -> void: call_deferred("run_tests")
func world(p: Vector3) -> Vector3: return MallCurve.world(p)

func run_tests() -> void:
	var game = load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	game.start_run(180,912)
	await physics_frame; await physics_frame
	game.crowd.set_physics_process(false)
	var fixed: int = game.run.true_id
	var floors := {-1:0,0:0,1:0,2:0,3:0}
	for p in game.crowd.positions: floors[Mall.level_at(p.y)] += 1
	expect(floors == {-1:28,0:75,1:31,2:31,3:15},"Default 180 identities occupy all five floors including B1 and roof")
	expect(game.run.price("gun") == 600,"Gun price scales to the 180-person slice without changing the initial tool")
	var state: PhysicsDirectSpaceState3D = game.get_world_3d().direct_space_state
	for fixture in [Vector3(-82,-5.35,-6.5),Vector3(-87,16.4,-12),Vector3(-120,0,-5.5)]:
		var hit: Dictionary = state.intersect_ray(PhysicsRayQueryParameters3D.create(world(fixture)+Vector3.UP,world(fixture)-Vector3.UP,1))
		expect(not hit.is_empty() and absf(hit.position.y-fixture.y) < .1,"Real floor collision at %s" % fixture)
	var car := MallAnnex.cars()[0]
	expect(not state.intersect_ray(PhysicsRayQueryParameters3D.create(car+Vector3(-3,.7,0),car+Vector3(3,.7,0),1)).is_empty(),"Parked car physically blocks movement and scanning")
	for level in [-1,0,1,2,3]:
		var y := Mall.floor_height(level)
		expect(Mall.level_at(y) == level,"Floor height and label agree for %s" % Mall.floor_title(level))
		var query := PhysicsRayQueryParameters3D.create(Vector3(-94,y+1.6,-7),Vector3(-88,y+1.6,-7),1)
		expect(state.intersect_ray(query).is_empty(),"West circulation doorway is open on %s" % Mall.floor_title(level))
	var from: int = game.crowd.nav.get_closest_point(Mall.ENTRANCE)
	var connected := true
	for key in Mall.HUBS:
		var at := Mall.hub_position(key)
		if not Mall.walkable(at) or game.crowd.nav.get_point_path(from,game.crowd.nav.get_closest_point(at)).is_empty(): connected = false
	expect(connected,"All ten visited-only travel destinations have connected walkable approaches")
	var readable := true
	var parking := 0
	for id in game.run.population:
		if game.crowd.activities[id] == "parking": parking += 1
		if id < 108 or game.crowd.roles[id] == "walking": continue
		var seen := false
		for point in game.mall.spawn_points:
			if point.distance_squared_to(game.crowd.positions[id]) > 5.5*5.5: continue
			var head: Vector3 = game.crowd.positions[id]+Vector3.UP*(1.2 if game.crowd.roles[id] == "seated" else 1.7)
			if state.intersect_ray(PhysicsRayQueryParameters3D.create(point+Vector3.UP*1.68,head,1)).is_empty(): seen = true; break
		if not seen: readable = false; push_error("Unreachable scanner vantage: %d" % id)
	expect(readable and parking == 8,"All new stationary identities have a handheld scanner vantage, including eight parking visitors")
	# Follow the actual switchback flights: no elevator/teleport operation is used.
	game.player.position = Vector3(-87,.05,-7); game.player.velocity = Vector3.ZERO
	expect(await walk_to(game,Vector3(-94,0,-7),4),"Enter west core from mall through the open 1F door")
	expect(await walk_to(game,Vector3(-94,0,-4.5),3),"Walk onto the front landing")
	expect(await walk_to(game,Vector3(-106,0,-5),4),"Reach descending stair flight from landing")
	var routes := MallAnnex.core_routes()
	var down := routes[0].duplicate(); down.reverse()
	expect(await follow(game,down),"Walk continuously from 1F down to B1")
	expect(absf(game.player.position.y-Mall.floor_height(-1)) < .16,"Arrive on the basement floor")
	for route in routes:
		# Move across the same front landing between consecutive flights.
		expect(await walk_to(game,route[0],4),"Approach next switchback stair flight")
		expect(await follow(game,route),"Walk up to %s via physical stairs" % Mall.floor_title(Mall.level_at(route[-1].y)))
	expect(absf(game.player.position.y-16.4) < .16,"Arrive on roof without using fast travel or jumping")
	expect(await walk_to(game,Vector3(-94,16.4,-5),4),"Cross roof core landing")
	expect(await walk_to(game,Vector3(-87,16.4,-6.5),4),"Walk from roof core to terrace access")
	expect(await walk_to(game,Vector3(-87,16.4,-12),4),"Enter roof garden")
	# Reverse the routes from roof back to 1F, then walk into the car park.
	expect(await walk_to(game,Vector3(-87,16.4,-6.5),4),"Leave roof garden through access path")
	expect(await walk_to(game,Vector3(-94,16.4,-5),4),"Return to core roof landing")
	for index in [3,2,1]:
		var route: PackedVector3Array = routes[index].duplicate(); route.reverse()
		expect(await walk_to(game,route[0],4) and await follow(game,route),"Walk down a full storey through core")
	expect(absf(game.player.position.y) < .16,"Return to the actual 1F landing after descending from roof")
	expect(await walk_to(game,Vector3(-119,0,-5),7),"Walk from 1F core directly into the car park")
	expect(game.run.true_id == fixed and not game.run.won,"Full building traversal leaves the original identity fixed")
	# A card for every destination stays on-screen, and unvisited destinations remain locked.
	game.run.ap = 1000; game.run.purchase("travel")
	game.player.position = Mall.ENTRANCE; game._visit_points()
	game.set_mode("map"); await process_frame
	var fit := true
	for button in game.hud.buttons.get_children():
		if button is Button and (button.position.x+button.size.x > 1440 or button.position.y+button.size.y > 900): fit = false
	expect(fit,"All ten destination buttons and resume control fit the map screen")
	game.run.visited.erase("屋上庭園")
	expect(not game.fast_travel("屋上庭園"),"Cannot warp to an unvisited roof")
	game.set_mode("play"); game.player.position = Mall.hub_position("屋上庭園"); game._visit_points()
	game.set_mode("map")
	expect(game.fast_travel("屋上庭園") and absf(game.player.position.y-16.5) < .01,"Visited roof destination preserves its actual vertical position")
	await test_new_area_originals(game)
	game.start_run(180,912)
	var chests_valid := true
	var sample_floors := {}
	for seed_value in 200:
		var loot := RunLoot.new(game.mall.spawn_points,seed_value)
		for chest in loot.chests:
			sample_floors[Mall.level_at(chest.pos.y)] = true
			if not Mall.walkable(chest.pos): chests_valid = false
	expect(chests_valid and sample_floors.size() == 5,"Two hundred chest layouts use legal positions across all five floors")
	game.queue_free(); await process_frame
	print("ANNEX RESULT: %d checks, %d failures" % [checks,failures]); quit(1 if failures else 0)

func test_new_area_originals(game: Node3D) -> void:
	for category in [[108,128,"basement"],[129,136,"roof"],[137,144,"parking"]]:
		var chosen_seed := -1
		for seed_value in 1000:
			var state := IdentityRun.new(180,seed_value)
			if state.true_id >= category[0] and state.true_id <= category[1]: chosen_seed = seed_value; break
		expect(chosen_seed >= 0,"Find a naturally selected original in %s" % category[2])
		game.start_run(180,chosen_seed)
		game.crowd.set_physics_process(false)
		await physics_frame; await physics_frame
		var original: int = game.run.true_id
		var target: Vector3 = game.crowd.positions[original]
		var head := target+Vector3.UP*(1.2 if game.crowd.roles[original] == "seated" else 1.7)
		var found := false
		for point in game.mall.spawn_points:
			if absf(point.y-target.y) > .1 or point.distance_to(target) > 5 or point.distance_to(target) < 1.5: continue
			game.player.position = point+Vector3.UP*.05
			game.player.velocity = Vector3.ZERO
			game.player.camera.look_at(head)
			var hit: Dictionary = game.ray_target()
			if not hit.is_empty() and hit.collider.get_meta("identity",-1) == original: found = true; break
		expect(found,"Actual handheld ray reaches naturally selected original in %s" % category[2])
		if not found: continue
		game.resolve(original,IdentityRun.Source.SPECIAL)
		expect(game.run.located and not game.run.won,"Special scan only locates original in %s" % category[2])
		Input.action_press("fire")
		await create_timer(2.2).timeout
		Input.action_release("fire")
		expect(game.run.won and game.run.true_id == original,"Two-second initial scanner confirms original in %s" % category[2])
		expect(game.run.cleared == 0 and game.crowd.positions.size() == 180,"Other identities remain after a first-person clear in %s" % category[2])

func walk_to(game: Node3D,p: Vector3,seconds: float) -> bool:
	var destination := world(p)
	Input.action_press("forward")
	for frame in ceili(seconds*60):
		var difference: Vector3 = destination-game.player.position; difference.y = 0
		if difference.length() < .18:
			Input.action_release("forward"); await physics_frame; return true
		game.player.rotation.y = atan2(-difference.x,-difference.z)
		await physics_frame
	Input.action_release("forward")
	push_error("Stair walk stuck at %s wanted %s" % [game.player.position,destination])
	quit(1)
	return false

func follow(game: Node3D,route: PackedVector3Array) -> bool:
	for p in route:
		if not await walk_to(game,p,1.5): return false
	return true
