extends SceneTree
## Mechanical mesh cross-sections and the GPU-facing transforms of all installed machines.
var mechanical: Node3D

func _initialize() -> void:
	call_deferred("run")

func setting(name: String, fallback: String) -> String:
	for a: String in OS.get_cmdline_user_args():
		if a.begins_with(name + "="): return a.trim_prefix(name + "=")
	return fallback

func top_of_casing(faces: PackedVector3Array, x: float, z: float) -> float:
	var p := Vector2(x,z)
	var result := -INF
	for j: int in range(0,faces.size(),3):
		var a := faces[j]
		var b := faces[j+1]
		var c := faces[j+2]
		var u := Vector2(b.x-a.x,b.z-a.z)
		var v := Vector2(c.x-a.x,c.z-a.z)
		var w := p - Vector2(a.x,a.z)
		var d := u.cross(v)
		if absf(d) < .0000001: continue
		var s := w.cross(v)/d
		var t := u.cross(w)/d
		if s >= -.0001 and t >= -.0001 and s+t <= 1.0001:
			result = maxf(result, a.y + s*(b.y-a.y) + t*(c.y-a.y))
	return result

func geometry(bank: Dictionary, casing: Mesh) -> Array:
	var faces := casing.get_faces()
	var rows: Array = []
	for side: int in [-1,1]:
		var level := 0. if side<0 else float(bank.rise)
		for along: float in [.08,.40,.61,.76,1.10,1.32,1.50,1.62]:
			var sample := top_of_casing(faces,.127,side*(float(bank.run)*.5+along))-level
			var correct := false
			if along < .70: correct = sample>.010 and sample<.017
			elif along<1.42:correct = sample>.036 and sample<.047
			else: correct = sample>.007 and sample<.039
			rows.append({"end":side,"offset_m":along,"fixed_surface_height":sample,"expected_face": "understep bed" if along<.70 else ("service cover" if along<1.42 else "feathered outer sill"),"pass":correct})
	return rows

func larger_gap(spans: Array[Vector2], low: float, high: float) -> float:
	spans.sort_custom(func(a,b):return a.x < b.x)
	var cursor := low
	var worst := 0.
	for pair: Vector2 in spans:
		if pair.y < low or pair.x > high: continue
		worst=maxf(worst, minf(high,pair.x)-cursor)
		cursor=maxf(cursor,pair.y)
	return maxf(worst, high-cursor)

