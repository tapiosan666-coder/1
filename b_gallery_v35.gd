extends Node3D

## Time Plaza and its two adjacent retailers use the same surveyed circulation.
const FLOOR := 0.048
const CLOCK := Vector3(-4.72, 0.04, 15.10)
const CLOCK_RADIUS := 1.23
const CLOCK_CENTER := Vector3(0.0, 2.47, 0.0)
const CLOCK_TRIANGLE_COLLISION := 1
const AREA_CENTER := Vector2(-10.5, 27.0)
const ACTIVE_RADIUS := 64.0
const RETIRE_RADIUS := 79.0
const IVORY := Color("#f4e4c3")
const TEXT_FONT := preload("res://assets/NotoSansCJKjp-Regular.otf")

var game: Node3D
var installation: Node3D
var sections: Dictionary = {}
var batches: Dictionary = {}
var clock_hands: Array[Node3D] = []
var refresh_elapsed := 0.0
var shown_minute := -1


func setup(scene: Node3D) -> void:
 game = scene
 name = "V35_B_Gallery"
 refresh_elapsed = 0.25


func _process(delta: float) -> void:
 refresh_elapsed += delta
 if refresh_elapsed < 0.25:
  return
 refresh_elapsed = 0.0
 update_near()
 update_clock()


func update_near() -> void:
 var player: Node3D = game.get("player")
 if not is_instance_valid(player):
  return
 var point := player.global_position
 var at := Vector2(point.x, point.z)
 var near := at.distance_to(AREA_CENTER)
 if is_instance_valid(installation):
  if near > RETIRE_RADIUS or absf(point.y) > 5.9:
   clock_hands.clear()
   remove_child(installation)
   installation.queue_free()
   installation = null
  return
 # The plaza clock stays visible from its 2F gallery.
 if near < ACTIVE_RADIUS and absf(point.y) < 5.9:
  build()


func finish(key: String, tint: Color, roughness: float, metal: float = 0.0, emission: float = 0.0) -> StandardMaterial3D:
 if sections.has(key):
  return sections[key]
 var surface := StandardMaterial3D.new()
 surface.resource_name = key
 surface.albedo_color = tint
 surface.roughness = roughness
 surface.metallic = metal
 if emission > 0.0:
  surface.emission_enabled = true
  surface.emission = tint
  surface.emission_energy_multiplier = emission
 sections[key] = surface
 return surface


func stone(key: String, tint: Color) -> StandardMaterial3D:
 var surface := finish(key, tint, 0.67)
 surface.albedo_texture = load("res://assets/v10/materials/terrazzo-albedo.webp")
 return surface


func timber() -> StandardMaterial3D:
 var surface := finish("Smoked quarter sawn oak", Color("#9d7756"), 0.63)
 surface.albedo_texture = load("res://assets/v8/oak.webp")
 surface.normal_enabled = true
 surface.normal_texture = load("res://assets/v8/oak-normal.webp")
 surface.normal_scale = 0.40
 return surface


func mesh_batch(surface: Material) -> SurfaceTool:
 if not batches.has(surface):
  var tool := SurfaceTool.new()
  tool.begin(Mesh.PRIMITIVE_TRIANGLES)
  tool.set_material(surface)
  batches[surface] = tool
 return batches[surface]


func panel(point: Vector3, size: Vector3, surface: Material, orientation: Basis = Basis.IDENTITY) -> void:
 var geometry := BoxMesh.new()
 geometry.size = size
 mesh_batch(surface).append_from(geometry, 0, Transform3D(orientation, point))


func round_shape(point: Vector3, radius: float, height: float, surface: Material, orientation: Basis = Basis.IDENTITY) -> void:
 var geometry := CylinderMesh.new()
 geometry.top_radius = radius
 geometry.bottom_radius = radius
 geometry.height = height
 geometry.radial_segments = 24
 geometry.rings = 1
 mesh_batch(surface).append_from(geometry, 0, Transform3D(orientation, point))


func append_quad(tool: SurfaceTool, points: Array[Vector3], normal: Vector3, uvs: Array[Vector2]) -> void:
 for i: int in [0, 1, 2, 0, 2, 3]:
  tool.set_normal(normal)
  tool.set_uv(uvs[i])
  tool.add_vertex(points[i])


