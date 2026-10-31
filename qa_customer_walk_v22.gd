extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="v21-actual-characterbody-walk";root.add_child(g)
 while g.results.is_empty():await process_frame
 var way=g.get_node("V21_Route_Derived_Wayfinding")
 while not way.has_meta("ready"):await process_frame
 Engine.max_fps=0;g.player.set_physics_process(false);g.shoppers_v18.set_frozen(true);var probe=CharacterBody3D.new();probe.collision_layer=0;probe.collision_mask=1;probe.floor_snap_length=.30;probe.safe_margin=.01;var shape=CollisionShape3D.new();var cap=CapsuleShape3D.new();cap.radius=.31;cap.height=1.80;shape.shape=cap;probe.add_child(shape);g.add_child(probe);await physics_frame
 var routes:Array=g.read_json("res://source/v22/customer-walk-routes.json");var by_store:Dictionary={}
 for route:Dictionary in routes:
  if not by_store.has(route.store_id)or route.role=="checkout":by_store[route.store_id]=route
 var rows:Array=[]
 for route:Dictionary in by_store.values():
  var start=g.v3(route.points[0]);var y:float=way.floor_y(start);probe.position=Vector3(start.x,y+.92,start.z);probe.velocity=Vector3.ZERO;probe.reset_physics_interpolation();var target_index:int=1;var ticks:int=0;var stuck:int=0;var previous:Vector3=probe.position;var fallen:bool=false;var contacts:Array=[]
  while target_index<route.points.size()and ticks<7200:
   await physics_frame;ticks+=1;var target=g.v3(route.points[target_index]);var delta=Vector3(target.x-probe.position.x,0,target.z-probe.position.z)
   if delta.length()<.13:target_index+=1;continue
   var direction=delta.normalized();probe.velocity.x=direction.x*2.0;probe.velocity.z=direction.z*2.0;probe.velocity.y-=9.8/60.;probe.move_and_slide()
   if probe.position.y<float(route.points[0][1])+.25:fallen=true;break
   if probe.position.distance_to(previous)<.0008:stuck+=1
   else:stuck=0
   previous=probe.position
   if stuck>90:
    for i in probe.get_slide_collision_count():contacts.append(str(probe.get_slide_collision(i).get_collider().name))
    break
  rows.append({"store_id":route.store_id,"route":route.id,"role":route.role,"reached":target_index>=route.points.size(),"fell":fallen,"ticks":ticks,"simulated_seconds":ticks/60.,"contacts":contacts,"pass":target_index>=route.points.size()and not fallen});print("V22_CUSTOMER_BODY_WALK ",route.store_id," ",rows[-1]["pass"])
 g.write_json("v22-customer-characterbody-walk.json",{"routes":rows,"human_playtest":false,"method":"Automatic CharacterBody3D with gravity and move_and_slide at fixed60Hz,2m/s. Capsule centre .92m above measured floor, r=.31,h=1.80. Nine corrected customer spines, including five B door seams; not every checkout; distinct from geometric and swept-capsule checks."});probe.queue_free();g.queue_free();await process_frame;await process_frame;quit()
