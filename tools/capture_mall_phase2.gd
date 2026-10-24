extends SceneTree
## Real gameplay rendering at fixed cameras, for art comparison, not an FPS test.
func _initialize() -> void: call_deferred("capture")
func capture() -> void:
	var game = load("res://scenes/main.tscn").instantiate(); root.add_child(game)
	game.start_run(300,912); game.set_physics_process(false); game.crowd.set_physics_process(false); game.player.set_physics_process(false)
	game.hud.visible=false;game.player.handheld.visible=false;game.player.gun.visible=false;game.crowd.clock=2.0
	var pass_name := "before" if "--before" in OS.get_cmdline_user_args() else "after"
	var shots := [
		["signs",Vector3(-57,7.25,6),Vector3(-57,8.5,-15)],
		["beauty",Vector3(-57,7.25,-5),Vector3(-57,7.9,-17)],
		["music",Vector3(15,12.60,-5),Vector3(15,13.2,-17)],
		["restroom",Vector3(-82,1.7,38.5),Vector3(-85,1.3,48.5)],
		["foyer",Vector3(-73,1.7,27.5),Vector3(-73,1.7,38)]
	]
	for shot in shots:
		game.player.position=MallCurve.world(shot[1])-Vector3.UP*1.68
		game.player.camera.global_position=MallCurve.world(shot[1]);game.player.camera.look_at(MallCurve.world(shot[2]))
		game.crowd._render()
		for frame in 3: await process_frame
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/fy-phase2-%s-%s.png" % [pass_name,shot[0]])
	print("PHASE2_CAPTURE_OK ",pass_name);game.queue_free();await process_frame;quit()
