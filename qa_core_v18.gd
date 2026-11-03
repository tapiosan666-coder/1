extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="v16-auto-collision-QA";root.add_child(g)
 while g.ui==null or g.commons_v16==null or g.results.is_empty():await process_frame
 Engine.max_fps=0
 g.shoppers_v18.set_enabled(false,true)
 var validator=load("res://validation_v16.gd").new()
 for category:String in["","ES","EV"]:
  g.only_shot=category;await validator.walk(g)
 print("V16_CORE_FINISHED");quit()
