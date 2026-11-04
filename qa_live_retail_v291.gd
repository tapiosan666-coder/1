extends SceneTree
var g
var helper
var output_dir:String="res://evidence/v291-live"
var way
var data:Dictionary={"new_fixture_overlap":[],"paths":[],"unresolved":[],"walks":[],"human_playtest":false,"architecture_changed":false}
func _initialize()->void:call_deferred("run")
func run()->void:
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--output="):output_dir=arg.trim_prefix("--output=")
 DirAccess.make_dir_recursive_absolute(output_dir)
 g=load("res://main.tscn").instantiate();g.mode="live-retail-QA";g.output=output_dir;root.add_child(g)
 while g.results.is_empty():await process_frame
 while not g.get_node("V291_Retail_Continuation").has_meta("ready"):await process_frame
 Engine.max_fps=0;g.shoppers_v18.set_frozen(true);g.player.set_physics_process(false);g.player.position=Vector3(0,80,0);await physics_frame;await physics_frame
 helper=g.get_node("V26_Mall_Architecture");way=g.get_node("V21_Route_Derived_Wayfinding")
 var changes:Dictionary=g.read_json("res://source/v291/fitout-changes.json");var mb:Dictionary=g.read_json("res://source/v291/model-bounds.json")
 var owner=g.get_node("V22_Separate_Fixtures_And_SKUs")
 for d:Dictionary in changes.added:
  var body=owner.get_node(str(d.id).validate_node_name());var b:Dictionary=mb[d.model];var size=g.v3(b.max)-g.v3(b.min);var center=(g.v3(b.max)+g.v3(b.min))*.5;size.y=maxf(.10,size.y-.16);center.y+=.06;var shape=BoxShape3D.new();shape.size=size*float(d.scale)*.96;var n=Vector3(d.n[0],0,d.n[1]);var basis=Basis(Vector3.UP.cross(n),Vector3.UP,n)
  var q=PhysicsShapeQueryParameters3D.new();q.shape=shape;q.transform=Transform3D(basis,g.v3(d.p)+basis*center*float(d.scale));q.collision_mask=1;q.exclude=[body.get_rid()];var hits=g.get_world_3d().direct_space_state.intersect_shape(q,12)
  data.new_fixture_overlap.append({"id":d.id,"store_id":d.store_id,"conservative_bound_contacts":hits.map(func(h):return str(h.collider.get_path())),"pass":hits.is_empty()})
 var relocations:Array=[]
 var bad_ids:Array=data.new_fixture_overlap.filter(func(r):return not r["pass"]).map(func(r):return str(r.id))
 for fid:String in bad_ids:owner.get_node(fid.validate_node_name()).collision_layer=0
 await physics_frame;await physics_frame
 var store_row:Dictionary=g.read_json("res://source/v25/retail-plan.json").stores.filter(func(r):return r.id=="B1-040")[0]
 for fid:String in bad_ids:
  var d:Dictionary=changes.added.filter(func(r):return r.id==fid)[0];var box:Dictionary=mb[d.model];var n=Vector3(d.n[0],0,d.n[1]);var u=Vector3.UP.cross(n);var original=g.v3(d.p);var shape=BoxShape3D.new();var size=g.v3(box.max)-g.v3(box.min);var center=(g.v3(box.max)+g.v3(box.min))*.5;size.y=maxf(.1,size.y-.16);center.y+=.06;shape.size=size*float(d.scale)*.96;var accepted:bool=false;var selected:Vector3=original
  for radius:float in[0.,.6,1.2,1.8,2.4,3.,3.6,4.2]:
   if accepted:break
   for step in 16:
    var trial=original+Vector3(cos(float(step)*TAU/16.),0,sin(float(step)*TAU/16.))*radius;var okay:bool=true
    for xx:float in[float(box.min[0]),float(box.max[0])]:
     for zz:float in[float(box.min[2]),float(box.max[2])]:
      var foot=trial+(u*xx+n*zz)*float(d.scale)
      if not in_shape(Vector2(foot.x,foot.z),store_row.sales_world)or in_shape(Vector2(foot.x,foot.z),store_row.protected_aisles_world)or not way.floor_hit(foot):okay=false
    if not okay:continue
    var query=PhysicsShapeQueryParameters3D.new();query.shape=shape;query.transform=Transform3D(Basis(u,Vector3.UP,n),trial+Basis(u,Vector3.UP,n)*center*float(d.scale));query.collision_mask=1
    if not g.get_world_3d().direct_space_state.intersect_shape(query,1).is_empty():continue
    var approach=trial+n*(float(box.max[2])*float(d.scale)+.75)
    if not helper.standing_clear(approach):continue
    selected=trial;accepted=true;break
  var body=owner.get_node(fid.validate_node_name())
  if accepted:body.global_position=selected;body.collision_layer=1
  relocations.append({"id":fid,"accepted":accepted,"before":d.p,"after":[selected.x,selected.y,selected.z]if accepted else[],"reason":"Actual legacy furniture collision, conservative bounds and floor/aisle checks"})
  await physics_frame;await physics_frame
 data.relocations=relocations
 var old:Dictionary=g.read_json("res://source/v291/interior-paths.json");var target_paths:Array=old.paths.filter(func(p):return p.store_id=="B1-040")
 var graph=AStar2D.new();var points:Dictionary={};var keys:Dictionary={};var start=Vector3(-30.48,.02,-12.154864094)
 var plots:Array=g.read_json("res://source/v25/retail-plan.json").stores;var store:Dictionary=plots.filter(func(s):return s.id=="B1-040")[0];var polygons:Array=store.sales_world.coordinates if store.sales_world.type=="MultiPolygon"else[store.sales_world.coordinates]
 var id:int=0
 for ix in range(94):
  for iz in range(91):
   var p=Vector3(-42.+float(ix)*.4,.02,-44.+float(iz)*.4);var inside:bool=false
   for rings:Array in polygons:
    if Geometry2D.is_point_in_polygon(Vector2(p.x,p.z),PackedVector2Array(rings[0].map(func(v):return Vector2(v[0],v[1])))):inside=true
   if not inside or not helper.standing_clear(p)or not way.floor_hit(p):continue
   graph.add_point(id,Vector2(p.x,p.z));points[Vector2i(ix,iz)]=id;keys[id]=p;id+=1
 for key:Vector2i in points:
  var a:int=points[key]
  for delta:Vector2i in[Vector2i(1,0),Vector2i(0,1),Vector2i(1,1),Vector2i(1,-1)]:
   var other:Vector2i=key+delta
   if not points.has(other):continue
   var b:int=points[other]
   if way.sweep(keys[a],keys[b])and way.sweep(keys[b],keys[a]):graph.connect_points(a,b)
 var from:int=graph.get_closest_point(Vector2(start.x,start.z));var actual_start:Vector3=keys[from]
 for r:Dictionary in target_paths:
  var goal=g.v3(r.points[-1])
  for change:Dictionary in relocations:
   if change.id==r.target and change.accepted:goal+=g.v3(change.after)-g.v3(change.before)
  var options:Array=[]
  for key:int in keys:
   var d:float=keys[key].distance_to(goal)
   if d<2.0:options.append([d,key])
  options.sort_custom(func(a,b):return a[0]<b[0]);var result:Array=[];var adjusted:float=0.
  for option:Array in options:
   var found:PackedInt64Array=graph.get_id_path(from,option[1])
   if found.is_empty():continue
   for k:int in found:result.append([keys[k].x,.02,keys[k].z])
   adjusted=option[0];break
  if result.is_empty():data.unresolved.append({"id":r.target,"reason":"No live capsule path to within2m of intended display view"});continue
  if way.sweep(start,actual_start):result.push_front([start.x,start.y,start.z])
  # Simplify only where the actual physical capsule can sweep across the segment.
  var simple:Array=[result[0]];var i:int=0
  while i<result.size()-1:
   var j:int=result.size()-1
   while j>i+1 and not way.sweep(g.v3(result[i]),g.v3(result[j])):j-=1
   simple.append(result[j]);i=j
  var check=way.check_path(simple);data.paths.append({"id":r.target,"store_id":r.store_id,"points":simple,"goal_adjustment_m":adjusted,"pass":check["pass"],"all_waypoints_clear":simple.all(func(p):return helper.standing_clear(g.v3(p))),"method":"Live physical .4m graph inside existing sales polygon; no wall/floor edited"})
  print("V291_LIVE_PATH ",r.target," ",check["pass"])
 data.camera_repairs=[]
 for c:Dictionary in g.read_json("res://source/v291/review-cameras.json"):
  var foot=g.v3(c.eye)-Vector3.UP*1.65
  if not helper.standing_clear(foot)and str(c.wing)=="B":
   var best:int=graph.get_closest_point(Vector2(foot.x,foot.z));var q:Vector3=keys[best]
   data.camera_repairs.append({"id":c.id,"before":c.eye,"after":[q.x,1.65,q.z],"moved_m":Vector2(foot.x,foot.z).distance_to(Vector2(q.x,q.z))})
 var f=FileAccess.open(output_dir+"/results.json",FileAccess.WRITE);f.store_string(JSON.stringify(data,"  "));f=null;print("V291_LIVE_DONE nodes ",id," paths ",data.paths.size());g.queue_free();await process_frame;await process_frame;quit()

func in_shape(p:Vector2,shape:Dictionary)->bool:
 var polys:Array=shape.coordinates if shape.type=="MultiPolygon"else[shape.coordinates]
 for rings:Array in polys:
  if Geometry2D.is_point_in_polygon(p,PackedVector2Array(rings[0].map(func(q):return Vector2(q[0],q[1])))):return true
 return false
