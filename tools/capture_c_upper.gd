extends SceneTree
## Normal full-game renders; no replacement materials or hidden architecture.
func _initialize()->void:call_deferred("capture")
func capture()->void:
 var game=load("res://scenes/main.tscn").instantiate();root.add_child(game)
 game.start_run(300,912);game.set_physics_process(false);game.crowd.set_physics_process(false);game.player.set_physics_process(false)
 GraphicsOptions.apply(game,"balanced",false);game.hud.visible=false;game.player.handheld.visible=false;game.player.gun.visible=false;game.crowd.clock=2.0
 var before:="--before" in OS.get_cmdline_user_args();var tag:="before" if before else "after"
 var y:=Mall.floor_height(1)
 var shots:Array=[
  ["garden-ground",Vector3(-386,1.7,-102),Vector3(-428,6,-132)],
  ["gate-stairs",Vector3(-387,1.7,-96),Vector3(-365,5,-89)]
 ]
 if not before:
  shots.append(["garden-terrace",Vector3(-432,y+1.7,-117),Vector3(-432,y+2,-151)])
  shots.append(["garden-bridge",Vector3(-442,y+1.7,-34),Vector3(-442,y+2,-94)])
 for shot:Array in shots:
  game.player.camera.global_position=shot[1];game.player.camera.look_at(shot[2]);game.crowd._render()
  await save_image("/tmp/fy021-%s-%s.png"%[tag,shot[0]])
 if not before:
  game.hud.visible=true;game.set_mode("map");game.hud.set_map_floor(1)
  await save_image("/tmp/fy021-after-map-2f.png")
 print("C_UPPER_CAPTURE_OK ",tag);game.queue_free();await process_frame;quit()
func save_image(path:String)->void:
 for frame in 4:await process_frame
 await RenderingServer.frame_post_draw
 root.get_texture().get_image().save_png(path)