func curve_strip(path: PackedVector3Array, width: float, surface: Material) -> void:
 var side := PackedVector3Array()
 for i in range(path.size()):
  var tangent := path[mini(i+1, path.size()-1)] - path[maxi(i-1, 0)]
  side.append(Vector3.UP.cross(tangent.normalized()) * width * 0.5)
 var tool := mesh_batch(surface)
 var accumulated := 0.0
 for i in range(path.size()-1):
  var a := path[i]
  var b := path[i+1]
  var length := a.distance_to(b)
  append_quad(tool, [a-side[i],a+side[i],b+side[i+1],b-side[i+1]], Vector3.UP,
   [Vector2(accumulated,0.0),Vector2(accumulated,width),Vector2(accumulated+length,width),Vector2(accumulated+length,0.0)])
  accumulated += length


func annulus(center: Vector3, inner: float, outer: float, surface: Material) -> void:
 var tool := mesh_batch(surface)
 for i in range(128):
  var a := TAU * float(i) / 128.0
  var b := TAU * float(i+1) / 128.0
  var first := Vector3(cos(a), 0.0, sin(a))
  var second := Vector3(cos(b), 0.0, sin(b))
  var vertices: Array[Vector3] = [
   center + first * inner, center + first * outer,
   center + second * outer, center + second * inner
  ]
  var uv: Array[Vector2] = []
  for p: Vector3 in vertices:
   uv.append(Vector2(p.x, p.z) * 0.58)
  append_quad(tool, vertices, Vector3.UP, uv)


func octagon(x: float, z: float, bevel: float) -> PackedVector2Array:
 var half_x := x * 0.5
 var half_z := z * 0.5
 return PackedVector2Array([
  Vector2(-half_x+bevel,-half_z),Vector2(half_x-bevel,-half_z),
  Vector2(half_x,-half_z+bevel),Vector2(half_x,half_z-bevel),
  Vector2(half_x-bevel,half_z),Vector2(-half_x+bevel,half_z),
  Vector2(-half_x,half_z-bevel),Vector2(-half_x,-half_z+bevel)
 ])


func plinth(point: Vector3, size: Vector3, bevel: float, surface: Material, collidable: bool) -> void:
 var ring := octagon(size.x,size.z,bevel)
 var tool := SurfaceTool.new()
 tool.begin(Mesh.PRIMITIVE_TRIANGLES)
 tool.set_material(surface)
 for i in range(ring.size()):
  var a := ring[i]
  var b := ring[(i+1)%ring.size()]
  var bottom_a := point + Vector3(a.x, 0.0, a.y)
  var bottom_b := point + Vector3(b.x, 0.0, b.y)
  var top_a := bottom_a + Vector3.UP * size.y
  var top_b := bottom_b + Vector3.UP * size.y
  var outward := (bottom_b-bottom_a).cross(Vector3.UP).normalized() * -1.0
  append_quad(tool, [bottom_a,bottom_b,top_b,top_a], outward, [Vector2(0,1),Vector2(1,1),Vector2(1,0),Vector2(0,0)])
  for p: Vector3 in [point+Vector3.UP*size.y,top_a,top_b]:
   tool.set_normal(Vector3.UP)
   tool.set_uv(Vector2(p.x,p.z)*0.40)
   tool.add_vertex(p)
 var piece := MeshInstance3D.new()
 piece.mesh = tool.commit()
 installation.add_child(piece)
 if collidable:
  var body := StaticBody3D.new()
  body.name = "ClockPlinth"
  body.collision_layer = CLOCK_TRIANGLE_COLLISION
  body.collision_mask = 0
  var shape := CollisionShape3D.new()
  shape.shape = piece.mesh.create_trimesh_shape()
  body.add_child(shape)
  installation.add_child(body)


func wall_label(point: Vector3, facing: Vector3, wording: String, height: float, tint: Color) -> void:
 var label := Label3D.new()
 label.font = TEXT_FONT
 label.font_size = 64
 label.pixel_size = height / 64.0
 label.modulate = tint
 label.outline_size = 0
 label.double_sided = false
 label.no_depth_test = false
 label.visibility_range_end = 41.0
 label.position = point
 label.basis = Basis(Vector3.UP.cross(facing),Vector3.UP,facing)
 label.text = wording
 installation.add_child(label)


