extends SceneTree
var checks:=0
var failures:=0
func expect(ok:bool,message:String)->void:
	checks+=1
	if not ok:failures+=1;push_error(message)
func _initialize()->void:call_deferred("verify")
func verify()->void:
	var mall:=Mall.new();root.add_child(mall)
	await physics_frame;await physics_frame
	var a:=Vector3(-75,1.6,-22.7);var b:=Vector3(-75,1.6,-24.4)
	var hit:=mall.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(a,b,1))
	expect(hit.is_empty(),"Bookshop rear public doorway remains physically open")
	var visible_blocker:=false
	for node in mall.find_children("*","MeshInstance3D",true,false):
		if not node.name.begins_with("Sector_"):continue
		var from:Vector3=node.to_local(a);var to:Vector3=node.to_local(b)
		if node.mesh.get_aabb().intersects_segment(from,to)==null:continue
		for s in node.mesh.get_surface_count():
			var arrays:Array=node.mesh.surface_get_arrays(s);var points:PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
			var ids:PackedInt32Array=arrays[Mesh.ARRAY_INDEX]
			for i in range(0,ids.size(),3):
				if Geometry3D.segment_intersects_triangle(from,to,points[ids[i]],points[ids[i+1]],points[ids[i+2]])!=null:visible_blocker=true;break
			if visible_blocker:break
		if visible_blocker:break
	expect(not visible_blocker,"Decorative wall panels do not visually close the public bookshop doorway")
	mall.queue_free();await process_frame
	print("VISUAL ACCESS RESULT: %d checks, %d failures"%[checks,failures]);quit(1 if failures else 0)
