extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://Integrated_candidate_v22.tscn").instantiate();g.mode="v22-real-product-support";root.add_child(g)
 while g.results.is_empty():await process_frame
 while not g.get_node("V21_Route_Derived_Wayfinding").has_meta("ready"):await process_frame
 Engine.max_fps=0;g.player.set_physics_process(false);g.shoppers_v18.set_frozen(true);await physics_frame
 var world=g.get_world_3d().direct_space_state;var rows:Array=[]
 for row:Dictionary in g.read_json("res://source/v22/shared-wall-queries.json"):
  var query=PhysicsRayQueryParameters3D.create(g.v3(row.a),g.v3(row.b),1);var hit=world.intersect_ray(query);var result=row.duplicate(true);result.blocked=not hit.is_empty();result.collider=str(hit.collider.name)if not hit.is_empty()else"NONE";result.missing_expected_partition=row.expected_source_solid and hit.is_empty();result.glazed_party_boundary=not hit.is_empty()and str(hit.collider.name).contains("glass")
  if result.glazed_party_boundary:
   query.exclude=[hit.collider.get_rid()];var second=world.intersect_ray(query);result.opaque_partition_behind_glass=not second.is_empty()and not str(second.collider.name).contains("glass");result.secondary_collider=str(second.collider.name)if not second.is_empty()else"NONE"
  rows.append(result)
 g.write_json("v22-shared-wall-physics.json",{"checks":rows,"missing_expected_partitions":rows.filter(func(r):return r.missing_expected_partition),"glazed_party_boundaries":rows.filter(func(r):return r.glazed_party_boundary),"human_playtest":false,"method":"Actual horizontal ray across exact store shared boundary at three longitudinal samples; .6m each side,1m above each floor. Not a complete facade/mesh seam certification."});print("V22_PARTY_WALLS ",rows.size()," missing ",rows.filter(func(r):return r.missing_expected_partition).size());g.queue_free();await process_frame;await process_frame;quit()
