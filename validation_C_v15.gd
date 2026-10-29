extends RefCounted
func walk(g)->void:
 var checks:Array=[];g.player.belt_enabled=false;g.staff.set_all_open(true)
 for i in range(4):await g.get_tree().physics_frame
 if g.only_shot!="EV":
  for route:Dictionary in g.read_json("res://source/physical-routes-v11.json"):
   if g.only_shot=="EXTERNAL":
    if not (String(route.id).begins_with("BR-") or String(route.id).begins_with("AB-") or String(route.id).begins_with("BC-")):continue
   elif g.only_shot!="" and not String(route.id).begins_with(g.only_shot):continue
   await g.settle(g.v3(route.points[0]));var result=await g.walk_points(route.points,5.0);result.id=route.id;result.kind=route.kind;checks.append(result);print("V7_WALK ",route.id," ",result["pass"])
   if not result["pass"]:print("V7_FAILURE ",JSON.stringify(result));g.write_json("latest-failures.json",checks.filter(func(c):return not c["pass"]))
  if g.only_shot=="ES":
   for e:Dictionary in g.manifest.escalators:
    var a=g.v3(e.test_start);var b=g.v3(e.test_end);await g.settle(a);var result=await g.walk_points([[b.x,b.y,b.z]],2.);result.id=e.id;checks.append(result);print("V7_ES ",e.id," ",result["pass"])
 else:
  for i in range(g.elevators.records.size()):
   var r:Dictionary=g.elevators.records[i];var start=int(r.current)
   # Every stop including B1/RF: enter/exit through the real opening and ride continuous carrier.
   var stop_order=range(r.data.stops.size());stop_order.append(0)
   for stop in stop_order:
    var center=r.car.position;var outside=Vector3(r.data.door_xz[0],center.y,r.data.door_xz[2])-Vector3(r.data.inside[0],0,r.data.inside[1])*.9
    await g.settle(outside)
    var before=await g.walk_points([[center.x,center.y,center.z]],2.0)
    var request:bool=g.elevators.request(i,stop);var reached:bool=false;var max_separation:float=0;var min_y:float=g.player.position.y;var max_y:float=min_y;var samples:Array=[]
    for tick in range(1600):
     await g.get_tree().physics_frame
     max_separation=max(max_separation,abs(g.player.position.y-r.car.position.y));min_y=min(min_y,g.player.position.y);max_y=max(max_y,g.player.position.y)
     if tick%30==0:samples.append([tick,g.player.position.y,r.car.position.y])
     if r.state=="open" and int(r.current)==stop:reached=true;break
    var dest=Vector3(outside.x,r.data.stops[stop].y,outside.z);var after=await g.walk_points([[dest.x,dest.y,dest.z]],2.0)
    var okay:bool=before["pass"] and request and reached and after["pass"] and max_separation<.28
    var result={"id":r.data.id+"-STOP-"+r.data.stops[stop].label,"pass":okay,"enter":before,"request":request,"arrival":reached,"exit":after,"max_player_car_floor_error_m":max_separation,"height_range":[min_y,max_y],"samples_tick_playerY_carY":samples,"not_teleport":true};checks.append(result);print("V7_EV ",result.id," ",okay)
 var passed:int=0
 for c:Dictionary in checks:
  if c["pass"]:passed+=1
 g.results.checks=checks;g.results.passed=passed;g.results.failed=checks.size()-passed;g.results.not_fps_benchmark=true;g.results.mode="60Hz automatic CharacterBody3D / actual collision; no human playtest";g.results.human_playtest=false;g.write_json("physics-"+(g.only_shot if g.only_shot!=""else"all")+".json",g.results);print("V7_COMPLETE ",passed,"/",checks.size());g.get_tree().quit()
func capture(g)->void:
 g.player.set_physics_process(false);g.hud.visible=false
 var shots=g.read_json("res://source/cameras-v7.json")
 for shot:Dictionary in shots:
  if g.only_shot=="MAPS":
   if shot.ui!="map":continue
  elif g.only_shot=="UI":
   if shot.id not in ["22-map-B","23-settings"]:continue
  elif g.only_shot!="" and shot.id!=g.only_shot:continue
  g.ui.close();g.player.set_physics_process(false);g.elevators.set_physics_process(false)
  g.player.rotation=Vector3.ZERO;g.player.position=g.v3(shot.eye)-Vector3(0,1.65,0);g.player.camera.position=Vector3(0,1.65,0);g.player.camera.fov=float(shot.get("fov",75));g.player.camera.far=float(shot.get("far_m",800));g.player.camera.look_at(g.v3(shot.look))
  if shot.get("ui","")=="map":g.ui.show_map()
  if shot.get("ui","")=="settings":g.ui.show_settings()
  for i in range(1):await g.get_tree().process_frame
  await RenderingServer.frame_post_draw
  var im=g.get_viewport().get_texture().get_image();g.results.resolution=[im.get_width(),im.get_height()];im.save_png(g.output+"/"+shot.id+".png");print("V7_CAPTURE ",shot.id," ",im.get_width(),"x",im.get_height())
 g.results.human_playtest=false;g.results.screenshot_kind="Actual Godot Viewport";g.results.settings=g.ui.settings.snapshot();g.write_json("render-v7.json",g.results);g.get_tree().quit()

