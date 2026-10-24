extends SceneTree
func _initialize() -> void: call_deferred("capture")
func capture() -> void:
	var game = load("res://scenes/main.tscn").instantiate(); root.add_child(game)
	game.start_run(300,912); game.set_physics_process(false); game.crowd.set_physics_process(false); game.player.set_physics_process(false)
	GraphicsOptions.apply(game,"balanced",false)
	var tag := "before" if "--before" in OS.get_cmdline_user_args() else "after"
	game.crowd.positions[0] = MallCurve.world(Vector3(-57,0,-13)); game.crowd.headings[0] = PI; game.crowd.roles[0] = "walking"; game.crowd.waits[0] = 30
	for shot in [["face",Vector3(-57,.1,-12),Vector3(-57,1.69,-13),.4],["closed",Vector3(-57,.1,-12),Vector3(-57,1.69,-13),.09],["body",Vector3(-57,.1,-10.7),Vector3(-57,1.4,-13),.4]]:
		game.player.position = MallCurve.world(shot[1]); game.player.camera.look_at(MallCurve.world(shot[2])); game.crowd.clock = shot[3]; game.crowd._render()
		game.hud.player_position = game.player.position; game.hud.location_name = Mall.zone_name(game.player.position); game.hud.notice_time = 0; game.hud.queue_redraw()
		await create_timer(.3).timeout; await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/fy11-%s-%s.png" % [tag,shot[0]])
		print("PEOPLE_CAPTURE ",tag," ",shot[0]," draws=",Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))
	quit()
