class_name GraphicsOptions
extends RefCounted
const PRESETS := {
 "low":{"name":"軽量","scale":.75,"msaa":0,"shadow":false,"shadow_range":0.,"detail":18.,"distance":100.},
 "balanced":{"name":"標準","scale":1.,"msaa":0,"shadow":true,"shadow_range":40.,"detail":26.,"distance":140.},
 "high":{"name":"高画質","scale":1.,"msaa":1,"shadow":true,"shadow_range":70.,"detail":38.,"distance":190.}
}
static func load_choice() -> String:
	var config := ConfigFile.new()
	if config.load("user://graphics.cfg") != OK: return "balanced"
	var choice: Variant = config.get_value("graphics","preset","balanced")
	return choice if choice is String and PRESETS.has(choice) else "balanced"
static func apply(game: Node3D,choice: String,save: bool = true) -> void:
	if not PRESETS.has(choice): return
	var preset: Dictionary = PRESETS[choice]
	game.get_viewport().msaa_3d = preset.msaa
	game.get_viewport().scaling_3d_scale = preset.scale
	for node in game.get_children():
		if node is DirectionalLight3D: node.shadow_enabled = preset.shadow; node.directional_shadow_max_distance = maxf(1,preset.shadow_range)
	game.crowd.detail_distance = preset.detail; game.crowd.draw_distance = preset.distance
	game.hud.graphics_choice = choice
	if save:
		var config := ConfigFile.new(); config.set_value("graphics","preset",choice); config.save("user://graphics.cfg")
