extends Node3D
## Mechanical assembly and tread transport for the authored escalator definitions.
const ES_MESH = preload("res://es_mechanical_mesh_v34.gd")
var shared_machines: Dictionary = {}
var bank_ids: Dictionary = {}
var comb_material: Material
var stainless_material: Material
var traction_material: Material
var laminated_glass: StandardMaterial3D
var sign_panel_material: StandardMaterial3D
var label_font: Font
var directional_panels: Array[Dictionary] = []
var exit_symbol: ArrayMesh

var banks:Array=[]
var definitions:Array=[]
var shared_tread:Mesh
var simulation_time:float=0.
var nearby_check:float=0.
var clock:float=0.0
var paused:bool=false
const ES_MOTION=preload("res://escalator_motion_v33.gd")
var speed:float=ES_MOTION.SURFACE_SPEED
var material_set:Dictionary
var samples:Array=[]
var culled_updates:int=0
var visible_updates:int=0
var next_far_update:float=0.0
func v3(a:Array)->Vector3:return Vector3(a[0],a[1],a[2])
func setup(manifest: Dictionary, mats: Dictionary) -> void:
 material_set = mats
 definitions = manifest.escalators
 label_font = load("res://assets/NotoSansCJKjp-Regular.otf")
 traction_material = ES_MESH.material(Color("#283338"), .45, .58)
 stainless_material = ES_MESH.material(Color("#aeb7b7"), .68, .36)
 comb_material = ES_MESH.material(Color("#b88c38"), .51, .47)
 sign_panel_material = StandardMaterial3D.new()
 sign_panel_material.albedo_color = Color("#15242a")
 sign_panel_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
 laminated_glass = ES_MESH.material(Color(.66,.83,.81,.31), .015, .15)
 laminated_glass.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
 shared_tread = ES_MESH.tread(traction_material, mats.yellow)
 var camera := get_viewport().get_camera_3d()
 ensure_near(camera.global_position if camera != null else Vector3.ZERO)

func machine_resources(rise: float, run: float) -> Dictionary:
 var key := Vector2(rise, run)
 if not shared_machines.has(key):
  shared_machines[key] = {
   "rail": ES_MESH.rail(rise, run),
   "case": ES_MESH.machine_case(rise, run, stainless_material, material_set.metal, comb_material, laminated_glass),
   "collider": ES_MESH.housing_collision(rise, run),
  }
 return shared_machines[key]

