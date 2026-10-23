class_name HumanMesh
extends RefCounted
## Original ring-sculpted meshes: dimensions are normalized for shared instancing.
static func sculpt(profile: Array, segments: int = 12) -> ArrayMesh:
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for ring in range(profile.size() - 1):
		for side in segments:
			var points: Array[Vector3] = []
			for pair in [[ring, side], [ring + 1, side], [ring + 1, side + 1], [ring, side + 1]]:
				var row: Vector3 = profile[pair[0]]
				var angle: float = TAU * pair[1] / segments
				points.append(Vector3(sin(angle) * row.x, row.y, cos(angle) * row.z))
			for index in [0, 1, 2, 0, 2, 3]:
				surface.add_vertex(points[index])
	surface.generate_normals()
	return surface.commit()

static func torso() -> ArrayMesh:
	return sculpt([Vector3(0, -.5, 0), Vector3(.38, -.49, .42), Vector3(.35, -.22, .39), Vector3(.44, .21, .48), Vector3(.5, .35, .42), Vector3(.25, .5, .3), Vector3(0, .5, 0)])

static func face() -> ArrayMesh:
	return sculpt([Vector3(0, -.5, 0), Vector3(.24, -.46, .3), Vector3(.4, -.26, .42), Vector3(.49, .02, .46), Vector3(.47, .3, .45), Vector3(.32, .46, .34), Vector3(0, .5, 0)], 20)

static func limb() -> ArrayMesh:
	return sculpt([Vector3(0, -.5, 0), Vector3(.41, -.49, .41), Vector3(.43, -.1, .43), Vector3(.49, .38, .48), Vector3(.4, .5, .4), Vector3(0, .5, 0)])
