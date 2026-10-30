extends SceneTree
var g
var w
func _initialize()->void:call_deferred("run")
func run()->void:
 g=load("res://main.tscn").instantiate();g.mode="v23-retail-actual-world-QA";root.add_child(g)
 while g.results.is_empty():await process_frame
 w=g.get_node("V21_Route_Derived_Wayfinding")
 while not w.has_meta("ready"):await process_frame
 Engine.max_fps=0;g.player.set_physics_process(false);g.shoppers_v18.set_frozen(true);await physics_frame;await physics_frame
 var plan:Dictionary=g.read_json("res://source/v23/retail-plan.json");var b:Dictionary=g.read_json("res://source/v21/model-bounds.json");b.merge(g.read_json("res://source/v22/model-bounds.json"));b.merge(g.read_json("res://source/v23/model-bounds.json"));var hosts:Dictionary={};var fixture_rows:Array=[];var product_failed:Array=[];var corrections:Array=[];var stack_pending:Array=[];var stack_rows:Array=[];var passed_ids:Dictionary={};var product_map:Dictionary={};var product_count:int=0;var product_pass:int=0;var hanging:int=0;var entry_rows:Array=[];var interior_rows:Array=[];var world=g.get_world_3d().direct_space_state;var directions:Dictionary=g.read_json("res://source/v22/store-directions.json")
 for f:Dictionary in plan.fixtures:
  hosts[f.id]=f;fixture_rows.append({"id":f.id,"store_id":f.store_id,"pass":w.floor_hit(g.v3(f.p)-Vector3.UP*.02)})
 for r:Dictionary in plan.products:product_map[r.id]=r
 for r:Dictionary in plan.products:
  if hosts[r.host].model=="fixture_apparel_rail":hanging+=1;continue
  if r.has("supported_by_product_id"):stack_pending.append(r);continue
  var bounds:Dictionary=b[r.model];var a:float=deg_to_rad(float(r.get("pitch_deg",0.)));var bottom:float=INF
  for y:float in[bounds.min[1],bounds.max[1]]:
   for z:float in[bounds.min[2],bounds.max[2]]:bottom=minf(bottom,cos(a)*y-sin(a)*z)
  var p:Vector3=g.v3(r.p)+Vector3.UP*bottom;var query=PhysicsRayQueryParameters3D.create(p+Vector3.UP*.035,p-Vector3.UP*.05,1);var hit=world.intersect_ray(query);var own:bool=not hit.is_empty()and hit.normal.y>.6 and hit.collider.has_meta("v21_fixture")and str(hit.collider.get_meta("v21_fixture").id)==str(r.host);product_count+=1
  if own:product_pass+=1;passed_ids[r.id]=true;continue
  var snap=world.intersect_ray(PhysicsRayQueryParameters3D.create(p+Vector3.UP*.25,p-Vector3.UP*.28,1));var okay:bool=not snap.is_empty()and snap.normal.y>.6 and snap.collider.has_meta("v21_fixture")and str(snap.collider.get_meta("v21_fixture").id)==str(r.host)
  if okay:corrections.append({"id":r.id,"host":r.host,"old_y":r.p[1],"new_y":float(r.p[1])+snap.position.y-p.y+.003})
  product_failed.append({"id":r.id,"store_id":r.store_id,"host":r.host,"model":r.model,"can_snap":okay,"hit":str(hit.collider.name)if not hit.is_empty()else"NONE"})
 for layer in range(1,4):
  for r:Dictionary in stack_pending:
   if int(r.get("stack_layer",0))!=layer:continue
   var parent:Dictionary=product_map.get(r.supported_by_product_id,{});var okay:bool=not parent.is_empty()and parent.host==r.host and passed_ids.has(parent.id);var gap:float=INF
   if okay:
    var cb:Dictionary=b[r.model];var pb:Dictionary=b[parent.model];var ca:float=deg_to_rad(float(r.get("pitch_deg",0)));var pa:float=deg_to_rad(float(parent.get("pitch_deg",0)));var low:float=INF;var high:float=-INF
    for y:float in[cb.min[1],cb.max[1]]:
     for z:float in[cb.min[2],cb.max[2]]:low=minf(low,cos(ca)*y-sin(ca)*z)
    for y:float in[pb.min[1],pb.max[1]]:
     for z:float in[pb.min[2],pb.max[2]]:high=maxf(high,cos(pa)*y-sin(pa)*z)
    gap=float(r.p[1])+low-float(parent.p[1])-high;okay=absf(gap-.001)<.005 and Vector2(r.p[0]-parent.p[0],r.p[2]-parent.p[2]).length()<.01
   stack_rows.append({"id":r.id,"parent_product":r.supported_by_product_id,"pass":okay,"contact_gap_m":gap})
   if okay:passed_ids[r.id]=true
 for s:Dictionary in plan.stores:
  var e=Vector3(s.entry_world[0],s.height,s.entry_world[1]);var n:Vector3=g.v3(directions[s.id]);var entry_ok:bool=w.sweep(e-n*.85,e+n*1.2);entry_rows.append({"id":s.id,"pass":entry_ok})
  var path:Array=s.main_route_world;var clear:bool=true;var failures:Array=[]
  for i in range(path.size()-1):
   var a:Vector3=g.v3(path[i]);var end:Vector3=g.v3(path[i+1]);var supported:bool=true
   for t in range(ceili(a.distance_to(end)/.65)+1):
    if not w.floor_hit(a.lerp(end,float(t)/maxi(1,ceili(a.distance_to(end)/.65)))):supported=false;break
   if not w.sweep(a,end)or not supported:clear=false;failures.append({"from":path[i],"to":path[i+1],"supported":supported})
  interior_rows.append({"id":s.id,"pass":clear,"failed_segments":failures})
 var stats:Dictionary=g.get_node("V22_Separate_Fixtures_And_SKUs").stats
 g.write_json("v23-retail-physics.json",{"fixtures":fixture_rows,"unsupported_fixtures":fixture_rows.filter(func(r):return not r["pass"]),"products_tested":product_count,"products_passed":product_pass,"hanging_garments_separate":hanging,"stacked_merchandise":stack_rows,"failed_stacks":stack_rows.filter(func(r):return not r["pass"]),"total_product_records":plan.products.size(),"product_failed":product_failed,"product_corrections":corrections,"entrances":entry_rows,"failed_entrances":entry_rows.filter(func(r):return not r["pass"]),"sales_spines":interior_rows,"failed_sales_spines":interior_rows.filter(func(r):return not r["pass"]),"renderer_stats":stats,"human_playtest":false,"scope":"Actual own-host product bottom point rays, fixture floor rays, r=.31m/h=1.8m capsule entrance and declared sales-spine sweeps with floor sampling. Not complete merchandise surface contact or exhaustive human browsing."});print("V23_RETAIL_QA entries ",entry_rows.filter(func(r):return r["pass"]).size(),"/480 spines ",interior_rows.filter(func(r):return r["pass"]).size(),"/480 fixture floor bad ",fixture_rows.filter(func(r):return not r["pass"]).size()," products ",product_pass,"/",product_count);g.queue_free();await process_frame;await process_frame;quit()
