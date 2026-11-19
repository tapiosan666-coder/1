extends RefCounted

const RESOLUTIONS = [Vector2i(1920, 1080), Vector2i(2560, 1440), Vector2i(3840, 2160)]
const LIMITS = [30, 60, 120, 144, 0]
const GRAPHICS_NAMES = ["標準", "高画質（v33相当）", "軽量"]
const PROFILES = [
	{"scale": 0.90, "msaa": Viewport.MSAA_DISABLED, "ssao": true, "ssil": false, "ssr": false},
	{"scale": 1.0, "msaa": Viewport.MSAA_4X, "ssao": true, "ssil": true, "ssr": true},
	{"scale": 0.75, "msaa": Viewport.MSAA_DISABLED, "ssao": false, "ssil": false, "ssr": false},
]

var resolution_index: int = 0
var fps_limit: int = 144
var vsync: bool = true
var graphics_index: int = 0
var sound_level: float = 0.7
var config_path: String = "user://site-v7-settings.cfg"

func restore() -> void:
	var config := ConfigFile.new()
	if config.load(config_path) == OK:
		resolution_index = clampi(int(config.get_value("display", "resolution_index", 0)), 0, RESOLUTIONS.size() - 1)
		var cap := int(config.get_value("display", "fps_limit", 144))
		fps_limit = cap if cap in LIMITS else 144
		vsync = bool(config.get_value("display", "vsync", true))
		graphics_index = clampi(int(config.get_value("display", "graphics_index", 0)), 0, PROFILES.size() - 1)
		sound_level = clampf(float(config.get_value("sound", "level", 0.7)), 0.0, 1.0)
	apply(false)

func apply(persist: bool = true) -> void:
	var resolution: Vector2i = RESOLUTIONS[resolution_index]
	var window: Window = Engine.get_main_loop().root
	window.content_scale_size = Vector2i(1920, 1080)
	window.content_scale_mode = Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	window.size = resolution
	Engine.max_fps = fps_limit
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED if vsync else DisplayServer.VSYNC_DISABLED)
	apply_graphics(window)
	if persist:
		var config := ConfigFile.new()
		config.set_value("display", "resolution_index", resolution_index)
		config.set_value("display", "fps_limit", fps_limit)
		config.set_value("display", "vsync", vsync)
		config.set_value("display", "graphics_index", graphics_index)
		config.set_value("sound", "level", sound_level)
		var result := config.save(config_path)
		if result != OK:
			push_warning("画面設定を保存できませんでした: %s" % error_string(result))

func apply_graphics(window: Viewport) -> void:
	var profile: Dictionary = PROFILES[graphics_index]
	window.scaling_3d_mode = Viewport.SCALING_3D_MODE_BILINEAR
	window.scaling_3d_scale = profile.scale
	window.msaa_3d = profile.msaa
	window.screen_space_aa = Viewport.SCREEN_SPACE_AA_DISABLED if graphics_index == 1 else Viewport.SCREEN_SPACE_AA_FXAA
	var environment: Environment = window.world_3d.environment
	if environment == null:
		return
	environment.ssao_enabled = profile.ssao
	environment.ssil_enabled = profile.ssil
	environment.ssr_enabled = profile.ssr

func snapshot() -> Dictionary:
	var window: Window = Engine.get_main_loop().root
	return {
		"requested_resolution": [RESOLUTIONS[resolution_index].x, RESOLUTIONS[resolution_index].y],
		"window_size": [window.size.x, window.size.y],
		"fps_limit": Engine.max_fps,
		"vsync_requested": vsync,
		"physics_ticks": Engine.physics_ticks_per_second,
		"graphics_index": graphics_index,
		"graphics_name": GRAPHICS_NAMES[graphics_index],
		"render_scale": window.scaling_3d_scale,
		"sound_level": sound_level,
		"note": "VSync and display refresh can impose a lower real FPS"
	}
