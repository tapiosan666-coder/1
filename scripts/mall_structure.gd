class_name MallStructure
extends RefCounted
## Compiled authored polygons drive the same floor mesh, floor queries and map.
static var packets:Dictionary={}
static func floor_packets(building:String,level:int)->Array:
 if level<0 or not MallStructureData.DATA.has(building) or level>=MallStructureData.DATA[building].floors.size():return []
 var key:=building+str(level)
 if packets.has(key):return packets[key]
 var result:Array=[]
 for source in MallStructureData.DATA[building].floors[level].polygons:
  var p:={"outer":poly(source.outer),"holes":[],"bounds":Rect2()}
  p.bounds=Rect2(p.outer[0],Vector2.ZERO)
  for point:Vector2 in p.outer:p.bounds=p.bounds.expand(point)
  for hole:Array in source.holes:p.holes.append(poly(hole))
  result.append(p)
 packets[key]=result;return result
static func poly(points:Array)->PackedVector2Array:
 var result:=PackedVector2Array()
 for p:Array in points:result.append(Vector2(p[0],p[1]))
 return result
static func contains(building:String,level:int,at:Vector2)->bool:
 for p:Dictionary in floor_packets(building,level):
  if not p.bounds.grow(.001).has_point(at) or not Geometry2D.is_point_in_polygon(at,p.outer):continue
  var hole:=false
  for ring:PackedVector2Array in p.holes:
   if Geometry2D.is_point_in_polygon(at,ring):hole=true;break
  if not hole:return true
 return false
static func bounds(building:String,level:int)->Rect2:
 if floor_packets(building,level).is_empty():return Rect2()
 var a:Array=MallStructureData.DATA[building].floors[level].bounds
 return Rect2(a[0],a[1],a[2]-a[0],a[3]-a[1])
static func surface(root:Node3D,triangles:Array,y:float,mat:Material,solid:bool)->MeshInstance3D:
 var st:=SurfaceTool.new();st.begin(Mesh.PRIMITIVE_TRIANGLES)
 for triangle:Array in triangles:
  for p:Array in triangle:
   st.set_normal(Vector3.UP);st.set_uv(Vector2(p[0],p[1]));st.add_vertex(Vector3(p[0],y,p[1]))
 if solid:
  for triangle:Array in triangles:
   for i in [2,1,0]:
    var p:Array=triangle[i];st.set_normal(Vector3.DOWN);st.set_uv(Vector2(p[0],p[1]));st.add_vertex(Vector3(p[0],y-.35,p[1]))
 st.index()
 var node:=MeshInstance3D.new();node.mesh=st.commit();node.material_override=mat;root.add_child(node)
 if solid:
  var body:=StaticBody3D.new();var shape:=CollisionShape3D.new();shape.shape=node.mesh.create_trimesh_shape();node.add_child(body);body.add_child(shape)
 return node
static func segment(root:Node3D,a:Vector2,b:Vector2,y:float,height:float,depth:float,mat:Material,solid:bool=false)->MeshInstance3D:
 var d:=b-a
 var node:=Shapes.box(root,Vector3((a.x+b.x)*.5,y,(a.y+b.y)*.5),Vector3(d.length(),height,depth),mat,solid)
 node.rotation.y=-atan2(d.y,d.x);return node