func clock_bezel(surface: Material, rims: Array[Vector2]) -> void:
 # Complex ruled profile keeps the face clean, with seams where real parts would meet.
 var tool := mesh_batch(surface)
 var center := CLOCK + CLOCK_CENTER
 for ring in range(rims.size()-1):
  var first := rims[ring]
  var second := rims[ring+1]
  for i in range(96):
   var a := TAU * float(i) / 96.0
   var b := TAU * float(i+1) / 96.0
   var axis_a := Vector3(sin(a), cos(a), 0.0)
   var axis_b := Vector3(sin(b), cos(b), 0.0)
   var normal := (axis_a+axis_b).normalized() * (second.y-first.y)
   normal.z = first.x-second.x
   append_quad(tool,[
    center+axis_a*first.x+Vector3.BACK*first.y,
    center+axis_b*first.x+Vector3.BACK*first.y,
    center+axis_b*second.x+Vector3.BACK*second.y,
    center+axis_a*second.x+Vector3.BACK*second.y
   ], normal.normalized(), [
    Vector2(float(i)/96.0,0.0), Vector2(float(i+1)/96.0,0.0),
    Vector2(float(i+1)/96.0,1.0), Vector2(float(i)/96.0,1.0)
   ])


func clock_hand(center: Vector3, facing: Vector3, length: float, width: float, depth: float, surface: Material) -> void:
 var pivot := Node3D.new()
 pivot.position = center
 pivot.basis = Basis(Vector3.UP.cross(facing), Vector3.UP, facing)
 installation.add_child(pivot)
 var hand := MeshInstance3D.new()
 var housing := PrismMesh.new()
 housing.size = Vector3(width, length, depth)
 hand.mesh = housing
 hand.material_override = surface
 hand.position.y = length * .35
 pivot.add_child(hand)
 clock_hands.append(pivot)


func update_clock() -> void:
 if clock_hands.size() != 4:
  return
 var time := Time.get_time_dict_from_system()
 var minute: int = time.minute
 if shown_minute == minute:
  return
 shown_minute = minute
 var hours := (float(time.hour % 12) + float(minute) / 60.0) / 12.0
 for i in [0,2]:
  var face := Basis(Vector3.UP, PI if i==2 else 0.0)
  clock_hands[i].basis = face * Basis(Vector3.BACK, -TAU * hours)
  clock_hands[i+1].basis = face * Basis(Vector3.BACK, -TAU * float(minute) / 60.0)


