extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var out="/workspace/v20-review/viewer"
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--output="):out=arg.trim_prefix("--output=")
 DirAccess.make_dir_recursive_absolute(out);root.size=Vector2i(1920,1080);var v=load("res://Character_Review_v20.tscn").instantiate();root.add_child(v)
 for i in range(3):await process_frame
 var checks:Array=[]
 for clip:String in["Idle","Walk","Stop","TurnLeft","TurnRight","SitDown","SitIdle","StandUp","Browse"]:
  v.select_motion(clip);v.hero.pose(clip,.2,.25,.016,.01,false);checks.append({"id":"viewer-"+clip,"actual_clip":v.hero.state().actual_player_clip,"pass":v.hero.current_clip==clip})
 v.select_motion("SitIdle");v.playing=false;v.hero.deterministic_pose("SitIdle",.5);v.toggle_variant();checks.append({"id":"paused-v19-comparison","pass":v.hero.state().variant=="v19"and v.hero.state().hip_y_local_m<.65});v.toggle_variant();v.select_motion("Idle");v.hero.deterministic_pose("Idle",.3);v.view(0)
 for i in range(2):await process_frame
 await RenderingServer.frame_post_draw
 root.get_texture().get_image().save_png(out+"/interactive-viewer.png");var panel:Control=v.label.get_parent().get_parent();checks.append({"id":"UI-fits-1920x1080","pass":panel.position.x+panel.size.x<1920 and panel.position.y+panel.size.y<1080,"panel_size":[panel.size.x,panel.size.y]});var f=FileAccess.open(out+"/viewer.json",FileAccess.WRITE);f.store_string(JSON.stringify({"checks":checks,"human_playtest":false},"  "));print("FY20_VIEWER ",checks.filter(func(r):return r["pass"]).size(),"/",checks.size());quit()
