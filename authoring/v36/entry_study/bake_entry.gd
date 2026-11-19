extends SceneTree
## Rebuild only the two cells used by the optional TERRUNE entrance study.
## Aperture dimensions are in metres. The existing stainless header sits above 2.67 m.
const OUTPUT := "res://assets/v36/entry_study/"
const POINT := Vector3(178.99594525,0.,-39.18126625)
const DEPTH := Vector3(.66726156855,0,.74482346844)
const WIDTH := Vector3(-.74482346844,0,.66726156855)
const SHELL := "res://assets/v33/prepared-world/shell_-9_3_-1.scn"
const PHYS := "res://assets/v31/world/c72169aa67e05357/physics_-9_3_-1.scn"
const GLAZING := "res://assets/v30/world/meshes/9a305e0f44bb72f282bda85b41630bd8fff3e52aaca167c016f04b9925fd2353.res"
const MULLION := "res://assets/v30/world/meshes/bcfd68bfd6f2481dd92a4c3b3761930bda47d1c3c0202f7df27417d667d4fd14.res"
const SOLID := "res://assets/v30/world/shapes/world3368.res"
const HALF_WIDTH := 1.2
const HEAD := 2.63

func _initialize() -> void:
	call_deferred("bake")

func boundary(point: Vector3, side: int) -> float:
	var delta := point-POINT
	match side:
		0: return delta.dot(WIDTH)-HALF_WIDTH
		1: return -delta.dot(WIDTH)-HALF_WIDTH
		2: return delta.dot(DEPTH)-.12
		3: return -delta.dot(DEPTH)-.12
		4: return delta.y-HEAD
	return -.12-delta.y

func interpolate(a: Dictionary,b: Dictionary,t: float)-> Dictionary:
	var value:Dictionary={"p":a.p.lerp(b.p,t)}
	if a.has("n"):value.n=a.n.lerp(b.n,t).normalized()
	if a.has("uv"):value.uv=a.uv.lerp(b.uv,t)
	if a.has("uv2"):value.uv2=a.uv2.lerp(b.uv2,t)
	if a.has("color"):value.color=a.color.lerp(b.color,t)
	if a.has("t"):value.t=a.t.lerp(b.t,t)
	return value

func clip(poly: Array, side: int, keep_inside: bool) -> Array:
	var result:Array=[]
	for i:int in poly.size():
		var a:Dictionary=poly[i]
		var b:Dictionary=poly[(i+1)%poly.size()]
		var fa:=boundary(a.p,side)
		var fb:=boundary(b.p,side)
		var keep_a:=fa<=0. if keep_inside else fa>=0.
		var keep_b:=fb<=0. if keep_inside else fb>=0.
		if keep_a:result.append(a)
		if keep_a!=keep_b:
			result.append(interpolate(a,b,fa/(fa-fb)))
	return result

func subtract(triangle:Array)->Array:
	# The collision packet also carries the public/store slab at y=0.
	# Preserve these wide structural faces. The short metal mullion base is part
	# of the opening and is identified by its local footprint.
	var a:Vector3=triangle[0].p
	var b:Vector3=triangle[1].p
	var c:Vector3=triangle[2].p
	var hmin:=minf(a.y,minf(b.y,c.y));var hmax:=maxf(a.y,maxf(b.y,c.y))
	if hmax<.015 and hmin>-.12 and maxf(a.distance_to(b),maxf(a.distance_to(c),b.distance_to(c)))>.13:
		return [triangle]
	# First reject whole triangles on one side; only bisect faces intersecting the aperture.
	var center:Array=triangle
	var outside:Array=[]
	for side:int in 6:
		if center.is_empty():return [triangle]
		var next:=clip(center,side,true)
		var rem:=clip(center,side,false)
		if rem.size()>=3:outside.append(rem)
		center=next
	if center.size()<3:return [triangle]
	return outside

func rebuilt_mesh(old: Mesh, expected_faces: int) -> ArrayMesh:
	assert(old.get_surface_count()==1)
	var m:=old.surface_get_arrays(0)
	var positions:PackedVector3Array=m[Mesh.ARRAY_VERTEX]
	var indices:PackedInt32Array=m[Mesh.ARRAY_INDEX] if m[Mesh.ARRAY_INDEX]!=null else PackedInt32Array()
	if indices.is_empty():
		indices.resize(positions.size())
		for i:int in indices.size():indices[i]=i
	var surface:=SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	surface.set_material(old.surface_get_material(0))
	var changed:=0
	for base:int in range(0,indices.size(),3):
		var tri:Array=[]
		for k:int in [indices[base],indices[base+1],indices[base+2]]:
			var point:Dictionary={"p":positions[k]}
			if m[Mesh.ARRAY_NORMAL]!=null:point.n=m[Mesh.ARRAY_NORMAL][k]
			if m[Mesh.ARRAY_TEX_UV]!=null:point.uv=m[Mesh.ARRAY_TEX_UV][k]
			if m[Mesh.ARRAY_TEX_UV2]!=null:point.uv2=m[Mesh.ARRAY_TEX_UV2][k]
			if m[Mesh.ARRAY_COLOR]!=null:point.color=m[Mesh.ARRAY_COLOR][k]
			if m[Mesh.ARRAY_TANGENT]!=null:
				var t:PackedFloat32Array=m[Mesh.ARRAY_TANGENT]
				point.t=Vector4(t[4*k],t[4*k+1],t[4*k+2],t[4*k+3])
			tri.append(point)
		var polygons:=subtract(tri)
		if polygons!=[tri]:
			changed+=1
		for p:Array in polygons:
			for j:int in range(1,p.size()-1):
				for v:Dictionary in [p[0],p[j],p[j+1]]:
					if v.has("n"):surface.set_normal(v.n)
					if v.has("color"):surface.set_color(v.color)
					if v.has("uv"):surface.set_uv(v.uv)
					if v.has("uv2"):surface.set_uv2(v.uv2)
					if v.has("t"):surface.set_tangent(Plane(v.t.x,v.t.y,v.t.z,v.t.w))
					surface.add_vertex(v.p)
	if changed!=expected_faces:
		push_error("Unexpected count on identified facade component: expected %d, observed %d" % [expected_faces,changed])
		return null
	return surface.commit()

