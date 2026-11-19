extends SceneTree

# The 48 m world cells already batch identical rigid displays with MultiMesh.
# Recover geometric LOD on their shared meshes, using offline meshoptimizer.
# The normal-distance mesh byte buffers and the separate physics files are preserved.
const LIBRARY := "res://assets/v30/world/meshes"
const MIN_FILE_BYTES := 16384
const MIN_INDICES := 1536
const MAX_EXTENT_M := 16.0

func _initialize() -> void:
	var records := []
	var failures := 0
	for file in DirAccess.get_files_at(LIBRARY):
		if not file.ends_with(".res"):
			continue
		var path := LIBRARY.path_join(file)
		var size := FileAccess.get_size(path)
		if size < MIN_FILE_BYTES:
			continue
		var mesh: ArrayMesh = load(path) as ArrayMesh
		if not mesh or mesh.get_blend_shape_count() or mesh.get_aabb().size.length() > MAX_EXTENT_M:
			continue
		var originals: Array = mesh.get("_surfaces")
		if originals.is_empty(): continue
		var builder := ImporterMesh.new()
		var valid := true
		var base_indices := 0
		for si in originals.size():
			var surface: Dictionary = originals[si]
			if surface.has("lods") or int(surface.primitive) != Mesh.PRIMITIVE_TRIANGLES or int(surface.get("index_count", 0)) == 0:
				valid = false
				break
			builder.add_surface(Mesh.PRIMITIVE_TRIANGLES, mesh.surface_get_arrays(si), [], {}, mesh.surface_get_material(si))
			base_indices += int(surface.index_count)
		if not valid or base_indices < MIN_INDICES: continue
		builder.generate_lods(25., 60., [])
		var reduced: ArrayMesh = builder.get_mesh()
		var generated: Array = reduced.get("_surfaces")
		var levels := 0
		for si in originals.size():
			var arrays := mesh.surface_get_arrays(si)
			var output := reduced.surface_get_arrays(si)
			# Only use decimated indices when they address the same original
			# vertices. Never replace original normals, UVs, tangent or colors.
			if arrays[Mesh.ARRAY_VERTEX] != output[Mesh.ARRAY_VERTEX] or arrays[Mesh.ARRAY_INDEX] != output[Mesh.ARRAY_INDEX]:
				continue
			var source_lods: Array = generated[si].get("lods", [])
			var indices_per_vertex := 2 if int(originals[si].vertex_count) <= 65536 else 4
			var lods := []
			for k in range(0, source_lods.size(), 2):
				if source_lods[k+1].size() / indices_per_vertex < maxf(96., originals[si].index_count * .055):
					break
				lods.append(source_lods[k])
				lods.append(source_lods[k+1])
			if not lods.is_empty():
				originals[si].lods = lods
				levels += lods.size() / 2
		if levels == 0: continue
		mesh.clear_surfaces()
		mesh.set("_surfaces", originals)
		var save_error := ResourceSaver.save(mesh, path, ResourceSaver.FLAG_COMPRESS)
		if save_error != OK:
			push_error("LOD write failed: " + path)
			failures += 1
			continue
		var rebound: ArrayMesh = ResourceLoader.load(path, "ArrayMesh", ResourceLoader.CACHE_MODE_IGNORE)
		var saved: Array = rebound.get("_surfaces")
		for si in originals.size():
			for field: String in ["format","primitive","vertex_data","vertex_count","attribute_data","skin_data","aabb","uv_scale","index_data","index_count","lods"]:
				if saved[si].get(field) != originals[si].get(field):
					push_error("LOD serialization altered " + field + " in " + path)
					failures += 1
		records.append({"file":file,"original_triangles":base_indices/3,"screen_error_levels":levels,"added_bytes":FileAccess.get_size(path)-size})
	var report := FileAccess.open(OS.get_cmdline_user_args()[0],FileAccess.WRITE)
	report.store_string(JSON.stringify({"failures":failures,"meshes":records}," "))
	report.close()
	print("Shared rigid meshes with distance LOD: ", records.size(), "; failures ", failures)
	quit(1 if failures else 0)