func build_station() -> void:
 var terrazzo := stone("Terrazzo plinth", Color("#81736d"))
 var bronze := finish("Phosphor bronze", Color("#b07545"), .35, .45)
 var deep := finish("Kiln fired indigo enamel", Color("#275058"), .42, .18)
 var mantel := finish("Deep bronze structure", Color("#513e37"), .52, .32)
 var lettering := finish("Putty ceramic", IVORY, .73, 0.0, .12)
 annulus(Vector3(CLOCK.x,FLOOR,CLOCK.z), 0.0, 2.64,
  stone("Clock terrazzo socket", Color("#807673")))
 annulus(Vector3(CLOCK.x,FLOOR+.003,CLOCK.z), 2.52,2.59,bronze)
 annulus(Vector3(CLOCK.x,FLOOR+.003,CLOCK.z), 2.35,2.38,bronze)
 plinth(CLOCK,Vector3(3.32,.27,1.30),.21,terrazzo,true)
 plinth(CLOCK+Vector3.UP*.05,Vector3(3.36,.037,1.34),.21,bronze,true)
 plinth(CLOCK+Vector3.UP*.27,Vector3(3.20,.055,1.18),.20,mantel,false)
 # Cantilever brackets terminate under the dial, with their feet on the plinth.
 for x: float in [-.90,.90]:
  var low := CLOCK+Vector3(x,.32,0.0)
  var high := CLOCK+Vector3(x*.69,1.68,0.0)
  var lean := atan2(-(high.x-low.x),high.y-low.y)
  panel((low+high)*.5,Vector3(.22,low.distance_to(high),.36),mantel,Basis(Vector3.BACK,lean))
  panel(low+Vector3.UP*.041,Vector3(.43,.087,.58),bronze)
 panel(CLOCK+Vector3.UP*.96, Vector3(1.48,.35,.155), deep)
 # The guarded bezel lies entirely over its plinth and extends above the plaque.
 var structure := StaticBody3D.new()
 structure.name = "ClockBody"
 structure.collision_layer = CLOCK_TRIANGLE_COLLISION
 structure.collision_mask = 0
 var plaque_collision := CollisionShape3D.new()
 var plaque_box := BoxShape3D.new()
 plaque_box.size = Vector3(1.53,.37,.39)
 plaque_collision.shape = plaque_box
 plaque_collision.position = CLOCK+Vector3.UP*.95
 structure.add_child(plaque_collision)
 var dial_collision := CollisionShape3D.new()
 var dial_cylinder := CylinderShape3D.new()
 dial_cylinder.radius = CLOCK_RADIUS
 dial_cylinder.height = .40
 dial_collision.shape = dial_cylinder
 dial_collision.position = CLOCK+CLOCK_CENTER
 dial_collision.rotation.x = PI/2.0
 structure.add_child(dial_collision)
 for x: float in [-.84,.84]:
  var leg := CollisionShape3D.new()
  var leg_box := BoxShape3D.new()
  leg_box.size = Vector3(.25,1.15,.36)
  leg.shape = leg_box
  leg.position = CLOCK+Vector3(x,.87,0.0)
  leg.rotation.z = signf(x)*.16
  structure.add_child(leg)
 installation.add_child(structure)

 var face_center := CLOCK+CLOCK_CENTER
 var face_rotation := Basis(Vector3.RIGHT,PI/2.0)
 round_shape(face_center,CLOCK_RADIUS-.11,.32,deep,face_rotation)
 clock_bezel(mantel, [Vector2(1.09,-.19),Vector2(1.22,-.22),Vector2(1.27,-.155),Vector2(1.27,.155),Vector2(1.22,.22),Vector2(1.09,.19)])
 clock_bezel(bronze, [Vector2(1.08,-.197),Vector2(1.12,-.217),Vector2(1.19,-.222),Vector2(1.20,-.213)])
 clock_bezel(bronze, [Vector2(1.20,.213),Vector2(1.19,.222),Vector2(1.12,.217),Vector2(1.08,.197)])
 for side: float in [1.0,-1.0]:
  var normal := Vector3.BACK * side
  var basis := Basis(Vector3.UP.cross(normal), Vector3.UP, normal)
  for tick in range(60):
   var angle := TAU * float(tick) / 60.0
   var radius := 1.009 if tick%5==0 else 1.045
   var radial := Vector3(sin(angle),cos(angle),0.0)
   var tick_basis := basis * Basis(Vector3.BACK,-angle)
   var at := face_center + normal*.177 + basis*(radial*radius)
   var size := Vector3(.020,.034,.014)
   if tick%5==0:
    size = Vector3(.031,.083,.018)
   panel(at,size,lettering if tick%5==0 else bronze,tick_basis)
  var numerals := ["12","3","6","9"]
  for quarter in range(4):
   var angle := TAU*float(quarter)/4.0
   var radial := Vector3(sin(angle),cos(angle),0.0)
   wall_label(face_center+normal*.189+basis*(radial*.80),normal,numerals[quarter],.185,IVORY)
  wall_label(face_center+normal*.190+Vector3.UP*.40,normal,"MERIDIAN",.104,IVORY)
  wall_label(CLOCK+Vector3.UP*1.016+normal*.081,normal,"時の広場",.141,IVORY)
  wall_label(CLOCK+Vector3.UP*.872+normal*.082,normal,"TIME PLAZA  •  B 1F",.073,IVORY)
  clock_hand(face_center+normal*.207,normal,.63,.067,.024,lettering)
  clock_hand(face_center+normal*.244,normal,.94,.041,.021,bronze)
  round_shape(face_center+normal*.27,.078,.036,bronze,face_rotation)
  var wash := Vector3(CLOCK.x,4.73,CLOCK.z+side*1.72)
  round_shape(wash+Vector3.UP*.24,.022,.37,mantel)
  round_shape(wash+Vector3.UP*.065,.090,.20,mantel)
  task_light(wash,face_center+normal*.15,Color("#ffe1bc"),.68,4.4)
 shown_minute = -1
 update_clock()


func sweep(a: Vector3,b: Vector3,c: Vector3,d: Vector3) -> PackedVector3Array:
 var points := PackedVector3Array()
 for i in range(33):
  points.append(a.bezier_interpolate(b,c,d,float(i)/32.0))
 return points


