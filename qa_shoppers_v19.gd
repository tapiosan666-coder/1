extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="v19-activity-physics-QA";root.add_child(g)
 while g.shoppers_v18==null or g.results.is_empty():await process_frame
 g.player.set_physics_process(false);g.player.input_enabled=false;g.player.position=Vector3(325,0,-63);Engine.max_fps=0;var samples:Array=[];var state_samples:Array=[];var snapshots:Array=[]
 for tick in range(5400):
  await physics_frame
  if tick in[1199,2399,3599]:g.write_json("v19-npc-snapshot-"+str(tick+1)+".json",g.shoppers_v18.snapshot())
  if tick%120==119:
   for a in g.shoppers_v18.actors:
    var q=PhysicsRayQueryParameters3D.create(a.position+Vector3(0,.25,0),a.position-Vector3(0,.40,0),1);q.exclude=[a.get_rid()];var hit=g.get_world_3d().direct_space_state.intersect_ray(q)
    if hit.is_empty()or a.position.y<-.20 or a.position.y>.25:samples.append({"id":a.record.id,"tick":tick,"p":[a.position.x,a.position.y,a.position.z],"activity":a.activity,"support":not hit.is_empty()})
    if a.activity=="seated"and bool(a.record.get("seat_cycle",false)):
     var wanted=a.vec(a.record.stand_point);var error:float=Vector2(a.position.x-wanted.x,a.position.z-wanted.z).length()
     if error>.10:state_samples.append({"id":a.record.id,"tick":tick,"seat_anchor_error_m":error})
 var rows:Array=[]
 for a in g.shoppers_v18.actors:
  rows.append({"id":a.record.id,"female":a.female!=null,"role":a.record.role,"visited_states":a.visited_states,"distance_walked_m":a.distance_walked,"minimum_y":a.minimum_y,"maximum_y":a.maximum_y,"floor_safe":a.minimum_y>-.20 and a.maximum_y<.25,"walking_progress":a.record.role!="walking"or a.distance_walked>25.,"seat_cycle_completed":not bool(a.record.get("seat_cycle",false))or a.visited_states.has("sit_down")and a.visited_states.has("stand_up")and a.visited_states.has("approach_seat"),"browse_cycle_completed":not bool(a.record.get("browse_cycle",false))or a.visited_states.has("browse")and a.visited_states.has("leave_display")and a.visited_states.has("approach_display")})
 g.write_json("v19-npc-activity-physics.json",{"actors":rows,"simulated_seconds":90.,"unsupported_samples":samples,"seat_alignment_failures":state_samples,"human_playtest":false,"method":"Actual Godot CharacterBody3D 60Hz simulation, floor support rays and actual arrival-gated activity states, not human operation"});print("V19_ACTIVITY_QA floor issues ",samples.size()," seat errors ",state_samples.size()," incomplete actors ",rows.filter(func(r):return not r.floor_safe or not r.walking_progress or not r.seat_cycle_completed or not r.browse_cycle_completed).size());quit()
