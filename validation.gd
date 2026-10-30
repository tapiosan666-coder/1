extends RefCounted
func capture(g)->void:
 var shots=g.read_json("res://source/cameras.json");g.hud.visible=false;g.player.set_physics_process(false);var times:Array=[]
 for shot:Dictionary in shots:
  if g.baseline and shot.get("after_only",false):continue
  if g.context_only and shot.scope!="context":continue
  if not g.context_only and shot.scope=="context":continue
  if g.only_shot=="ports":
   if shot.id not in["09-AB-2-bridge","10-BC-2-bridge"]:continue
  elif g.only_shot=="annex-interiors":
   if shot.id not in["13-B1-market","14-support-reservation"]:continue
  elif g.only_shot=="updates":
   if shot.id not in["05-B2-047-corner","09-AB-2-bridge"]:continue
  elif g.only_shot=="extra":
   if int(shot.id.substr(0,2))<13:continue
  elif g.only_shot!="" and shot.id!=g.only_shot:continue
  g.player.rotation=Vector3.ZERO;g.player.camera.global_position=g.v3(shot.eye_local);g.player.camera.look_at(g.v3(shot.look_local))
  for i in range(3):await g.get_tree().process_frame
  await RenderingServer.frame_post_draw
  var im=g.get_viewport().get_texture().get_image();var err=im.save_png(g.output+"/"+shot.id+".png");print("CAPTURE ",shot.id," ",err)
  if g.baseline:continue
  var count:int=0
  if count==0:continue
  var samples:Array=[];var last=Time.get_ticks_usec()
  for i in range(count):
   await g.get_tree().process_frame
   var now=Time.get_ticks_usec();samples.append((now-last)/1000.0);last=now
  var total:float=0
  for x in samples:total+=x
  var ss=samples.duplicate();ss.sort();times.append({"id":shot.id,"samples_ms":samples,"sample_frames":count,"mean_ms":total/count,"fps":1000.0*count/total,"p95_ms":ss[count-1],"camera":shot,"draw_calls":Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)})
 g.results.screenshot_kind="Actual Godot Viewport, no generated imagery";g.results.baseline_reconstruction=g.baseline;g.results.performance=times;g.results.npc_count=0;g.results.human_playtest=false;g.write_json("render-results.json",g.results);g.get_tree().quit()
func walk(g)->void:
 var checks:Array=[];g.player.belt_enabled=false;g.staff.set_all_open(true)
 for i in range(4):await g.get_tree().physics_frame
 var routes=g.read_json("res://source/physical-routes.json")
 for route:Dictionary in routes:
  if g.only_shot=="public" and not String(route.id).begins_with("PUBLIC-"):continue
  await g.settle(g.v3(route.points[0]));var result=await g.walk_points(route.points,6.0);result.id=route.id;result.kind=route.kind;checks.append(result);print("PHYSICS ",route.id," ",result["pass"])
 for e:Dictionary in (g.manifest.escalators if g.only_shot!="public" else[]):
  for reverse in[false,true]:
   var a=g.v3(e.test_end if reverse else e.test_start);var b=g.v3(e.test_start if reverse else e.test_end);await g.settle(a);var result=await g.walk_points([[b.x,b.y,b.z]],2.0);result.id=e.id+("-down"if reverse else"-up");result.kind="physical incline, no teleport, conveyor disabled";checks.append(result);print("ESC ",result.id," ",result["pass"])
 var pass_count:int=0
 for q:Dictionary in checks:
  if q["pass"]:pass_count+=1
 g.results.checks=checks;g.results.passed=pass_count;g.results.failed=checks.size()-pass_count;g.results.human_playtest=false;g.results.mode="headless fixed 60Hz automated CharacterBody3D move_and_slide";g.results.not_fps_benchmark=true;g.results.staff_doors="Opened through real door transforms; not removed";g.write_json("physical-results.json",g.results);print("PHYSICS_COMPLETE ",pass_count," / ",checks.size());g.get_tree().quit()