func route_materials() -> void:
 var aggregate := stone("Warm pale aggregate",Color("#a69c8d"))
 var band := stone("Mineral green mortar",Color("#596e67"))
 var trim := finish("Satin mosaic brass", Color("#b79b73"), .63, .28)
 # Edge of the retail parade and wide branch toward plaza, flush with the existing 0.04m finish.
 for point_z: float in [28.81,29.07]:
  curve_strip(sweep(Vector3(-25.1,FLOOR,point_z+.5),Vector3(-15.2,FLOOR,point_z-.8),
   Vector3(-8.9,FLOOR,point_z-.9),Vector3(1.7,FLOOR,point_z+.16)),.13,band)
 var feeder := sweep(Vector3(-5.83,FLOOR+.001,28.70),Vector3(-5.0,FLOOR+.001,24.15),
  Vector3(-8.04,FLOOR+.001,21.3),Vector3(-6.48,FLOOR+.001,17.1))
 curve_strip(feeder,.54,aggregate)
 var braze := PackedVector3Array()
 for point: Vector3 in feeder:
  braze.append(point + Vector3(-.26,.002,0.0))
 curve_strip(braze,.031,trim)

 # Department thresholds are differentiated inside the tenant line only.
 curve_strip(PackedVector3Array([Vector3(-3.56,.011,33.15),Vector3(-3.56,.011,34.19),Vector3(-5.18,.011,35.05)]),.38,
  stone("Fernell espresso aggregate", Color("#98765f")))
 curve_strip(sweep(Vector3(-20.44,.011,33.30),Vector3(-20.44,.011,34.42),Vector3(-21.14,.011,36.40),
  Vector3(-22.14,.011,39.71)),.47,stone("Ovelis moss aggregate", Color("#627166")))


func graphic(path: String, point: Vector3, size: Vector2, orientation: Basis) -> void:
 var print_mat := StandardMaterial3D.new()
 print_mat.albedo_texture = load(path)
 print_mat.roughness = .79
 print_mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
 var printed := MeshInstance3D.new()
 var face := QuadMesh.new()
 face.size = size
 printed.mesh = face
 printed.material_override = print_mat
 printed.position = point
 printed.basis = orientation
 installation.add_child(printed)


func task_light(point: Vector3, aim: Vector3, tint: Color, power: float, extent: float) -> void:
 var spot := SpotLight3D.new()
 spot.position = point
 spot.light_color = tint
 spot.light_energy = power
 spot.spot_range = extent
 spot.spot_angle = 39.0
 spot.shadow_enabled = false
 spot.distance_fade_enabled = true
 spot.distance_fade_begin = 25.0
 spot.distance_fade_length = 9.0
 installation.add_child(spot)
 spot.look_at(aim,Vector3.FORWARD if absf((aim-point).normalized().y)>.95 else Vector3.UP)


func lanterns() -> void:
 # Ceiling blade material stops under the original solid soffit and follows its public edge.
 var oak := timber()
 var bronze := finish("Blackened bronze", Color("#50382e"), .55, .55)
 var milk := finish("Warm opal diffuser", Color("#ffe7c7"), .48, 0.0, .85)
 for row: float in [-.31,.31]:
  var path := sweep(Vector3(-23.8,4.79,28.08+row), Vector3(-16.6,4.79,25.69+row),
   Vector3(-10.65,4.79,26.32+row), Vector3(-6.15,4.79,27.47+row))
  for i in range(0,path.size()-1):
   var a := path[i]
   var b := path[i+1]
   var axis := (b-a).normalized()
   var facing := Basis(Vector3.UP,atan2(axis.x,axis.z))
   var midpoint := (a+b)*.5
   panel(midpoint,Vector3(.14,.19,a.distance_to(b)+.009),oak,facing)
   panel(midpoint-Vector3.UP*.096,Vector3(.033,.010,a.distance_to(b)+.006),milk,facing)
  for i in [0,8,16,24,32]:
   var mount := path[i]
   panel(mount+Vector3.UP*.22,Vector3(.036,.30,.041),bronze)


