extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="v21-scene-QA";root.add_child(g)
 while g.results.is_empty():await process_frame
 var way=g.get_node("V21_Route_Derived_Wayfinding")
 while not way.has_meta("ready"):await process_frame
 Engine.max_fps=0;g.shoppers_v18.set_frozen(true);g.player.set_physics_process(false)
 await physics_frame;await physics_frame
 var retail=g.get_node("V21_Separate_Fixtures_And_SKUs")
 var plan:Dictionary=g.read_json("res://source/v21/retail-plan.json");var hosts:Dictionary={}
 for item:Dictionary in plan.fixtures:hosts[item.id]=item
 var rows:Array=[];var world=g.get_world_3d().direct_space_state
 for d:Dictionary in plan.fixtures:
  var p=g.v3(d.p)-Vector3.UP*.02;rows.append({"id":d.id,"check":"fixture-floor-support","pass":way.floor_hit(p)})
 for d:Dictionary in plan.products:
  var p=g.v3(d.p)
  if hosts[d.host].model=="fixture_apparel_rail":p.y+=1.05
  var q=PhysicsRayQueryParameters3D.create(p+Vector3.UP*.045,p-Vector3.UP*.07,1);var hit=world.intersect_ray(q);rows.append({"id":d.id,"host":d.host,"check":"product-physical-shelf-support","pass":not hit.is_empty()and hit.normal.y>.60 and absf(hit.position.y-p.y)<.06})
 var routes:Array=g.read_json("res://source/v21/store-walk-routes.json");var route_rows:Array=[]
 for d:Dictionary in routes:
  var ok:bool=true;var floor_ok:bool=true;var contacts:Array=[]
  for i in range(d.points.size()-1):
   var a=g.v3(d.points[i]);var b=g.v3(d.points[i+1])
   if not way.sweep(a,b):
    ok=false;var query=PhysicsShapeQueryParameters3D.new();query.shape=way.capsule;query.transform=Transform3D(Basis.IDENTITY,a+Vector3.UP*.95);query.motion=b-a;query.margin=.008;query.collision_mask=1;var fraction=world.cast_motion(query);query.motion=Vector3.ZERO;query.transform.origin+=(b-a)*minf(1.,fraction[0]+.02)
    for hit:Dictionary in world.intersect_shape(query,6):contacts.append({"collider":str(hit.collider.name),"from":[a.x,a.y,a.z],"to":[b.x,b.y,b.z]})
   for j in range(ceili(a.distance_to(b)/.65)+1):
    if not way.floor_hit(a.lerp(b,float(j)/maxi(1,ceili(a.distance_to(b)/.65)))):floor_ok=false
  route_rows.append({"id":d.id,"store_id":d.store_id,"role":d.role,"contacts":contacts,"capsule_sweep":ok,"floor_support":floor_ok,"pass":ok and floor_ok})
 g.write_json("v21-fixture-products-physics.json",{"checks":rows,"failed":rows.filter(func(r):return not r["pass"]),"pipeline_complete":retail.has_meta("ready")and retail.stats.fixtures==plan.fixtures.size()and retail.stats.products==plan.products.size()and retail.stats.missing.is_empty(),"renderer_stats":retail.stats,"fixture_count":plan.fixtures.size(),"product_count":plan.products.size(),"human_playtest":false,"method":"Actual Godot collision geometry: host shelves use shared ConcavePolygonShape3D from the same imported meshes, not fixture bounding boxes."})
 g.write_json("v21-store-route-sweeps.json",{"routes":route_rows,"failed":route_rows.filter(func(r):return not r["pass"]),"human_playtest":false,"method":"Continuous .31m radius /1.80m capsule casts plus .65m floor samples; separate from actual CharacterBody walking."})
 g.write_json("v21-runtime-environment-assets.json",load("res://asset_usage_v21.gd").paths.keys())
 print("V21_QA fixtures/products ",rows.filter(func(r):return r["pass"]).size(),"/",rows.size()," routes ",route_rows.filter(func(r):return r["pass"]).size(),"/",route_rows.size());g.queue_free();await process_frame;await process_frame;quit()
