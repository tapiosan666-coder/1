extends SceneTree
func _initialize() -> void: call_deferred("capture")
func capture() -> void:
	var game = load("res://scenes/main.tscn").instantiate(); root.add_child(game)
	game.start_run(300,912); game.set_physics_process(false); game.crowd.set_physics_process(false); game.player.set_physics_process(false)
	GraphicsOptions.apply(game,"balanced",false)
	game.crowd.clock = .4
	var tag := "before" if "--before" in OS.get_cmdline_user_args() else "after"
	for shot in [["concourse",Vector3(-70,.1,0),Vector3(-10,7,0)],["fashion",Vector3(-57,.1,-4),Vector3(-57,2,-19)],["materials",Vector3(-55,.1,-7),Vector3(-57,.08,-11)],["upper",Vector3(-25,10.975,5.2),Vector3(35,5.5,-6)],["inside",Vector3(-57,.1,-10),Vector3(-57,2,-22)]]:
		game.player.position = MallCurve.world(shot[1]); game.player.camera.look_at(MallCurve.world(shot[2])); game.crowd._render()
		game.hud.player_position = game.player.position; game.hud.location_name = Mall.zone_name(game.player.position); game.hud.notice_time = 0; game.hud.queue_redraw()
		await create_timer(.3).timeout; await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/fy12-%s-%s.png" % [tag,shot[0]])
		print("INTERIOR_CAPTURE ",tag," ",shot[0]," draws=",Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))
	quit()
