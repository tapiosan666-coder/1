extends SceneTree
func _initialize()->void:call_deferred("capture")
func capture()->void:
	if DisplayServer.get_name()=="headless":quit(2);return
	var stage:=Node3D.new();root.add_child(stage)
	var env:=WorldEnvironment.new();var settings:=Environment.new();settings.background_mode=Environment.BG_COLOR;settings.background_color=Color("b1bdc2");settings.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;settings.ambient_light_color=Color("dde4ec");settings.ambient_light_energy=.38;settings.tonemap_mode=Environment.TONE_MAPPER_FILMIC;env.environment=settings;stage.add_child(env)
	var sun:=DirectionalLight3D.new();sun.rotation_degrees=Vector3(-58,-24,0);sun.light_energy=.8;sun.light_color=Color("fff0d1");sun.shadow_enabled=true;sun.directional_shadow_max_distance=40;stage.add_child(sun)
	var world_path:="/tmp/fy15-baseline/assets/world/mall.scn" if "--comparison-world" in OS.get_cmdline_user_args() else "res://assets/world/mall.scn"
	var world:Node3D=load(world_path).instantiate();stage.add_child(world)
	var points:Array[Vector3]=[];points.assign(world.get_meta("spawn_points"))
	WorldCache.navigation={"hash":hash(points),"positions":world.get_meta("nav_positions"),"edges":world.get_meta("nav_edges")}
	var camera:=Camera3D.new();camera.fov=50;camera.current=true;stage.add_child(camera)
	var crowd:=Crowd.new();stage.add_child(crowd);crowd.setup(IdentityRun.new(1,912),points);crowd.set_physics_process(false)
	crowd.positions[0]=Vector3(-57,0,-13);crowd.headings[0]=PI;crowd.waits[0]=30;crowd.roles[0]="walking"
	var tag:="before" if "--before" in OS.get_cmdline_user_args() else "after"
	var portrait:="--portrait-pass" in OS.get_cmdline_user_args()
	var shots:Array=[
	 ["body",Vector3(-57,1.36,-9.9),Vector3(-57,1.05,-13),"walking",false,.4],
	 ["side",Vector3(-54.1,1.35,-12.5),Vector3(-57,1.05,-13),"walking",false,.4],
	 ["three-quarter",Vector3(-55.0,1.42,-10.2),Vector3(-57,1.10,-13),"walking",false,.4],
	 ["face",Vector3(-57,1.7,-11.7),Vector3(-57,1.7,-13),"walking",false,.4],
	 ["walk",Vector3(-55.5,1.36,-9.9),Vector3(-57,1.05,-13),"walking",true,.83],
	 ["seated",Vector3(-55.3,1.15,-10.1),Vector3(-57,.90,-13),"seated",false,.4]
	]
	if portrait:
		camera.fov=42
		shots=[
		 ["face",Vector3(-57,1.7,-12.2),Vector3(-57,1.7,-13),"walking",false,.4],
		 ["profile",Vector3(-55.95,1.7,-12.85),Vector3(-57,1.7,-13),"walking",false,.4],
		 ["talk",Vector3(-57,1.7,-12.2),Vector3(-57,1.7,-13),"conversation",false,1.35],
		 ["upper-body",Vector3(-56.0,1.57,-11.5),Vector3(-57,1.37,-13),"walking",false,.4]
		]
	for shot:Array in shots:
		crowd.roles[0]=shot[3];crowd.activities[0]="food_wait" if shot[3]=="seated" else "walking";crowd.clock=shot[5]
		crowd.waits[0]=0 if shot[4] else 30;crowd.paths[0]=PackedVector3Array([crowd.positions[0]+Vector3.BACK*5]) if shot[4] else PackedVector3Array()
		camera.position=shot[1];camera.look_at(shot[2]);crowd._render()
		await create_timer(.3).timeout;await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/%s-%s-%s.png"%["fy16" if portrait else "fy15",tag,shot[0]])
		print("CIVILIAN_PREVIEW ",tag," ",shot[0])
	quit()
