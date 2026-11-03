extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="v22-480-interior-route-audit";root.add_child(g)
 while g.results.is_empty():await process_frame
 var w=g.get_node("V21_Route_Derived_Wayfinding")
 while not w.has_meta("ready"):await process_frame
 Engine.max_fps=0;g.player.set_physics_process(false);g.shoppers_v18.set_frozen(true);await physics_frame
 var p:Dictionary=g.read_json("res://source/v22/retail-plan.json");var rows:Array=[]
 for s:Dictionary in p.stores:
  var path:Array=s.main_route_world;var pass_route:bool=true;var segments:Array=[]
  for i in range(path.size()-1):
   var a:Vector3=g.v3(path[i]);var b:Vector3=g.v3(path[i+1]);var clear:bool=w.sweep(a,b);var supported:bool=true
   for t in range(ceili(a.distance_to(b)/.65)+1):
    if not w.floor_hit(a.lerp(b,float(t)/maxi(1,ceili(a.distance_to(b)/.65)))):supported=false;break
   var contacts:Array=[]
   if not clear:
    var query=PhysicsShapeQueryParameters3D.new();query.shape=w.capsule;query.transform.origin=a+Vector3.UP*.95;query.motion=b-a;query.margin=.008;query.collision_mask=1;var hit=g.get_world_3d().direct_space_state.cast_motion(query);query.transform.origin+=(b-a)*minf(1.,hit[0]+.002);query.motion=Vector3.ZERO
    for contact:Dictionary in g.get_world_3d().direct_space_state.intersect_shape(query,8):contacts.append(str(contact.collider.name))
   segments.append({"from":path[i],"to":path[i+1],"clear":clear,"supported":supported,"contacts":contacts});pass_route=pass_route and clear and supported
  rows.append({"id":s.id,"pass":pass_route,"segments":segments,"geometric_checkout_access":s.get("geometric_checkout_access",false)})
 g.write_json("v22-interior-route-physics.json",{"stores":rows,"failed":rows.filter(func(r):return not r["pass"]),"human_playtest":false,"method":"Actual .31m radius capsule cast along declared entrance-to-depth spine plus .65m floor samples. Not exhaustive browsing or checkout walking. Checkout accessibility here is the separate geometric layout flag."});print("V22_INTERIOR_ROUTES ",rows.size()-rows.filter(func(r):return not r["pass"]).size(),"/",rows.size());g.queue_free();await process_frame;await process_frame;quit()
