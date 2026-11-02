extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="v16-facility-W-input";root.add_child(g)
 while g.ui==null or g.commons_v16==null or g.results.is_empty():await process_frame
 Engine.max_fps=0;g.staff.set_all_open(true);g.player.belt_enabled=false;var helper=load("res://walk_input_v16.gd").new();var checks:Array=[]
 var paths:Array=[
 ["A-information",[[339,0,-47],[347,0,-47],[354,0,-46.5]]],
 ["B-food-west",[[6,0,25],[6,0,10],[-1,0,10]]],
 ["B-food-east",[[6,0,13],[14,0,13],[17,0,10]]],
 ["C-kids-entrance",[[-105,0,-289.5],[-105,0,-297],[-103,0,-302]]],
 ["C-food-truck",[[-84,0,-289.5],[-84,0,-308],[-88,0,-320.5]]]]
 for row:Array in paths:checks.append(await helper.walk(g,row[0],row[1],-.25))
 var c=g.commons_v16;c.request_gate("C-DOG-outer")
 for i in range(90):await physics_frame
 checks.append(await helper.walk(g,"dog-outer-gate-entry",[[-118,0,-279.8],[-118,0,-275]],-.25))
 c.request_gate("C-DOG-outer")
 for i in range(90):await physics_frame
 checks.append({"id":"outer-closed-before-inner-opens","pass":abs(float(c.gates["C-DOG-outer"].angle))<.001})
 c.request_gate("C-DOG-inner")
 for i in range(90):await physics_frame
 checks.append(await helper.walk(g,"dog-inner-gate-entry",[[-118,0,-275],[-118,0,-270.7]],-.25))
 g.write_json("v16-facility-walk.json",{"checks":checks,"pass":checks.all(func(r):return r["pass"]),"human_playtest":false,"method":"Physical W input with automated steering and unchanged CharacterBody3D; actual gate animation and visible collisions; not human operation"});print("V16_FACILITY_WALK ",checks.filter(func(r):return r["pass"]).size(),"/",checks.size());quit()
