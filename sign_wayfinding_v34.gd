extends Node3D

const PLACEMENT_PATH := "res://source/v34/sign-mounts.json"
var game
var definitions: Array = []
var placements: Dictionary = {}
var mounting_material: StandardMaterial3D

func face_texture(path: String) -> Texture2D:
 var info := ConfigFile.new()
 if info.load(path + ".import") == OK and FileAccess.file_exists(str(info.get_value("remap", "path", ""))):
  return load(path) as Texture2D
 return ImageTexture.create_from_image(Image.load_from_file(path))

func initialize(g) -> void:
 game = g
 name = "V31_Signs"
 definitions = game.read_json("res://source/v32/signs.json")
 if FileAccess.file_exists(PLACEMENT_PATH):
  placements = game.read_json(PLACEMENT_PATH)
 mounting_material = StandardMaterial3D.new()
 mounting_material.albedo_color = Color("#3c494f")
 mounting_material.roughness = .62

func build_board(board: Dictionary) -> Node3D:
 var attachment: Dictionary = placements.get(board.id, {})
 var p: Vector3 = game.v3(attachment.get("p", board.p))
 var n := Vector3(board.n[0], 0, board.n[1])
 var width := float(attachment.get("width", board.width))
 var centre_y := float(attachment.get("height", board.height))
 var face_height := float(attachment.get("face_height", .64))
 var mount := Node3D.new()
 mount.name = str(board.id).validate_node_name()
 mount.transform = Transform3D(Basis(Vector3.UP.cross(n), Vector3.UP, n), p)
 add_child(mount)
 if not attachment.is_empty():
  build_hanger(mount, p.y, width, face_height, centre_y, attachment.supports_y)
 for side: int in [1, -1]:
  var plane := MeshInstance3D.new()
  var quad := QuadMesh.new()
  quad.size = Vector2(width, face_height)
  plane.mesh = quad
  plane.position = Vector3(0, centre_y, .085 * side)
  plane.rotation.y = PI if side < 0 else 0.0
  var mat := StandardMaterial3D.new()
  mat.albedo_texture = face_texture(board.textures.front if side > 0 else board.textures.back)
  mat.roughness = .72
  mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
  plane.material_override = mat
  plane.visibility_range_end = 95.0
  plane.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
  mount.add_child(plane)
 return mount

func build_hanger(mount: Node3D, floor_y: float, width: float, face_height: float, centre_y: float, support_heights: Array) -> void:
 add_trim_box(mount, Vector3(width + .07, face_height + .04, .14), Vector3(0, centre_y, 0))
 for i in range(2):
  var x := width * (-.35 if i == 0 else .35)
  var rod_start := centre_y + face_height*.5
  var rod_end := float(support_heights[i]) - floor_y + .025
  var rod_length := rod_end - rod_start
  if rod_length > .03:
   add_trim_box(mount, Vector3(.036, rod_length, .036), Vector3(x, rod_start + rod_length * .5, 0))

func add_trim_box(parent: Node3D, size: Vector3, position: Vector3) -> void:
 var instance := MeshInstance3D.new()
 var box := BoxMesh.new()
 box.size = size
 instance.mesh = box
 instance.position = position
 instance.material_override = mounting_material
 instance.visibility_range_end = 95.0
 instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 parent.add_child(instance)

func clean_chunk(chunk: Node) -> void:
 for label: Label3D in chunk.find_children("*", "Label3D", true, false):
  for board: Dictionary in definitions:
   # Clean the authored position even if the runtime face was moved.
   var n := Vector3(board.n[0], 0, board.n[1])
   var basis := Basis(Vector3.UP.cross(n), Vector3.UP, n)
   var local: Vector3 = basis.inverse() * (label.global_position - game.v3(board.p))
   if absf(local.y - float(board.height)) < .29 and absf(local.x) < float(board.width) * .5 + .08 and absf(local.z) < .16:
    label.hide()
    break
