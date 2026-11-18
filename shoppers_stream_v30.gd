extends Node3D
var game
var data:Dictionary
var actors: Array = []
var staged: Dictionary = {}
var retired_actors: Array[Node] = []
const ShopperActor = preload("res://shopper_actor_v20.gd")
var states:Dictionary={}
var enabled:bool=true
var frozen:bool=false
var comparison_mode:String="v20"
var simulated_seconds:float=0.
var elapsed:float=0.
func setup(g)->void:
 game=g;name="V30_Streamed_Shoppers";data=g.read_json("res://source/v19/shoppers.json");game.player.collision_mask|=4
 if OS.get_cmdline_user_args().has("--shoppers-off"):enabled=false
func state_of(a)->Dictionary:
 var row:Dictionary={"p":[a.position.x,a.position.y,a.position.z],"yaw":a.rotation.y,"clock":a.clock,"point_index":a.point_index}
 for key:String in ["seat_phase","browse_phase","gait_phase","motion_weight","speed_current","activity_time"]:row[key]=a.get(key)
 return row
func despawn(actor) -> void:
 var id := str(actor.record.id)
 if not staged.has(id):
  states[id] = state_of(actor)
 staged.erase(id)
 actors.erase(actor)
 remove_child(actor)
 retired_actors.append(actor)

func near_destination(p: Vector3, centre: Vector3, radius: float, height: float) -> bool:
 return Vector2(p.x - centre.x, p.z - centre.z).length_squared() <= radius * radius and absf(p.y - centre.y) <= height

func spawn_shopper(d: Dictionary, pre_stage: bool) -> void:
 var actor = ShopperActor.new()
 add_child(actor)
 actor.setup(game, d)
 actor.frozen = frozen
 var id := str(d.id)
 if states.has(id):
  var saved: Dictionary = states[id]
  actor.position = game.v3(saved.p)
  actor.rotation.y = saved.yaw
  actor.clock = saved.clock
  actor.point_index = saved.point_index
  for key: String in ["seat_phase", "browse_phase", "gait_phase", "motion_weight", "speed_current", "activity_time"]:
   if saved.get(key) != null:
    actor.set(key, saved[key])
  actor.last_position = actor.position
  actor.update_activity()
  actor.pose(0.0, false)
  actor.reset_physics_interpolation()
 if pre_stage:
  staged[id] = actor
  actor.hide()
  actor.set_physics_process(false)
 actors.append(actor)

func populate(centre: Vector3, deadline_usec: int, pre_stage: bool) -> bool:
 if not enabled:
  return true
 var live: Dictionary = {}
 for actor in actors:
  live[str(actor.record.id)] = true
 for d: Dictionary in data.people:
  var id := str(d.id)
  if live.has(id):
   continue
  var p: Vector3 = game.v3(states[id].p) if states.has(id) else game.v3(d.p)
  if not near_destination(p, centre, 72.0, 7.0):
   continue
  if Time.get_ticks_usec() >= deadline_usec:
   return false
  spawn_shopper(d, pre_stage)
 return true

func prepare_near(point: Vector3, deadline_usec: int) -> bool:
 return populate(point, deadline_usec, true)

func discard_staged() -> void:
 for actor in staged.values():
  despawn(actor)

func activate_staged() -> void:
 for actor in staged.values():
  actor.show()
  actor.set_physics_process(true)
 staged.clear()

func update_near() -> void:
 if game == null:
  return
 var centre: Vector3 = game.player.position
 for actor in actors.duplicate():
  var id := str(actor.record.id)
  if staged.has(id):
   continue
  if not enabled or not near_destination(actor.position, centre, 95.0, 10.0):
   despawn(actor)
 populate(centre, 9223372036854775807, false)

func set_enabled(value:bool,force:bool=false)->bool:
 if value and not enabled and not force:
  for d:Dictionary in data.people:
   var p:Vector3=game.v3(states[str(d.id)].p)if states.has(str(d.id))else game.v3(d.p)
   if game.player.position.distance_to(p)<.9:return false
 enabled=value;update_near();return true
func set_frozen(value:bool)->void:
 frozen=value
 for a in actors:a.frozen=value
func _process(dt:float)->void:
 if not retired_actors.is_empty():
  retired_actors.pop_front().queue_free()
 elapsed+=dt
 if not frozen:simulated_seconds+=dt
 if elapsed>.4:elapsed=0.;update_near()
func _unhandled_key_input(e:InputEvent)->void:
 if game.developer_mode()and e is InputEventKey and e.pressed and not e.echo and e.keycode==KEY_F12:set_enabled(not enabled);get_viewport().set_input_as_handled()
func snapshot()->Dictionary:return {"planned_records":data.people.size(),"active_actors":actors.size(),"enabled":enabled,"simulated_seconds":simulated_seconds,"saved_states":states}

func _exit_tree() -> void:
 for actor in retired_actors:
  actor.free()
 retired_actors.clear()
