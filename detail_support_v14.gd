extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="detail-floor-check";root.add_child(g)
 while g.ui==null:await process_frame
 for i in range(3):await physics_frame
 var rows:Array=[]
 for d:Dictionary in g.read_json("res://source/v14/detail-cameras.json"):
  var p=g.v3(d.eye)-Vector3(0,1.65,0);var ray=PhysicsRayQueryParameters3D.create(p+Vector3.UP*.8,p-Vector3.UP*.4);ray.exclude=[g.player.get_rid()];var h=g.get_world_3d().direct_space_state.intersect_ray(ray);rows.append({"id":d.id,"pass":not h.is_empty()and abs(h.position.y-p.y)<.15,"surface_y":h.position.y if not h.is_empty()else -999,"floor_expected":p.y})
 g.write_json("detail-floor-check.json",{"checks":rows,"failed":rows.filter(func(q):return not q["pass"]).size(),"human_walk":false});quit()
