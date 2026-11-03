extends Node3D
## Visible mechanical assembly. Continuous collision ramp remains the v1 movement support.
var banks:Array=[]
var clock:float=0.0
var paused:bool=false
var speed:float=.50
var material_set:Dictionary
var samples:Array=[]
var culled_updates:int=0
var visible_updates:int=0
var next_far_update:float=0.0
func v3(a:Array)->Vector3:return Vector3(a[0],a[1],a[2])
func setup(manifest:Dictionary,mats:Dictionary)->void:
 material_set=mats
 for data:Dictionary in manifest.escalators:
  var rise=float(data.rise_m);var run=float(data.run_m);var lo=float(data.low_y) if data.has("low_y") else float(manifest.floors[int(data.levels[0])].height)
  var c=v3(data.c);c.y=lo;var u=Vector3(data.u[0],0,data.u[1]);var lateral=Vector3(u.z,0,-u.x)
  var bank:Dictionary={"id":data.id,"direction":1.0 if data.direction=="UP" else -1.0,"c":c,"u":u,"x":lateral,"rise":rise,"run":run,"path":[]}
  var points:PackedVector3Array=[]
  # Top centers, arc returns and underside. Turnaround stays within original 14.8m shaft.
  var end:float=run*.5+1.10;var radius:float=.30
  for i in range(141):
   var s=lerp(-end,end,i/140.0);points.append(Vector3(0,height(s,bank),s))
  for i in range(1,21):
   var a=PI/2-i*PI/20;points.append(Vector3(0,rise-radius+sin(a)*radius,end+cos(a)*radius))
  for i in range(1,141):
   var s=lerp(end,-end,i/140.0);points.append(Vector3(0,height(s,bank)-2*radius,s))
  for i in range(1,21):
   var a=-PI/2-i*PI/20;points.append(Vector3(0,-radius+sin(a)*radius,-end+cos(a)*radius))
  var distance:float=0.0;var previous=points[0];var distance_table:Array=[0.0]
  for i in range(1,points.size()):distance+=points[i].distance_to(previous);distance_table.append(distance);previous=points[i]
  var rubber=ShaderMaterial.new();rubber.shader=load("res://rubber.gdshader");bank.rubber=rubber
  bank.points=points;bank.distances=distance_table;bank.length=distance;bank.top_length=float(distance_table[140]);bank.top_end=140
  var count=int(ceil(distance/.4));bank.count=count;bank.pitch=distance/count
  var instance=MultiMeshInstance3D.new();instance.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF;var mm=MultiMesh.new();mm.transform_format=MultiMesh.TRANSFORM_3D;mm.mesh=step_mesh(mats);mm.instance_count=count;instance.multimesh=mm;instance.name=data.id+"_moving_treads";add_child(instance);bank.multimesh=mm
  # Rubber loop is a smooth elliptic profile, not a flat diagonal strip.
  for side in[-1,1]:
   var rail=MeshInstance3D.new();rail.name=data.id+"_continuous_handrail";rail.mesh=rail_mesh(bank,.94*side,rubber);add_child(rail)
  var comb=MultiMeshInstance3D.new();comb.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF;var comb_mesh=BoxMesh.new();comb_mesh.size=Vector3(.017,.016,.15);comb_mesh.material=mats.yellow
  var comb_mm=MultiMesh.new();comb_mm.transform_format=MultiMesh.TRANSFORM_3D;comb_mm.mesh=comb_mesh;comb_mm.instance_count=64
  for side_index in range(2):
   var side=-1.0 if side_index==0 else 1.0
   for tooth in range(32):
    var x=-.615+(tooth+.5)*.0395;var s=side*6.89;var yy=.010+(rise if side>0 else 0.0)
    var origin=c+lateral*x+u*s+Vector3.UP*yy;comb_mm.set_instance_transform(side_index*32+tooth,Transform3D(Basis(lateral,Vector3.UP,u),origin))
  comb.multimesh=comb_mm;comb.name=data.id+"_interleaved_comb_teeth";add_child(comb)
  for side in[-1,1]:
   var plate=MeshInstance3D.new();plate.name=data.id+"_comb_backing_plate";var plate_mesh=BoxMesh.new();plate_mesh.size=Vector3(1.40,.035,.24);plate_mesh.material=mats.metal;plate.mesh=plate_mesh;plate.transform=Transform3D(Basis(lateral,Vector3.UP,u),c+u*(side*6.89)+Vector3.UP*(-.010+(rise if side>0 else 0.0)));add_child(plate)
  add_truss_housing(bank,mats)
  banks.append(bank)
 set_time(0.0)
