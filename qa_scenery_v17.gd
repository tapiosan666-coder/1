extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="v17-new-fitout-QA";root.add_child(g)
 while g.ui==null or g.results.is_empty():await process_frame
 for i in range(3):await physics_frame
 var rows:Array=[];var physics=g.get_world_3d().direct_space_state;var exclude:Array[RID]=[g.player.get_rid()]
 for group:Node in g.scenery_v17.groups.values():
  for body in group.get_children():
   if body is StaticBody3D:exclude.append(body.get_rid())
 for d:Dictionary in g.scenery_v17.data.instances:
  if d.host!=null:continue
  var supported:int=0;var all_points:int=0
  for q:Array in d.footprint.coordinates[0]:
   all_points+=1;var ray=PhysicsRayQueryParameters3D.create(Vector3(q[0],d.p[1]+.20,q[1]),Vector3(q[0],d.p[1]-.20,q[1]));ray.exclude=exclude;var hit=physics.intersect_ray(ray)
   if not hit.is_empty()and abs(hit.position.y-d.p[1])<.12 and hit.normal.y>.9:supported+=1
  rows.append({"id":d.id,"test":"actual_native_floor_support_at_footprint_vertices","pass":supported==all_points,"supported":supported,"points":all_points})
 rows.append({"id":"all-assets-loaded","pass":g.scenery_v17.stats.missing.is_empty()and g.scenery_v17.stats.placements==g.scenery_v17.data.instances.size()})
 var fair_group=g.scenery_v17.groups.get("aichi_fair");g.player.position=Vector3(325,.06,-63);var off:bool=g.commons_v16.set_fair(false);rows.append({"id":"F11-new-advertising-hidden-with-fair","pass":off and fair_group!=null and not fair_group.visible});var on:bool=g.commons_v16.set_fair(true);rows.append({"id":"F11-new-advertising-restored-with-fair","pass":on and fair_group.visible})
 var ids:Array=g.scenery_v17.data.preserved_shop_ids;rows.append({"id":"480-original-shop-IDs","pass":ids.size()==480})
 var f=FileAccess.open("/workspace/v17-review/tests/scenery.json",FileAccess.WRITE);f.store_string(JSON.stringify({"runtime":g.results,"checks":rows,"passed":rows.filter(func(q):return q["pass"]).size(),"failed":rows.filter(func(q):return not q["pass"]).size(),"method":"Native physics support rays and automated event toggle; no human playtest"},"  "));print("V17_SCENERY_QA ",rows.filter(func(q):return q["pass"]).size(),"/",rows.size());quit()
