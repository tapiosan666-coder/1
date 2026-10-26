extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var game=load("res://main.tscn").instantiate();game.mode="service-qa";root.add_child(game)
 game.player.input_enabled=false;game.player.belt_enabled=false;game.staff.set_all_open(false)
 for i in range(3):await physics_frame
 var checks:Array=[]
 for room:Dictionary in game.manifest.service_rooms_v4:
  if not room.has("name"):continue
  var index:int=-1
  for j in range(game.staff.doors.size()):
   if game.staff.doors[j].data.store==room.id:index=j
  if index<0:checks.append({"id":room.id+"-door-present","pass":false});continue
  var d:Dictionary=game.staff.doors[index];var n=Vector3(d.data.n[0],0,d.data.n[1]);var u=Vector3(d.data.u[0],0,d.data.u[1]);var c:Vector3=d.center
  game.staff.set_open(index,false);await physics_frame
  var q=PhysicsRayQueryParameters3D.create(c-n*.5+Vector3.UP,c+n*.5+Vector3.UP);q.exclude=[game.player.get_rid()]
  var hit:Dictionary=game.get_world_3d().direct_space_state.intersect_ray(q)
  checks.append({"id":room.id+"-closed-leaf","pass":not hit.is_empty()and hit.collider==d.pivot,"kind":"actual closed door collider"})
  game.staff.set_open(index,true);await physics_frame
  for offset:float in[-.25,0,.25]:
   var a:Vector3=c-n*1.0+u*offset;var b:Vector3=c+n*1.0+u*offset
   await game.settle(a)
   var points:Array=[[b.x,b.y,b.z]];var result:Dictionary=await game.walk_points(points,2.0);result.id=room.id+"-aperture-"+str(offset);result.kind="actual CharacterBody3D door traversal";checks.append(result)
  var coords:Array=room.reserved_staff_route.coordinates;var path:Array=[]
  path.append([c.x-n.x*.8,c.y,c.z-n.z*.8])
  for pp:Array in coords:path.append([pp[0]+429,c.y,pp[1]-46])
  await game.settle(Vector3(path[0][0],path[0][1],path[0][2]))
  var result:Dictionary=await game.walk_points(path,3.0);result.id=room.id+"-source-route";result.kind="actual CharacterBody3D source staff route, corrected coordinates";checks.append(result)
  # Wall closure is tested at room edges away from the source aperture, not by floor support alone.
  var poly:Array=room.polygon.coordinates[0]
  for k in range(0,poly.size()-1,max(1,int(poly.size()/5))):
   var aa:Array=poly[k];var bb:Array=poly[k+1];var mid=Vector3((aa[0]+bb[0])*.5+429,c.y+1.2,(aa[1]+bb[1])*.5-46)
   if Vector2(mid.x-c.x,mid.z-c.z).length()<2:continue
   if mid.x< -82 or mid.x>79 or mid.z< -61 or mid.z>77:continue
   var tangent=Vector3(bb[0]-aa[0],0,bb[1]-aa[1]).normalized();var nn=Vector3(-tangent.z,0,tangent.x)
   var query=PhysicsRayQueryParameters3D.create(mid-nn*.3,mid+nn*.3);query.exclude=[game.player.get_rid()];query.collision_mask=2
   var h:Dictionary=game.get_world_3d().direct_space_state.intersect_ray(query);checks.append({"id":room.id+"-wall-"+str(k),"pass":not h.is_empty(),"kind":"actual opaque service-room perimeter collider"})
  if room.rack_footprints.size()>0:
   var ring:Array=room.rack_footprints[0].coordinates[0];var center=Vector3.ZERO
   for j in range(4):center+=Vector3(ring[j][0]+429,c.y+.722,ring[j][1]-46)/4.0
   var rq=PhysicsRayQueryParameters3D.create(center-n*.7,center+n*.7);rq.exclude=[game.player.get_rid()];rq.collision_mask=1
   var rh:Dictionary=game.get_world_3d().direct_space_state.intersect_ray(rq)
   checks.append({"id":room.id+"-rack-shelf-collider","pass":not rh.is_empty(),"kind":"rack shelf actual metal collider at body height","hit":str(rh.collider.name)if not rh.is_empty()else"none"})
 var passed:int=0
 for check:Dictionary in checks:
  if check["pass"]:passed+=1
 var r:Dictionary=game.results.duplicate(true);r.checks=checks;r.passed=passed;r.total=checks.size();r.failed=checks.size()-passed;r.kind="automated Godot collision tests; not human operation; no inventory/delivery-operation certification"
 var file=FileAccess.open("res://evidence/service-room-walk.json",FileAccess.WRITE);file.store_string(JSON.stringify(r,"  "));print("SERVICE_QA ",passed,"/",checks.size());quit(0 if passed==checks.size()else 1)
