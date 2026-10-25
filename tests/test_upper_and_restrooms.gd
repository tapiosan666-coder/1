extends SceneTree
var checks:=0
var failures:=0
func expect(ok:bool,message:String)->void:
	checks+=1
	if not ok:failures+=1;push_error(message)
func _initialize()->void:call_deferred("verify")
func verify()->void:
	var dirty:=PackedVector2Array([Vector2.ZERO,Vector2(1,0),Vector2(1.00001,0),Vector2(2,0),Vector2(2,2),Vector2(0,2),Vector2.ZERO])
	var cleaned:=FindHUD.clean_map_polygon(dirty)
	expect(cleaned.size()==4 and Geometry2D.triangulate_polygon(cleaned).size()==6,"Minimap clipping removes duplicate and collinear vertices without changing the filled rectangle")
	expect(FindHUD.clean_map_polygon(PackedVector2Array([Vector2(0,0),Vector2(2,0),Vector2(2,.00001)])).is_empty(),"Clipped zero-area map slivers do not reach the renderer")
	var bad:=0;var triangles:=0
	for kind in ["garment","cosmetics","glasses","jewelry","suitcase","guitar","toy","stationery","model_car"]:
		var mesh:=TenantProducts.make(kind)
		for surface in mesh.get_surface_count():
			var a:=mesh.surface_get_arrays(surface);var ids:PackedInt32Array=a[Mesh.ARRAY_INDEX]
			for i in range(0,ids.size(),3):
				var cross:Vector3=(a[Mesh.ARRAY_VERTEX][ids[i+1]]-a[Mesh.ARRAY_VERTEX][ids[i]]).cross(a[Mesh.ARRAY_VERTEX][ids[i+2]]-a[Mesh.ARRAY_VERTEX][ids[i]])
				if cross.length_squared()<.000000000001:continue
				triangles+=1
				var normal:Vector3=a[Mesh.ARRAY_NORMAL][ids[i]]+a[Mesh.ARRAY_NORMAL][ids[i+1]]+a[Mesh.ARRAY_NORMAL][ids[i+2]]
				if cross.dot(normal)>.0000001:bad+=1
	expect(triangles>1000 and bad==0,"New goods have outward-facing clockwise triangles")
	var names:={}
	for level in [1,2]:
		var tenants:=TenantCatalog.all_for_floor(level)
		expect(tenants.size()==12,"Each upper floor has twelve fitted stores")
		for tenant in tenants:names[tenant.name]=true
	expect(names.size()==24,"All 24 upper-floor tenant names differ")
	var game=load("res://scenes/main.tscn").instantiate();root.add_child(game)
	game.start_run(300,912);game.crowd.set_physics_process(false);game.set_physics_process(false);game.player.set_physics_process(false)
	await physics_frame;await physics_frame
	var state:PhysicsDirectSpaceState3D=game.get_world_3d().direct_space_state
	expect(game.mall.get_meta("upper_tenants",[]).size()==24,"Upper-floor metadata survives cached loading")
	expect(game.mall.get_meta("restroom_layout",{}).get("stalls",0)==9,"Restroom fixture metadata survives cached loading")
	expect(game.doors.doors.size()==13 and game.mall.find_children("*","AnimatableBody3D",true,false).is_empty(),"Thirteen dynamic doors are outside the static cached world")
	expect(game.crowd.slots.size()==267 and game.crowd.roles.count("walking")==33,"Population remains 267 fixed plus 33 walking")
	var reachable:=true;var readable:=true;var targets:=0
	for id in game.crowd.slots.size():
		var p:=MallCurve.plan(game.crowd.positions[id])
		if not ((Mall.level_at(p.y) in [1,2] and p.x>=-90) or (Mall.level_at(p.y)==0 and Mall.RESTROOM.has_point(Vector2(p.x,p.z)))):continue
		targets+=1;var cat_ok:=false;var reader_ok:=false
		for nav_id in game.crowd.nav_ids:
			var at:Vector3=game.crowd.nav.get_point_position(nav_id)
			if absf(at.y-game.crowd.positions[id].y)>.4 or at.distance_squared_to(game.crowd.positions[id])>30:continue
			if CatSearch.can_scan(at,game.crowd.positions[id],false,state):cat_ok=true
			var ray:=PhysicsRayQueryParameters3D.create(at+Vector3.UP*1.65,game.crowd.positions[id]+Vector3.UP*1.5,1,[game.player.get_rid()])
			if state.intersect_ray(ray).is_empty():reader_ok=true
			if cat_ok and reader_ok:break
		if not cat_ok:push_error("Cat cannot reach changed slot %d at %s"%[id,p])
		if not reader_ok:push_error("Reader cannot see changed slot %d at %s"%[id,p])
		reachable=reachable and cat_ok;readable=readable and reader_ok
	expect(targets==54 and reachable,"Cats can approach all 54 identities in the changed areas")
	expect(readable,"Initial scanner has a clear approach to every changed identity")
	var private_empty:=true
	for point in game.mall.spawn_points:
		var p:=MallCurve.plan(point)
		if Mall.level_at(p.y)!=0:continue
		for room in RestroomWing.PRIVATE_ROOMS:
			if room.has_point(Vector2(p.x,p.z)):private_empty=false
		if p.z>=52.4 and ((p.x>=-82.5 and p.x<-76.5) or (p.x>=-69.5 and p.x<-57.5)) and Mall.RESTROOM.has_point(Vector2(p.x,p.z)):private_empty=false
	expect(private_empty,"No NPC/treasure candidates are placed behind private doors")
	var first:int=game.crowd.nav.get_closest_point(Mall.ENTRANCE)
	var chest_ok:=true
	for seed_value in 100:
		var loot:=RunLoot.new(game.mall.spawn_points,seed_value)
		for chest in loot.chests:
			if not Mall.walkable(chest.pos) or game.crowd.nav.get_point_path(first,game.crowd.nav.get_closest_point(chest.pos)).is_empty():chest_ok=false
	expect(chest_ok,"100 treasure layouts remain reachable from the entrance with private rooms excluded")
	await test_doors(game,state)
	await test_each_door(game,state)
	game.player.set_physics_process(true)
	for position in [Vector3(-57,Mall.floor_height(1),-6),Vector3(15,Mall.floor_height(2),-6)]:
		game.player.position=MallCurve.world(position+Vector3.UP*.05);game.player.velocity=Vector3.ZERO
		# Enter through the unchanged doorway, then follow the aisle around the
		# new central merchandising table instead of walking through that table.
		var walked:=true
		for offset in [Vector3(0,0,-4),Vector3(2.2,0,-4),Vector3(2.2,0,-10),Vector3(0,0,-10)]:
			walked=(await walk_to(game,MallCurve.world(position+offset),4)) and walked
		expect(walked,"Physically enter the shop and walk around its central display without a hidden collision")
	game.queue_free();await process_frame
	print("UPPER/RESTROOM RESULT: %d checks, %d failures"%[checks,failures]);quit(1 if failures else 0)

