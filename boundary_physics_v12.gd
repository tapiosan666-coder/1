extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="external-audit";root.add_child(g)
 while g.ui==null:await process_frame
 g.player.set_physics_process(false);g.staff.set_all_open(false)
 for i in range(5):await physics_frame
 var data=g.read_json("res://source/v12/boundary-audit-before.json");var checks:Array=[];var failures:Array=[];var total:int=0
 for shop:Dictionary in data.stores:
  if shop.floor=="RF":continue
  var n:int=0
  for s:Array in shop.samples:
   # Inspect two diagonal rays through the boundary point so a grazing ray is not mistaken for an open passage.
   var p=Vector3(s[0],s[1],s[2]);var hit:bool=false
   for direction:Vector3 in[Vector3(1,0,0),Vector3(0,0,1)]:
    var q=PhysicsRayQueryParameters3D.create(p-direction*.34,p+direction*.34);q.exclude=[g.player.get_rid()];q.hit_back_faces=true
    if not g.get_world_3d().direct_space_state.intersect_ray(q).is_empty():hit=true;break
   total+=1
   if not hit:n+=1
  var r={"id":shop.id,"samples":shop.samples.size(),"uncovered":n};checks.append(r)
  if n>0:failures.append(r)
 g.write_json("boundary-physics-v12.json",{"method":"Godot direct_space_state rays across actual visible-boundary sample points; excludes declared customer/staff openings. Two perpendicular rays, 0.68m each. No human visual approval.","samples":total,"stores":checks.size(),"flags":failures,"checks":checks,"human_playtest":false});print("BOUNDARY_GODOT ",total," samples; ",failures.size()," flagged stores");quit()
