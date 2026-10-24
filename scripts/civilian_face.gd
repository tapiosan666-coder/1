class_name CivilianFace
extends RefCounted
## One small float texture shares eye motion across the same visible slots as the body.
var texture:ImageTexture
var bytes:PackedByteArray
var capacity:int
func _init(population:int)->void:
	capacity=maxi(1,population);bytes.resize(capacity*16)
	texture=ImageTexture.create_from_image(Image.create_from_data(1,capacity,false,Image.FORMAT_RGBAF,bytes))
func install(parts:Array)->void:
	for part:Dictionary in parts:
		if part.name not in ["head","hair","eye_l","eye_r"]:continue
		var mesh:Mesh=part.instances.mesh
		for surface in mesh.get_surface_count():
			var old:Material=mesh.surface_get_material(surface)
			if part.name in ["eye_l","eye_r"]:
				var eye:=ShaderMaterial.new();eye.shader=preload("res://assets/civilian_eye.gdshader")
				eye.resource_name=old.resource_name
				eye.set_shader_parameter("eye_tint",old.albedo_color)
				eye.set_shader_parameter("feature_kind",1 if old.resource_name.begins_with("Iris") else 2 if old.resource_name.begins_with("Ink") else 0)
				eye.set_shader_parameter("expression_palette",texture);mesh.surface_set_material(surface,eye)
				eye.set_shader_parameter("eye_side",-1.0 if part.name=="eye_l" else 1.0)
			elif part.name=="hair":
				old.next_pass=null
			elif old is ShaderMaterial and old.shader.resource_path=="res://assets/hair.gdshader":
				old.set_shader_parameter("brow_surface",true)
			elif old is StandardMaterial3D and old.resource_name.begins_with("Ink"):
				var ink:=ShaderMaterial.new();ink.shader=preload("res://assets/civilian_expression_ink.gdshader");ink.resource_name=old.resource_name
				mesh.surface_set_material(surface,ink)
func update(ids:Array[int],motions:Dictionary)->void:
	for slot in ids.size():
		var motion:Dictionary=motions[ids[slot]];var gaze:Vector2=motion.get("iris",motion.get("eyes",Vector2.ZERO))
		bytes.encode_float(slot*16,gaze.x);bytes.encode_float(slot*16+4,gaze.y)
		bytes.encode_float(slot*16+8,motion.expression);bytes.encode_float(slot*16+12,motion.blink)
	texture.update(Image.create_from_data(1,capacity,false,Image.FORMAT_RGBAF,bytes))