func add_truss_housing(bank:Dictionary,mats:Dictionary)->void:
 # Return treads and landing pits belong inside a real closed machinery casing.
 # Their 0.60m return loop used to protrude through the next floor's underside.
 var st=SurfaceTool.new();st.begin(Mesh.PRIMITIVE_TRIANGLES)
 var half:float=bank.run*.5;var end:float=half+1.45;var ss:Array=[-end,-half,half,end];var width:float=.77
 for i in range(ss.size()-1):
  var a:float=ss[i];var b:float=ss[i+1];var ya:float=height(a,bank);var yb:float=height(b,bank)
  for side in[-1,1]:housing_quad(st,[Vector3(side*width,ya-.84,a),Vector3(side*width,yb-.84,b),Vector3(side*width,yb-.025,b),Vector3(side*width,ya-.025,a)],bank)
  housing_quad(st,[Vector3(-width,ya-.84,a),Vector3(width,ya-.84,a),Vector3(width,yb-.84,b),Vector3(-width,yb-.84,b)],bank)
 for z in[-end,end]:
  var yy:float=height(z,bank);housing_quad(st,[Vector3(-width,yy-.84,z),Vector3(width,yy-.84,z),Vector3(width,yy-.025,z),Vector3(-width,yy-.025,z)],bank)
 st.generate_normals();var material=StandardMaterial3D.new();material.resource_name="V11_enclosed_escalator_truss";material.albedo_color=Color(.43,.45,.47);material.metallic=.72;material.roughness=.33;material.cull_mode=BaseMaterial3D.CULL_DISABLED;st.set_material(material);var mesh:Mesh=st.commit();var body=StaticBody3D.new();body.name=bank.id+"_enclosed_truss_and_landing_pit";add_child(body)
 var visible=MeshInstance3D.new();visible.mesh=mesh;visible.gi_mode=GeometryInstance3D.GI_MODE_STATIC;body.add_child(visible)
 var collision=CollisionShape3D.new();collision.shape=mesh.create_trimesh_shape();collision.shape.backface_collision=true;body.add_child(collision)
func housing_quad(st:SurfaceTool,points:Array,bank:Dictionary)->void:
 for i in[0,1,2,0,2,3]:
  var p:Vector3=points[i];st.set_uv(Vector2(p.z,p.y));st.add_vertex(bank.c+bank.x*p.x+Vector3.UP*p.y+bank.u*p.z)
func height(s:float,b:Dictionary)->float:
 var half:float=b.run*.5
 return float(b.rise)*clamp((s+half)/float(b.run),0.0,1.0)
func at_distance(bank:Dictionary,distance:float)->Dictionary:
 var distances:Array=bank.distances;var points:PackedVector3Array=bank.points
 var d=fposmod(distance,float(bank.length));var low:int=0;var high:int=distances.size()-1
 while low+1<high:
  var m=(low+high)/2
  if distances[m]<=d:low=m
  else:high=m
 var f=(d-float(distances[low]))/max(.00001,float(distances[high])-float(distances[low]));var local=points[low].lerp(points[high],f)
 var angle:float=0.0
 if low>140 and low<=160:angle=-(low-140)*PI/20
 elif low>160 and low<=300:angle=-PI
 elif low>300:angle=-PI-(low-300)*PI/20
 return {"local":local,"angle":angle,"index":low}
func set_time(t:float)->void:
 clock=t
 for b:Dictionary in banks:
  var camera=get_viewport().get_camera_3d()
  if t>0 and camera!=null and camera.global_position.distance_to(b.c)>65 and int(clock*4)==int((clock-get_process_delta_time())*4):
   culled_updates+=1;continue
  visible_updates+=1
  var mm:MultiMesh=b.multimesh
  b.rubber.set_shader_parameter("belt_offset",clock*speed*float(b.direction))
  for i in range(b.count):
   var d=float(i)*float(b.pitch)+clock*speed*float(b.direction);var point:Dictionary=at_distance(b,d);var local:Vector3=point.local
   var position:Vector3=b.c+b.x*local.x+Vector3.UP*local.y+b.u*local.z
   # Yaw aligns bank to shaft. Top treads remain horizontal; return rotates under enclosed truss.
   var yaw=Basis(b.x,Vector3.UP,b.u)
   mm.set_instance_transform(i,Transform3D(yaw*Basis(Vector3.RIGHT,float(point.angle)),position))
