extends Node3D

# The print sits inside a recessed joinery bay on a solid, measured wall.
# The four construction materials are shared across the active shop interiors.
const INDEX := "res://source/v36/wall-editions.json"
const ART := "res://assets/v36/wall_editions/"
const CELL := 48.
const LOAD_M := 54.
const RETAIN_M := 68.

var player: Node3D
var by_cell: Dictionary = {}
var active: Dictionary = {}
var finishes: Array[StandardMaterial3D] = []
var joinery_cache: Dictionary = {}
var print_finishes: Dictionary = {}
var elapsed := 0.0
var washers: Array[SpotLight3D] = []

func setup(game: Node3D) -> void:
 name = "V36_Wall_Editions"
 player = game.player
 for color: Color in [Color("#6f513a"),Color("#54666a"),Color("#e4d6b9"),Color("#e5c58e")]:
  var finish := StandardMaterial3D.new()
  finish.albedo_color = color
  finish.roughness = .57
  finishes.append(finish)
 finishes[3].metallic = .52
 for i in 2:
  var light := SpotLight3D.new()
  light.name = "WallWasher%d" % i
  light.light_color = Color("#ffe4bb")
  light.light_energy = .62
  light.spot_angle = 70.
  light.spot_range = 3.6
  light.spot_attenuation = .78
  light.shadow_enabled = false
  light.hide()
  add_child(light)
  washers.append(light)
 for record:Dictionary in game.read_json(INDEX):
  var point: Vector3 = game.v3(record.p)
  record["point"] = point
  var cell := Vector2i(floori(point.x/CELL),floori(point.z/CELL))
  if not by_cell.has(cell): by_cell[cell] = []
  by_cell[cell].append(record)
 update_near()

func _process(delta:float) -> void:
 elapsed += delta
 if elapsed >= .28:
  elapsed = 0.
  update_near()

func update_near() -> void:
 if not is_instance_valid(player):return
 var p := player.global_position
 for id:String in active.keys():
  var root:Node3D = active[id]
  if absf(root.position.y-p.y-2.45)>7. or Vector2(root.position.x-p.x,root.position.z-p.z).length_squared()>RETAIN_M*RETAIN_M:
   active.erase(id)
   remove_child(root)
   root.queue_free()
 for x in range(floori((p.x-LOAD_M)/CELL),floori((p.x+LOAD_M)/CELL)+1):
  for z in range(floori((p.z-LOAD_M)/CELL),floori((p.z+LOAD_M)/CELL)+1):
   for d:Dictionary in by_cell.get(Vector2i(x,z),[]):
    var a:Vector3=d.point
    if not active.has(d.id) and absf(a.y-p.y-2.45)<5.5 and Vector2(a.x-p.x,a.z-p.z).length_squared()<LOAD_M*LOAD_M:
     install(d)
 update_lights(p)

func update_lights(p:Vector3)->void:
 var nearest: Array[Node3D] = []
 for holder:Node3D in active.values():
  var separation:=p-holder.position
  var distance:=Vector2(separation.x,separation.z).length_squared()
  if absf(separation.y+2.45)>1.9 or distance>13.*13. or separation.dot(holder.basis.z)<0.:
   continue
  nearest.append(holder)
 nearest.sort_custom(func(a:Node3D,b:Node3D):return a.position.distance_squared_to(p)<b.position.distance_squared_to(p))
 for i in washers.size():
  var light:=washers[i]
  if i>=nearest.size():
   light.hide()
   continue
  var holder:=nearest[i]
  light.position=holder.position+Vector3.UP*1.04+holder.basis.z*.20
  light.look_at(holder.position+Vector3.UP*.25+holder.basis.z*.04)
  light.show()

func box(tool:SurfaceTool,x:float,y:float,z:float,w:float,h:float,depth:float)->void:
 var mesh:=BoxMesh.new()
 mesh.size=Vector3(w,h,depth)
 tool.append_from(mesh,0,Transform3D(Basis.IDENTITY,Vector3(x,y,z)))

