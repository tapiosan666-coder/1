extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var out="/workspace/v18-review"
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--output="):out=arg.trim_prefix("--output=")
 var g=load("res://main.tscn").instantiate();g.mode="v18-fixed-state-pair-capture";root.add_child(g)
 while g.shoppers_v18==null or g.results.is_empty():await process_frame
 for i in range(3):await physics_frame
 g.shoppers_v18.restore_snapshot(g.read_json("res://source/v18/review-npc-state.json"));g.staff.set_all_open(true);g.player.set_physics_process(false);g.player.input_enabled=false;g.hud.visible=false;g.elevators.set_physics_process(false);g.animator.paused=true;g.animator.set_time(1.75);root.size=Vector2i(1920,1080);g.player.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF;g.player.camera.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF
 for enabled:bool in[false,true]:
  g.shoppers_v18.set_enabled(enabled,true);var directory=out+("/people"if enabled else"/after");DirAccess.make_dir_recursive_absolute(directory);var rows:Array=[]
  for s:Dictionary in g.read_json("res://source/v18/pair-cameras.json"):
   g.player.position=g.v3(s.eye)-Vector3(0,1.65,0);g.player.rotation=Vector3.ZERO;g.player.camera.position=Vector3(0,1.65,0);g.player.camera.fov=s.fov;g.player.camera.look_at(g.v3(s.look));g.player.reset_physics_interpolation()
   for i in range(2):await process_frame
   await RenderingServer.frame_post_draw
   var image=root.get_texture().get_image();image.save_png(directory+"/"+s.id+".png");rows.append(s.merged({"resolution":[image.get_width(),image.get_height()],"actual_Godot_Viewport":true,"NPC_enabled":enabled,"NPC_count":43 if enabled else 0,"warmup_frames":2,"actual_camera_global":[g.player.camera.global_position.x,g.player.camera.global_position.y,g.player.camera.global_position.z],"actual_look_direction":[-g.player.camera.global_basis.z.x,-g.player.camera.global_basis.z.y,-g.player.camera.global_basis.z.z]}));print("V18_PAIR ",s.id," NPC ",enabled)
  var path=directory+"/captures.json";var prior:Dictionary=g.read_json(path)if FileAccess.file_exists(path)else{};var ids=rows.map(func(r):return r.id);rows=prior.get("shots",[]).filter(func(r):return not r.id in ids)+rows;var f=FileAccess.open(path,FileAccess.WRITE);f.store_string(JSON.stringify({"runtime":g.results,"shots":rows,"NPC_enabled":enabled,"NPC_count":43,"snapshot_sha256":g.data_hash("res://source/v18/review-npc-state.json")},"  "))
 quit()
