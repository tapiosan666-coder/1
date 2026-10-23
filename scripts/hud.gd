class_name FindHUD
extends Control

signal play_pressed
signal resume_pressed
signal restart_pressed
signal skill_pressed(key: String)
signal exit_pressed
var mode := "title"
var run: IdentityRun
var ammo := 30
var reload_progress := -1.0
var elapsed := 0.0
var target_id := -1
var notice := ""
var notice_time := 0.0
var hit_time := 0.0
var combo := 0
var sonar_cooldown := 0.0
var pulse_cooldown := 0.0
var target_distance := 0.0
var player_position := Vector3.ZERO
var using_gun := false
var scan_progress := 0.0
var buttons: Control
var face_slider: HSlider
var skin_select: OptionButton
var hair_select: OptionButton
var font: Font
var ink := Color("eeecdf")
var muted := Color("8da4a6")
var lime := Color("b6f39b")
var orange := Color("f2b184")

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	font = ThemeDB.fallback_font
	buttons = Control.new()
	buttons.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	buttons.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(buttons)
	show_mode("title")

func _process(delta: float) -> void:
	notice_time = maxf(0, notice_time - delta)
	hit_time = maxf(0, hit_time - delta)
	queue_redraw()

func message(text: String) -> void:
	notice = text
	notice_time = 4.0

func _text(text: String, at: Vector2, size: int = 18, color: Color = ink) -> void:
	draw_string(font, at, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, color)

func _line(a: Vector2, b: Vector2, color: Color = Color("405456")) -> void:
	draw_line(a, b, color, 1, true)

