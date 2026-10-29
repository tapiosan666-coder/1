extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="es-approach-input";root.add_child(g)
 while g.ui==null:await process_frame
 g.staff.set_all_open(true);var checks:Array=[];var out="res://evidence/v12/es-approach"
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--output="):out=arg.trim_prefix("--output=")
 DirAccess.make_dir_recursive_absolute(out)
 for e:Dictionary in g.manifest.escalators:
  var u=Vector3(e.u[0],0,e.u[1]);var center=g.v3(e.c);var a=center-u*(float(e.run_m)*.5+2.2);a.y=e.low_y;var b=center+u*(float(e.run_m)*.5+2.2);b.y=e.high_y
  var aa=[a.x,a.y,a.z];var bb=[b.x,b.y,b.z];var points=[aa,bb]if e.direction=="UP"else[bb,aa]
  checks.append(await walk(g,e.id,points,float(e.low_y)-.3))
 var f=FileAccess.open(out+"/es-approach-input.json",FileAccess.WRITE);f.store_string(JSON.stringify({"checks":checks,"passed":checks.filter(func(c):return c["pass"]).size(),"failed":checks.filter(func(c):return not c["pass"]).size(),"method":"Actual physical W input, 0.7m beyond both 1.5m landings; complete boarding, flight and exit, not an inside-landing start","human_playtest":false,"runtime":g.results},"  "));quit()

func walk(g,id:String,points:Array,floor_limit:float)->Dictionary:
 var p:CharacterBody3D=g.player;p.input_enabled=false;p.auto_active=false;p.velocity=Vector3.ZERO;p.position=Vector3(points[0][0],points[0][1]+.06,points[0][2])
 for i in range(14):await physics_frame
 p.input_enabled=true;var okay:bool=true;var info:Dictionary={}
 for q:Array in points.slice(1):
  var target=Vector3(q[0],q[1],q[2]);var d=target-p.position;d.y=0;p.rotation.y=atan2(-d.x,-d.z);var reached:bool=false;var old=p.position;var key=InputEventKey.new();key.physical_keycode=KEY_W;key.pressed=true;Input.parse_input_event(key)
  for tick in range(1200):
   await physics_frame;var flat=p.position-target;flat.y=0
   if flat.length()<.20 and abs(p.position.y-target.y)<.3:reached=true;break
   if p.position.y<floor_limit:info.fall_y=p.position.y;break
   if tick%120==119:
    if p.position.distance_to(old)<.05:break
    old=p.position
  key.pressed=false;Input.parse_input_event(key)
  if not reached:okay=false;info.position=[p.position.x,p.position.y,p.position.z];info.target=q;break
 print("TRANSFER_INPUT ",id," ",okay," ",JSON.stringify(info));return{"id":id,"pass":okay,"detail":info}
