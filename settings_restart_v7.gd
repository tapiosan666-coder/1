extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var s=load("res://settings_v7.gd").new();s.config_path="user://settings-automated-test-v7.cfg";s.restore();var result={"fresh_process":true,"pass":s.resolution_index==2 and s.fps_limit==0 and not s.vsync,"observed":s.snapshot()};var f=FileAccess.open("res://evidence/settings-fresh-process-v7.json",FileAccess.WRITE);f.store_string(JSON.stringify(result,"  "));print("SETTINGS_RESTART ",result);quit()
