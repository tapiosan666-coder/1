extends SceneTree
func _initialize()->void:call_deferred("run")
func clear(g,p:Vector3)->bool:
 var space=g.get_world_3d().direct_space_state;var ray=PhysicsRayQueryParameters3D.create(p+Vector3.UP*.8,p-Vector3.UP*.2,1);ray.exclude=[g.player.get_rid()];var hit=space.intersect_ray(ray)
 if hit.is_empty()or abs(hit.position.y)>.035:return false
 var query=PhysicsShapeQueryParameters3D.new();var cap=CapsuleShape3D.new();cap.radius=.39;cap.height=1.8;query.shape=cap;query.transform=Transform3D(Basis.IDENTITY,p+Vector3.UP*.92);query.collision_mask=1;query.exclude=[g.player.get_rid()];return space.intersect_shape(query,4).is_empty()
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="v18-actual-floor-placement";root.add_child(g)
 while g.shoppers_v18==null or g.results.is_empty():await process_frame
 g.shoppers_v18.set_enabled(false,true);g.player.set_physics_process(false)
 for i in range(3):await physics_frame
 var candidates:Array=[]
 for z:float in[-220.,-221.,-222.,-219.,-218.,-216.,-215.]:
  for x:float in[-92.,-91.,-93.,-90.,-94.]:
   var a=Vector3(x-.60,0,z);var b=Vector3(x+.60,0,z)
   if clear(g,a)and clear(g,b):candidates.append({"a":[a.x,0,a.z],"b":[b.x,0,b.z]})
 g.write_json("v18-ground-conversation-candidates.json",{"candidates":candidates,"method":"Actual downward floor ray plus 0.39m-radius capsule overlap at 1.8m height. Reject planter tops above 35mm."});print("GROUND_CANDIDATES ",JSON.stringify(candidates));quit()
