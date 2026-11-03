extends SceneTree
var g
func _initialize()->void:call_deferred("run")
func key(code:int)->void:
 var e=InputEventKey.new();e.keycode=code;e.physical_keycode=code;e.pressed=true;Input.parse_input_event(e);Input.flush_buffered_events();await process_frame
 e=InputEventKey.new();e.keycode=code;e.physical_keycode=code;e.pressed=false;Input.parse_input_event(e);Input.flush_buffered_events();await process_frame
func count()->int:
 var total:int=0
 for a in g.shoppers_v18.actors+g.shoppers_v18.baseline:
  if a.visible and a.collision_layer==4:total+=1
 return total
func run()->void:
 g=load("res://main.tscn").instantiate();g.mode="v19-key-QA";root.add_child(g)
 while g.shoppers_v18==null or g.results.is_empty():await process_frame
 Engine.max_fps=0;g.player.position=Vector3(325,0,-63);g.mode="interactive";var rows:Array=[]
 rows.append({"id":"default-43","pass":count()==43})
 await key(KEY_N);rows.append({"id":"N-original-v18-43","pass":count()==43 and g.shoppers_v18.comparison_mode=="baseline"})
 await key(KEY_N);rows.append({"id":"N-female-only-1","pass":count()==1 and g.shoppers_v18.comparison_mode=="female_only"})
 await key(KEY_F12);rows.append({"id":"F12-off-no-person-colliders","pass":count()==0})
 await key(KEY_F12);rows.append({"id":"F12-restores-one","pass":count()==1})
 await key(KEY_N);rows.append({"id":"N-restores-v19-43","pass":count()==43 and g.shoppers_v18.comparison_mode=="v19"})
 await key(KEY_M);var a=g.shoppers_v18.actors[0];var before:float=a.clock;var pp:Vector3=a.position
 for i in range(30):await physics_frame
 rows.append({"id":"M-pauses-NPC-and-player","pass":g.ui.overlay=="map"and a.clock==before and a.position==pp and not g.player.is_physics_processing()});await key(KEY_M)
 g.write_json("v19-npc-controls.json",{"checks":rows,"human_playtest":false,"method":"Injected real N / F12 / M key events, actual actor visibility/collision masks/clock and player physics status"});print("V19_MODES ",rows);quit()
