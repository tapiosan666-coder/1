extends Node3D
var doors:Array=[]
var mat:Material
func setup(definitions:Array,materials:Dictionary)->void:
 mat=materials.wall_taupe
 for d:Dictionary in definitions:
  var original_axis=Vector3(d.u[0],0,d.u[1]);var side:float=float(d.get("hinge_side",-1));var axis=original_axis*(-side);var z=Vector3(-axis.z,0,axis.x);var center=Vector3(d.p[0],d.p[1],d.p[2])
  var pivot=AnimatableBody3D.new();pivot.sync_to_physics=false;pivot.name=d.id;pivot.position=center+original_axis*side*float(d.leaf_width_m)*.5;pivot.basis=Basis(axis,Vector3.UP,z)
  var col=CollisionShape3D.new();var shape=BoxShape3D.new();shape.size=Vector3(d.leaf_width_m,d.height_m,.042);col.shape=shape;col.position=Vector3(float(d.leaf_width_m)*.5,float(d.height_m)*.5+.015,0);pivot.add_child(col)
  var mesh=MeshInstance3D.new();var box=BoxMesh.new();box.size=shape.size;box.material=mat
  if d.get("amenity_v13",false):
   var finish=StandardMaterial3D.new();finish.albedo_color=Color(.30,.34,.30);finish.roughness=.53;box.material=finish
  mesh.mesh=box;mesh.position=col.position;pivot.add_child(mesh)
  var strip=MeshInstance3D.new();var bm=BoxMesh.new();bm.size=Vector3(.055,.25,.018);bm.material=materials.metal;strip.mesh=bm;strip.position=Vector3(float(d.leaf_width_m)-.10,1.03,-.035);pivot.add_child(strip)
  var text=Label3D.new();text.font=load("res://assets/NotoSansCJKjp-Regular.otf");text.text=(d.get("role_label","階段 / 公共設備") if d.get("role","staff")=="public" else "STAFF ONLY\n関係者以外立入禁止")+("\n"+str(d.room_label) if d.has("room_label") else "");text.font_size=38;text.pixel_size=.0018;text.modulate=Color(.16,.20,.19);text.outline_size=0;text.no_depth_test=false
  var normal_sign=-sign(Vector3(d.n[0],0,d.n[1]).dot(z));text.position=Vector3(float(d.leaf_width_m)*.5,1.55,.027*normal_sign)
  if normal_sign<0:text.rotation.y=PI
  pivot.add_child(text)
  add_child(pivot)
  var normal=Vector3(d.n[0],0,d.n[1]);var angle=-PI*.5 if normal.dot(z)>0 else PI*.5
  doors.append({"data":d,"pivot":pivot,"closed":pivot.transform,"angle":angle,"open":false,"center":center})
func set_open(index:int,value:bool)->void:
 var d:Dictionary=doors[index];var tr:Transform3D=d.closed
 if value:
  if d.data.get("mechanism","hinged")=="sliding":
   var public_pocket:bool=d.data.get("role","staff")=="public"
   var travel:float=float(d.data.clear_width_m)+.06 if public_pocket else float(d.data.leaf_width_m)
   tr.origin+=Vector3(d.data.u[0],0,d.data.u[1])*float(d.data.slide_side)*travel+Vector3(d.data.n[0],0,d.data.n[1])*(0.0 if public_pocket else .08)
  else:tr.basis=tr.basis*Basis(Vector3.UP,float(d.angle))
 d.pivot.transform=tr;d.open=value
func set_all_open(value:bool)->void:
 for i in range(doors.size()):set_open(i,value)
func interact(position:Vector3,exclude:RID=RID())->bool:
 var best:int=-1;var distance:float=2.5
 for i in range(doors.size()):
  var d:Dictionary=doors[i];var point:Vector3=d.pivot.to_global(Vector3(float(d.data.leaf_width_m)*.5,1.1,0))
  var dd=position.distance_to(point)
  if dd>=distance:continue
  var query=PhysicsRayQueryParameters3D.create(position+Vector3.UP*1.65,point)
  if exclude.is_valid():query.exclude=[exclude]
  var hit=get_world_3d().direct_space_state.intersect_ray(query)
  if hit.is_empty()or hit.collider!=d.pivot:continue
  distance=dd;best=i
 if best<0:return false
 set_open(best,not doors[best].open);return true
