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
	var fixed: int = game.run.true_id
	var ids: Array[int] = []
	for id in game.run.population:
		if CWing.contains(game.crowd.positions[id]) and game.crowd.roles[id] != "walking": ids.append(id)
	expect(game.run.population == 300 and game.crowd.roles.count("walking") == 33,"C reuses fixed slots and keeps the 300-person population and 33 walkers")
	expect(ids.size() == 30,"Thirty fixed C shopkeepers, shoppers and seated visitors exist before the area is visited")
	expect(game.run.price("gun") == 1000 and game.run.true_id == fixed,"C does not alter the economy formula or selected original")
	expect(WorldCache.can_load() and game.mall.identity_slots.size() == 267,"The prebuilt world includes C without adding fixed-slot overhead")
	expect(CWing.regions(-1).is_empty() and CWing.regions(1).is_empty(),"C only advertises the implemented ground floor")
	var state: PhysicsDirectSpaceState3D = game.get_world_3d().direct_space_state
	for store in CWing.SHOPS:
		var center: Vector3 = store.at+Basis(Vector3.UP,store.yaw)*Vector3(2.2,0,-5)
		var floor_hit: Dictionary = state.intersect_ray(PhysicsRayQueryParameters3D.create(center+Vector3.UP,center-Vector3.UP,1))
		expect(not floor_hit.is_empty() and absf(floor_hit.position.y) < .05,"Physical floor in C shop %s" % store.name)
		var doorway: Vector3 = store.at+Basis(Vector3.UP,store.yaw)*Vector3(0,1.6,3)
		var inside: Vector3 = store.at+Basis(Vector3.UP,store.yaw)*Vector3(0,1.6,-3)
		expect(state.intersect_ray(PhysicsRayQueryParameters3D.create(doorway,inside,1)).is_empty(),"Open public doorway in C shop %s" % store.name)
	var roof_query := PhysicsRayQueryParameters3D.create(Vector3(-370,1.7,-94),Vector3(-370,20,-94),1)
	expect(state.intersect_ray(roof_query).is_empty(),"C's central court remains open to the sky")
	expect(not state.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(-438,.3,-134),Vector3(-432,.3,-134),1)).is_empty(),"Raised planted islands block walking and low scanner rays")
	var all_readable := true
	for id in ids:
		var readable := false
		var head: Vector3 = game.crowd.positions[id]+Vector3.UP*(1.2 if game.crowd.roles[id] == "seated" else 1.7)
		for point in game.mall.spawn_points:
			if point.distance_squared_to(game.crowd.positions[id]) > 5.5*5.5: continue
			if state.intersect_ray(PhysicsRayQueryParameters3D.create(point+Vector3.UP*1.68,head,1)).is_empty(): readable = true; break
		if not readable: all_readable = false; push_error("No reachable scanner vantage for C identity %d" % id)
	expect(all_readable,"All thirty fixed C visitors can be read within handheld range, including terrace and cafe seats")
	var source: int = game.crowd.nav.get_closest_point(Mall.ENTRANCE)
	var connected := true
	for id in ids:
		var target: int = game.crowd.nav.get_closest_point(game.crowd.positions[id])
		if game.crowd.nav.get_point_path(source,target).is_empty(): connected = false
	expect(connected,"C shop approaches are connected to A's entrance through the same cat and walking graph")
	game.player.position = Vector3(-370,.05,-24); game.player.velocity = Vector3.ZERO
	expect(await walk_to(game,Vector3(-370,0,-90),14),"Walk from B's west foyer through its north doorway and the entire covered C link")
	expect(await follow_nav(game,Vector3(-432,0,-120),22),"Walk along the branched street to the garden court")
	expect(await follow_nav(game,Vector3(-432,0,-149),12),"Approach the sports shop around the planted garden island")
	# Follow the public aisle around the new entrance display, in both directions.
	var entered:=true
	for point in [Vector3(-432,0,-154.5),Vector3(-429.8,0,-154.5),Vector3(-429.8,0,-159),Vector3(-432,0,-159)]:
		entered=(await walk_to(game,point,3)) and entered
	expect(entered,"Enter the north shop around its display without jumping or teleporting")
	var left_shop:=true
	for point in [Vector3(-429.8,0,-159),Vector3(-429.8,0,-154.5),Vector3(-432,0,-154.5),Vector3(-432,0,-149)]:
		left_shop=(await walk_to(game,point,3)) and left_shop
	expect(left_shop,"Leave the C shop around its display through the same public doorway")
	expect(game.run.true_id == fixed and not game.run.won,"Physical travel to C preserves the selected original")
	game.run.ap = 1000; game.run.purchase("travel"); game.run.visited.erase("C館テラス")
	game.set_mode("map"); game.hud.set_map_floor(0)
	var before: Vector3 = game.player.position
	expect(not game.fast_travel("C館テラス") and game.player.position == before,"Map browsing does not unlock an unvisited C terrace")
	var fit := true
	for button in game.hud.buttons.get_children():
		if button is Button and (button.position.x+button.size.x > 1440 or button.position.y+button.size.y > 900): fit = false
	expect(Mall.HUBS.size() == 18 and fit,"All eighteen travel destinations fit with the five floor tabs")
	game.set_mode("play"); game.player.position = Mall.hub_position("C館テラス"); game._visit_points(); game.set_mode("map")
	expect(game.fast_travel("C館テラス") and game.player.position == Mall.hub_position("C館テラス"),"C travel requires a real visit and preserves the ground-floor location")
	var has_c_chest := false; var legal_chests := true
	for seed_value in 100:
		var loot := RunLoot.new(game.mall.spawn_points,seed_value)
		for chest in loot.chests:
			if not Mall.walkable(chest.pos): legal_chests = false
			if CWing.contains(chest.pos): has_c_chest = true
	expect(has_c_chest and legal_chests,"Random treasure can appear on C's connected legal floor without changing the ten-chest budget")
	await test_c_original(game,ids)
	game.queue_free(); await process_frame; await create_timer(.3).timeout
	print("WING C RESULT: %d checks, %d failures" % [checks,failures]); quit(1 if failures else 0)

