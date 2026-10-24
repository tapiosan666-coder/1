extends SceneTree
func _initialize() -> void: call_deferred("capture")
func capture() -> void:
	var game = load("res://scenes/main.tscn").instantiate(); root.add_child(game)
	game.start_run(300,912); game.set_physics_process(false); game.crowd.set_physics_process(false); game.player.set_physics_process(false)
	GraphicsOptions.apply(game,"balanced",false); game.crowd.clock = .4
	var tag := "before" if "--before" in OS.get_cmdline_user_args() else "after"
	var shots := [["atrium",Vector3(-39,.1,-13),Vector3(-39,1.7,-23)],["gateway",Vector3(70,.1,-9),Vector3(70,1.6,-31)],["waiting",Vector3(68,.1,-18),Vector3(62.35,1.2,-20)],["water",Vector3(66,.1,-28),Vector3(62.1,1.1,-28)],["court",Vector3(69,.1,-35),Vector3(69,2.3,-60)],["garden",Vector3(87,.1,-45),Vector3(102,1.5,-47)]]
	if tag == "before": shots.append(["old-loop",Vector3(0,.1,-30),Vector3(50,1.7,-30)])
	for shot in shots:
		game.player.position = MallCurve.world(shot[1]); game.player.camera.look_at(MallCurve.world(shot[2])); game.crowd._render()
		game.hud.player_position = game.player.position; game.hud.location_name = Mall.zone_name(game.player.position); game.hud.notice_time = 0; game.hud.queue_redraw()
		await create_timer(.3).timeout; await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/fy14-%s-%s.png" % [tag,shot[0]])
		print("DINING_CAPTURE ",tag," ",shot[0])
	quit()
