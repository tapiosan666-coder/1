extends SceneTree
const POINT := Vector3(178.99594525,0.,-39.18126625)
const INWARD := Vector3(.66726156855,0,.74482346844)
const ALONG := Vector3(-.74482346844,0,.66726156855)
var game
var normal := false
var capture_mode := false
var output := ""
var trials: Array = []
func _initialize()->void:call_deferred("run")

func local(lateral:float,depth:float,y:=0.)->Vector3:
	return POINT+ALONG*lateral+INWARD*depth+Vector3.UP*y

func xyz(v:Vector3)->Array:return [v.x,v.y,v.z]

func warm_location(p:Vector3)->void:
	game.player.input_enabled=false
	game.player.reset_motion_state()
	game.player.position=p+Vector3.UP*.07
	game.get_node("V30_Runtime").prepare_position(p)
	game.get_node("V31_Sales").update_near()
	game.player.reset_physics_interpolation()
	for i:int in 10:await physics_frame

func cast(a:Vector3,b:Vector3)->Dictionary:
	var query:=PhysicsRayQueryParameters3D.create(a,b,1,[game.player.get_rid()])
	query.hit_back_faces=true
	var h:Dictionary=game.get_world_3d().direct_space_state.intersect_ray(query)
	if h.is_empty():return {}
	return {"collider":str(h.collider.name),"p":xyz(h.position)}

func walk(label:String,start:Vector3,targets:Array)->void:
	await warm_location(start)
	var path:Array=[]
	for v:Vector3 in targets:path.append(xyz(v))
	var r:Dictionary=await game.walk_points(path,2.4)
	if r.has("position") and r.position is Vector3:r.position=xyz(r.position)
	if r.has("target") and r.target is Vector3:r.target=xyz(r.target)
	trials.append({"label":label,"start":xyz(start),"targets":path,"result":r})
	print("B032_WALK ",label," ",r.get("pass"))

func run()->void:
	RenderingServer.set_render_loop_enabled(false)
	for arg:String in OS.get_cmdline_user_args():
		if arg=="--normal":normal=true
		if arg=="--capture":capture_mode=true
		if arg.begins_with("--out="):output=arg.trim_prefix("--out=")
	if output.is_empty():quit(2);return
	game=load("res://main.tscn" if normal else "res://TERRUNE_additional_entry_proposal.tscn").instantiate()
	game.mode="v36-entry-inspection"
	root.add_child(game)
	while game.results.is_empty() or (not normal and not game.results.has("terrune_entry_study")):await process_frame
	RenderingServer.set_render_loop_enabled(false)
	game.shoppers_v18.set_enabled(false,true)
	await warm_location(local(0.,-4.))
	if capture_mode:
		game.player.set_physics_process(false)
		game.ui.hide()
		if game.hud!=null:game.hud.get_parent().hide()
		for shot: Array in [["from_concourse",local(-2.7,-2.3,1.65),local(.55,2.5,1.30)],["from_store",local(.45,3.72,1.65),local(-.8,-3.,1.36)]]:
			game.player.camera.global_transform=Transform3D(Basis.IDENTITY,shot[1]).looking_at(shot[2],Vector3.UP)
			game.player.camera.fov=72.
			game.player.camera.reset_physics_interpolation()
			game.player.camera.force_update_transform()
			RenderingServer.set_render_loop_enabled(true)
			for frame:int in 2:
				await RenderingServer.frame_post_draw
			var image:=root.get_texture().get_image()
			image.save_jpg(output+"-"+shot[0]+".jpg",.92)
			RenderingServer.set_render_loop_enabled(false)
	var rays:Array=[]
	for depth:float in [-1.8,0.,1.4]:
		for along:float in [-.8,0.,.8]:
			# The v35 window sheet has a horizontal lower face at 0.10 m.
			# Start below this face to measure the structural floor itself in both scenes.
			var g:=cast(local(along,depth,.08),local(along,depth,-.28))
			rays.append({"type":"support","pass":not g.is_empty() and absf(g.p[1])<.03,"hit":g})
	for h:float in [.3,1.6,2.4]:
		for along:float in [-.9,-.57,0.,.9]:
			var x:=cast(local(along,-.3,h),local(along,.30,h))
			rays.append({"type":"opening","pass":x.is_empty() if not normal else not x.is_empty(),"lat":along,"h":h,"hit":x})
	for along:float in [-1.4,1.4]:
		var x:=cast(local(along,-.3,1.5),local(along,.30,1.5))
		rays.append({"type":"sidelight_guard","pass":not x.is_empty(),"hit":x})
	if not capture_mode:
		if not normal:
			await walk("centre to main sales aisle",local(0.,-3.),[local(0.,1.5),local(.18,3.75)])
			await walk("reverse from sales aisle to public floor",local(.18,3.75),[local(0.,1.5),local(0.,-3.)])
			for side:float in [-.77,.77]:
				await walk("edge %s" % side,local(side,-2.6),[local(side,1.3),local(.15,1.65)])
		var step:=local(-9.45,-1.5)
		var old:Array=game.read_json("res://source/v32/proposals/B032-entry-option.json").existing_automatic_walk
		var points:Array=[]
		for pp:Array in old:points.append(game.v3(pp))
		await walk("retained original entry to rear",step,points)
	var writes:=FileAccess.open(output+".json",FileAccess.WRITE)
	var passes:int=rays.filter(func(v):return v.pass).size()
	writes.store_string(JSON.stringify({"normal_map":normal,"automated_physics":true,"real_human_walk":false,"rays":rays,"passed_rays":passes,"trials":trials}," "))
	print("B032_STUDY_RESULT ",passes,"/",rays.size())
	game.queue_free()
	await process_frame
	await physics_frame
	quit(0 if passes==rays.size() and trials.all(func(t):return t.result.pass) else 1)
