extends SceneTree
## Diagnostic view of the installed landings inside the full streamed building.
## Only the two inspected material IDs change. Architecture still participates in depth.
var game: Node3D
var camera: Camera3D
var fixed_mark: StandardMaterial3D
var moving_mark: StandardMaterial3D
var dest := "user://es-landing-visibility"
var machine_limit := 1000
var selected_prefix := ""

func _initialize() -> void:
	call_deferred("run")

func marker(colour: Color) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = colour
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	return material

func tagged_pixel(image: Image, world: Vector3) -> String:
	var uv := Vector2i(camera.unproject_position(world))
	if not Rect2i(Vector2i.ZERO,image.get_size()).has_point(uv): return "offscreen"
	var c := image.get_pixelv(uv)
	if c.r > .56 and c.b > .56 and c.g < .34: return "fixed"
	if c.g > .51 and c.r < .40 and c.b < .40: return "moving"
	return "other"

func inspect(bank: Dictionary, side: int) -> Dictionary:
	var axis: Vector3 = bank.u
	var lateral: Vector3 = bank.x
	var level: Vector3 = bank.c + Vector3.UP*(float(bank.rise) if side>0 else 0.) + axis*side*float(bank.run)*.5
	var target := level + axis*side*.81
	game.player.global_position = target
	game.player.reset_physics_interpolation()
	var stream: Node = game.get_node("V30_Runtime")
	await stream.settle()
	game.get_node("V31_Sales").update_near()
	camera.global_position = target + Vector3.UP * 1.9
	camera.look_at(target, axis)
	camera.reset_physics_interpolation()
	camera.force_update_transform()
	var sets := []
	var pass_all := true
	for t: float in [0.,.21,.42]:
		game.animator.set_time(t)
		RenderingServer.set_render_loop_enabled(true)
		await process_frame
		await RenderingServer.frame_post_draw
		var picture := root.get_texture().get_image()
		RenderingServer.set_render_loop_enabled(false)
		var deck := {"moving":0,"fixed":0,"other":0,"offscreen":0}
		var plate := deck.duplicate()
		for offset: float in [-.47,-.16,.16,.47]:
			for depth: float in [.11,.27,.43,.60]:
				var tag := tagged_pixel(picture,level + axis*side*depth + lateral*offset + Vector3.UP*.026)
				deck[tag] += 1
			for depth: float in [.93,1.11,1.32,1.47,1.57]:
				var tag := tagged_pixel(picture,level + axis*side*depth + lateral*offset + Vector3.UP*.036)
				plate[tag] += 1
		var passed: bool = deck.moving >= 12 and deck.other+deck.offscreen == 0 and plate.fixed==20
		pass_all = pass_all and passed
		if (not passed or bank.id=="B-WEST-V15-0-UP") and is_zero_approx(t):
			picture.save_png(dest.path_join("%s-%d.png" % [bank.id,side]))
		sets.append({"time":t,"exposed_tread_points":deck,"fixed_access_plate_points":plate,"pass":passed})
	return {"machine":bank.id,"end":"upper" if side>0 else "lower","measured":sets,"pass":pass_all}

func run() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--out="): dest=arg.trim_prefix("--out=")
		if arg.begins_with("--only="): selected_prefix=arg.trim_prefix("--only=")
		if arg.begins_with("--limit="): machine_limit=int(arg.trim_prefix("--limit="))
	DirAccess.make_dir_recursive_absolute(dest)
	RenderingServer.set_render_loop_enabled(false)
	game=load("res://main.tscn").instantiate()
	root.add_child(game)
	while game.results.is_empty(): await process_frame
	if game.results.get("startup_failed",false): quit(1); return
	game.player.set_physics_process(false)
	game.player.input_enabled=false
	game.shoppers_v18.set_enabled(false,true)
	game.hud.get_parent().hide()
	game.animator.paused=true
	camera=Camera3D.new()
	game.add_child(camera)
	camera.set_orthogonal(2.45,1.61,2.28)
	camera.physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF
	var environment := Environment.new()
	environment.background_mode=Environment.BG_COLOR
	environment.background_color=Color.BLACK
	environment.tonemap_mode=Environment.TONE_MAPPER_LINEAR
	camera.environment=environment
	camera.make_current()
	fixed_mark=marker(Color(1,0,1))
	moving_mark=marker(Color(0,1,0))
	root.content_scale_mode=Window.CONTENT_SCALE_MODE_DISABLED
	root.size=Vector2i(256,256)
	root.content_scale_size=root.size
	root.scaling_3d_scale=1.
	var rows := []
	var machines := 0
	for data: Dictionary in game.animator.definitions:
		if not selected_prefix.is_empty() and not str(data.id).begins_with(selected_prefix):continue
		game.animator.ensure_near(Vector3(data.c[0],data.low_y,data.c[2]))
		var bank: Dictionary
		for record: Dictionary in game.animator.banks:
			if record.id == data.id: bank=record; break
		var assembly: Node3D = bank.assembly
		var casing: MeshInstance3D = assembly.get_child(0).get_child(1)
		var treads: MultiMeshInstance3D = assembly.get_node(str(bank.id)+"_moving_treads")
		casing.set_surface_override_material(1,fixed_mark)
		treads.material_override=moving_mark
		for side: int in [-1,1]:
			var result := await inspect(bank,side)
			rows.append(result)
			print("V36_INSTALLED_PLATE ",bank.id," ",side," ",result)
		machines+=1
		if machines>=machine_limit: break
	var passed := rows.filter(func(r):return r["pass"]).size()
	var report := {"passes":passed,"landings":rows.size(),"machines":machines,"rows":rows,"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"scope":"Building and public-floor depth rendered in a 0.67 m vertical section. Diagnostic material IDs on real tread and stationary cover alone. Sampling 16 exposed-tread and 20 stationary-cover points at 3 phases per landing. The unmodified art is photographed separately."}
	FileAccess.open(dest.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(report," "))
	game.queue_free()
	await process_frame
	quit(0 if passed==rows.size() else 1)