func test_doors(game:Node3D,state:PhysicsDirectSpaceState3D)->void:
	var original:int=game.run.true_id
	var door:Dictionary=game.doors.doors[0]
	var hinge:Vector3=door.spec.hinge
	var outside:=hinge+Vector3(door.spec.width*.5,-hinge.y,-1.6)
	game.player.position=outside+Vector3.UP*.05;game.player.velocity=Vector3.ZERO
	game.player.camera.look_at(hinge+Vector3(door.spec.width*.5,1,0))
	await physics_frame;await physics_frame
	expect(game.doors.focused(game.player.camera)==0 and not game.doors.hint(game.player.camera).is_empty(),"Close visible door has a contextual F prompt")
	var ray:=PhysicsRayQueryParameters3D.create(hinge+Vector3(.45,1,-1),hinge+Vector3(.45,1,1),1,[game.player.get_rid()])
	var hit:=state.intersect_ray(ray)
	expect(not hit.is_empty() and hit.collider.has_meta("interactive_door"),"Closed runtime door blocks scanner and cat sight rays")
	game.player.position=hinge+Vector3(.45,-hinge.y,.5)
	expect(not game.doors._clear_between(door,0,door.spec.open_angle),"Door cannot swing into the player")
	game.player.position=outside+Vector3.UP*.05
	var fake:int=(original+1)%game.run.population;var saved:Vector3=game.crowd.positions[fake]
	game.crowd.positions[fake]=hinge+Vector3(.45,-hinge.y,.5)
	expect(not game.doors._clear_between(door,0,door.spec.open_angle),"Door cannot swing into an NPC")
	game.crowd.positions[fake]=saved
	game.run.ap=1000;game.run.purchase("sonar")
	game.player.camera.look_at(hinge+Vector3(.45,1,0));await physics_frame
	var event:=InputEventKey.new();event.keycode=KEY_F;event.pressed=true
	game._input(event)
	expect(door.moving and door.open and game.sonar_left==0,"F operates the focused door without consuming sonar")
	await physics_frame
	game.set_mode("pause");var angle:float=door.angle
	await create_timer(.15,true).timeout;game._input(event)
	expect(door.angle==angle and game.sonar_left==0,"Menus pause door motion and block interaction/sonar")
	game.set_mode("play");await create_timer(.5).timeout
	expect(not door.moving and is_equal_approx(door.angle,door.spec.open_angle),"Door finishes its opening animation after resume")
	hit=state.intersect_ray(ray)
	expect(hit.is_empty(),"Open door clears the same physical line through its doorway")
	game.player.set_physics_process(true)
	expect(await walk_to(game,hinge+Vector3(.45,-hinge.y,.9),4),"Player capsule can physically enter the open cubicle without teleporting")
	game.player.set_physics_process(false)
	game.player.camera.look_at(game.player.camera.global_position+Vector3(0,0,-5))
	game._input(event)
	expect(game.sonar_left==12,"F retains normal sonar behavior away from doors")
	expect(game.run.true_id==original and not game.run.won,"Door operations do not affect original identity or clear state")
	game.start_run(300,912);game.crowd.set_physics_process(false);game.set_physics_process(false);game.player.set_physics_process(false)
	expect(not door.open and door.angle==0,"New run resets dynamic doors without rebaking or rerolling mid-run")

