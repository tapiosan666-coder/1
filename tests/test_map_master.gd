extends SceneTree
## Physical acceptance of the B 1–3F structure. Uses actual player input/colliders.
var checks:=0
var failures:=0
var routes:Array=[]
func expect(ok:bool,message:String)->void:
 checks+=1
 if not ok:failures+=1;push_error(message)
func _initialize()->void:call_deferred("verify")
func verify()->void:
 var game=load("res://scenes/main.tscn").instantiate();root.add_child(game);game.start_run(1000,912)
 game.set_physics_process(false);game.crowd.set_physics_process(false)
 await physics_frame;await physics_frame
 var space:PhysicsDirectSpaceState3D=game.get_world_3d().direct_space_state
 expect(WorldCache.can_load(),"The shipped game loads the matching B structure cache")
 expect(game.run.population==1000 and game.crowd.slots.size()==900,"No NPCs or skills were added to the existing population")
 var original:int=game.run.true_id
 var extent:=MallStructure.bounds("B",0)
 expect(extent.position.x<=-690 and extent.end.x>=-190,"B's architectural body spans at least 500 physical metres")
 var ids:={}
 for u:Dictionary in RetailDensity.units():
  if u.building=="B":ids[u.id]=true
 expect(ids.size()==39,"Only the thirty-nine existing fitted B outlets are counted")
 for level in [0,1,2]:
  var y:=Mall.floor_height(level)
  var crossing_a:=Vector3(-379,y+1.0,-43);var crossing_b:=Vector3(-361,y+1.0,-43)
  expect(space.intersect_ray(PhysicsRayQueryParameters3D.create(crossing_a,crossing_b,1)).is_empty(),"North loop remains open across both sides of the historical C walkway: %dF"%(level+1))
  for plaza:Dictionary in MallStructureData.DATA.B.plazas:
   var centre:=Vector3(plaza.at[0],y,plaza.at[1])
   var ray:=PhysicsRayQueryParameters3D.create(centre+Vector3.UP*.1,centre-Vector3.UP*.2,1)
   expect(space.intersect_ray(ray).is_empty() if level>0 else not space.intersect_ray(ray).is_empty(),"Real floor/void at %s / %dF"%[plaza.id,level+1])
   if level==0:
    # Centre is away from the event stalls and the perimeter escalator shafts.
    var eye:=centre+Vector3(0,1.68,-8)
    expect(space.intersect_ray(PhysicsRayQueryParameters3D.create(eye,eye+Vector3.UP*14,1)).is_empty(),"Unbroken upward sightline through both upper floors: "+str(plaza.id))
  # Force intermediate waypoints on each alternative: an endpoint-only shortest
  # path could silently use the main spine and never test the northern route.
  for route_spec:Array in [["north",[[-624,-18],[-570,-43],[-490,-46],[-414,-43],[-305,-44],[-245,-30],[-218,-20]]],["south",[[-624,20],[-618,35],[-555,61],[-470,72],[-414,73.5],[-320,65],[-242,38],[-218,20]]]]:
   var points:Array=route_spec[1];game.player.position=Vector3(points[0][0],y+.05,points[0][1]);game.player.velocity=Vector3.ZERO;await physics_frame
   var complete:=true
   for i in range(1,points.size()):
    var goal:=Vector3(points[i][0],y,points[i][1])
    complete=await follow_nav(game,goal,60,"B%dF/%s/%d"%[level+1,route_spec[0],i]) and complete
   expect(complete,"Walk the entire alternative loop: B%dF/%s"%[level+1,route_spec[0]])
  for base:Dictionary in BWing.STORES:
   var t:=BWing.store_transform(base)
   var a:=t*Vector3(base.x,y,base.side*6)
   var b:=t*Vector3(base.x,y,base.side*11)
   game.player.position=a+Vector3.UP*.05;game.player.velocity=Vector3.ZERO;await physics_frame
   expect(await follow_nav(game,b,8,"tenant/%d/%s/%s"%[level,base.x,base.side]),"Actually enter the fitted main tenant on floor %d: %s/%s"%[level+1,base.x,base.side])
   expect(await follow_nav(game,a,8,"tenant-exit/%d/%s/%s"%[level,base.x,base.side]),"Actually leave the tenant through its entrance")
  var anchor:=BWing.anchor_transform();var outside:=anchor*Vector3(-370,y,0);var inside:=anchor*Vector3(-378,y,0)
  game.player.position=outside+Vector3.UP*.05;game.player.velocity=Vector3.ZERO;await physics_frame
  expect(await follow_nav(game,inside,8,"anchor-enter/%d"%level),"Enter the west anchor's actual doorway on floor "+str(level+1))
  expect(await follow_nav(game,outside,8,"anchor-exit/%d"%level),"Leave the west anchor through the same doorway")
 # The all-bank test separately verifies all twelve B and eight unchanged A flights.
 # Here continue from each B arrival all the way onto its public concourse.
 for bank:Dictionary in MallStructureData.DATA.B.escalator_banks:
  for level in [1,2]:
   var y:=Mall.floor_height(level);var x:float=bank.at[0]+bank.side*13.5
   game.player.position=Vector3(x,y+.05,bank.at[1]+7.5);game.player.velocity=Vector3.ZERO;await physics_frame
   var goal:=Vector3(bank.at[0],y,bank.at[1]+20)
   expect(await follow_nav(game,goal,14,"landing/%s/%d"%[bank.id,level+1]),"Leave the actual upper landing for the atrium promenade")
 for pair:Array in [["A/B 2F",Mall.hub_position("2階アトリウム"),Mall.hub_position("B館2階ラウンジ")],["B/C 2F",Vector3(-442,Mall.floor_height(1),-35),Mall.hub_position("C館2階テラス")],["B/C 1F",Vector3(-366,0,19),Mall.hub_position("C館屋外広場")]]:
  game.player.position=pair[1]+Vector3.UP*.05;game.player.velocity=Vector3.ZERO;await physics_frame
  expect(await follow_nav(game,pair[2],75,pair[0]),"Physical inter-building crossing: "+str(pair[0]))
 # A existing 5 floors, B 3, C 2 remain the declared ten implemented floors.
 var count:=0
 for f:Dictionary in MallLayout.catalog():
  if f.implemented:count+=1
 expect(count==10,"Five missing floors are not reported as implemented")
 for hub:Dictionary in MallLayout.travel_points():
  expect(Mall.walkable(hub.position),"Existing travel landing remains walkable: "+hub.id)
 var reachable:=true
 for id in game.crowd.slots.size():
  if MallLayout.floor_at(game.crowd.positions[id]).begins_with("B/") and CatSearch.route(game.crowd,Mall.hub_position("B館東入口"),id,space).is_empty():
   reachable=false;push_error("No cat scan approach to B identity %d at %s"%[id,game.crowd.positions[id]])
 expect(reachable,"Every fixed B NPC is approachable with the existing cat scan range")
 expect(game.run.true_id==original and game.run.cleared==0 and not game.run.won,"Construction and movement preserve the selected original and scan state")
 var result:={"checks":checks,"failures":failures,"routes":routes,"conditions":"Godot 4.6.3, fixed 60 Hz simulation, real player input and architectural collision, 1000 identities, frozen NPC motion; not a frame-rate benchmark"}
 var file:=FileAccess.open("res://docs/map-master-movement.json",FileAccess.WRITE);file.store_string(JSON.stringify(result,"  "));file.close()
 game.queue_free();await process_frame;print("MAP MASTER RESULT: %d checks, %d failures"%[checks,failures]);quit(1 if failures else 0)
