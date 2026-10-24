class_name MallFinishes
extends RefCounted
static func plaster(color: Color) -> ShaderMaterial:
	var material := ShaderMaterial.new(); material.shader = preload("res://assets/plaster.gdshader")
	material.set_shader_parameter("paint_tint",color)
	material.set_shader_parameter("surface_map",preload("res://assets/interiors/paint_surface.png"))
	return material

static func stone(albedo_scale: float = 1.0) -> ShaderMaterial:
	var material := ShaderMaterial.new(); material.shader = preload("res://assets/terrazzo.gdshader")
	material.set_shader_parameter("color_map",preload("res://assets/interiors/limestone_color.png"))
	material.set_shader_parameter("surface_map",preload("res://assets/interiors/limestone_surface.png"))
	material.set_shader_parameter("albedo_scale",albedo_scale)
	return material

static func oak_floor() -> ShaderMaterial:
	var material := ShaderMaterial.new(); material.shader = preload("res://assets/oak_floor.gdshader")
	material.set_shader_parameter("color_map",preload("res://assets/interiors/oak_color.png"))
	material.set_shader_parameter("surface_map",preload("res://assets/interiors/oak_surface.png"))
	return material
