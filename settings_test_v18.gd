extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var cls=load("res://settings_v7.gd");var s=cls.new();s.config_path="user://settings-automated-test-v7.cfg";DirAccess.remove_absolute(ProjectSettings.globalize_path(s.config_path));s.restore();var checks:Array=[]
 checks.append({"id":"defaults","pass":s.resolution_index==0 and s.fps_limit==144 and s.vsync and Engine.physics_ticks_per_second==60,"observed":s.snapshot()})
 for resolution in range(3):
  for limit in s.LIMITS:
   for sync in [true,false]:
    s.resolution_index=resolution;s.fps_limit=limit;s.vsync=sync;s.apply();var restored=cls.new();restored.config_path=s.config_path;restored.restore();checks.append({"id":"save-restore-%s-%s-%s"%[resolution,limit,sync],"pass":restored.resolution_index==resolution and restored.fps_limit==limit and restored.vsync==sync and Engine.physics_ticks_per_second==60,"observed":restored.snapshot()})
 var f=FileAccess.open("/workspace/v18-review/physics/settings-save-restore-v18.json",FileAccess.WRITE);f.store_string(JSON.stringify({"checks":checks,"headless":DisplayServer.get_name()=="headless","actual_cross_process_restore":"requires second command","not_ui_screenshot_test":true},"  "));print("SETTINGS_CHECKS ",checks.size());quit()
