extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://ES_site_proposal_v15.tscn").instantiate();g.mode="v17-transfer-comparison";root.add_child(g)
 while g.ui==null or g.results.is_empty():await process_frame
 Engine.max_fps=0;g.staff.set_all_open(true);g.player.belt_enabled=true
 var rows:Array=[]
 for d:Dictionary in g.read_json("res://source/v15/ES-site-proposal.json").transfers:
  var a:Array=d.points[0];var b:Array=d.points[-1];var y:float=a[1];var x:float=d.points[1][0];var z0:float=a[2];var z1:float=b[2];var sign_z:float=sign(z1-z0)
  var left:Array=[[a[0]-.35,y,a[2]],[b[0]-.35,y,b[2]]];var right:Array=[[a[0]+.35,y,a[2]],[b[0]+.35,y,b[2]]]
  var options:Array=[]
  for delta:float in[-.35,.0,.35]:options.append({"id":"rounded-middle-offset-"+str(delta),"points":[a,[x+delta,y,z0+sign_z*.60],[x+delta,y,z1-sign_z*.60],b]})
  for option:Dictionary in options:
   var result:Dictionary=await walk(g,str(d.from)+"/"+str(option.id),option.points,y-.30);var length:float=0
   for i in range(option.points.size()-1):length+=g.v3(option.points[i]).distance_to(g.v3(option.points[i+1]))
   result.design_length_m=length;result.points=option.points;result.option=option.id;result.adopted=false;rows.append(result)
 var f=FileAccess.open("/workspace/v17-review/F6-rounded-width-and-belt.json",FileAccess.WRITE);f.store_string(JSON.stringify({"runtime":g.results,"checks":rows,"human_playtest":false,"machine_layout_unchanged":true,"status":"UNAPPROVED; candidate routes only; measured polyline lengths, not human walking distance"},"  "));quit()
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
