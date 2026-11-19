extends SceneTree
## Automatic W-key walking of the real mall staircases. One initial placement
## per independent direction, or per entire bank with --continuous.
var g
var stream
var records:={}
var checks:=[]
var output:=""
var reuse_position:=false
func _initialize()->void:call_deferred("run")
func xyz(p:Vector3)->Array:return [p.x,p.y,p.z]
func w(pressed:bool)->void:
 var e:=InputEventKey.new();e.keycode=KEY_W;e.physical_keycode=KEY_W;e.pressed=pressed;Input.parse_input_event(e)
func init_at(p:Vector3)->void:
 w(false);await process_frame
 g.player.auto_active=false;g.player.set_physics_process(false);g.player.position=p+Vector3.UP*.06;g.player.velocity=Vector3.ZERO;stream.prepare_position(p)
 await physics_frame;await physics_frame;g.player.set_physics_process(true);g.player.input_enabled=true
 await g.settle(p)
func leg(target:Vector3,tol:float)->Dictionary:
 var start:Vector3=g.player.position;var max_count:=int((start.distance_to(target)/4.3+3.)*60.)
 var nearest:=INF
 for tick in max_count:
  var p:Vector3=g.player.position
  var dir:=Vector3(target.x-p.x,0.,target.z-p.z)
  nearest=minf(nearest,dir.length())
  if dir.length()<=tol and absf(p.y-target.y)<(.30 if tol>.25 else .16):
   return {"pass":true,"ticks":tick,"closest_horizontal_m":nearest,"position":xyz(p)}
  if p.y<minf(start.y,target.y)-.55:break
  g.player.rotation.y=atan2(-dir.x,-dir.z)
  await physics_frame
 return {"pass":false,"closest_horizontal_m":nearest,"position":xyz(g.player.position),"target":xyz(target),"contacts":g.collision_diagnostics()}
func audit(route:Dictionary,shift:float,radius:float)->bool:
 var original:Array=route.points
 var pts:Array=original.duplicate(true)
 var first:Vector3=g.v3(pts[3])-g.v3(pts[2]);var tangent:Vector3=Vector3.UP.cross(Vector3(first.x,0.,first.z)).normalized()
 for i in range(1,pts.size()-1):pts[i]=xyz(g.v3(pts[i])+tangent*shift)
 if not reuse_position:
  await init_at(g.v3(pts[0]))
 var continued:bool=reuse_position
 var row:={"id":route.id,"lateral_offset_m":shift,"intermediate_steering_radius_m":radius,"final_required_horizontal_m":.16,"stages":[],"pass":false}
 w(true);await physics_frame
 for i in range(1,pts.size()):
  var required:=.16 if i==pts.size()-1 else radius
  var step:=await leg(g.v3(pts[i]),required)
  row.stages.append(step)
  if not step.pass:break
 w(false);await physics_frame
 row["pass"]=row.stages.size()==pts.size()-1 and row.stages[-1].pass
 row["continuous_from_last_landing"]=continued
 row["final_grounded"]=g.player.is_on_floor();row["final"]=xyz(g.player.position)
 checks.append(row)
 var f=FileAccess.open(output,FileAccess.WRITE);f.store_string(JSON.stringify(checks," "));f.close()
 print("RAW_STAIR_W ",route.id," ",shift," ",radius," ",row["pass"]," stages=",row.stages.size())
 return row["pass"] and row["final_grounded"]
func run()->void:
 var continuous:=false
 output=""
 for arg:String in OS.get_cmdline_user_args():
  if arg=="--continuous":continuous=true
  elif arg.begins_with("--out="):output=arg.trim_prefix("--out=")
 if output.is_empty():
  push_error("Supply --out=/writable/path/results.json after --")
  quit(2)
  return
 if DirAccess.make_dir_recursive_absolute(output.get_base_dir())!=OK:
  push_error("Cannot create report directory: "+output.get_base_dir())
  quit(2)
  return
 RenderingServer.set_render_loop_enabled(false)
 g=load("res://main.tscn").instantiate();root.add_child(g)
 while g.results.is_empty():await process_frame
 stream=g.get_node("V30_Runtime");stream.stream_ready=false
 g.shoppers_v18.set_enabled(false,true)
 for route:Dictionary in g.read_json("res://source/physical-routes-v11.json"):
  var wing:=str(route.id).get_slice("-",0)
  if route.kind=="two-flight physical stair support" and wing in ["A","B","C"]:
   records[route.id]=route
 if records.size()!=96:
  push_error("Unexpected number of mall stair directions: "+str(records.size()))
  quit(2)
  return
 var passed:=0
 if continuous:
  for core:String in ["B-K2","C-K-CSW","A-A-KW"]:
   reuse_position=false
   for suffix:String in ["-1-UP","0-UP","1-UP","2-UP","2-DOWN","1-DOWN","0-DOWN","-1-DOWN"]:
    var okay:=await audit(records[core+"-STAIR-"+suffix],0.,.46)
    if not okay:break
    passed+=1
    reuse_position=true
  quit(0 if passed==24 else 1)
 else:
  for id:String in records:
   var okay:=await audit(records[id],0.,.46)
   if not okay:
    for shift:float in [-.19,.19]:
     okay=await audit(records[id],shift,.48)
     if okay:break
   if okay:passed+=1
  quit(0 if passed==96 else 1)
