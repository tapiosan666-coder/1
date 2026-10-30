extends Node3D
var game
var data:Dictionary={}
var actors:Array=[]
var enabled:bool=true
var simulated_seconds:float=0.
var frozen:bool=false
func setup(g)->void:
 game=g;name="V18_Test_Shoppers";data=g.read_json("res://source/v18/shoppers.json")
 for d:Dictionary in data.people:
  var person=load("res://shopper_actor_v18.gd").new();add_child(person);person.setup(g,d);actors.append(person)
 game.player.collision_mask=game.player.collision_mask|4
 for arg:String in OS.get_cmdline_user_args():
  if arg=="--shoppers-off":set_enabled(false,true)
 print("V18_SHOPPERS_BUILT ",actors.size()," enabled ",enabled)
func set_enabled(value:bool,force:bool=false)->bool:
 if value and not enabled and not force:
  for actor in actors:
   var delta:Vector3=game.player.global_position-actor.global_position;delta.y=0
   if delta.length()<.90:game.interaction_notice="買い物客の予定位置から離れて切り替えてください";game.notice_seconds=3.;return false
 enabled=value
 for actor in actors:actor.set_enabled(value)
 game.interaction_notice="買い物客 ON（%d人）"%actors.size()if value else"買い物客 OFF";game.notice_seconds=2.;return true
func _unhandled_key_input(e:InputEvent)->void:
 if e is InputEventKey and e.pressed and not e.echo and e.keycode==KEY_F12:set_enabled(not enabled);get_viewport().set_input_as_handled()
func _physics_process(dt:float)->void:
 if enabled and not frozen and game.ui!=null and game.ui.overlay=="":simulated_seconds+=dt
func set_frozen(value:bool)->void:
 frozen=value
 for actor in actors:actor.frozen=value
func snapshot()->Dictionary:
 var rows:Array=[]
 for actor in actors:rows.append({"id":actor.record.id,"p":[actor.position.x,actor.position.y,actor.position.z],"yaw":actor.rotation.y,"clock":actor.clock,"point_index":actor.point_index,"distance_walked":actor.distance_walked,"minimum_y":actor.minimum_y,"pose_role":actor.shown_role})
 return{"simulated_seconds":simulated_seconds,"actors":rows,"plan_sha256":game.data_hash("res://source/v18/shoppers.json"),"person_script_sha256":FileAccess.get_sha256("res://shopper_actor_v18.gd"),"actual_physics_snapshot":true}
func restore_snapshot(state:Dictionary)->void:
 assert(state.plan_sha256==game.data_hash("res://source/v18/shoppers.json"))
 set_frozen(true);simulated_seconds=float(state.simulated_seconds)
 for row:Dictionary in state.actors:
  for actor in actors:
   if str(actor.record.id)!=str(row.id):continue
   actor.position=game.v3(row.p);actor.rotation.y=float(row.yaw);actor.clock=float(row.clock);actor.point_index=int(row.point_index);actor.pose(actor.clock,actor.record.role=="walking");actor.reset_physics_interpolation()