func cafe() -> void:
 var oak := timber()
 var copper := finish("Fernell oxidized copper", Color("#98735a"), .46, .43)
 var olive := finish("Fernell olive trim", Color("#34433a"), .62)
 var glow := finish("Fernell lamp opal", Color("#ffd299"), .45, 0.0, .7)
 # The menu is mounted against the solid diagonal interior wall, leaving glazing open.
 var inward := Vector3(-.631,0.0,-.776).normalized()
 var menu_basis := Basis(Vector3.UP.cross(inward),Vector3.UP,inward)
 var copy := Vector3(-5.47,2.03,36.404) + inward*.176
 panel(copy,Vector3(2.88,1.86,.094),oak,menu_basis)
 panel(copy+inward*.055,Vector3(2.76,1.75,.038),olive,menu_basis)
 graphic("res://assets/v35/b_gallery/fernell-menu.png",copy+inward*.077,Vector2(2.60,1.625),menu_basis)
 panel(copy+Vector3.UP*.96+inward*.120,Vector3(2.78,.038,.127),copper,menu_basis)
 panel(copy+Vector3.UP*.933+inward*.15,Vector3(2.58,.017,.068),glow,menu_basis)
 task_light(copy+Vector3.UP*.98+inward*.59,copy,Color("#ffdbad"),.58,3.1)
 wall_label(copy+Vector3.UP*1.224+inward*.022,inward,"FERNELL COFFEE",.211,IVORY)

 # The seasonal graphic is attached directly to an existing public-side glazing bay.
 var facade := Vector3(-15.79,2.13,32.961)
 var street := Basis(Vector3.UP,PI)
 panel(facade,Vector3(1.94,1.19,.052),olive,street)
 graphic("res://assets/v35/b_gallery/fernell-poster.png",facade-Vector3.BACK*.029,Vector2(1.86,1.116),street)
 espresso_station(Vector3(-18.928,0.006,36.81),oak,olive)
 banquette(Vector3(-13.32,0.0,39.875),oak)


func espresso_station(at: Vector3, oak: Material, olive: Material) -> void:
 # Coffee equipment has a dedicated counter against the short rear wall behind the inherited till.
 var orientation := Basis(Vector3.UP,PI*.5)
 var espresso := finish("Cast enamel espresso housing",Color("#744736"),.38,.19)
 var granite := stone("Black mineral worktop",Color("#716965"))
 var black := finish("Fernell charcoal metal",Color("#332b26"),.48,.47)
 var brass := finish("Fernell boiler brass",Color("#c29a63"),.39,.51)
 var steel := finish("Fernell brushed steel",Color("#c3b9a6"),.42,.37)
 var cup := finish("Fernell cups",Color("#e1c9a2"),.42)
 var grounds := finish("Fernell coffee beans",Color("#5b3626"),.60)
 panel(at+Vector3.UP*.417,Vector3(1.96,.825,.365),olive,orientation)
 panel(at+Vector3.UP*.845,Vector3(2.03,.042,.405),granite,orientation)
 panel(at+Vector3.UP*.05,Vector3(1.90,.095,.382),black,orientation)
 for slat in range(22):
  var rib := at + orientation*Vector3((float(slat)-10.5)*.086,.354,.192)
  panel(rib,Vector3(.027,.48,.020),oak,orientation)
 var pane := at+orientation*Vector3(0.,1.63,-.193)
 panel(pane,Vector3(2.04,1.25,.046),olive,orientation)
 for level: float in [1.67,2.21]:
  panel(at+orientation*Vector3(0.,level,-.082),Vector3(1.90,.035,.24),oak,orientation)
  panel(at+orientation*Vector3(0.,level-.029,-.047),Vector3(1.75,.010,.035),brass,orientation)
 for x: float in [-.78,-.52,-.26,.0,.26,.52,.78]:
  var caps := at+orientation*Vector3(x,1.703,-.058)
  vessel(caps,.067,[Vector2(.64,0),Vector2(.78,.023),Vector2(1.,.108),Vector2(.93,.118),Vector2(.76,.113),Vector2(.56,.045)],cup)
 for x: float in [-.78,-.52,-.26,.0,.26,.52,.78]:
  var jar := at+orientation*Vector3(x,2.231,-.074)
  round_shape(jar+Vector3.UP*.071,.070,.137,grounds)
  round_shape(jar+Vector3.UP*.148,.071,.025,brass)
 var bar := at+orientation*Vector3(-.22,.862,.007)
 panel(bar+orientation*Vector3(0.,.026,0),Vector3(1.02,.05,.342),steel,orientation)
 panel(bar+orientation*Vector3(0.,.192,-.127),Vector3(1.00,.30,.095),espresso,orientation)
 panel(bar+orientation*Vector3(0.,.315,.007),Vector3(1.02,.125,.347),espresso,orientation)
 panel(bar+orientation*Vector3(0.,.293,.190),Vector3(.95,.049,.038),steel,orientation)
 for point: float in [-.30,0.,.30]:
  round_shape(bar+orientation*Vector3(point,.227,.079),.059,.041,steel)
  panel(bar+orientation*Vector3(point,.211,.155),Vector3(.037,.031,.127),black,orientation)
  vessel(bar+orientation*Vector3(point,.052,.088),.035,
   [Vector2(.60,0),Vector2(.83,.013),Vector2(1.,.061),Vector2(.75,.064),Vector2(.52,.013)],cup)
  round_shape(bar+orientation*Vector3(point,.310,.218),.014,.012,brass,orientation*Basis(Vector3.RIGHT,PI*.5))
 for point: float in [-.29,.02,.29]:
  round_shape(bar+orientation*Vector3(point,.386,.01),.066,.018,cup)
 var mill := at+orientation*Vector3(.69,1.006,.024)
 round_shape(mill,.103,.293,black)
 round_shape(mill+Vector3.UP*.23,.073,.18,grounds)
 round_shape(mill+Vector3.UP*.324,.080,.026,brass)
 task_light(at+orientation*Vector3(0.,2.54,.29),at+orientation*Vector3(-.2,1.04,.12),Color("#ffdbad"),.80,2.9)
 var body := StaticBody3D.new()
 body.name = "FernellCounter"
 body.collision_layer = CLOCK_TRIANGLE_COLLISION
 body.collision_mask = 0
 var shape := CollisionShape3D.new()
 var box := BoxShape3D.new()
 box.size = Vector3(.39,.865,2.00)
 shape.shape = box
 shape.position = at+Vector3.UP*.431
 body.add_child(shape)
 installation.add_child(body)


