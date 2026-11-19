extends SceneTree

var game
var world: PhysicsDirectSpaceState3D
var exclude: Array[RID]
var box := BoxShape3D.new()
var capsule := CapsuleShape3D.new()
func _initialize() -> void:
	call_deferred("run")
func vec(a: Array) -> Vector3:
	return Vector3(a[0],a[1],a[2])
func touch(p: Vector3, rotation_y: float, shape: Shape3D) -> String:
	var q := PhysicsShapeQueryParameters3D.new()
	q.shape = shape
	q.collision_mask = 1
	q.transform = Transform3D(Basis(Vector3.UP,rotation_y),p)
	q.exclude = exclude
	var contact := world.intersect_shape(q,1)
	return str(contact[0].collider.name) if not contact.is_empty() else ""
func supported(p:Vector3) -> bool:
	var hit:=world.intersect_ray(PhysicsRayQueryParameters3D.create(p+Vector3.UP*.13,p-Vector3.UP*.14,1,exclude))
	return not hit.is_empty() and hit.normal.y>.99 and absf(p.y-hit.position.y)<.14
func run() -> void:
	var args:=OS.get_cmdline_user_args()
	var design: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	var out: String = args[1]
	var check_new: bool=args.size()>2 and args[2]=="with-install"
	RenderingServer.set_render_loop_enabled(false)
	game=load("res://main.tscn").instantiate()
	game.mode="qa"
	root.add_child(game)
	while game.results.is_empty():await process_frame
	game.shoppers_v18.set_enabled(false,true)
	var stream=game.get_node("V30_Runtime")
	stream.stream_ready=false
	var player=game.player
	player.set_physics_process(false)
	exclude=[player.get_rid()]
	capsule.radius=.31;capsule.height=1.77
	var tested:=[]
	for room: Dictionary in design.rooms:
		var heights: Vector3=vec(room.placements[0].p)
		var p := Vector3(36.30,heights.y,-193.74)
		player.global_position=p
		stream.prepare_position(p)
		await physics_frame
		await physics_frame
		world=player.get_world_3d().direct_space_state
		var row: Dictionary={"id":room.id,"floor_supported":[],"solid_conflicts":[],"visitor_lanes":[],"furniture_loaded":[],"walk":{}}
		if check_new:
			var registry=game.get_node("V35_Mall_Art/V36_Store_Studios")
			registry.update_near()
			for station: Dictionary in room.placements:
				row.furniture_loaded.append(registry.resident.has(room.id+"/"+station.role))
		for set:Dictionary in room.placements:
			var mat := Transform3D(Basis(Vector3.UP,float(set.yaw)),vec(set.p))
			for solid:Dictionary in design.models[set.program].solids:
				var center:Vector3=mat*vec(solid.p)
				var feet:=Vector3(center.x,p.y,center.z)
				if not check_new:
					var grounded:=supported(feet)
					row.floor_supported.append(grounded)
					# Shrink touching tolerance at the support floor and test at the
					# designed vertical intervals, not a solid bounding rectangle.
					var sz:=vec(solid.size)
					box.size=Vector3(maxf(.014,sz.x-.025),maxf(.014,sz.y-.035),maxf(.014,sz.z-.025))
					var blocker:=touch(center+Vector3.UP*.025,float(set.yaw)+float(solid.yaw),box)
					if not blocker.is_empty():row.solid_conflicts.append([set.role,blocker,solid.p])
		# The aisle stays clear for two passing visitors. Additional lateral
		# samples cover access from the aisle to the checkout and seating.
		for x: float in [35.71,36.30,36.89]:
			for z:float in [-194.1,-192.2,-190.2,-188.2,-186.2,-184.2,-182.2,-180.2,-178.2,-176.8]:
				var point:=Vector3(x,p.y,z)
				row.visitor_lanes.append(supported(point) and touch(point+Vector3.UP*.95,0,capsule).is_empty())
		for z: float in [-192.4,-188.2,-176.9]:
			for x: float in [28.,30.,32.,34.,38.,40.,42.,44.]:
				var point:=Vector3(x,p.y,z)
				var contact:=touch(point+Vector3.UP*.96,0,capsule)
				row.get_or_add("side_access_samples",[]).append({"x":x,"z":z,"clear":supported(point) and contact.is_empty()})
		if check_new:
			player.position=p+Vector3.UP*.032
			player.rotation=Vector3(0,PI,0);player.camera.rotation=Vector3.ZERO
			player.reset_motion_state();player.input_enabled=true;player.set_physics_process(true)
			var w := InputEventKey.new()
			w.physical_keycode=KEY_W;w.keycode=KEY_W;w.pressed=true
			Input.parse_input_event(w);Input.flush_buffered_events()
			var no_floor:=0
			var start_z:float=player.position.z
			var ticks:=0
			for i in 270:
				await physics_frame
				ticks+=1
				if i>5 and not player.is_on_floor():no_floor+=1
				if player.position.z-start_z>14: break
			var up := InputEventKey.new()
			up.physical_keycode=KEY_W;up.keycode=KEY_W;up.pressed=false
			Input.parse_input_event(up);Input.flush_buffered_events()
			player.set_physics_process(false)
			row.walk={"input":"physical W","ticks":ticks,"metres":player.position.z-start_z,"off_floor_ticks_after_settle":no_floor,
				"end":[player.position.x,player.position.y,player.position.z]}
		tested.append(row)
	var f:=FileAccess.open(out,FileAccess.WRITE);f.store_string(JSON.stringify(tested," "));f.close()
	print("DINING_TEST_DONE ",tested.size())
	quit()
