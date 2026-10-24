extends SceneTree
var checks := 0
var failures := 0
func expect(ok: bool,message: String) -> void:
	checks += 1
	if not ok: failures += 1; push_error(message)
func _initialize() -> void: call_deferred("run_tests")
func world(x: float,y: float,z: float) -> Vector3: return MallCurve.world(Vector3(x,y,z))

func run_tests() -> void:
	var game = load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	game.start_run(120,912)
	await physics_frame; await physics_frame
	game.crowd.set_physics_process(false)
	var fixed: int = game.run.true_id
	var floors := {-1:0,0:0,1:0,2:0,3:0}
	for p in game.crowd.positions: floors[Mall.level_at(p.y)] += 1
	expect(floors[0] >= 60 and floors[1] >= 24 and floors[2] >= 24 and floors[-1] > 0 and floors[3] > 0,"120-person regression fixture retains existing stationary roles and walkers on all floors")
	for level in 3:
		var y := Mall.floor_height(level)
		var from := world(-75,y+2,-10)
		var hit: Dictionary = game.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(from,from-Vector3.UP*3,1))
		expect(not hit.is_empty() and absf(hit.position.y-y) < .12,"Store floor has physical collision on floor %d" % (level+1))
		var door := PhysicsRayQueryParameters3D.create(world(-75,y+1.6,-6),world(-75,y+1.6,-11),1)
		expect(game.get_world_3d().direct_space_state.intersect_ray(door).is_empty(),"Actual store entrance is open on floor %d" % (level+1))
		if level > 0:
			var void_hit: Dictionary = game.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(world(-20,y+.3,0),world(-20,y-.5,0),1))
			expect(void_hit.is_empty(),"Atrium has no solid slab across floor %d" % (level+1))
	var inverse_ok := true
	for x in range(-89,93,7):
		for z in range(-60,55,9):
			var p := Vector3(x,5.525,z)
			if MallCurve.plan(MallCurve.world(p)).distance_to(p) > .001: inverse_ok = false
	expect(inverse_ok,"Curved rendering and logical navigation round-trip consistently")
	expect(Mall.walkable(world(53,0,19)) and Mall.walkable(world(55,10.875,19)),"Counter-edge spawn points stay consistent after curved float coordinate conversion")
	game.player.position = world(-43.5,.05,7)
	game.player.velocity = Vector3.ZERO
	expect(await walk_to(game,world(-43.5,5.525,22.7),6),"Walk up first escalator without jumping or teleporting")
	expect(absf(game.player.position.y-5.525) < .15,"First escalator lands on 2F")
	expect(await walk_to(game,world(-35,5.525,22.7),4),"Walk between escalators on the 2F landing")
	expect(await walk_to(game,world(-35,10.875,7.8),6),"Walk up second escalator onto 3F")
	expect(absf(game.player.position.y-10.875) < .15,"Second escalator lands on 3F")
	expect(await walk_to(game,world(-35,5.525,22.7),6),"Can walk down from 3F")
	expect(await walk_to(game,world(-43.5,5.525,22.7),4),"Can cross 2F rear landing")
	expect(await walk_to(game,world(-43.5,0,7.5),6),"Can return to 1F down the escalator")
	for level in [1,2]:
		game.player.position = world(-60,Mall.floor_height(level)+.1,-6.5)
		game.player.velocity = Vector3.ZERO
		expect(await walk_to(game,world(-60,Mall.floor_height(level),6.5),5),"Cross the atrium bridge on floor %d without railing blocking the entrance" % (level+1))
	var source: int = game.crowd.nav.get_closest_point(world(-43,0,7))
	var dest: int = game.crowd.nav.get_closest_point(world(-75,10.875,-17))
	var path: PackedVector3Array = game.crowd.nav.get_point_path(source,dest)
	expect(not path.is_empty() and path.size() > 10,"Cat and attraction navigation connect ground to 3F shop")
	# Bubble: same contextual text regardless of truth, respects distance, wall and floor.
	for id in game.run.population:
		game.crowd.positions[id] = Vector3(500+id*10,0,500)
		game.crowd.bodies[id].collision_layer = 0
	game.crowd.positions[0] = world(-75,5.525,-12)
	game.crowd.roles[0] = "staff"
	game.player.position = world(-75,5.625,-9.5)
	game.player.camera.look_at(world(-75,7,-12))
	expect(game.speech.update_nearby(game.crowd,game.player.camera,true) == 0 and not game.speech.label.text.is_empty(),"Near a visible NPC shows Japanese contextual bubble")
	var text: String = game.speech.label.text
	game.run.true_id = 0
	game.speech.update_nearby(game.crowd,game.player.camera,true)
	expect(game.speech.label.text == text,"Dialogue cannot disclose original identity")
	game.player.position = world(-75,5.625,-3)
	expect(game.speech.update_nearby(game.crowd,game.player.camera,true) == -1,"Bubble hides outside proximity range")
	game.player.position = world(-81,5.625,-7)
	game.crowd.positions[0] = world(-81,5.525,-10)
	game.player.camera.look_at(world(-81,7,-10))
	expect(game.speech.update_nearby(game.crowd,game.player.camera,true) == -1,"Bubble does not appear through shop glazing")
	game.player.position = world(-75,.1,-10)
	game.crowd.positions[0] = world(-75,5.525,-10)
	expect(game.speech.update_nearby(game.crowd,game.player.camera,true) == -1,"Bubble does not leak from another floor")
	game.run.true_id = fixed
	_test_motion()
	await test_loot(game)
	game.queue_free(); await process_frame
	await create_timer(.2).timeout
	print("EXPANSION RESULT: %d checks, %d failures" % [checks,failures]); quit(1 if failures else 0)

