extends SceneTree
var rig: Node3D
func output_path() -> String:
	for argument: String in OS.get_cmdline_user_args():
		if argument.begins_with("--out="):
			return argument.trim_prefix("--out=")
	return "user://es-render-motion-v36.json"
func _initialize() -> void:
	call_deferred("run")
func xyz(p: Vector3) -> Array:
	return [p.x,p.y,p.z]
func motion_resource(e: Dictionary) -> Dictionary:
	var animator := rig as Node
	animator.ensure_near(Vector3(e.c[0],e.low_y,e.c[2]))
	var bank: Dictionary
	for b: Dictionary in animator.banks:
		if b.id == e.id:
			bank = b
			break
	var instance: int = roundi(float(bank.count) * .20)
	var step_seconds := .30
	var start_time := 1.2
	animator.update_bank(bank,start_time)
	var old_offset := float(bank.rubber.get_shader_parameter("belt_offset"))
	var p: Vector3 = bank.multimesh.get_instance_transform(instance).origin
	animator.update_bank(bank,start_time + step_seconds)
	var new_offset := float(bank.rubber.get_shader_parameter("belt_offset"))
	var q: Vector3 = bank.multimesh.get_instance_transform(instance).origin
	var direction := 1. if e.direction == "UP" else -1.
	var speed := float(animator.speed)
	var path_m := (q-p).length()
	var belt_m := (new_offset-old_offset)*direction
	return {"id":e.id,"physical_tread_sample_index":instance,"tread_before_xyz":xyz(p),"tread_after_xyz":xyz(q),
		"renderer":RenderingServer.get_current_rendering_method(),"interval_s":step_seconds,"surface_speed_m_s":speed,
		"signed_rubber_uv_displacement_m":new_offset-old_offset,"sampled_tread_distance_m":path_m,
		"pass":(q.z-p.z)*direction > .1 and (q.y-p.y)*direction > .025 and absf(path_m-step_seconds*speed)<.008 and absf(belt_m-step_seconds*speed)<.001}

func run() -> void:
	RenderingServer.set_render_loop_enabled(false)
	var game: Node3D = load("res://main.gd").new()
	game.build_materials()
	var manifest: Dictionary = game.read_json("res://assets/v30/world/context.json").manifest
	rig = load("res://escalator_v2.gd").new()
	rig.paused = true
	root.add_child(rig)
	rig.setup(manifest, game.mats)
	var rows: Array[Dictionary] = []
	for flight: Dictionary in manifest.escalators:
		rows.append(motion_resource(flight))
	var passed := rows.filter(func(r): return r.pass).size()
	var shape_inventory: Array = []
	for size_key: Vector2 in rig.shared_machines:
		var resources: Dictionary = rig.shared_machines[size_key]
		var casing: ArrayMesh = resources["case"]
		var rail: ArrayMesh = resources["rail"]
		var glass_faces := 0
		for index: int in casing.get_surface_count():
			if casing.surface_get_material(index) == rig.laminated_glass:
				glass_faces += int(casing.surface_get_array_index_len(index) / 3.)
		shape_inventory.append({"rise":size_key.x,"run":size_key.y,"pane_triangles":glass_faces,
			"rubber_triangles_both_sides":int(rail.surface_get_array_index_len(0)/3.),"case_surfaces_including_glass":casing.get_surface_count()})
	var report := {"shared_machine_geometry":shape_inventory,"all":rows.size(),"pass_count":passed,"rows":rows,"human_playtest":false,"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"method":"Actual Forward+ MultiMesh instance transform and moving handrail shader parameter at 1.2 and 1.5 seconds of the shipped animation update for each flight. This is GPU-facing motion data, not 42 visually reviewed clips."}
	var f := FileAccess.open(output_path(),FileAccess.WRITE)
	f.store_string(JSON.stringify(report," "))
	f.close()
	print("ES36_ANIMATION ",passed,"/",rows.size())
	rig.queue_free()
	game.free()
	await process_frame
	quit(0 if passed == rows.size() else 1)
