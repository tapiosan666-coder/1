extends Node3D
## Floor medallions and suspended joinery at surveyed public crossroads. Dimensions
## and hanger contact heights come from the actual floor and ceiling at each site.

const CATALOG := "res://source/v36/public-courts.json"
const MATERIALS := {
 "A":[Color("#d1b478"), Color("#566d73"), Color("#f0e4cd"), Color("#fff1cc")],
 "B":[Color("#946c44"), Color("#52675a"), Color("#ceae79"), Color("#ffdfb6")],
 "C":[Color("#a17955"), Color("#69665a"), Color("#d3bda4"), Color("#ffe7bc")]
}
var game: Node3D
var zones: Array
var resident: Dictionary = {}
var palette: Dictionary = {}
var textures: Dictionary = {}
var timer := 0.0

func setup(scene: Node3D) -> void:
 game = scene
 name = "V36_Public_Courts"
 zones = game.read_json(CATALOG)
 update_near()

func _process(delta: float) -> void:
 timer += delta
 if timer >= .32:
  timer = 0.0
  update_near()

func update_near() -> void:
 if not is_instance_valid(game) or not is_instance_valid(game.get("player")): return
 var eye: Vector3 = game.player.position
 for row: Dictionary in zones:
  var at := Vector3(row.p[0],row.p[1],row.p[2])
  var radius2 := Vector2(at.x-eye.x,at.z-eye.z).length_squared()
  if resident.has(row.zone):
   if radius2 > 101.0*101.0 or absf(at.y-eye.y)>13.2:
    var old:Node3D=resident[row.zone]
    resident.erase(row.zone)
    remove_child(old)
    old.queue_free()
  elif radius2<81.0*81.0 and absf(at.y-eye.y)<9.0:
   var node=build(row)
   add_child(node)
   resident[row.zone]=node

func materials(wing:String) -> Array:
 if palette.has(wing): return palette[wing]
 var out := []
 var colors:Array=MATERIALS[wing]
 for index:int in colors.size():
  var mat:=StandardMaterial3D.new()
  mat.albedo_color=colors[index]
  mat.roughness=[.39,.55,.64,.29][index]
  if index==0 and wing=="A": mat.metallic=.55
  if index==3:
   mat.emission_enabled=true
   mat.emission=colors[index]
   mat.emission_energy_multiplier=1.16
  out.append(mat)
 palette[wing]=out
 return out

func inlay(wing:String, district:int) -> Material:
 var key: String=wing+str(district)
 if textures.has(key):return textures[key]
 var mat:=StandardMaterial3D.new()
 mat.albedo_texture=load("res://assets/v36/commons/inlay-"+key+".webp")
 mat.texture_filter=BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
 mat.roughness=.56 if wing=="C" else .4
 textures[key]=mat
 return mat

# Build one indexed surface per finish for an entire bay. All hanging elements
# lie above normal sign/door head clearance and never supply a fake support floor.
func tri(tool:SurfaceTool,a:Vector3,b:Vector3,c:Vector3,normal:Vector3) -> void:
 var vertices:=[a,b,c] if (b-a).cross(c-a).dot(normal)<0 else [a,c,b]
 for vertex:Vector3 in vertices:
  tool.set_normal(normal)
  tool.add_vertex(vertex)

func quad(tool:SurfaceTool,a:Vector3,b:Vector3,c:Vector3,d:Vector3,n:Vector3) -> void:
 tri(tool,a,b,c,n)
 tri(tool,a,c,d,n)

func bar(tool:SurfaceTool,a:Vector3,b:Vector3,width:float,depth:float) -> void:
 var along:=(b-a).normalized()
 var side:=Vector3.UP.cross(along).normalized()
 if side.length_squared()<.5:side=Vector3.RIGHT
 var top:=along.cross(side).normalized()
 side*=width*.5
 top*=depth*.5
 var corners:=[a-side-top,a+side-top,a+side+top,a-side+top,b-side-top,b+side-top,b+side+top,b-side+top]
 for face:Array in [[0,1,2,3,-along],[4,5,6,7,along],[0,1,5,4,-top.normalized()],[1,2,6,5,side.normalized()],[2,3,7,6,top.normalized()],[3,0,4,7,-side.normalized()]]:
  quad(tool,corners[face[0]],corners[face[1]],corners[face[2]],corners[face[3]],face[4])

