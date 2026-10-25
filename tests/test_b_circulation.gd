extends SceneTree
var checks:=0
var failures:=0
func expect(ok:bool,message:String)->void:
 checks+=1
 if not ok:failures+=1;push_error(message)
func _initialize()->void:call_deferred("verify")
func verify()->void:
 var game=load("res://scenes/main.tscn").instantiate();root.add_child(game)
 game.start_run(1000,912);game.crowd.set_physics_process(false);game.set_physics_process(false)
 await physics_frame;await physics_frame
 var truth:int=game.run.true_id;var state:PhysicsDirectSpaceState3D=game.get_world_3d().direct_space_state
 expect(WorldCache.can_load(),"Rear tenants and paired escalators use a matching saved world")
 expect(game.run.population==1000 and game.crowd.slots.size()==900 and game.crowd.roles.count("walking")==100,"The existing thousand-person population budget is preserved")
 expect(game.mall.get_meta("b_rear_retail",{}).get("shop_count",0)==12,"All twelve rear-loop tenants are saved, rather than generated only for screenshots")
 var new_staff:Dictionary={};var stocked:Dictionary={};var designed:Dictionary={}
 for id in range(267,900):
  var slot:Dictionary=game.crowd.slots[id]
  if slot.has("tenant"):new_staff[slot.tenant]=id
 for plan:Dictionary in game.mall.get_meta("stocking_plan",[]):stocked[plan.id]=true
 for sign:Dictionary in StoreSigns.specifications():
  var outlet:String=sign.get("outlet",sign.id)
  if not outlet.is_empty():designed[outlet]=StoreSignCatalog.DATA.aliases.has(sign.text)
 expect(new_staff.size()==12,"Each new tenant has a real separately scannable clerk within the thousand-person budget")
 for level in [0,1,2]:
  var kinds:Dictionary={}
  for store:Dictionary in BRearRetail.stores(level):
   kinds[store.kind]=true
   var p:Vector3=store.t*Vector3(3,0,-20)
   expect(Mall.walkable(p) and MallLayout.floor_at(p)=="B/"+["1F","2F","3F"][level],"Rear tenant's public floor matches navigation and declared floor: "+store.id)
   var floor_hit:=state.intersect_ray(PhysicsRayQueryParameters3D.create(p+Vector3.UP*.15,p-Vector3.UP*.2,1))
   expect(not floor_hit.is_empty() and absf(floor_hit.position.y-p.y)<.03,"Rear tenant has a physical floor at its clerk: "+store.id)
   var a:Vector3=store.t*Vector3(0,1.65,-6);var b:Vector3=store.t*Vector3(0,1.65,-10)
   expect(state.intersect_ray(PhysicsRayQueryParameters3D.create(a,b,1)).is_empty(),"The rear storefront opens through the former exterior wall: "+store.id)
   expect(stocked.has(store.id) and designed.get(store.id,false),"The new shop has both dense stock and a designed brand sign: "+store.id)
   var id:int=new_staff.get(store.id,-1)
   expect(id>=267 and game.crowd.roles[id]=="staff" and not CatSearch.route(game.crowd,Mall.ENTRANCE,id,state).is_empty(),"Cats can reach the separately managed new clerk: "+store.id)
   game.player.position=store.t*Vector3(0,.05,-6);game.player.velocity=Vector3.ZERO
   expect(await follow_nav(game,store.t*Vector3(0,0,-15.8),10),"Walk from the rear concourse into the furnished shop: "+store.id)
   var inside:Vector3=store.t.affine_inverse()*game.player.position
   expect(inside.z< -10 and absf(inside.y)<.2,"Entering the new shop reaches its actual interior: "+store.id)
   expect(await follow_nav(game,store.t*Vector3(0,0,-6),10),"Leave the stocked shop through its public doorway: "+store.id)
  expect(kinds.size()==4,"The new floor has four distinct tenant categories: "+str(level+1))
 expect(stocked.size()==101 and designed.size()==101,"All 101 outlets share consistent merchandise and branding coverage")
 var one_way:PackedInt32Array=WorldCache.navigation.get("one_way",PackedInt32Array());var directions:=true;var up:=0;var down:=0
 for index in range(0,one_way.size(),2):
  var a:int=one_way[index];var b:int=one_way[index+1]
  if not game.crowd.nav.are_points_connected(a,b,false) or game.crowd.nav.are_points_connected(b,a,false):directions=false
  var rise:float=game.crowd.nav.get_point_position(b).y-game.crowd.nav.get_point_position(a).y
  if rise>0:up+=1
  elif rise<0:down+=1
 expect(one_way.size()==520 and up==130 and down==130 and directions,"All 260 directed escalator edges retain their up/down direction after cache restoration")
 expect(BWing.escalators().size()==12 and MallStructureData.DATA.B.escalator_banks.size()==3,"Three atrium banks each have paired up/down flights for both floor connections")
 for bank:Dictionary in MallStructureData.DATA.B.escalator_banks:
  for lower in [0,1]:
   var y:=Mall.floor_height(lower);var mid:float=(y+Mall.floor_height(lower+1))*.5
   for lane in [0,1]:
    var x:float=bank.at[0]+bank.side*[13.5,16.5][lane]
    var carry:=Mall.escalator_carry(Vector3(x,mid,bank.at[1]))
    expect(carry.z>.8 if lane==0 else carry.z<-.8,"Physical conveyor agrees with its paired direction: %s %d/%d"%[bank.id,lower,lane])
    var start:=Vector3(x,y+.05,bank.at[1]-7.5);var target:=Vector3(x,Mall.floor_height(lower+1),bank.at[1]+7.5)
    if lane==1:
     var swap:=start;start=target+Vector3.UP*.05;target=swap-Vector3.UP*.05
    expect(Mall.walkable(start) and Mall.walkable(target),"Both escalator landings are on the public circulation floor")
    var path:PackedVector3Array=game.crowd.nav.get_point_path(game.crowd.nav.get_closest_point(start),game.crowd.nav.get_closest_point(target));var ramp_seen:=false
    for point:Vector3 in path:
     if point.y>y+.1 and point.y<Mall.floor_height(lower+1)-.1 and absf(point.x-x)<.1:ramp_seen=true
    expect(ramp_seen,"NPC route uses the correct nearby up/down flight")
    game.player.position=start;game.player.velocity=Vector3.ZERO;await physics_frame;await physics_frame
    expect(await walk_to(game,target,6) and absf(game.player.position.y-target.y)<.2,"Walk the full paired escalator without jumping: %s %d/%d"%[bank.id,lower,lane])
  var upper_y:=Mall.floor_height(2)
  for lane in [0,1]:
   var x:float=bank.at[0]+bank.side*[13.5,16.5][lane]
   var guard:=state.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(x,upper_y+.6,bank.at[1]-7),Vector3(x,upper_y+.6,bank.at[1]-5),1))
   expect(not guard.is_empty(),"Top floor guards the unused north end of the shaft: "+str(bank.id))
 expect(Mall.escalator_carry(Vector3(-331,2.7625,60))==Vector3.ZERO and Mall.escalator_carry(Vector3(-316.5,8.2,60))==Vector3.ZERO,"No conveyor remains in the old remote B court")
 var new_chest:=false;var legal:=true
 for seed_value in 128:
  var loot:=RunLoot.new(game.mall.spawn_points,seed_value)
  for chest:Dictionary in loot.chests:
   if not Mall.walkable(chest.pos):legal=false
   for level in [0,1,2]:
    for store:Dictionary in BRearRetail.stores(level):
     var p:Vector3=store.t.affine_inverse()*chest.pos
     if absf(p.y)<.1 and absf(p.x)<8.5 and p.z< -8.5 and p.z> -23.5:new_chest=true
 expect(legal and new_chest,"Random treasure includes the reachable new interiors without placing it inside shelves")
 expect(game.run.true_id==truth and not game.run.won and game.run.cleared==0,"All physical exploration preserves the selected original and unresolved NPCs")
 var selected_seed:=-1
 for value in 2000:
  if IdentityRun.new(1000,value).true_id in new_staff.values():selected_seed=value;break
 expect(selected_seed>=0,"A new rear-shop clerk can naturally be chosen as the original")
 if selected_seed>=0:
  game.start_run(1000,selected_seed);game.crowd.set_physics_process(false);await physics_frame;await physics_frame
  var original:int=game.run.true_id;game.resolve(original,IdentityRun.Source.SPECIAL)
  expect(game.run.located and not game.run.won,"Special scanning a new clerk only reports the location")
  var head:Vector3=game.crowd.positions[original]+Vector3.UP*1.7;var found:=false
  for point:Vector3 in game.mall.spawn_points:
   if absf(point.y-game.crowd.positions[original].y)>.1 or point.distance_to(game.crowd.positions[original])>5:continue
   game.player.position=point+Vector3.UP*.05;game.player.velocity=Vector3.ZERO;game.player.camera.look_at(head)
   var hit:Dictionary=game.ray_target()
   if not hit.is_empty() and hit.collider.get_meta("identity",-1)==original:found=true;break
  expect(found,"The initial scanner can target the new original through its store aisle")
  if found:
   game.set_physics_process(true);Input.action_press("fire");await create_timer(2.2).timeout;Input.action_release("fire")
   expect(game.run.won and game.run.cleared==0 and game.run.true_id==original,"Only the initial scan clears the game; all other 999 identities remain")
 game.queue_free();await process_frame
 print("B CIRCULATION RESULT: %d checks, %d failures"%[checks,failures]);quit(1 if failures else 0)
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
 if index<path.size():push_error("Rear route stuck at %s; next %s; destination %s"%[game.player.position,path[index],target])
 return index>=path.size()
func walk_to(game:Node3D,target:Vector3,seconds:float)->bool:
 Input.action_press("forward");Input.action_press("sprint")
 for frame in ceili(seconds*60):
  var d:Vector3=target-game.player.position;d.y=0
  if d.length()<.22:Input.action_release("forward");Input.action_release("sprint");await physics_frame;return true
  game.player.rotation.y=atan2(-d.x,-d.z);await physics_frame
 Input.action_release("forward");Input.action_release("sprint");return false
