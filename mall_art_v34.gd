extends Node3D

# The two anchor stores have separate finish, lighting and legibility treatments.
# The inherited sales nodes still own goods, fixture collisions, and checkout interaction.
var game: Node3D
var resident: Dictionary = {}
var centers := {
 "Rivora": Vector3(439.0,0.,-8.3),
 "Suvel": Vector3(474.5,0.,-6.4),
 "Terrune": Vector3(184.1,0.,-39.4),
 "Courtyard": Vector3(-126.0,0.,-360.0),
}
var materials: Dictionary = {}
var batch: Dictionary = {}
var checked_time := 0.0

func setup(scene: Node3D) -> void:
 game = scene
 name = "V34_Mall_Art"
 checked_time = .25

func _process(delta: float) -> void:
 checked_time += delta
 if checked_time >= .25:
  checked_time = 0.
  update_near()

func update_near() -> void:
 var player: Node3D = game.get("player")
 if not is_instance_valid(player):
  return
 for area: String in centers:
  var location: Vector3 = centers[area]
  var point := player.global_position
  var distance := Vector2(point.x-location.x,point.z-location.z).length()
  if resident.has(area):
   var retire_radius := 92. if area == "Courtyard" else 78.
   if distance > retire_radius or absf(point.y) > 4.9:
    var node: Node3D = resident[area]
    resident.erase(area)
    remove_child(node)
    node.queue_free()
   continue
  var exhibit_radius := 80. if area == "Courtyard" else 59.
  if distance < exhibit_radius and absf(point.y) < 2.9:
   build_area(area, location)

func material(key: String, tint: Color, roughness: float = .64, metal: float = 0., emit: float = 0.) -> StandardMaterial3D:
 if materials.has(key):
  return materials[key]
 var result := StandardMaterial3D.new()
 result.albedo_color = tint
 result.roughness = roughness
 result.metallic = metal
 if emit > 0.:
  result.emission_enabled = true
  result.emission = tint
  result.emission_energy_multiplier = emit
 materials[key] = result
 return result

func box(location: Vector3, size: Vector3, yaw: float, surface: Material) -> void:
 var geometry := BoxMesh.new()
 geometry.size = size
 if not batch.has(surface):
  var tool := SurfaceTool.new()
  tool.begin(Mesh.PRIMITIVE_TRIANGLES)
  tool.set_material(surface)
  batch[surface] = tool
 var destination: SurfaceTool = batch[surface]
 destination.append_from(geometry, 0, Transform3D(Basis(Vector3.UP,yaw),location))

func bake_finish(root: Node3D) -> void:
 for tool: SurfaceTool in batch.values():
  var panel := MeshInstance3D.new()
  panel.mesh = tool.commit()
  panel.visibility_range_end = 77.
  panel.visibility_range_end_margin = 8.
  # Existing structural slab supplies shadowing; decorative solids cast normal shadows.
  root.add_child(panel)
 batch.clear()

func text(root: Node3D, at: Vector3, facing: Vector3, copy: String, height: float, tint: Color) -> void:
 var label := Label3D.new()
 label.font = game.get("font")
 label.font_size = 52
 label.pixel_size = height/52.
 label.modulate = tint
 label.outline_size = 0
 label.text = copy
 label.position = at
 label.basis = Basis(Vector3.UP.cross(facing),Vector3.UP,facing)
 label.double_sided = false
 label.visibility_range_end = 46.
 root.add_child(label)

func light(root: Node3D, at: Vector3, tint: Color, extent: float, power: float) -> void:
 var lamp := OmniLight3D.new()
 lamp.position = at
 lamp.light_color = tint
 lamp.omni_range = extent
 lamp.light_energy = power
 lamp.shadow_enabled = false
 lamp.distance_fade_enabled = true
 lamp.distance_fade_begin = 23.
 lamp.distance_fade_length = 8.
 root.add_child(lamp)

func hang_board(root: Node3D, at: Vector3, inward: Vector3, width: float, label: String, sublabel: String,
  surface: Material, lettering: Color, mount_y: float = 5.145) -> void:
 var side := Vector3.UP.cross(inward)
 var yaw := atan2(inward.x, inward.z)
 box(at,Vector3(width,.55,.07),yaw,surface)
 # Hanger top meets the collision-measured structural underside. All scenery remains >=2.3m.
 var bottom := at.y+.25
 for sign: float in [-1.,1.]:
  var top := at + side * (width*.33*sign)
  top.y = (bottom+mount_y)*.5
  box(top,Vector3(.016,mount_y-bottom,.016),yaw,surface)
 text(root,at+inward*.039+Vector3.UP*.085,inward,label,.225,lettering)
 text(root,at+inward*.040-Vector3.UP*.128,inward,sublabel,.098,lettering)

