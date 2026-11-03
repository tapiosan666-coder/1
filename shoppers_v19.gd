extends "res://shoppers_v18.gd"
var comparison_mode:String="v19"
var baseline:Array=[]
func setup(g)->void:
 game=g;name="V19_Test_Shoppers";data=g.read_json("res://source/v19/shoppers.json")
 for d:Dictionary in data.people:
  var person=load("res://shopper_actor_v19.gd").new();add_child(person);person.setup(g,d);actors.append(person)
 game.player.collision_mask=game.player.collision_mask|4
 for arg:String in OS.get_cmdline_user_args():
  if arg=="--shoppers-off":set_enabled(false,true)
  elif arg=="--npc-baseline":set_mode("baseline",true)
  elif arg=="--female-only":set_mode("female_only",true)
 print("V19_SHOPPERS_BUILT ",actors.size()," female 1; mode ",comparison_mode)
func set_mode(value:String,force:bool=false)->bool:
 if not force:
  for a in actors:
   var delta:Vector3=game.player.position-a.position;delta.y=0
   if delta.length()<1.0:game.interaction_notice="人物から少し離れて比較モードを変更してください";game.notice_seconds=3.;return false
 comparison_mode=value
 if comparison_mode=="baseline"and baseline.is_empty():
  for d:Dictionary in game.read_json("res://source/v18/shoppers.json").people:
   var actor=load("res://shopper_actor_v18.gd").new();add_child(actor);actor.setup(game,d);baseline.append(actor)
 apply_visibility();return true
func apply_visibility()->void:
 for actor in actors:actor.set_enabled(enabled and comparison_mode!="baseline"and(comparison_mode!="female_only"or bool(actor.record.get("female_reference",false))))
 for actor in baseline:actor.set_enabled(enabled and comparison_mode=="baseline")
func set_enabled(value:bool,force:bool=false)->bool:
 if value and not enabled and not force:
  for actor in actors+baseline:
   var delta:Vector3=game.player.position-actor.position;delta.y=0
   if delta.length()<.90:game.interaction_notice="人物予定位置から離れて切り替えてください";game.notice_seconds=3.;return false
 enabled=value;apply_visibility();game.interaction_notice="買い物客 "+("ON / "+comparison_mode if enabled else"OFF");game.notice_seconds=2.;return true
func _unhandled_key_input(e:InputEvent)->void:
 if e is InputEventKey and e.pressed and not e.echo:
  if e.keycode==KEY_F12:set_enabled(not enabled);get_viewport().set_input_as_handled()
  elif e.keycode==KEY_N:
   var modes:Array=["v19","baseline","female_only"];set_mode(modes[(modes.find(comparison_mode)+1)%3]);game.interaction_notice="人物比較 "+comparison_mode;game.notice_seconds=3.;get_viewport().set_input_as_handled()
func set_frozen(value:bool)->void:
 super.set_frozen(value)
 for actor in baseline:actor.frozen=value
func snapshot()->Dictionary:
 var state=super.snapshot();state.plan_sha256=game.data_hash("res://source/v19/shoppers.json");state.person_script_sha256=game.data_hash("res://shopper_actor_v19.gd");state.comparison_mode=comparison_mode
 for row in state.actors:
  for actor in actors:
   if actor.record.id==row.id:row.merge({"activity":actor.activity,"seat_phase":actor.seat_phase,"browse_phase":actor.browse_phase,"gait_phase":actor.gait_phase,"motion_weight":actor.motion_weight,"speed_current":actor.speed_current,"visited_states":actor.visited_states,"female":actor.female!=null})
 return state
func restore_snapshot(state:Dictionary)->void:
 assert(state.plan_sha256==game.data_hash("res://source/v19/shoppers.json"));set_frozen(true);simulated_seconds=float(state.simulated_seconds)
 for row in state.actors:
  for actor in actors:
   if str(actor.record.id)!=str(row.id):continue
   actor.position=game.v3(row.p);actor.rotation.y=row.yaw;actor.clock=row.clock;actor.point_index=int(row.point_index);actor.seat_phase=row.get("seat_phase",6.6);actor.browse_phase=row.get("browse_phase",3.);actor.gait_phase=row.get("gait_phase",0.);actor.motion_weight=row.get("motion_weight",0.);actor.speed_current=row.get("speed_current",0.);actor.update_activity();actor.pose(actor.clock,actor.motion_weight>.1);actor.reset_physics_interpolation()
