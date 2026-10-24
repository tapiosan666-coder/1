extends SceneTree
func _initialize()->void:call_deferred("capture")
func capture()->void:
	var game=load("res://scenes/main.tscn").instantiate();root.add_child(game)
	await preload("res://scripts/realism_capture.gd").capture(game,"before" if "--before" in OS.get_cmdline_user_args() else "after")
	quit()
