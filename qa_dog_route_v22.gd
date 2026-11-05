extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://Integrated_candidate_v22.tscn").instantiate();g.mode="v22-real-product-support";root.add_child(g)
 while g.results.is_empty():await process_frame
 while not g.get_node("V21_Route_Derived_Wayfinding").has_meta("ready"):await process_frame
 Engine.max_fps=0;g.player.set_physics_process(false);g.shoppers_v18.set_frozen(true);await physics_frame
 var way=g.get_node("V21_Route_Derived_Wayfinding");var grids:Dictionary=g.read_json("res://source/v22/navigation-grids.json");var design:Dictionary=g.read_json("res://source/v22/dog-access.json");var graph=load("res://nav_live_v21.gd").new();graph.setup(grids["combined-C-1F"],way)
 var row:Dictionary={"path":[design.route_world[0]],"target_point":design.target};var path:Array=graph.repair(row);var result:Dictionary={"path":path,"check":way.check_path(path)if path.size()>1 else{"pass":false,"reason":"No path"},"human_playtest":false,"method":"AStar on authored public floor, every tested edge filtered against actual capsule collision and floor support"};g.write_json("v22-dog-route-live.json",result);print("V22_DOG_LIVE ",path.size()," ",result.check);graph.clear();graph.way=null;g.queue_free();await process_frame;await process_frame;quit()
