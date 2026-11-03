extends SceneTree
var checks:Array=[]
var g
func _initialize()->void:call_deferred("run")
func check(id:String,ok:bool,details:Variant=null)->void:
 checks.append({"id":id,"pass":ok,"details":details});print("V26_CHECK ",id," ",ok)
func run()->void:
 var out:String="res://evidence/v28-QA"
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--qa-output="):out=arg.trim_prefix("--qa-output=")
 g=load("res://main.tscn").instantiate();g.mode="v26-architecture-QA";root.add_child(g)
 while g.results.is_empty():await process_frame
 var module=g.get_node_or_null("V26_Mall_Architecture")
 if module==null:push_error("Missing v26 module");quit(1);return
 while not module.has_meta("ready"):await process_frame
 while not g.get_node("V28_Architecture").has_meta("ready"):await process_frame
 g.shoppers_v18.set_frozen(true);g.player.set_physics_process(false)
 check("480-store-identities",g.read_json("res://source/v25/retail-plan.json").stores.size()==480)
 check("43-test-NPC",g.shoppers_v18.actors.size()==43)
 check("three-double-door-entrances",module.entrances.size()==3,module.entrances)
 check("six-collidable-sliding-doors",module.doors.size()==6)
 var door_rows:Array=[]
 for d in module.doors:d.sense_npcs=false
 for d in module.doors:
  g.player.global_position=d.global_position+d.global_basis.z*3.;await physics_frame
  for tick in 60:await physics_frame
  var opened:bool=d.progress>.98
  # Keep a capsule in the threshold longer than the close delay: no closing into the player.
  g.player.global_position=d.global_position
  for tick in 150:await physics_frame
  var held:bool=d.progress>.98
  g.player.global_position=Vector3(1000,0,1000)
  for tick in 180:await physics_frame
  var closed:bool=d.progress<.02
  var w=g.get_node("V21_Route_Derived_Wayfinding");var blocked:bool=not w.sweep(d.global_position-d.global_basis.z,d.global_position+d.global_basis.z)
  door_rows.append({"door":str(d.get_path()),"opens":opened,"threshold_hold":held,"closes":closed,"closed_collision_blocks":blocked,"state":d.state()})
 check("door-open-hold-close",door_rows.size()==6 and door_rows.all(func(r):return r.opens and r.threshold_hold and r.closes and r.closed_collision_blocks),door_rows)
 if not module.doors.is_empty():
  var door=module.doors[0];var actor=g.shoppers_v18.actors[0];var saved:Vector3=actor.global_position;var visible_before:bool=actor.visible;actor.visible=true;actor.global_position=door.global_position;door.sense_npcs=true;g.player.global_position=Vector3(1000,0,1000)
  for tick in 60:await physics_frame
  check("existing-NPC-opens-door",door.progress>.98)
  actor.global_position=saved;actor.visible=visible_before;door.sense_npcs=false
 # Actual CharacterBody passes through both physical doors in both directions.
 var walks:Array=[]
 for e in module.entrances:
  for reverse in [false,true]:
   var a:Vector3=g.v3(e.inside if reverse else e.outside);var b:Vector3=g.v3(e.outside if reverse else e.inside)
   g.player.global_position=a+Vector3.UP*.08;g.player.velocity=Vector3.ZERO
   for tick in 450:
    var delta:Vector3=b-g.player.global_position;delta.y=0
    if delta.length()<.25:break
    g.player.velocity=delta.normalized()*2.;g.player.velocity.y=-2.;g.player.move_and_slide();await physics_frame
   var residual:Vector3=g.player.global_position-b;residual.y=0
   walks.append({"entrance":e.id,"reverse":reverse,"pass":residual.length()<.35,"residual_m":residual.length(),"feet_y":g.player.global_position.y})
 check("six-two-door-physical-walks",walks.size()==6 and walks.all(func(r):return r["pass"]),walks)
 g.player.global_position=Vector3(1000,0,1000);await physics_frame
 var way=g.get_node("V21_Route_Derived_Wayfinding")
 check("navigation-source-integrity",way.stats.source_mismatches.is_empty(),way.stats.source_mismatches)
 check("existing-navigation-routes",way.stats.blocked_rows.is_empty(),way.stats.blocked_rows)
 var route_issues:Array=[]
 for door in module.doors:door.force_open=true
 for tick in 60:await physics_frame
 for route:Dictionary in way.checks:
  if not route["pass"]:continue
  var status:Dictionary=way.check_path(route.actual_path)
  if not status["pass"]:route_issues.append({"sign":route.sign,"target":route.target,"reason":status.reason})
 check("routes-after-v26-colliders",route_issues.is_empty(),route_issues)
 var evacuations:Array=module.reports.get("local_evacuation_diagrams",[])
 check("three-local-evacuation-diagrams",evacuations.size()==3 and evacuations.all(func(e):return way.check_path(e.route)["pass"]),evacuations)
 var fire_rows:Array=[]
 for e:Dictionary in module.reports.wall_equipment:
  var p=g.v3(e.p);var n=Vector3(e.normal[0],0,e.normal[1]);fire_rows.append({"p":e.p,"actual_wall_ray":e.actual_wall_ray,"approach_clear":module.standing_clear(p+n*.9)and way.sweep(p+n*1.4,p+n*.7)})
 check("three-supported-fire-equipment-groups",fire_rows.size()>=3 and fire_rows.all(func(r):return r.actual_wall_ray and r.approach_clear),fire_rows)
 var audit:Dictionary=g.read_json("res://source/v26/guide-store-audit.json")
 check("guide-catalog-all-15-floors",audit.total_store_count==480 and audit.rows.size()==15 and audit.source_sha256==FileAccess.get_sha256("res://source/v25/retail-plan.json.zst"))
 check("all-three-wing-floor-finishes",module.reports.floor_surfaces.any(func(r):return r.wing=="A")and module.reports.floor_surfaces.any(func(r):return r.wing=="B")and module.reports.floor_surfaces.any(func(r):return r.wing=="C"))
 check("existing-slab-collision-retained",not module.reports.structural_floor_changed)
 check("rotated-box-batching-preserves-geometry",module.reports.batched_box_maximum_corner_error_m<.0001,module.reports.batched_box_maximum_corner_error_m)
 check("guides-at-entrances-and-plazas",module.reports.guides.size()==6,module.reports.guides)
 check("guides-in-public-circulation",module.reports.guides.all(func(r):return module.public_point(g.v3(r.p),r.wing)))
 var report={"checks":checks,"door_tests":door_rows,"walks":walks,"architecture":module.reports,"human_playtest":false,"actual_CharacterBody_move_and_slide":true,"physics_hz":60,"renderer":RenderingServer.get_current_rendering_method()}
 DirAccess.make_dir_recursive_absolute(out);var f=FileAccess.open(out+"/architecture-QA.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f=null
 var failed:int=checks.filter(func(r):return not r["pass"]).size();print("V26_RESULT ",checks.size()," checks, ",failed," failures");g.queue_free();await process_frame;quit(1 if failed else 0)
