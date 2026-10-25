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
 expect(WorldCache.can_load(),"Structural map uses a matching saved world")
 expect(game.run.population==300 and game.mall.identity_slots.size()==267,"All 300 identities, including 267 stationary slots, survive the layout change")
 expect(truth==IdentityRun.new(300,912).true_id,"Geometry never rerolls or moves the randomly chosen true ID")
 var origin:int=game.crowd.nav.get_closest_point(Mall.hub_position("中央入口"));var seen:Dictionary={origin:true};var pending:Array[int]=[origin];var cursor:=0
 while cursor<pending.size():
  var id:int=pending[cursor];cursor+=1
  for next in game.crowd.nav.get_point_connections(id):
   if not seen.has(next):seen[next]=true;pending.append(next)
 expect(seen.size()==game.crowd.nav.get_point_count(),"Every navigation point connects to the original entrance")
 for level in [0,1,2]:
  var y:=Mall.floor_height(level)
  for at in [Vector2(-430,-20),Vector2(-325,22),Vector2(-218,-20),Vector2(-400,80),Vector2(-282,95)]:
   var p:=Vector3(at.x,y,at.y)
   var hit:=state.intersect_ray(PhysicsRayQueryParameters3D.create(p+Vector3.UP*.12,p-Vector3.UP*.12,1))
   expect(not hit.is_empty(),"B physical gallery/loop floor %d at %s"%[level,at])
  for at in [Vector2(-430,0),Vector2(-325,43),Vector2(-218,0)]:
   var p:=Vector3(at.x,y,at.y)
   var hit:=state.intersect_ray(PhysicsRayQueryParameters3D.create(p+Vector3.UP*.10,p-Vector3.UP*.15,1))
   expect(hit.is_empty() if level>0 else not hit.is_empty(),"Three B courts have solid 1F and open 2F/3F centres: %d %s"%[level,at])
  var north:=MallCurve.world(Vector3(-39,y,-38))
  var hole:=state.intersect_ray(PhysicsRayQueryParameters3D.create(north+Vector3.UP*.1,north-Vector3.UP*.15,1))
  expect(hole.is_empty() if level>0 else not hole.is_empty(),"A north court opens through three levels")
  var destination:=MallCurve.world(Vector3(6,y,-40))
  expect(Mall.walkable(destination),"A new gallery is public on floor %d"%level)
  var start:int=game.crowd.nav.get_closest_point(MallCurve.world(Vector3(-82,0,0)))
  var goal:int=game.crowd.nav.get_closest_point(destination)
  expect(not game.crowd.nav.get_point_path(start,goal).is_empty(),"A new upper gallery connects to the original entrance")
  for base:Dictionary in BWing.STORES:
   var t:=BWing.store_transform(base)
   var a:Vector3=t*Vector3(base.x,y+1.65,base.side*7.5)
   var b:Vector3=t*Vector3(base.x,y+1.65,base.side*10.0)
   expect(state.intersect_ray(PhysicsRayQueryParameters3D.create(a,b,1)).is_empty(),"B relocated storefront entrance is physically open %d %s"%[level,base.x])
 for at in [Vector3(-370,0,-94),Vector3(-432,0,-120),Vector3(-320,0,-150),Vector3(-400,0,-189)]:
  expect(Mall.walkable(at),"C courts and return street have public floors at %s"%at)
  var path:PackedVector3Array=game.crowd.nav.get_point_path(game.crowd.nav.get_closest_point(Mall.hub_position("中央入口")),game.crowd.nav.get_closest_point(at))
  expect(not path.is_empty(),"C street connects to A's entrance")
 expect(Mall.escalator_carry(Vector3(-311.5,2.7625,43)).z>.8,"B time-court upward escalator follows its new position")
 expect(Mall.escalator_carry(Vector3(-308.5,8.2,43)).z<-.8,"B paired downward escalator moves in the opposite direction")
 expect(Mall.escalator_carry(Vector3(-241.5,0,9))==Vector3.ZERO,"No conveyor motion remains at the former B escalator")
 # Access all fixed identities through the same path and sight queries used by cats.
 var accessible:=true
 for id in game.mall.identity_slots.size():
  if CatSearch.route(game.crowd,Mall.hub_position("中央入口"),id,state).is_empty():
   accessible=false;push_error("No cat approach to identity %d at %s"%[id,game.crowd.positions[id]])
 expect(accessible,"Cats can approach every stationary identity after all three buildings change")
 var chest_access:=true
 for seed_value in range(32):
  var loot:=RunLoot.new(game.mall.spawn_points,seed_value)
  for chest:Dictionary in loot.chests:
   if not Mall.walkable(chest.pos) or MallLayout.floor_at(chest.pos).is_empty():chest_access=false
 expect(chest_access,"Treasure samples stay on reachable public floors across 32 seeds")
 for hub:Dictionary in MallLayout.travel_points():
  expect(Mall.walkable(hub.position),"Travel landing is walkable: "+hub.id)
  var p:Vector3=hub.position
  expect(state.intersect_ray(PhysicsRayQueryParameters3D.create(p+Vector3.UP*.2,p-Vector3.UP*.3,1)).size()>0,"Travel landing has a physical floor: "+hub.id)
 # Follow real collision, including curved A coordinates, rather than accepting a map-only connection.
 if "--routes-only" in OS.get_cmdline_user_args() or failures==0:
  game.player.position=MallCurve.world(Vector3(-39,.05,-10));game.player.velocity=Vector3.ZERO
  expect(await follow_nav(game,MallCurve.world(Vector3(6,0,-40)),25),"Player can walk from A's original concourse into the north gallery")
  expect(await follow_nav(game,MallCurve.world(Vector3(69,0,-7)),25),"Player returns through the east branch, completing A's new loop")
  for level in [1,2]:
   game.player.position=MallCurve.world(Vector3(-39,Mall.floor_height(level)+.05,-6));game.player.velocity=Vector3.ZERO
   expect(await follow_nav(game,MallCurve.world(Vector3(6,Mall.floor_height(level),-40)),25),"Player enters A's new north gallery on floor %d"%level)
   expect(await follow_nav(game,MallCurve.world(Vector3(69,Mall.floor_height(level),-6)),30),"Player returns through A's east gallery on floor %d"%level)
  game.player.position=Vector3(-194,.05,-5);game.player.velocity=Vector3.ZERO
  expect(await follow_nav(game,Vector3(-282,0,95),45),"Player reaches B's island shops along the new public circulation")
  expect(await follow_nav(game,Vector3(-432,0,-120),65),"Player walks through B to the redesigned C garden court")
 expect(game.run.true_id==truth and not game.run.won and game.run.cleared==0,"Walking all new structures preserves the true identity and unresolved NPCs")
 game.queue_free();await process_frame
 print("MALL STRUCTURE RESULT: %d checks, %d failures"%[checks,failures]);quit(1 if failures else 0)
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
