extends SceneTree
var g
func _initialize()->void:call_deferred("run")
func percentile(values:Array,fraction:float)->float:
 var sorted:Array=values.duplicate();sorted.sort();return float(sorted[mini(sorted.size()-1,floori((sorted.size()-1)*fraction))])if not sorted.is_empty()else 0.
func run()->void:
 var seconds:float=60.;var trial:String="1";var npc:bool=true;var use_vsync:bool=false;var side:String="v30";var out:String="user://v30-benchmark";var selected:String=""
 for a:String in OS.get_cmdline_user_args():
  if a.begins_with("--seconds="):seconds=maxf(60.,float(a.trim_prefix("--seconds=")))
  if a.begins_with("--trial="):trial=a.trim_prefix("--trial=")
  if a=="--NPC-off":npc=false
  if a=="--VSync-on":use_vsync=true
  if a.begins_with("--point="):selected=a.trim_prefix("--point=")
  if a.begins_with("--side="):side=a.trim_prefix("--side=")
  if a.begins_with("--out="):out=a.trim_prefix("--out=")
 if RenderingServer.get_video_adapter_name()=="":push_error("Rendering benchmark requires real display/renderer, never --headless.");quit(2);return
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out));RenderingServer.set_render_loop_enabled(false);var start:int=Time.get_ticks_usec();g=load("res://main.tscn").instantiate();g.mode="v30-benchmark";root.add_child(g)
 while g.results.is_empty():await process_frame
 if side!="v30":
  while not g.get_node("V294_Experience_Displays").has_meta("ready"):await process_frame
 var boot:float=(Time.get_ticks_usec()-start)/1000.;g.player.set_physics_process(false);g.player.input_enabled=false;g.player.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF;g.shoppers_v18.set_enabled(npc,true);g.hud.get_parent().visible=false;Engine.max_fps=144;DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED if use_vsync else DisplayServer.VSYNC_DISABLED)
 RenderingServer.viewport_set_measure_render_time(root.get_viewport_rid(),true)
 var poses:Array=JSON.parse_string(FileAccess.get_file_as_string("res://source/v30/benchmark-cameras.json"))if side=="v30"else[]
 if side!="v30":
  for a:String in OS.get_cmdline_user_args():
   if a.begins_with("--cameras="):poses=JSON.parse_string(FileAccess.get_file_as_string(a.trim_prefix("--cameras=")))
 var results:Array=[]
 for shot:Dictionary in poses:
  if selected!=""and shot.id!=selected:continue
  RenderingServer.set_render_loop_enabled(false);g.player.position=g.v3(shot.eye)-Vector3.UP*1.65;g.player.camera.position=Vector3.UP*1.65;g.player.camera.fov=float(shot.get("fov",72));g.player.camera.look_at(g.v3(shot.look));g.player.reset_physics_interpolation()
  if side=="v30":await g.get_node("V30_Runtime").settle();g.shoppers_v18.update_near()
  RenderingServer.set_render_loop_enabled(true);var warming:int=Time.get_ticks_msec()
  while Time.get_ticks_msec()-warming<10000:await process_frame;await RenderingServer.frame_post_draw
  var times:Array=[];var gpu:Array=[];var draws:Array=[];var primitive:Array=[];var nodes:Array=[];var began:int=Time.get_ticks_usec();var previous:int=began
  while Time.get_ticks_usec()-began<seconds*1000000.:
   await process_frame;await RenderingServer.frame_post_draw
   var now:int=Time.get_ticks_usec();times.append((now-previous)/1000.);previous=now;gpu.append(RenderingServer.viewport_get_measured_render_time_gpu(root.get_viewport_rid()));draws.append(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME));primitive.append(Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME));nodes.append(get_node_count())
  var duration:float=(Time.get_ticks_usec()-began)/1000000.;results.append({"point":shot,"seconds":duration,"frames":times.size(),"average_FPS":times.size()/duration,"median_FPS":1000./maxf(.001,percentile(times,.5)),"one_percent_low_FPS":1000./maxf(.001,percentile(times,.99)),"median_frame_ms":percentile(times,.5),"GPU_ms_median":percentile(gpu,.5),"DrawCalls_median":percentile(draws,.5),"primitives_median":percentile(primitive,.5),"nodes_median":percentile(nodes,.5),"memory_bytes":Performance.get_monitor(Performance.MEMORY_STATIC),"render_memory_bytes":Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED),"raw_frame_ms":times,"NPC_records":43,"NPC_enabled":npc,"resident_NPC":g.shoppers_v18.actors.size()});print("V30_BENCHMARK_POINT ",shot.id)
 var report:Dictionary={"side":side,"trial":trial,"OS":OS.get_name(),"GPU":RenderingServer.get_video_adapter_name(),"renderer":RenderingServer.get_current_rendering_method(),"VSync":use_vsync,"FPS_cap":144,"resolution":[root.size.x,root.size.y],"boot_ms":boot,"results":results}
 var path:String=out+"/"+side+"-"+trial+"-NPC"+str(npc)+"-VSync"+str(use_vsync)+".json";var file=FileAccess.open(path,FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close();print("V30_BENCHMARK_SAVED ",ProjectSettings.globalize_path(path));quit()
