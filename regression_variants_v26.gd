extends SceneTree
func _initialize()->void:call_deferred("run")
func wait_ready()->void:
 while current_scene==null or current_scene.results.is_empty():await process_frame
 while not current_scene.get_node("V21_Route_Derived_Wayfinding").has_meta("ready"):await process_frame
 while not current_scene.get_node("V26_Mall_Architecture").has_meta("ready"):await process_frame
func key(code:int)->void:
 var e=InputEventKey.new();e.keycode=code;e.physical_keycode=code;e.pressed=true;Input.parse_input_event(e);Input.flush_buffered_events();await process_frame
 e=InputEventKey.new();e.keycode=code;e.physical_keycode=code;e.pressed=false;Input.parse_input_event(e);Input.flush_buffered_events();await process_frame
func run()->void:
 change_scene_to_file("res://main.tscn");await wait_ready();Engine.max_fps=0;var rows:Array=[]
 for code:int in[KEY_F4,KEY_F4,KEY_F6,KEY_F6]:
  var before:String=current_scene.scene_file_path;current_scene.mode="interactive";await key(code);await wait_ready();var after:String=current_scene.scene_file_path
  rows.append({"key":OS.get_keycode_string(code),"from":before,"to":after,"pass":before!=after and(current_scene.c_open_proposal or current_scene.es_site_proposal),"source_mismatches":current_scene.get_node("V21_Route_Derived_Wayfinding").stats.source_mismatches});print("V22_REFERENCE_KEY ",rows[-1])
 current_scene.write_json("v22-reference-scene-keys.json",{"checks":rows,"human_playtest":false,"method":"Actual injected F4/F6 input events and scene lifecycle; normal integrated candidate restores on second press."});quit()