func mark_segment(a: Vector3,b: Vector3,width: float,surface: Material) -> void:
 var dir := (b-a).normalized()
 box((a+b)*.5,Vector3(width,.002,a.distance_to(b)),atan2(dir.x,dir.z),surface)

func make_rivora(root: Node3D, origin: Vector3) -> void:
 var timber := material("Rivora oak", Color("#a57142"))
 var deep_wood := material("Rivora wood edge", Color("#725034"))
 var green := material("Rivora enamel",Color("#283d2d"))
 var brass := material("Rivora brass inlay",Color("#bf894a"),.5,.2)
 var lit := material("Rivora warm diffuser",Color("#ffddaa"),.5,0.,.7)
 var aisle := Vector3(-.988,0.,-.155).normalized()
 var side := Vector3.UP.cross(aisle)
 var up := Vector3.UP
 var yaw := atan2(aisle.x,aisle.z)
 # Long main aisle beneath a retail canopy with three warm, open joist modules.
 for section: float in [-4.,3.,10.]:
  var center := origin + aisle*section + up*4.62
  for span: float in [-2.25,2.25]:
   box(center+side*span, Vector3(.13,.21,5.45),yaw,deep_wood)
   for end: float in [-2.35,2.35]:
    box(center+side*span+aisle*end+up*.28,Vector3(.11,.49,.13),yaw,deep_wood)
  for rib: int in range(8):
   var line := center+aisle*((float(rib)-3.5)*.65)
   box(line,Vector3(4.55,.16,.088),yaw,timber)
   if rib in [1,6]:
    box(line-up*.085,Vector3(4.23,.012,.086),yaw,lit)
  light(root,center-up*.72,Color("#ffe7cb"),8.4,.42)
 hang_board(root,Vector3(446.4,3.08,-6.40),-aisle,3.35,"リヴォラ マーケット","RIVORA STUDIO  /  フード・デリ",green,Color("#fff3d3"))
 hang_board(root,Vector3(437.7,3.12,-7.82),-aisle,2.55,"季節の青果","SEASONAL  /  01",green,Color("#fff3d3"))
 hang_board(root,Vector3(428.3,3.12,-9.17),-aisle,2.65,"ベーカリー・デリ","BAKERY AND DELI  /  02",green,Color("#fff3d3"))
 # Flush brass runners lie beyond the actual entry, clearly leaving the central aisle open.
 for offset: float in [-.87,.87]:
  var low := Vector3(447.9,.012,-6.16)+side*offset
  var high := Vector3(426.6,.012,-9.52)+side*offset
  mark_segment(low, high,.022,brass)

func make_suvel(root: Node3D, origin: Vector3) -> void:
 var ink := material("Suvel blued alloy",Color("#223c52"),.55,.28)
 var silver := material("Suvel recycled aluminium",Color("#95a6a9"),.43,.46)
 var frost := material("Suvel frosted light",Color("#d4eeef"),.4,0.,.8)
 var edge := material("Suvel slate floor insert",Color("#61768d"),.65)
 var aisle := Vector3(.9996,0.,.029).normalized()
 var side := Vector3.UP.cross(aisle)
 var up := Vector3.UP
 var yaw := atan2(aisle.x,aisle.z)
 # Floating lines are supported on short posts into the slab rather than copied from the timber shop.
 for segment: float in [-7.5,0.,7.5,15.]:
  var center := origin+aisle*segment+up*4.64
  for i: float in [-1.55,1.55]:
   box(center+side*i,Vector3(.14,.16,6.34),yaw,ink)
   box(center+side*i-up*.087,Vector3(.11,.013,6.20),yaw,frost)
   for end: float in [-2.9,2.9]:
    box(center+side*i+aisle*end+up*.295,Vector3(.11,.46,.11),yaw,silver)
  box(center+aisle*1.9+up*.015,Vector3(3.1,.12,.13),yaw,silver)
  light(root,center-up*.68,Color("#d4eaff"),8.,.38)
 hang_board(root,Vector3(464.7,3.08,-6.5),-aisle,3.5,"スヴェル 体験ギャラリー","SUVEL STUDIO  /  TECHNOLOGY GALLERY",ink,Color("#f2fafa"))
 hang_board(root,Vector3(475.8,3.12,-6.09),-aisle,2.8,"写真と音を試す","IMAGING  /  LISTENING",ink,Color("#f2fafa"))
 for offset: float in [-.85,.85]:
  var low := Vector3(463.5,.012,-6.48)+side*offset
  var high := Vector3(494.8,.012,-5.59)+side*offset
  mark_segment(low,high,.038,edge)

