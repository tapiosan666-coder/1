extends SceneTree
func _initialize()->void:
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("/tmp/fy15-body.json"))
	var mesh:=ArrayMesh.new();var triangles:=0
	for channel:Dictionary in data.channels:
		var values:Array=channel.vertices
		if values.is_empty():continue
		var b:=SurfaceTool.new();b.begin(Mesh.PRIMITIVE_TRIANGLES)
		for i in range(0,values.size(),11):
			b.set_normal(Vector3(values[i+3],values[i+4],values[i+5]));b.set_uv(Vector2(values[i+6],values[i+7]));b.set_uv2(Vector2(values[i+8],values[i+9]))
			b.set_color(Color(values[i+10],values[i+10],values[i+10],1));b.add_vertex(Vector3(values[i],values[i+1],values[i+2]))
		var material:=StandardMaterial3D.new();material.resource_name=channel.name;b.set_material(material)
		b.index();b.generate_tangents();b.commit(mesh);triangles+=values.size()/33
	mesh.set_meta("body_format",1);mesh.set_meta("bones",CivilianRig.BONE_COUNT);mesh.set_meta("triangles",triangles);mesh.set_meta("continuous_garments",true)
	assert(ResourceSaver.save(mesh,"res://assets/characters/civilian_body.res",ResourceSaver.FLAG_COMPRESS)==OK)
	print("BODY_IMPORTED ",triangles," triangles ",mesh.get_surface_count()," surfaces");quit()
