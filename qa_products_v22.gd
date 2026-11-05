extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://Integrated_candidate_v22.tscn").instantiate();g.mode="v22-real-product-support";root.add_child(g)
 while g.results.is_empty():await process_frame
 while not g.get_node("V21_Route_Derived_Wayfinding").has_meta("ready"):await process_frame
 Engine.max_fps=0;g.player.set_physics_process(false);g.shoppers_v18.set_frozen(true);await physics_frame
 var plan:Dictionary=g.read_json("res://source/v22/retail-plan.json");var bounds:Dictionary=g.read_json("res://source/v21/model-bounds.json");bounds.merge(g.read_json("res://source/v22/model-bounds.json"));var hosts:Dictionary={};var tested:int=0;var passed:int=0;var excluded:Array=[];var failed:Array=[];var corrections:Array=[];var world=g.get_world_3d().direct_space_state
 for r:Dictionary in plan.fixtures:hosts[r.id]=r
 for r:Dictionary in plan.products:
  var host:Dictionary=hosts[r.host]
  if host.model=="fixture_apparel_rail":excluded.append(r.id);continue
  var b:Dictionary=bounds[r.model];var a:float=deg_to_rad(float(r.get("pitch_deg",0.)));var lower:float=INF
  for y:float in[b.min[1],b.max[1]]:
   for z:float in[b.min[2],b.max[2]]:lower=minf(lower,cos(a)*y-sin(a)*z)
  var p=g.v3(r.p)+Vector3.UP*lower;var q=PhysicsRayQueryParameters3D.create(p+Vector3.UP*.035,p-Vector3.UP*.05,1);var hit=world.intersect_ray(q);var own:bool=not hit.is_empty()and hit.normal.y>.60 and hit.collider.has_meta("v21_fixture")and str(hit.collider.get_meta("v21_fixture").id)==str(r.host);tested+=1
  if own:passed+=1;continue
  var rescue=PhysicsRayQueryParameters3D.create(p+Vector3.UP*.24,p-Vector3.UP*.26,1);var alternative=world.intersect_ray(rescue);var can_snap:bool=not alternative.is_empty()and alternative.normal.y>.60 and alternative.collider.has_meta("v21_fixture")and str(alternative.collider.get_meta("v21_fixture").id)==str(r.host)
  if can_snap:corrections.append({"id":r.id,"host":r.host,"old_y":r.p[1],"new_y":float(r.p[1])+alternative.position.y-p.y+.003,"delta_y":alternative.position.y-p.y+.003,"method":"Actual own host mesh ray, maximum 26cm shelf correction"})
  failed.append({"id":r.id,"store_id":r.store_id,"host":r.host,"model":r.model,"at":[p.x,p.y,p.z],"actual_collider":str(hit.collider.name)if not hit.is_empty()else"NONE","own_host_snap_possible":can_snap})
 g.write_json("v22-product-support.json",{"tested":tested,"passed":passed,"failed":failed,"own_host_correction_candidates":corrections,"excluded_hanging_garments":excluded.size(),"human_playtest":false,"scope":"Actual point ray at merchandise bottom versus its named imported mesh host. Does not certify complete contact footprint or artwork quality."});print("V22_PRODUCT_SUPPORT ",passed,"/",tested," exempt garments ",excluded.size());g.queue_free();await process_frame;await process_frame;quit()
