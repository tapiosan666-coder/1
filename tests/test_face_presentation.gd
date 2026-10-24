extends SceneTree
## Real GPU checks: shared visible-slot gaze, stable eye outline and a moving mouth line.
var checks:=0
var failures:=0
var viewport:SubViewport
var camera:Camera3D
var instance:MultiMesh
func expect(ok:bool,message:String)->void:
	checks+=1
	if not ok:failures+=1;push_error(message)
func _initialize()->void:
	if DisplayServer.get_name()=="headless":printerr("Face presentation checks require a real renderer.");quit(2);return
	call_deferred("verify")
func frame()->Image:
	await process_frame;await RenderingServer.frame_post_draw
	await process_frame;await RenderingServer.frame_post_draw
	return viewport.get_texture().get_image()
func red_centers(image:Image)->Array[float]:
	var sums:=[0.0,0.0];var counts:=[0,0]
	for y in image.get_height():
		for x in image.get_width():
			var c:=image.get_pixel(x,y)
			if c.r>.7 and c.g<.1 and c.b<.1:
				var half:int=0 if x<image.get_width()/2 else 1
				sums[half]+=x;counts[half]+=1
	return [sums[0]/maxi(1,counts[0]),sums[1]/maxi(1,counts[1]),float(counts[0]),float(counts[1])]
func eye_bounds(image:Image)->Rect2i:
	var low:=Vector2i(image.get_width(),image.get_height());var high:=Vector2i(-1,-1)
	for y in image.get_height():
		for x in image.get_width():
			var c:=image.get_pixel(x,y)
			if minf(c.r,minf(c.g,c.b))>.7:
				low=low.min(Vector2i(x,y));high=high.max(Vector2i(x,y))
	return Rect2i(low,high-low)
func mouth_rows(image:Image)->Vector2:
	var sums:=Vector2.ZERO;var counts:=Vector2.ZERO
	for y in image.get_height():
		for x in image.get_width():
			var c:=image.get_pixel(x,y)
			if c.a>.9 and maxf(c.r,maxf(c.g,c.b))<.08:
				if x<image.get_width()*.30 or x>image.get_width()*.70:sums.x+=y;counts.x+=1
				elif absf(x-image.get_width()*.5)<image.get_width()*.08:sums.y+=y;counts.y+=1
	return sums/Vector2(maxf(1,counts.x),maxf(1,counts.y))
