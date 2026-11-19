extends SceneTree
const HANDLE:="res://assets/v30/world/meshes/ec844cee285f76658857515f4d3d2b6b2440ce9be9ea0558385a76239b02a32d.res"
const SCENE:="res://assets/v31/world/c72169aa67e05357/interior_0_-1_0.scn"
func _initialize()->void:
	var original=load(SCENE)
	var root_node:Node3D=original.instantiate()
	var stores=JSON.parse_string(FileAccess.get_file_as_string("res://source/v32/sales-design.json")).stores
	var store=stores.filter(func(r):return r.id=="B1-SW32")[0]
	var poly=PackedVector2Array(store.scope.coordinates[0].map(func(q):return Vector2(q[0],q[1])))
	var changed:int=0
	for n:MultiMeshInstance3D in root_node.find_children("*","MultiMeshInstance3D",true,false):
		var mm:=n.multimesh
		if mm==null or mm.mesh.resource_path!=HANDLE:continue
		if mm.instance_count!=14:
			printerr("Unexpected prepared geometry count ",mm.instance_count);quit(1);return
		for i in mm.instance_count:
			var pose:=n.transform*mm.get_instance_transform(i)
			var centre:=pose*mm.mesh.get_aabb().get_center()
			var b:=pose*mm.mesh.get_aabb()
			if not Geometry2D.is_point_in_polygon(Vector2(centre.x,centre.z),poly) or b.size.y<.30 or minf(b.size.x,b.size.z)>.045:
				printerr("Instance belongs to another room or has a different shape",i);quit(2);return
		changed+=mm.instance_count;n.free()
	if changed!=14:printerr("Incomplete affected ownership");quit(3);return
	var packed:=PackedScene.new()
	if packed.pack(root_node)!=OK:quit(4);return
	if ResourceSaver.save(packed,SCENE,ResourceSaver.FLAG_COMPRESS)!=OK:quit(5);return
	print("SALES_CACHE_REMOVED ",changed," checked orphan handles only.")
	root_node.free();quit()