func install(d:Dictionary)->void:
 var holder:=Node3D.new()
 holder.name=str(d.id).validate_node_name()
 holder.position=d.point
 holder.rotation.y=atan2(float(d.normal[0]),float(d.normal[1]))
 add_child(holder)
 active[d.id]=holder
 # The millwork is fabricated in 10 cm increments inside the measured wall span.
 var width_steps := floori(float(d.width)*10.)
 var key := Vector2i(width_steps,int(d.style))
 if not joinery_cache.has(key):
  joinery_cache[key]=fabricate(float(width_steps)*.1,float(d.height),int(d.style))
 var frame:=MeshInstance3D.new()
 frame.mesh=joinery_cache[key]
 if not print_finishes.has(d.tile):
  var print_material:=StandardMaterial3D.new()
  print_material.albedo_texture=load(ART+str(d.tile)+".webp")
  print_material.roughness=.73
  print_finishes[d.tile]=print_material
 frame.set_surface_override_material(2,print_finishes[d.tile])
 frame.visibility_range_end=RETAIN_M
 holder.add_child(frame)

func fabricate(w:float,h:float,style:int)->ArrayMesh:
 var joinery:=ArrayMesh.new()
 var casework:=SurfaceTool.new()
 casework.begin(Mesh.PRIMITIVE_TRIANGLES)
 casework.set_material(finishes[style])
 # The lip and reveals cast a shadow over the existing interior wall.
 box(casework,0.,h*.50,.009,w,h+.16,.023)
 box(casework,0.,h+.075,.064,w+.035,.035,.12)
 box(casework,0.,-.067,.055,w+.035,.032,.094)
 var picture_w:=minf(w-.36,2.74)
 var location:=0. if style==0 else (w-picture_w)*(.31 if style==1 else -.31)
 var slats:=floori(w/.12)
 for i in slats:
  var x:=(i+.5)*w/slats-w*.5
  if absf(x-location)>picture_w*.5+.055:
   box(casework,x,h*.5,.03,.039,h+.07,.036)
 # Extend the lower lining to the lowest verified segment of opaque wall. The
 # customer route and the furniture below the original rear signage stay clear.
 var dado_height:=1.16
 box(casework,0.,-.09-dado_height*.5,.0005,w,dado_height,.018)
 var bay_count:=maxi(2,roundi(w/(.9 if style==2 else 1.28)))
 for bay in range(1,bay_count):
  var seam_x:=(float(bay)/float(bay_count)-.5)*w
  box(casework,seam_x,-.09-dado_height*.5,.016,.014,dado_height,.018)
 if style==1:
  box(casework,0.,-.62,.016,w,.018,.018)
 elif style==0:
  var parts:=maxi(2,floori(w/.15))
  for n in parts:
   var slat_x:=((n+.5)/parts-.5)*w
   if absf(slat_x)>.32*w:
    box(casework,slat_x,-.09-dado_height*.5,.018,.038,dado_height,.026)
 box(casework,0.,-1.25,.019,w,.034,.042)
 casework.commit(joinery)
 var trims:=SurfaceTool.new()
 trims.begin(Mesh.PRIMITIVE_TRIANGLES)
 trims.set_material(finishes[3])
 for x:float in [-picture_w*.5-.018,picture_w*.5+.018]:
  box(trims,location+x,h*.5,.051,.021,h+.029,.043)
 box(trims,location,h+.009,.051,picture_w+.055,.018,.044)
 box(trims,location,-.009,.051,picture_w+.055,.018,.044)
 trims.commit(joinery)
 var face:=QuadMesh.new()
 face.size=Vector2(picture_w,h)
 var print_surface:=SurfaceTool.new()
 print_surface.begin(Mesh.PRIMITIVE_TRIANGLES)
 print_surface.set_material(finishes[2])
 print_surface.append_from(face,0,Transform3D(Basis.IDENTITY,Vector3(location,h*.5,.054)))
 print_surface.commit(joinery)
 return joinery
