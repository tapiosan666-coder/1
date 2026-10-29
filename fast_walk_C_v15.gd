extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="unthrottled-walk-QA";root.add_child(g)
 while g.ui==null:await process_frame
 for i in range(3):await physics_frame
 Engine.max_fps=0
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--single="):g.only_shot=arg.trim_prefix("--single=")
 await load("res://validation_C_v15.gd").new().walk(g)
