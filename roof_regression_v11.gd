extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();root.add_child(g)
 while g.ui==null:await process_frame
 g.player.belt_enabled=false;g.player.input_enabled=false;g.staff.set_all_open(true);var checks:Array=[]
 for r:Dictionary in g.read_json("res://source/physical-routes-v11.json"):
  if not r.points.any(func(p):return abs(float(p[1])-16.4)<.1):continue
  await g.settle(g.v3(r.points[0]));var result:Dictionary=await g.walk_points(r.points,5.0);result["id"]=r.id;checks.append(result);print("ROOF_REGRESSION ",r.id," ",result["pass"])
 g.write_json("roof-regression.json",{"checks":checks,"passed":checks.filter(func(c):return c["pass"]).size(),"failed":checks.filter(func(c):return not c["pass"]).size(),"human_playtest":false,"runtime":g.results});quit()
