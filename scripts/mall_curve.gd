class_name MallCurve
extends RefCounted
## Logical retail plan -> a straight west wing flowing into a 60-degree arc.
const START := -35.0
const RADIUS := 130.0
const EDGE := 3.0

static func angle(x: float) -> float:
	return maxf(0,(x-START)/RADIUS)

static func world(p: Vector3) -> Vector3:
	if p.x <= START: return p
	var a := angle(p.x)
	return Vector3(START+(RADIUS-p.z)*sin(a),p.y,RADIUS-(RADIUS-p.z)*cos(a))

static func plan(p: Vector3) -> Vector3:
	if p.x <= START: return p
	var dx := p.x-START
	var dz := RADIUS-p.z
	return Vector3(START+RADIUS*atan2(dx,dz),p.y,RADIUS-sqrt(dx*dx+dz*dz))

static func jacobian(p: Vector3) -> Basis:
	var a := angle(p.x)
	return Basis(Vector3(cos(a),0,sin(a))*(1-p.z/RADIUS if p.x > START else 1.0),Vector3.UP,Vector3(-sin(a),0,cos(a)))

static func polygon(rect: Rect2) -> PackedVector2Array:
	var corners := [rect.position,Vector2(rect.end.x,rect.position.y),rect.end,Vector2(rect.position.x,rect.end.y)]
	var result := PackedVector2Array()
	for side in 4:
		var a: Vector2 = corners[side]
		var b: Vector2 = corners[(side+1)%4]
		var steps := maxi(1,ceili(a.distance_to(b)/EDGE))
		for index in steps:
			var p := a.lerp(b,float(index)/steps)
			var q := world(Vector3(p.x,0,p.y))
			result.append(Vector2(q.x,q.z))
	return result

static func _faces(a: Vector3,b: Vector3,c: Vector3,out: PackedVector3Array) -> void:
	var ab := a.distance_squared_to(b)
	var bc := b.distance_squared_to(c)
	var ca := c.distance_squared_to(a)
	if maxf(ab,maxf(bc,ca)) <= EDGE*EDGE:
		out.append_array(PackedVector3Array([world(a),world(b),world(c)]))
	elif ab >= bc and ab >= ca:
		var middle := (a+b)*.5
		_faces(a,middle,c,out); _faces(middle,b,c,out)
	elif bc >= ca:
		var middle := (b+c)*.5
		_faces(a,b,middle,out); _faces(a,middle,c,out)
	else:
		var middle := (c+a)*.5
		_faces(a,b,middle,out); _faces(middle,b,c,out)

static func _triangle(vertices: Array,normals: Array,uvs: Array,surface: SurfaceTool) -> void:
	var distances := [vertices[0].distance_squared_to(vertices[1]),vertices[1].distance_squared_to(vertices[2]),vertices[2].distance_squared_to(vertices[0])]
	var edge: int = distances.find(distances.max())
	if distances[edge] > EDGE*EDGE:
		var other := (edge+1)%3
		var last := (edge+2)%3
		var v: Vector3 = (vertices[edge]+vertices[other])*.5
		var n: Vector3 = (normals[edge]+normals[other]).normalized()
		var uv: Vector2 = (uvs[edge]+uvs[other])*.5
		_triangle([vertices[edge],v,vertices[last]],[normals[edge],n,normals[last]],[uvs[edge],uv,uvs[last]],surface)
		_triangle([v,vertices[other],vertices[last]],[n,normals[other],normals[last]],[uv,uvs[other],uvs[last]],surface)
		return
	for i in 3:
		surface.set_normal((jacobian(vertices[i]).inverse().transposed()*normals[i]).normalized())
		surface.set_uv(uvs[i])
		surface.add_vertex(world(vertices[i]))

static func bend_mesh(mesh: Mesh, transform: Transform3D) -> ArrayMesh:
	var result := ArrayMesh.new()
	for index in mesh.get_surface_count():
		var arrays := mesh.surface_get_arrays(index)
		var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX] if arrays[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
		var points: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var count := indices.size() if not indices.is_empty() else points.size()
		var surface := SurfaceTool.new()
		surface.begin(Mesh.PRIMITIVE_TRIANGLES)
		for triangle in range(0,count,3):
			var vs: Array = []; var ns: Array = []; var uv: Array = []
			for offset in 3:
				var id := indices[triangle+offset] if not indices.is_empty() else triangle+offset
				vs.append(transform*points[id])
				ns.append((transform.basis.inverse().transposed()*arrays[Mesh.ARRAY_NORMAL][id]).normalized())
				uv.append(arrays[Mesh.ARRAY_TEX_UV][id] if arrays[Mesh.ARRAY_TEX_UV] != null else Vector2.ZERO)
			_triangle(vs,ns,uv,surface)
		surface.set_material(mesh.surface_get_material(index))
		surface.commit(result)
	return result

static func bake(root: Node3D) -> void:
	# Capture original transforms before any parent transforms are reset.
	var collisions := PackedVector3Array()
	var bodies := root.find_children("*","StaticBody3D",true,false)
	for body in bodies:
		for child in body.get_children():
			if not child is CollisionShape3D: continue
			var faces := PackedVector3Array()
			if child.shape is BoxShape3D:
				var box := BoxMesh.new(); box.size = child.shape.size; faces = box.get_faces()
			elif child.shape is ConcavePolygonShape3D:
				faces = child.shape.get_faces()
			for i in range(0,faces.size(),3):
				_faces(child.global_transform*faces[i],child.global_transform*faces[i+1],child.global_transform*faces[i+2],collisions)
	var jobs: Array[Dictionary] = []
	for node in root.find_children("*","MeshInstance3D",true,false):
		jobs.append({"node":node,"transform":node.global_transform})
	var labels: Array[Dictionary] = []
	for node in root.find_children("*","Label3D",true,false):
		labels.append({"node":node,"transform":node.global_transform})
	for job in jobs:
		var node: MeshInstance3D = job.node
		var t: Transform3D = job.transform
		var bounds := t*node.mesh.get_aabb()
		if bounds.size.x > 4:
			node.mesh = bend_mesh(node.mesh,t)
			node.global_transform = Transform3D.IDENTITY
		else:
			node.global_transform = Transform3D(jacobian(t.origin)*t.basis,world(t.origin))
	for node in root.find_children("*","MultiMeshInstance3D",true,false):
		var original: Transform3D = node.global_transform
		for index in node.multimesh.instance_count:
			var t: Transform3D = original*node.multimesh.get_instance_transform(index)
			node.multimesh.set_instance_transform(index,Transform3D(jacobian(t.origin)*t.basis,world(t.origin)))
		node.global_transform = Transform3D.IDENTITY
		node.multimesh.custom_aabb = AABB(Vector3(-110,-10,-90),Vector3(270,40,230))
	for job in labels:
		var t: Transform3D = job.transform
		job.node.global_transform = Transform3D(Basis(Vector3.UP,-angle(t.origin.x))*t.basis,world(t.origin))
	for light in root.find_children("*","OmniLight3D",true,false):
		light.global_position = world(light.global_position)
	for body in bodies:
		body.get_parent().remove_child(body); body.queue_free()
	var body := StaticBody3D.new()
	var shape := ConcavePolygonShape3D.new(); shape.set_faces(collisions)
	var collision := CollisionShape3D.new(); collision.shape = shape
	body.add_child(collision); root.add_child(body)
