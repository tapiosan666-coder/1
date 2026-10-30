extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="v18-crowd-physics-QA";root.add_child(g)
 while g.shoppers_v18==null or g.results.is_empty():await process_frame
 g.player.set_physics_process(false);g.player.input_enabled=false;g.player.position=Vector3(330,0,-63);Engine.max_fps=0
 var checks:Array=[];var sample_rows:Array=[];var saved:bool=false
 for tick in range(3600):
  await physics_frame
  if tick==1199:
   g.write_json("v18-actual-npc-snapshot.json",g.shoppers_v18.snapshot());saved=true
  if tick%120==119:
   for a in g.shoppers_v18.actors:
    var q=PhysicsRayQueryParameters3D.create(a.position+Vector3(0,.25,0),a.position-Vector3(0,.5,0),1);q.exclude=[a.get_rid()];var hit=g.get_world_3d().direct_space_state.intersect_ray(q)
    if hit.is_empty()or a.position.y<float(a.record.p[1])-.20 or a.position.y>float(a.record.p[1])+.25:sample_rows.append({"id":a.record.id,"tick":tick,"p":[a.position.x,a.position.y,a.position.z],"support":not hit.is_empty()})
 var state=g.shoppers_v18.snapshot();g.write_json("v18-crowd-final-state.json",state)
 for row in state.actors:
  var role:String=""
  for a in g.shoppers_v18.actors:
   if a.record.id==row.id:role=a.record.role
  checks.append({"id":row.id,"role":role,"minimum_y":row.minimum_y,"distance_walked":row.distance_walked,"pass":float(row.minimum_y)>-.20 and (role!="walking"or float(row.distance_walked)>15.)})
 g.shoppers_v18.set_enabled(false,true);var off:bool=true
 for a in g.shoppers_v18.actors:off=off and not a.visible and a.collision_layer==0 and a.collision_mask==0
 g.shoppers_v18.set_enabled(true,true);var on:bool=true
 for a in g.shoppers_v18.actors:on=on and a.visible and a.collision_layer==4
 g.write_json("v18-crowd-physics.json",{"method":"Godot CharacterBody3D physics, fixed timestep 60 Hz, simulated 60 seconds; not human operation","count":checks.size(),"checks":checks,"unsupported_samples":sample_rows,"off_removes_visuals_and_collision":off,"on_restores":on,"snapshot_saved":saved,"runtime":g.results});print("V18_CROWD_QA ",checks.filter(func(r):return not r.pass).size()," failed actors; support samples ",sample_rows.size());quit()
