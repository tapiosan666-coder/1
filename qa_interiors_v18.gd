extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="v18-interior-physics";root.add_child(g)
 while g.shoppers_v18==null or g.results.is_empty():await process_frame
 g.shoppers_v18.set_enabled(false,true);Engine.max_fps=0;g.staff.set_all_open(true);var checks:Array=[]
 for r:Dictionary in g.read_json("res://source/v18/interior-routes.json"):
  await g.settle(g.v3(r.points[0]));var result=await g.walk_points(r.points,2.);result.id=r.id;checks.append(result);print("V18_INTERIOR ",r.id," ",result.pass)
 g.write_json("v18-interior-physics.json",{"checks":checks,"human_playtest":false,"method":"Actual player CharacterBody3D collision traversal of planned shop department paths, NPC off","runtime":g.results});quit()
