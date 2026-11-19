extends SceneTree
## F calls the physical cabin from the basement. After boarding, F opens the
## live stop picker and the test emits the selected Button.pressed signal.
var g
var runtime
var dest:String
var report:={"scope":"Forward+ runtime in headless mode, automatic CharacterBody3D at fixed 60Hz. Player is placed once at each independent core/subtest, never reset during a chain. No human playtest.","lifts":[],"stairs":[]}
func _initialize()->void:call_deferred("run")
func xyz(p:Vector3)->Array:return [p.x,p.y,p.z]
func store()->void:
 var f=FileAccess.open(dest,FileAccess.WRITE);f.store_string(JSON.stringify(report," "));f.close()
func key_f()->void:
 var e:=InputEventKey.new();e.keycode=KEY_F;e.physical_keycode=KEY_F;e.pressed=true;Input.parse_input_event(e)
 await process_frame; e=InputEventKey.new();e.keycode=KEY_F;e.physical_keycode=KEY_F;e.pressed=false;Input.parse_input_event(e);await process_frame
func wait_stop(record:Dictionary,stop:int)->Dictionary:
 var seen:={}
 var bound:=0.
 var ystep:=0.
 var start_y:float=g.player.position.y
 var prev_y:=start_y
 var carried:bool=g.elevators.is_inside(g.elevators.records.find(record))
 var count:=0
 for tick:int in 1350:
  await physics_frame
  seen[record.state]=true;count+=1
  if carried:bound=maxf(bound,absf(g.player.position.y-record.car.position.y));ystep=maxf(ystep,absf(g.player.position.y-prev_y));prev_y=g.player.position.y
  if record.state=="open" and int(record.current)==stop:break
 return {"arrived":record.state=="open" and int(record.current)==stop,"ticks":count,"states":seen.keys(),"onboard":carried,"player_y_range":[start_y,g.player.position.y],"largest_player_to_car_floor_m":bound,"largest_player_dy_per_tick_m":ystep}
func landing(r:Dictionary,i:int)->Vector3:
 return Vector3(r.data.door_xz[0],r.data.stops[i].y,r.data.door_xz[2])-Vector3(r.data.inside[0],0,r.data.inside[1])*1.28
func init_at(p:Vector3)->void:
 g.player.auto_active=false;g.player.velocity=Vector3.ZERO;g.player.set_physics_process(false);g.player.position=p+Vector3.UP*.06;runtime.prepare_position(p)
 await physics_frame;await physics_frame;g.player.set_physics_process(true);g.player.input_enabled=false
 await g.settle(p)
func lift(r:Dictionary)->void:
 var index:int=g.elevators.records.find(r)
 var report_item:={"id":r.data.id,"wing":r.data.wing,"rides":[],"all_ok":true}
 report.lifts.append(report_item)
 var p:=landing(r,0)
 await init_at(p)
 var normal:=Vector3(r.data.inside[0],0.,r.data.inside[1])
 var mouth:=Vector3(r.data.door_xz[0],p.y,r.data.door_xz[2])
 g.player.auto_target=mouth+normal*.9
 g.player.auto_speed=2.5
 g.player.auto_active=true
 var intrusion:=-INF
 var lowest:float=g.player.position.y
 for i in 65:
  await physics_frame
  intrusion=maxf(intrusion,(g.player.position-mouth).dot(normal));lowest=minf(lowest,g.player.position.y)
 g.player.auto_active=false
 var retreat:Dictionary=await g.walk_points([xyz(p)],2.6)
 report_item["absent_cabin_landing_gate"]={"max_centre_into_shaft_m":intrusion,"minimum_player_y":lowest,"pass":intrusion<-.18 and lowest>=p.y-.14 and retreat.get("pass",false),"contact":g.collision_diagnostics()}
 g.player.camera.look_at(Vector3(r.data.door_xz[0],p.y+1.53,r.data.door_xz[2]))
 g.player.camera.force_update_transform()
 report_item["call_nearest_index_matches"]=g.elevators.nearest()==index
 await key_f()
 var called:Dictionary=await wait_stop(r,0)
 report_item["ground_call"]=called
 if not called.arrived or not report_item.call_nearest_index_matches:
  report_item.all_ok=false;store();return
 for stop:int in [4,3,2,1,0]:
  var current:int=r.current
  var foot:Vector3=r.car.global_position
  var step:={"from":r.data.stops[current].label,"to":r.data.stops[stop].label}
  var enter:Dictionary=await g.walk_points([xyz(foot)],2.2)
  step["entry_pass"]=enter.get("pass",false)
  step["entry_check"]=enter if not step.entry_pass else {"position":xyz(g.player.position)}
  if step.entry_pass:
   await key_f()
   step["normal_floor_selector"]=g.ui.overlay=="lift" and g.ui.lift_index==index
   var button:Button=null
   for child in g.ui.lift_buttons.get_children():
    if child is Button and child.text==r.data.stops[stop].label and not child.is_queued_for_deletion():button=child
   if step.normal_floor_selector and button!=null:
    button.pressed.emit()
    step["ride"]=await wait_stop(r,stop)
    var out:=landing(r,stop)
    if step.ride.arrived:
     var leave:Dictionary=await g.walk_points([xyz(out)],2.2)
     step["exit_pass"]=leave.get("pass",false)
     step["exit_check"]=leave if not step.exit_pass else {"position":xyz(g.player.position),"on_floor":g.player.is_on_floor()}
  step["pass"]=step.entry_pass and step.get("normal_floor_selector",false) and step.get("ride",{}).get("arrived",false) and step.get("ride",{}).get("onboard",false) and step.get("ride",{}).get("largest_player_to_car_floor_m",99.)<.20 and step.get("exit_pass",false)
  report_item.rides.append(step)
  print("REAL_LIFT ",r.data.id," ",step.from," ",step.to," ",step["pass"])
  store()
  if not step["pass"]:report_item.all_ok=false;break
 if g.ui.overlay!="":g.ui.close()
 store()
