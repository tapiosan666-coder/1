extends SceneTree
var g
func _initialize()->void:call_deferred("run")
func run()->void:
 var baseline:bool=OS.get_cmdline_user_args().has("--v29-baseline");var out:String="res://evidence/v291"
 for a:String in OS.get_cmdline_user_args():
  if a.begins_with("--output="):out=a.trim_prefix("--output=")
 DirAccess.make_dir_recursive_absolute(out)
 g=load("res://main.tscn").instantiate();g.output=out;g.mode="v291-QA";root.add_child(g)
 while g.results.is_empty():await process_frame
 while not g.get_node("V29_Continuous_1F").has_meta("ready"):await process_frame
 if not baseline:
  while not g.get_node("V291_Retail_Continuation").has_meta("ready"):await process_frame
 g.shoppers_v18.set_frozen(true);g.player.set_physics_process(false);g.player.global_position=Vector3(0,80,0);await physics_frame;await physics_frame
 var helper=g.get_node("V26_Mall_Architecture");var way=g.get_node("V21_Route_Derived_Wayfinding");var data:Dictionary={"baseline":baseline,"human_playtest":false,"floor_and_plot_modified":false,"routes":[],"interior_paths":[],"new_fixture_support":[],"cameras":[],"actual_body_walks":[]}
 for r:Dictionary in g.read_json("res://source/v29/routes.json"):
  var sweep:Dictionary=way.check_path(r.points);var standing:bool=r.points.all(func(p):return helper.standing_clear(g.v3(p)));data.routes.append({"id":r.id,"pass":sweep["pass"]and standing})
 for r:Dictionary in g.read_json("res://source/v291/interior-paths.json").paths:
  var sweep:Dictionary=way.check_path(r.points);var standing:bool=r.points.all(func(p):return helper.standing_clear(g.v3(p)));data.interior_paths.append({"id":r.target,"store_id":r.store_id,"pass":sweep["pass"]and standing,"kind":r.kind,"sweep":sweep,"standing":standing,"points":r.points,"first_blocking_contacts":blocking_contacts(r.points)if not(sweep["pass"]and standing)else[]})
 if not baseline:
  for f:Dictionary in g.read_json("res://source/v291/fitout-changes.json").added:
   var p=g.v3(f.p);var b:Dictionary=g.read_json("res://source/v291/model-bounds.json")[f.model];var n=Vector3(f.n[0],0,f.n[1]);var u=Vector3.UP.cross(n);var all_supported:bool=true
   for x:float in[float(b.min[0]),float(b.max[0])]:
    for z:float in[float(b.min[2]),float(b.max[2])]:
     var q=p+(u*x+n*z)*float(f.scale);var hit=get_root().get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(q+Vector3.UP*.11,q-Vector3.UP*.15,1))
     if hit.is_empty()or absf(hit.position.y-p.y)>.10:all_supported=false
   data.new_fixture_support.append({"id":f.id,"all_four_corners_supported":all_supported,"other_geometry_contacts":fixture_contacts(f,b)})
 for c:Dictionary in g.read_json("res://source/v291/review-cameras.json"):
  var p=g.v3(c.eye)-Vector3.UP*1.65;data.cameras.append({"id":c.id,"standing":helper.standing_clear(p),"floor":way.floor_hit(p)})
 for sid:String in["A1F-002","A1F-044","B1-040","C1F-CE-3"]:
  var candidates:Array=data.interior_paths.filter(func(r):return r.store_id==sid and r["pass"])
  candidates.sort_custom(func(a,b):return route_length(a.points)>route_length(b.points))
  if candidates.is_empty():continue
  var route:Array=candidates[0].points.duplicate(true);var back:Array=route.slice(0,route.size()-1).duplicate(true);back.reverse();route.append_array(back)
  data.actual_body_walks.append(await walk_route(sid,route));print("V291_ACTUAL_WALK ",sid," ",data.actual_body_walks[-1]["pass"])
 g.player.set_physics_process(false)
 var api=load("res://shopping_catalog_v25.gd").new();api.setup(g);data.catalog={"stores":api.stores.size(),"fixtures":api.fixtures.size(),"products":api.products.size(),"index_rows":api.index.size()};data.NPC=g.shoppers_v18.actors.size();data.cap=Engine.max_fps;data.vsync=DisplayServer.window_get_vsync_mode();data.continuation=g.get_node("V291_Retail_Continuation").report if not baseline else{}
 var file=FileAccess.open(out+"/"+("before"if baseline else"after")+"-QA.json",FileAccess.WRITE);file.store_string(JSON.stringify(data,"  "));file=null
 print("V291_QA_DONE routes ",data.routes.filter(func(r):return r["pass"]).size(),"/",data.routes.size()," interior ",data.interior_paths.filter(func(r):return r["pass"]).size(),"/",data.interior_paths.size())
 g.queue_free();await process_frame;await process_frame;quit()

