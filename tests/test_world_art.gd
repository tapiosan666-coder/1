extends SceneTree
var checks:=0
var failures:=0
func expect(ok:bool,message:String)->void:
	checks+=1
	if not ok:failures+=1;push_error(message)
func _initialize()->void:call_deferred("verify")
func verify()->void:
	if DisplayServer.get_name()=="headless":push_error("Run with an actual renderer to validate saved MultiMesh and material data.");quit(2);return
	var world:Node3D=load(WorldCache.PATH).instantiate();root.add_child(world)
	var bad:=0;var count:=0;var tree_count:=0
	for node in world.find_children("*","MultiMeshInstance3D",true,false):
		count+=1
		for i in node.multimesh.instance_count:
			var t:Transform3D=node.multimesh.get_instance_transform(i)
			if not t.origin.is_finite() or absf(t.basis.determinant())<.00001:bad+=1
		if node.multimesh.instance_count==34:tree_count+=1
	expect(count>10 and tree_count>=5 and bad==0,"Saved trees, books and product labels retain non-zero, finite instanced transforms")
	var ao:Dictionary=world.get_meta("world_occlusion",{})
	expect(ao.get("applied",false) and ao.get("rays",0)==24 and ao.get("vertices",0)>100000,"Distribution includes offline static occlusion, rather than calculating it during movement")
	expect(ao.get("mean",1)<.95 and ao.get("min",1)>=.35,"Static occlusion contains bounded, non-uniform shading")
	var paint_colors:Dictionary={};var menu:=0
	for node in world.find_children("*","MeshInstance3D",true,false):
		for s in node.mesh.get_surface_count():
			var material:Material=node.get_active_material(s)
			if material is ShaderMaterial and material.shader.resource_path=="res://assets/plaster.gdshader":
				var arrays:Array=node.mesh.surface_get_arrays(s)
				for color:Color in arrays[Mesh.ARRAY_COLOR]:
					var total:=color.r+color.g+color.b
					if total>.01:paint_colors[Vector2(roundf(color.r/total*100),roundf(color.g/total*100))]=true
			if material is StandardMaterial3D and material.albedo_texture!=null and material.albedo_texture.resource_path=="res://assets/dining/menus.png":menu+=1
	expect(paint_colors.size()>=6,"Distinct tenant paint colours survive static mesh batching")
	expect(menu>0,"Original Japanese food menus survive cache serialization")
	var spots:=0;var spot_positions:=true
	for light in world.find_children("*","SpotLight3D",true,false):
		if not light.has_meta("plan_origin"):continue
		spots+=1
		if light.global_position.distance_to(MallCurve.world(light.get_meta("plan_origin")))>.001:spot_positions=false
	expect(spots>=60 and spot_positions,"Retail spotlights follow their intended plan positions around the curved mall")
	world.queue_free();await process_frame
	print("WORLD ART RESULT: %d checks, %d failures"%[checks,failures]);quit(1 if failures else 0)