func _draw() -> void:
	if font == null:
		return
	if mode == "title":
		draw_rect(Rect2(0, 0, 690, 900), Color(0.035, 0.07, 0.085, 0.96))
		draw_rect(Rect2(690, 0, 750, 900), Color(0.02, 0.04, 0.05, 0.12))
		_text("STUDIO / IDENTITY RESEARCH", Vector2(80, 78), 16, lime)
		_line(Vector2(80, 105), Vector2(610, 105))
		_text("FIND", Vector2(74, 230), 106)
		_text("YOURSELF", Vector2(74, 329), 106)
		_text("EVERY FACE IS YOURS. ONLY ONE IS YOU.", Vector2(82, 380), 18, lime)
		_text("A quiet mall. A crowd of reflections.", Vector2(82, 433), 21)
		_text("Scan the imitations. Find the original.", Vector2(82, 465), 21)
		_text("YOUR SHARED FACE", Vector2(82, 524), 14, muted)
		_text("SKIN", Vector2(82, 558), 13, muted)
		_text("HAIR", Vector2(258, 558), 13, muted)
		_text("FACE WIDTH", Vector2(434, 558), 13, muted)
		_text("WASD  Move    MOUSE  Look    SHIFT  Sprint", Vector2(82, 730), 16, muted)
		_text("HOLD LMB  Read one person / 2 s    RMB  Focus", Vector2(82, 758), 16, muted)
		_text("1  Reader    2  Pistol (unlock in TAB)    ESC  Pause", Vector2(82, 786), 16, muted)
		_line(Vector2(82, 831), Vector2(610, 831))
		_text("DEVELOPMENT BUILD  0.2  /  A-1F SECTOR  /  120 IDENTITIES", Vector2(82, 860), 13, muted)
		_text("A / ATRIUM", Vector2(1030, 790), 35)
		_text("01  —  THE FIRST REFLECTION", Vector2(1030, 820), 14, lime)
		return
	if run == null:
		return
	# Quiet header and large counters leave the center of the screen clear.
	draw_rect(Rect2(30, 25, 1380, 87), Color(0.035, 0.07, 0.085, 0.87))
	draw_rect(Rect2(30, 25, 4, 87), lime)
	_text("FIND YOURSELF", Vector2(55, 62), 24)
	_text("A / ATRIUM    •    1F", Vector2(55, 90), 14, muted)
	_text("IDENTITIES REMAINING", Vector2(550, 51), 13, muted)
	_text("%03d" % (run.population - run.cleared), Vector2(550, 91), 35)
	_text("/ %03d" % run.population, Vector2(630, 88), 18, muted)
	_text("ABILITY POINTS", Vector2(855, 51), 13, muted)
	_text("%04d AP" % run.ap, Vector2(855, 91), 35, lime)
	_text("ELAPSED", Vector2(1210, 51), 13, muted)
	_text("%02d:%02d" % [int(elapsed) / 60, int(elapsed) % 60], Vector2(1210, 89), 30)
	if mode == "play":
		var center := Vector2(720, 450)
		var c := lime if target_id >= 0 else ink
		if hit_time > 0:
			for offset in [Vector2(-1, -1), Vector2(1, -1), Vector2(-1, 1), Vector2(1, 1)]:
				draw_line(center + offset * 9, center + offset * 16, lime, 2, true)
		else:
			draw_circle(center, 2.0, c)
			for dir in [Vector2.LEFT, Vector2.RIGHT, Vector2.UP, Vector2.DOWN]:
				draw_line(center + dir * 9, center + dir * 14, c, 1, true)
		if target_id >= 0:
			_text("IDENTITY / %04d" % (target_id + 1), Vector2(765, 443), 13, muted)
			if using_gun:
				var count := mini(run.hits[target_id], run.required_hits())
				for i in run.required_hits():
					draw_rect(Rect2(765 + i * 19, 455, 14, 4), lime if i < count else Color("52686a"))
			else:
				_text("HOLD LMB / %.1f s" % (2.0 * (1 - scan_progress)), Vector2(765, 467), 14, lime)
		if not using_gun and scan_progress > 0:
			draw_arc(center, 25, -PI / 2, -PI / 2 + TAU * scan_progress, 64, lime, 3, true)
		if run.located:
			draw_rect(Rect2(498, 131, 444, 45), Color(0.08, 0.18, 0.17, 0.95))
			_text("ORIGINAL LOCATED / %.0f m / FOLLOW THE BEACON" % target_distance, Vector2(515, 159), 15, lime)
		if notice_time > 0:
			draw_rect(Rect2(420, 679, 650, 55), Color(0.035, 0.07, 0.085, 0.92))
			_text(notice, Vector2(438, 712), 16, lime)
		if combo > 1 and notice_time > 0:
			_text("%02d CHAIN" % combo, Vector2(1060, 665), 32, orange)
		_draw_minimap()
		draw_rect(Rect2(1130, 753, 280, 112), Color(0.035, 0.07, 0.085, 0.9))
		if using_gun:
			_text("[2] SCAN PISTOL", Vector2(1152, 779), 14, lime)
			_text("%02d" % ammo, Vector2(1150, 831), 45)
			_text("/ %02d  UNLIMITED" % run.magazine_size(), Vector2(1226, 828), 15, muted)
			if reload_progress >= 0:
				draw_rect(Rect2(1152, 846, 236 * reload_progress, 3), lime)
		else:
			_text("[1] IDENTITY READER", Vector2(1152, 779), 14, lime)
			_text("%03d%%" % int(scan_progress * 100), Vector2(1150, 825), 35)
			_text("ONE PERSON / 2 s / 6 m", Vector2(1152, 850), 13, muted)
		draw_rect(Rect2(310, 818, 780, 47), Color(0.035, 0.07, 0.085, 0.9))
		_text("TAB / SKILLS", Vector2(325, 846), 14, muted)
		_text("F / ECHO " + ("LOCKED" if run.upgrades.sonar == 0 else ("READY" if sonar_cooldown <= 0 else "%ds" % ceili(sonar_cooldown))), Vector2(535, 846), 14, lime if run.upgrades.sonar > 0 else muted)
		_text("Q / PULSE " + ("LOCKED" if run.upgrades.pulse == 0 else ("READY" if pulse_cooldown <= 0 else "%ds" % ceili(pulse_cooldown))), Vector2(800, 846), 14, lime if run.upgrades.pulse > 0 else muted)
		return
	draw_rect(Rect2(0, 0, 1440, 900), Color(0.025, 0.055, 0.065, 0.95))
	if mode == "skills":
		_text("BECOME MORE THAN A REFLECTION.", Vector2(70, 90), 36)
		_text("UPGRADE YOUR SEARCH     /     %d AP" % run.ap, Vector2(72, 130), 19, lime)
		_text("Purchased abilities last for this run. The world pauses while this panel is open.", Vector2(72, 163), 16, muted)
	elif mode == "pause":
		_text("TAKE A BREATH.", Vector2(460, 325), 52)
		_text("The search can wait.", Vector2(463, 370), 20, muted)
	elif mode == "win":
		_text("YOU FOUND YOURSELF.", Vector2(240, 300), 66, lime)
		_text("Among every reflection, you were always here.", Vector2(398, 354), 22)
		_text("%d scanned    /    %02d:%02d    /    %d AP remaining" % [run.cleared, int(elapsed) / 60, int(elapsed) % 60, run.ap], Vector2(452, 425), 20, muted)
		_text("The other identities remain in the mall.", Vector2(479, 466), 18, muted)
	elif mode == "map":
		_text("THE ATRIUM / A-1F", Vector2(100, 160), 40)
		_text("VISITED SECTOR", Vector2(102, 201), 16, lime)
		draw_rect(Rect2(310, 280, 820, 390), Color("253e44"))
		for x in range(4):
			for y in [0, 1]:
				draw_rect(Rect2(320 + x * 200, 290 + y * 260, 180, 110), Color("617269"))
		draw_rect(Rect2(620, 425, 200, 80), Color("71906b"))
		_text("ATRIUM GARDEN", Vector2(643, 470), 17)
		_text("A-1F is the only playable sector in this build.", Vector2(450, 733), 19, muted)
		_text("Other floors and fast travel are planned; no unvisited destination can be selected.", Vector2(318, 766), 16, muted)

