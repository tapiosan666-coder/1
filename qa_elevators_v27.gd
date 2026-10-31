extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="v22-EV-actual-rides";root.add_child(g)
 while g.results.is_empty():await process_frame
 while not g.get_node("V21_Route_Derived_Wayfinding").has_meta("ready"):await process_frame
 while not g.get_node("V27_Architecture").has_meta("ready"):await process_frame
 Engine.max_fps=0;g.shoppers_v18.set_frozen(true);g.only_shot="EV";await load("res://validation_elevators_v27.gd").new().walk(g)
