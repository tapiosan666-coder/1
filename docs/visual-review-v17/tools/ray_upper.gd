extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="v16-architectural-ray-audit";root.add_child(g)
 while g.ui==null or g.results.is_empty():await process_frame
 for i in range(3):await physics_frame
 var shots:Array=g.read_json("/workspace/FIND_YOURSELF-Site-v17/source/v17/compare-cameras.json")
 shots=shots.filter(func(q):return str(q.id)in["V17-B2-gallery","V17-B3-gallery"]);var rows:Array=[];var seen:Dictionary={}
 for shot:Dictionary in shots:
  if seen.has(shot.id):continue
  seen[shot.id]=true;var eye=g.v3(shot.eye);var look=g.v3(shot.look);var forward=look-eye;forward.y=0;forward=forward.normalized();var side=Vector3.UP.cross(forward)
  for offset:float in[-14.,-7.,0.,7.,14.]:
   var start=eye+side*offset;start.y=eye.y
   for angle:float in[-70.,-45.,-20.,0.,20.,45.,70.]:
    var direction=forward.rotated(Vector3.UP,deg_to_rad(angle));var ray=PhysicsRayQueryParameters3D.create(start,start+direction*65);ray.exclude=[g.player.get_rid()];var hit=g.get_world_3d().direct_space_state.intersect_ray(ray)
    if hit.is_empty()or abs(hit.normal.y)>.05:continue
    var body=hit.collider
    if not str(body.name).begins_with("Collision_")or str(body.name).contains("fixture"):continue
    var p:Vector3=hit.position;var n:Vector3=hit.normal;rows.append({"view":shot.id,"start":[start.x,start.y,start.z],"position":[p.x,p.y,p.z],"normal":[n.x,n.y,n.z],"collider":str(body.name),"distance":start.distance_to(p)})
 var f=FileAccess.open("/workspace/v17-review/v16-upper-wall-rays.json",FileAccess.WRITE);f.store_string(JSON.stringify({"runtime":g.results,"method":"Actual 3D collision rays from v16 camera neighbourhoods. Wall candidates, not a visual quality pass.","hits":rows},"  "));print("V17_BASELINE_RAY_HITS ",rows.size());quit()
