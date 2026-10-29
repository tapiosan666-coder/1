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
  var gate=CollisionShape3D.new();var gate_shape=BoxShape3D.new();gate_shape.size=Vector3(w,2.2,.05);gate.shape=gate_shape;gate.position=Vector3(0,1.1,-dep/2+.02);car.add_child(gate)
  var gate_mesh=MeshInstance3D.new();var gate_cube=BoxMesh.new();gate_cube.size=gate_shape.size;gate_cube.material=mats.metal;gate_mesh.mesh=gate_cube;gate_mesh.position=gate.position;car.add_child(gate_mesh)
  var leaves:Array=[]
  for stop:Dictionary in d.stops:
   var leaf=StaticBody3D.new();leaf.name="LandingDoor_"+d.id+"_"+stop.label;leaf.position=Vector3(d.door_xz[0],stop.y,d.door_xz[2]);leaf.basis=Basis(tangent,Vector3.UP,n);add_child(leaf)
   boxnode(Vector3(d.door_width,2.2,.055),Vector3(0,1.1,0),mats.metal,leaf);leaves.append(leaf)
  records.append({"data":d,"car":car,"doors":leaves,"current":1 if d.stops.size()==5 else 0,"target":1 if d.stops.size()==5 else 0,"state":"open","speed":0.,"timer":0.,"start_y":car.position.y,"arrival_count":0,"gate":gate,"gate_mesh":gate_mesh})
 for r:Dictionary in records:update_doors(r)
func update_doors(r:Dictionary)->void:
 r.gate.disabled=r.state=="open";r.gate_mesh.visible=r.state!="open"
 for i in range(r.doors.size()):
  var leaf:StaticBody3D=r.doors[i];var opened:bool=r.state=="open" and i==int(r.current)
  # A real sliding panel parks beside the opening. Its collider remains enabled.
  leaf.position.x=float(r.data.door_xz[0])+(float(r.data.u[0])*float(r.data.door_width)*1.05 if opened else 0.)
  leaf.position.z=float(r.data.door_xz[2])+(float(r.data.u[1])*float(r.data.door_width)*1.05 if opened else 0.)
func request(index:int,stop:int)->bool:
 var r:Dictionary=records[index]
 if r.state!="open" or stop<0 or stop>=r.data.stops.size():return false
 if stop==int(r.current):return true
 # Doorway sensor: do not close through a capsule straddling the threshold.
 var at=player.position;var dp=Vector3(r.data.door_xz[0],r.car.position.y,r.data.door_xz[2])
 if abs(at.y-dp.y)<1.9 and Vector2(at.x-dp.x,at.z-dp.z).length()<.42:return false
 r.target=stop;r.state="closing";r.timer=.6;r.speed=0.;r.start_y=r.car.position.y;update_doors(r);return true
func _physics_process(dt:float)->void:
 for r:Dictionary in records:
  if r.state=="closing":
   r.timer-=dt
   if r.timer<=0:r.state="moving"
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
   if r.timer<=0:r.state="open";r.arrival_count+=1;update_doors(r)
func nearest()->int:
 var best:int=-1;var dist:float=3.5
 for i in range(records.size()):
  var r:Dictionary=records[i];var door=Vector3(r.data.door_xz[0],player.position.y,r.data.door_xz[2]);var dd=Vector2(player.position.x-door.x,player.position.z-door.z).length()
  var lp:Vector3=r.car.to_local(player.position)
  if abs(lp.x)<float(r.data.width)/2 and abs(lp.z)<float(r.data.depth)/2 and abs(lp.y)<.5:return i
  if dd<dist:dist=dd;best=i
 return best
