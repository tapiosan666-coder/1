extends SceneTree
var g
func _initialize()->void:call_deferred("run")
func run()->void:
 var before:bool=OS.get_cmdline_user_args().has("--v28-baseline")
 g=load("res://main.tscn").instantiate();g.mode="v29-physics";root.add_child(g)
 while g.results.is_empty():await process_frame
 while not g.get_node("V28_Architecture").has_meta("ready"):await process_frame
 if not before:
  while not g.get_node("V29_Continuous_1F").has_meta("ready"):await process_frame
 Engine.max_fps=0
 g.shoppers_v18.set_frozen(true);g.player.set_physics_process(false);g.player.input_enabled=false
 var helper=g.get_node("V26_Mall_Architecture");var way=g.get_node("V21_Route_Derived_Wayfinding")
 for d in helper.doors:d.force_open=true
 for i in 90:await physics_frame
 var routes:Array=[]
 for r:Dictionary in g.read_json("res://source/v29/routes.json"):
  var result:Dictionary=way.check_path(r.points)
  routes.append({"id":r.id,"wing":r.wing,"pass":result["pass"],"details":result,"test_method":"swept player capsule + support ray; not a human walk"})
 var store_rows:Array=[];var plan:Dictionary=g.read_json("res://source/v25/retail-plan.json")
 for s:Dictionary in plan.stores:
  if s.floor!="1F":continue
  var path:Array=s.main_route_world;var r:Dictionary=way.check_path(path)
  var actual:Array=[]
  # Actual CharacterBody3D advances through the authored entry route in both directions.
  for reverse:bool in [false,true]:
   var points:Array=path.duplicate(true)
   if reverse:points.reverse()
   g.player.global_position=g.v3(points[0])+Vector3.UP*.08;g.player.velocity=Vector3.ZERO;var stopped:bool=false
   for i in range(1,points.size()):
    var target:Vector3=g.v3(points[i]);var safety:int=0;var maximum_ticks:int=ceili(g.player.global_position.distance_to(target)/12.*60.)+180
    while Vector2(g.player.position.x-target.x,g.player.position.z-target.z).length()>.18 and safety<maximum_ticks:
     var delta:Vector3=target-g.player.position;delta.y=0.;g.player.velocity=delta.normalized()*12.;g.player.velocity.y=-2.;g.player.move_and_slide();await physics_frame;safety+=1
    if safety>=maximum_ticks:stopped=true;break
   var residual:float=Vector2(g.player.position.x-float(points[-1][0]),g.player.position.z-float(points[-1][2])).length()
   actual.append({"reverse":reverse,"pass":not stopped and residual<.25,"residual_m":residual,"speed_m_s":12.,"note":"accelerated automatic collision walk, not normal-speed human validation"})
  store_rows.append({"store_id":s.id,"sweep_pass":r["pass"],"sweep":r,"physical_walks":actual})
 var equipment:Array=[]
 for old:Dictionary in g.read_json("res://source/v25/shopping-physics.json").equipment:
  if not str(old.store_id)in store_rows.map(func(r):return str(r.store_id)):continue
  if not old.get("approach",[]) is Array or old.get("approach",[]).size()!=3:
   equipment.append({"fixture_id":old.fixture_id,"store_id":old.store_id,"status":"NOT TESTED","reason":"Inherited service approach has no 3D coordinate"});continue
  var at:Vector3=g.v3(old.approach);var supported:bool=way.floor_hit(at);var clear:bool=supported and helper.standing_clear(at)
  equipment.append({"fixture_id":old.fixture_id,"store_id":old.store_id,"previous_recorded_standing_clear":old.standing_clear,"standing_clear_now":clear,"floor_supported":supported,"test_method":"actual standing capsule at inherited service approach; not complete service interaction"})
 var signs:Array=[]
 for c:Dictionary in way.checks:
  if c["pass"]:signs.append({"sign":c.sign,"target":c.target,"pass":way.check_path(c.actual_path)["pass"],"front_arrow":c.front_arrow,"back_arrow":c.back_arrow})
 var report:Dictionary={"equipment_approaches":equipment,"baseline":before,"route_sweeps":routes,"stores":store_rows,"sign_route_rechecks":signs,"store_count":plan.stores.size(),"NPC_count":g.shoppers_v18.actors.size(),"physics_ticks_per_second":Engine.physics_ticks_per_second,"engine":Engine.get_version_info(),"human_playtest":false,"Windows_GPU_measured":false,"environment":g.get_node("V29_Continuous_1F").report if not before else{},"protected_structure_hashes":{}}
 for p:String in ["res://source/v28/scene-design.json","res://source/v28/entrances.json","res://source/v28/wayfinding.json","res://source/v28/terrain-plan.json","res://shoppers_v20.gd"]:report.protected_structure_hashes[p]=FileAccess.get_sha256(p)
 var out:String="res://evidence/v29"
 for a:String in OS.get_cmdline_user_args():
  if a.begins_with("--qa-output="):out=a.trim_prefix("--qa-output=")
 DirAccess.make_dir_recursive_absolute(out);var f=FileAccess.open(out+("/before-physics.json"if before else"/after-physics.json"),FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f=null
 print("V29_PHYSICS_DONE ","before"if before else"after"," ",routes.size()," routes ",store_rows.size()," shops")
 g.queue_free();await process_frame;await process_frame;quit()
