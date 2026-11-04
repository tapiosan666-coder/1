extends SceneTree
var g
func _initialize()->void:call_deferred("run")
func run()->void:
 var before:bool=OS.get_cmdline_user_args().has("--v28-baseline");var out:String="res://evidence/v29-review";var select:Array=[]
 for a:String in OS.get_cmdline_user_args():
  if a.begins_with("--review-output="):out=a.trim_prefix("--review-output=")
  if a.begins_with("--select="):select=Array(a.trim_prefix("--select=").split(","))
 g=load("res://main.tscn").instantiate();g.mode="v29-review";root.add_child(g)
 while g.results.is_empty():await process_frame
 while not g.get_node("V28_Architecture").has_meta("ready"):await process_frame
 if not before:
  while not g.get_node("V29_Continuous_1F").has_meta("ready"):await process_frame
 var side:String="before"if before else"after";DirAccess.make_dir_recursive_absolute(out+"/"+side);DirAccess.make_dir_recursive_absolute(out+"/data")
 root.size=Vector2i(1920,1080);g.shoppers_v18.set_frozen(true);g.player.set_physics_process(false);g.player.input_enabled=false;g.player.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF;g.hud.get_parent().visible=false;g.animator.paused=true;g.elevators.set_physics_process(false)
 if OS.get_cmdline_user_args().has("--targeted-inspection"):
  load("res://qa_inspection_v29.gd").new().run(g,out,before)
 var rows:Array=[]
 for s:Dictionary in g.read_json("res://source/v29/review-cameras.json"):
  if not select.is_empty()and not s.id in select:continue
  g.player.global_position=g.v3(s.eye)-Vector3.UP*1.65;g.player.rotation=Vector3.ZERO;g.player.camera.position=Vector3.UP*1.65;g.player.camera.fov=s.fov;g.player.camera.look_at(g.v3(s.look));g.player.reset_physics_interpolation()
  var frames:Array=[]
  g.player.camera.force_update_transform()
  for i in 1:
   var t:int=Time.get_ticks_usec();await process_frame;await RenderingServer.frame_post_draw;frames.append((Time.get_ticks_usec()-t)/1000.)
  var file:String=out+"/"+side+"/"+str(s.id)+".jpg";var status:int=root.get_texture().get_image().save_jpg(file,.94)
  rows.append({"camera":s,"file":side+"/"+str(s.id)+".jpg","save_error":status,"frame_ms":frames,"draw_calls":Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),"primitives":Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),"CPU_process_ms":Performance.get_monitor(Performance.TIME_PROCESS)*1000.,"physics_process_ms":Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS)*1000.,"static_memory_bytes":Performance.get_monitor(Performance.MEMORY_STATIC),"video_memory_bytes":Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED),"objects":Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME)})
  print("V29_CAPTURE ",side," ",s.id)
 var report:Dictionary={"side":side,"rows":rows,"actual_Godot_viewport":true,"resolution":[1920,1080],"adapter":RenderingServer.get_video_adapter_name(),"engine":Engine.get_version_info(),"human_playtest":false,"Windows_GPU_measured":false,"environment":g.get_node("V29_Continuous_1F").report if not before else{},"settings":{"cap":Engine.max_fps,"vsync":DisplayServer.window_get_vsync_mode(),"C":g.c_open_proposal,"B_ES":g.es_site_proposal,"continuous":g.a_continuous_v22}}
 var f=FileAccess.open(out+"/data/"+side+"-native.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f=null
 g.queue_free();await process_frame;await process_frame;quit()