func rebuilt_collision(old: ConcavePolygonShape3D)->ConcavePolygonShape3D:
	var faces:=old.get_faces()
	var revised:=PackedVector3Array()
	var changed:=0
	for i:int in range(0,faces.size(),3):
		var tri:=[{"p":faces[i]},{"p":faces[i+1]},{"p":faces[i+2]}]
		var polygons:=subtract(tri)
		if polygons!=[tri]:
			changed+=1
		for p:Array in polygons:
			for j:int in range(1,p.size()-1):
				revised.append(p[0].p)
				revised.append(p[j].p)
				revised.append(p[j+1].p)
	if changed!=16:
		push_error("Expected sixteen glass/mullion collision faces; observed %d" % changed)
		return null
	var result:=ConcavePolygonShape3D.new()
	result.set_faces(revised)
	result.backface_collision=old.backface_collision
	return result

func update_occluder(node:OccluderInstance3D)->int:
	var original:=node.occluder as ArrayOccluder3D
	if original==null:return 0
	var vertices:=original.vertices
	var order:=original.indices
	var revised:=PackedVector3Array()
	var edits:=0
	for i:int in range(0,order.size(),3):
		var tri:=[{"p":vertices[order[i]]},{"p":vertices[order[i+1]]},{"p":vertices[order[i+2]]}]
		var polygons:=subtract(tri)
		if polygons!=[tri]:edits+=1
		for p:Array in polygons:
			for j:int in range(1,p.size()-1):
				revised.append(p[0].p)
				revised.append(p[j].p)
				revised.append(p[j+1].p)
	if edits:
		var replacement:=ArrayOccluder3D.new()
		var ids:=PackedInt32Array()
		for i:int in revised.size():ids.append(i)
		replacement.set_arrays(revised,ids)
		node.occluder=replacement
	return edits

func save_chunk(node:Node)->bool:
	var packed:=PackedScene.new()
	if packed.pack(node)!=OK:return false
	return ResourceSaver.save(packed,OUTPUT+str(node.name)+".scn",ResourceSaver.FLAG_COMPRESS)==OK

func bake()->void:
	RenderingServer.set_render_loop_enabled(false)
	var shell:Node=load(SHELL).instantiate()
	var physics:Node=load(PHYS).instantiate()
	var mesh:=rebuilt_mesh(load(GLAZING),6)
	var mullion:=rebuilt_mesh(load(MULLION),10)
	var shape:=rebuilt_collision(load(SOLID))
	if mesh==null or shape==null or mullion==null:
		shell.free()
		physics.free()
		quit(1)
		return
	var visuals:=0
	var physical:=0
	for visual:MultiMeshInstance3D in shell.find_children("*","MultiMeshInstance3D",true,false):
		var path:=visual.multimesh.mesh.resource_path
		if path not in [GLAZING,MULLION]:continue
		if visual.multimesh.instance_count!=1:quit(1);return
		var copy:=visual.multimesh.duplicate(false) as MultiMesh
		copy.mesh=mesh if path==GLAZING else mullion
		visual.multimesh=copy
		visuals+=1
	for col:CollisionShape3D in physics.find_children("*","CollisionShape3D",true,false):
		if col.shape.resource_path==SOLID:
			col.shape=shape
			physical+=1
	var occlusion_edits:=0
	for o:OccluderInstance3D in shell.find_children("*","OccluderInstance3D",true,false):
		if not o.transform.is_equal_approx(Transform3D.IDENTITY):push_error("Unexpected occluder transform");quit(1);return
		occlusion_edits+=update_occluder(o)
	print("B032_OCCLUSION_FACES ",occlusion_edits)
	var success:=visuals==2 and physical==1 and save_chunk(shell) and save_chunk(physics)
	print("B032_OPTION_BAKE ",success," ",shell.name," ",physics.name,"  replaced resources ",[visuals,physical])
	shell.free()
	physics.free()
	quit(0 if success else 1)