static func build(building:String,root:Node3D)->void:
 var data:Dictionary=MallStructureData.DATA[building]
 var plaster:=MallFinishes.plaster(Color("d9d6cd"));var stone:=MallFinishes.stone();var metal:=Shapes.material(Color("637579"));var glass:StandardMaterial3D=root._glass()
 for level in data.floors.size():
  var y:=Mall.floor_height(level)
  if building!="A" or level>0:surface(root,data.floors[level].triangles,y,stone,true)
  for p:Dictionary in floor_packets(building,level):
   var rings:Array=[p.outer];rings.append_array(p.holes)
   for ring:PackedVector2Array in rings:
    for i in ring.size():segment(root,ring[i],ring[(i+1)%ring.size()],y-.175,.35,.06,plaster)
  for line:Array in data.walls[level]:
   for i in line.size()-1:
    var a:=Vector2(line[i][0],line[i][1]);var b:=Vector2(line[i+1][0],line[i+1][1])
    if a.distance_to(b)<.01:continue
    segment(root,a,b,y+2.65,5.3,.25,plaster,true)
    segment(root,a,b,y+.09,.18,.29,metal)
  if level==0:continue
  for line:Array in data.rails[level]:
   for i in line.size()-1:
    var a:=Vector2(line[i][0],line[i][1]);var b:=Vector2(line[i+1][0],line[i+1][1])
    if a.distance_to(b)<.01 or (building=="B" and minf(a.x,b.x)>-190):continue
    segment(root,a,b,y+.65,1.12,.08,glass,true)
    segment(root,a,b,y+1.24,.055,.12,metal)
    if building=="B":
     segment(root,a,b,y-.16,.32,.32,plaster)
     segment(root,a,b,y-.34,.045,.38,metal)
 var roof:=Shapes.material(Color("cbdcde"));roof.roughness=.34;roof.cull_mode=BaseMaterial3D.CULL_DISABLED
 surface(root,data.roof.triangles,16.4,roof,false)
 if building=="B":
  # Real roof apertures over the three courts: glazing and ribs, no opaque lid
  # over an otherwise correctly opened 2F/3F atrium.
  var skylight:=Shapes.material(Color("b7d4df"));skylight.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
  skylight.albedo_color.a=.28;skylight.roughness=.22;skylight.cull_mode=BaseMaterial3D.CULL_DISABLED
  surface(root,data.skylights.triangles,17.2,skylight,false)
  for packet:Dictionary in data.skylights.polygons:
   var ring:=poly(packet.outer)
   for i in ring.size():
    segment(root,ring[i],ring[(i+1)%ring.size()],16.7,.8,.22,plaster)
    segment(root,ring[i],ring[(i+1)%ring.size()],17.17,.10,.30,metal)
  for plaza:Dictionary in data.plazas:
   var cx:float=plaza.at[0];var cz:float=plaza.at[1];var radius:Array=plaza.void_radius
   for offset in [-.6,-.3,0.0,.3,.6]:
    var span:float=radius[0]*sqrt(1-offset*offset)
    segment(root,Vector2(cx-span,cz+offset*radius[1]),Vector2(cx+span,cz+offset*radius[1]),17.10,.18,.09,metal)
  surface(root,data.ground_roof.triangles,5.3,glass,false)
  var path:Array=MallStructureData.DATA.B.c_access
  for i in path.size()-1:
   var a:=Vector3(path[i][0],0,path[i][1]);var b:=Vector3(path[i+1][0],0,path[i+1][1]);var count:=maxi(1,ceili(a.distance_to(b)/12))
   for index in count:
    var at:=a.lerp(b,(index+.5)/count)+Vector3.UP*4.7
    Shapes.box(root,at,Vector3(1.4,.05,.35),Shapes.material(Color("fff0d7"),.7))
    var light:=OmniLight3D.new();root.add_child(light);light.position=at-Vector3.UP*.3;light.omni_range=10;light.light_energy=.5;light.distance_fade_enabled=true;light.distance_fade_begin=16;light.distance_fade_length=6
 # Court centres share the same layout data used for floor openings and labels.
 for p:Dictionary in data.plazas:
  var at:=Vector3(p.at[0],0,p.at[1])
  for side in [-1,1]:
   Shapes.box(root,at+Vector3(side*(p.radius[0]-3),8,0),Vector3(.5,16,.5),plaster,true)
  for level in [0,1,2]:
   var light:=OmniLight3D.new();root.add_child(light);light.position=at+Vector3(0,Mall.floor_height(level)+4,0)
   light.light_color=Color("f2ebdb");light.light_energy=.95;light.omni_range=30
   light.distance_fade_enabled=true;light.distance_fade_begin=35;light.distance_fade_length=10
   var sign:=Shapes.sign_text(root,at+Vector3(0,Mall.floor_height(level)+3.5,-p.radius[1]+1),p.name,40);sign.pixel_size=.007