func make_terrune(root: Node3D) -> void:
 var walnut := material("Terrune smoked wood",Color("#644634"))
 var forest := material("Terrune glazed green",Color("#354941"),.49)
 var amber := material("Terrune warm light",Color("#f2cd96"),.52,0.,.7)
 var gold := material("Terrune bronze trace",Color("#b99a75"),.48,.37)
 var glaze := material("Terrune terrazzo ribbon",Color("#7d8578"),.72)
 # Preserve the slanted approach and turn the threshold into the first chapter of the store.
 # Centerline derives from physically verified inherited consumer route, not the alternate (unbuilt) opening.
 # A separate brand plate meets the existing doorway header whose face was
 # sampled at +.325m along the shopfront normal, Y=3.50m.
 var exterior := Vector3(-.667262,0.,-.744823).normalized()
 var plate := Vector3(186.04334,3.50,-45.49479) + exterior*.378
 var plate_yaw := atan2(exterior.x, exterior.z)
 # Wide walnut surround re-faces the original category plaque. The trade
 # name stays centred on the walking opening beneath it.
 var surround := plate - Vector3.UP.cross(exterior)*.175 - exterior*.030
 box(surround,Vector3(3.24,.58,.071),plate_yaw,walnut)
 box(plate,Vector3(2.10,.37,.106),plate_yaw,forest)
 box(plate+exterior*.055-Vector3.UP*.16,Vector3(2.05,.014,.008),plate_yaw,gold)
 text(root,plate+exterior*.057+Vector3.UP*.038,exterior,"TERRUNE TOKYO",.154,Color("#f8eaca"))
 text(root,plate+exterior*.058-Vector3.UP*.098,exterior,"暮らしの道具",.080,Color("#f8eaca"))
 var p0 := Vector3(186.04,.012,-45.49)
 var p1 := Vector3(186.55,.012,-45.30)
 var p2 := Vector3(186.88,.012,-44.93)
 var p3 := Vector3(186.11,.012,-42.90)
 var p4 := Vector3(183.98,.012,-32.77)
 for pair: Array in [[p0,p1],[p1,p2],[p2,p3],[p3,p4]]:
  mark_segment(pair[0],pair[1],.42,glaze)
 var inward := Vector3(-.203,0,.979).normalized()
 var front := -inward
 hang_board(root,Vector3(186.40,2.58,-43.82),front,1.50,"テラルーン","TERRUNE TOKYO",forest,Color("#f6dfb9"))
 hang_board(root,Vector3(184.75,2.70,-36.3),front,2.0,"器・暮らしの道具","TABLE AND HOME",forest,Color("#f6dfb9"))
 for position: Vector3 in [Vector3(186.10,4.31,-42.9),Vector3(185.14,4.31,-38.4),Vector3(184.12,4.31,-33.55)]:
  var yaw := atan2(inward.x,inward.z)
  box(position,Vector3(.98,.17,.23),yaw,walnut)
  box(position-Vector3.UP*.09,Vector3(.91,.012,.15),yaw,amber)
  box(position+Vector3.UP*.44,Vector3(.025,.80,.025),yaw,gold)
  light(root,position-Vector3.UP*.69,Color("#ffe7cb"),5.2,.44)

func build_area(area: String, origin: Vector3) -> void:
 var root := Node3D.new()
 root.name = area
 add_child(root)
 resident[area] = root
 match area:
  "Rivora":
   make_rivora(root,origin)
  "Suvel":
   make_suvel(root,origin)
  "Terrune":
   make_terrune(root)
  "Courtyard":
   if ResourceLoader.exists("res://c_courtyard_v34.gd"):
    var courtyard: Node3D = load("res://c_courtyard_v34.gd").new()
    root.add_child(courtyard)
    courtyard.call("setup",game)
 bake_finish(root)
