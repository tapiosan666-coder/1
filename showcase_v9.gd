extends RefCounted
func pose(g,shot:Dictionary)->void:
 g.player.rotation=Vector3.ZERO;g.player.position=g.v3(shot.eye)-Vector3(0,1.65,0);g.player.velocity=Vector3.ZERO;g.player.camera.position=Vector3(0,1.65,0);g.player.camera.fov=float(shot.get("fov",75));g.player.camera.look_at(g.v3(shot.look))
func capture(g)->void:
 g.player.set_physics_process(false);g.hud.visible=false;g.elevators.set_physics_process(false)
 var records:Array=[]
 for shot:Dictionary in g.read_json("res://source/cameras-v8.json"):
  if g.only_shot!="" and shot.id!=g.only_shot:continue
  pose(g,shot)
  for i in range(4):await g.get_tree().process_frame
  await RenderingServer.frame_post_draw
  var im=g.get_viewport().get_texture().get_image();im.save_png(g.output+"/"+shot.id+".png");records.append({"id":shot.id,"eye":shot.eye,"look":shot.look,"fov":g.player.camera.fov,"resolution":[im.get_width(),im.get_height()],"actual_godot_viewport":true,"baseline_v7_visual":g.visual_v7});print("V9_CAPTURE ",shot.id," ",im.get_width(),"x",im.get_height())
 g.write_json("captures.json",{"runtime":g.results,"shots":records});await g.get_tree().process_frame;g.get_tree().quit()
func benchmark(g)->void:
 g.player.set_physics_process(false);g.elevators.set_physics_process(false);g.animator.paused=false
 var records:Array=[];var shots=g.read_json("res://source/cameras-v8.json")
 for idx in [0,2,4]:
  var shot:Dictionary=shots[idx];pose(g,shot)
  for i in range(4):await g.get_tree().process_frame
  var samples:Array=[];var start=Time.get_ticks_usec();var last=start
  while (Time.get_ticks_usec()-start<20000000 or samples.size()<8)and Time.get_ticks_usec()-start<90000000:
   await RenderingServer.frame_post_draw
   var now=Time.get_ticks_usec();samples.append((now-last)/1000.0);last=now
   await g.get_tree().process_frame
  samples.sort();var elapsed=(last-start)/1000000.0
  var record={"id":shot.id,"frames":samples.size(),"elapsed_seconds":elapsed,"average_fps":samples.size()/elapsed,"median_frame_ms":samples[samples.size()/2],"p99_frame_ms":samples[min(samples.size()-1,int(samples.size()*.99))],"max_frame_ms":samples[-1],"resolution":[g.get_viewport().get_visible_rect().size.x,g.get_viewport().get_visible_rect().size.y],"settings":g.ui.settings.snapshot(),"actual_wall_clock_rendering":true,"not_fixed_fps":true,"human_playtest":false};records.append(record);print("V9_BENCHMARK ",JSON.stringify(record))
 g.write_json("fps-v9.json",{"runtime":g.results,"measurements":records,"RTX4060_tested":false,"NPC_count":0,"144FPS_verified":false});g.get_tree().quit()
func walk(g)->void:
 g.staff.set_all_open(true);g.player.belt_enabled=false
 var ids:Array=[]
 for s:Dictionary in g.read_json("res://source/fitout-v8.json").stores:ids.append(s.id)
 var checks:Array=[]
 for route:Dictionary in g.read_json("res://source/physical-routes-v7.json"):
  var selected:bool=false
  for id:String in ids:
   if str(route.id).contains(id):selected=true;break
  if not selected:continue
  await g.settle(g.v3(route.points[0]));var result=await g.walk_points(route.points,5.0);result.id=route.id;checks.append(result);print("V9_WALK ",route.id," ",result["pass"])
  if not result["pass"]:print("V9_FAILURE ",JSON.stringify(result))
 # New camera positions checked against actual collision floor under the player.
 for shot:Dictionary in g.read_json("res://source/cameras-v8.json"):
  await g.settle(g.v3(shot.eye)-Vector3(0,1.65,0));var start=g.player.position
  var okay:bool=g.player.is_on_floor()and abs(start.y)<.10
  checks.append({"id":"CAMERA-"+shot.id,"pass":okay,"position":[start.x,start.y,start.z],"on_floor":g.player.is_on_floor()});print("V9_GROUND ",shot.id," ",okay)
 var passed=checks.filter(func(c):return c["pass"]).size();g.write_json("walk-v9.json",{"runtime":g.results,"checks":checks,"passed":passed,"failed":checks.size()-passed,"human_playtest":false,"scope":"affected shops and camera foot positions; not entire 15-layer repetition"});print("V9_WALK_COMPLETE ",passed,"/",checks.size());g.get_tree().quit()