func create_bank(data: Dictionary) -> void:
 var rise := float(data.rise_m)
 var run := float(data.run_m)
 var centre := v3(data.c)
 centre.y = float(data.get("low_y", centre.y))
 var axis := Vector3(data.u[0], 0., data.u[1]).normalized()
 # Local +X is the left flank when looking from the low landing toward the upper level.
 var lateral := Vector3(axis.z, 0., -axis.x)
 var yaw := Basis(lateral, Vector3.UP, axis)
 var direction := 1.0 if data.direction == "UP" else -1.0
 var bank: Dictionary = {"id": data.id, "direction": direction, "c": centre, "u": axis, "x": lateral, "rise": rise, "run": run}
 var end := run * .5 + 1.12
 var half := run * .5
 var return_radius := .30
 var points: PackedVector3Array = [Vector3(0., 0., -end), Vector3(0., 0., -half), Vector3(0., rise, half), Vector3(0., rise, end)]
 var angles: PackedFloat32Array = [0., 0., 0., 0.]
 # The flat/sloping track knots are exact at the support mesh's transition points.
 for i: int in range(1, 19):
  var a := PI * float(i) / 18
  points.append(Vector3(0., rise - return_radius + cos(a) * return_radius, end + sin(a) * return_radius))
  angles.append(a)
 points.append(Vector3(0., rise - 2. * return_radius, half));angles.append(PI)
 points.append(Vector3(0., -2. * return_radius, -half));angles.append(PI)
 points.append(Vector3(0., -2. * return_radius, -end));angles.append(PI)
 for i: int in range(1, 19):
  var a := PI * float(i) / 18
  points.append(Vector3(0., -return_radius - cos(a) * return_radius, -end - sin(a) * return_radius))
  angles.append(PI + a)
 var distances: PackedFloat32Array = [0.]
 for i: int in range(1, points.size()):
  distances.append(distances[i - 1] + points[i - 1].distance_to(points[i]))
 var length := float(distances[-1])
 var count := ceili(length / .4)
 bank.merge({"points": points, "distances": distances, "angles": angles, "top_length": distances[3], "top_end": 3, "length": length, "count": count, "pitch": length / count})
 var assembly := Node3D.new()
 assembly.name = str(data.id) + "_Assembly"
 assembly.transform = Transform3D(yaw, centre)
 add_child(assembly)
 var local_machine := machine_resources(rise, run)
 var body := StaticBody3D.new()
 body.name = str(data.id) + "_enclosed_truss_and_landing_pit"
 assembly.add_child(body)
 var shape := CollisionShape3D.new()
 shape.shape = local_machine.collider
 body.add_child(shape)
 var casing := MeshInstance3D.new()
 casing.mesh = local_machine.case
 casing.visibility_range_end = 125.
 casing.visibility_range_end_margin = 15.
 body.add_child(casing)
 var rail := MeshInstance3D.new()
 rail.name = str(data.id) + "_continuous_handrail"
 rail.mesh = local_machine.rail
 var rubber := ShaderMaterial.new()
 rubber.shader = preload("res://rubber.gdshader")
 rail.material_override = rubber
 rail.visibility_range_end = 125.
 rail.visibility_range_end_margin = 15.
 assembly.add_child(rail)
 var treads := MultiMeshInstance3D.new()
 treads.name = str(data.id) + "_moving_treads"
 treads.physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF
 treads.visibility_range_end = 125.
 treads.visibility_range_end_margin = 15.
 var multimesh := MultiMesh.new()
 multimesh.transform_format = MultiMesh.TRANSFORM_3D
 multimesh.mesh = shared_tread
 multimesh.instance_count = count
 multimesh.custom_aabb = AABB(Vector3(-.8, -.9, -end - .63), Vector3(1.6, rise + 1.2, (end + .63) * 2.))
 treads.multimesh = multimesh
 assembly.add_child(treads)
 bank.merge({"rubber": rubber, "multimesh": multimesh, "next_update": 0., "assembly": assembly})
 for side: float in [-1., 1.]:
  mount_direction_panel(assembly, bank, side)
 banks.append(bank)
 bank_ids[data.id] = true
 update_bank(bank, clock)

## The white stripe has a separate depth plane from the red disc. These are raised
## printed faces, shared by all exit markers, with no font fallback at distance.
func no_entry_symbol() -> ArrayMesh:
 if exit_symbol != null:
  return exit_symbol
 var brush := SurfaceTool.new()
 brush.begin(Mesh.PRIMITIVE_TRIANGLES)
 var ink := StandardMaterial3D.new()
 ink.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
 ink.vertex_color_use_as_albedo = true
 ink.vertex_color_is_srgb = true
 ink.cull_mode = BaseMaterial3D.CULL_DISABLED
 brush.set_material(ink)
 brush.set_color(Color("#dd302d"))
 var radius := .081
 for i: int in 32:
  var a := TAU * i / 32.
  var b := TAU * (i + 1) / 32.
  brush.add_vertex(Vector3.ZERO)
  brush.add_vertex(Vector3(cos(b), sin(b), 0.) * radius)
  brush.add_vertex(Vector3(cos(a), sin(a), 0.) * radius)
 brush.set_color(Color("#fff9eb"))
 var stripe := PackedVector3Array([Vector3(-.053,-.014,.0015),Vector3(.053,-.014,.0015),Vector3(.053,.014,.0015),Vector3(-.053,.014,.0015)])
 for vertex: int in [0,2,1,0,3,2]:
  brush.add_vertex(stripe[vertex])
 exit_symbol = brush.commit()
 return exit_symbol

