extends RefCounted
func walk(g)->void:
 var checks:Array=[];g.player.belt_enabled=false;g.staff.set_all_open(true)
 for i in range(4):await g.get_tree().physics_frame
 if g.only_shot!="EV":
  for route:Dictionary in g.read_json("res://source/physical-routes-v11.json"):
   if g.only_shot!="" and not String(route.id).contains(g.only_shot):continue
   await g.settle(g.v3(route.points[0]));var result=await g.walk_points(route.points,5.0);result.id=route.id;result.kind=route.kind;checks.append(result);print("V7_WALK ",route.id," ",result["pass"])
   if not result["pass"]:print("V7_FAILURE ",JSON.stringify(result));g.write_json("latest-failures.json",checks.filter(func(c):return not c["pass"]))
  if g.only_shot=="ES":
   for e:Dictionary in g.manifest.escalators:
    var a=g.v3(e.test_start);var b=g.v3(e.test_end);await g.settle(a);var result=await g.walk_points([[b.x,b.y,b.z]],2.);result.id=e.id;checks.append(result);print("V7_ES ",e.id," ",result["pass"])
 else:
  for i in range(g.elevators.records.size()):
   var r:Dictionary=g.elevators.records[i];var start=int(r.current)
   if r.data.wing!="B":continue
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
 g.results.checks=checks;g.results.passed=passed;g.results.failed=checks.size()-passed;g.results.not_fps_benchmark=true;g.results.mode="60Hz automatic CharacterBody3D / actual collision; no human playtest";g.results.human_playtest=false;g.write_json("v27-B-elevator-rides.json",g.results);print("V7_COMPLETE ",passed,"/",checks.size());g.get_tree().quit()
