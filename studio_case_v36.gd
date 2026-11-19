extends RefCounted

const DIRECTORY := "res://assets/v36/studios/"

# Solid furniture envelopes are kept below the displayed stock. The gallery's
# full-height back and the low arrival sign have matching physical thickness.
static func shape_for(role: String, variant: int, pose: Transform3D) -> ConcavePolygonShape3D:
	var height := .40 if role == "gallery" else float([.62,.48,.55][variant])
	var top := height + .118
	var sections := [AABB(Vector3(-1.29,0,-.37),Vector3(2.58,top,.74))]
	if role == "dining":
		sections = [AABB(Vector3(-1.255,0,-.47),Vector3(2.51,.49,.55)),
			AABB(Vector3(-1.275,.49,-.484),Vector3(2.55,.85,.18))]
		for x: float in [-.61,.61]:
			sections.append(AABB(Vector3(x-.19,0,.09),Vector3(.38,.705,.27)))
			sections.append(AABB(Vector3(x-.455,.705,-.002),Vector3(.91,.043,.46)))
	elif role == "gallery":
		sections.append(AABB(Vector3(-1.26,top,-.338),Vector3(2.52,2.27-top,.08)))
		for side: float in [-1.26,1.26]:
			sections.append(AABB(Vector3(side-.024,top,-.33),Vector3(.048,2.27-top,.46)))
	else:
		var side := .858 if variant == 1 else -.858
		sections.append(AABB(Vector3(side-.32,top,-.252),Vector3(.64,.70,.09)))
	var faces := PackedVector3Array()
	for section: AABB in sections:
		var box := BoxMesh.new()
		box.size = section.size
		for vertex: Vector3 in box.get_faces():
			faces.append(pose * (vertex + section.get_center()))
	var result := ConcavePolygonShape3D.new()
	result.set_faces(faces)
	result.backface_collision = true
	return result
