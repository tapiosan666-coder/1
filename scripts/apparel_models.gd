class_name ApparelModels
extends RefCounted
## Original, volumetric display clothing. Metres; no NPC identity or animation.
static var cache:Dictionary={}
static var shared:Array[Material]=[]
var surfaces:Dictionary={}

static func outline(points:Array,depth:float)->ArrayMesh:
 var area:=0.0
 for i in points.size():area+=points[i].cross(points[(i+1)%points.size()])
 var vertices:=points.duplicate()
 if area<0:vertices.reverse()
 return TenantProducts.extrude(vertices,depth)
static func materials()->Array[Material]:
 if not shared.is_empty():return shared
 var cloth:=ShaderMaterial.new();cloth.shader=preload("res://assets/retail_cloth.gdshader")
 cloth.set_shader_parameter("weave",preload("res://assets/retail/cloth_weave.png"))
 cloth.set_shader_parameter("weave_normal",preload("res://assets/retail/cloth_normal.png"))
 cloth.set_meta("retail_channel",0);shared.append(cloth)
 for i in [1,2]:
  var m:=StandardMaterial3D.new();m.vertex_color_use_as_albedo=true;m.vertex_color_is_srgb=false
  m.roughness=.32 if i==1 else .48;m.metallic=.75 if i==1 else 0.0
  m.set_meta("retail_channel",i);shared.append(m)
 return shared
func surface(channel:int)->SurfaceTool:
 if not surfaces.has(channel):
  var b:=SurfaceTool.new();b.begin(Mesh.PRIMITIVE_TRIANGLES);b.set_material(materials()[channel]);surfaces[channel]=b
 return surfaces[channel]
func part(mesh:Mesh,t:Transform3D,color:Color,channel:int)->void:
 var out:=surface(channel);var normal_t:=t.basis.inverse().transposed()
 for s in mesh.get_surface_count():
  var a:=mesh.surface_get_arrays(s);var ids:PackedInt32Array=a[Mesh.ARRAY_INDEX] if a[Mesh.ARRAY_INDEX]!=null else PackedInt32Array()
  var size:int=ids.size() if not ids.is_empty() else a[Mesh.ARRAY_VERTEX].size()
  for j in size:
   var i:int=ids[j] if not ids.is_empty() else j
   out.set_normal((normal_t*a[Mesh.ARRAY_NORMAL][i]).normalized())
   out.set_color(color.srgb_to_linear()*(a[Mesh.ARRAY_COLOR][i] if a[Mesh.ARRAY_COLOR]!=null else Color.WHITE))
   out.set_uv(a[Mesh.ARRAY_TEX_UV][i] if a[Mesh.ARRAY_TEX_UV]!=null else Vector2.ZERO);out.add_vertex(t*a[Mesh.ARRAY_VERTEX][i])
func box(at:Vector3,size:Vector3,color:Color,channel:int=0)->void:
 var m:Mesh=DisplayMeshes.beveled_box(size,minf(.006,minf(size.x,minf(size.y,size.z))*.18))
 part(m,Transform3D(Basis.IDENTITY,at),color,channel)
func rod(a:Vector3,b:Vector3,r:float,color:Color,channel:int=1)->void:
 var m:=CylinderMesh.new();m.top_radius=r;m.bottom_radius=r;m.height=a.distance_to(b);m.radial_segments=8;m.rings=0
 part(m,Transform3D(CivilianMotion.segment(a,b),(a+b)*.5),color,channel)
func blob(at:Vector3,size:Vector3,color:Color,channel:int=2)->void:
 var m:=SphereMesh.new();m.radius=1;m.height=2;m.radial_segments=14;m.rings=7
 part(m,Transform3D(Basis.IDENTITY.scaled(size),at),color,channel)
# profile rows are [Vector3 centre, half-width, half-depth].
func position(rows:Array,row:int,angle:float,fold:float,square:float)->Vector3:
 var p:Array=rows[row];var c:=cos(angle);var s:=sin(angle)
 var x:=signf(c)*pow(absf(c),2.0/square);var z:=signf(s)*pow(absf(s),2.0/square)
 var ripple:=1.0+fold*sin(angle*6+row*.85)*sin(PI*float(row)/maxi(1,rows.size()-1))
 return p[0]+Vector3(x*float(p[1])*ripple,0,z*float(p[2])*ripple)
