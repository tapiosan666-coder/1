class_name RenderChunks
extends RefCounted
## Merge static triangles by spatial cell and render state; keep all collision intact.
const CELL := Vector3(28,5.35,24)
static var state_properties := ["roughness","metallic","specular_mode","shading_mode","transparency","blend_mode","cull_mode","diffuse_mode","emission_enabled","emission","emission_energy_multiplier","no_depth_test","disable_receive_shadows","albedo_texture","texture_filter","uv1_scale","uv1_offset"]

static func build(root: Node3D) -> Dictionary:
	var material_cache: Dictionary = {}
	var groups: Dictionary = {}
	var sources := root.find_children("*","MeshInstance3D",true,false)
	var input_meshes := 0
	var triangles := 0
	var detail_meshes := 0; var detail_surfaces := 0; var detail_triangles := 0
	for node in sources:
		if not node.is_visible_in_tree() or node.mesh == null: continue
		input_meshes += 1
		if node.get_meta("retail_detail",false):
			detail_meshes += 1; detail_surfaces += node.mesh.get_surface_count()
			for i in node.mesh.get_surface_count():
				var data: Array = node.mesh.surface_get_arrays(i)
				detail_triangles += (data[Mesh.ARRAY_INDEX].size() if data[Mesh.ARRAY_INDEX] != null and not data[Mesh.ARRAY_INDEX].is_empty() else data[Mesh.ARRAY_VERTEX].size())/3
			continue
		var transform: Transform3D = node.global_transform
		var normal_basis := transform.basis.inverse().transposed()
		for surface_index in node.mesh.get_surface_count():
			var material: Material = node.get_active_material(surface_index)
			if material == null: material = Shapes.material(Color.WHITE)
			var tint := Color.WHITE
			var signature := ""
			if material is StandardMaterial3D:
				tint = material.albedo_color.srgb_to_linear()
				var values: Array = []
				for property in state_properties:
					var value: Variant = material.get(property)
					if value is Resource: value = value.resource_path if not value.resource_path.is_empty() else value.get_instance_id()
					values.append(value)
				signature = var_to_str(values)
				if not material_cache.has(signature):
					var shared: StandardMaterial3D = material.duplicate()
					shared.albedo_color = Color.WHITE; shared.vertex_color_use_as_albedo = true; shared.vertex_color_is_srgb = false
					material_cache[signature] = shared
			else:
				# Shader uniforms are retained, including the animated cinema projection.
				signature = "material:"+str(material.get_instance_id())
				if material is ShaderMaterial:
					signature = "shader:"+material.shader.resource_path
					for parameter in material.shader.get_shader_uniform_list():
						var value: Variant = material.get_shader_parameter(parameter.name)
						# Compare texture identity, never serialize an embedded image into
						# every geometry key (the contact atlas has three million bytes).
						if value is Resource: value = value.resource_path if not value.resource_path.is_empty() else value.get_instance_id()
						signature += ":"+str(parameter.name)+"="+var_to_str(value)
				if not material_cache.has(signature): material_cache[signature] = material
			var arrays: Array = node.mesh.surface_get_arrays(surface_index)
			var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
			var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX] if arrays[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
			var count := indices.size() if not indices.is_empty() else vertices.size()
			for triangle in range(0,count,3):
				var ids := [indices[triangle],indices[triangle+1],indices[triangle+2]] if not indices.is_empty() else [triangle,triangle+1,triangle+2]
				var center: Vector3 = transform*((vertices[ids[0]]+vertices[ids[1]]+vertices[ids[2]])/3)
				var cell := Vector3i(floori(center.x/CELL.x),floori(center.y/CELL.y),floori(center.z/CELL.z))
				var key := str(cell)+signature
				if not groups.has(key):
					var builder := SurfaceTool.new(); builder.begin(Mesh.PRIMITIVE_TRIANGLES); builder.set_material(material_cache[signature])
					groups[key] = {"builder":builder,"cell":cell}
				var builder: SurfaceTool = groups[key].builder
				for id in ids:
					builder.set_normal((normal_basis*arrays[Mesh.ARRAY_NORMAL][id]).normalized())
					builder.set_uv(arrays[Mesh.ARRAY_TEX_UV][id] if arrays[Mesh.ARRAY_TEX_UV] != null else Vector2.ZERO)
					var color: Color = arrays[Mesh.ARRAY_COLOR][id] if arrays[Mesh.ARRAY_COLOR] != null and material is StandardMaterial3D and material.vertex_color_use_as_albedo else Color.WHITE
					builder.set_color(tint*color)
					builder.add_vertex(transform*vertices[id])
				triangles += 1
	var cells: Dictionary = {}
	for group in groups.values():
		if not cells.has(group.cell): cells[group.cell] = ArrayMesh.new()
		group.builder.index()
		group.builder.commit(cells[group.cell])
	for cell in cells:
		var node := MeshInstance3D.new(); node.name = "Sector_%d_%d_%d" % [cell.x,cell.y,cell.z]
		node.mesh = cells[cell]; node.extra_cull_margin = .15; root.add_child(node)
	for node in sources:
		if node.get_meta("retail_detail",false): continue
		# Retain non-mesh children (labels, lights) at their original world transforms.
		for child in node.get_children():
			if child is Node3D and child not in sources: child.reparent(root,true)
		node.get_parent().remove_child(node); node.queue_free()
	for node in root.find_children("*","MultiMeshInstance3D",true,false):
		var bounds := AABB(); var first := true
		for index in node.multimesh.instance_count:
			var box: AABB = node.multimesh.get_instance_transform(index)*node.multimesh.mesh.get_aabb()
			bounds = box if first else bounds.merge(box); first = false
		node.multimesh.custom_aabb = bounds.grow(.1)
	for label in root.find_children("*","Label3D",true,false): label.visibility_range_end = 65
	for light in root.find_children("*","OmniLight3D",true,false):
		light.distance_fade_enabled = true; light.distance_fade_begin = 28; light.distance_fade_length = 12
	return {"source_meshes":input_meshes,"sectors":cells.size(),"surfaces":groups.size()+detail_surfaces,"static_surfaces":groups.size(),"triangles":triangles+detail_triangles,"static_triangles":triangles,"detail_triangles":detail_triangles,"detail_meshes":detail_meshes,"detail_surfaces":detail_surfaces}