func mount_direction_panel(assembly: Node3D, bank: Dictionary, side: float) -> void:
 var entering: bool = (side < 0.) == (bank.direction > 0.)
 var upper: bool = side > 0.
 var destination: String = "上り" if bank.direction > 0. else "下り"
 var holder := Node3D.new()
 holder.name = "UpperDirection" if upper else "LowerDirection"
 # The sign's back sits on the fixed balustrade return, below the moving grip.
 # It is offset away from the centre of the 1.30 m tread.
 # Across the C north upper landing the neighbouring down handrail screens a
 # low sign. The raised mast sits outside the moving grip and bolts into the
 # stationary skirt. Keep it in sight from both upper landing approaches.
 var north_exit := str(bank.id) == "CN23-UP" and upper
 var marker_height := 1.34 if north_exit else .70
 var end_offset := .13 if north_exit else .50
 holder.position = Vector3(-1.12 if north_exit else -.974, marker_height + (float(bank.rise) if upper else 0.), side * (float(bank.run) * .5 + end_offset))
 holder.rotation.y = 0. if upper else PI
 assembly.add_child(holder)
 var panel := MeshInstance3D.new()
 var shell := BoxMesh.new()
 shell.size = Vector3(.31, .31, .048)
 shell.material = sign_panel_material
 panel.mesh = shell
 panel.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 panel.visibility_range_end = 30.
 holder.add_child(panel)
 var clamp := MeshInstance3D.new()
 var stem := BoxMesh.new()
 stem.size = Vector3(.06, marker_height - .39 if north_exit else .41, .065)
 stem.material = stainless_material
 clamp.mesh = stem
 clamp.position.y = -marker_height + .25 + stem.size.y * .5 if north_exit else -.35
 clamp.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 clamp.visibility_range_end = 30.
 holder.add_child(clamp)
 if north_exit:
  var bracket := MeshInstance3D.new()
  var tie := BoxMesh.new()
  tie.size = Vector3(.38,.042,.09)
  tie.material = stainless_material
  bracket.mesh = tie
  bracket.position = Vector3(.16, .25 - marker_height, 0.)
  bracket.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
  bracket.visibility_range_end = 30.
  holder.add_child(bracket)
 if entering:
  var indicator := Label3D.new()
  indicator.font = label_font
  indicator.font_size = 68
  indicator.pixel_size = .0027
  indicator.text = "↑"
  indicator.position = Vector3(0., .041, .0255)
  indicator.modulate = Color("#9ff6cc")
  indicator.outline_size = 0
  indicator.double_sided = false
  indicator.visibility_range_end = 30.
  holder.add_child(indicator)
 else:
  var symbol := MeshInstance3D.new()
  symbol.name = "NoEntry"
  symbol.mesh = no_entry_symbol()
  symbol.position = Vector3(0., .047, .027)
  symbol.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
  symbol.visibility_range_end = 30.
  holder.add_child(symbol)
 var caption := Label3D.new()
 caption.font = label_font
 caption.font_size = 36 if entering else 24
 caption.pixel_size = .0025
 caption.text = destination if entering else "進入禁止"
 caption.position = Vector3(0., -.091, .0255)
 caption.modulate = Color("#f2f7ee")
 caption.outline_size = 0
 caption.double_sided = false
 caption.visibility_range_end = 30.
 holder.add_child(caption)
 directional_panels.append({"id": bank.id, "end": "upper" if upper else "lower", "entry": entering, "panel": caption.text, "floor_relative_y_m": marker_height, "distance_label": false})

func ensure_near(point: Vector3) -> void:
 for data: Dictionary in definitions:
  if bank_ids.has(data.id):
   continue
  var centre := v3(data.c) + Vector3.UP * float(data.rise_m) * .5
  if Vector2(centre.x - point.x, centre.z - point.z).length_squared() > 150. * 150. or absf(centre.y - point.y) > 17.:
   continue
  create_bank(data)

