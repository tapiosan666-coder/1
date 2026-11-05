extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="v19-female-walking-contact-observation";root.add_child(g)
 while g.shoppers_v18==null or g.results.is_empty():await process_frame
 Engine.max_fps=0;g.shoppers_v18.set_mode("female_only",true);var a=g.shoppers_v18.actors[0];var d:Dictionary={}
 for row:Dictionary in g.read_json("res://source/v19/shoppers.json").people:
  if row.wing=="A"and row.role=="walking":d=row;break
 a.record=a.record.duplicate(true);a.record.role="walking";a.record.seat_cycle=false;a.record.browse_cycle=false;a.record.path=d.path;a.record.speed=.95;a.point_index=1;a.position=g.v3(d.path[0]);a.rotation.y=float(d.yaw);a.velocity=Vector3.ZERO;a.gait_phase=0.;g.player.set_physics_process(false);g.player.position=a.position+Vector3(0,0,3);a.reset_physics_interpolation()
 var rig:Skeleton3D=a.rig;var indices:Array=[]
 for tag:String in["foot.L","foot.R"]:
  var index=rig.find_bone(tag)
  if index<0:index=rig.find_bone(tag.replace(".","_"))
  indices.append(index)
 var samples:Array=[];var previous:Dictionary={};var unsupported:int=0
 for tick in range(1200):
  await physics_frame
  if a.minimum_y<-.20:unsupported+=1
  if a.female.current_clip!="Walk"or a.speed_current<.75:previous.clear();continue
  var phase:float=a.female.animation.current_animation_position/a.female.animation.current_animation_length
  for side:int in range(2):
   var k:int=indices[side]
   if k<0:continue
   var t:float=fmod(phase+.5*side,1.);var foot:Vector3=rig.global_transform*rig.get_bone_global_pose(k).origin
   if t>.10 and t<.48 and previous.has(side):
    var delta:Vector3=foot-previous[side];delta.y=0;samples.append({"tick":tick,"foot":side,"stance_phase":t,"horizontal_ankle_drift_m_per_tick":delta.length(),"ankle_height_m":foot.y,"speed_mps":a.speed_current})
   if t>.10 and t<.48:previous[side]=foot
   else:previous.erase(side)
 var values:Array=samples.map(func(r):return r.horizontal_ankle_drift_m_per_tick);values.sort();g.write_json("v19-female-foot-contact-observation.json",{"foot_bone_indices":indices,"sample_count":samples.size(),"samples":samples,"median_stance_drift_m_per_tick":values[values.size()/2]if not values.is_empty()else null,"maximum_stance_drift_m_per_tick":values[-1]if not values.is_empty()else null,"unsupported_ticks":unsupported,"simulated_seconds":20,"human_playtest":false,"method":"Actual moving female actor on existing A walking route. Animated ankle pivots sampled during middle of nominal stance, not sole contact or full foot IK against arbitrary terrain. Turning/acceleration and garment intersections require visual evaluation; no zero-sliding claim."});print("V19_FOOT_SAMPLES ",samples.size());quit()