func walk_to(game: Node3D,destination: Vector3,seconds: float) -> bool:
	var frames := ceili(seconds*60)
	Input.action_press("forward")
	for step in frames:
		var d: Vector3 = destination-game.player.position; d.y = 0
		if d.length() < .25:
			Input.action_release("forward"); await physics_frame; return true
		game.player.rotation.y = atan2(-d.x,-d.z)
		await physics_frame
	Input.action_release("forward")
	push_error("Walk stuck at %s, wanted %s" % [MallCurve.plan(game.player.position),MallCurve.plan(destination)])
	return false

func _test_motion() -> void:
	var valid := true
	for role in ["walking","staff","reading","browsing","seated","conversation","restroom"]:
		for time in [0.,1.,4.,8.]:
			var pose := CivilianMotion.sample(role,"book" if role == "reading" else role,time,0)
			for side in ["left","right"]:
				var arm: Dictionary = pose[side]
				var upper_end: Vector3 = arm.arm.pos-arm.arm.basis.y*.15
				var lower_start: Vector3 = arm.forearm.pos+arm.forearm.basis.y*.145
				if upper_end.distance_to(lower_start) > .001: valid = false
	expect(valid,"Procedural role animations keep elbows connected through the pose cycle")

func test_loot(game: Node3D) -> void:
	game.start_run(120,912); await physics_frame; await physics_frame
	game.crowd.set_physics_process(false)
	var fixed: int = game.run.true_id
	var rarities := {"通常":0,"レア":0,"伝説":0}
	var reachable := true
	var first: int = game.crowd.nav.get_closest_point(Mall.ENTRANCE)
	for chest in game.loot.chests:
		rarities[chest.rarity] += 1
		var dest: int = game.crowd.nav.get_closest_point(chest.pos)
		if not Mall.walkable(chest.pos) or game.crowd.nav.get_point_path(first,dest).is_empty(): reachable = false
	expect(game.loot.chests.size() == 10 and rarities == {"通常":6,"レア":3,"伝説":1},"Exactly six normal, three rare and one legendary chest")
	expect(reachable,"Every random chest is reachable across the three-floor graph")
	var varied := false
	var legal := true
	for seed_value in 200:
		var layout := RunLoot.new(game.mall.spawn_points,seed_value)
		if layout.chests[0].pos != game.loot.chests[0].pos: varied = true
		for index in layout.chests.size():
			var p: Vector3 = layout.chests[index].pos
			if not Mall.walkable(p): legal = false
			for other in range(index):
				if p.distance_squared_to(layout.chests[other].pos) < 36: legal = false
	expect(legal and varied,"200 seeded treasure layouts use accessible separated positions and vary between runs")
	expect(RunLoot.new(game.mall.spawn_points,912).chests == game.loot.chests,"Seeded cache generation is reproducible without changing original identity")
	var chest: Dictionary = game.loot.chests[0]
	game.player.position = chest.pos+Vector3(.8,.1,0)
	game.player.camera.look_at(chest.pos+Vector3.UP*.4)
	await physics_frame
	expect(game.open_cache(),"G action opens a nearby reachable chest")
	var count: int = game.loot.inventory[chest.item]
	expect(not game.open_cache() and game.loot.inventory[chest.item] == count,"Opened chest cannot duplicate items")
	game.player.position = Mall.ENTRANCE
	expect(not game.open_cache(),"Cannot open a chest remotely")
	# Timed consumables, pause and reset preserve the contract.
	for key in RunLoot.ITEMS: game.loot.inventory[key] = 1
	game.player.position = world(-75,.1,0)
	expect(game.use_item("clock") and game.crowd.frozen,"Clock freezes NPC actions immediately")
	var clock: float = game.crowd.clock
	game.crowd._physics_process(.25)
	expect(game.crowd.clock == clock,"Frozen action clock does not advance")
	expect(game.use_item("cart") and game.player.cart_boost > 1,"Cart temporarily raises move speed")
	game.set_mode("inventory")
	await process_frame
	var cards_fit := true
	for button in game.hud.buttons.get_children():
		if button is Button and button.position.y < 750 and (button.size.x > 313 or button.position.x+button.size.x > 1390): cards_fit = false
	expect(cards_fit,"Inventory descriptions fit inside four non-overlapping cards per row")
	var copy: Label = game.hud.buttons.get_child(0).get_node("ItemCopy")
	expect(copy.get_line_count() > copy.text.count("\n")+1 and copy.get_minimum_size().y <= 191,"Long item description actually wraps instead of being clipped")
	var before: float = game.loot.clock_left
	await create_timer(.15).timeout
	expect(game.loot.clock_left == before,"Inventory pauses consumable timers")
	expect(not game.use_item("sonar"),"Cannot consume items in a menu")
	game.set_mode("play")
	game._tick_items(31)
	expect(not game.crowd.frozen and game.player.cart_boost == 1,"Clock and cart expire cleanly")
	var snapshots: Array[Vector3] = game._global_snapshot()
	var recorded: Vector3 = snapshots[0]
	game.crowd.positions[0] += Vector3(1,0,0)
	expect(snapshots[0] == recorded,"Global sonar snapshot does not follow moving NPCs")
	# Special attacks may locate the original, never finish the run.
	for key in ["hole","laser","disco","chain"]:
		game.start_run(120,912); await physics_frame; await physics_frame
		game.crowd.set_physics_process(false)
		for id in game.run.population:
			game.crowd.positions[id] = Vector3(500+id*10,0,500); game.crowd.bodies[id].collision_layer = 0
		var original: int = game.run.true_id
		game.crowd.positions[original] = world(-75,0,2)
		game.crowd.bodies[original].position = world(-75,.95,2); game.crowd.bodies[original].collision_layer = 2
		game.player.position = world(-75,.1,5)
		game.player.camera.look_at(world(-75,1.2,2))
		game.loot.inventory[key] = 1
		await physics_frame
		expect(game.use_item(key) and game.loot.inventory[key] == 0,"%s consumes one owned item" % key)
		if key == "disco": game._tick_items(.01)
		expect(game.run.located and not game.run.won and not game.run.eliminated[original],"%s locates original without automatic clear" % key)
		expect(not game.use_item(key),"%s cannot be reused without inventory" % key)
	game.start_run(120,912); await physics_frame; await physics_frame
	game.crowd.set_physics_process(false)
	var id: int = game.crowd.roles.find("reading")
	var home: Vector3 = game.crowd.positions[id]
	game.crowd.attract(home+Vector3(0,0,1),5,.1)
	var participated: bool = game.crowd.attracted.has(id)
	for step in 1200: game.crowd._physics_process(.02)
	expect(participated and not game.crowd.attracted.has(id) and game.crowd.positions[id] == home,"Magnet gathers a seated reader and restores their home and pose")
	expect(game.run.true_id == fixed and not game.run.won,"Item effects preserve the original fixed random identity")
	game.loot.inventory.hole = 4; game.loot.clock_left = 8
	game.start_run(120,912)
	expect(game.loot.inventory.hole == 0 and game.loot.clock_left == 0 and not game.crowd.frozen and game.speech.current_id == -1,"New run clears items, buffs and speech bubble")