func box_collider(host: StaticBody3D, center: Vector3, size: Vector3, orientation: Basis) -> void:
 var shape := CollisionShape3D.new()
 var geom := BoxShape3D.new()
 geom.size = size
 shape.shape = geom
 shape.transform = Transform3D(orientation, center)
 host.add_child(shape)


func banquette(at: Vector3, oak: Material) -> void:
 # This pocket is offset from the door-to-till line and reuses the rear sales wall.
 var inward := Vector3(.259,0.0,-.966).normalized()
 var basis := Basis(Vector3.UP.cross(inward),Vector3.UP,inward)
 var seat := finish("Rust woven upholstery",Color("#915744"),.86)
 var back := finish("Woven olive upholstery",Color("#575d49"),.82)
 var table := stone("Cafe honed quartz composite",Color("#c4a588"))
 var foot := finish("Cafe blackened pedestal",Color("#4c453c"),.51,.34)
 var table_seat_graphic := finish("Fernell tabletop ceramic",Color("#ddd1b9"),.44)
 var clay := finish("Fernell coffee enamel",Color("#6d4a3a"),.40)
 var support := StaticBody3D.new()
 support.name = "FernellSeating"
 support.collision_layer = CLOCK_TRIANGLE_COLLISION
 support.collision_mask = 0
 var base_center := at+basis*Vector3(0.0,.231,.503)
 panel(base_center,Vector3(3.08,.462,.57),oak,basis)
 panel(at+basis*Vector3(0.0,.61,.311),Vector3(3.08,.85,.178),oak,basis)
 panel(at+basis*Vector3(0.0,.924,.386),Vector3(2.94,.058,.067),oak,basis)
 box_collider(support,base_center,Vector3(3.08,.58,.60),basis)
 box_collider(support,at+basis*Vector3(0.0,.62,.35),Vector3(3.08,.86,.19),basis)
 for offset: float in [-.76,.76]:
  panel(at+basis*Vector3(offset,.517,.542),Vector3(1.47,.120,.56),seat,basis)
  panel(at+basis*Vector3(offset,.761,.438),Vector3(1.47,.31,.121),back,basis*Basis(Vector3.RIGHT,-.10))
  var top := at+basis*Vector3(offset,.742,1.285)
  round_shape(top-Vector3.UP*.714,.252,.029,foot)
  round_shape(top-Vector3.UP*.380,.059,.678,foot)
  round_shape(top,.386,.049,table)
  var edge := CollisionShape3D.new()
  var cylinder := CylinderShape3D.new()
  cylinder.height = .080
  cylinder.radius = .384
  edge.shape = cylinder
  edge.position = top
  support.add_child(edge)
  var plate := top+basis*Vector3(.05,.033,-.077)
  round_shape(plate,.105,.012,table_seat_graphic)
  vessel(plate+Vector3.UP*.007,.061,
   [Vector2(.67,0.),Vector2(.79,.019),Vector2(1.,.105),Vector2(.91,.109),Vector2(.76,.101),Vector2(.70,.033)],clay)
  panel(top+basis*Vector3(-.11,.032,.071),Vector3(.13,.008,.098),table_seat_graphic,basis*Basis(Vector3.UP,.38))
 installation.add_child(support)


