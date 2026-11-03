extends Node3D
var records:Array=[]
var player:CharacterBody3D
var mats:Dictionary
var font:Font
func boxnode(size:Vector3,pos:Vector3,material:Material,parent:Node3D,collision:bool=true)->void:
 var mesh=MeshInstance3D.new();var cube=BoxMesh.new();cube.size=size;cube.material=material;mesh.mesh=cube;mesh.position=pos;parent.add_child(mesh)
 if collision:
  var col=CollisionShape3D.new();var shape=BoxShape3D.new();shape.size=size;col.shape=shape;col.position=pos;parent.add_child(col)
func setup(data:Array,p:CharacterBody3D,materials:Dictionary,f:Font)->void:
 player=p;mats=materials;font=f
 for d:Dictionary in data:
  var n=Vector3(d.inside[0],0,d.inside[1]);var u=Vector3(d.u[0],0,d.u[1]);var tangent=Vector3(-n.z,0,n.x)
  var car=AnimatableBody3D.new();car.name="Cabin_"+d.id;car.sync_to_physics=false;car.position=Vector3(d.center[0],d.stops[1].y if d.stops.size()==5 else d.stops[0].y,d.center[2]);car.basis=Basis(tangent,Vector3.UP,n);car.collision_layer=1;add_child(car)
  var w=float(d.width);var dep=float(d.depth)
  boxnode(Vector3(w,.18,dep),Vector3(0,-.09,0),mats.metal,car)
  boxnode(Vector3(w,2.35,.07),Vector3(0,1.175,dep/2),mats.wall_taupe,car)
  for side in [-1,1]:boxnode(Vector3(.07,2.35,dep),Vector3(side*w/2,1.175,0),mats.metal,car)
  boxnode(Vector3(w,.10,dep),Vector3(0,2.35,0),mats.ceiling_panel,car)
  # Fixed cabin jambs keep the door opening as narrow as the actual landing aperture.
  for side in [-1,1]:boxnode(Vector3((w-float(d.door_width))*.5,2.35,.08),Vector3(side*(w+float(d.door_width))*.25,1.175,-dep/2),mats.wall_taupe,car)
  build_shaft(d,tangent,n)
  var gate=CollisionShape3D.new();var gate_shape=BoxShape3D.new();gate_shape.size=Vector3(d.door_width,2.2,.05);gate.shape=gate_shape;gate.position=Vector3(0,1.1,-dep/2+.02);car.add_child(gate)
  var gate_mesh=MeshInstance3D.new();var gate_cube=BoxMesh.new();gate_cube.size=gate_shape.size;gate_cube.material=mats.metal;gate_mesh.mesh=gate_cube;gate_mesh.position=gate.position;car.add_child(gate_mesh)
  var car_panels:Array=[];var car_panel_cols:Array=[]
  for side in [-1,1]:
   var panel=MeshInstance3D.new();var mesh=BoxMesh.new();mesh.size=Vector3(float(d.door_width)*.5-.008,2.2,.06);mesh.material=mats.metal;panel.mesh=mesh;panel.position=Vector3(side*float(d.door_width)*.25,1.1,-dep/2+.02);car.add_child(panel);car_panels.append(panel)
   var col=CollisionShape3D.new();var shape=BoxShape3D.new();shape.size=mesh.size;col.shape=shape;col.position=panel.position;car.add_child(col);car_panel_cols.append(col)
  var leaves:Array=[]
  for stop:Dictionary in d.stops:
   var leaf=StaticBody3D.new();leaf.name="LandingDoor_"+d.id+"_"+stop.label;leaf.position=Vector3(d.door_xz[0],stop.y,d.door_xz[2]);leaf.basis=Basis(tangent,Vector3.UP,n);add_child(leaf)
   var safety=CollisionShape3D.new();var safety_shape=BoxShape3D.new();safety_shape.size=Vector3(d.door_width,2.25,.10);safety.shape=safety_shape;safety.position.y=1.125;leaf.add_child(safety);leaf.set_meta("gate",safety)
   var panels:Array=[]
   for side in [-1,1]:
    var panel=MeshInstance3D.new();var pm=BoxMesh.new();pm.size=Vector3(float(d.door_width)*.5-.008,2.25,.08);pm.material=mats.metal;panel.mesh=pm;panel.position=Vector3(side*float(d.door_width)*.25,1.125,0);leaf.add_child(panel);panels.append(panel)
   leaf.set_meta("panels",panels);var panel_cols:Array=[]
   for panel:MeshInstance3D in panels:
    var col=CollisionShape3D.new();var shape=BoxShape3D.new();shape.size=panel.mesh.size;col.shape=shape;col.position=panel.position;leaf.add_child(col);panel_cols.append(col)
   leaf.set_meta("panel_colliders",panel_cols);leaves.append(leaf)
  records.append({"data":d,"car":car,"doors":leaves,"current":1 if d.stops.size()==5 else 0,"target":1 if d.stops.size()==5 else 0,"state":"open","speed":0.,"timer":0.,"start_y":car.position.y,"arrival_count":0,"gate":gate,"gate_mesh":gate_mesh,"pending_calls":[],"car_panels":car_panels,"car_panel_colliders":car_panel_cols,"reopen_count":0})
 for r:Dictionary in records:update_doors(r)