func vehicle(g)->void:
 g.player.set_physics_process(false);g.elevators.set_physics_process(false)
 var checks:Array=[];var data=g.read_json("res://source/site-v11.json")
 var height:float=2.1 if g.only_shot=="TALL" else 1.65
 var shape=BoxShape3D.new();shape.size=Vector3(1.85,height,4.8)
 for fac:Dictionary in data.parking.facilities:
  for ramp:Dictionary in fac.ramps:
   var pts:Array=ramp.profile_xyz;var collisions:Array=[];var samples:int=0
   for i in range(pts.size()):
    var p=g.v3(pts[i])+Vector3(429,0,-46);var prev=g.v3(pts[max(0,i-1)]);var next=g.v3(pts[min(pts.size()-1,i+1)]);var forward=(next-prev).normalized();var right=forward.cross(Vector3.UP).normalized();var up=right.cross(forward).normalized()
    var query=PhysicsShapeQueryParameters3D.new();query.shape=shape;query.transform=Transform3D(Basis(right,up,-forward),p+up*(height/2+.115));query.margin=.005;query.exclude=[g.player.get_rid()]
    var hits=g.get_world_3d().direct_space_state.intersect_shape(query,8);samples+=1
    if not hits.is_empty():
     collisions.append({"sample":i,"position":[p.x,p.y,p.z],"colliders":hits.map(func(h):return str(h.collider.name))})
   var result={"id":ramp.id,"pass":collisions.is_empty(),"sample_count":samples,"collisions":collisions,"test":"static 4.8x1.85x1.65m swept-pose clearance on source vertical ramp centreline","vehicle_dynamic_driving":false,"entry_turns_and_parking_maneuvers_verified":false};checks.append(result);print("V7_VEHICLE ",ramp.id," ",result["pass"])
 var passed:int=checks.filter(func(c):return c["pass"]).size();g.write_json(("vehicle-clearance-2_1m-v7.json" if g.only_shot=="TALL" else "vehicle-clearance-v7.json"),{"geometry":g.results,"tested_car_height_m":height,"checks":checks,"passed":passed,"failed":checks.size()-passed,"human_driving":false,"all_vehicle_network_verified":false});g.get_tree().quit()

func ui_test(g)->void:
 var checks:Array=[];g.player.input_enabled=true;g.mode="interactive";var event=InputEventKey.new();event.keycode=KEY_M;event.pressed=true;Input.parse_input_event(event)
 await g.get_tree().process_frame
 var start=g.player.position;var ticks=g.player.ticks;var key=InputEventKey.new();key.physical_keycode=KEY_W;key.pressed=true;Input.parse_input_event(key)
 for i in range(60):await g.get_tree().physics_frame
 checks.append({"id":"M-opens-map-and-freezes-motion","pass":g.ui.overlay=="map" and g.player.position.distance_to(start)<.00001 and g.player.ticks==ticks,"position_error_m":g.player.position.distance_to(start),"physics_ticks_advanced":g.player.ticks-ticks})
 for i in range(g.ui.map.wing_select.item_count):
  g.ui.map.wing_select.select(i);g.ui.map.wing_select.item_selected.emit(i)
  for j in range(g.ui.map.floor_select.item_count):
   g.ui.map.floor_select.select(j);g.ui.map.floor_select.item_selected.emit(j);checks.append({"id":"map-selector-%s-%s"%[i,j],"pass":not g.ui.map.selected.is_empty() and g.player.position.distance_to(start)<.00001})
 key.pressed=false;Input.parse_input_event(key.duplicate());var release=InputEventKey.new();release.keycode=KEY_M;release.pressed=false;Input.parse_input_event(release)
 await g.get_tree().process_frame
 var press=InputEventKey.new();press.keycode=KEY_M;press.pressed=true;Input.parse_input_event(press)
 await g.get_tree().process_frame
 checks.append({"id":"M-closes-map-and-resumes-controller","pass":g.ui.overlay=="" and g.player.input_enabled and g.player.is_physics_processing()})
 g.write_json("ui-interaction-v7.json",{"checks":checks,"automated_input_events":true,"human_playtest":false});print("UI_TEST ",checks.filter(func(c):return c["pass"]).size(),"/",checks.size());g.get_tree().quit()
