extends SceneTree
## Identical logical viewpoints in the normal game render; HUD and motion hidden only.
func _initialize()->void:call_deferred("capture")
func capture()->void:
 var game=load("res://scenes/main.tscn").instantiate();root.add_child(game);game.start_run(1000,912)
 game.set_physics_process(false);game.crowd.set_physics_process(false);game.player.set_physics_process(false)
 GraphicsOptions.apply(game,"balanced",false);game.hud.visible=false;game.player.handheld.visible=false;game.player.gun.visible=false
 var tag:="before" if "--before" in OS.get_cmdline_user_args() else "after"
 for shot:Array in [
  ["a-center",Vector3(-34,1.7,-1),Vector3(-42,7,17)],
  ["a-north",Vector3(-34,1.7,-25),Vector3(-45,6,-39)],
  ["b-light-2f",Vector3(-204.5,7.2,9.5),Vector3(-231,7.2,13)],
  ["b-time-3f",Vector3(-311.5,12.55,52.5),Vector3(-334,12.55,62)],
  ["a-entry",Vector3(-57,1.7,-3),Vector3(-57,2,-14)]
 ]:
  var at:=MallCurve.world(shot[1]);game.player.position=at-Vector3.UP*1.68;game.player.camera.global_position=at;game.player.camera.look_at(MallCurve.world(shot[2]));game.crowd._render()
  for frame in 5:await process_frame
  await RenderingServer.frame_post_draw
  root.get_texture().get_image().save_png("/tmp/fy023-%s-%s.png"%[tag,shot[0]])
 if tag=="after":
  game.hud.visible=true;game.set_mode("title")
  for frame in 5:await process_frame
  await RenderingServer.frame_post_draw
  root.get_texture().get_image().save_png("/tmp/fy023-after-title.png")
 print("UPPER_ACCESS_CAPTURE_OK ",tag);game.queue_free();await process_frame;quit()
