extends SceneTree
## Like-for-like normal game frames of B's new public destinations.
func _initialize()->void:call_deferred("capture")
func capture()->void:
 var game=load("res://scenes/main.tscn").instantiate();root.add_child(game)
 game.start_run(300,912);game.set_physics_process(false);game.crowd.set_physics_process(false);game.player.set_physics_process(false)
 GraphicsOptions.apply(game,"balanced",false);game.hud.visible=false;game.player.handheld.visible=false;game.player.gun.visible=false;game.crowd.clock=2.0
 var tag:="before" if "--before" in OS.get_cmdline_user_args() else "after"
 var shots:Array=[
  ["b-event",Vector3(-340,1.7,28),Vector3(-323,2.1,39)],
  ["b-information",Vector3(-218,1.7,-4),Vector3(-218,1.8,10)],
  ["b-reading",Vector3(-386.8,7.225,78),Vector3(-386.8,7.0,88.3)],
  ["b-family",Vector3(-254.1,12.575,82),Vector3(-254.1,12.0,92.7)]
 ]
 for shot:Array in shots:
  game.player.camera.global_position=shot[1];game.player.camera.look_at(shot[2]);game.crowd._render()
  for frame in 4:await process_frame
  await RenderingServer.frame_post_draw
  root.get_texture().get_image().save_png("/tmp/fy021-%s-%s.png"%[tag,shot[0]])
 print("B_CONCOURSE_CAPTURE_OK ",tag);game.queue_free();await process_frame;quit()
