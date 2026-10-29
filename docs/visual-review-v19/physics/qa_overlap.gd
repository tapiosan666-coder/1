extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="v19-body-overlap-QA";root.add_child(g)
 while g.shoppers_v18==null or g.results.is_empty():await process_frame
 Engine.max_fps=0;g.player.set_physics_process(false);g.player.position=Vector3(325,0,-63);var failures:Array=[];var probes:int=0
 for tick in range(3600):
  await physics_frame
  if tick%120!=119:continue
  for actor in g.shoppers_v18.actors:
   var capsule=CapsuleShape3D.new();capsule.radius=maxf(.20,actor.shape_node.shape.radius-.025);capsule.height=actor.shape_node.shape.height-.05;var query=PhysicsShapeQueryParameters3D.new();query.shape=capsule;query.transform=actor.shape_node.global_transform;query.collision_mask=1;query.exclude=[actor.get_rid()];query.margin=0.
   var excluded:Array[RID]=[actor.get_rid()]
   for body in actor.get_collision_exceptions():excluded.append(body.get_rid())
   query.exclude=excluded
   var hits=g.get_world_3d().direct_space_state.intersect_shape(query,4);probes+=1
   if not hits.is_empty():
    var names:Array=[]
    for h in hits:names.append(str(h.collider.name))
    failures.append({"id":actor.record.id,"tick":tick,"activity":actor.activity,"position":[actor.position.x,actor.position.y,actor.position.z],"architecture_colliders":names})
 g.write_json("v19-body-overlap.json",{"probes":probes,"simulated_seconds":60,"failures":failures,"human_playtest":false,"method":"Actual capsule overlap queries, radius and height inset by 25mm, architecture collision layer1, designated seat self-contact excluded. Samples every2s; not exact animated skin-mesh intersection or continuous swept proof."});print("V19_BODY_OVERLAP ",failures.size(),"/",probes);quit()
