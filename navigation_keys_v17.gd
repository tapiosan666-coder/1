extends SceneTree
func _initialize()->void:call_deferred("run")
func press(code:int)->void:
 var e=InputEventKey.new();e.keycode=code;e.physical_keycode=code;e.pressed=true;Input.parse_input_event(e);Input.flush_buffered_events();await process_frame
 e=InputEventKey.new();e.keycode=code;e.physical_keycode=code;e.pressed=false;Input.parse_input_event(e);Input.flush_buffered_events();await process_frame
func run()->void:
 var scene=load("res://main.tscn").instantiate();root.add_child(scene);current_scene=scene;var checks:Array=[]
 for step:Array in[[KEY_F4,true,false],[KEY_F6,false,true],[KEY_F6,false,false]]:
  var old_id:int=current_scene.get_instance_id();await press(step[0])
  for tick in range(12):
   await process_frame
   if current_scene!=null and current_scene.get_instance_id()!=old_id and not current_scene.results.is_empty():break
  var good:bool=current_scene!=null and current_scene.get_instance_id()!=old_id
  if good:good=current_scene.c_open_proposal==step[1]and current_scene.es_site_proposal==step[2]
  checks.append({"key":step[0],"expected_C":step[1],"expected_ES":step[2],"pass":good});print("V16_NAVIGATION ",JSON.stringify(checks[-1]))
 var out="/workspace/v17-review/tests/navigation.json";var file=FileAccess.open(out,FileAccess.WRITE);file.store_string(JSON.stringify({"checks":checks,"pass":checks.all(func(q):return q["pass"]),"human_playtest":false,"method":"Physical F4/F6 key events through actual SceneTree.current_scene; not just constructor flags"},"  "));quit()
