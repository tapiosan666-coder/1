extends SceneTree
func _initialize()->void:call_deferred("run")
func key(code:int,value:bool)->void:
 var e=InputEventKey.new();e.keycode=code;e.physical_keycode=code;e.pressed=value;Input.parse_input_event(e)
func run()->void:
 var g=load("res://main.tscn").instantiate();root.add_child(g);current_scene=g
 while g.ui==null:await process_frame
 var checks:Array=[];key(KEY_F8,true);await process_frame;key(KEY_F8,false);await process_frame;var start=g.player.position;key(KEY_W,true)
 for i in range(30):await physics_frame
 key(KEY_W,false);checks.append({"id":"F8 freezes movement","pass":g.ui.overlay=="pilots"and g.player.position.distance_to(start)<.001})
 for j in range(6):
  if g.ui.overlay!="pilots":g.ui.show_pilots();await process_frame
  var buttons=g.ui.lift_buttons.get_children().filter(func(c):return c is Button);var label:String=buttons[j].text;buttons[j].pressed.emit()
  for i in range(20):await physics_frame
  checks.append({"id":"pilot "+label,"pass":g.ui.overlay==""and abs(g.player.position.y)<.2 and g.player.is_on_floor(),"position":[g.player.position.x,g.player.position.y,g.player.position.z]})
 var absent:int=0;var wrong:int=0;var ids=g.manifest.escalators.map(func(e):return e.id)
 for f:Dictionary in g.ui.map.data:
  for item:Dictionary in f.items:
   if item.kind=="エスカレーター"and item.id not in ids:absent+=1;wrong+=int(item.implemented)
 checks.append({"id":"planned B1/RF ES marked unavailable","pass":absent==12 and wrong==0,"planned_items":absent})
 key(KEY_F4,true);await process_frame;key(KEY_F4,false)
 while current_scene==null or current_scene==g:await process_frame
 var option=current_scene
 while option.ui==null:await process_frame
 checks.append({"id":"F4 C option","pass":option.c_open_proposal and not option.results.main_game_loaded})
 key(KEY_F7,true);await process_frame;key(KEY_F7,false)
 while current_scene==null or current_scene==option:await process_frame
 var study=current_scene
 while study.player==null:await process_frame
 checks.append({"id":"F7 independent ES study","pass":study.get_script().resource_path=="res://es_transfer_study_v12.gd"})
 key(KEY_F4,true);await process_frame;key(KEY_F4,false)
 while current_scene==null or current_scene==study:await process_frame
 var normal=current_scene
 while normal.ui==null:await process_frame
 checks.append({"id":"F4 returns from study","pass":not normal.c_open_proposal and not normal.results.main_game_loaded})
 normal.write_json("controls-v12.json",{"checks":checks,"synthetic_key_and_Button_pressed_events":true,"human_playtest":false,"passed":checks.filter(func(c):return c["pass"]).size(),"failed":checks.filter(func(c):return not c["pass"]).size()});print("CONTROLS_V12 ",checks.filter(func(c):return c["pass"]).size(),"/",checks.size());quit()
