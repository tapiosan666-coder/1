extends SceneTree
var g
var w
func _initialize()->void:call_deferred("run")
func clear(p:Vector3)->bool:
 var y:float=w.floor_y(p)
 if is_nan(y):return false
 var q=PhysicsShapeQueryParameters3D.new();q.shape=w.capsule;q.transform.origin=Vector3(p.x,y+.95,p.z);q.margin=.008;q.collision_mask=1;return g.get_world_3d().direct_space_state.intersect_shape(q,1).is_empty()
func nodes_near(graph,p:Vector3,r:float)->Array:
 var a:Array=[]
 for id:int in graph.get_point_ids():
  var d:float=graph.get_point_position(id).distance_squared_to(Vector2(p.x,p.z))
  if d<=r*r:a.append([d,id])
 a.sort_custom(func(x,y):return x[0]<y[0]);return a
func route(graph,start:Vector3,end:Vector3)->Array:
 var a:int=-1;var b:int=-1
 for option:Array in nodes_near(graph,start,4.5):
  if graph.clear_node(option[1])and w.sweep(start,graph.world(option[1])):a=option[1];break
 for option:Array in nodes_near(graph,end,2.5):
  if graph.clear_node(option[1])and w.sweep(graph.world(option[1]),end):b=option[1];break
 if a<0 or b<0:return[]
 var points:PackedVector2Array=graph.get_point_path(a,b)
 if points.is_empty():return[]
 var raw:Array=[start]
 for q:Vector2 in points:raw.append(Vector3(q.x,graph.height,q.y))
 raw.append(end);var result:Array=[[start.x,start.y,start.z]];var i:int=0
 while i<raw.size()-1:
  var j:int=mini(raw.size()-1,i+18)
  while j>i+1:
   var ok:bool=w.sweep(raw[i],raw[j])
   if ok:
    for t in range(ceili(raw[i].distance_to(raw[j])/.5)+1):
     if not w.floor_hit(raw[i].lerp(raw[j],float(t)/maxi(1,ceili(raw[i].distance_to(raw[j])/.5)))):ok=false;break
   if ok:break
   j-=1
  result.append([raw[j].x,raw[j].y,raw[j].z]);i=j
 return result
func run()->void:
 g=load("res://main.tscn").instantiate();g.mode="v23-data-only-shopping-positions-QA";root.add_child(g)
 while g.results.is_empty():await process_frame
 w=g.get_node("V21_Route_Derived_Wayfinding")
 while not w.has_meta("ready"):await process_frame
 Engine.max_fps=0;g.player.set_physics_process(false);g.shoppers_v18.set_frozen(true);await physics_frame
 var plan:Dictionary=g.read_json("res://source/v24/retail-plan.json");var stores:Dictionary={};var fixtures:Dictionary={};var dirs:Dictionary=g.read_json("res://source/v22/store-directions.json");var grids:Dictionary={};var graphs:Dictionary={};var rows:Array=[];var all_paths:Array=[];var facility_paths:Array=[];var representative_ids:Array=g.read_json("res://source/v23/representatives.json").values()
 for s:Dictionary in plan.stores:stores[s.id]=s
 for f:Dictionary in plan.fixtures:fixtures[f.id]=f
 for d:Dictionary in g.read_json("res://source/v23/shopping-grids.json"):grids[d.id]=d
 for d:Dictionary in g.read_json("res://source/v23/shopping-candidates.json"):
  var valid:Array=[]
  for q:Array in d.candidates:
   if clear(g.v3(q)):valid.append(q)
  var selected:Array=valid[0]if not valid.is_empty()else[];var path:Array=[];var connected:bool=false;var tested:bool=false
  if d.store_id in representative_ids and d.kind in["checkout","fitting_room","mirror","photo_booth"]:
   tested=true
   if not graphs.has(d.store_id):var graph=load("res://nav_live_v21.gd").new();graph.setup(grids[d.store_id],w);graphs[d.store_id]=graph
   var s:Dictionary=stores[d.store_id];var start=Vector3(s.entry_world[0],s.height,s.entry_world[1])-g.v3(dirs[d.store_id])*.85
   for goal:Array in valid.slice(0,8):
    path=route(graphs[d.store_id],start,g.v3(goal))
    if not path.is_empty():selected=goal;connected=true;break
   all_paths.append({"id":d.id,"store_id":d.store_id,"fixture_id":d.fixture_id,"role":d.kind,"points":path,"pass":connected});print("V23_FACILITY_ROUTE ",d.store_id," ",d.kind," ",connected)
  var r:Dictionary={"id":d.id,"store_id":d.store_id,"fixture_id":d.fixture_id,"kind":d.kind,"point":selected,"point_clear":not selected.is_empty(),"entry_connection_tested":tested,"entry_connected":connected,"face_towards_ref":d.fixture_id,"human_playtest":false,"spawned_NPC":false};rows.append(r)
  if d.has("facility_walk_path"):
   var ok:bool=true
   for i in range(d.facility_walk_path.size()-1):
    if not w.sweep(g.v3(d.facility_walk_path[i]),g.v3(d.facility_walk_path[i+1])):ok=false
   facility_paths.append({"id":d.fixture_id+"-inside","store_id":d.store_id,"role":d.kind,"points":d.facility_walk_path,"pass":ok});print("V23_FACILITY_INSIDE ",d.kind," ",ok)
   if d.has("photo_equipment"):r.photo_equipment=d.photo_equipment
 var output:Dictionary={"authoritative_layout_sha256":load("res://shopping_catalog_v23.gd").new().source_hash("res://source/v24/retail-plan.json"),"structural_pack_sha256":g.results.get("v22_structure_sha256",""),"approaches":rows,"unresolved_points":rows.filter(func(r):return not r.point_clear),"representative_routes":all_paths,"failed_representative_routes":all_paths.filter(func(r):return not r["pass"]),"facility_inside_routes":facility_paths,"human_playtest":false,"method":"Actual capsule clearance at generated fixture-relative approach points. Ten representative store primary facilities additionally route from actual public entrance through a .7m collision-aware sales graph. Other clear points are NOT claimed entry-connected. No NPC spawn, shopping or purchase system implemented."}
 g.write_json("v23-shopping-physics.json",output);g.write_json("v23-shopping-body-routes.json",{"routes":all_paths.filter(func(r):return r["pass"])+facility_paths.filter(func(r):return r["pass"]),"human_playtest":false});print("V23_SHOPPING_QA ",rows.size()," points unresolved ",output.unresolved_points.size()," routes failed ",output.failed_representative_routes.size());g.queue_free();await process_frame;await process_frame;quit()
