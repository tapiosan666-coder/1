extends SceneTree
func _initialize()->void:call_deferred("capture")
func capture()->void:
 var game=load("res://scenes/main.tscn").instantiate();root.add_child(game)
 GraphicsOptions.apply(game,"balanced",false)
 await save_image("/tmp/fy021-population-title.png")
 game.start_run(1000,912);game.set_physics_process(false);game.crowd.set_physics_process(false);game.player.set_physics_process(false)
 game.player.handheld.visible=false;game.player.gun.visible=false;game.crowd.clock=2.0
 var shots:Array=[
  ["b-event-1000",Vector3(-340,1.7,28),Vector3(-323,2.1,39)],
  ["b-information-1000",Vector3(-218,1.7,-4),Vector3(-218,1.8,10)]
 ]
 for shot:Array in shots:
  game.player.global_position=shot[1]-Vector3.UP*1.68
  game.player.camera.global_position=shot[1];game.player.camera.look_at(shot[2]);game.crowd._render();game.hud.visible=false
  await save_image("/tmp/fy021-%s.png"%shot[0])
 game.hud.visible=true;game.hud.player_position=game.player.position;game.hud.location_name=Mall.zone_name(game.player.position)
 await save_image("/tmp/fy021-population-play-1000.png")
 print("POPULATION_CAPTURE_OK identities=",game.run.population," fixed=",game.crowd.slots.size()," walking=",game.crowd.roles.count("walking"))
 game.queue_free();await process_frame;quit()
func save_image(path:String)->void:
 for frame in 8:await process_frame
 await RenderingServer.frame_post_draw
 root.get_texture().get_image().save_png(path)
