extends SceneTree
func _initialize() -> void: call_deferred("capture")
func capture() -> void:
	var game = load("res://scenes/main.tscn").instantiate(); root.add_child(game)
	game.start_run(300,912); game.set_physics_process(false); game.crowd.set_physics_process(false); game.player.set_physics_process(false)
	GraphicsOptions.apply(game,"balanced",false); game.crowd.clock = .4
	var tag := "before" if "--before" in OS.get_cmdline_user_args() else "after"
	for shot in [["fashion",Vector3(-57,.1,-9.5),Vector3(-57,1.6,-19)],["daily",Vector3(-21,.1,-10),Vector3(-21,1.5,-22)],["wares",Vector3(-27,.1,-19.4),Vector3(-27,1.8,-22.1)],["digital",Vector3(-3,.1,-11),Vector3(-7.5,1.25,-13.5)],["cafe",Vector3(15,.1,-11),Vector3(10.5,1,-13.5)],["b-clothes",Vector3(-346,.1,-10),Vector3(-346,1.6,-22)],["c-shoes",Vector3(-402,.1,-84),Vector3(-402,1.5,-77)]]:
		game.player.position = MallCurve.world(shot[1]); game.player.camera.look_at(MallCurve.world(shot[2])); game.crowd._render()
		game.hud.player_position = game.player.position; game.hud.location_name = Mall.zone_name(game.player.position); game.hud.notice_time = 0; game.hud.queue_redraw()
		await create_timer(.3).timeout; await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/fy13-%s-%s.png" % [tag,shot[0]])
		print("STOCK_CAPTURE ",tag," ",shot[0])
	quit()