func _draw_minimap() -> void:
	draw_rect(Rect2(30, 712, 250, 153), Color(0.035, 0.07, 0.085, 0.9))
	_text("SECTOR / A-1F", Vector2(48, 738), 13, lime)
	draw_rect(Rect2(49, 751, 212, 86), Color("243d43"))
	draw_rect(Rect2(135, 778, 40, 30), Color("718669"))
	var here := Vector2(155 + player_position.x * 2.7, 794 + player_position.z * 1.5)
	draw_circle(here, 4, lime)
	_text("M / FLOOR PLAN", Vector2(48, 854), 12, muted)

func show_mode(next: String) -> void:
	mode = next
	for child in buttons.get_children():
		buttons.remove_child(child)
		child.queue_free()
	match mode:
		"title":
			skin_select = _option(Vector2(82, 570), ["Sand", "Umber", "Rose"])
			hair_select = _option(Vector2(258, 570), ["Charcoal", "Chestnut", "Silver"])
			face_slider = HSlider.new()
			face_slider.position = Vector2(434, 570)
			face_slider.size = Vector2(160, 36)
			face_slider.min_value = 0.85
			face_slider.max_value = 1.15
			face_slider.step = 0.01
			face_slider.value = 1.0
			buttons.add_child(face_slider)
			_button("ENTER THE ATRIUM     →", Rect2(82, 638, 400, 58), func(): play_pressed.emit(), true)
		"pause":
			_button("RESUME SEARCH", Rect2(460, 420, 520, 58), func(): resume_pressed.emit(), true)
			_button("NEW RUN", Rect2(460, 498, 520, 54), func(): restart_pressed.emit())
			_button("QUIT", Rect2(460, 572, 520, 54), func(): exit_pressed.emit())
		"skills":
			var i := 0
			for key in IdentityRun.SKILLS:
				var skill: Dictionary = IdentityRun.SKILLS[key]
				var col := i % 4
				var row := i / 4
				var maxed: bool = run.upgrades[key] >= skill.max
				var text := "%s\n%s  [%d/%d]\n%s\n%s" % [skill.branch, skill.name, run.upgrades[key], skill.max, skill.detail, "MAX LEVEL" if maxed else "%d AP" % run.price(key)]
				var button := _button(text, Rect2(70 + col * 330, 206 + row * 171, 312, 148), func(): skill_pressed.emit(key))
				button.add_theme_font_size_override("font_size", 14)
				button.disabled = maxed or run.ap < run.price(key) or (key == "cat_speed" and run.upgrades.cat == 0) or (key in ["focus", "magazine", "reload", "range"] and run.upgrades.gun == 0)
				i += 1
			_button("BACK TO SEARCH  /  TAB", Rect2(70, 772, 420, 56), func(): resume_pressed.emit(), true)
		"win":
			_button("SEARCH AGAIN", Rect2(460, 530, 520, 62), func(): restart_pressed.emit(), true)
			_button("QUIT", Rect2(460, 612, 520, 54), func(): exit_pressed.emit())
		"map":
			_button("BACK TO SEARCH  /  M", Rect2(510, 806, 420, 55), func(): resume_pressed.emit(), true)
	queue_redraw()

func _option(at: Vector2, options: Array) -> OptionButton:
	var option := OptionButton.new()
	option.position = at
	option.size = Vector2(160, 36)
	for text in options:
		option.add_item(text)
	buttons.add_child(option)
	return option

func _button(text: String, rect: Rect2, callback: Callable, primary: bool = false) -> Button:
	var button := Button.new()
	button.text = text
	button.position = rect.position
	button.size = rect.size
	button.add_theme_font_size_override("font_size", 19)
	var style := StyleBoxFlat.new()
	style.bg_color = lime if primary else Color("1c343c")
	style.border_color = Color("4e686b")
	style.set_border_width_all(1)
	style.set_corner_radius_all(3)
	button.add_theme_stylebox_override("normal", style)
	var hover := style.duplicate() as StyleBoxFlat
	if primary:
		hover.bg_color = Color("d6ffc1")
	else:
		hover.bg_color = Color("34545b")
	button.add_theme_stylebox_override("hover", hover)
	button.add_theme_stylebox_override("pressed", hover)
	button.add_theme_color_override("font_color", Color("152b30") if primary else ink)
	button.add_theme_color_override("font_hover_color", Color("152b30") if primary else ink)
	button.add_theme_color_override("font_pressed_color", Color("152b30") if primary else ink)
	button.pressed.connect(callback)
	buttons.add_child(button)
	return button
