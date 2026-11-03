extends "res://shoppers_v19.gd"
func setup(g)->void:
 comparison_mode="v20";game=g;name="V20_Test_Shoppers";data=g.read_json("res://source/v19/shoppers.json")
 for d:Dictionary in data.people:
  var person=load("res://shopper_actor_v20.gd").new();add_child(person);person.setup(g,d);actors.append(person)
 game.player.collision_mask=game.player.collision_mask|4
 for arg:String in OS.get_cmdline_user_args():
  if arg=="--shoppers-off":set_enabled(false,true)
  elif arg=="--npc-baseline":set_mode("baseline",true)
  elif arg=="--female-only":set_mode("female_only",true)
  elif arg=="--v19-reference":set_mode("v19",true)
 print("V20_SHOPPERS_BUILT ",actors.size()," reference female1 / ",comparison_mode)
func set_mode(value:String,force:bool=false)->bool:
 var changed:bool=super.set_mode(value,force)
 if changed:
  for a in actors:
   if a.female!=null:
    a.female.set_variant("v19"if value=="v19"else"v20");a.record.stride_m=.62 if value=="v19"else .66;a.gait_phase=a.distance_walked/float(a.record.stride_m)
 return changed
func _unhandled_key_input(e:InputEvent)->void:
 if e is InputEventKey and e.pressed and not e.echo:
  if e.keycode==KEY_F12:set_enabled(not enabled);get_viewport().set_input_as_handled()
  elif e.keycode==KEY_N:
   var modes:Array=["v20","v19","female_only","baseline"];var changed:bool=set_mode(modes[(modes.find(comparison_mode)+1)%modes.size()]);game.interaction_notice="人物比較 "+comparison_mode if changed else game.interaction_notice;game.notice_seconds=3.;get_viewport().set_input_as_handled()
  elif e.keycode==KEY_P:
   for a in actors:
    if a.female==null:continue
    if comparison_mode in["v19","baseline"]:game.interaction_notice="表情の確認はv20モデルで行ってください";game.notice_seconds=3.;break
    var names:Array=a.female.expression_data.keys();a.female.set_expression(names[(names.find(a.female.expression)+1)%names.size()]);game.interaction_notice="基準モデル表情："+str(a.female.expression_data[a.female.expression].label);game.notice_seconds=3.
   get_viewport().set_input_as_handled()
func snapshot()->Dictionary:
 var result=super.snapshot();result.person_script_sha256=game.data_hash("res://shopper_actor_v20.gd")
 for row in result.actors:
  for a in actors:
   if row.id==a.record.id and a.female!=null:row.character_state=a.female.state()
 return result

func restore_snapshot(state:Dictionary)->void:
 set_mode(str(state.get("comparison_mode","v20")),true)
 super.restore_snapshot(state)
 for row in state.actors:
  if not row.has("character_state"):continue
  for actor in actors:
   if actor.record.id!=row.id or actor.female==null:continue
   var saved:Dictionary=row.character_state;var player_clip:String=str(saved.get("actual_player_clip",""))
   if player_clip=="":player_clip=str(saved.get("requested_clip","Idle"))
   var component=actor.female;component.set_expression(str(saved.get("expression","normal")),true)
   if component.animation.has_animation(player_clip):
    var player_time:float=float(saved.get("player_time_seconds",0.));var phase:float=player_time/component.animation.get_animation(player_clip).length
    component.deterministic_pose(player_clip,player_time,phase)
