extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();root.add_child(g)
 while g.player==null or g.animator==null:await process_frame
 for i in range(4):await physics_frame
 g.staff.set_all_open(true);g.player.belt_enabled=true
 var seen:Dictionary={};var records:Array=[]
 for e:Dictionary in g.manifest.escalators:
  var wing:String=e.get("wing","B");var key:String=wing+str(e.direction)
  if int(e.levels[0])!=0 or seen.has(key):continue
  if "--short"in OS.get_cmdline_user_args()and key!="AUP":continue
  seen[key]=true
  var start:Vector3=g.v3(e.test_start if e.direction=="UP"else e.test_end);var end:Vector3=g.v3(e.test_end if e.direction=="UP"else e.test_start)
  await g.settle(start);g.player.reset_physics_interpolation();g.player.auto_active=true;g.player.auto_speed=4.3;g.player.auto_target=end
  var dir=(end-start);dir.y=0;dir=dir.normalized();g.player.rotation=Vector3(0,atan2(-dir.x,-dir.z),0);g.player.camera.rotation=Vector3.ZERO
  var samples:Array=[];var interior:Array=[];var reached:bool=false
  for tick in range(800):
   await physics_frame
   var p:Vector3=g.player.position;var u=Vector3(e.u[0],0,e.u[1]);var ss=(p-g.v3(e.c)).dot(u);var half:float=e.run_m*.5;var expected:float=float(e.low_y)+float(e.rise_m)*clamp((ss+half)/float(e.run_m),0.,1.)
   var residual:float=p.y-expected;var camera:Vector3=g.player.camera.get_global_transform_interpolated().origin
   samples.append({"tick":tick,"s_m":ss,"body_y_m":p.y,"camera_y_m":camera.y,"expected_support_y_m":expected,"residual_m":residual,"on_floor":g.player.is_on_floor()})
   if ss>-half+.8 and ss<half-.8:interior.append(residual)
   if Vector2(p.x-end.x,p.z-end.z).length()<.16:reached=abs(p.y-end.y)<.25;break
  g.player.auto_active=false
  var range_m:float=0. if interior.is_empty()else interior.max()-interior.min();var okay:bool=reached and not interior.is_empty()and range_m<.045
  records.append({"id":e.id,"wing":wing,"direction":e.direction,"pass":okay,"reached":reached,"interior_height_residual_range_m":range_m,"samples":samples});print("ES_TRACE ",e.id," ",okay," range=",range_m)
 var passed=records.filter(func(r):return r["pass"]).size();var out="/tmp/v11-es-trace.json"
 for a:String in OS.get_cmdline_user_args():
  if a.begins_with("--trace-output="):out=a.trim_prefix("--trace-output=")
 var file=FileAccess.open(out,FileAccess.WRITE);file.store_string(JSON.stringify({"records":records,"passed":passed,"failed":records.size()-passed,"human_playtest":false,"render_step_simulation_only":true,"physical_tick_Hz":Engine.physics_ticks_per_second},"  "));quit()
