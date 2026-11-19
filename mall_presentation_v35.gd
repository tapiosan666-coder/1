extends Node

const LOCATION_CHECK_MS := 1200
const CONTROLS := "WASD  移動    Shift  速歩    F  扉・EV    M  館内マップ    Esc  設定\nF1  A館    F2  B館    F3  C館    H  操作ガイド"

var game: Node3D
var controls: Label
var last_check: int = -LOCATION_CHECK_MS
var label: String = "A館  1F"
var controls_until: int
var pin_caption := ""
var pin_id := ""

func setup(g: Node3D) -> void:
	game = g
	name = "MallPresentation"
	var hud: Label = game.hud
	hud.position = Vector2(28, 25)
	hud.add_theme_font_size_override("font_size", 21)
	hud.add_theme_stylebox_override("normal", card_style())
	hud.add_theme_color_override("font_color", Color("#f5f4ea"))
	for child in hud.get_parent().get_children():
		if child is Label and child != hud:
			controls = child
			break
	if controls != null:
		controls.position = Vector2(28, 956)
		controls.add_theme_font_size_override("font_size", 18)
		controls.add_theme_color_override("font_color", Color("#f5f4ea"))
		controls.add_theme_stylebox_override("normal", card_style())
	show_controls(14000)
	refresh()

func card_style() -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.032, 0.061, 0.075, 0.86)
	style.border_color = Color(0.60, 0.83, 0.83, 0.35)
	style.set_border_width_all(1)
	style.set_corner_radius_all(8)
	style.content_margin_left = 15
	style.content_margin_right = 16
	style.content_margin_top = 8
	style.content_margin_bottom = 9
	return style

func show_controls(duration: int = 12000) -> void:
	controls_until = Time.get_ticks_msec() + duration

func refresh() -> void:
	var now := Time.get_ticks_msec()
	var hud: Label = game.hud
	var map_screen = game.ui.map
	var selected_id := "" if map_screen.pinned.is_empty() else str(map_screen.pinned.item.id)
	if now - last_check >= LOCATION_CHECK_MS or selected_id != pin_id:
		pin_id = selected_id
		last_check = now
		var location: Dictionary = map_screen.floor_at(map_screen.world_plan_point(), game.player.global_position.y)
		if not location.is_empty():
			label = map_screen.floor_title(location)
		pin_caption = map_screen.pin_walking_caption(location, map_screen.world_plan_point(), game.player.global_position.y)
	if controls != null:
		var expanded := now < controls_until
		controls.position.y = 956.0 if expanded else 1003.0
		controls.text = CONTROLS if expanded else "M  館内マップ    H  操作ガイド"
		controls.visible = game.ui.overlay.is_empty() and hud.visible
	var message := label
	if not pin_caption.is_empty():
		message += "\n" + pin_caption
	if game.player.belt_id != "":
		message += "   エスカレーター"
	if game.notice_seconds > 0.0:
		message += "\n" + game.interaction_notice
	if game.developer_mode():
		var point: Vector3 = game.player.global_position
		message += "\n%.1f / %.2f / %.1f m   FPS %d" % [point.x, point.y, point.z, Engine.get_frames_per_second()]
	hud.text = message