func build_shaft(d:Dictionary,tangent:Vector3,n:Vector3)->void:
 var body=StaticBody3D.new();body.name="EnclosedShaft_"+str(d.id);body.position=Vector3(d.center[0],0,d.center[2]);body.basis=Basis(tangent,Vector3.UP,n);add_child(body)
 var low:float=d.stops[0].y-.30;var high:float=d.stops[-1].y+2.7;var w:float=d.width+.16;var dep:float=d.depth
 var door_local=body.to_local(Vector3(d.door_xz[0],0,d.door_xz[2]));var front:float=door_local.z;var back:float=dep*.5+.10;var length:float=back-front
 for side in [-1,1]:boxnode(Vector3(.16,high-low,length+.16),Vector3(side*(w*.5+.08),(high+low)*.5,(front+back)*.5),mats.wall_taupe,body)
 boxnode(Vector3(w+.32,high-low,.16),Vector3(0,(high+low)*.5,back+.08),mats.wall_taupe,body)
 var clear:float=d.door_width
 for side in [-1,1]:boxnode(Vector3((w-clear)*.5,high-low,.20),Vector3(side*(w+clear)*.25,(high+low)*.5,front),mats.wall_taupe,body)
 for i in range(d.stops.size()):
  var stop:Dictionary=d.stops[i];var top:float=d.stops[i+1].y if i+1<d.stops.size()else high
  boxnode(Vector3(clear,top-stop.y-2.25,.20),Vector3(0,(top+stop.y+2.25)*.5,front),mats.wall_taupe,body)
  # Threshold covers only the gap between landing and cabin, never the shaft itself.
  var end:float=-dep*.5+.06;var start:float=front-.18
  boxnode(Vector3(clear+.12,.12,max(.08,end-start)),Vector3(0,stop.y-.06,(start+end)*.5),mats.metal,body)
  var marker=Label3D.new();marker.font=font;marker.text="EV  "+str(stop.label);marker.font_size=56;marker.pixel_size=.008;marker.position=Vector3(0,stop.y+2.48,front-.12);marker.rotation.y=PI;marker.scale.x=-1.0;marker.no_depth_test=false;body.add_child(marker)
func update_doors(r:Dictionary)->void:
 var opened:bool=r.state=="open"
 var car_amount:float=1.0 if opened else clamp(float(r.timer)/.6,0.,1.)if r.state=="closing"else clamp(1.-float(r.timer)/.6,0.,1.)if r.state=="opening"else 0.0
 r.gate.set_deferred("disabled",r.state in["open","opening","closing"]);r.gate_mesh.visible=false
 for j in range(2):
  r.car_panels[j].position.x=(-1 if j==0 else 1)*float(r.data.door_width)*(.25+.52*car_amount);r.car_panel_colliders[j].position=r.car_panels[j].position
 for i in range(r.doors.size()):
  var leaf:StaticBody3D=r.doors[i];var amount:float=0.0
  if i==int(r.current):
   if r.state=="open":amount=1.0
   elif r.state=="closing":amount=clamp(float(r.timer)/.6,0.,1.)
   elif r.state=="opening":amount=clamp(1.-float(r.timer)/.6,0.,1.)
  var gate:CollisionShape3D=leaf.get_meta("gate");gate.set_deferred("disabled",i==int(r.current)and r.state in["open","opening","closing"])
  var panels:Array=leaf.get_meta("panels")
  for j in range(2):
   panels[j].position.x=(-1 if j==0 else 1)*float(r.data.door_width)*(.25+.52*amount)
   leaf.get_meta("panel_colliders")[j].position=panels[j].position
