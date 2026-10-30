extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="v22-local-customer-route-repair";root.add_child(g)
 while g.results.is_empty():await process_frame
 var w=g.get_node("V21_Route_Derived_Wayfinding")
 while not w.has_meta("ready"):await process_frame
 Engine.max_fps=0;g.player.set_physics_process(false);g.shoppers_v18.set_frozen(true);await physics_frame;var result:Array=[];var dirs:Dictionary=g.read_json("res://source/v22/store-directions.json")
 for d:Dictionary in g.read_json("res://source/v22/interior-route-grids.json"):
  var graph=load("res://nav_live_v21.gd").new();graph.setup(d,w);var e=Vector2(d.entry[0],d.entry[1]);var start:Vector3=Vector3(e.x,d.height,e.y)-g.v3(dirs[d.id])*.85;var a:int=graph.nearest_clear(e);var nearby:Array=[]
  for id:int in graph.get_point_ids():
   var dist:float=graph.get_point_position(id).distance_squared_to(e)
   if dist<=20.25:nearby.append([dist,id])
  nearby.sort_custom(func(x,y):return x[0]<y[0]);a=-1
  for option:Array in nearby:
   if graph.clear_node(option[1])and w.sweep(start,graph.world(option[1])):a=option[1];break
  var diagnostic:Array=[]
  if a<0:
   for option:Array in nearby.slice(0,6):
    var wp:Vector3=graph.world(option[1]);var query=PhysicsShapeQueryParameters3D.new();query.shape=w.capsule;query.transform.origin=wp+Vector3.UP*.95;query.margin=.008;query.collision_mask=1;var contacts:Array=[]
    for hit:Dictionary in g.get_world_3d().direct_space_state.intersect_shape(query,8):contacts.append(str(hit.collider.name))
    var ray=PhysicsRayQueryParameters3D.create(wp+Vector3.UP*.8,wp-Vector3.UP*.8,1);var fh=g.get_world_3d().direct_space_state.intersect_ray(ray)
    diagnostic.append({"p":[wp.x,wp.y,wp.z],"node_clear":graph.clear_node(option[1]),"entry_sweep":w.sweep(start,wp),"floor":w.floor_hit(wp),"floor_hit":str(fh.get("position","NONE")),"contacts":contacts})
  var candidates:Array=[]
  for id:int in graph.get_point_ids():candidates.append([graph.get_point_position(id).distance_squared_to(e),id])
  candidates.sort_custom(func(x,y):return x[0]>y[0]);var route:Array=[];var reach_distance:float=0.
  if a>=0 and w.sweep(start,graph.world(a)):
   for option:Array in candidates:
    var b:int=option[1]
    if not graph.clear_node(b):continue
    var path:PackedVector2Array=graph.get_point_path(a,b)
    if path.is_empty():continue
    var raw:Array=[start]
    for q:Vector2 in path:raw.append(Vector3(q.x,d.height,q.y))
    var i:int=0;route.append([start.x,start.y,start.z])
    while i<raw.size()-1:
     var j:int=mini(raw.size()-1,i+18)
     while j>i+1:
      var okay:bool=w.sweep(raw[i],raw[j])
      if okay:
       for t in range(ceili(raw[i].distance_to(raw[j])/.5)+1):
        if not w.floor_hit(raw[i].lerp(raw[j],float(t)/maxi(1,ceili(raw[i].distance_to(raw[j])/.5)))):okay=false;break
      if okay:break
      j-=1
     route.append([raw[j].x,raw[j].y,raw[j].z]);i=j
    reach_distance=sqrt(option[0]);break
  result.append({"id":d.id,"route":route,"endpoint_distance_from_entry_m":reach_distance,"pass":not route.is_empty(),"geometry_changed":false,"diagnostic":diagnostic,"start_node":a,"nearby_nodes":nearby.size(),"entrance_crossing_included":true});print("V22_CUSTOMER_REPAIR ",d.id," ",reach_distance,"m ",not route.is_empty())
 g.write_json("v22-customer-route-repairs.json",{"stores":result,"human_playtest":false,"method":"Local .6m sales-only graph with actual capsule/floor validation at each edge. Deepest reachable sampled point; no new floor, opening or fixture edits."});quit()
