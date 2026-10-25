extends SceneTree
## Fixed walkable cameras, frozen shared seed. Interior evidence, not an FPS test.
func _initialize()->void:call_deferred("capture")
func capture()->void:
 var game=load("res://scenes/main.tscn").instantiate();root.add_child(game)
 game.start_run(300,912);game.set_physics_process(false);game.crowd.set_physics_process(false);game.player.set_physics_process(false)
 GraphicsOptions.apply(game,"balanced",false)
 game.hud.visible=false;game.player.handheld.visible=false;game.player.gun.visible=false;game.crowd.clock=2.0
 var tag:="before" if "--before" in OS.get_cmdline_user_args() else "after"
 var shots=[
  ["fashion-a",Vector3(-58.3,1.7,-9.5),Vector3(-57,1.7,-19)],
  ["fashion-upper",Vector3(-22.3,7.225,-9.5),Vector3(-21,7.225,-19)],
  ["fashion-b",Vector3(-347.3,1.7,-10.0),Vector3(-346,1.7,-21)],
  ["home-c",Vector3(-351,1.7,-153.5),Vector3(-352,1.7,-165)],
  ["market",Vector3(24,1.7,17),Vector3(24,1.7,37)],
  ["beauty",Vector3(-58.3,7.225,-9.5),Vector3(-57,7.225,-20)]
 ]
 for shot in shots:
  game.player.position=MallCurve.world(shot[1])-Vector3.UP*1.68
  game.player.camera.global_position=MallCurve.world(shot[1]);game.player.camera.look_at(MallCurve.world(shot[2]));game.crowd._render()
  for frame in 4:await process_frame
  await RenderingServer.frame_post_draw
  root.get_texture().get_image().save_png("/tmp/fy018-%s-%s.png"%[tag,shot[0]])
 print("RETAIL_DENSITY_CAPTURE_OK ",tag);game.queue_free();await process_frame;quit()
