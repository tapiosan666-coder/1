extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var out="res://evidence/v12/es-transfer-viewport"
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--output="):out=arg.trim_prefix("--output=")
 DirAccess.make_dir_recursive_absolute(out);var g=load("res://ES_transfer_study_v12.tscn").instantiate();root.add_child(g)
 while g.player==null:await process_frame
 g.player.set_physics_process(false);g.animator.paused=true;g.animator.set_time(1.75);root.size=Vector2i(1920,1080)
 var shots=[{"id":"ES-study-1F","eye":Vector3(10.2,1.65,8.8),"look":Vector3(-2.5,5.5,-1)},{"id":"ES-study-transfer-2F","eye":Vector3(-10.2,7.175,8.8),"look":Vector3(0,8.5,1)}];var records:Array=[]
 for s:Dictionary in shots:
  g.player.position=s.eye-Vector3(0,1.65,0);g.player.rotation=Vector3.ZERO;g.player.camera.rotation=Vector3.ZERO;g.player.camera.look_at(s.look);g.player.reset_physics_interpolation();var timing:Array=[]
  for i in range(4):
   var start=Time.get_ticks_usec();await process_frame;timing.append((Time.get_ticks_usec()-start)/1000.0)
  await RenderingServer.frame_post_draw
  root.get_texture().get_image().save_png(out+"/"+s.id+".png");records.append({"id":s.id,"eye":[s.eye.x,s.eye.y,s.eye.z],"look":[s.look.x,s.look.y,s.look.z],"resolution":[1920,1080],"actual_Godot_Viewport":true,"adapter":RenderingServer.get_video_adapter_name(),"four_frame_times_ms_not_benchmark":timing});print("TRANSFER_CAPTURE ",s.id)
 var f=FileAccess.open(out+"/captures.json",FileAccess.WRITE);f.store_string(JSON.stringify(records,"  "));quit()
