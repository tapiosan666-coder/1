extends SceneTree
var checks := 0
var failures := 0
func expect(ok: bool,message: String) -> void:
	checks += 1
	if not ok: failures += 1; push_error(message)
func _initialize() -> void: call_deferred("run_tests")
func run_tests() -> void:
	var game = load("res://scenes/main.tscn").instantiate(); root.add_child(game)
	game.start_run(300,912); game.set_physics_process(false); game.crowd.set_physics_process(false); game.player.set_physics_process(false)
	await physics_frame; await physics_frame
	var state: PhysicsDirectSpaceState3D = game.get_world_3d().direct_space_state
	var selected: int = game.run.true_id
	game.run.ap = 1000; game.buy_skill("cat"); game.set_mode("play")
	expect(Mall.walkable(game.cat.position),"A purchased cat spawns on a public navigation point, even when the player is beside furniture")
	var blocked_id := -1; var approach := Vector3.ZERO
	for id in game.run.population:
		if id == selected or game.crowd.roles[id] == "walking": continue
		var at: Vector3 = game.crowd.nav.get_point_position(game.crowd.nav.get_closest_point(game.crowd.positions[id]))
		if at.distance_to(game.crowd.positions[id]) <= 1.12: continue
		if CatSearch.can_scan(at,game.crowd.positions[id],game.crowd.roles[id] == "seated",state): blocked_id = id; approach = at; break
	expect(blocked_id >= 0,"Reproduce a stationary NPC whose nearest public point is beyond the old 1.1m limit")
	if blocked_id >= 0:
		game.cat.position = approach; game.cat_target = blocked_id; game.cat_scan_time = 0
		for tick in 199: game._tick_cat(.1)
		expect(not game.run.eliminated[blocked_id] and game.hud.cat_status.contains("解析中"),"Cat visibly reports progress and does not finish before the twenty-second requirement")
		game._tick_cat(.2)
		expect(game.run.eliminated[blocked_id] and game.run.ap == 910,"Cat completes the formerly stuck target and awards exactly ten AP")
	game.start_run(300,912); game.crowd.set_physics_process(false); game.set_physics_process(false)
	game.run.ap = 1000; game.buy_skill("cat"); game.set_mode("play")
	# Real starting population and furniture: no manual target and no moved identities.
	for tick in 1600: game._tick_cat(.1)
	expect(game.run.cleared >= 3,"The cat autonomously approaches and scans multiple real stationary shoppers without manual target assignment")
	expect(game.run.true_id == selected and not game.run.won,"Autonomous cat work never changes the original or wins the game")
	var fake: int = (selected+1)%300
	game.crowd.positions[fake] = MallCurve.world(Vector3(-81,0,-9))
	game.cat.position = MallCurve.world(Vector3(-81,0,-8)); game.cat_target = fake; game.cat_scan_time = 19.99; game.cat_retarget = 1
	game.run.eliminated[fake] = 0
	var ap: int = game.run.ap
	game._tick_cat(.02)
	expect(not game.run.eliminated[fake] and game.run.ap == ap,"A cat beside a display window cannot scan through the glass")
	game.crowd.positions[selected] = Vector3(-75,0,0); game.cat.position = Vector3(-75,0,1)
	game.run.located = false; game.cat_target = selected; game.cat_scan_time = 19.99
	game._tick_cat(.02)
	expect(game.run.located and not game.run.won and not game.run.eliminated[selected],"Cat detection of the original only marks its location")
	await test_wider_walkways(game)
	await test_skill_panel(game)
	game.queue_free(); await process_frame; await create_timer(.3).timeout
	print("CAT/SKILLS RESULT: %d checks, %d failures" % [checks,failures]); quit(1 if failures else 0)

func test_wider_walkways(game: Node3D) -> void:
	game.player.set_physics_process(true)
	for level in [1,2]:
		var y := Mall.floor_height(level)
		for route in [[Vector3(-82,y+.05,4.45),Vector3(-67,y,4.45)],[Vector3(-300,y+.05,2.5),Vector3(-289,y,2.5)]]:
			game.player.position = MallCurve.world(route[0]); game.player.velocity = Vector3.ZERO
			var target := MallCurve.world(route[1]); Input.action_press("sprint"); Input.action_press("forward")
			var arrived := false
			for step in 240:
				var difference: Vector3 = target-game.player.position; difference.y = 0
				if difference.length() < .22: arrived = true; break
				game.player.rotation.y = atan2(-difference.x,-difference.z); await physics_frame
			Input.action_release("forward"); Input.action_release("sprint"); await physics_frame
			expect(arrived and absf(game.player.position.y-y) < .15,"Walk along the newly widened edge without falling or hitting the old railing: level %d, x %.0f" % [level,route[0].x])
	game.player.set_physics_process(false)

func test_skill_panel(game: Node3D) -> void:
	game.start_run(300,912); game.set_physics_process(false); game.crowd.set_physics_process(false)
	game.run.ap = 0; game.hud.skill_branch = 0; game.hud.skill_selected = "focus"; game.set_mode("skills")
	expect(game.hud.buttons.get_node("SkillPurchase").disabled and game.hud.buttons.get_node("SkillPurchaseReason").text.contains("スキャン銃"),"Locked gun upgrades remain inspectable and explain their exact prerequisite")
	var all_keys := {}; var fits := true
	for branch in 4:
		game.hud.buttons.get_node("SkillBranch_%d" % branch).pressed.emit(); await process_frame
		for key in SkillPanel.BRANCHES[branch].keys:
			all_keys[key] = true
			var card: Button = game.hud.buttons.get_node("SkillCard_"+key)
			card.pressed.emit(); await process_frame
			expect(game.hud.skill_selected == key and game.hud.buttons.get_node("SkillDetailTitle").text == IdentityRun.SKILLS[key].name,"Selecting %s shows its own details without buying it" % key)
		for node in game.hud.buttons.get_children():
			if node is Control and (node.position.x+node.size.x > 1440 or node.position.y+node.size.y > 900): fits = false
	expect(all_keys.size() == IdentityRun.SKILLS.size() and fits and game.run.ap == 0,"Four branches expose all fifteen skills, fit on-screen and never spend AP on selection")
	game.hud.skill_branch = 1; game.hud.skill_selected = "cat_speed"; game.hud.show_mode("skills")
	expect(game.hud.buttons.get_node("SkillPurchaseReason").text.contains("探索猫"),"Cat speed explains its cat prerequisite")
	game.hud.skill_selected = "cat"; game.hud.show_mode("skills")
	expect(game.hud.buttons.get_node("SkillPurchase").disabled and game.hud.buttons.get_node("SkillPurchaseReason").text.contains("100 AP"),"AP shortage is explicit and purchase is disabled")
	game.run.ap = 100; game.hud.show_mode("skills"); game.hud.buttons.get_node("SkillPurchase").pressed.emit(); await process_frame
	expect(game.run.upgrades.cat == 1 and game.run.ap == 0 and is_instance_valid(game.cat),"The dedicated purchase button buys one cat and immediately refreshes the panel")
	expect(game.hud.buttons.get_node("SkillPurchase").disabled and game.hud.buttons.get_node("SkillPurchaseReason").text.contains("最大"),"Maxed skills cannot be bought again")
