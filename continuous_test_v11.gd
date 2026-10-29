extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();root.add_child(g)
 while g.ui==null:await process_frame
 var route:Dictionary=g.read_json("res://source/v11/continuous-route.json");g.player.input_enabled=false;g.player.belt_enabled=true
 await g.settle(g.v3(route.points[0]));g.player.reset_physics_interpolation()
 var checks:Array=[];var path_length:float=0.;var previous:Vector3=g.player.position
 for i in range(1,route.points.size()):
  var target:Vector3=g.v3(route.points[i]);var direction=(target-g.player.position).normalized();g.player.rotation=Vector3(0,atan2(-direction.x,-direction.z),0);g.player.camera.rotation=Vector3.ZERO
  var check:Dictionary=await g.walk_points([route.points[i]],4.3);check["segment"]=i;check["target"]=route.points[i];checks.append(check);path_length+=previous.distance_to(g.player.position);previous=g.player.position
  print("CONTINUOUS_SEGMENT ",i," ",check["pass"])
  if not check["pass"]:break
 var okay:bool=checks.size()==route.points.size()-1 and checks.all(func(r):return r["pass"])
 g.write_json("continuous-A-B-C.json",{"pass":okay,"checks":checks,"planned_route_m":route.length_m,"checkpoint_chords_m":path_length,"teleports_after_initial_placement":0,"human_playtest":false,"method":"Continuous CharacterBody3D walk at 4.3m/s, turning the camera at each waypoint; no intermediate placement, no noclip; automated, not manual input.","runtime":g.results});print("CONTINUOUS_COMPLETE ",okay);quit()
