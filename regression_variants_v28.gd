extends SceneTree
func _initialize()->void:call_deferred("run")
func wait_ready()->void:
 while current_scene==null or current_scene.results.is_empty():await process_frame
 while not current_scene.get_node("V21_Route_Derived_Wayfinding").has_meta("ready"):await process_frame
 while not current_scene.get_node("V28_Architecture").has_meta("ready"):await process_frame
func key(code:int)->void:
 var e=InputEventKey.new();e.keycode=code;e.physical_keycode=code;e.pressed=true;Input.parse_input_event(e);Input.flush_buffered_events();await process_frame
 e=InputEventKey.new();e.keycode=code;e.physical_keycode=code;e.pressed=false;Input.parse_input_event(e);Input.flush_buffered_events();await process_frame
func run()->void:
 change_scene_to_file("res://main.tscn");await wait_ready();Engine.max_fps=0;var rows:Array=[]
 for code:int in[KEY_F4,KEY_F4,KEY_F6,KEY_F6]:
  var before:String=current_scene.scene_file_path;current_scene.mode="interactive";await key(code);await wait_ready();var after:String=current_scene.scene_file_path
  var active_b:int=current_scene.player.escalators.filter(func(e):return str(e.id).begins_with("B-WEST")).size()
  var zone:Dictionary=current_scene.commons_v16.data.zones.filter(func(e):return e.id=="C-DOG-RUN")[0]
  var expected:int=6 if current_scene.es_site_proposal else 0
  rows.append({"key":OS.get_keycode_string(code),"from":before,"to":after,"pass":before!=after and(current_scene.c_open_proposal or current_scene.es_site_proposal)and active_b==expected and absf(zone.preferred[0]+77)<.01 and absf(zone.preferred[1]+245)<.01,"dog_world":zone.preferred,"B_west_ids":current_scene.player.escalators.filter(func(e):return str(e.id).begins_with("B-WEST")).map(func(e):return e.id),"retired_B_ids_present":current_scene.player.escalators.filter(func(e):return e.id in ["E1-12-UP","E1-12-DOWN","E1-23-UP","E1-23-DOWN"]).map(func(e):return e.id),"source_mismatches":current_scene.get_node("V21_Route_Derived_Wayfinding").stats.source_mismatches});print("V22_REFERENCE_KEY ",rows[-1])
 current_scene.write_json("v28-reference-scene-keys.json",{"checks":rows,"human_playtest":false,"method":"Actual injected F4/F6 input events and scene lifecycle; normal integrated candidate restores on second press."});quit()
