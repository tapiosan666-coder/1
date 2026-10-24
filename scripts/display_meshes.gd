class_name DisplayMeshes
extends RefCounted
static var cache: Dictionary = {}
static func beveled_box(size: Vector3,amount: float = .015) -> ArrayMesh:
	var key := Vector4(size.x,size.y,size.z,amount)
	if cache.has(key): return cache[key]
	var half := size*.5
	var b := minf(amount,minf(half.x,minf(half.y,half.z))*.4)
	var inner := half-Vector3.ONE*b
	var surface := SurfaceTool.new(); surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	# Six inset planes, twelve bevel strips and eight corner triangles.
	for axis in 3:
		var u := (axis+1)%3; var v := (axis+2)%3
		for sign in [-1,1]:
			var normal := Vector3.ZERO; normal[axis] = sign
			var points: Array[Vector3] = []
			for corner in [Vector2(-1,-1),Vector2(1,-1),Vector2(1,1),Vector2(-1,1)]:
				var p := Vector3.ZERO; p[axis] = half[axis]*sign; p[u] = inner[u]*corner.x; p[v] = inner[v]*corner.y; points.append(p)
			_polygon(surface,points,normal)
	for axis in 3:
		var u := (axis+1)%3; var v := (axis+2)%3
		for a in [-1,1]:
			for c in [-1,1]:
				var points: Array[Vector3] = []
				for end in [-1,1]:
					for edge in [0,1]:
						var p := Vector3.ZERO; p[axis] = inner[axis]*end; p[u] = (half[u] if edge == 0 else inner[u])*a; p[v] = (inner[v] if edge == 0 else half[v])*c; points.append(p)
				var normal := Vector3.ZERO; normal[u] = a; normal[v] = c
				_polygon(surface,[points[0],points[1],points[3],points[2]],normal.normalized())
	for x in [-1,1]:
		for y in [-1,1]:
			for z in [-1,1]:
				var signs := Vector3(x,y,z)
				_polygon(surface,[Vector3(half.x,inner.y,inner.z)*signs,Vector3(inner.x,half.y,inner.z)*signs,Vector3(inner.x,inner.y,half.z)*signs],signs.normalized())
	var mesh := surface.commit(); cache[key] = mesh; return mesh
static func _polygon(surface: SurfaceTool,points: Array,normal: Vector3) -> void:
	# Godot front faces use clockwise winding when viewed from outside.
	if (points[1]-points[0]).cross(points[2]-points[0]).dot(normal) > 0: points.reverse()
	for index in range(1,points.size()-1):
		for p: Vector3 in [points[0],points[index],points[index+1]]:
			surface.set_normal(normal); surface.set_uv(Vector2(p.x+p.z,p.y)); surface.add_vertex(p)
