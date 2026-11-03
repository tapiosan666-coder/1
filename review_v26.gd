extends SceneTree
var g
var out:String="res://evidence/v26-review"
var baseline:bool=false
var performance:Array=[]
var doors_only:bool=false
func _initialize()->void:call_deferred("run")
func pose(eye:Vector3,look:Vector3,fov:float=65.)->void:
 g.player.position=eye-Vector3.UP*1.65;g.player.rotation=Vector3.ZERO;g.player.camera.position=Vector3.UP*1.65;g.player.camera.fov=fov;g.player.camera.look_at(look);g.player.reset_physics_interpolation()
func shot(path:String,warmup:int=1)->void:
 for i in warmup:await process_frame
 await RenderingServer.frame_post_draw
 root.get_texture().get_image().save_jpg(path,.96)
func run()->void:
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--review-output="):out=arg.trim_prefix("--review-output=")
  if arg=="--doors-only":doors_only=true
 baseline=OS.get_cmdline_user_args().has("--v25-baseline")
 var folder:String=out+("/before"if baseline else"/after");DirAccess.make_dir_recursive_absolute(folder);DirAccess.make_dir_recursive_absolute(out+"/data")
 g=load("res://main.tscn").instantiate();g.mode="v26-review";root.add_child(g)
 while g.results.is_empty():await process_frame
 while not g.get_node("V25_Supported_Decor").has_meta("ready"):await process_frame
 var module=g.get_node_or_null("V26_Mall_Architecture")
 if module!=null:
  while not module.has_meta("ready"):await process_frame
 root.size=Vector2i(1920,1080)
 var state:Dictionary=g.read_json("res://source/v21/review-npc-state.json");state.comparison_mode="v20";g.shoppers_v18.restore_snapshot(state);g.shoppers_v18.set_frozen(true)
 g.player.set_physics_process(false);g.player.input_enabled=false;g.player.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF;g.hud.get_parent().visible=false;g.animator.paused=true;g.elevators.set_physics_process(false)
 var rows:Array=[]
 for s:Dictionary in g.read_json("res://source/v26/review-cameras.json"):
  if doors_only:break
  pose(g.v3(s.eye),g.v3(s.look),s.fov);await shot(folder+"/"+s.id+".jpg",2 if str(s.id).begins_with("commons-")else 1)
  if str(s.id).begins_with("commons-"):
   var durations:Array=[];var drawcalls:Array=[];var objects:Array=[]
   for tick in 3:
    var start:int=Time.get_ticks_usec();await process_frame;await RenderingServer.frame_post_draw;durations.append((Time.get_ticks_usec()-start)/1000.);drawcalls.append(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME));objects.append(Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME))
   performance.append({"camera":s.id,"frame_ms_samples":durations,"draw_calls":drawcalls,"primitives":objects,"memory_static_bytes":Performance.get_monitor(Performance.MEMORY_STATIC),"viewport":[1920,1080],"NPC_count":43,"render_scale":1.,"adapter":RenderingServer.get_video_adapter_name(),"renderer":RenderingServer.get_current_rendering_method(),"hardware_GPU_measured":false})
  rows.append(s.merged({"native_Godot_viewport":true,"image_postprocessing":false,"resolution":[1920,1080],"human_playtest":false,"baseline":baseline}));print("V26_REVIEW_CAPTURE ",s.id)
 if module!=null:
  DirAccess.make_dir_recursive_absolute(out+"/doors")
  var npc_visible_before:bool=g.shoppers_v18.visible;g.shoppers_v18.visible=false
  for d in module.doors:d.set_physics_process(false);d.sense_npcs=false
  for e in module.entrances:
   var p=g.v3(e.p);var n=Vector3(e.n[0],0,e.n[1]);var u=Vector3(n.z,0,-n.x);pose(p-n*7.+u*2.3+Vector3.UP*1.65,p+Vector3.UP*1.45)
   var trace:Array=[]
   for stage in ["01-closed","02-opening","03-open","04-threshold-held","05-reclosed"]:
    var player_point:Vector3=p-n*12.
    if stage=="02-opening"or stage=="03-open":player_point=p-n*3.0
    if stage=="04-threshold-held":player_point=p
    # Controller inputs come from player proximity; only fixed 60Hz time is accelerated.
    var camera_pose:Transform3D=g.player.global_transform;g.player.global_position=player_point
    var count:int=15 if stage=="02-opening"else 180
    for tick in count:
     for d in module.doors:d._physics_process(1./60.)
    var states:Array=[]
    for d in module.doors:
     if d.get_parent().name=="V26_"+e.wing+"_Vestibule":states.append(d.state())
    g.player.global_transform=camera_pose;await shot(out+"/doors/"+e.wing+"-"+stage+".jpg");trace.append({"stage":stage,"controller_states":states,"fixed_step_hz":60,"human_playtest":false,"NPC_displayed":false,"occupancy_input":"controlled player coordinates; separate live NPC detection is tested in architecture-QA.json"})
   var file=FileAccess.open(out+"/data/door-sequence-"+e.wing+".json",FileAccess.WRITE);file.store_string(JSON.stringify(trace,"  "));file=null
  g.shoppers_v18.visible=npc_visible_before
  for d:Dictionary in module.reports.guides:
   if doors_only:break
   var n=Vector3(d.normal[0],0,d.normal[1]);var p=g.v3(d.p);pose(p+n*2.5+Vector3.UP*1.6,p+Vector3.UP*1.45,52.);await shot(folder+"/guide-"+d.id+".jpg")
  for i in module.reports.wall_equipment.size():
   if doors_only:break
   var d:Dictionary=module.reports.wall_equipment[i];var p=g.v3(d.p);var n=Vector3(d.normal[0],0,d.normal[1]);pose(p+n*2.4+Vector3.UP*1.4,p+Vector3.UP*1.15,55.);await shot(folder+"/fire-"+str(i+1)+".jpg")
  for i in module.reports.signs.size():
   if doors_only:break
   var d:Dictionary=module.reports.signs[i];var sign:Node3D=g.get_node("V21_Route_Derived_Wayfinding").mounts[d.sign];var p:Vector3=sign.global_position;var n:Vector3=sign.global_basis.z;pose(p+n*4.5+Vector3.UP*1.65,p+Vector3.UP*3.15,60.);await shot(folder+"/hanging-sign-"+str(i+1)+".jpg")
 var file_name:String="v26-door-native-review.json"if doors_only else("v25"if baseline else"v26")+"-native-review.json"
 var f=FileAccess.open(out+"/data/"+file_name,FileAccess.WRITE);f.store_string(JSON.stringify({"shots":rows,"performance":performance,"adapter":RenderingServer.get_video_adapter_name(),"renderer":RenderingServer.get_current_rendering_method(),"human_playtest":false},"  "));f=null
 print("V26_REVIEW_DONE ","v25"if baseline else"v26");g.queue_free();await process_frame;quit()
