class_name MallFinishes
extends RefCounted
static func plaster(color: Color) -> ShaderMaterial:
	var material := ShaderMaterial.new(); material.shader = preload("res://assets/plaster.gdshader")
	var linear := color.srgb_to_linear(); material.set_shader_parameter("paint_tint",Vector3(linear.r,linear.g,linear.b))
	return material
