class_name CivilianLod
extends RefCounted
## Distant silhouette; alpha is a cloth mask, never transparency.
static func mesh_for(seated: bool,skin: Color,hair: Color,width: float) -> ArrayMesh:
	var builder := SurfaceTool.new(); builder.begin(Mesh.PRIMITIVE_TRIANGLES)
	var torso := CapsuleMesh.new(); torso.radius = .19; torso.height = .66; torso.radial_segments = 8; torso.rings = 3
	_append(builder,torso,Transform3D(Basis.IDENTITY,Vector3(0,.74 if seated else 1.14,0)),Color(1,1,1,1))
	var head := SphereMesh.new(); head.radius = .112; head.height = .31; head.radial_segments = 8; head.rings = 4
	var skin_color := skin; skin_color.a = 0
	_append(builder,head,Transform3D(Basis().scaled(Vector3(width,1,1)),Vector3(0,1.28 if seated else 1.70,0)),skin_color)
	var cap := SphereMesh.new(); cap.radius = .12; cap.height = .12; cap.radial_segments = 8; cap.rings = 3
	var hair_color := hair; hair_color.a = 0
	_append(builder,cap,Transform3D(Basis().scaled(Vector3(width,1,1)),Vector3(0,1.42 if seated else 1.84,0)),hair_color)
	for side in [-1,1]:
		var arm := CapsuleMesh.new(); arm.radius = .055; arm.height = .55; arm.radial_segments = 6; arm.rings = 2
		_append(builder,arm,Transform3D(Basis(Vector3.RIGHT,-.7 if seated else 0),Vector3(side*.235,.83 if seated else 1.12,-.12 if seated else 0)),Color(1,1,1,1))
		var leg := CapsuleMesh.new(); leg.radius = .085; leg.height = .76 if not seated else .46; leg.radial_segments = 6; leg.rings = 2
		var trousers := Color("344449"); trousers.a = 0
		_append(builder,leg,Transform3D(Basis.IDENTITY,Vector3(side*.105,.43 if not seated else .26,-.4 if seated else 0)),trousers)
		if seated: _append(builder,leg,Transform3D(Basis(Vector3.RIGHT,-PI/2),Vector3(side*.105,.48,-.2)),trousers)
	var material := ShaderMaterial.new(); material.shader = preload("res://assets/civilian_lod.gdshader")
	builder.set_material(material)
	return builder.commit()

static func _append(builder: SurfaceTool,mesh: Mesh,t: Transform3D,color: Color) -> void:
	var arrays := mesh.surface_get_arrays(0)
	var ids: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
	for id in ids:
		builder.set_normal((t.basis*arrays[Mesh.ARRAY_NORMAL][id]).normalized())
		builder.set_color(color)
		builder.add_vertex(t*arrays[Mesh.ARRAY_VERTEX][id])
