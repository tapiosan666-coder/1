extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var es:bool="--es-site-proposal"in OS.get_cmdline_user_args()
 var c:bool="--c-open-proposal"in OS.get_cmdline_user_args()
 var g=load("res://ES_site_proposal_v15.tscn"if es else"res://C_proposal_v12.tscn"if c else"res://main.tscn").instantiate();g.mode="v16-physics";root.add_child(g)
 while g.ui==null:await process_frame
 Engine.max_fps=0;g.staff.set_all_open(true);g.player.belt_enabled=not c
 var checks:Array=[];var transfers:Array=[]
 if es:
  for e:Dictionary in g.manifest.escalators:
   if not str(e.id).begins_with("B-WEST-V15"):continue
   var u=Vector3(e.u[0],0,e.u[1]);var a=g.v3(e.c)-u*(float(e.run_m)/2+2.2);a.y=e.low_y;var b=g.v3(e.c)+u*(float(e.run_m)/2+2.2);b.y=e.high_y
   var aa=[a.x,a.y,a.z];var bb=[b.x,b.y,b.z];checks.append(await walk(g,e.id,[aa,bb]if e.direction=="UP"else[bb,aa],float(e.low_y)-.30))
  for t:Dictionary in g.read_json("res://source/v15/ES-site-proposal.json").transfers:transfers.append(await walk(g,"TRANSFER-"+str(t.from),t.points,float(t.points[0][1])-.30))
  for y:float in[5.525,10.875]:
   var x:float=-199.8 if y<6 else -184.2;var side:float=-200.8 if y<6 else -183.2;var z0:float=-19.8 if y<6 else -13.4;var z1:float=-13.4 if y<6 else -19.8
   transfers.append(await walk(g,"DOWN-TRANSFER-"+str(y),[[x,y,z0],[side,y,z0],[side,y,z1],[x,y,z1]],y-.30))
  for y:float in[0.,5.525,10.875,16.4]:
   for side:int in[-1,1]:
    var x0:float=-221.0 if side<0 else-163.0;var x1:float=-201.5 if side<0 else-182.5
    transfers.append(await walk(g,"PUBLIC-CONNECTOR-"+str(y)+"-"+str(side),[[x0,y,-15.5],[x1,y,-15.5]],y-.30))
 if c:
  for row:Dictionary in g.read_json("res://source/v15/C-outlet-proposal.json").gallery_connections:
   for lev:int in row.get("levels",[1]):
    var y:float={1:5.525,2:10.875}[lev]
    var points:Array=[]
    for p:Array in row.points:points.append([p[0]+429,y,p[1]-46])
    checks.append(await walk(g,row.id+"-"+str(y),points,y-.30))
 var out="res://evidence/v16/physics-"+("ES"if es else"C"if c else"normal")+".json"
 var f=FileAccess.open(out,FileAccess.WRITE);f.store_string(JSON.stringify({"checks":checks,"transfers":transfers,"human_playtest":false,"method":"Physical W input with automated per-tick steering / unchanged player controller. C access bridges: conveyor off; ES boarding separately tests conveyor on. Not human play","runtime":g.results},"  "));quit()

func walk(g,id:String,points:Array,floor_limit:float)->Dictionary:
 var p:CharacterBody3D=g.player;p.input_enabled=false;p.auto_active=false;p.velocity=Vector3.ZERO;p.position=Vector3(points[0][0],points[0][1]+.06,points[0][2])
 for i in range(14):await physics_frame
 p.input_enabled=true;var okay:bool=true;var info:Dictionary={}
 for q:Array in points.slice(1):
  var target=Vector3(q[0],q[1],q[2]);var d=target-p.position;d.y=0;p.rotation.y=atan2(-d.x,-d.z);var reached:bool=false;var old=p.position;var max_dy:float=0;var last_y:float=p.position.y;var key=InputEventKey.new();key.physical_keycode=KEY_W;key.pressed=true;Input.parse_input_event(key)
  for tick in range(int((p.position.distance_to(target)/4.3+6.0)*60)):
   await physics_frame;var aim=target-p.position;aim.y=0
   if aim.length()>.12:p.rotation.y=atan2(-aim.x,-aim.z)
   max_dy=max(max_dy,abs(p.position.y-last_y));last_y=p.position.y;var flat=p.position-target;flat.y=0
   if flat.length()<.20 and abs(p.position.y-target.y)<.3:reached=true;break
   if p.position.y<floor_limit:info.fall_y=p.position.y;break
   if tick%120==119:
    if p.position.distance_to(old)<.05:break
    old=p.position
  info.max_frame_rise_m=max(float(info.get("max_frame_rise_m",0)),max_dy);key.pressed=false;Input.parse_input_event(key)
  if not reached:okay=false;info.position=[p.position.x,p.position.y,p.position.z];info.target=q;info.contacts=g.collision_diagnostics();break
 print("TRANSFER_INPUT ",id," ",okay," ",JSON.stringify(info));return{"id":id,"pass":okay,"detail":info}
