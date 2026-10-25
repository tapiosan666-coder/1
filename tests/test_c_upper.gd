extends SceneTree
var checks:=0
var failures:=0
func expect(ok:bool,message:String)->void:
 checks+=1
 if not ok:failures+=1;push_error(message)
func _initialize()->void:call_deferred("verify")
func verify()->void:
 var game=load("res://scenes/main.tscn").instantiate();root.add_child(game)
 game.start_run(300,912);game.crowd.set_physics_process(false)
 await physics_frame;await physics_frame
 var truth:int=game.run.true_id;var state:PhysicsDirectSpaceState3D=game.get_world_3d().direct_space_state;var y:=Mall.floor_height(1)
 expect(WorldCache.can_load(),"New C floor uses a saved world matching all geometry and navigation inputs")
 expect(MallLayout.floor_data("C",1).implemented and not MallLayout.floor_data("C",2).implemented,"C/2F is implemented while C/3F remains explicitly unbuilt")
 expect(game.run.population==300 and game.mall.identity_slots.size()==267 and game.crowd.roles.count("walking")==33,"New tenants reuse fixed identities without increasing the simulation budget")
 for at:Vector2 in CUpper.supports():
  var a:=Vector3(at.x-1,1.5,at.y);var b:=Vector3(at.x+1,1.5,at.y)
  expect(not Mall.plan_walkable(Vector3(at.x,0,at.y)) and not state.intersect_ray(PhysicsRayQueryParameters3D.create(a,b,1)).is_empty(),"C ground support column agrees with its navigation obstacle: "+str(at))
 var ids:Array[int]=[];var staff:=0;var seated:=0
 for id in game.mall.identity_slots.size():
  if MallLayout.floor_at(game.crowd.positions[id])=="C/2F":
   ids.append(id)
   if game.crowd.roles[id]=="staff":staff+=1
   if game.crowd.roles[id]=="seated":seated+=1
 expect(ids.size()==9 and staff==3 and seated==2,"Three upper tenants have nine assigned staff/shoppers/cafe visitors before visiting")
 for at in [Vector3(-442,y,-58),Vector3(-442,y,-65),Vector3(-442,y,-90),Vector3(-432,y,-117),Vector3(-448,y,-126),Vector3(-355,y,-94)]:
  expect(Mall.walkable(at) and MallLayout.floor_at(at)=="C/2F","Bridge/gallery point agrees with floor ownership and navigation: "+str(at))
  var hit:=state.intersect_ray(PhysicsRayQueryParameters3D.create(at+Vector3.UP*.15,at-Vector3.UP*.2,1))
  expect(not hit.is_empty() and absf(hit.position.y-y)<.03,"Bridge/gallery has a real physical floor: "+str(at))
 for at in [Vector3(-432,y,-134),Vector3(-370,y,-102)]:
  expect(not MallStructure.contains("C",1,Vector2(at.x,at.z)),"C upper court centre remains an actual hole in the floor definition")
  expect(state.intersect_ray(PhysicsRayQueryParameters3D.create(at+Vector3.UP*.1,at-Vector3.UP*.15,1)).is_empty(),"C upper court centre has no invisible collision slab")
 expect(not state.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(-382,y+.65,-89),Vector3(-380,y+.65,-89),1)).is_empty(),"Upper floor retains a guardrail over the stair bottom instead of exposing a five-metre drop")
 for i in CUpper.SHOPS.size():
  var shop:Dictionary=CUpper.SHOPS[i];var basis:=Basis(Vector3.UP,shop.yaw)
  var outside:Vector3=shop.at+basis*Vector3(0,1.65,3);var inside:Vector3=shop.at+basis*Vector3(0,1.65,-3)
  expect(state.intersect_ray(PhysicsRayQueryParameters3D.create(outside,inside,1)).is_empty(),"Upper shop doorway is physically open: "+str(shop.name))
  var stocked:=false;var signed:=false
  for u:Dictionary in game.mall.get_meta("stocking_plan",[]):
   if u.id=="c_1_%d"%i:stocked=true
  for spec:Dictionary in StoreSigns.specifications():
   if spec.id=="c_1_%d"%i and StoreSignCatalog.DATA.aliases.has(spec.text):signed=true
  expect(stocked and signed,"Upper tenant has stocked shelves and a designed brand sign: "+str(shop.name))
 var source:=Mall.hub_position("B館2階ラウンジ");var reachable:=true
 for id in ids:
  if CatSearch.route(game.crowd,source,id,state).is_empty():reachable=false;push_error("Upper tenant has no cat approach: "+str(id))
 expect(reachable,"Cats reach all nine upper visitors through the shared bridge/stair graph")
 game.player.position=Vector3(-442,y+.05,-18);game.player.velocity=Vector3.ZERO
 expect(await follow_nav(game,Vector3(-432,y,-117),30),"Player physically crosses B/2F to C/2F without warping or jumping")
 game.player.position=Vector3(-384,.05,-94);game.player.velocity=Vector3.ZERO
 expect(await follow_nav(game,Vector3(-355,y,-94),20) and absf(game.player.position.y-y)<.15,"Player walks up the normal C stairs from 1F to 2F")
 expect(await follow_nav(game,Vector3(-384,0,-94),20) and absf(game.player.position.y)<.15,"Player walks down the same C stairs without falling through the shaft")
 game.run.ap=1000;game.run.purchase("travel");game.run.visited.erase("C館2階テラス");game.set_mode("map");game.hud.set_map_floor(1)
 var before:Vector3=game.player.position
 expect(not game.fast_travel("c.terrace.2") and before==game.player.position,"Selecting C/2F on the map cannot unlock unvisited travel")
 game.set_mode("play");game.player.position=Mall.hub_position("C館2階テラス");game._visit_points(false);game.set_mode("map")
 expect(game.fast_travel("c.terrace.2") and MallLayout.floor_at(game.player.position)=="C/2F","A real upper terrace visit unlocks its own second-floor travel point")
 var upper_loot:=false;var legal:=true
 for seed_value in 128:
  var loot:=RunLoot.new(game.mall.spawn_points,seed_value)
  for chest:Dictionary in loot.chests:
   if not Mall.walkable(chest.pos):legal=false
   if MallLayout.floor_at(chest.pos)=="C/2F":upper_loot=true
 expect(legal and upper_loot,"Ten-chest random placements include reachable C/2F floor samples across 128 seeds")
 expect(game.run.true_id==truth and not game.run.won,"Upper exploration and travel preserve the original selected identity")
 var seed_value:=-1
 for candidate in 2000:
  if IdentityRun.new(300,candidate).true_id in ids:seed_value=candidate;break
 expect(seed_value>=0,"An upper visitor can naturally be the uniformly selected original")
 if seed_value>=0:
  game.start_run(300,seed_value);game.crowd.set_physics_process(false);await physics_frame;await physics_frame
  var original:int=game.run.true_id
  game.resolve(original,IdentityRun.Source.SPECIAL)
  expect(game.run.located and not game.run.won and game.run.cleared==0,"Special scanning an upper original only reports the position")
  var head:Vector3=game.crowd.positions[original]+Vector3.UP*(1.2 if game.crowd.roles[original]=="seated" else 1.7);var found:=false
  for point:Vector3 in game.mall.spawn_points:
   if absf(point.y-y)>.1 or point.distance_to(game.crowd.positions[original])>5:continue
   game.player.position=point+Vector3.UP*.05;game.player.velocity=Vector3.ZERO;game.player.camera.look_at(head)
   var hit:Dictionary=game.ray_target()
   if not hit.is_empty() and hit.collider.get_meta("identity",-1)==original:found=true;break
  expect(found,"The initial handheld ray reaches the upper original from an accessible aisle")
  if found:
   Input.action_press("fire");await create_timer(2.2).timeout;Input.action_release("fire")
   expect(game.run.won and game.run.true_id==original and game.run.cleared==0,"Only a completed initial handheld scan wins; all other 299 identities remain")
 game.queue_free();await process_frame
 print("C UPPER RESULT: %d checks, %d failures"%[checks,failures]);quit(1 if failures else 0)
func follow_nav(game:Node3D,target:Vector3,seconds:float)->bool:
 var nav:AStar3D=game.crowd.nav;var path:=nav.get_point_path(nav.get_closest_point(game.player.position),nav.get_closest_point(target));var index:=0
 if path.is_empty():return false
 Input.action_press("sprint");Input.action_press("forward")
 for frame in ceili(seconds*60):
  if index>=path.size():break
  var d:Vector3=path[index]-game.player.position;d.y=0
  if d.length()<.42:index+=1;continue
  game.player.rotation.y=atan2(-d.x,-d.z);await physics_frame
 Input.action_release("forward");Input.action_release("sprint");await physics_frame
 if index<path.size():push_error("Upper route stopped at %s; next %s; target %s"%[game.player.position,path[index],target])
 return index>=path.size()
