extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="v18-obstacle-diagnostic";root.add_child(g)
 while g.shoppers_v18==null:await process_frame
 g.shoppers_v18.set_enabled(false,true);g.player.set_physics_process(false);var rows:Array=[]
 for node in g.get_children():
  if not node is StaticBody3D or not str(node.name).begins_with("Collision_"):continue
  for child in node.get_children():
   if not child is CollisionShape3D or not child.shape is ConcavePolygonShape3D:continue
   var faces:PackedVector3Array=child.shape.get_faces()
   for i in range(0,faces.size(),3):
    var t:Array=[faces[i],faces[i+1],faces[i+2]]
    for p:Vector3 in[Vector3(-60.47,.2,-7.55),Vector3(37.53,.5,38.11),Vector3(383.27,.5,-57.10)]:
     var box=AABB(t[0],Vector3.ZERO);box=box.expand(t[1]);box=box.expand(t[2])
     if box.grow(.40).has_point(p):rows.append({"body":str(node.name),"point":str(p),"triangle":[[t[0].x,t[0].y,t[0].z],[t[1].x,t[1].y,t[1].z],[t[2].x,t[2].y,t[2].z]]})
 g.write_json("v18-obstacle-triangles.json",rows);print("OBSTACLE_TRIANGLES ",rows.size());quit()
