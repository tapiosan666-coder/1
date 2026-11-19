extends SceneTree

const TARGET := "res://assets/v36/studios/"
const FINISHES := ["veneers", "metal", "paper", "diffuser", "grained_oak"]
var finishes: Array[Material] = []

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 1:
		printerr("Pass the directory containing model.py output.")
		quit(1)
		return
	for kind in FINISHES:
		var m := StandardMaterial3D.new()
		m.resource_name = "Studio " + kind
		m.vertex_color_use_as_albedo = true
		m.roughness = .57
		if kind == "metal":
			m.metallic = .70
			m.roughness = .36
		elif kind == "paper":
			m.albedo_texture = load(TARGET+"edition-cards.webp")
			m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
			m.roughness = .68
		elif kind == "grained_oak":
			m.albedo_texture = load("res://assets/v10/wood-oak.png")
			m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
			m.albedo_color = Color(1.8,1.8,1.8,1)
		elif kind == "diffuser":
			m.emission_enabled = true
			m.emission = Color("#ffedcb")
			m.emission_energy_multiplier = .62
		var path: String = TARGET + kind + ".tres"
		if ResourceSaver.save(m,path,ResourceSaver.FLAG_CHANGE_PATH) != OK:
			quit(2)
			return
		finishes.append(m)
	var count := 0
	for file_name: String in DirAccess.get_files_at(args[0]):
		if file_name.get_extension() != "bin":
			continue
		var f := FileAccess.open(args[0].path_join(file_name),FileAccess.READ)
		var mesh := ArrayMesh.new()
		for surface in FINISHES.size():
			var count_vertices := f.get_32()
			if count_vertices == 0:
				continue
			var bytes := f.get_buffer(count_vertices * 36)
			var vertices := PackedVector3Array()
			var normals := PackedVector3Array()
			var colors := PackedColorArray()
			var texcoords := PackedVector2Array()
			vertices.resize(count_vertices)
			normals.resize(count_vertices)
			colors.resize(count_vertices)
			texcoords.resize(count_vertices)
			for j in count_vertices:
				var off := j*36
				vertices[j] = Vector3(bytes.decode_float(off),bytes.decode_float(off+4),bytes.decode_float(off+8))
				normals[j] = Vector3(bytes.decode_float(off+12),bytes.decode_float(off+16),bytes.decode_float(off+20))
				colors[j] = Color8(bytes[off+24],bytes[off+25],bytes[off+26],bytes[off+27]).srgb_to_linear()
				texcoords[j] = Vector2(bytes.decode_float(off+28),bytes.decode_float(off+32))
			var arrays := []
			arrays.resize(Mesh.ARRAY_MAX)
			arrays[Mesh.ARRAY_VERTEX] = vertices
			arrays[Mesh.ARRAY_NORMAL] = normals
			arrays[Mesh.ARRAY_COLOR] = colors
			arrays[Mesh.ARRAY_TEX_UV] = texcoords
			var tool := SurfaceTool.new()
			tool.create_from_arrays(arrays)
			tool.set_material(finishes[surface])
			tool.index()
			tool.commit(mesh)
		var path := TARGET + file_name.get_basename() + ".res"
		if f.get_position() != f.get_length() or ResourceSaver.save(mesh,path,ResourceSaver.FLAG_COMPRESS) != OK:
			printerr("Mesh export failed ",path)
			quit(2)
			return
		count += 1
	print("BAKED_STUDIO_MESHES ",count)
	quit(0)