func stair(core:String,idx:Dictionary)->void:
 var first:Dictionary=idx[core+"-STAIR--1-UP"]
 await init_at(g.v3(first.points[0]))
 var reset_needed:=false
 var independent_recovery:=0
 for name:String in ["-1-UP","0-UP","1-UP","2-UP","2-DOWN","1-DOWN","0-DOWN","-1-DOWN"]:
  var r:Dictionary=idx[core+"-STAIR-"+name]
  if reset_needed:
   await init_at(g.v3(r.points[0]));independent_recovery+=1;reset_needed=false
  var route:Dictionary=await g.walk_points(r.points.slice(1),2.7)
  var row:={"id":r.id,"from_y":r.points[0][1],"to_y":r.points[-1][1],"steps":r.points.size()-1,"segment_relocations_since_first_landing":independent_recovery,"pass":route.get("pass",false),"ticks":route.ticks,"on_final_floor":g.player.is_on_floor(),"end":xyz(g.player.position),"walk":route}
  report.stairs.append(row);store()
  print("REAL_STAIR ",r.id," ",row["pass"])
  if not row["pass"]:reset_needed=true
func run()->void:
 var extended:=false
 var stair_only:=false
 var lifts_only:=false
 dest=""
 for a in OS.get_cmdline_user_args():
  if a=="--extended":extended=true
  if a=="--stair-only":stair_only=true
  if a=="--lifts-only":lifts_only=true
  if a.begins_with("--out="):dest=a.trim_prefix("--out=")
 if dest.is_empty() or (stair_only and lifts_only):
  push_error("Supply --out=/writable/path/results.json and at most one mode switch.")
  quit(2)
  return
 if DirAccess.make_dir_recursive_absolute(dest.get_base_dir())!=OK:
  push_error("Cannot create report directory: "+dest.get_base_dir())
  quit(2)
  return
 RenderingServer.set_render_loop_enabled(false)
 g=load("res://main.tscn").instantiate();root.add_child(g)
 while g.results.is_empty():await process_frame
 g.player.input_enabled=false;g.shoppers_v18.set_enabled(false,true)
 runtime=g.get_node("V30_Runtime");runtime.stream_ready=false
 var lifts:={}
 for record:Dictionary in g.elevators.records:lifts[record.data.id]=record
 var stairs:={}
 for route:Dictionary in g.read_json("res://source/physical-routes-v11.json"):
  if route.kind=="two-flight physical stair support":stairs[route.id]=route
 var order:=["B-K2","C-K-CSW","A-A-KW"]
 if extended:order=["A-A-KE","A-A-KS","B-K1","B-K3","C-K-CW","C-K-CNW","C-K-CNE","C-K-CE","C-K-CSE"]
 for id:String in order:
  if not stair_only:await lift(lifts[id])
  if not lifts_only:await stair(id,stairs)
 report["complete"]=true;store()
 var good_lifts:bool=report.lifts.all(func(r):return r.all_ok and r.rides.size()==5 and r.absent_cabin_landing_gate.pass)
 var good_stairs:bool=report.stairs.all(func(r):return r.pass)
 quit(0 if good_lifts and good_stairs else 1)
