extends SceneTree
func _initialize()->void:call_deferred("run")
func key(code:int,pressed:bool,physical:bool=false)->void:
 var e=InputEventKey.new();e.pressed=pressed
 if physical:e.physical_keycode=code
 else:e.keycode=code
 Input.parse_input_event(e)
func run()->void:
 var g=load("res://main.tscn").instantiate();root.add_child(g)
 while g.ui==null:await process_frame
 for tick in range(5):await physics_frame
 var checks:Array=[];g.player.input_enabled=false;g.player.belt_enabled=false
 # Every shaft/stop: push into the central landing gate and both former side gaps while the car is elsewhere.
 for index in range(g.elevators.records.size()):
  var r:Dictionary=g.elevators.records[index];var n=Vector3(r.data.inside[0],0,r.data.inside[1]);var u=Vector3(-n.z,0,n.x)
  for stop in range(r.data.stops.size()):
   if stop==int(r.current):continue
   var yy:float=r.data.stops[stop].y
   for offset in[0.,-float(r.data.door_width)*.5-.34,float(r.data.door_width)*.5+.34]:
    var door=Vector3(r.data.door_xz[0],yy,r.data.door_xz[2]);var start=door-n*.85+u*offset;await g.settle(start);g.player.reset_physics_interpolation()
    var minimum:float=g.player.position.y;var furthest:float=-10;g.player.auto_active=true;g.player.auto_speed=2.0;g.player.auto_target=start+n*2.0
    for tick in range(75):
     await physics_frame;minimum=min(minimum,g.player.position.y);furthest=max(furthest,(g.player.position-door).dot(n))
    g.player.auto_active=false
    var okay:bool=minimum>yy-.20 and furthest<.12
    checks.append({"id":str(r.data.id)+"-"+str(r.data.stops[stop].label)+"-shaft-side-"+str(offset),"pass":okay,"floor_y":yy,"minimum_body_y":minimum,"inside_distance_m":furthest,"offset_m":offset})
    if not okay:print("SHAFT_FAILURE ",JSON.stringify(checks[-1]))
  # Move the empty car away and probe the initially occupied floor too: every landing is tested with no car behind its doors.
  var initial:int=r.current;var away:int=0 if initial!=0 else 1;var moved:bool=g.elevators.request(index,away)
  for tick in range(1400):
   await physics_frame
   if r.state=="open"and int(r.current)==away:break
  var yy:float=r.data.stops[initial].y;var door=Vector3(r.data.door_xz[0],yy,r.data.door_xz[2])
  for offset in[0.,-float(r.data.door_width)*.5-.34,float(r.data.door_width)*.5+.34]:
   var start=door-n*.85+u*offset;await g.settle(start);g.player.reset_physics_interpolation();g.player.auto_active=true;g.player.auto_speed=2.;g.player.auto_target=start+n*2.;var minimum:float=g.player.position.y;var inside:float=-10
   for tick in range(75):await physics_frame;minimum=min(minimum,g.player.position.y);inside=max(inside,(g.player.position-door).dot(n))
   g.player.auto_active=false;checks.append({"id":str(r.data.id)+"-initial-floor-car-absent-"+str(offset),"pass":moved and minimum>yy-.20 and inside<.12,"floor_y":yy,"minimum_body_y":minimum,"inside_distance_m":inside})
 # Test the actual F-key UI: call to a different floor; enter, select a destination, ride, exit.
 var r:Dictionary=g.elevators.records[0];var d:Dictionary=r.data;var n=Vector3(d.inside[0],0,d.inside[1]);var stop:int=2;var door=Vector3(d.door_xz[0],d.stops[stop].y,d.door_xz[2]);await g.settle(door-n*.9);g.player.input_enabled=true;g.player.rotation=Vector3(0,atan2(-n.x,-n.z),0);g.player.camera.rotation=Vector3.ZERO;key(KEY_F,true);await process_frame;await process_frame;key(KEY_F,false);await process_frame
 var called:bool=int(r.target)==stop and g.ui.overlay==""
 for tick in range(1300):
  await physics_frame
  if r.state=="open" and int(r.current)==stop:break
 var arrived:bool=r.state=="open"and int(r.current)==stop
 var enter=await g.walk_points([[r.car.position.x,r.car.position.y,r.car.position.z]],2.0);g.player.auto_active=false;key(KEY_F,true);await process_frame;await process_frame;key(KEY_F,false);await process_frame
 var menu:bool=g.ui.overlay=="lift";var clicked:bool=false
 for child in g.ui.lift_buttons.get_children():
  if child is Button and child.text=="3F":child.pressed.emit();clicked=true;break
 for tick in range(1300):
  await physics_frame
  if r.state=="open"and int(r.current)==3:break
 var exited=await g.walk_points([[door.x-n.x*.9,d.stops[3].y,door.z-n.z*.9]],2.0)
 checks.append({"id":"F-key-call-enter-choose-3F-ride-exit","pass":called and arrived and enter["pass"]and menu and clicked and int(r.current)==3 and exited["pass"],"called":called,"arrived":arrived,"entry":enter,"menu":menu,"destination_button":clicked,"exit":exited})
 # Closing doors must reopen when a passenger enters the threshold after travel was requested.
 var current_y:float=r.car.position.y;await g.walk_points([[r.car.position.x,current_y,r.car.position.z]],2.0);g.player.auto_active=false
 var previous_reopens:int=r.reopen_count;var requested:bool=g.elevators.request(0,0)
 g.player.auto_active=true;g.player.auto_speed=7.0;g.player.auto_target=Vector3(d.door_xz[0],current_y,d.door_xz[2])-n*.15
 for tick in range(80):
  await physics_frame
  if int(r.reopen_count)>previous_reopens:g.player.auto_active=false;break
 g.player.auto_active=false
 for tick in range(70):await physics_frame
 checks.append({"id":"closing-door-threshold-reopens-before-car-departs","pass":requested and int(r.reopen_count)>previous_reopens and abs(r.car.position.y-current_y)<.002 and r.state=="open","reopen_count":r.reopen_count,"state":r.state,"car_movement_m":r.car.position.y-current_y})
 var out={"checks":checks,"passed":checks.filter(func(x):return x["pass"]).size(),"failed":checks.filter(func(x):return not x["pass"]).size(),"human_playtest":false,"method":"Actual CharacterBody3D pushes against every closed landing, plus injected F-key and real destination button interaction.","runtime":g.results};g.write_json("shaft-safety-and-F.json",out);print("SAFETY_COMPLETE ",out.passed,"/",checks.size());quit()