func verify()->void:
	var kit:Node3D=preload("res://assets/characters/civilian.glb").instantiate()
	var eye_mesh:Mesh;var head_mesh:Mesh;var hair_mesh:Mesh
	for node in kit.find_children("*","MeshInstance3D",true,false):
		if node.name=="eye_l":eye_mesh=node.mesh.duplicate(true)
		if node.name=="head":head_mesh=node.mesh.duplicate(true)
		if node.name=="hair":hair_mesh=node.mesh
	var hair_triangles:=0;var valid_flow:=true
	for s in hair_mesh.get_surface_count():
		var a:Array=hair_mesh.surface_get_arrays(s);hair_triangles+=a[Mesh.ARRAY_INDEX].size()/3
		for uv:Vector2 in a[Mesh.ARRAY_TEX_UV]:valid_flow=valid_flow and uv.is_finite() and uv.x>=0 and uv.x<=1 and uv.y>=0 and uv.y<=1
	expect(valid_flow and hair_triangles>1500 and hair_triangles<5000,"Directional hair UVs and the full layered silhouette stay inside a 5,000 triangle budget")
	viewport=SubViewport.new();viewport.size=Vector2i(384,128);viewport.own_world_3d=true;viewport.transparent_bg=true;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	camera=Camera3D.new();viewport.add_child(camera);camera.projection=Camera3D.PROJECTION_ORTHOGONAL;camera.size=.085;camera.position=Vector3(0,0,-.25);camera.look_at(Vector3.ZERO);camera.current=true
	instance=MultiMesh.new();instance.transform_format=MultiMesh.TRANSFORM_3D;instance.use_colors=true;instance.use_custom_data=true;instance.mesh=eye_mesh;instance.instance_count=2
	instance.set_instance_transform(0,Transform3D(Basis.IDENTITY,Vector3(-.045,0,0)));instance.set_instance_transform(1,Transform3D(Basis.IDENTITY,Vector3(.045,0,0)))
	for i in 2:instance.set_instance_color(i,Color.WHITE)
	var node:=MultiMeshInstance3D.new();node.multimesh=instance;viewport.add_child(node)
	var face:=CivilianFace.new(300);face.install([{"name":"eye_l","instances":instance}])
	for s in eye_mesh.get_surface_count():
		var m:ShaderMaterial=eye_mesh.surface_get_material(s)
		if m.resource_name.begins_with("Iris"):m.set_shader_parameter("eye_tint",Color.RED)
	var ids:Array[int]=[299,3];var motions:Dictionary={299:{"eyes":Vector2.ZERO,"expression":0.,"blink":0.},3:{"eyes":Vector2.ZERO,"expression":0.,"blink":0.}}
	face.update(ids,motions)
	# Build the mask from the actual white surface, independently of the shader's
	# clipping formula. Hidden iris/liner surfaces leave a complete white almond.
	var white_only:=ArrayMesh.new()
	for s in eye_mesh.get_surface_count():
		if eye_mesh.surface_get_material(s).resource_name.begins_with("Eye"):
			white_only.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,eye_mesh.surface_get_arrays(s));white_only.surface_set_material(white_only.get_surface_count()-1,eye_mesh.surface_get_material(s))
	instance.mesh=white_only;var white_mask:=await frame();instance.mesh=eye_mesh
	var neutral:=await frame();var before:=red_centers(neutral)
	expect(before[2]>20 and before[3]>20,"Both real iris surfaces render through the installed gaze shader")
	motions[299].eyes=Vector2(-.06,0);motions[3].eyes=Vector2(.06,0);face.update(ids,motions)
	var moved:=await frame();var after:=red_centers(moved);var dx:=Vector2(after[0]-before[0],after[1]-before[1])
	expect(absf(dx.x)>2 and absf(dx.y)>2 and dx.x*dx.y<0,"Opposite visible-slot gaze moves the two real irises in opposite directions on the GPU")
	expect(eye_bounds(neutral)==eye_bounds(moved),"Gaze leaves the actual almond eye outline fixed")
	ids.reverse();face.update(ids,motions);var swapped:=red_centers(await frame());var dx_swapped:=Vector2(swapped[0]-before[0],swapped[1]-before[1])
	expect(dx.x*dx_swapped.x<0 and dx.y*dx_swapped.y<0,"Reordering IDs 299 and 3 changes their rendered gaze without retaining the previous slot's face")
	motions[299].eyes=Vector2(1,1);motions[3].eyes=Vector2(-1,-1);face.update(ids,motions)
	var extreme:=await frame();var contained:=true
	for y in extreme.get_height():
		for x in extreme.get_width():
			var c:=extreme.get_pixel(x,y)
			if c.r>.7 and c.g<.1 and c.b<.1:
				var covered:=false
				for dy in range(-1,2):
					for dx_pixel in range(-1,2):covered=covered or white_mask.get_pixel(clampi(x+dx_pixel,0,extreme.get_width()-1),clampi(y+dy,0,extreme.get_height()-1)).r>.7
				contained=contained and covered
	expect(contained,"Even extreme gaze keeps every rendered iris pixel inside the authored white almond, with one-pixel raster tolerance")
	instance.mesh=head_mesh;instance.instance_count=1;instance.set_instance_transform(0,Transform3D.IDENTITY);instance.set_instance_color(0,Color.WHITE)
	for s in head_mesh.get_surface_count():
		var m:StandardMaterial3D=head_mesh.surface_get_material(s);m.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
	face.install([{"name":"head","instances":instance}])
	viewport.size=Vector2i(128,96);camera.size=.035;camera.position=Vector3(0,-.080,-.28);camera.look_at(Vector3(0,-.080,-.12))
	instance.set_instance_custom_data(0,Color(0,0,0,1));var mouth_neutral:=mouth_rows(await frame())
	instance.set_instance_custom_data(0,Color(0,1,0,1));var mouth_smile:=mouth_rows(await frame())
	expect(mouth_neutral.x-mouth_smile.x>2 and absf(mouth_neutral.y-mouth_smile.y)<2,"The actual drawn mouth corners lift with expression while the center stays stable")
	kit.free();viewport.queue_free();await process_frame
	print("FACE PRESENTATION RESULT: %d checks, %d failures"%[checks,failures]);quit(1 if failures else 0)