func _physics_process(dt: float) -> void:
 if not paused:
  simulation_time += dt

func height(s:float,b:Dictionary)->float:
 var half:float=b.run*.5
 return float(b.rise)*clamp((s+half)/float(b.run),0.0,1.0)
func sample_track(bank: Dictionary, distance: float) -> Vector4:
 var distances: PackedFloat32Array = bank.distances
 var points: PackedVector3Array = bank.points
 var angles: PackedFloat32Array = bank.angles
 var d := fposmod(distance, float(bank.length))
 var low := 0
 var high := distances.size() - 1
 while low + 1 < high:
  var mid := (low + high) / 2
  if distances[mid] <= d:
   low = mid
  else:
   high = mid
 var f := (d - distances[low]) / maxf(.00001, distances[high] - distances[low])
 var local := points[low].lerp(points[high], f)
 return Vector4(local.z, local.y, lerpf(angles[low], angles[high], f), float(low))

func at_distance(bank: Dictionary, distance: float) -> Dictionary:
 var sample := sample_track(bank, distance)
 return {"local": Vector3(0., sample.y, sample.x), "angle": sample.z, "index": int(sample.w)}

func update_bank(bank: Dictionary, t: float) -> void:
 var count: int = bank.count
 var pitch: float = bank.pitch
 var belt_distance := t * speed * float(bank.direction)
 var multimesh: MultiMesh = bank.multimesh
 var data := PackedFloat32Array()
 data.resize(count * 12)
 bank.rubber.set_shader_parameter("belt_offset", belt_distance)
 for i: int in count:
  var d := i * pitch + belt_distance
  var point := sample_track(bank, d)
  var angle := point.z
  var stretch := pitch / .4
  var tread_y := point.y
  if point.w < float(bank.top_end):
   # At a floor/slope transition keep adjacent treads at a uniform projected
   # pitch. This avoids the visible gap or overlap left by a fixed tread depth.
   var before := sample_track(bank, d - pitch * .5)
   var after := sample_track(bank, d + pitch * .5)
   stretch = clampf((after.x - before.x) / .4, .60, 1.04)
   # Set the level plateau above the highest support under its footprint. The
   # controller keeps a continuous contact plane; the visible stair top and
   # riser stay intact and do not intersect the baked support surface.
   tread_y = height(point.x + .20 * stretch, bank)
  var a := i * 12
  var sine := sin(angle)
  var cosine := cos(angle)
  data[a] = 1.
  data[a + 5] = cosine
  data[a + 6] = -sine * stretch
  data[a + 7] = tread_y
  data[a + 9] = sine
  data[a + 10] = cosine * stretch
  data[a + 11] = point.x
 multimesh.buffer = data
 visible_updates += 1

func set_time(t: float) -> void:
 clock = t
 for bank: Dictionary in banks:
  update_bank(bank, t)
  bank.next_update = t

func _process(dt: float) -> void:
 nearby_check += dt
 var camera := get_viewport().get_camera_3d()
 if nearby_check > .25:
  nearby_check = 0.
  if camera != null:
   ensure_near(camera.global_position)
 if paused:
  return
 clock = maxf(0., simulation_time - (1. - Engine.get_physics_interpolation_fraction()) * get_physics_process_delta_time())
 for bank: Dictionary in banks:
  var delta := (Vector3(bank.c) + Vector3.UP * float(bank.rise) * .5) - camera.global_position if camera != null else Vector3.ZERO
  var distance_sq := delta.length_squared()
  if distance_sq > 130. * 130.:
   culled_updates += 1
   continue
  var interval := 0. if distance_sq < 40. * 40. else 1. / 24. if distance_sq < 75. * 75. else 1. / 12.
  if clock < float(bank.next_update) and interval > 0.:
   culled_updates += 1
   continue
  bank.next_update = clock + interval
  update_bank(bank, clock)

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
