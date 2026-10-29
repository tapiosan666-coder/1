extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="v19-short-software-performance";root.add_child(g)
 while g.shoppers_v18==null or g.results.is_empty():await process_frame
 root.size=Vector2i(1920,1080);Engine.max_fps=144;g.player.set_physics_process(false);g.player.input_enabled=false;g.elevators.set_physics_process(false);g.hud.visible=false;g.animator.paused=true
 g.player.position=Vector3(351.9,0,-23.2);g.player.camera.fov=68;g.player.camera.look_at(Vector3(355.5,1.,-20.3));g.player.reset_physics_interpolation();var rows:Array=[]
 for condition:String in["none","v18_43","female_1","v19_43_moving"]:
  g.shoppers_v18.set_mode("baseline"if condition=="v18_43"else"female_only"if condition=="female_1"else"v19",true);g.shoppers_v18.set_enabled(condition!="none",true);g.shoppers_v18.set_frozen(condition!="v19_43_moving")
  for i in range(2):await process_frame
  var frames:Array=[];var draws:Array=[];var tris:Array=[];var before:float=g.shoppers_v18.simulated_seconds
  for i in range(4):
   var start=Time.get_ticks_usec();await process_frame;await RenderingServer.frame_post_draw
   frames.append((Time.get_ticks_usec()-start)/1000.);draws.append(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME));tris.append(Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME))
  var sorted=frames.duplicate();sorted.sort();rows.append({"condition":condition,"sample_frames":4,"frame_ms":frames,"median_frame_ms":(sorted[1]+sorted[2])/2.,"draw_calls":draws,"rendered_primitives":tris,"static_memory_bytes":Performance.get_monitor(Performance.MEMORY_STATIC),"video_memory_bytes":Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED),"texture_memory_bytes":Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED),"buffer_memory_bytes":Performance.get_monitor(Performance.RENDER_BUFFER_MEM_USED),"physics_process_seconds":Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS),"simulation_seconds_during_samples":g.shoppers_v18.simulated_seconds-before,"frozen":condition!="v19_43_moving"});print("V19_PERF ",condition," ",rows[-1].median_frame_ms)
  g.write_json("v19-render-performance.json",{"measurements":rows,"resolution":[1920,1080],"adapter":RenderingServer.get_video_adapter_name(),"renderer":RenderingServer.get_current_rendering_method(),"Windows_GPU":false,"144FPS_verified":false,"human_playtest":false,"steady_state_benchmark":false,"caveat":"Only four software-Vulkan frames per condition; cold/warm cache order and CPU contention affect results. Moving case actually advances physics; this is not a Windows GPU benchmark. Earlier baseline actor resources stay cached in later cases, memory is total process, not isolated per-model delta."})
 quit()