func tool_for(mat:Material) -> SurfaceTool:
 var tool:=SurfaceTool.new()
 tool.begin(Mesh.PRIMITIVE_TRIANGLES)
 tool.set_material(mat)
 return tool

func medallion(width:float,depth:float,wing:String,district:int) -> ArrayMesh:
 var tool:=tool_for(inlay(wing,district))
 var vertices := PackedVector2Array()
 # Metal-edged oval in the atrium, mitred stone in the city galleries,
 # and clipped brick corners on the outdoor walking decks.
 var samples:=64 if wing=="B" else 8
 if wing=="B":
  for i in samples:
   var a:=float(i)*TAU/float(samples)
   vertices.append(Vector2(cos(a)*.49,sin(a)*.49))
 else:
  var corner:= .19 if wing=="A" else .105
  vertices=PackedVector2Array([Vector2(-.48+corner,-.49),Vector2(.48-corner,-.49),Vector2(.48,-.49+corner),Vector2(.48,.49-corner),Vector2(.48-corner,.49),Vector2(-.48+corner,.49),Vector2(-.48,.49-corner),Vector2(-.48,-.49+corner)])
 for i in vertices.size():
  for v:Vector2 in [Vector2.ZERO,vertices[i],vertices[(i+1)%vertices.size()]]:
   tool.set_uv(v+Vector2(.5,.5))
   tool.set_normal(Vector3.UP)
   tool.add_vertex(Vector3(v.x*width,.017,v.y*depth))
 var result:=tool.commit()
 var edge:=tool_for(materials(wing)[0])
 for i in vertices.size():
  var p:=vertices[i]
  var q:=vertices[(i+1)%vertices.size()]
  var a:=Vector3(p.x*width,.018,p.y*depth)
  var b:=Vector3(q.x*width,.018,q.y*depth)
  var ra:=Vector3(a.x*.984,a.y,a.z*.984)
  var rb:=Vector3(b.x*.984,b.y,b.z*.984)
  quad(edge,a,b,rb,ra,Vector3.UP)
 edge.index();edge.commit(result)
 return result

func joinery(row:Dictionary, width:float,depth:float) -> ArrayMesh:
 var wing:=str(row.wing)
 var mats:=materials(wing)
 var wood:=tool_for(mats[0])
 var frame:=tool_for(mats[1])
 var trim:=tool_for(mats[2])
 var lamp:=tool_for(mats[3])
 var lower:float=float(row.soffit_samples_y.min())-float(row.p[1])-.35
 var legs:= row.soffit_samples_y as Array
 var count:=0
 for x: float in [-.38,.38]:
  for z: float in [-.38,.38]:
   var foot:=Vector3(width*x,lower,depth*z)
   bar(frame,foot,Vector3(foot.x,float(legs[count])-float(row.p[1])+.011,foot.z),.04,.04)
   count+=1
 # Suspended edge rails make the four measured attachment points legible.
 for x: float in [-.38,.38]:
  bar(frame,Vector3(width*x,lower,depth*-.38),Vector3(width*x,lower,depth*.38),.07,.09)
 var model_scale:=minf(width/5.4,1.)
 if wing=="A":
  # Three pleated bronze coffers, open between sections to retain the ceiling.
  for j:int in 3:
   var z:float=(j-1)*depth*.23
   var ridge:=Vector3(0.,lower-.19*model_scale,z+.19)
   var left:=Vector3(-width*.38,lower,z-.32*model_scale)
   var right:=Vector3(width*.38,lower,z-.32*model_scale)
   for end:Vector3 in [left,right]:
    bar(wood,end,ridge,.10,.095)
    bar(lamp,end-Vector3.UP*.052,ridge-Vector3.UP*.052,.038,.012)
   var tail:=ridge+Vector3(0.,.19*model_scale,depth*.095)
   tri(trim,left,tail,ridge,Vector3.DOWN)
   tri(trim,right,ridge,tail,Vector3.DOWN)
   bar(frame,left,right,.09,.08)
 elif wing=="B":
  # Leaf-shaped laminated light trough. A central keel meets the transverse
  # suspension beams; each swept rib has a different chord length.
  for z:float in [-.38,.38]:
   bar(frame,Vector3(-width*.38,lower,depth*z),Vector3(width*.38,lower,depth*z),.07,.12)
  bar(wood,Vector3(0.,lower,depth*-.38),Vector3(0.,lower,depth*.38),.15,.14)
  for i:int in 13:
   var u:float=float(i+1)/14.
   var z:=lerpf(-.37,.37,u)*depth
   var span:=width*.39*pow(sin(u*PI),.74)
   for side:float in [-1.,1.]:
    var base:=Vector3(0.,lower-.03,z-.06)
    var mid:=Vector3(side*span*.54,lower-model_scale*.17,z+.15*model_scale)
    var end:=Vector3(side*span,lower-.055,z+.45*model_scale)
    bar(wood,base,mid,.060,.11)
    bar(trim,mid,end,.060,.085)
    if i%3==1:bar(lamp,base-Vector3.UP*.062,mid-Vector3.UP*.062,.031,.012)
 else:
  # Slatted portico panels, with dark trim at the actual abutting ceiling edges.
  for i:int in 9:
   var z:float=lerpf(-.35,.35,float(i)/8.)*depth
   var mid:=Vector3(0.,lower-.14*model_scale,z)
   var left:=Vector3(-width*.38,lower,z)
   var right:=Vector3(width*.38,lower,z)
   bar(wood,left,mid,.10,.115)
   bar(trim,mid,right,.10,.115)
   if i in [1,7]:bar(lamp,left-Vector3.UP*.065,mid-Vector3.UP*.065,.06,.014)
 var result:=ArrayMesh.new()
 for t:SurfaceTool in [wood,frame,trim,lamp]:
  t.index()
  t.commit(result)
 return result

