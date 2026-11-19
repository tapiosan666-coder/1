extends RefCounted

const DIRECTORY := "res://assets/v36/studios/"
const SHAPE_DATA := "res://source/v36/studio-solids.json"
static var authored_shapes: Dictionary = {}
static var unit_faces := PackedVector3Array()

# Collision follows the visible occupied parts of the display. In particular,
# an open garment rail never inherits the solid rear of a bookcase.
static func shape_for(role: String, _variant: int, pose: Transform3D, model_key: String) -> ConcavePolygonShape3D:
	if authored_shapes.is_empty():
		authored_shapes = JSON.parse_string(FileAccess.get_file_as_string(SHAPE_DATA))
	if unit_faces.is_empty():
		unit_faces = BoxMesh.new().get_faces()
	var sections: Array[AABB] = []
	if authored_shapes.has(model_key):
		for row: Array in authored_shapes[model_key]:
			var centre := Vector3(row[0], row[1], row[2])
			var size := Vector3(row[3], row[4], row[5])
			sections.append(AABB(centre - size * .5, size))
	elif role == "dining":
		sections.assign([AABB(Vector3(-1.255,0,-.47),Vector3(2.51,.49,.55)),
			AABB(Vector3(-1.275,.49,-.484),Vector3(2.55,.85,.18))])
		for x: float in [-.61,.61]:
			sections.append(AABB(Vector3(x-.19,0,.09),Vector3(.38,.705,.27)))
			sections.append(AABB(Vector3(x-.455,.705,-.002),Vector3(.91,.043,.46)))
	else:
		push_error("Missing retail physical section data for " + model_key)
		return null
	var faces := PackedVector3Array()
	faces.resize(sections.size() * unit_faces.size())
	var cursor := 0
	for section: AABB in sections:
		var centre := section.get_center()
		for vertex: Vector3 in unit_faces:
			faces[cursor] = pose * (vertex * section.size + centre)
			cursor += 1
	var result := ConcavePolygonShape3D.new()
	result.set_faces(faces)
	result.backface_collision = true
	return result
