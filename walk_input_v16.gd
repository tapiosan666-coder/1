extends RefCounted
func walk(g,id:String,points:Array,floor_limit:float)->Dictionary:
 var p:CharacterBody3D=g.player;p.input_enabled=false;p.auto_active=false;p.velocity=Vector3.ZERO;p.position=Vector3(points[0][0],points[0][1]+.06,points[0][2])
 for i in range(14):await g.get_tree().physics_frame
 p.input_enabled=true;var okay:bool=true;var info:Dictionary={}
 for q:Array in points.slice(1):
  var target=Vector3(q[0],q[1],q[2]);var d=target-p.position;d.y=0;p.rotation.y=atan2(-d.x,-d.z);var reached:bool=false;var old=p.position;var max_dy:float=0;var last_y:float=p.position.y;var key=InputEventKey.new();key.physical_keycode=KEY_W;key.pressed=true;Input.parse_input_event(key)
  for tick in range(int((p.position.distance_to(target)/4.3+6.0)*60)):
   await g.get_tree().physics_frame;var aim=target-p.position;aim.y=0
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
