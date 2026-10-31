extends SceneTree
var g
var body:CapsuleShape3D
func _initialize():call_deferred("run")
func clear(p:Vector3)->bool:
 var world=g.get_world_3d().direct_space_state
 var floor_y:float=p.y
 for offset:Vector3 in[Vector3.ZERO,Vector3(.22,0,.22),Vector3(-.22,0,.22),Vector3(.22,0,-.22),Vector3(-.22,0,-.22)]:
  var ray=world.intersect_ray(PhysicsRayQueryParameters3D.create(p+offset+Vector3.UP*.20,p+offset-Vector3.UP*.18,1))
  if ray.is_empty()or ray.normal.y<.65 or ray.collider.has_meta("v21_fixture"):return false
  floor_y=maxf(floor_y,ray.position.y)
 var q=PhysicsShapeQueryParameters3D.new();q.shape=body;q.transform.origin=Vector3(p.x,floor_y+.95,p.z);q.margin=.01;q.collision_mask=1;return world.intersect_shape(q,1).is_empty()
func run():
 g=load("res://Integrated_candidate_v22.tscn").instantiate();g.mode="v25-retain-approaches";root.add_child(g)
 while g.results.is_empty():await process_frame
 while not g.get_node("V25_Supported_Decor").has_meta("ready"):await process_frame
 g.player.set_physics_process(false);g.shoppers_v18.set_frozen(true);body=CapsuleShape3D.new();body.radius=.34;body.height=1.8;await physics_frame
 var old:Dictionary=g.read_json("res://source/v24/shopping-physics.json");var equipment:Array=[];var failures:Array=[]
 for r:Dictionary in old.equipment:
  var row:Dictionary=r.duplicate(true);var okay:bool=clear(g.v3(r.approach))if not r.approach.is_empty()else false;row.standing_clear=okay
  if not okay:row.navigation_possible=false;row.usable_capacity=0;failures.append(row)
  row.approach_unchanged=true;row.human_playtest=false;equipment.append(row)
 old.equipment=equipment;old.unresolved_all_standing=failures;old.unresolved_original_155=equipment.filter(func(r):return r.previously_unresolved_v23 and not r.standing_clear);old.authoritative_layout_sha256=load("res://shopping_catalog_v25.gd").new().source_hash("res://source/v25/retail-plan.json");old.structural_pack_sha256=g.results.v22_structure_sha256;old.method="All inherited approach coordinates rechecked against v25 actual slab rays and r.34/h1.8 capsule; retained v24 connectivity additionally rewalked separately in v25, not assumed human validated.";g.write_json("v25-equipment-retained.json",old);print("V25_RETAINED_APPROACHES ",equipment.size()," failed ",failures.size());quit()
