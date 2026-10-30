extends SceneTree
var g
var w
var body:CapsuleShape3D
func _initialize()->void:call_deferred("run")
func clear(p:Vector3)->bool:
 var world=g.get_world_3d().direct_space_state
 var floor_y:float=p.y
 for offset:Vector3 in[Vector3.ZERO,Vector3(.22,0,.22),Vector3(-.22,0,.22),Vector3(.22,0,-.22),Vector3(-.22,0,-.22)]:
  var ray=world.intersect_ray(PhysicsRayQueryParameters3D.create(p+offset+Vector3.UP*.20,p+offset-Vector3.UP*.18,1))
  if ray.is_empty()or ray.normal.y<.65 or ray.collider.has_meta("v21_fixture"):return false
  floor_y=maxf(floor_y,ray.position.y)
 var q=PhysicsShapeQueryParameters3D.new();q.shape=body;q.transform.origin=Vector3(p.x,floor_y+.95,p.z);q.margin=.01;q.collision_mask=1;return world.intersect_shape(q,1).is_empty()
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
 g=load("res://main.tscn").instantiate();g.mode="v24-equipment-first-check";root.add_child(g)
 while g.results.is_empty():await process_frame
 w=g.get_node("V21_Route_Derived_Wayfinding")
 while not w.has_meta("ready"):await process_frame
 Engine.max_fps=0;g.player.set_physics_process(false);g.shoppers_v18.set_frozen(true);body=CapsuleShape3D.new();body.radius=.34;body.height=1.8;await physics_frame
 var stores:Dictionary={};var graphs:Dictionary={};var grids:Dictionary={};var rows:Array=[];var paths:Array=[];var focus:Array=[]
 for f:Dictionary in g.read_json("res://source/v24/focus-stores.json"):focus.append(f.id)
 for s:Dictionary in g.read_json("res://source/v24/retail-plan.json").stores:stores[s.id]=s
 for d:Dictionary in g.read_json("res://source/v24/equipment-grids.json"):grids[d.id]=d
 var directions:Dictionary=g.read_json("res://source/v22/store-directions.json")
 for d:Dictionary in g.read_json("res://source/v24/equipment-candidates.json"):
  var valid:Array=[]
  for option:Dictionary in d.candidates:
   if clear(g.v3(option.p)):valid.append(option)
   if valid.size()>=(40 if d.previously_unresolved_v23 else 12):break
  var tested:bool=d.previously_unresolved_v23 or d.store_id in focus and d.kind in["checkout","fitting_room","mirror","photo_booth"]
  var selected:Dictionary=valid[0]if not valid.is_empty()else{};var path:Array=[]
  if tested and not selected.is_empty():
   if not graphs.has(d.store_id):var graph=load("res://nav_live_v21.gd").new();graph.setup(grids[d.store_id],w);graphs[d.store_id]=graph
   var st:Dictionary=stores[d.store_id];var start:Vector3=Vector3(st.entry_world[0],st.height,st.entry_world[1])-g.v3(directions[d.store_id])*.85
   for option:Dictionary in valid:
    path=route(graphs[d.store_id],start,g.v3(option.p))
    if not path.is_empty():selected=option;break
  var okay:bool=not selected.is_empty();var connected:bool=not path.is_empty();var row:Dictionary={"fixture_id":d.fixture_id,"store_id":d.store_id,"kind":d.kind,"world_position":d.fixture_world,"equipment_forward":d.fixture_forward,"approach":selected.get("p",[]),"approach_direction":selected.get("towards",[]),"approach_face":selected.get("face",""),"required_clearance":d.required_clearance,"standing_clear":okay,"navigation_tested":tested,"navigation_possible":connected,"usable_capacity":1 if okay and connected else 0,"previously_unresolved_v23":d.previously_unresolved_v23,"human_playtest":false};rows.append(row)
  if connected:paths.append({"id":d.fixture_id,"store_id":d.store_id,"role":d.kind,"points":path,"pass":true})
  if d.previously_unresolved_v23:print("V24_PREVIOUS_155 ",d.fixture_id," stand ",okay," route ",connected)
 var old:Array=rows.filter(func(r):return r.previously_unresolved_v23);var failed:Array=old.filter(func(r):return not r.standing_clear or not r.navigation_possible)
 g.write_json("v24-equipment-physics.json",{"authoritative_layout_sha256":load("res://shopping_catalog_v24.gd").new().source_hash("res://source/v24/retail-plan.json"),"structural_pack_sha256":str(g.results.get("v22_structure_sha256","")),"equipment":rows,"original_155":old,"unresolved_original_155":failed,"unresolved_all_standing":rows.filter(func(r):return not r.standing_clear),"body_radius_m":.34,"body_height_m":1.8,"routes":paths,"human_playtest":false,"method":"Five actual slab-support rays excluding fixture tops, real r.34m capsule clearance. Original155 and30focus primary facilities additionally route from public entrance through actual collision. Untested connectivity not marked usable."});print("V24_EQUIPMENT_RESULT original155 unresolved ",failed.size()," all no-standing ",rows.filter(func(r):return not r.standing_clear).size());g.queue_free();await process_frame;await process_frame;quit()
