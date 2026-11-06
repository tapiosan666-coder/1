extends Node3D
var game
var data:Dictionary
var actors:Array=[]
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
func despawn(a)->void:
 states[str(a.record.id)]=state_of(a);actors.erase(a);remove_child(a);a.queue_free()
func update_near()->void:
 if game==null:return
 var centre:Vector3=game.player.position
 for a in actors.duplicate():
  var distance:float=Vector2(a.position.x-centre.x,a.position.z-centre.z).length()
  if not enabled or distance>95. or absf(a.position.y-centre.y)>10.:despawn(a)
 if not enabled:return
 var live:Dictionary={}
 for a in actors:live[str(a.record.id)]=true
 for d:Dictionary in data.people:
  if live.has(str(d.id)):continue
  var p:Vector3=game.v3(states[str(d.id)].p)if states.has(str(d.id))else game.v3(d.p)
  if Vector2(p.x-centre.x,p.z-centre.z).length()>72. or absf(p.y-centre.y)>7.:continue
  var a=load("res://shopper_actor_v20.gd").new();add_child(a);a.setup(game,d);a.frozen=frozen
  if states.has(str(d.id)):
   var s:Dictionary=states[str(d.id)];a.position=game.v3(s.p);a.rotation.y=s.yaw;a.clock=s.clock;a.point_index=s.point_index
   for key:String in ["seat_phase","browse_phase","gait_phase","motion_weight","speed_current","activity_time"]:
    if s.get(key)!=null:a.set(key,s[key])
   a.last_position=a.position;a.update_activity();a.pose(0.,false);a.reset_physics_interpolation()
  actors.append(a)
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
 elapsed+=dt
 if not frozen:simulated_seconds+=dt
 if elapsed>.4:elapsed=0.;update_near()
func _unhandled_key_input(e:InputEvent)->void:
 if game.developer_mode()and e is InputEventKey and e.pressed and not e.echo and e.keycode==KEY_F12:set_enabled(not enabled);get_viewport().set_input_as_handled()
func snapshot()->Dictionary:return {"planned_records":data.people.size(),"active_actors":actors.size(),"enabled":enabled,"simulated_seconds":simulated_seconds,"saved_states":states}
