extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="v15-store-input";root.add_child(g)
 while g.ui==null:await process_frame
 Engine.max_fps=0;g.staff.set_all_open(true);var checks:Array=[]
 for row:Dictionary in g.read_json("res://source/v15/service-paths.json"):
  if not row.pass_geometry:checks.append({"id":row.id,"pass":false,"reason":"No geometric route"});continue
  await g.settle(g.v3(row.points[0]));var r:Dictionary=await g.walk_points(row.points,4.3);r.id=row.id;checks.append(r);print("V15_SERVICE_WALK ",row.id," ",r["pass"])
 var file=FileAccess.open("res://evidence/v15/service-walk.json",FileAccess.WRITE);file.store_string(JSON.stringify({"checks":checks,"passed":checks.filter(func(c):return c["pass"]).size(),"failed":checks.filter(func(c):return not c["pass"]).size(),"human_playtest":false,"method":"Actual CharacterBody3D collision, automated waypoint steering; not human input"},"  "));quit()