func blocking_contacts(points:Array)->Array:
 var hits:Array=[];var capsule=CapsuleShape3D.new();capsule.radius=.31;capsule.height=1.8
 for k in range(points.size()-1):
  var a=g.v3(points[k]);var b=g.v3(points[k+1]);var count:int=maxi(1,ceili(a.distance_to(b)/.18))
  for i in count+1:
   var p=a.lerp(b,float(i)/count);var q=PhysicsShapeQueryParameters3D.new();q.shape=capsule;q.transform=Transform3D(Basis.IDENTITY,p+Vector3.UP*.94);q.collision_mask=1;var collisions=g.get_world_3d().direct_space_state.intersect_shape(q,6)
   if not collisions.is_empty():
    hits.append({"p":[p.x,p.y,p.z],"colliders":collisions.map(func(h):return str(h.collider.get_path()))});return hits
 return hits

func route_length(points:Array)->float:
 var total:float=0.
 for i in range(points.size()-1):total+=g.v3(points[i]).distance_to(g.v3(points[i+1]))
 return total
func walk_route(sid:String,points:Array)->Dictionary:
 var p:CharacterBody3D=g.player;p.input_enabled=false;p.collision_mask=1;p.velocity=Vector3.ZERO;p.auto_active=false;p.position=g.v3(points[0])+Vector3.UP*.05;p.reset_physics_interpolation();p.set_physics_process(true)
 for i in 12:await physics_frame
 var passed:bool=true;var lowest:float=p.position.y;var ticks:int=0;var failed_target:Array=[]
 for target:Array in points.slice(1):
  p.auto_target=g.v3(target);p.auto_speed=2.6;p.auto_active=true;var reached:bool=false
  for i in range(ceili(p.position.distance_to(p.auto_target)/2.6*60.)+240):
   await physics_frame;ticks+=1;lowest=minf(lowest,p.position.y);var delta=p.position-p.auto_target;delta.y=0
   if delta.length()<.075:reached=true;break
   if p.position.y<-.35:break
  if not reached:passed=false;failed_target=target;break
 p.auto_active=false;p.velocity=Vector3.ZERO;p.set_physics_process(false)
 return {"store_id":sid,"pass":passed,"physics_ticks":ticks,"speed_m_s":2.6,"lowest_y":lowest,"failed_target":failed_target,"end":[p.position.x,p.position.y,p.position.z],"points":points,"NPC_collision_excluded":true,"method":"Actual player controller, CharacterBody3D and move_and_slide, out-and-return along one representative interior path","human_playtest":false}
func fixture_contacts(d:Dictionary,b:Dictionary)->Array:
 var owner=g.get_node("V22_Separate_Fixtures_And_SKUs");var body=owner.get_node(str(d.id).validate_node_name());var size=g.v3(b.max)-g.v3(b.min);var center=(g.v3(b.max)+g.v3(b.min))*.5;size.y=maxf(.10,size.y-.16);center.y+=.06;var shape=BoxShape3D.new();shape.size=size*float(d.scale)*.96;var n=Vector3(d.n[0],0,d.n[1]);var basis=Basis(Vector3.UP.cross(n),Vector3.UP,n);var q=PhysicsShapeQueryParameters3D.new();q.shape=shape;q.transform=Transform3D(basis,g.v3(d.p)+basis*center*float(d.scale));q.collision_mask=1;q.exclude=[body.get_rid()];return g.get_world_3d().direct_space_state.intersect_shape(q,8).map(func(h):return str(h.collider.get_path()))
