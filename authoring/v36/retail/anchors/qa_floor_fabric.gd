extends SceneTree
var g
func _initialize() -> void:
	call_deferred("run")
func run() -> void:
	var output:=OS.get_cmdline_user_args()[0]
	RenderingServer.set_render_loop_enabled(false)
	g=load("res://main.tscn").instantiate()
	g.mode="qa"
	root.add_child(g)
	while g.results.is_empty():await process_frame
	g.player.set_physics_process(false)
	g.shoppers_v18.set_enabled(false,true)
	var runtime=g.get_node("V30_Runtime")
	runtime.stream_ready=false
	var floors:Dictionary={}
	var excluded:Array[RID]=[g.player.get_rid()]
	var capsule:=CapsuleShape3D.new();capsule.radius=.37;capsule.height=1.75
	var q:=PhysicsShapeQueryParameters3D.new();q.shape=capsule;q.exclude=excluded;q.collision_mask=1
	for level:Array in [["AB1-001",-5.348],["A2F-001",5.527],["A3F-001",10.877]]:
		var eye:=Vector3(437,level[1],0)
		g.player.position=eye
		runtime.prepare_position(eye)
		for name:String in ["V31_Sales","V34_Mall_Art","V35_Mall_Art","V35_Mall_Art/V36_Store_Studios"]:
			g.get_node(name).update_near()
		await physics_frame;await physics_frame
		var space:PhysicsDirectSpaceState3D=g.player.get_world_3d().direct_space_state
		var sampled: Array=[]
		for x in range(412,458):
			for z in range(-29,35):
				var p:=Vector3(x,level[1],z)
				var hit:=space.intersect_ray(PhysicsRayQueryParameters3D.create(p+Vector3.UP*.18,p-Vector3.UP*.16,1,excluded))
				if hit.is_empty() or hit.normal.y<.98 or absf(hit.position.y-level[1])>.038:continue
				q.transform=Transform3D(Basis.IDENTITY,p+Vector3.UP*.94)
				sampled.append([x,z,snappedf(hit.position.y,.001),space.intersect_shape(q,1).is_empty()])
		floors[level[0]]=sampled
	var f:=FileAccess.open(output,FileAccess.WRITE);f.store_string(JSON.stringify(floors));f.close()
	print("ANCHOR_FLOOR_FABRIC ",floors.size())
	quit()
