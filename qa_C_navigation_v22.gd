extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://Integrated_candidate_v22.tscn").instantiate();g.mode="v22-real-product-support";root.add_child(g)
 while g.results.is_empty():await process_frame
 while not g.get_node("V21_Route_Derived_Wayfinding").has_meta("ready"):await process_frame
 Engine.max_fps=0;g.player.set_physics_process(false);g.shoppers_v18.set_frozen(true);await physics_frame
 var way=g.get_node("V21_Route_Derived_Wayfinding");var world=g.get_world_3d().direct_space_state;var rows:Array=[]
 for r:Dictionary in g.read_json("res://source/v22/blocked-sign-paths.json"):
  var contacts:Array=[]
  for i in range(r.actual_path.size()-1):
   var a=g.v3(r.actual_path[i]);var b=g.v3(r.actual_path[i+1]);var query=PhysicsShapeQueryParameters3D.new();query.shape=way.capsule;query.transform.origin=a+Vector3.UP*.95;query.motion=b-a;query.margin=.008;query.collision_mask=1;var cast=world.cast_motion(query)
   if cast[0]<.997:
    query.transform.origin+=(b-a)*minf(1.,cast[0]+.01);query.motion=Vector3.ZERO
    for hit:Dictionary in world.intersect_shape(query,6):contacts.append({"from":r.actual_path[i],"to":r.actual_path[i+1],"collider":str(hit.collider.name),"fixture":hit.collider.get_meta("v21_fixture",{})})
  rows.append({"sign":r.sign,"kind":r.kind,"contacts":contacts})
 g.write_json("v22-C-navigation-obstacles.json",rows);print("V22_C_NAV_DIAGNOSTICS ",rows.size());g.queue_free();await process_frame;await process_frame;quit()
