extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://ES_transfer_study_v12.tscn").instantiate();root.add_child(g)
 while g.player==null:await process_frame
 var out="res://evidence/v12/es-transfer"
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--output="):out=arg.trim_prefix("--output=")
 DirAccess.make_dir_recursive_absolute(out);var checks:Array=[]
 for e:Dictionary in g.manifest.escalators:
  var a:Array=e.test_start if e.direction=="UP"else e.test_end;var b:Array=e.test_end if e.direction=="UP"else e.test_start
  checks.append(await walk(g,e.id,[a,b],min(float(a[1]),float(b[1]))-.35))
 for r:Dictionary in g.manifest.transfers:checks.append(await walk(g,r.from+"-TRANSFER",r.points,float(r.points[0][1])-.35))
 # Reverse-direction transfer has the same 8.4m perimeter route, using the outer down lanes.
 var down=g.manifest.escalators.filter(func(e):return e.direction=="DOWN")
 for i in range(3,0,-1):
  var a:Array=down[i].test_start;var b:Array=down[i-1].test_end;var x:float=8.8 if float(a[0])>0 else-8.8
  checks.append(await walk(g,down[i].id+"-TRANSFER",[a,[x,a[1],a[2]],[x,a[1],b[2]],b],float(a[1])-.35))
 var guards:Array=[]
 for y:float in[0.0,5.525,10.875,16.4]:
  for q:Array in[[8.4,0,1,0],[-8.4,0,-1,0],[0,8.4,0,1],[0,-8.4,0,-1]]:
   var p=g.player;p.input_enabled=false;p.position=Vector3(q[0],y+.06,q[1]);p.velocity=Vector3.ZERO
   for i in range(14):await physics_frame
   p.input_enabled=true;p.rotation.y=atan2(float(q[2]),float(q[3]));var low:float=p.position.y;var key=InputEventKey.new();key.physical_keycode=KEY_W;key.pressed=true;Input.parse_input_event(key)
   for i in range(120):await physics_frame;low=min(low,p.position.y)
   key.pressed=false;Input.parse_input_event(key);guards.append({"floor_y":y,"start":[q[0],y,q[1]],"min_y":low,"pass":low>y-.30})
 var result={"checks":checks,"passed":checks.filter(func(c):return c["pass"]).size(),"failed":checks.filter(func(c):return not c["pass"]).size(),"physical_W_input":true,"human_playtest":false,"site_relocated":false,"floor_edge_pushes":guards,"floor_edge_failed":guards.filter(func(c):return not c["pass"]).size(),"status":"UNAPPROVED module only"};var f=FileAccess.open(out+"/es-transfer-test.json",FileAccess.WRITE);f.store_string(JSON.stringify(result,"  "));quit()
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
