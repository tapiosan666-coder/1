extends "res://sign_wayfinding_v34.gd"

const LOAD_RADIUS_M := 116.0
const UNLOAD_RADIUS_M := 144.0

var active_mounts: Dictionary = {}
var visual_specs: Dictionary = {}

func setup(g) -> void:
 initialize(g)
 for sign: Dictionary in definitions:
  var placement: Dictionary = placements.get(sign.id, {})
  var position_xz: Vector3 = game.v3(placement.get("p", sign.p))
  visual_specs[sign.id] = {"position": position_xz, "definition": sign}
 ensure_near(game.player.position)

func ensure_near(point: Vector3) -> void:
 for id in visual_specs:
  if active_mounts.has(id):
   continue
  var visual: Dictionary = visual_specs[id]
  if point.distance_squared_to(visual.position) > LOAD_RADIUS_M * LOAD_RADIUS_M:
   continue
  active_mounts[id] = build_board(visual.definition)

func retire_far(point: Vector3) -> void:
 for id in active_mounts.keys():
  if point.distance_squared_to(visual_specs[id].position) <= UNLOAD_RADIUS_M * UNLOAD_RADIUS_M:
   continue
  var mount: Node3D = active_mounts[id]
  active_mounts.erase(id)
  remove_child(mount)
  mount.queue_free()