func mesh_part(root:Node3D,mesh:Mesh,id:String) -> void:
 var piece:=MeshInstance3D.new()
 piece.name=id
 piece.mesh=mesh
 piece.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 piece.visibility_range_end=88.
 piece.visibility_range_end_margin=5.
 root.add_child(piece)

func bridge_plate(bay:Node3D,row:Dictionary,width:float,depth:float) -> void:
 var drop:float=float(row.soffit_samples_y.min())-float(row.p[1])-.35
 var key:String="link-"+str(row.link)+"-"+str(row.floor)
 if not textures.has(key):
  var ink:=StandardMaterial3D.new()
  ink.albedo_texture=load("res://assets/v36/commons/"+key+".webp")
  ink.texture_filter=BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
  ink.roughness=.63
  textures[key]=ink
 var plate_width:=minf(width*.76,2.24)
 var plate_height:=plate_width*168./864.
 var crossbar:=tool_for(materials(row.wing)[1])
 var z:float=-depth*.38
 var top:=drop-.062
 var level:=top-.15-plate_height*.5
 for x:float in [-.38,.38]:
  var arm:=Vector3(width*x,drop,z)
  bar(crossbar,arm,Vector3(x*plate_width,top-.15,z),.041,.043)
 bar(crossbar,Vector3(-plate_width*.52,level,z),Vector3(plate_width*.52,level,z),.078,plate_height+.033)
 var trim:=crossbar.commit()
 mesh_part(bay,trim,"Link_identification_frame")
 for side:float in [-1.,1.]:
  var face:=MeshInstance3D.new()
  var printed:=QuadMesh.new()
  printed.size=Vector2(plate_width,plate_height)
  printed.material=textures[key]
  face.mesh=printed
  face.position=Vector3(0.,level,z+side*.0405)
  if side<0:face.rotation.y=PI
  face.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
  face.visibility_range_end=70.
  bay.add_child(face)

