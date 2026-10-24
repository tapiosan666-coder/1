class_name WorldOcclusion
extends RefCounted
## Offline vertex ambient-occlusion interchange. No runtime rays or textures.
static func refine(root: Node3D) -> Dictionary:
	var triangles:=0;var samples:=0
	for node in root.find_children("*","MeshInstance3D",true,false):
		if not node.name.begins_with("Sector_"):continue
		var mesh:=ArrayMesh.new()
		for s in node.mesh.get_surface_count():
			var a:Array=node.mesh.surface_get_arrays(s)
			var builder:=SurfaceTool.new();builder.begin(Mesh.PRIMITIVE_TRIANGLES);builder.set_material(node.mesh.surface_get_material(s))
			var ids:PackedInt32Array=a[Mesh.ARRAY_INDEX]
			var count:int=ids.size() if not ids.is_empty() else a[Mesh.ARRAY_VERTEX].size()
			for i in range(0,count,3):
				var v:Array=[];var n:Array=[];var uv:Array=[];var colors:Array=[]
				for j in 3:
					var id:=ids[i+j] if not ids.is_empty() else i+j
					v.append(a[Mesh.ARRAY_VERTEX][id]);n.append(a[Mesh.ARRAY_NORMAL][id]);uv.append(a[Mesh.ARRAY_TEX_UV][id]);colors.append(a[Mesh.ARRAY_COLOR][id])
				var material:Material=node.mesh.surface_get_material(s)
				var edge:=1.2 if material is ShaderMaterial and material.shader.resource_path=="res://assets/plaster.gdshader" else 5.0
				_triangle(v,n,uv,colors,builder,edge*edge)
			builder.index();builder.commit(mesh)
		for s in mesh.get_surface_count():
			var a:Array=mesh.surface_get_arrays(s);triangles+=a[Mesh.ARRAY_INDEX].size()/3;samples+=a[Mesh.ARRAY_VERTEX].size()
		node.mesh=mesh
	return {"static_triangles":triangles,"vertices":samples}
static func _triangle(v:Array,n:Array,uv:Array,c:Array,b:SurfaceTool,edge_squared:float) -> void:
	var d:=[v[0].distance_squared_to(v[1]),v[1].distance_squared_to(v[2]),v[2].distance_squared_to(v[0])]
	var edge:int=d.find(d.max());var other:=(edge+1)%3;var last:=(edge+2)%3
	if d[edge]>edge_squared and (v[1]-v[0]).cross(v[2]-v[0]).length_squared()>.36:
		var p:Vector3=v[edge].lerp(v[other],.5);var nn:Vector3=n[edge].lerp(n[other],.5).normalized();var t:Vector2=uv[edge].lerp(uv[other],.5);var cc:Color=c[edge].lerp(c[other],.5)
		_triangle([v[edge],p,v[last]],[n[edge],nn,n[last]],[uv[edge],t,uv[last]],[c[edge],cc,c[last]],b,edge_squared)
		_triangle([p,v[other],v[last]],[nn,n[other],n[last]],[t,uv[other],uv[last]],[cc,c[other],c[last]],b,edge_squared)
		return
	for i in 3:
		b.set_normal(n[i]);b.set_uv(uv[i]);b.set_color(c[i]);b.add_vertex(v[i])
static func entries(root:Node3D) -> Array[Dictionary]:
	var result:Array[Dictionary]=[]
	for node in root.find_children("*","MeshInstance3D",true,false):
		if not (node.name.begins_with("Sector_") or node.get_meta("retail_detail",false)):continue
		for s in node.mesh.get_surface_count():
			var mat:Material=node.mesh.surface_get_material(s)
			if mat is StandardMaterial3D and (mat.transparency!=BaseMaterial3D.TRANSPARENCY_DISABLED or mat.emission_enabled):continue
			result.append({"node":node,"surface":s})
	return result
static func emit(root:Node3D,path:String) -> void:
	var records:=entries(root);var file:=FileAccess.open(path,FileAccess.WRITE)
	file.store_32(records.size())
	for record in records:
		var node:MeshInstance3D=record.node;var a:Array=node.mesh.surface_get_arrays(record.surface)
		var ids:PackedInt32Array=a[Mesh.ARRAY_INDEX] if a[Mesh.ARRAY_INDEX]!=null else PackedInt32Array()
		if ids.is_empty():
			for i in a[Mesh.ARRAY_VERTEX].size():ids.append(i)
		file.store_32(a[Mesh.ARRAY_VERTEX].size());file.store_32(ids.size())
		for i in a[Mesh.ARRAY_VERTEX].size():
			var p:Vector3=node.global_transform*a[Mesh.ARRAY_VERTEX][i]
			var n:Vector3=(node.global_transform.basis.inverse().transposed()*a[Mesh.ARRAY_NORMAL][i]).normalized()
			for f:float in [p.x,p.y,p.z,n.x,n.y,n.z]:file.store_float(f)
		for id in ids:file.store_32(id)
	file.close();print("OCCLUSION_INPUT surfaces=",records.size()," file=",path)
static func apply(root:Node3D,path:String) -> Dictionary:
	var file:=FileAccess.open(path,FileAccess.READ);var records:=entries(root)
	assert(file.get_32()==records.size(),"Occlusion output does not match static geometry")
	var grouped:Dictionary={};var count:=0;var total:=0.0;var lowest:=1.0
	for record in records:
		var node:MeshInstance3D=record.node;var s:int=record.surface
		if not grouped.has(node):grouped[node]={}
		var arrays:Array=node.mesh.surface_get_arrays(s);var vertices:PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
		assert(file.get_32()==vertices.size(),"Occlusion vertex mismatch")
		var colors:PackedColorArray=arrays[Mesh.ARRAY_COLOR] if arrays[Mesh.ARRAY_COLOR]!=null else PackedColorArray()
		if colors.is_empty():colors.resize(vertices.size());colors.fill(Color.WHITE)
		for i in vertices.size():
			var raw:=file.get_float();assert(raw>=.35 and raw<=1.0)
			var shade:=lerpf(1.0,raw,.65)
			colors[i]=Color(colors[i].r*shade,colors[i].g*shade,colors[i].b*shade,colors[i].a)
			total+=shade;lowest=minf(lowest,shade);count+=1
		arrays[Mesh.ARRAY_COLOR]=colors;grouped[node][s]=arrays
	for node:MeshInstance3D in grouped:
		var result:=ArrayMesh.new()
		for s in node.mesh.get_surface_count():
			result.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,grouped[node].get(s,node.mesh.surface_get_arrays(s)))
			result.surface_set_material(s,node.mesh.surface_get_material(s))
		node.mesh=result
	var result:={"applied":true,"method":"static vertex ambient occlusion","rays":24,"radius_m":2.4,"strength":.65,"vertices":count,"mean":total/maxi(1,count),"min":lowest}
	root.set_meta("world_occlusion",result);return result
