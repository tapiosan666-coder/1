extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var out:String="res://evidence/v21-performance";var camera_path:String="res://source/v21/review-cameras.json";var state_path:String="res://source/v21/review-npc-state.json"
 for a:String in OS.get_cmdline_user_args():
  if a.begins_with("--output="):out=a.trim_prefix("--output=")
  if a.begins_with("--cameras="):camera_path=a.trim_prefix("--cameras=")
  if a.begins_with("--npc-state="):state_path=a.trim_prefix("--npc-state=")
 DirAccess.make_dir_recursive_absolute(out);var g=load("res://main.tscn").instantiate();g.mode="v21-software-performance";root.add_child(g)
 while g.results.is_empty():await process_frame
 if g.has_node("V21_Route_Derived_Wayfinding"):
  while not g.get_node("V21_Route_Derived_Wayfinding").has_meta("ready"):await process_frame
 root.size=Vector2i(1920,1080);Engine.max_fps=144;g.player.set_physics_process(false);g.player.input_enabled=false;g.player.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF;g.hud.get_parent().visible=false;g.animator.paused=true;g.elevators.set_physics_process(false);var cameras:Array=JSON.parse_string(FileAccess.get_file_as_string(camera_path));var snapshot:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(state_path));var rows:Array=[]
 for id:String in["A1F-007-entry","NAV-B-1F"]:
  var shot:Dictionary=cameras.filter(func(c):return c.id==id)[0];g.player.position=g.v3(shot.eye)-Vector3.UP*1.65;g.player.rotation=Vector3.ZERO;g.player.camera.position=Vector3.UP*1.65;g.player.camera.fov=shot.fov;g.player.camera.look_at(g.v3(shot.look));g.player.reset_physics_interpolation()
  for enabled:bool in[false,true]:
   g.shoppers_v18.restore_snapshot(snapshot);g.shoppers_v18.set_mode("v20",true);g.shoppers_v18.set_enabled(enabled,true);g.shoppers_v18.set_frozen(not enabled)
   for tick in range(2):await process_frame
   var samples:Array=[];var simulated_before:float=g.shoppers_v18.simulated_seconds
   for tick in range(3):
    var start:int=Time.get_ticks_usec();await process_frame;await RenderingServer.frame_post_draw;samples.append({"frame_ms":(Time.get_ticks_usec()-start)/1000.,"draw_calls":Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),"primitives":Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),"static_memory":Performance.get_monitor(Performance.MEMORY_STATIC),"video_memory":Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED),"texture_memory":Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED),"buffer_memory":Performance.get_monitor(Performance.RENDER_BUFFER_MEM_USED)})
   rows.append({"camera_id":id,"NPC_enabled":enabled,"global_NPC_count":43 if enabled else 0,"samples":samples,"simulation_seconds_during_samples":g.shoppers_v18.simulated_seconds-simulated_before});print("V21_PERF ",id," ",enabled," ",JSON.stringify(samples))
   var f=FileAccess.open(out+"/performance.json",FileAccess.WRITE);f.store_string(JSON.stringify({"adapter":RenderingServer.get_video_adapter_name(),"resolution":[1920,1080],"measurements":rows,"max_fps":144,"VSync":DisplayServer.window_get_vsync_mode(),"Windows_GPU":false,"144FPS_verified":false,"human_playtest":false,"steady_state_benchmark":false,"caveat":"Linux software Vulkan,3 sampled frames/case after2 warmup. Global actors43 does not mean all43 visible in camera. Moving actors advance real physics. CPU/cache order and limited samples affect times; total process memory includes cached resources. Not a Windows GPU benchmark."},"  "))
 g.queue_free();await process_frame;await process_frame;quit()
