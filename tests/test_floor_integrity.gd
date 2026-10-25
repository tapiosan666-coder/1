extends SceneTree
var shared_edge_probes:=0
func _initialize()->void:call_deferred("verify")
func verify()->void:
 var game=load("res://scenes/main.tscn").instantiate();root.add_child(game);game.start_run(300,912);game.crowd.set_physics_process(false);game.set_physics_process(false);game.player.set_physics_process(false)
 await physics_frame;await physics_frame
 var space:PhysicsDirectSpaceState3D=game.get_world_3d().direct_space_state
 var ray:=PhysicsRayQueryParameters3D.new();ray.collision_mask=1;ray.exclude=[game.player.get_rid()]
 var floors:Dictionary={};var missing:=0;var checked:=0
 for p:Vector3 in game.mall.spawn_points:
  var key:=MallLayout.floor_at(p);floors[key]=floors.get(key,0)+1;checked+=1
  if not floor_beneath(space,ray,p):
   missing+=1
   if missing<9:push_error("No physical floor at public sample "+str(MallCurve.plan(p)))
 var midpoint_count:=0;var midpoint_missing:=0
 var positions:PackedVector3Array=WorldCache.navigation.positions;var edges:PackedInt32Array=WorldCache.navigation.edges
 for i in range(0,edges.size(),2):
  var a:Vector3=positions[edges[i]];var b:Vector3=positions[edges[i+1]]
  if absf(a.y-b.y)>.01:continue
  midpoint_count+=1
  if not floor_beneath(space,ray,(a+b)*.5):
   midpoint_missing+=1
   if midpoint_missing<9:push_error("No physical floor between connected public samples "+str(MallCurve.plan((a+b)*.5)))
 var failures:=int(missing>0)+int(midpoint_missing>0)+int(floors.size()!=10)
 print("SHARED_EDGE_FOOTPRINT_RECHECKS ",shared_edge_probes)
 print("FLOOR INTEGRITY AUDIT: samples=%d missing=%d horizontal_midpoints=%d missing=%d implemented_floors=%d"%[checked,missing,midpoint_count,midpoint_missing,floors.size()])
 game.queue_free();await process_frame;print("FLOOR INTEGRITY RESULT: 3 checks, %d failures"%failures);quit(1 if failures else 0)
func floor_beneath(space:PhysicsDirectSpaceState3D,ray:PhysicsRayQueryParameters3D,p:Vector3)->bool:
 ray.from=p+Vector3.UP*.12;ray.to=p-Vector3.UP*.22
 var hit:=space.intersect_ray(ray)
 if not hit.is_empty() and absf(hit.position.y-p.y)<.05:return true
 # Ray/trimesh tests can miss an exactly shared triangle edge at float precision.
 # Require real coplanar floor in all four directions, never merely one side of a gap.
 for offset:Vector3 in [Vector3(.025,0,0),Vector3(-.025,0,0),Vector3(0,0,.025),Vector3(0,0,-.025)]:
  ray.from=p+offset+Vector3.UP*.12;ray.to=p+offset-Vector3.UP*.22
  hit=space.intersect_ray(ray)
  if hit.is_empty() or absf(hit.position.y-p.y)>=.05:return false
 shared_edge_probes+=1;return true
