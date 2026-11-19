extends MeshInstance3D
## The narrow lawn strip between the north court paving and the shop arcade.
## Local Z=6.45 is on the arcade wearing surface, Z=7.58 is the seat terrace.
const START_Z:=6.45
const END_Z:=7.58
const CENTER_X:=1.95

func surface_z(z:float)->float:
 return lerpf(.004,.0305,(z-START_Z)/(END_Z-START_Z))

func point(x:float,z:float,offset:float=0.)->Vector3:
 return Vector3(x,surface_z(z)+offset,z)

func width(z:float)->float:
 return lerpf(1.25,1.62,(z-START_Z)/(END_Z-START_Z))

func patch(st:SurfaceTool,x0:float,x1:float,z0:float,z1:float,c:Color,raised:float)->void:
 var p00:=point(clampf(x0,CENTER_X-width(z0),CENTER_X+width(z0)),z0,raised)
 var p10:=point(clampf(x1,CENTER_X-width(z0),CENTER_X+width(z0)),z0,raised)
 var p01:=point(clampf(x0,CENTER_X-width(z1),CENTER_X+width(z1)),z1,raised)
 var p11:=point(clampf(x1,CENTER_X-width(z1),CENTER_X+width(z1)),z1,raised)
 var n:=(p01-p00).cross(p10-p00).normalized()
 if n.y<.96:n=Vector3.UP
 for v:Vector3 in [p00,p10,p11,p00,p11,p01]:
  st.set_normal(n)
  st.set_color(c)
  st.add_vertex(v)

func _ready()->void:
 name="North_Garden_Access_Paving"
 var mat:=StandardMaterial3D.new()
 mat.vertex_color_use_as_albedo=true
 mat.vertex_color_is_srgb=true
 mat.roughness=.79
 var st:=SurfaceTool.new()
 st.begin(Mesh.PRIMITIVE_TRIANGLES)
 st.set_material(mat)
 patch(st,-3.,7.,START_Z,END_Z,Color("#827f73"),-.002)
 var shades:=["#b9b4a6","#b6b3a6","#acab9f","#c0bbad","#b3b0a2"]
 for row:int in 3:
  var z0:=START_Z+(END_Z-START_Z)*row/3.
  var z1:=START_Z+(END_Z-START_Z)*(row+1)/3.
  for column:int in range(-4,5):
   var x:=CENTER_X+column*.74+(row%2)*.37
   if x+.735<CENTER_X-width(z1) or x>CENTER_X+width(z1):continue
   patch(st,x+.004,x+.735,z0+.004,z1-.004,Color(shades[posmod(column+row,shades.size())]),0.)
 st.index()
 mesh=st.commit()
 cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 var body:=StaticBody3D.new()
 var collider:=CollisionShape3D.new()
 var surface:=ConcavePolygonShape3D.new()
 var a:=point(CENTER_X-width(START_Z),START_Z)
 var b:=point(CENTER_X+width(START_Z),START_Z)
 var c:=point(CENTER_X+width(END_Z),END_Z)
 var d:=point(CENTER_X-width(END_Z),END_Z)
 surface.set_faces(PackedVector3Array([a,b,c,a,c,d]))
 surface.backface_collision=true
 collider.shape=surface
 body.add_child(collider)
 add_child(body)
