extends SceneTree

var game
var player
var shape := CapsuleShape3D.new()
var space: PhysicsDirectSpaceState3D
var excluded: Array[RID]
var steps_after_settle := 0
func _initialize() -> void:
	call_deferred("inspect")
func vec(a: Array) -> Vector3:
	return Vector3(a[0],a[1],a[2])
func input_w(pressed:bool) -> void:
	var key:=InputEventKey.new()
	key.physical_keycode=KEY_W;key.keycode=KEY_W;key.pressed=pressed
	Input.parse_input_event(key);Input.flush_buffered_events()
func place_player(p:Vector3) -> void:
	input_w(false)
	player.set_physics_process(false)
	player.position=p+Vector3.UP*.035
	player.reset_motion_state()
	player.reset_physics_interpolation()
	player.input_enabled=true
	player.set_physics_process(true)
	steps_after_settle=0
	for i in 10:await physics_frame
func walk_to(target:Vector3,extra:float=.0) -> Dictionary:
	var start:Vector3=player.position
	var forward:=target-start;forward.y=0
	var required:=forward.length()
	forward=forward.normalized()
	player.rotation=Vector3(0,atan2(-forward.x,-forward.z),0)
	player.camera.rotation=Vector3.ZERO
	input_w(true)
	var lost:=0;var ticks:=0
	var wall_contacts:Dictionary={};var trace:Array=[];var cross_track:=0.0
	var line_origin:=Vector2(start.x,start.z);var line_dir:=Vector2(forward.x,forward.z)
	for i in ceili((required+2)*34):
		# Steer on the real floor while turning, including the controller's retained lateral momentum on the previous segment.
		var sight:Vector3=target-player.position
		player.rotation.y=atan2(-sight.x,-sight.z)
		await physics_frame
		ticks+=1
		steps_after_settle+=1
		var where:=Vector2(player.position.x,player.position.z)
		cross_track=maxf(cross_track,absf((where-line_origin).cross(line_dir)))
		if i%12==0:trace.append([snappedf(where.x,.001),snappedf(where.y,.001)])
		for j in player.get_slide_collision_count():
			var hit:KinematicCollision3D=player.get_slide_collision(j)
			if hit.get_normal().y<.4 and hit.get_collider()!=null:
				var host:String=str(hit.get_collider().name)
				if not wall_contacts.has(host):wall_contacts[host]={"first_tick":ticks,"point":[where.x,where.y]}
		if not player.is_on_floor():lost+=1
		var left:=Vector2(target.x-player.position.x,target.z-player.position.z).length()
		if left<=.095+extra:break
	input_w(false)
	var actual:=Vector2(start.x-player.position.x,start.z-player.position.z).length()
	var error:=Vector2(target.x-player.position.x,target.z-player.position.z).length()
	return {"start":[start.x,start.y,start.z],"goal":[target.x,target.y,target.z],"metres":snappedf(actual,.001),"ticks":ticks,"trace_xz_12ticks":trace,"max_cross_track_m":snappedf(cross_track,.001),"nonfloor_contacts":wall_contacts,"lost_floor_frames":lost,"end_error":snappedf(error,.001),"pass":error<=.155+extra and lost==0}
func clear_surface(p:Vector3) -> bool:
	var h:=space.intersect_ray(PhysicsRayQueryParameters3D.create(p+Vector3.UP*.13,p-Vector3.UP*.14,1,excluded))
	if h.is_empty() or h.normal.y<.98 or absf(p.y-h.position.y)>.05:return false
	var q:=PhysicsShapeQueryParameters3D.new()
	q.shape=shape;q.transform=Transform3D(Basis.IDENTITY,p+Vector3.UP*.94);q.exclude=excluded;q.collision_mask=1
	return space.intersect_shape(q,1).is_empty()
func inspect() -> void:
	var args:=OS.get_cmdline_user_args()
	var design:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://source/v36/anchor-programs.json"))
	var routes:Array=JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	RenderingServer.set_render_loop_enabled(false)
	game=load("res://main.tscn").instantiate();game.mode="qa"
	root.add_child(game)
	while game.results.is_empty():await process_frame
	game.shoppers_v18.set_enabled(false,true)
	player=game.player
	player.set_physics_process(false)
	excluded=[player.get_rid()];shape.radius=.31;shape.height=1.78
	var runtime=game.get_node("V30_Runtime");runtime.stream_ready=false
	var registry=game.get_node("V35_Mall_Art/V36_Store_Studios")
	var results:=[];var all_ok:=true
	for room:Dictionary in design.rooms:
		var result:Dictionary={"id":room.id,"stations":[],"trails":[]}
		var start:=vec(room.placements[0].p)
		player.position=start;runtime.prepare_position(start)
		game.get_node("V31_Sales").update_near()
		game.get_node("V34_Mall_Art").update_near()
		game.get_node("V35_Mall_Art").update_near()
		registry.update_near()
		await physics_frame;await physics_frame
		space=player.get_world_3d().direct_space_state
		for station:Dictionary in room.placements:
			var node=registry.resident.get(room.id+"/"+station.role)
			var program:Dictionary=design.models[station.program]
			var st:Dictionary={"role":station.role,"program":station.program,"model":node!=null and node.get_child(0).mesh!=null,"collision_shapes":0,"campaign_images":0,"clear_samples":0,"walk":{}}
			if node!=null:
				for child in node.get_children():
					if child is CollisionShape3D and child.shape!=null:st.collision_shapes+=1
					if child is MeshInstance3D and child.mesh is QuadMesh:
						if child.mesh.material.albedo_texture!=null:st.campaign_images+=1
			var verified:bool=st.model and st.collision_shapes==program.solids.size() and st.campaign_images==program.get("posters",[]).size()
			if station.role!="floor_finish":
				var mat:=Transform3D(Basis(Vector3.UP,station.yaw),vec(station.p))
				for x in [-2.7,-1.8,-.9,0.,.9,1.8,2.7]:
					for z in [2.67,2.94]:
						if clear_surface(mat*Vector3(x,0,z)):st.clear_samples+=1
				await place_player(mat*Vector3(-2.64,0,2.77))
				st.walk=await walk_to(mat*Vector3(2.64,0,2.77))
				verified=verified and st.clear_samples==14 and st.walk.pass
			st.pass=verified;all_ok=all_ok and verified
			result.stations.append(st)
		var trail=routes.filter(func(r):return r.id==room.id)[0]
		var marks:Array=trail.entrance_path.duplicate(true)
		marks.append_array(trail.department_path.slice(1))
		await place_player(Vector3(marks[0][0],start.y,marks[0][1]))
		for i in range(1,marks.size()):
			var dest:=Vector3(marks[i][0],start.y,marks[i][1])
			var run:Dictionary=await walk_to(dest)
			result.trails.append(run)
			all_ok=all_ok and bool(run.pass)
			if not run.pass:break
		player.set_physics_process(false)
		results.append(result)
	var file:=FileAccess.open(args[1],FileAccess.WRITE)
	file.store_string(JSON.stringify({"all_pass":all_ok,"method":"normal CharacterBody3D with physical W input, native physics; no scripted position changes between route waypoints","results":results}," "));file.close()
	print("ANCHOR_WALKS ",all_ok)
	quit(0 if all_ok else 1)
