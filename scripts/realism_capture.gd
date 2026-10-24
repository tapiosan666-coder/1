class_name RealismCapture
extends RefCounted
## Fixed-camera development evidence; only called by the explicit capture flag.
static func capture(game:Node3D,tag:String="after")->void:
	game.start_run(300,912);game.set_physics_process(false);game.player.set_physics_process(false);game.crowd.set_physics_process(false)
	GraphicsOptions.apply(game,"balanced",false);game.crowd.clock=.4
	# Common walker fixture, legal in both layouts. Existing fixed slots remain as authored.
	var actors:Array=[[-63.0,-5.35,-11.0,-0.571742],[-369.0,0.0,-3.0,1.68978],[-217.0,5.525,-17.0,-0.018705],[-317.0,10.875,13.0,-2.465506],[-85.0,16.4,-23.0,-2.142783],[-51.0,-5.35,-5.0,-1.519996],[42.25937,0.0,24.2078,0.377543],[-287.0,5.525,-9.0,-0.479132],[-347.0,10.875,15.0,0.953437],[-73.0,16.4,-15.0,-0.184048],[-49.0,-5.35,23.0,1.58962],[-299.0,0.0,9.0,-2.705287],[-335.0,5.525,-25.0,0.368055],[-227.0,10.875,9.0,1.997408],[-69.0,16.4,-15.0,-2.117198],[-87.0,-5.35,5.0,-0.579986],[-397.0,0.0,15.0,-2.09933],[-325.0,5.525,23.0,1.55113],[-47.0,10.875,21.0,-3.025517],[-63.0,16.4,-23.0,0.038614],[22.19196,-5.35,23.36942,-2.209226],[-309.0,0.0,7.0,-0.844168],[-265.0,5.525,11.0,-1.00498],[-345.0,10.875,9.0,-2.731972],[-49.0,16.4,-11.0,3.11926],[-45.0,-5.35,5.0,-0.402938],[-399.0,0.0,15.0,1.794006],[-20.39079,5.525,11.90016,1.932754],[-409.0,10.875,-5.0,1.359675],[-83.0,16.4,-15.0,-1.00405],[9.78311,-5.35,24.07799,2.571404],[-225.0,0.0,-1.0,2.201941],[-271.0,5.525,-7.0,2.399233]]
	for j in actors.size():
		var i:=267+j;var actor:Array=actors[j]
		game.crowd.positions[i]=Vector3(actor[0],actor[1],actor[2]);game.crowd.headings[i]=actor[3]
		game.crowd._set_body_pose(i,false)
	var shots:=[
	 ["entrance",Vector3(-82,.1,0),Vector3(-25,1.7,0)],
	 ["atrium",Vector3(-47,.1,0),Vector3(-39,8,16)],
	 ["upper",Vector3(-66,5.625,6),Vector3(-25,8,0)],
	 ["fashion",Vector3(-57,.1,-9.5),Vector3(-57,1.6,-19)],
	 ["bookshop",Vector3(-75,.1,-9),Vector3(-75,1.6,-22)],
	 ["foyer",Vector3(70,.1,-9),Vector3(70,1.6,-31)],
	 ["dining",Vector3(69,.1,-35),Vector3(69,2.3,-60)],
	 ["lounge",Vector3(-39,.1,-13),Vector3(-39,1.7,-23)],
	 ["garden",Vector3(87,.1,-45),Vector3(102,1.5,-47)],
	 ["b-gallery",Vector3(-282,.1,0),Vector3(-340,7,0)],
	 ["b-store",Vector3(-346,.1,-10),Vector3(-346,1.6,-22)],
	 ["c-store",Vector3(-402,.1,-84),Vector3(-402,1.5,-77)]
	]
	if "--only-bookshop" in OS.get_cmdline_user_args():shots=shots.filter(func(shot:Array):return shot[0]=="bookshop")
	for shot in shots:
		game.player.position=MallCurve.world(shot[1]);game.player.camera.look_at(MallCurve.world(shot[2]));game.crowd._render()
		game.hud.player_position=game.player.position;game.hud.location_name=Mall.zone_name(game.player.position);game.hud.notice_time=0;game.hud.queue_redraw()
		await game.get_tree().create_timer(.3).timeout;await RenderingServer.frame_post_draw
		game.get_viewport().get_texture().get_image().save_png("/tmp/fy14-%s-%s.png"%[tag,shot[0]])
		print("REALISM_CAPTURE ",tag," ",shot[0])
	game.crowd.positions[0]=MallCurve.world(Vector3(-57,0,-13));game.crowd.headings[0]=PI;game.crowd.roles[0]="walking";game.crowd.waits[0]=30
	for shot in [["face",Vector3(-57,.1,-12),Vector3(-57,1.69,-13)],["body",Vector3(-57,.1,-10.7),Vector3(-57,1.4,-13)]]:
		game.player.position=MallCurve.world(shot[1]);game.player.camera.look_at(MallCurve.world(shot[2]));game.crowd._render()
		game.hud.player_position=game.player.position;game.hud.location_name=Mall.zone_name(game.player.position);game.hud.queue_redraw()
		await game.get_tree().create_timer(.3).timeout;await RenderingServer.frame_post_draw
		game.get_viewport().get_texture().get_image().save_png("/tmp/fy14-%s-%s.png"%[tag,shot[0]])
		print("REALISM_CAPTURE ",tag," ",shot[0])
