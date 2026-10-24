extends SceneTree
var checks:=0
var failures:=0
func expect(ok:bool,message:String)->void:
	checks+=1
	if not ok:failures+=1;push_error(message)
func _initialize()->void:call_deferred("verify")
func verify()->void:
	var game=load("res://scenes/main.tscn").instantiate();root.add_child(game)
	game.start_run(300,912);game.set_physics_process(false);game.crowd.set_physics_process(false);game.player.set_physics_process(false)
	await physics_frame;await physics_frame
	var state:PhysicsDirectSpaceState3D=game.get_world_3d().direct_space_state
	expect(game.crowd.slots.size()==267 and game.crowd.roles.count("walking")==33,"Dining redesign preserves the 300-person population and fixed/walking budget")
	var empty:=true
	for p in game.mall.spawn_points:
		var plan:=MallCurve.plan(p)
		if Mall.level_at(plan.y)==0 and DiningWing.CLOSED_REAR.has_point(Vector2(plan.x,plan.z)):empty=false
	expect(empty,"Removed rear loop has no public spawn points or treasure candidates")
	for p in [Vector2(-40,-30),Vector2(0,-30),Vector2(35,-33)]:
		expect(not Mall.inside_floor(p),"Closed back-of-house space is no longer public floor: %s"%p)
	var boundary:=PhysicsRayQueryParameters3D.create(MallCurve.world(Vector3(-39,1.6,-21)),MallCurve.world(Vector3(-39,1.6,-27)),1,[game.player.get_rid()])
	expect(not state.intersect_ray(boundary).is_empty(),"Information lounge physically closes the former rear passage")
	var original:int=game.run.true_id
	var waits:Array[int]=[];var staff:Array[int]=[]
	for id in game.crowd.slots.size():
		var plan:=MallCurve.plan(game.crowd.positions[id])
		if game.crowd.activities[id]=="food_wait":waits.append(id)
		if game.crowd.roles[id]=="staff" and Mall.FOOD.has_point(Vector2(plan.x,plan.z)):staff.append(id)
	expect(waits.size()==4 and staff.size()==4,"Four waiting guests and four food tenants retain individual identities")
	for id:int in waits+staff:
		var at:Vector3=game.crowd.positions[id];var reachable:=false
		for nav_id in game.crowd.nav_ids:
			var p:Vector3=game.crowd.nav.get_point_position(nav_id)
			if p.distance_squared_to(at)>CatSearch.REACH*CatSearch.REACH:continue
			if CatSearch.can_scan(p,at,id in waits,state):reachable=true;break
		expect(reachable,"Cat can approach and scan dining identity %d, with its real fixtures"%id)
		var readable:=false
		for nav_id in game.crowd.nav_ids:
			var p:Vector3=game.crowd.nav.get_point_position(nav_id)
			if absf(p.y-at.y)>.4 or p.distance_squared_to(at)>30:continue
			var query:=PhysicsRayQueryParameters3D.create(p+Vector3.UP*1.68,at+Vector3.UP*(1.05 if id in waits else 1.55),1,[game.player.get_rid()])
			if state.intersect_ray(query).is_empty():readable=true;break
		expect(readable,"Initial handheld reader has line of sight to dining identity %d"%id)
	game.player.set_physics_process(true)
	for route in [[Vector3(70,.05,-7),Vector3(70,0,-34)],[Vector3(-39,.05,-12),Vector3(-39,0,-21)]]:
		game.player.position=MallCurve.world(route[0]);game.player.velocity=Vector3.ZERO
		var goal:=MallCurve.world(route[1]);var arrived:=false
		Input.action_press("forward");Input.action_press("sprint")
		for tick in 420:
			var d:Vector3=goal-game.player.position;d.y=0
			if d.length()<.25:arrived=true;break
			game.player.rotation.y=atan2(-d.x,-d.z);await physics_frame
		Input.action_release("forward");Input.action_release("sprint");await physics_frame
		expect(arrived and absf(game.player.position.y)<.15,"Physically walk redesigned route without teleporting, hidden walls or a missing floor")
	expect(game.run.true_id==original and not game.run.won and game.run.ap==0,"Walking the new circulation never changes the original or game progress")
	game.queue_free();await process_frame
	print("DINING RESULT: %d checks, %d failures"%[checks,failures]);quit(1 if failures else 0)
