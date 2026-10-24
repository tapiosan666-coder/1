extends SceneTree
var checks := 0
var failures := 0
func expect(condition: bool,message: String) -> void:
	checks += 1
	if not condition: failures += 1; push_error(message)
	else: print("PASS: ",message)
func _initialize() -> void: call_deferred("verify")
func pixel(image: Image,at: Vector2) -> Color:
	var uv := (at-FloorContacts.AREA.position)/FloorContacts.AREA.size
	return image.get_pixel(clampi(int(uv.x*image.get_width()),0,image.get_width()-1),clampi(int(uv.y*image.get_height()),0,image.get_height()-1))
func verify() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("Run without --headless: material uniforms require a real renderer."); quit(2); return
	var world: Node3D = load(WorldCache.PATH).instantiate(); root.add_child(world)
	var atlas: Texture2D
	for node in world.find_children("*","MeshInstance3D",true,false):
		for index in node.mesh.get_surface_count():
			var material: Material = node.get_active_material(index)
			if material is ShaderMaterial and material.shader.resource_path == "res://assets/terrazzo.gdshader" and material.get_shader_parameter("has_contacts"):
				atlas = material.get_shader_parameter("contact_map"); break
		if atlas != null: break
	expect(atlas != null,"Prebuilt scene retains an embedded floor-contact atlas")
	if atlas != null:
		var image := atlas.get_image()
		expect(image.get_size() == Vector2i(1024,1024),"Embedded atlas preserves its full RGB data")
		var bench := pixel(image,Vector2(-57,3.4)); var open := pixel(image,Vector2(0,0))
		expect(bench.r < .85 and open.r > .99,"Static bench contact is shaded while clear floor stays clear")
		expect(bench.g > bench.r+.1 and bench.b > bench.r+.1,"Ground-floor bench contact does not repeat on upper floors")
	var material := MallFinishes.stone()
	var color: Texture2D = material.get_shader_parameter("color_map")
	expect(color.get_image().has_mipmaps(),"Stone detail has mipmaps for distant surfaces")
	var oak := MallFinishes.oak_floor()
	var oak_map: Texture2D = oak.get_shader_parameter("color_map")
	expect(oak_map.get_image().has_mipmaps(),"Wood grain has mipmaps for distant surfaces")
	world.queue_free()
	var group := Node3D.new(); root.add_child(group)
	var first := Image.create(4,4,false,Image.FORMAT_RGB8); first.fill(Color.WHITE)
	var second := Image.create(4,4,false,Image.FORMAT_RGB8); second.fill(Color(.7,.8,.9))
	var a := ImageTexture.create_from_image(first); var b := ImageTexture.create_from_image(second)
	for i in 3:
		var mat := MallFinishes.stone(); mat.set_shader_parameter("contact_map",a if i < 2 else b); mat.set_shader_parameter("has_contacts",true)
		Shapes.box(group,Vector3(1+i,1,1),Vector3(.4,.4,.4),mat)
	var stats := RenderChunks.build(group)
	expect(stats.source_meshes == 3 and stats.surfaces == 2,"Same-atlas geometry merges, distinct texture identities stay separate")
	var retained: Dictionary = {}
	for node in group.find_children("*","MeshInstance3D",true,false):
		for i in node.mesh.get_surface_count():
			var mat: ShaderMaterial = node.get_active_material(i)
			retained[mat.get_shader_parameter("contact_map").get_instance_id()] = true
	expect(retained.has(a.get_instance_id()) and retained.has(b.get_instance_id()),"Both embedded textures survive geometry batching")
	print("RENDER_MATERIAL_TESTS: ",checks," checks, ",failures," failures")
	quit(1 if failures else 0)
