extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var out="/tmp/v11-viewports";var shots_path="";var only:String=""
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--capture-shots="):shots_path=arg.trim_prefix("--capture-shots=")
  if arg.begins_with("--output="):out=arg.trim_prefix("--output=")
  if arg.begins_with("--only="):only=arg.trim_prefix("--only=")
 DirAccess.make_dir_recursive_absolute(out)
 var variant:bool="--c-open-proposal"in OS.get_cmdline_user_args();var g=load("res://C_proposal_v12.tscn"if variant else"res://main.tscn").instantiate();g.mode="external-review";root.add_child(g)
 while g.ui==null:await process_frame
 for i in range(3):await physics_frame
 g.staff.set_all_open(true);g.player.set_physics_process(false);g.player.input_enabled=false;g.hud.visible=false;g.elevators.set_physics_process(false);g.animator.paused=true;g.animator.set_time(1.75);root.size=Vector2i(1920,1080)
 var rows:Array=[]
 for s:Dictionary in JSON.parse_string(FileAccess.get_file_as_string(shots_path)):
  if only!=""and not str(s.id).contains(only):continue
  g.player.position=g.v3(s.eye)-Vector3(0,1.65,0);g.player.rotation=Vector3.ZERO;g.player.camera.position=Vector3(0,1.65,0);g.player.camera.fov=s.fov;g.player.camera.look_at(g.v3(s.look));g.player.reset_physics_interpolation()
  for i in range(4):await process_frame
  await RenderingServer.frame_post_draw
  var image=root.get_texture().get_image();image.save_png(out+"/"+str(s.id)+".png");rows.append(s.merged({"resolution":[image.get_width(),image.get_height()],"actual_Godot_Viewport":true,"warmup_frames":4}));print("REVIEW_CAPTURE ",s.id)
 var f=FileAccess.open(out+"/captures.json",FileAccess.WRITE);f.store_string(JSON.stringify({"runtime":g.results,"shots":rows},"  "));quit()