func test_each_door(game:Node3D,state:PhysicsDirectSpaceState3D)->void:
	for door in game.doors.doors:
		game.doors.reset()
		var base:Transform3D=door.base
		game.player.position=base*Vector3(door.spec.width*.5,.05,-1.7)
		game.player.camera.look_at(base*Vector3(door.spec.width*.5,1.1,0))
		await physics_frame;await physics_frame
		var index:int=game.doors.doors.find(door)
		var focus_ok:bool=game.doors.focused(game.player.camera)==index
		var opened:bool=game.doors.interact(game.player.camera)==DoorField.Interaction.STARTED
		await create_timer(.45).timeout
		var ray:=PhysicsRayQueryParameters3D.create(base*Vector3(door.spec.width*.5,1.1,-1),base*Vector3(door.spec.width*.5,1.1,1),1,[game.player.get_rid()])
		expect(focus_ok and opened and not door.moving and state.intersect_ray(ray).is_empty(),"Both curved and straight doorways retain focus, animation and clear openings: "+door.spec.id)
	game.doors.reset()

func walk_to(game:Node3D,goal:Vector3,seconds:float)->bool:
	Input.action_press("forward")
	for tick in ceili(seconds*60):
		var d:Vector3=goal-game.player.position;d.y=0
		if d.length()<.25:Input.action_release("forward");return true
		game.player.rotation.y=atan2(-d.x,-d.z);await physics_frame
	Input.action_release("forward");return false
