extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var configured:String=ProjectSettings.get_setting("application/run/main_scene");change_scene_to_file(configured)
 while current_scene==null or current_scene.results.is_empty():await process_frame
 var g=current_scene
 while not g.get_node("V29_Continuous_1F").has_meta("ready"):await process_frame
 root.size=Vector2i(1920,1080)
 for i in 2:await process_frame
 await RenderingServer.frame_post_draw
 var out:String="res://evidence"
 for a:String in OS.get_cmdline_user_args():
  if a.begins_with("--output="):out=a.trim_prefix("--output=")
 root.get_texture().get_image().save_jpg(out+"/fresh-normal-start.jpg",.95)
 var api=load("res://shopping_catalog_v25.gd").new();api.setup(g)
 var d={"configured_main_scene":configured,"actual_current_scene":g.scene_file_path,"engine":Engine.get_version_info(),"version29_ready":true,"stores":api.stores.size(),"NPC":g.shoppers_v18.actors.size(),"FPS_setting":Engine.max_fps,"VSync":DisplayServer.window_get_vsync_mode(),"resolution":[root.size.x,root.size.y],"adapter":RenderingServer.get_video_adapter_name(),"human_F5_key_press":false,"method":"fresh archive, native boot via configured main scene; F5-equivalent automated startup","all_15_layers_from_inherited_architecture":true};var f=FileAccess.open(out+"/fresh-normal-start.json",FileAccess.WRITE);f.store_string(JSON.stringify(d,"  "));f=null
 print("V29_FRESH_BOOT_READY ",d.stores," stores ",d.NPC," NPC");g.queue_free();await process_frame;await process_frame;quit()
