extends SceneTree
## All-device side clearance checks in the normal streamed world.
var game: Node3D
var player: CharacterBody3D
var stream: Node
var capsule: CapsuleShape3D

func _initialize() -> void:
	call_deferred("run")

func arg(name: String, fallback: String) -> String:
	for a: String in OS.get_cmdline_user_args():
		if a.begins_with(name + "="):
			return a.trim_prefix(name + "=")
	return fallback

func point(p: Vector3) -> Array:
	return [p.x, p.y, p.z]

func cast_at(feet: Vector3, motion: Vector3) -> Dictionary:
	var state := player.get_world_3d().direct_space_state
	var q := PhysicsShapeQueryParameters3D.new()
	q.shape = capsule
	q.margin = .002
	q.collision_mask = 1
	q.exclude = [player.get_rid()]
	q.transform = Transform3D(Basis.IDENTITY, feet + Vector3.UP * .90)
	var overlap := state.intersect_shape(q, 3)
	q.motion = motion
	var result := state.cast_motion(q)
	return {"overlap": overlap.map(func(hit): return str(hit.collider.name)), "safe_fraction": result[0] if not result.is_empty() else 1.}

func run() -> void:
	RenderingServer.set_render_loop_enabled(false)
	game = load(ProjectSettings.get_setting("application/run/main_scene")).instantiate()
	game.mode = "v36-ES-side-qa"
	root.add_child(game)
	var began := Time.get_ticks_msec()
	while game.results.is_empty():
		await process_frame
		if Time.get_ticks_msec() - began > 120000:
			quit(1)
			return
	player = game.player
	stream = game.get_node("V30_Runtime")
	player.set_physics_process(false)
	player.input_enabled = false
	game.shoppers_v18.set_enabled(false, true)
	game.animator.paused = true
	game.animator.set_process(false)
	capsule = CapsuleShape3D.new()
	capsule.radius = .30
	capsule.height = 1.80
	var report: Dictionary = {"version": "v36", "rows": [], "complete": false, "human_playtest": false,
		"scope": "Actual world collisions, shipped capsule; inside to outside over both edges at slope trunk and flat end. Overlapping start is reported separately; it is never counted as guard PASS."}
	for es: Dictionary in game.manifest.escalators:
		var centre := Vector3(es.c[0], es.low_y, es.c[2])
		var u := Vector3(es.u[0], 0., es.u[1]).normalized()
		var v := Vector3(-u.z, 0., u.x)
		var half := float(es.run_m) * .5
		var rise: float = es.rise_m
		player.position = centre
		stream.prepare_position(centre)
		for i: int in 3:
			await physics_frame
		for along: float in [-half - .23, -half + .65, -half * .5, 0., half * .5, half - .65, half + .23]:
			var y := rise * clampf(along / float(es.run_m) + .5, 0., 1.)
			var start := centre + u * along + Vector3.UP * (y + .065)
			for side: float in [-1., 1.]:
				var target := v * side * 1.65
				var check := cast_at(start, target)
				var ok: bool = check.overlap.is_empty() and float(check.safe_fraction) < .95
				report.rows.append({"id": es.id, "wing": es.get("wing", "B"), "local_s": along, "side": side,
					"from": point(start), "to": point(start + target), "guard_blocked": ok, "overlap": check.overlap, "safe_fraction": check.safe_fraction})
		print("V36_ES_GUARD ", es.id, " blocked ", report.rows.slice(report.rows.size() - 14).filter(func(r): return r.guard_blocked).size(), "/14")
	report.complete = true
	report.guarded = report.rows.filter(func(r): return r.guard_blocked).size()
	report.not_guarded = report.rows.size() - report.guarded
	report.animation = game.animator.audit()
	var out := FileAccess.open(arg("--out", "user://es-side-guards-v36.json"), FileAccess.WRITE)
	out.store_string(JSON.stringify(report, " "))
	out.close()
	print("V36_ES_GUARDS_COMPLETE ", report.guarded, "/", report.rows.size(), " animation failed ", report.animation.failed)
	game.queue_free()
	await process_frame
	await physics_frame
	quit()