func _process(dt:float)->void:
 if not paused:set_time(clock+dt)
func add_box(st:SurfaceTool,c:Vector3,size:Vector3)->void:
 var mesh=BoxMesh.new();mesh.size=size
 st.append_from(mesh,0,Transform3D(Basis.IDENTITY,c))
func step_mesh(mats:Dictionary)->ArrayMesh:
 var output=ArrayMesh.new()
 var st=SurfaceTool.new();st.begin(Mesh.PRIMITIVE_TRIANGLES)
 # Horizontal ribbed tread with a genuine vertical riser, inner flanges and a lower curved lip.
 add_box(st,Vector3(0,-.022,0),Vector3(1.30,.044,.37))
 add_box(st,Vector3(0,-.105,-.183),Vector3(1.30,.19,.014))
 for x in[-.62,.62]:add_box(st,Vector3(x,-.11,0),Vector3(.022,.17,.35))
 st.set_material(mats.step);st.generate_normals();st.commit(output)
 st=SurfaceTool.new();st.begin(Mesh.PRIMITIVE_TRIANGLES)
 for i in range(32):
  var x=-.615+i*.0395;add_box(st,Vector3(x,.003,0),Vector3(.010,.006,.355))
 st.set_material(mats.metal);st.generate_normals();st.commit(output)
 st=SurfaceTool.new();st.begin(Mesh.PRIMITIVE_TRIANGLES)
 add_box(st,Vector3(0,.007,-.176),Vector3(1.30,.008,.013))
 for x in[-.64,.64]:add_box(st,Vector3(x,.007,0),Vector3(.013,.008,.35))
 st.set_material(mats.yellow);st.generate_normals();st.commit(output);return output
func rail_mesh(b:Dictionary,offset:float,mat:Material)->ArrayMesh:
 var st=SurfaceTool.new();st.begin(Mesh.PRIMITIVE_TRIANGLES)
 var points:PackedVector3Array=b.points;var sides:int=10
 for i in range(points.size()-1):
  var a=points[i]+Vector3(offset,1.02,0);var bb=points[i+1]+Vector3(offset,1.02,0)
  var dir=(bb-a).normalized();var cross=Vector3(0,dir.z,-dir.y).normalized()
  for j in range(sides):
   var a0=j*TAU/sides;var a1=(j+1)*TAU/sides
   var q0=Vector3.RIGHT*cos(a0)*.053+cross*sin(a0)*.037;var q1=Vector3.RIGHT*cos(a1)*.053+cross*sin(a1)*.037
   var coords:Array=[a+q0,bb+q0,bb+q1,a+q1]
   for k in[0,2,1,0,3,2]:
    var local:Vector3=coords[k];var world:Vector3=b.c+b.x*local.x+Vector3.UP*local.y+b.u*local.z
    st.set_uv(Vector2(float(j)/sides,float(b.distances[i])));st.add_vertex(world)
 st.set_material(mat);st.generate_normals();st.generate_tangents();return st.commit()
func audit()->Dictionary:
 var checks:Array=[]
 for b:Dictionary in banks:
  var upper:Dictionary=at_distance(b,float(b.top_length)*.3);var later:Dictionary=at_distance(b,float(b.top_length)*.3+.5*float(b.direction))
  checks.append({"id":b.id+"-direction","pass":(later.local.z-upper.local.z)*float(b.direction)>0,"surface_speed_m_s":speed})
  var closing0:Dictionary=at_distance(b,0);var closing1:Dictionary=at_distance(b,float(b.length)-.001)
  checks.append({"id":b.id+"-closed-return","pass":closing0.local.distance_to(closing1.local)<.003,"closure_m":closing0.local.distance_to(closing1.local)})
  var flat0:Dictionary=at_distance(b,.25);checks.append({"id":b.id+"-flat-entry","pass":abs(flat0.local.y)<.001,"entry_y":flat0.local.y})
  checks.append({"id":b.id+"-pitch","pass":abs(float(b.pitch)-.4)<.015,"pitch_m":b.pitch,"instances":b.count})
  checks.append({"id":b.id+"-rendered-instances","pass":b.multimesh.instance_count==b.count})
 return {"checks":checks,"total":checks.size(),"failed":checks.filter(func(c):return not c["pass"]).size(),"method":"actual instanced mesh transform and sampled closed mechanical return path; not a texture scroll"}
