extends SceneTree
var g
func _initialize()->void:call_deferred("run")
func run()->void:
 var before:bool=OS.get_cmdline_user_args().has("--v27-baseline")
 var out:String="res://evidence/v28-review"
 for a in OS.get_cmdline_user_args():
  if a.begins_with("--review-output="):out=a.trim_prefix("--review-output=")
 var scene:String="res://main.tscn";var selection:Array=[];var suffix:String=""
 for a in OS.get_cmdline_user_args():
  if a.begins_with("--scene="):scene=a.trim_prefix("--scene=");suffix="-"+scene.get_file().get_basename()
  if a.begins_with("--select="):selection=Array(a.trim_prefix("--select=").split(","))
 var side:String="before"if before else"after"
 side+=suffix
 DirAccess.make_dir_recursive_absolute(out+"/"+side);DirAccess.make_dir_recursive_absolute(out+"/data")
 g=load(scene).instantiate();g.mode="v27-review";root.add_child(g)
 while g.results.is_empty():await process_frame
 while not g.get_node("V26_Mall_Architecture").has_meta("ready"):await process_frame
 while not g.get_node("V27_Architecture").has_meta("ready"):await process_frame
 var mod=g.get_node_or_null("V28_Architecture")
 if mod!=null:
  while not mod.has_meta("ready"):await process_frame
 var snapshot={"scene":scene,"flags":{"C":g.c_open_proposal,"B_ES":g.es_site_proposal,"A_continuous":g.a_continuous_v22,"B_legacy":g.comparison_B_v28},"escalators":g.manifest.escalators,"elevators":g.elevators.records.map(func(e):return e.data),"architecture":g.get_node("V26_Mall_Architecture").reports,"v28":mod.report if mod!=null else{},"wayfinding_stats":g.get_node("V21_Route_Derived_Wayfinding").stats}
 var sf=FileAccess.open(out+"/data/"+side+"-runtime.json",FileAccess.WRITE);sf.store_string(JSON.stringify(snapshot,"  "));sf=null
 root.size=Vector2i(1920,1080);g.shoppers_v18.set_frozen(true);g.player.set_physics_process(false);g.player.input_enabled=false;g.player.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF;g.hud.get_parent().visible=false;g.animator.paused=true;g.elevators.set_physics_process(false)
 var perf:Array=[]
 for s in g.read_json("res://source/v28/review-cameras.json"):
  if not selection.is_empty() and not s.id in selection:continue
  g.hud.get_parent().visible=(s.id=="B-normal-startup" and not before)
  g.player.position=g.v3(s.eye)-Vector3.UP*1.65;g.player.rotation=Vector3.ZERO;g.player.camera.position=Vector3.UP*1.65;g.player.camera.projection=Camera3D.PROJECTION_ORTHOGONAL if s.get("orthographic",false)else Camera3D.PROJECTION_PERSPECTIVE;g.player.camera.size=s.get("size",30.);g.player.camera.fov=s.fov;g.player.camera.look_at(g.v3(s.look));g.player.reset_physics_interpolation()
  for i in 2:await process_frame
  await RenderingServer.frame_post_draw
  root.get_texture().get_image().save_jpg(out+"/"+side+"/"+s.id+".jpg",.96)
  var samples:Array=[]
  for i in (3 if s.id in ["B-1F-oblique","C-dog-ground","C-L3-dog-ground"] else 0):
   var t=Time.get_ticks_usec();await process_frame;await RenderingServer.frame_post_draw;samples.append((Time.get_ticks_usec()-t)/1000.)
  perf.append({"camera":s.id,"frame_ms":samples,"draw_calls":Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),"primitives":Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)})
  print("V28_CAPTURE ",side," ",s.id)
 var f=FileAccess.open(out+"/data/"+side+"-native.json",FileAccess.WRITE);f.store_string(JSON.stringify({"cameras":g.read_json("res://source/v28/review-cameras.json"),"performance":perf,"adapter":RenderingServer.get_video_adapter_name(),"renderer":RenderingServer.get_current_rendering_method(),"engine":Engine.get_version_info(),"main_scene":scene,"normal_startup_flags":{"C":g.c_open_proposal,"B_ES":g.es_site_proposal,"A_continuous":g.a_continuous_v22},"screenshots_unedited":true,"human_playtest":false},"  "));f=null
 g.queue_free();await process_frame;await process_frame;quit()