func loft(rows:Array,color:Color,channel:int=0,segments:int=14,fold:float=.025,square:float=2.0)->void:
 var out:=surface(channel)
 for row in rows.size()-1:
  for j in segments:
   for corner in [Vector2i(0,0),Vector2i(1,0),Vector2i(0,1),Vector2i(1,0),Vector2i(1,1),Vector2i(0,1)]:
    var r:int=row+corner.y;var angle:float=(j+corner.x)*TAU/segments
    var p:=position(rows,r,angle,fold,square)
    var du:=position(rows,r,angle+.001,fold,square)-position(rows,r,angle-.001,fold,square)
    var dv:=position(rows,mini(r+1,rows.size()-1),angle,fold,square)-position(rows,maxi(0,r-1),angle,fold,square)
    out.set_normal(dv.cross(du).normalized());out.set_color(color.srgb_to_linear());out.set_uv(Vector2(float(j+corner.x)/segments,p.y*1.5));out.add_vertex(p)
 for top in [false,true]:
  var row:int=rows.size()-1 if top else 0;var center:Vector3=rows[row][0]
  for j in segments:
   for i in [-1,j if top else j+1,j+1 if top else j]:
    var p:Vector3=center if i<0 else position(rows,row,i*TAU/segments,fold,square)
    out.set_normal(Vector3.UP if top else Vector3.DOWN);out.set_color(color.srgb_to_linear());out.set_uv(Vector2(p.x,p.z));out.add_vertex(p)
func mesh()->ArrayMesh:
 var m:=ArrayMesh.new()
 for b:SurfaceTool in surfaces.values():b.index();b.generate_tangents();b.commit(m)
 return m
static func variant(index:int)->String:return ["jacket","shirt","knit"][posmod(index,3)]
static func make(kind:String)->ArrayMesh:
 if cache.has(kind):return cache[kind]
 var b:=ApparelModels.new()
 match kind:
  "jacket","shirt","knit":b.garment(kind,true)
  "trousers":b.trousers()
  "fold_stack":b.fold_stack()
  "mannequin":b.mannequin()
  _:push_error("Unknown apparel: "+kind)
 var m:=b.mesh();m.resource_name="Apparel_"+kind;cache[kind]=m;return m
func garment(kind:String,hanger:bool)->void:
 var cloth:=Color("4b596e") if kind=="jacket" else Color("c3d0da") if kind=="shirt" else Color("baaa90")
 loft([[Vector3(0,.02,0),.19,.085],[Vector3(0,.10,0),.195,.095],[Vector3(.004,.28,0),.175,.105],[Vector3(0,.44,0),.20,.11],[Vector3(0,.59,-.005),.225,.10],[Vector3(0,.66,0),.17,.075],[Vector3(0,.70,0),.065,.052]],cloth,0,16,.045,2.6)
 for side in [-1,1]:
  loft([[Vector3(side*.29,.13,.012),.045,.042],[Vector3(side*.285,.20,0),.049,.055],[Vector3(side*.27,.33,-.012),.06,.067],[Vector3(side*.25,.47,0),.07,.075],[Vector3(side*.21,.60,0),.09,.085]],cloth,0,12,.06)
  # Cuff piping, shoulder seam and tailored pocket edges.
  loft([[Vector3(side*.29,.12,.012),.048,.045],[Vector3(side*.29,.155,.012),.049,.046]],cloth.darkened(.10),0,12,0)
  if kind=="jacket":
   var lapel:Array=[Vector2(side*.055,.67),Vector2(side*.16,.57),Vector2(side*.045,.39)]
   part(ApparelModels.outline(lapel,.012),Transform3D(Basis.IDENTITY,Vector3(0,0,.11)),cloth.lightened(.16),0)
   box(Vector3(side*.105,.19,.094),Vector3(.115,.018,.018),cloth.darkened(.13))
  elif kind=="shirt":box(Vector3(side*.105,.46,.111),Vector3(.10,.12,.008),cloth.lightened(.055))
 if kind in ["jacket","shirt"]:
  box(Vector3(0,.34,.112),Vector3(.012,.52,.009),cloth.lightened(.09))
  for y in [.20,.31,.42]:blob(Vector3(.016,y,.122),Vector3(.007,.007,.004),Color("c0b6a4"),1)
 if kind=="shirt":
  for side in [-1,1]:
   part(ApparelModels.outline([Vector2(side*.035,.70),Vector2(side*.10,.65),Vector2(side*.045,.58)],.015),Transform3D(Basis.IDENTITY,Vector3(0,0,.087)),cloth.lightened(.15),0)
 else:
  part(RetailModels.arc(Vector3(0,.685,0),.056,.011,0,TAU),Transform3D(Basis(Vector3.RIGHT,PI/2),Vector3(0,.685,0)-Basis(Vector3.RIGHT,PI/2)*Vector3(0,.685,0)),cloth.darkened(.1),0)
 if hanger:
  for side in [-1,1]:rod(Vector3(0,.775,0),Vector3(side*.22,.63,0),.007,Color("a5a69c"))
  rod(Vector3(-.22,.63,0),Vector3(.22,.63,0),.007,Color("a5a69c"))
  part(RetailModels.arc(Vector3(0,.805,0),.029,.005,-PI*.2,PI*1.25),Transform3D.IDENTITY,Color("a5a69c"),1)
