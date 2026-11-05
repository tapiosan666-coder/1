extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="roof-support-v14";root.add_child(g)
 while g.ui==null:await process_frame
 Engine.max_fps=0
 for i in range(3):await physics_frame
 var data=g.read_json("res://source/v14/roof-planting.json");var checks:Array=[]
 for d:Dictionary in data.instances:
  var p=g.v3(d.p);var hit=g.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(p+Vector3.UP*1.5,p-Vector3.UP*.1))
  var okay:bool=not hit.is_empty()and hit.position.y>=16.39 and hit.position.y<=17.10
  checks.append({"bed":d.bed_id,"p":d.p,"pass":okay,"top_y":hit.position.y if not hit.is_empty()else -999})
  if okay:d.p[1]=hit.position.y+.012
 var f=FileAccess.open("res://source/v14/roof-planting.json",FileAccess.WRITE);f.store_string(JSON.stringify(data,"  "));g.write_json("roof-support.json",{"checks":checks,"passed":checks.filter(func(c):return c["pass"]).size(),"failed":checks.filter(func(c):return not c["pass"]).size(),"method":"Existing physics surface downward ray, no new support added; not structural load certification"});quit()
