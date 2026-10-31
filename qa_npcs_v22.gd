extends SceneTree
func _initialize()->void:call_deferred("run")
func save_snapshot(g,id:String)->void:g.write_json(id+".json",g.shoppers_v18.snapshot())
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="v22-preserved-character-physics";root.add_child(g)
 while g.shoppers_v18==null or g.results.is_empty():await process_frame
 while not g.get_node("V21_Route_Derived_Wayfinding").has_meta("ready"):await process_frame
 Engine.max_fps=0;g.player.set_physics_process(false);g.player.input_enabled=false;g.player.position=Vector3(350,0,-23);var issues:Array=[];var overlaps:Array=[];var overlap_probes:int=0;var saved:Dictionary={};var hero=g.shoppers_v18.actors[0]
 for tick in range(5400):
  await physics_frame
  var activity:String=hero.activity;var clip:String=hero.female.current_clip
  if not saved.has("world-seated")and activity=="seated"and tick>60:save_snapshot(g,"world-seated");saved["world-seated"]=tick
  if not saved.has("world-standing")and activity=="waiting"and clip=="Idle":save_snapshot(g,"world-standing");saved["world-standing"]=tick
  if not saved.has("world-walking")and clip=="Walk"and hero.speed_current>.45:save_snapshot(g,"world-walking");saved["world-walking"]=tick
  if not saved.has("world-standup")and activity=="stand_up"and hero.activity_time>.6:save_snapshot(g,"world-standup");saved["world-standup"]=tick
  if not saved.has("world-sitdown")and activity=="sit_down"and hero.activity_time>.6:save_snapshot(g,"world-sitdown");saved["world-sitdown"]=tick
  if tick%120!=119:continue
  for a in g.shoppers_v18.actors:
   var q=PhysicsRayQueryParameters3D.create(a.position+Vector3.UP*.25,a.position-Vector3.UP*.4,1);q.exclude=[a.get_rid()];var hit=g.get_world_3d().direct_space_state.intersect_ray(q)
   if hit.is_empty()or a.position.y<-.20 or a.position.y>.25:issues.append({"id":a.record.id,"tick":tick,"p":[a.position.x,a.position.y,a.position.z],"support":not hit.is_empty()})
   var shape=CapsuleShape3D.new();shape.radius=maxf(.20,a.shape_node.shape.radius-.025);shape.height=a.shape_node.shape.height-.05;var probe=PhysicsShapeQueryParameters3D.new();probe.shape=shape;probe.transform=a.shape_node.global_transform;probe.collision_mask=1;probe.margin=0.;var excluded:Array[RID]=[a.get_rid()]
   for body in a.get_collision_exceptions():excluded.append(body.get_rid())
   probe.exclude=excluded;var hits=g.get_world_3d().direct_space_state.intersect_shape(probe,4);overlap_probes+=1
   if not hits.is_empty():
    var names:Array=[]
    for h in hits:names.append(str(h.collider.name))
    overlaps.append({"id":a.record.id,"tick":tick,"activity":a.activity,"colliders":names})
 var rows:Array=[]
 for a in g.shoppers_v18.actors:rows.append({"id":a.record.id,"visited_states":a.visited_states,"distance_walked_m":a.distance_walked,"minimum_y":a.minimum_y,"maximum_y":a.maximum_y,"floor_safe":a.minimum_y>-.20 and a.maximum_y<.25,"walking_progress":a.record.role!="walking"or a.distance_walked>25.,"seat_cycle_completed":not bool(a.record.get("seat_cycle",false))or a.visited_states.has("sit_down")and a.visited_states.has("stand_up")and a.visited_states.has("approach_seat"),"browse_cycle_completed":not bool(a.record.get("browse_cycle",false))or a.visited_states.has("browse")and a.visited_states.has("leave_display")and a.visited_states.has("approach_display")})
 g.write_json("v20-crowd-physics.json",{"actors":rows,"simulated_seconds":90.,"unsupported_samples":issues,"body_overlap_samples":overlaps,"body_overlap_probes":overlap_probes,"saved_snapshots":saved,"human_playtest":false,"method":"Actual CharacterBody3D60Hz physics. Shape overlap uses capsule inset25mm and excludes designated seat. Not animated mesh intersection or human operation."})
 # Isolated browse scenario borrows an existing validated A shop activity point, retaining hero's ID.
 g.shoppers_v18.set_mode("female_only",true);var original:Dictionary=hero.record.duplicate(true);var borrowed:Dictionary=g.read_json("res://source/v19/shoppers.json").people[10].duplicate(true);borrowed.id=original.id;borrowed.female_reference=true;borrowed.stride_m=.66;borrowed.seat_cycle=false;hero.record=borrowed;hero.browse_phase=0.;hero.clock=0.;hero.position=g.v3(borrowed.home_point);hero.last_position=hero.position;hero.velocity=Vector3.ZERO;hero.speed_current=0.;hero.gait_phase=0.;hero.motion_weight=0.;hero.rotation.y=float(borrowed.yaw);hero.reset_physics_interpolation();var captured:bool=false
 for tick in range(900):
  await physics_frame
  if not captured and hero.activity=="browse"and hero.activity_time>1.0:
   var state:Dictionary=g.shoppers_v18.snapshot();state.character_scenario_override=borrowed;state.scenario_note="Isolated test on an existing A browsing point; same hero ID, no extra NPC and no production plan change";g.write_json("world-browsing.json",state);captured=true
 g.write_json("v20-browse-scenario.json",{"snapshot_created":captured,"temporary_record":borrowed,"production_plan_changed":false,"human_playtest":false});print("FY20_CROWD_PHYSICS floor ",issues.size()," overlap ",overlaps.size()," / ",overlap_probes," browse ",captured);g.queue_free();await process_frame;await process_frame;quit()
