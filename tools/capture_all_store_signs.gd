extends SceneTree
func _initialize()->void:call_deferred("capture")
func capture()->void:
 var game=load("res://scenes/main.tscn").instantiate();root.add_child(game)
 game.start_run(300,912);game.set_physics_process(false);game.crowd.set_physics_process(false);game.player.set_physics_process(false)
 game.hud.visible=false;game.player.handheld.visible=false;game.player.gun.visible=false;game.crowd.clock=2.0
 var shots=[
  ["market",Vector3(24,1.75,1),Vector3(24,3.5,10)],
  ["basement",Vector3(-58,-3.6,-6.5),Vector3(-58,-2.35,-23.4)],
  ["food",Vector3(68,1.75,-41),Vector3(68,3.1,-60)],
  ["electronics",Vector3(-356,1.75,0),Vector3(-374,3.6,0)],
  ["home",Vector3(-356,7.275,0),Vector3(-374,9,0)],
  ["cinema",Vector3(-356,12.625,0),Vector3(-374,14.4,0)]
 ]
 for shot in shots:
  game.player.position=MallCurve.world(shot[1])-Vector3.UP*1.68
  game.player.camera.global_position=MallCurve.world(shot[1]);game.player.camera.look_at(MallCurve.world(shot[2]));game.crowd._render()
  for frame in 4:await process_frame
  await RenderingServer.frame_post_draw
  root.get_texture().get_image().save_png("/tmp/fy-all-signs-%s.png"%shot[0])
 print("ALL_STORE_SIGNS_CAPTURE_OK");game.queue_free();await process_frame;quit()