func follow_nav(game:Node3D,target:Vector3,seconds:float,label:String)->bool:
 var nav:AStar3D=game.crowd.nav
 var path:=nav.get_point_path(nav.get_closest_point(game.player.position),nav.get_closest_point(target));var index:=0
 var start:Vector3=game.player.position;var distance:=0.0
 for i in range(1,path.size()):distance+=path[i-1].distance_to(path[i])
 if path.is_empty():routes.append({"id":label,"passed":false,"reason":"No navigation path"});return false
 Input.action_press("sprint");Input.action_press("forward")
 for frame in ceili(seconds*60):
  if index>=path.size():break
  var d:Vector3=path[index]-game.player.position;d.y=0
  if d.length()<.42:index+=1;continue
  game.player.rotation.y=atan2(-d.x,-d.z);await physics_frame
 Input.action_release("forward");Input.action_release("sprint");await physics_frame
 var passed:bool=index>=path.size() and absf(game.player.position.y-target.y)<.2 and Vector2(game.player.position.x-target.x,game.player.position.z-target.z).length()<2.2
 routes.append({"id":label,"passed":passed,"path_metres":distance,"from":[start.x,start.y,start.z],"target":[target.x,target.y,target.z],"end":[game.player.position.x,game.player.position.y,game.player.position.z]})
 if not passed:push_error("Physical route %s stopped at %s; wanted %s; next %s"%[label,game.player.position,target,path[mini(index,path.size()-1)]])
 return passed
