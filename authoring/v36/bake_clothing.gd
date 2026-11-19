extends SceneTree
func _initialize() -> void:
	var actor: Node3D = load("res://assets/v19/character/shopper-motion.scn").instantiate()
	var piece: MeshInstance3D = actor.find_child("ContinuousClothing", true, false)
	if not piece:
		quit(1)
		return
	var palette := load("res://skin_palette_v19.gd")
	var checks := []
	for i in 6:
		var mesh: ArrayMesh = palette.build_variant(i, piece.mesh)
		var path := "res://assets/v36/shopper-clothing-%d.res" % i
		if ResourceSaver.save(mesh, path, ResourceSaver.FLAG_COMPRESS) != OK:
			quit(1)
			return
		var saved: ArrayMesh = ResourceLoader.load(path,"ArrayMesh",ResourceLoader.CACHE_MODE_IGNORE)
		if saved.surface_get_arrays(0) != mesh.surface_get_arrays(0):
			push_error("Clothing geometry or skin weights changed on save: " + path)
			quit(1)
			return
		checks.append({"style":i,"exact_arrays":true,"vertices":mesh.surface_get_array_len(0)})
	var f := FileAccess.open(OS.get_cmdline_user_args()[0],FileAccess.WRITE)
	f.store_string(JSON.stringify({"source_mesh":piece.mesh.resource_path,"checks":checks}))
	f.close()
	actor.free()
	quit()