func is_inside(index:int)->bool:
 var r:Dictionary=records[index];var lp:Vector3=r.car.to_local(player.position)
 return abs(lp.x)<float(r.data.width)*.5-.12 and abs(lp.z)<float(r.data.depth)*.5-.12 and abs(lp.y)<.35
func landing_stop(index:int)->int:
 var d:Dictionary=records[index].data
 for i in range(d.stops.size()):
  if abs(player.position.y-float(d.stops[i].y))<.6:return i
 return -1
func threshold_blocked(r:Dictionary)->bool:
 var dp=Vector3(r.data.door_xz[0],r.car.position.y,r.data.door_xz[2]);var relative=player.position-dp;var n=Vector3(r.data.inside[0],0,r.data.inside[1]);var u=Vector3(-n.z,0,n.x)
 return abs(relative.y)<1.9 and abs(relative.dot(n))<.44 and abs(relative.dot(u))<float(r.data.door_width)*.5+.30
func call_to(index:int,stop:int)->bool:
 var r:Dictionary=records[index]
 if stop<0:return false
 if r.state=="open":return request(index,stop)
 if not r.pending_calls.has(stop)and int(r.target)!=stop:r.pending_calls.append(stop)
 return true
func request(index:int,stop:int)->bool:
 var r:Dictionary=records[index]
 if r.state!="open" or stop<0 or stop>=r.data.stops.size():return false
 if stop==int(r.current):return true
 # Doorway sensor: do not close through a capsule straddling the threshold.
 var at=player.position;var dp=Vector3(r.data.door_xz[0],r.car.position.y,r.data.door_xz[2])
 if threshold_blocked(r):return false
 r.target=stop;r.state="closing";r.timer=.6;r.speed=0.;r.start_y=r.car.position.y;update_doors(r);return true
func _physics_process(dt:float)->void:
 for r:Dictionary in records:
  if r.state=="open" and not r.pending_calls.is_empty():
   var index=records.find(r)
   if not is_inside(index)and request(index,int(r.pending_calls[0])):r.pending_calls.pop_front()
  if r.state=="closing":
   if threshold_blocked(r):r.state="opening";r.timer=.6-float(r.timer);r.target=r.current;r.reopen_count+=1
   else:r.timer-=dt
   update_doors(r)
   if r.timer<=0 and r.state=="closing":r.state="moving";update_doors(r)
  elif r.state=="moving":
   var goal:float=r.data.stops[int(r.target)].y;var delta=goal-r.car.position.y;var a:float=r.data.acceleration
   var desired=min(float(r.data.speed),sqrt(2*a*abs(delta)))
   r.speed=move_toward(float(r.speed),desired,a*dt)
   var dy=sign(delta)*min(abs(delta),float(r.speed)*dt)
   # Continuous swept carrier update; no floor-to-floor position assignment. Player moves through physics too.
   var lp:Vector3=r.car.to_local(player.position)
   var carried:bool=abs(lp.x)<float(r.data.width)/2-.1 and abs(lp.z)<float(r.data.depth)/2-.1 and lp.y>-.12 and lp.y<.35
   r.car.position.y+=dy
   if carried:
    player.velocity.y=0.;player.move_and_collide(Vector3(0,dy,0),false,.001)
   if abs(goal-r.car.position.y)<.0001:
    r.current=r.target;r.state="opening";r.timer=.6;r.speed=0.
  elif r.state=="opening":
   r.timer-=dt
   update_doors(r)
   if r.timer<=0:r.state="open";r.arrival_count+=1;update_doors(r)
func nearest()->int:
 var best:int=-1;var dist:float=3.5
 for i in range(records.size()):
  var r:Dictionary=records[i];var door=Vector3(r.data.door_xz[0],player.position.y,r.data.door_xz[2]);var dd=Vector2(player.position.x-door.x,player.position.z-door.z).length()
  var lp:Vector3=r.car.to_local(player.position)
  if abs(lp.x)<float(r.data.width)/2 and abs(lp.z)<float(r.data.depth)/2 and abs(lp.y)<.5:return i
  if landing_stop(i)>=0 and dd<dist:
   var toward=door-player.position;toward.y=0;var view=-player.camera.global_basis.z;view.y=0
   if toward.length()<.1 or toward.normalized().dot(view.normalized())>.35:dist=dd;best=i
 return best
