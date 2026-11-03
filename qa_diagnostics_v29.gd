extends SceneTree
var g
func _initialize()->void:call_deferred("run")
func run()->void:
 var before:bool=OS.get_cmdline_user_args().has("--v28-baseline");var out:String="res://evidence/v29-diagnostics"
 for a:String in OS.get_cmdline_user_args():
  if a.begins_with("--qa-output="):out=a.trim_prefix("--qa-output=")
 g=load("res://main.tscn").instantiate();g.mode="v29-diagnostics";root.add_child(g)
 while g.results.is_empty():await process_frame
 while not g.get_node("V28_Architecture").has_meta("ready"):await process_frame
 if not before:
  while not g.get_node("V29_Continuous_1F").has_meta("ready"):await process_frame
 Engine.max_fps=0;g.shoppers_v18.set_frozen(true);g.shoppers_v18.set_enabled(false,true);g.player.set_physics_process(false);g.player.input_enabled=false
 var helper=g.get_node("V26_Mall_Architecture");var way=g.get_node("V21_Route_Derived_Wayfinding")
 for d in helper.doors:d.force_open=true
 for i in 60:await physics_frame
 var report:Dictionary={"before":before,"human_playtest":false,"B1_030_precision_walks":[],"route_repairs":[],"camera_feet":[],"NPC_paths":[]}
 var s:Dictionary={}
 for row:Dictionary in g.read_json("res://source/v25/retail-plan.json").stores:
  if row.id=="B1-030":s=row;break
 for combination:Array in [[false,false],[false,true],[true,false],[true,true]]:
  var npc_enabled:bool=combination[0];var reverse:bool=combination[1];g.shoppers_v18.set_enabled(npc_enabled,true)
  var points:Array=s.main_route_world.duplicate(true)
  if reverse:points.reverse()
  g.player.global_position=g.v3(points[0])+Vector3.UP*.08;g.player.velocity=Vector3.ZERO
  var stages:Array=[]
  for i in range(1,points.size()):
   var target:Vector3=g.v3(points[i]);var maximum:int=ceili(g.player.global_position.distance_to(target)/2.6*60.)+240;var tick:int=0;var collisions:Dictionary={}
   while Vector2(g.player.position.x-target.x,g.player.position.z-target.z).length()>.03 and tick<maximum:
    var delta:Vector3=target-g.player.global_position;delta.y=0.;g.player.velocity=delta.normalized()*minf(2.6,delta.length()*60.);g.player.velocity.y=-2.;g.player.move_and_slide()
    for j in g.player.get_slide_collision_count():
     var collision=g.player.get_slide_collision(j);var collider=collision.get_collider()
     if collider!=null and absf(collision.get_normal().y)<.7:collisions[str(collider.name)]=true
    await physics_frame;tick+=1
   var residual:float=Vector2(g.player.position.x-target.x,g.player.position.z-target.z).length();stages.append({"step":i,"pass":residual<.04,"residual_m":residual,"feet":[g.player.position.x,g.player.position.y,g.player.position.z],"target":points[i],"colliders":collisions.keys()})
   if residual>.04:break
  report.B1_030_precision_walks.append({"NPC_enabled_frozen":npc_enabled,"reverse":reverse,"stages":stages,"pass":stages.size()==points.size()-1 and stages.all(func(x):return x["pass"]),"speed_m_s":2.6,"endpoint_tolerance_m":.03})
 g.shoppers_v18.set_enabled(false,true);g.player.global_position=Vector3(1000,0,1000);await physics_frame
 var graphs:Dictionary={};var variant:String="combined"if g.c_open_proposal and g.es_site_proposal else"C"if g.c_open_proposal else"ES"if g.es_site_proposal else"normal";var grids:Dictionary=g.read_json("res://source/v22/navigation-grids.json")
 var other:Dictionary={}
 if before and FileAccess.file_exists(out+"/after.json"):other=JSON.parse_string(FileAccess.get_file_as_string(out+"/after.json"))
 for r:Dictionary in g.read_json("res://source/v29/routes.json"):
  var status:Dictionary=way.check_path(r.points)
  if status["pass"]:continue
  var replacement:Array=[]
  if before:
   for previous:Dictionary in other.get("route_repairs",[]):
    if previous.id==r.id:replacement=previous.proposed_points;break
  else:
   var key:String=variant+"-"+r.wing+"-1F"
   if not graphs.has(key):var graph=load("res://nav_live_v21.gd").new();graph.setup(grids[key],way);graphs[key]=graph
   replacement=graphs[key].repair({"path":r.points,"target_point":[r.points[-1][0],r.points[-1][2]]})
   if not replacement.is_empty()and g.v3(replacement[0]).distance_to(g.v3(r.points[0]))>.01:replacement.push_front(r.points[0])
  var check:Dictionary=way.check_path(replacement)if replacement.size()>1 else{"pass":false,"reason":"No replacement path"}
  report.route_repairs.append({"id":r.id,"original_points":r.points,"original_status":status,"proposed_points":replacement,"proposed_status":check,"meaning":"inspection route recalculation, no building or corridor added"})
 for c:Dictionary in g.read_json("res://source/v29/review-cameras.json"):
  var foot:Vector3=g.v3(c.eye)-Vector3.UP*1.65;var clear:bool=helper.standing_clear(foot);var support:bool=way.floor_hit(foot);var proposed:Array=[]
  if not clear or not support:
   var key:String=variant+"-"+c.wing+"-1F"
   if not graphs.has(key):var graph=load("res://nav_live_v21.gd").new();graph.setup(grids[key],way);graphs[key]=graph
   var id:int=graphs[key].nearest_clear(Vector2(foot.x,foot.z))
   if id>=0:var p:Vector3=graphs[key].world(id);proposed=[p.x,1.65,p.z]
  report.camera_feet.append({"id":c.id,"standing_clear":clear,"floor_supported":support,"proposed_eye":proposed})
 for person:Dictionary in g.shoppers_v18.data.people:
  var points:Array=person.get("path",person.get("route",[]))
  if points.size()>1:report.NPC_paths.append({"id":person.id,"pass":way.check_path(points)["pass"],"scope":"authored path capsule sweep; not full animation or crowd interaction"})
  elif person.has("p"):
   var row:Dictionary={"id":person.id,"role":person.role,"floor_supported":way.floor_hit(g.v3(person.p)),"scope":"standing capsule or seat anchor; not full animation"}
   if person.role!="seated":row.standing_clear=helper.standing_clear(g.v3(person.p))
   elif person.has("home_point")and person.has("stand_point"):row.seat_approach_clear=way.check_path([person.home_point,person.stand_point])["pass"]
   report.NPC_paths.append(row)
 for graph in graphs.values():graph.clear();graph.way=null
 DirAccess.make_dir_recursive_absolute(out);var f=FileAccess.open(out+("/before.json"if before else"/after.json"),FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f=null
 print("V29_DIAGNOSTICS_DONE ","before"if before else"after");g.queue_free();await process_frame;await process_frame;quit()