func test_c_original(game: Node3D,ids: Array[int]) -> void:
	var selected_seed := -1
	for seed_value in 2000:
		var run := IdentityRun.new(300,seed_value)
		if run.true_id in ids: selected_seed = seed_value; break
	expect(selected_seed >= 0,"A C visitor can naturally be selected as the original at run creation")
	game.start_run(300,selected_seed); game.crowd.set_physics_process(false)
	await physics_frame; await physics_frame
	var original: int = game.run.true_id
	expect(CWing.contains(game.crowd.positions[original]) and game.run.visited.size() == 1,"C's original exists before C has been visited")
	game.resolve(original,IdentityRun.Source.SPECIAL)
	expect(game.run.located and not game.run.won and game.run.cleared == 0,"Special scanning C's original only reports its position")
	var head: Vector3 = game.crowd.positions[original]+Vector3.UP*(1.2 if game.crowd.roles[original] == "seated" else 1.7)
	var found := false
	for point in game.mall.spawn_points:
		if point.distance_to(game.crowd.positions[original]) > 5 or absf(point.y) > .1: continue
		game.player.position = point+Vector3.UP*.05; game.player.velocity = Vector3.ZERO; game.player.camera.look_at(head)
		var hit: Dictionary = game.ray_target()
		if not hit.is_empty() and hit.collider.get_meta("identity",-1) == original: found = true; break
	expect(found,"The normal handheld targeting ray can reach C's selected original")
	if found:
		Input.action_press("fire"); await create_timer(2.2).timeout; Input.action_release("fire")
		expect(game.run.won and game.run.true_id == original and game.run.cleared == 0,"Only the initial two-second scan confirms C's original; the other 299 people remain")

func walk_to(game: Node3D,target: Vector3,seconds: float) -> bool:
	Input.action_press("sprint"); Input.action_press("forward")
	for frame in ceili(seconds*60):
		var difference: Vector3 = target-game.player.position; difference.y = 0
		if difference.length() < .22:
			Input.action_release("forward"); Input.action_release("sprint"); await physics_frame; return true
		game.player.rotation.y = atan2(-difference.x,-difference.z); await physics_frame
	Input.action_release("forward"); Input.action_release("sprint")
	push_error("C route stuck at %s wanted %s" % [game.player.position,target]); return false

func follow_nav(game:Node3D,target:Vector3,seconds:float)->bool:
	var nav:AStar3D=game.crowd.nav
	var path:=nav.get_point_path(nav.get_closest_point(game.player.position),nav.get_closest_point(target))
	if path.is_empty():return false
	var index:=0
	Input.action_press("sprint");Input.action_press("forward")
	for frame in ceili(seconds*60):
		if index>=path.size():break
		var d:Vector3=path[index]-game.player.position;d.y=0
		if d.length()<.42:index+=1;continue
		game.player.rotation.y=atan2(-d.x,-d.z)
		await physics_frame
	Input.action_release("forward");Input.action_release("sprint");await physics_frame
	if index<path.size():push_error("Route stopped at %s, next %s, destination %s"%[game.player.position,path[index],target])
	return index>=path.size()
