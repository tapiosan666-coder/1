extends SceneTree
var g
func _initialize()->void:call_deferred("run")
func run()->void:
 var before:bool=OS.get_cmdline_user_args().has("--v291-baseline");var out:String="res://evidence/v292-review";var select:Array=[]
 for a:String in OS.get_cmdline_user_args():
  if a.begins_with("--review-output="):out=a.trim_prefix("--review-output=")
  if a.begins_with("--select="):select=Array(a.trim_prefix("--select=").split(","))
 g=load("res://main.tscn").instantiate();g.mode="v292-review";root.add_child(g)
 while g.results.is_empty():await process_frame
 while not g.get_node("V291_Retail_Continuation").has_meta("ready"):await process_frame
 if not before:
  while not g.get_node("V292_People_Campaigns").has_meta("ready"):await process_frame
 var side:String="before"if before else"after";DirAccess.make_dir_recursive_absolute(out+"/"+side);DirAccess.make_dir_recursive_absolute(out+"/data")
 root.size=Vector2i(1920,1080);g.shoppers_v18.set_frozen(true);g.player.set_physics_process(false);g.player.input_enabled=false;g.player.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF;g.hud.get_parent().visible=false;g.animator.paused=true;g.elevators.set_physics_process(false)
 var helper=g.get_node("V26_Mall_Architecture");var way=g.get_node("V21_Route_Derived_Wayfinding");var rows:Array=[];var cameras:Array=[];var route_checks:Array=[]
 for r:Dictionary in g.read_json("res://source/v29/routes.json"):
  route_checks.append({"id":r.id,"pass":way.check_path(r.points)["pass"]and r.points.all(func(p):return helper.standing_clear(g.v3(p)))})
 for s:Dictionary in g.read_json("res://source/v292/review-cameras.json"):
  if not select.is_empty()and not s.id in select:continue
  var foot=g.v3(s.eye)-Vector3.UP*1.65;cameras.append({"id":s.id,"standing":helper.standing_clear(foot),"floor":way.floor_hit(foot)})
  g.player.global_position=foot;g.player.rotation=Vector3.ZERO;g.player.camera.position=Vector3.UP*1.65;g.player.camera.fov=s.fov;g.player.camera.look_at(g.v3(s.look));g.player.reset_physics_interpolation();g.player.camera.force_update_transform()
  var t:int=Time.get_ticks_usec();await process_frame;await RenderingServer.frame_post_draw;var ms:float=(Time.get_ticks_usec()-t)/1000.
  var file:String=out+"/"+side+"/"+str(s.id)+".jpg";var status:int=root.get_texture().get_image().save_jpg(file,.95)
  rows.append({"camera":s,"file":side+"/"+str(s.id)+".jpg","save_error":status,"capture_frame_wait_ms":ms,"draw_calls":Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),"primitives":Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),"CPU_process_ms":Performance.get_monitor(Performance.TIME_PROCESS)*1000.,"static_memory_bytes":Performance.get_monitor(Performance.MEMORY_STATIC),"video_memory_bytes":Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED)})
  print("V292_CAPTURE ",side," ",s.id)
 var report:Dictionary={"revision":"29.2","side":side,"rows":rows,"camera_feet":cameras,"route_checks":route_checks,"actual_Godot_viewport":true,"resolution":[1920,1080],"adapter":RenderingServer.get_video_adapter_name(),"engine":Engine.get_version_info(),"human_playtest":false,"Windows_GPU_measured":false,"campaigns":g.get_node("V292_People_Campaigns").report if not before else{},"settings":{"cap":Engine.max_fps,"vsync":DisplayServer.window_get_vsync_mode(),"C":g.c_open_proposal,"B_ES":g.es_site_proposal,"continuous":g.a_continuous_v22}}
 var f=FileAccess.open(out+"/data/"+side+"-native.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f=null;g.queue_free();await process_frame;await process_frame;quit()
