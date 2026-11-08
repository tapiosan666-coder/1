extends SceneTree
var g
var stream
var way
var helper
var report:Dictionary={"human_playtest":false,"simulation":"Godot --fixed-fps 60, actual CharacterBody3D move_and_slide, 60Hz physics; accelerated wall-clock execution","checks":[],"routes":[],"ES_rides":[],"transfers":[],"guard_probes":[],"entrances":[],"streaming":[],"main_walks":[]}
var tracking:bool=false
var last_y:float=0.
var max_dy:float=0.
func sample_vertical()->void:
 if tracking:
  var y:float=g.player.position.y;max_dy=maxf(max_dy,absf(y-last_y));last_y=y
func _initialize()->void:
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("user://v31-verification"));call_deferred("run")
func key(code:int)->void:
 var e=InputEventKey.new();e.keycode=code;e.physical_keycode=code;e.pressed=true;Input.parse_input_event(e);await process_frame;e=InputEventKey.new();e.keycode=code;e.physical_keycode=code;e.pressed=false;Input.parse_input_event(e);await process_frame
func teleport(p:Vector3)->void:
 g.player.auto_active=false;g.player.velocity=Vector3.ZERO;g.player.set_physics_process(false);g.player.position=p+Vector3.UP*.06;stream.prepare_position(p)
 await physics_frame;await physics_frame;g.player.set_physics_process(true);g.player.input_enabled=false
 for i in 10:await physics_frame
