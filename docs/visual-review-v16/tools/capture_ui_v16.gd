extends SceneTree
func _initialize()->void:call_deferred("run")
func key(code:int)->void:
 var e=InputEventKey.new();e.keycode=code;e.physical_keycode=code;e.pressed=true;Input.parse_input_event(e);Input.flush_buffered_events();await process_frame
 e=InputEventKey.new();e.keycode=code;e.physical_keycode=code;e.pressed=false;Input.parse_input_event(e);Input.flush_buffered_events();await process_frame
func run()->void:
 var out="/workspace/v16-review/ui";DirAccess.make_dir_recursive_absolute(out);var g=load("res://main.tscn").instantiate();g.mode="UI-native-review";root.add_child(g)
 while g.ui==null or g.results.is_empty():await process_frame
 g.mode="interactive";g.player.position=Vector3(-118,.02,-280);root.size=Vector2i(1920,1080);var checks:Array=[]
 await key(KEY_M);g.ui.map.wing="C";g.ui.map.floor_label="1F";g.ui.map.wing_select.select(2);g.ui.map.refresh_floors()
 for i in range(2):await process_frame
 await RenderingServer.frame_post_draw;root.get_texture().get_image().save_png(out+"/M-map-C.png");checks.append({"id":"M-map-C","pass":g.ui.overlay=="map"and not g.player.is_physics_processing(),"actual_Viewport":true});await key(KEY_M)
 await key(KEY_F9)
 for i in range(2):await process_frame
 await RenderingServer.frame_post_draw;root.get_texture().get_image().save_png(out+"/F9-v16-destinations.png");checks.append({"id":"F9-native","pass":g.ui.overlay=="amenities","actual_Viewport":true});await key(KEY_F9)
 await key(KEY_F10)
 for i in range(2):await process_frame
 await RenderingServer.frame_post_draw;root.get_texture().get_image().save_png(out+"/F10-settings.png");checks.append({"id":"F10-native","pass":g.ui.overlay=="settings","actual_Viewport":true});var f=FileAccess.open(out+"/checks.json",FileAccess.WRITE);f.store_string(JSON.stringify({"checks":checks,"human_playtest":false,"method":"Native Godot Viewport, physical key-event injection; no human operator","resolution":[1920,1080]},"  "));quit()