func vessel(center: Vector3, radius: float, profile: Array[Vector2], surface: Material) -> void:
 var tool := mesh_batch(surface)
 for r in range(profile.size()-1):
  var a := profile[r]
  var b := profile[r+1]
  for i in range(32):
   var theta := TAU * float(i) / 32.0
   var next := TAU * float(i+1) / 32.0
   var first := Vector3(cos(theta),0.0,sin(theta))
   var second := Vector3(cos(next),0.0,sin(next))
   var normal := ((first+second)*.5 * (b.y-a.y) + Vector3.UP * radius*(a.x-b.x)).normalized()
   append_quad(tool,[
    center+first*(a.x*radius)+Vector3.UP*a.y,
    center+first*(b.x*radius)+Vector3.UP*b.y,
    center+second*(b.x*radius)+Vector3.UP*b.y,
    center+second*(a.x*radius)+Vector3.UP*a.y
   ], normal, [Vector2(0,0),Vector2(0,1),Vector2(1,1),Vector2(1,0)])


func home() -> void:
 var oak := timber()
 var clay := finish("Hand glazed clay", Color("#a05c43"), .47)
 var ink := finish("Ovelis fir green", Color("#3e4e47"), .51)
 var ivory := finish("Ovelis porcelain", Color("#e9dccb"), .35)
 var dark := finish("Ovelis basalt ware",Color("#3a3634"),.47)
 var glow := finish("Ovelis ivory case light", Color("#ffe6bf"), .54, 0., .66)
 var toward := Vector3.LEFT
 var basis := Basis(Vector3.UP.cross(toward), Vector3.UP, toward)
 var center := Vector3(-19.381,2.13,36.91)
 panel(center+Vector3.RIGHT*.035,Vector3(3.95,2.10,.095),oak,basis)
 panel(center+Vector3.LEFT*.023,Vector3(3.81,1.96,.051),ink,basis)
 graphic("res://assets/v35/b_gallery/ovelis-materials.png",center+Vector3(-.056,.049,-.65),Vector2(2.10,1.76),basis)
 panel(center+Vector3(-.18,-.43,1.09),Vector3(1.12,.043,.341),oak,basis)
 panel(center+Vector3(-.18,.67,1.09),Vector3(1.12,.053,.341),oak,basis)
 panel(center+Vector3(-.204,.64,1.09),Vector3(.97,.012,.162),glow,basis)
 vessel(center+Vector3(-.185,-.410,.81),.134,
  [Vector2(.61,0.0),Vector2(.74,.04),Vector2(.95,.095),Vector2(1.,.19),Vector2(.76,.25),Vector2(.43,.30),Vector2(.40,.44),Vector2(.47,.46),Vector2(.32,.456),Vector2(.27,.425),Vector2(.25,.29)],clay)
 vessel(center+Vector3(-.185,-.409,1.18),.126,
  [Vector2(.58,0.0),Vector2(.75,.021),Vector2(.92,.07),Vector2(1.,.16),Vector2(.96,.189),Vector2(.85,.198),Vector2(.74,.174),Vector2(.59,.078),Vector2(.16,.053)],ivory)
 vessel(center+Vector3(-.185,-.409,1.49),.123,
  [Vector2(.49,0.0),Vector2(.62,.051),Vector2(.78,.119),Vector2(.89,.257),Vector2(.64,.317),Vector2(.65,.39),Vector2(.71,.395),Vector2(.53,.397),Vector2(.51,.35)],dark)
 task_light(center+Vector3(-.70,.63,1.10),center+Vector3(-.1,-.12,1.10),Color("#ffdfb7"),.60,3.0)
 wall_label(center+Vector3(-.053,.89,.92),toward,"器 と 素 材",.145,IVORY)


func build() -> void:
 installation = Node3D.new()
 installation.name = "Time_Plaza_and_Parade"
 add_child(installation)
 route_materials()
 build_station()
 lanterns()
 cafe()
 home()
 for tool: SurfaceTool in batches.values():
  var fragment := MeshInstance3D.new()
  fragment.mesh = tool.commit()
  installation.add_child(fragment)
 batches.clear()