func measure_bank(bank: Dictionary, casing: Array) -> Dictionary:
	var half := float(bank.run)*.5
	var inset := .72
	var largest := 0.
	var minimum_headroom := INF
	var max_return_above_truss_middle := 0.
	var minimum_public_tread := INF
	var guard_count := 0
	var touched_lo := false
	var touched_hi := false
	var full_cycle := float(bank.length)/float(mechanical.speed)
	# For identical production steps, one pitch advances each individual position
	# into the neighbouring instance. Also inspect a full chain revolution to catch
	# wrap-around, including the same physical step returning to its starting slot.
	var times: Array[float] = []
	for i: int in 129: times.append(float(bank.pitch)/float(mechanical.speed)*i/128.)
	for i: int in 65: times.append(full_cycle*i/64.)
	var initial_origin := Vector3.ZERO
	var end_origin := Vector3.ZERO
	for index in times.size():
		mechanical.update_bank(bank,times[index])
		var values: PackedFloat32Array = bank.multimesh.buffer
		var low_spans: Array[Vector2] = []
		var high_spans: Array[Vector2] = []
		for i: int in bank.count:
			var n := i*12
			var z := float(values[n+11])
			var y := float(values[n+7])
			if i==0:
				if index==0: initial_origin=Vector3(values[n+3],y,z)
				if index==times.size()-1: end_origin=Vector3(values[n+3],y,z)
			if float(values[n])<.01:
				# A scaled, hidden return must stay inside the steel truss, not
				# under the casing or through the fixed cover. The +/- 0.001 m
				# bound covers all corners of the actual compressed tread mesh.
				var mid: float = mechanical.height(z,bank)-.38
				max_return_above_truss_middle=maxf(max_return_above_truss_middle,absf(y-mid)+.001)
				continue
			var tread_half_length := .198*absf(float(values[n+10]))
			var lo := z-tread_half_length
			var hi := z+tread_half_length
			low_spans.append(Vector2(-hi-half,-lo-half))
			high_spans.append(Vector2(lo-half,hi-half))
			for side: int in [-1,1]:
				var inner := minf(side*lo,side*hi)-half
				var outer := maxf(side*lo,side*hi)-half
				var level := float(bank.rise) if side>0 else 0.
				if inner<inset and outer>.10:
					minimum_public_tread=minf(minimum_public_tread, y-level-.004)
				if outer>inset and inner<1.42:
					minimum_headroom=minf(minimum_headroom, level+.041-(y+.006))
					guard_count+=1
					if side<0: touched_lo=true
					else: touched_hi=true
		largest=maxf(largest,maxf(larger_gap(low_spans,.08,inset),larger_gap(high_spans,.08,inset)))
	var closure := initial_origin.distance_to(end_origin)
	var ok: bool = casing.all(func(row):return row["pass"]) and largest<.006 and minimum_headroom>.003 and minimum_public_tread>.016 and max_return_above_truss_middle<.01 and touched_lo and touched_hi and closure<.001
	return {"id":bank.id,"pass":ok,"phases":times.size(),"engine_s":full_cycle,"pitch_m":bank.pitch,"treads":bank.count,"largest_tread_joint_flat_m":largest,"min_clearance_below_fixed_cover_m":minimum_headroom,"min_flat_tread_above_floor_m":minimum_public_tread,"max_hidden_return_offset_from_truss_middle_m":max_return_above_truss_middle,"cover_overlap_samples":guard_count,"chain_wrap_error_m":closure,"both_landings_tested":touched_lo and touched_hi}

func run() -> void:
	RenderingServer.set_render_loop_enabled(false)
	var game: Node3D = load("res://main.gd").new()
	game.build_materials()
	var manifest: Dictionary = game.read_json("res://assets/v30/world/context.json").manifest
	mechanical=load("res://escalator_v2.gd").new()
	root.add_child(mechanical)
	mechanical.paused=true
	mechanical.setup(manifest,game.mats)
	var shapes := {}
	var rows := []
	for e: Dictionary in manifest.escalators:
		mechanical.ensure_near(Vector3(e.c[0],e.low_y,e.c[2]))
		var bank: Dictionary
		for b: Dictionary in mechanical.banks:
			if b.id==e.id:bank=b;break
		var key := Vector2(bank.rise,bank.run)
		var name_key := "%.3f x %.3f" % [key.x,key.y]
		if not shapes.has(name_key):
			shapes[name_key]=geometry(bank,mechanical.shared_machines[key]["case"])
		rows.append(measure_bank(bank,shapes[name_key]))
		print("V36_PLATE ",bank.id," ",rows[-1])
	var ok: int=rows.filter(func(r):return r["pass"]).size()
	var result := {"passed":ok,"all":rows.size(),"rows":rows,"fixed_mesh_cross_sections":shapes,"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"scope":"Actual finished mesh cross-sections plus GPU-facing MultiMesh transforms. Winding geometry under the solid skirt is intentionally hidden. This test measures a full pitch at 129 phases and a full chain loop at 65 phases per machine. It does not assert clearance to arbitrary third-party props."}
	FileAccess.open(setting("--out","user://es36-comb-cycle.json"),FileAccess.WRITE).store_string(JSON.stringify(result," "))
	mechanical.queue_free()
	game.free()
	await process_frame
	quit(0 if ok==rows.size() else 1)
