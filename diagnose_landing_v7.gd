extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();root.add_child(g)
 while g.ui==null:await physics_frame
 g.staff.set_all_open(true);g.player.input_enabled=false;g.player.belt_enabled=false
 var start=Vector3(98.08794,.00094,-357.1863);var goal=Vector3(98.12835,0,-359.3656);await g.settle(start)
 for h in [.15,.9,1.65,2.0]:
  var ray=PhysicsRayQueryParameters3D.create(start+Vector3.UP*h,goal+Vector3.UP*h);ray.exclude=[g.player.get_rid()];var hit=g.get_world_3d().direct_space_state.intersect_ray(ray);print("LANDING_RAY ",h," ",JSON.stringify({"name":str(hit.get("collider","none")),"position":str(hit.get("position")),"normal":str(hit.get("normal"))}))
 g.player.auto_target=goal;g.player.auto_active=true;g.player.auto_speed=5.
 for i in range(20):
  await physics_frame
  if i%4==0:print("LANDING_MOVE ",i," ",JSON.stringify({"position":str(g.player.position),"velocity":str(g.player.velocity),"contacts":g.collision_diagnostics()}))
 quit()
