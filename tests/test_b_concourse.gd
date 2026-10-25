extends SceneTree
var checks:=0
var failures:=0
func expect(ok:bool,message:String)->void:
 checks+=1
 if not ok:failures+=1;push_error(message)
func _initialize()->void:call_deferred("verify")
func verify()->void:
 var game=load("res://scenes/main.tscn").instantiate();root.add_child(game)
 game.start_run(300,912);game.crowd.set_physics_process(false);game.set_physics_process(false)
 await physics_frame;await physics_frame
 var truth:int=game.run.true_id;var state:PhysicsDirectSpaceState3D=game.get_world_3d().direct_space_state
 var content:Dictionary=game.mall.get_meta("b_concourse",{})
 expect(WorldCache.can_load() and not content.is_empty(),"B public destinations are included in the matching saved world")
 if content.is_empty():game.queue_free();await process_frame;print("B CONCOURSE RESULT: %d checks, %d failures"%[checks,failures]);quit(1);return
 expect(content.station_count==12 and content.stations.size()==12,"B has six ground destinations and three destinations on each upper rear loop")
 expect(content.assigned_people==15 and content.browsers_reassigned==8 and content.lounge_visitors_reassigned==7,"Public visitors reuse eight browsers and seven existing lounge patrons")
 expect(content.shop_browsers_retained==9,"Nine pre-existing browsing visitors remain in B's shops")
 expect(content.population_added==0 and game.run.population==300 and game.mall.identity_slots.size()==267 and game.crowd.roles.count("walking")==33,"Public destinations retain the full identity and moving-agent budget")
 var counts:={0:0,1:0,2:0};var ids:={};var visitors:={};var geometry:=true;var free_approaches:=true
 for station:Dictionary in content.stations:
  counts[station.level]+=1;ids[station.id]=true
  for id:int in station.visitor_ids:visitors[id]=station.id
  var y:=Mall.floor_height(station.level)
  for footprint:Rect2 in station.footprints:
   var at:=Vector3(footprint.get_center().x,y,footprint.get_center().y)
   if Mall.plan_walkable(at):geometry=false;push_error("Facility not excluded from navigation: "+station.id)
   var hit:=state.intersect_ray(PhysicsRayQueryParameters3D.create(at+Vector3.UP*3.5,at+Vector3.UP*.04,1))
   if hit.is_empty():geometry=false;push_error("Missing real fixture collision: "+station.id)
  var approach:=Vector3(station.at.x,y,station.at.y-3.1)
  if not Mall.walkable(approach):free_approaches=false;push_error("No public front approach: "+station.id)
 expect(counts=={0:6,1:3,2:3} and ids.size()==12,"All destinations have stable distinct IDs and the intended floor distribution")
 expect(visitors.size()==15,"Every reassigned person belongs to exactly one public destination")
 expect(geometry,"The same published fixture footprints correspond to real collisions and AI exclusions")
 expect(free_approaches,"Every public destination keeps a usable front approach on its own floor")
 var accessible:=true;var furniture:=true;var preserved:=true
 for record:Dictionary in content.visitors:
  var id:int=record.id;var at:Vector3=game.crowd.positions[id]
  if at.distance_to(record.position)>.001 or at.z<=-80 or id in range(241,259):preserved=false
  if CatSearch.route(game.crowd,Mall.hub_position("B館東入口"),id,state).is_empty():accessible=false;push_error("No cat approach to B public visitor "+str(id))
  if record.role in ["seated","reading"]:
   var chair:=state.intersect_ray(PhysicsRayQueryParameters3D.create(at+Vector3.UP*.52,at+Vector3.UP*.1,1))
   # Seat colliders can contain the upper endpoint; query from above their back.
   if chair.is_empty():chair=state.intersect_ray(PhysicsRayQueryParameters3D.create(at+Vector3.UP*1.05,at+Vector3.UP*.1,1))
   if chair.is_empty():furniture=false;push_error("Public seated visitor has no physical chair: "+str(id))
 expect(preserved,"Public assignments retain their source IDs and leave C / cinema identity ranges alone")
 expect(accessible,"All fifteen public visitors have a shared-graph cat route and unobstructed final scan approach")
 expect(furniture,"All seven reassigned seated/readers have actual physical seats")
 var b_browsers:=0;var cinema:=0;var cafe:=0;var c_ground:=0;var c_upper:=0
 for id in game.mall.identity_slots.size():
  var p:Vector3=game.crowd.positions[id]
  if p.x< -190 and p.z> -80 and game.crowd.roles[id]=="browsing" and not visitors.has(id):b_browsers+=1
  if game.crowd.activities[id]=="cinema" and game.crowd.roles[id]=="seated":cinema+=1
  if p.x< -190 and p.z> -80 and game.crowd.activities[id]=="cafe" and game.crowd.roles[id]=="seated":cafe+=1
  if CWing.contains(p):
   if Mall.level_at(p.y)==0:c_ground+=1
   if Mall.level_at(p.y)==1:c_upper+=1
 expect(b_browsers==9 and cinema==18 and cafe==6,"Shop browsing, cinema seating and cafe occupancy remain present")
 expect(c_ground==30 and c_upper==9,"C1's thirty and C2's nine fixed visitors are preserved")
 # Former long blank walls now have destinations reached along the actual rear lane.
 for level in [0,1,2]:
  var y:=Mall.floor_height(level)
  game.player.position=Vector3(-560,y+.05,61);game.player.velocity=Vector3.ZERO
  expect(await follow_nav(game,Vector3(-552,y,58.9),12),"Player walks the rear concourse to its western public destination on floor "+str(level+1))
 game.player.position=Vector3(-433,.05,19);game.player.velocity=Vector3.ZERO
 expect(await follow_nav(game,Vector3(-417,0,18.5),12),"Player approaches the central event stalls around their real collisions")
 for level in [1,2]:
  var at:=Vector3(-414,Mall.floor_height(level),26)
  expect(state.intersect_ray(PhysicsRayQueryParameters3D.create(at+Vector3.UP*.1,at-Vector3.UP*.2,1)).is_empty(),"The public fit-out preserves the upper central atrium opening")
 # The information terminals are usable by the player, not only visual props.
 for level in [0,1]:
  var at:=Vector3(-219.5,0,8.0) if level==0 else Vector3(-624,Mall.floor_height(1),-20)
  game.set_mode("play");game.player.position=at+Vector3(0,.05,-2.7 if level==0 else 2.0);game.player.velocity=Vector3.ZERO
  game.player.camera.look_at(at+Vector3.UP*1.5)
  var hit:=state.intersect_ray(PhysicsRayQueryParameters3D.create(game.player.camera.global_position,at+Vector3.UP*1.5,1))
  expect(not hit.is_empty() and hit.collider.get_meta("mall_guide",false),"The reachable information terminal has its real interaction collider on floor "+str(level+1))
  var ap:int=game.run.ap;var seen:Dictionary=game.run.visited.duplicate();var position:Vector3=game.player.position
  var key:=InputEventKey.new();key.keycode=KEY_F;key.pressed=true;game._input(key)
  expect(game.hud.mode=="map" and game.hud.map_level==level,"F opens the current-floor guide from the physical terminal")
  expect(game.run.ap==ap and game.run.visited==seen and game.run.true_id==truth and game.player.position==position,"Reading the guide neither spends AP nor unlocks travel, moves the player or retargets the original")
  game.set_mode("play")
 var result_seed:=-1
 for seed_value in 2000:
  if IdentityRun.new(300,seed_value).true_id in visitors:result_seed=seed_value;break
 expect(result_seed>=0,"A public-area visitor can naturally be the original without rerolling its location")
 expect(game.run.true_id==truth and not game.run.won and game.run.cleared==0,"Exploring public destinations preserves the original and all unresolved NPCs")
 game.queue_free();await process_frame
 print("B CONCOURSE RESULT: %d checks, %d failures"%[checks,failures]);quit(1 if failures else 0)
func follow_nav(game:Node3D,target:Vector3,seconds:float)->bool:
 var nav:AStar3D=game.crowd.nav
 var path:=nav.get_point_path(nav.get_closest_point(game.player.position),nav.get_closest_point(target))
 if path.is_empty():return false
 var index:=0;Input.action_press("sprint");Input.action_press("forward")
 for frame in ceili(seconds*60):
  if index>=path.size():break
  var d:Vector3=path[index]-game.player.position;d.y=0
  if d.length()<.42:index+=1;continue
  game.player.rotation.y=atan2(-d.x,-d.z);await physics_frame
 Input.action_release("forward");Input.action_release("sprint");await physics_frame
 if index<path.size():push_error("B public route stopped at %s; next %s; wanted %s"%[game.player.position,path[index],target])
 return index>=path.size()