func clad_wall(panel:Node3D,row:Dictionary,spec:Dictionary) -> void:
 var survey:Dictionary=spec.cladding
 var wing:String=row.wing
 var key:="cladding-"+wing
 if not textures.has(key):
  var finish:=StandardMaterial3D.new()
  finish.albedo_texture=load("res://assets/v36/commons/"+key+".webp")
  finish.texture_filter=BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
  finish.roughness=.71
  textures[key]=finish
 var front:=tool_for(textures[key])
 var left:=float(survey.l)+.12
 var right:=float(survey.r)-.12
 var low:=float(row.p[1])+float(survey.bottom)-float(spec.p[1])
 var high:=float(row.p[1])+float(survey.top)-float(spec.p[1])
 # Return the edges into the original face, including minor surveyed rebates.
 # The directory itself is at +73mm relative to the reference wall plane.
 var nose:=float(survey.max_surface_offset)+.007-.073
 var back:=float(survey.min_surface_offset)-.004-.073
 var period:=2.35 if wing=="A" else 3.10
 var corners:=[Vector3(left,low,nose),Vector3(left,high,nose),Vector3(right,low,nose),Vector3(right,high,nose)]
 for index:int in [0,1,2,2,1,3]:
  var v:Vector3=corners[index]
  var h:=v.y+float(spec.p[1])-float(row.p[1])
  front.set_uv(Vector2((v.x-left)/period,(3.80-h)/3.60));front.set_normal(Vector3.BACK);front.add_vertex(v)
 var mesh:=front.commit()
 var edges:=tool_for(materials(wing)[1])
 for pair:Array in [[0,1,Vector3.LEFT],[3,2,Vector3.RIGHT],[1,3,Vector3.UP],[2,0,Vector3.DOWN]]:
  var a:Vector3=corners[pair[0]]
  var b:Vector3=corners[pair[1]]
  quad(edges,a,b,Vector3(b.x,b.y,back),Vector3(a.x,a.y,back),pair[2])
 edges.commit(mesh)
 mesh_part(panel,mesh,"Surveyed_wall_lining")

func exhibition(bay:Node3D,row:Dictionary) -> void:
 var spec:Dictionary=row.wall
 var key:String="wall-"+str(row.zone)
 if not textures.has(key):
  var print_mat:=StandardMaterial3D.new()
  print_mat.albedo_texture=load("res://assets/v36/commons/"+key+".webp")
  print_mat.texture_filter=BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
  print_mat.roughness=.72
  textures[key]=print_mat
 var normal:=Vector3(spec.n[0],0.,spec.n[2]).normalized()
 var at:=Vector3(spec.p[0],spec.p[1],spec.p[2])
 var width:=float(spec.width)
 var height:=float(spec.height)
 var panel:=Node3D.new()
 panel.name="Illustrated_local_directory"
 # The bench/plaza frame and the actual wall face often have different bearings.
 panel.transform=bay.transform.affine_inverse()*Transform3D(Basis(Vector3.UP.cross(normal),Vector3.UP,normal),at+normal*.073)
 bay.add_child(panel)
 if spec.has("cladding"):clad_wall(panel,row,spec)
 var strip:=tool_for(materials(row.wing)[0])
 var half:=Vector2(width*.5,height*.5)
 for edge:float in [-1.,1.]:
  bar(strip,Vector3(-half.x,edge*half.y,-.013),Vector3(half.x,edge*half.y,-.013),.025,.035)
  bar(strip,Vector3(edge*half.x,-half.y,-.012),Vector3(edge*half.x,half.y,-.012),.026,.03)
 mesh_part(panel,strip.commit(),"Extruded_frame")
 var artwork:=QuadMesh.new()
 artwork.size=Vector2(width-.033,height-.029)
 artwork.material=textures[key]
 mesh_part(panel,artwork,"Local_shops_and_original_mural")

func build(row:Dictionary) -> Node3D:
 var bay:=Node3D.new()
 bay.name=str(row.zone).validate_node_name()
 bay.position=Vector3(row.p[0],row.p[1],row.p[2])
 var n:=Vector3(row.n[0],0.,row.n[2]).normalized()
 bay.basis=Basis(Vector3.UP.cross(n),Vector3.UP,n)
 var width:=float(row.size[0])
 var depth:=float(row.size[1])
 mesh_part(bay,medallion(width,depth,row.wing,int(row.district)),"Cut_stone")
 if row.has("wall"):exhibition(bay,row)
 if row.canopy:
  mesh_part(bay,joinery(row,width,depth),"Suspended_joinery")
  if row.has("link"):bridge_plate(bay,row,width,depth)
 return bay
