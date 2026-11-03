extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var out="/tmp/v11-viewports";var shots_path="";var only:String=""
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--capture-shots="):shots_path=arg.trim_prefix("--capture-shots=")
  if arg.begins_with("--output="):out=arg.trim_prefix("--output=")
  if arg.begins_with("--only="):only=arg.trim_prefix("--only=")
 DirAccess.make_dir_recursive_absolute(out)
 var variant:bool="--c-open-proposal"in OS.get_cmdline_user_args();var es:bool="--es-site-proposal"in OS.get_cmdline_user_args();var g=load("res://ES_site_proposal_v15.tscn"if es else"res://C_proposal_v12.tscn"if variant else"res://main.tscn").instantiate();g.mode="external-review";root.add_child(g)
 while g.ui==null:await process_frame
 for i in range(3):await physics_frame
 if g.get("shoppers_v18")!=null:
  var state_path="res://source/v19/review-npc-state.json"
  if FileAccess.file_exists(state_path):g.shoppers_v18.restore_snapshot(JSON.parse_string(FileAccess.get_file_as_string(state_path)))
  else:g.shoppers_v18.set_frozen(true)
  g.shoppers_v18.set_enabled(not "--shoppers-off"in OS.get_cmdline_user_args(),true)
 g.staff.set_all_open(true);g.player.set_physics_process(false);g.player.input_enabled=false;g.hud.visible=false;g.elevators.set_physics_process(false);g.animator.paused=true;g.animator.set_time(1.75);root.size=Vector2i(1920,1080);g.player.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF;g.player.camera.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF
 var rows:Array=[]
 for s:Dictionary in JSON.parse_string(FileAccess.get_file_as_string(shots_path)):
  if only!=""and not str(s.id).contains(only):continue
  g.player.position=g.v3(s.eye)-Vector3(0,1.65,0);g.player.rotation=Vector3.ZERO;g.player.camera.position=Vector3(0,1.65,0);g.player.camera.fov=s.fov;g.player.camera.look_at(g.v3(s.look));g.player.reset_physics_interpolation()
  for i in range(2):await process_frame
  await RenderingServer.frame_post_draw
  var image=root.get_texture().get_image();image.save_png(out+"/"+str(s.id)+".png");rows.append(s.merged({"resolution":[image.get_width(),image.get_height()],"actual_Godot_Viewport":true,"warmup_frames":2,"reference_fps_1s_window":Engine.get_frames_per_second(),"performance_note":"Software Vulkan llvmpipe, capture window only; includes warmup, not steady-state Windows GPU FPS", "draw_calls":Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),"primitives":Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),"actual_camera_global":[g.player.camera.global_position.x,g.player.camera.global_position.y,g.player.camera.global_position.z],"actual_look_direction":[-g.player.camera.global_basis.z.x,-g.player.camera.global_basis.z.y,-g.player.camera.global_basis.z.z]}));print("REVIEW_CAPTURE ",s.id)
 if FileAccess.file_exists(out+"/captures.json"):
  var prior:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(out+"/captures.json"));var changed_ids:Array=rows.map(func(r):return r.id)
  rows=prior.get("shots",[]).filter(func(r):return not str(r.id)in changed_ids)+rows
 var f=FileAccess.open(out+"/captures.json",FileAccess.WRITE);f.store_string(JSON.stringify({"runtime":g.results,"NPC_enabled":g.shoppers_v18.enabled if g.get("shoppers_v18")!=null else false,"NPC_count":g.shoppers_v18.actors.size()if g.get("shoppers_v18")!=null else 0,"shots":rows},"  "));quit()
