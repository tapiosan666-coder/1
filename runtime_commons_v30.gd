extends Node3D
var game
var stream
var gates:Dictionary={}
var fair_enabled:bool=true
func set_fair(value:bool)->bool:
 if value and not fair_enabled and absf(game.player.position.y)<2.:
  for d:Dictionary in game.read_json("res://source/v25/commons.json").instances:
   if d.activation=="aichi_fair"and game.player.position.distance_to(game.v3(d.p))<2.:return false
 fair_enabled=value;stream.set_fair(value);return true
func request_gate(id:String)->bool:
 if not gates.has(id):return false
 var gate:Dictionary=gates[id];gate.target=0. if gate.target>0 else PI*.5;return true
func _physics_process(dt:float)->void:
 if game==null or game.ui==null or game.ui.overlay!="":return
 for gate in gates.values():gate.angle=move_toward(float(gate.angle),float(gate.target),dt*1.4);gate.body.rotation.y=gate.angle
func _unhandled_key_input(e:InputEvent)->void:
 if not e is InputEventKey or not e.pressed or e.echo:return
 if game.developer_mode()and e.keycode==KEY_F11:set_fair(not fair_enabled);get_viewport().set_input_as_handled()
 elif e.keycode==KEY_F and game.ui.overlay=="":
  var best:String="";var distance:float=2.4
  for id:String in gates:
   var d:float=game.player.position.distance_to(gates[id].body.global_position+Vector3(.6,0,0))
   if d<distance:best=id;distance=d
  if best!="":request_gate(best);get_viewport().set_input_as_handled()