func walk(points:Array)->Dictionary:return await g.walk_points(points,2.6)
func run()->void:
 RenderingServer.set_render_loop_enabled(false);g=load("res://main.tscn").instantiate();g.mode="v31-final-qa";root.add_child(g)
 while g.results.is_empty():await process_frame
 physics_frame.connect(sample_vertical)
 Engine.max_fps=0;stream=g.get_node("V31_Runtime");g.player.input_enabled=false;g.shoppers_v18.set_frozen(true);g.shoppers_v18.set_enabled(false,true);g.animator.paused=true;g.elevators.set_physics_process(false)
 way=load("res://wayfinding_v21.gd").new();g.add_child(way);way.game=g;way.capsule=CapsuleShape3D.new();way.capsule.radius=.31;way.capsule.height=1.8
 helper=load("res://mall_architecture_v26.gd").new();g.add_child(helper);helper.game=g;helper.way=way
 var ctx:Dictionary=g.read_json("res://assets/v30/world/context.json");var layers:Array=g.read_json("res://source/v22/map-data-integrated.json").filter(func(f):return f.wing in["A","B","C"])
 report.checks.append({"id":"protected-15layers-480stores-43NPC","pass":layers.size()==15 and g.retail_v23_cache.stores.size()==480 and g.shoppers_v18.data.people.size()==43})
 report.checks.append({"id":"139-first-floor-finish-records","pass":ctx.firstfloor_finishes.store_reports.filter(func(s):return str(s.id).contains("1F")or str(s.id).begins_with("B1-")).size()==139})
 # Actual normal input routing, no developer option.
 g.mode="interactive"
 for code:int in [KEY_F1,KEY_F2,KEY_F3]:
  await key(code);await physics_frame;var p:Vector3=g.player.position;report.checks.append({"id":"F1-F2-F3","key":code,"pass":p.x>260 if code==KEY_F1 else p.z< -160 if code==KEY_F3 else p.x<260 and p.z> -160})
 for code:int in [KEY_F4,KEY_F6,KEY_F7,KEY_F8,KEY_F9,KEY_F10,KEY_F11,KEY_F12]:
  var enabled:bool=g.shoppers_v18.enabled;var fair:bool=g.commons_v16.fair_enabled;await key(code);report.checks.append({"id":"debug-key-disabled-normal","key":code,"pass":g.ui.overlay==""and enabled==g.shoppers_v18.enabled and fair==g.commons_v16.fair_enabled})
 await key(KEY_M);report.checks.append({"id":"map-stops-movement","pass":g.ui.overlay=="map"and not g.player.is_physics_processing()});await key(KEY_M);await key(KEY_ESCAPE);report.checks.append({"id":"Escape-settings","pass":g.ui.overlay=="settings"});await key(KEY_ESCAPE);g.mode="v31-final-qa";g.player.set_physics_process(false)
 # Geometry audit mode: load every PHYSICS chunk, never every render/light chunk.
 stream.stream_ready=false
 for d:Dictionary in stream.definitions:
  if d.tier=="physics":stream.install_sync(d)
 await physics_frame;await physics_frame
 for r:Dictionary in g.read_json("res://source/v29/routes.json"):report.routes.append({"id":r.id,"pass":way.check_path(r.points)["pass"]})
 for r:Dictionary in g.read_json("res://source/v291/interior-paths.json").paths:report.routes.append({"id":r.target,"pass":way.check_path(r.points)["pass"]})
 print("V31_QA_GEOMETRY ",report.routes.size()," fail ",report.routes.filter(func(x):return not x["pass"]).size())
 # Public landing access and all six B-west directions.
 var spec:Dictionary=g.read_json("res://source/v30/B-core.json")
 for e:Dictionary in spec.escalators:
  var reverse:bool=e.direction=="DOWN";var start:Vector3=g.v3(e.test_end if reverse else e.test_start);var target:Array=e.test_start if reverse else e.test_end
  await teleport(start);g.player.belt_enabled=true;last_y=g.player.position.y;max_dy=0.;tracking=true;var result:Dictionary=await walk([target]);tracking=false;result["max_vertical_step_per_60Hz_frame_m"]=max_dy;result["no_large_vertical_jump"]=max_dy<.12;report.ES_rides.append({"id":e.id,"from":e.test_end if reverse else e.test_start,"to":target,"result":result});print("V31_ES_RIDE ",e.id," ",result["pass"])
 for transfer:Dictionary in spec.transfers:
  await teleport(g.v3(transfer.points[0]));var result:Dictionary=await walk(transfer.points.slice(1));report.transfers.append({"from":transfer["from"],"to":transfer.to,"length_m":transfer.centreline_length_m,"result":result});print("V31_TRANSFER ",transfer.centreline_length_m," ",result["pass"])
 for level:int in [1,2,3]:
  var y:float=[0.,5.525,10.875,16.4][level]
  for side:float in [-1.,1.]:
   var start=Vector3(-220 if side<0 else -164,y,-15.5);var target=Vector3(-201 if side<0 else -183,y,-15.5);await teleport(start);var result:Dictionary=await walk([[target.x,y,target.z]]);report.transfers.append({"kind":"public-approach","floor":level,"side":side,"result":result})
  # Probe a genuinely open shaft edge, not a landing mouth.
  var p=Vector3(-192,y,-9.12);await teleport(p);g.player.auto_target=Vector3(-192,y,-10.9);g.player.auto_speed=2.6;g.player.auto_active=true
  for i in 100:await physics_frame
  g.player.auto_active=false;var safe:bool=g.player.position.z> -9.76 and g.player.position.y>y-.25;report.guard_probes.append({"floor":level,"position":[g.player.position.x,g.player.position.y,g.player.position.z],"pass":safe});print("V31_GUARD ",level," ",safe)
 # Restore actual region streaming, then walk the complete three main streets.
 stream.stream_ready=true;stream.retire(g.player.position);g.player.belt_enabled=true
 for route:Dictionary in g.read_json("res://source/v30/main-routes.json"):
  await teleport(g.v3(route.points[0]));var result:Dictionary=await walk(route.points.slice(1));report.main_walks.append({"id":route.id,"length_m":route.length_m,"result":result});print("V31_MAIN_WALK ",route.id," ",result["pass"])
 for p:Vector3 in [Vector3(418,.03,-53),Vector3(-191.9,5.535,-4.9),Vector3(-152,.03,-289),Vector3(-113,-5.32,-55),Vector3(-201,16.43,-16)]:
  await teleport(p);var counts:Dictionary=stream.resident_counts();report.streaming.append({"p":[p.x,p.y,p.z],"floor":way.floor_hit(Vector3(p.x,p.y-.03,p.z)),"counts":counts})
 # Existing exterior double-door passage uses actual sliding leaf collisions.
 for e:Dictionary in ctx.entrances:
  if not e.wing in["A","B","C"]:continue
  var a:Vector3=g.v3(e.outside);var b:Array=e.inside;await teleport(a);var result:Dictionary=await walk([b]);report.entrances.append({"wing":e.wing,"result":result});print("V31_ENTRANCE ",e.wing," ",result["pass"])
 report.streaming_stats=stream.stats;report.boot=g.results;report.total_nodes=get_node_count();report.windows_GPU_tested=false;report.all_275_routes_pass=report.routes.all(func(x):return x["pass"])
 var file=FileAccess.open("user://v31-verification/final-runtime-QA.json",FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close();g.queue_free();await process_frame;await process_frame;print("V31_FINAL_QA_WRITTEN");quit()
