extends SceneTree
func _initialize()->void:
 var setting=load("res://settings_v7.gd").new();setting.config_path="user://v17-restart-proof.cfg"
 if "--write"in OS.get_cmdline_user_args():
  setting.resolution_index=1;setting.fps_limit=120;setting.vsync=false;setting.apply();print("V17_SETTINGS_RESTART_WRITE");quit();return
 setting.restore();var okay:bool=setting.resolution_index==1 and setting.fps_limit==120 and not setting.vsync and Engine.physics_ticks_per_second==60
 var f=FileAccess.open("/workspace/v17-review/tests/settings-cross-process.json",FileAccess.WRITE);f.store_string(JSON.stringify({"checks":[{"id":"settings-restored-in-second-Godot-process","pass":okay,"observed":setting.snapshot()}],"method":"Write then exit one Godot process; restore in a second process using an isolated test config","human_playtest":false},"  "));DirAccess.remove_absolute(ProjectSettings.globalize_path(setting.config_path));print("V17_SETTINGS_RESTART_RESTORE ",okay);quit(0 if okay else 2)