func trousers()->void:
 var c:=Color("66717c")
 loft([[Vector3(0,.52,0),.17,.09],[Vector3(0,.68,0),.18,.095],[Vector3(0,.75,0),.165,.085]],c,0,14,.025,2.8)
 for s in [-1,1]:
  loft([[Vector3(s*.09,.02,0),.056,.045],[Vector3(s*.094,.15,.006),.06,.05],[Vector3(s*.09,.32,-.009),.065,.055],[Vector3(s*.085,.49,0),.083,.075],[Vector3(s*.08,.59,0),.09,.084]],c,0,12,.045,2.6)
  box(Vector3(s*.09,.045,.044),Vector3(.09,.015,.005),c.lightened(.1))
 box(Vector3(0,.735,.083),Vector3(.32,.024,.012),c.darkened(.15))
 rod(Vector3(-.15,.785,0),Vector3(.15,.785,0),.007,Color("9b9b91"))
 for s in [-1,1]:box(Vector3(s*.11,.76,0),Vector3(.035,.05,.025),Color("8e928d"),1)
func fold_stack()->void:
 for i in 4:
  var y:float=i*.046;var c:Color=[Color("d2cbbb"),Color("79929a"),Color("dedbd2"),Color("526276")][i]
  loft([[Vector3(0,y+.003,0),.19,.13],[Vector3(.003,y+.013,0),.208,.144],[Vector3(0,y+.035,0),.206,.142],[Vector3(-.003,y+.041,0),.19,.13]],c,0,20,.02,5.0)
  box(Vector3(0,y+.019,.142),Vector3(.31,.005,.005),c.darkened(.17))
func mannequin()->void:
 var skin:=Color("d8d2c5");var suit:=Color("4b596e")
 box(Vector3(0,.018,0),Vector3(.56,.036,.42),Color("7b817e"),1)
 for s in [-1,1]:
  # Calves, knees and thighs taper independently instead of using straight rods.
  loft([[Vector3(s*.105,.09,0),.040,.042],[Vector3(s*.105,.19,0),.044,.049],[Vector3(s*.11,.34,-.012),.060,.063],[Vector3(s*.10,.47,-.018),.052,.060],[Vector3(s*.10,.59,0),.068,.073],[Vector3(s*.095,.77,0),.081,.085],[Vector3(s*.08,.87,0),.084,.087]],suit,0,14,.035)
  loft([[Vector3(s*.105,.038,.045),.070,.135],[Vector3(s*.105,.055,.05),.074,.143],[Vector3(s*.105,.085,.022),.063,.115],[Vector3(s*.105,.12,-.035),.040,.053]],Color("4a4a46"),2,14,0,3.0)
  loft([[Vector3(s*.29,.91,.015),.030,.032],[Vector3(s*.29,1.02,.005),.037,.042],[Vector3(s*.275,1.13,-.012),.047,.047],[Vector3(s*.25,1.27,0),.060,.057],[Vector3(s*.205,1.31,0),.075,.067]],skin,2,12,0)
  blob(Vector3(s*.294,.87,.021),Vector3(.033,.062,.024),skin)
  blob(Vector3(s*.267,.89,.043),Vector3(.014,.030,.015),skin)
 # Garment is built in its own local frame so the hanger is never worn.
 var jacket:=ApparelModels.new();jacket.garment("jacket",false)
 var jm:=jacket.mesh()
 for surface_index in jm.get_surface_count():
  var single:=ArrayMesh.new();single.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,jm.surface_get_arrays(surface_index))
  part(single,Transform3D(Basis.IDENTITY.scaled(Vector3(1.0,.88,1.0)),Vector3(0,.78,0)),Color.WHITE,int(jm.surface_get_material(surface_index).get_meta("retail_channel",0)))
 loft([[Vector3(0,1.37,0),.058,.050],[Vector3(0,1.49,0),.045,.043],[Vector3(0,1.53,0),.045,.042]],skin,2,14,0)
 loft([[Vector3(0,1.51,-.006),.040,.043],[Vector3(0,1.55,0),.062,.058],[Vector3(0,1.63,0),.082,.073],[Vector3(0,1.71,-.005),.078,.071],[Vector3(0,1.76,-.009),.050,.049],[Vector3(0,1.779,-.01),.008,.008]],skin,2,16,0)
