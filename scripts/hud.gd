class_name FindHUD
extends Control

signal item_selected(key: String)
signal graphics_selected(key: String)
signal play_pressed
signal resume_pressed
signal restart_pressed
signal travel_pressed(key: String)
signal skill_pressed(key: String)
signal exit_pressed
var mode := "title"
var skill_branch := 0
var skill_selected := "gun"
var cat_status := ""
var map_level := 0
var graphics_choice := "balanced"
var adapter_name := ""
var redraw_clock := 0.0
var cached_polygons: Dictionary = {}
var cached_polygon_bounds: Dictionary = {}
var loot: RunLoot
var nearby_cache := -1
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
var chain_cooldown := 0.0
var pulse_cooldown := 0.0
var target_distance := 0.0
var player_position := Vector3.ZERO
var cached_map_bounds: Dictionary = {}
var location_name := "A館1階 / ショッピングモール"
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
	font = preload("res://assets/fonts/NotoSansCJKjp-Regular.otf")
	theme = preload("res://assets/ui_theme.tres")
	buttons = Control.new()
	buttons.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	buttons.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(buttons)
	show_mode("title")

func _process(delta: float) -> void:
	notice_time = maxf(0, notice_time - delta)
	hit_time = maxf(0, hit_time - delta)
	redraw_clock += delta
	if redraw_clock >= 1.0/30 and mode in ["play","title"]:
		redraw_clock = 0
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
		_text("自分を探す、奇妙なショッピングモール", Vector2(80, 78), 16, lime)
		_line(Vector2(80, 105), Vector2(610, 105))
		_text("FIND", Vector2(74, 230), 106)
		_text("YOURSELF", Vector2(74, 329), 106)
		_text("全員が同じ顔。本当の自分は、たった1人。", Vector2(82, 380), 18, lime)
		_text("静かなモールに、あなたと同じ顔の人々。", Vector2(82, 433), 21)
		_text("偽物をスキャンし、本当の自分を探そう。", Vector2(82, 465), 21)
		_text("全員に共通する、あなたの顔", Vector2(82, 524), 14, muted)
		_text("肌の色", Vector2(82, 558), 13, muted)
		_text("髪の色", Vector2(258, 558), 13, muted)
		_text("顔の幅", Vector2(434, 558), 13, muted)
		_text("WASD：移動　マウス：視点　Shift：ダッシュ", Vector2(82, 730), 16, muted)
		_text("左クリック長押し：2秒スキャン　右クリック：照準", Vector2(82, 758), 16, muted)
		_text("1：初期スキャナー　2：購入済みの銃　Esc：一時停止", Vector2(82, 786), 16, muted)
		_line(Vector2(82, 831), Vector2(610, 831))
		_text("日本語開発版 0.12 ／ A・B・C館を探索 ／ 300人", Vector2(82, 860), 13, muted)
		_text("A館 / 中央通路", Vector2(1000, 790), 30)
		_text("店舗・フードコート・お手洗い", Vector2(1000, 820), 14, lime)
		return
	if run == null:
		return
	# Quiet header and large counters leave the center of the screen clear.
	draw_rect(Rect2(30, 25, 1380, 87), Color(0.035, 0.07, 0.085, 0.87))
	draw_rect(Rect2(30, 25, 4, 87), lime)
	_text("FIND YOURSELF", Vector2(55, 62), 24)
	_text(location_name, Vector2(55, 90), 14, muted)
	_text("残りの人数", Vector2(550, 51), 13, muted)
	_text("%03d" % (run.population - run.cleared), Vector2(550, 91), 35)
	_text("/ %03d" % run.population, Vector2(630, 88), 18, muted)
	_text("アビリティポイント", Vector2(855, 51), 13, muted)
	_text("%04d AP" % run.ap, Vector2(855, 91), 35, lime)
	_text("経過時間", Vector2(1210, 51), 13, muted)
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
			_text("対象 / %04d" % (target_id + 1), Vector2(765, 443), 13, muted)
			if using_gun:
				var count := mini(run.hits[target_id], run.required_hits())
				for i in run.required_hits():
					draw_rect(Rect2(765 + i * 19, 455, 14, 4), lime if i < count else Color("52686a"))
			else:
				_text("左クリック長押し / 残り %.1f秒" % (2.0 * (1 - scan_progress)), Vector2(765, 467), 14, lime)
		if not using_gun and scan_progress > 0:
			draw_arc(center, 25, -PI / 2, -PI / 2 + TAU * scan_progress, 64, lime, 3, true)
		if run.located:
			draw_rect(Rect2(498, 131, 444, 45), Color(0.08, 0.18, 0.17, 0.95))
			_text("本物を発見 / %.0fm / マーカーへ向かおう" % target_distance, Vector2(515, 159), 15, lime)
		if notice_time > 0:
			draw_rect(Rect2(420, 679, 650, 55), Color(0.035, 0.07, 0.085, 0.92))
			var notice_size := 16
			while font.get_string_size(notice, HORIZONTAL_ALIGNMENT_LEFT, -1, notice_size).x > 610 and notice_size > 12:
				notice_size -= 1
			_text(notice, Vector2(438, 712), notice_size, lime)
		if combo > 1 and notice_time > 0:
			_text("%02d 連続スキャン" % combo, Vector2(1060, 665), 32, orange)
		if nearby_cache >= 0:
			draw_rect(Rect2(500,505,440,45),Color(.04,.09,.10,.94))
			_text("G / %s宝箱を開ける" % loot.chests[nearby_cache].rarity,Vector2(545,535),18,orange)
		if loot != null:
			_text("I / バッグ　 X / %s ×%d" % [RunLoot.ITEMS[loot.selected].name,loot.inventory[loot.selected]],Vector2(335,792),18,orange)
			var active := ""
			if loot.clock_left > 0: active += "時間停止 %d秒　" % ceili(loot.clock_left)
			if loot.cart_left > 0: active += "カート %d秒　" % ceili(loot.cart_left)
			if loot.disco_left > 0: active += "フィーバー %d秒" % ceili(loot.disco_left)
			_text(active,Vector2(335,756),14,lime)
		_draw_minimap()
		draw_rect(Rect2(1130, 753, 280, 112), Color(0.035, 0.07, 0.085, 0.9))
		if using_gun:
			_text("[2] スキャン銃", Vector2(1152, 779), 14, lime)
			_text("%02d" % ammo, Vector2(1150, 831), 45)
			_text("/ %02d　予備弾∞" % run.magazine_size(), Vector2(1226, 828), 15, muted)
			if reload_progress >= 0:
				draw_rect(Rect2(1152, 846, 236 * reload_progress, 3), lime)
		else:
			_text("[1] 初期スキャナー", Vector2(1152, 779), 14, lime)
			_text("%03d%%" % int(scan_progress * 100), Vector2(1150, 825), 35)
			_text("単体 / 2秒 / 射程6m", Vector2(1152, 850), 13, muted)
		draw_rect(Rect2(310, 818, 780, 70), Color(0.035, 0.07, 0.085, 0.9))
		if not cat_status.is_empty(): _text(cat_status,Vector2(48,142),17,lime)
		_text("Tab / スキル購入", Vector2(325, 846), 14, muted)
		_text("F / ソナー " + ("未解放" if run.upgrades.sonar == 0 else ("使用可能" if sonar_cooldown <= 0 else "%d秒" % ceili(sonar_cooldown))), Vector2(535, 846), 14, lime if run.upgrades.sonar > 0 else muted)
		_text("E / 連鎖スキャン " + ("未解放" if run.upgrades.chain == 0 else ("使用可能" if chain_cooldown <= 0 else "%d秒" % ceili(chain_cooldown))), Vector2(800, 870), 14, lime if run.upgrades.chain > 0 else muted)
		_text("Q / 範囲スキャン " + ("未解放" if run.upgrades.pulse == 0 else ("使用可能" if pulse_cooldown <= 0 else "%d秒" % ceili(pulse_cooldown))), Vector2(800, 846), 14, lime if run.upgrades.pulse > 0 else muted)
		return
	draw_rect(Rect2(0, 0, 1440, 900), Color(0.025, 0.055, 0.065, 0.95))
	if mode == "skills":
		_text("探索する力を、手に入れよう。", Vector2(70, 90), 36)
		_text("スキル購入・強化　／　所持 %d AP" % run.ap, Vector2(72, 130), 19, lime)
		_text("4系統から選び、右側で効果と購入条件を確認。この画面ではゲームが一時停止します。", Vector2(72, 163), 16, muted)
	elif mode == "pause":
		_text("ひと休みしましょう。", Vector2(460, 325), 52)
		_text("準備ができたら、探索を再開できます。", Vector2(463, 370), 20, muted)
		_text("画質設定 / 軽量は影と描画解像度を下げます",Vector2(460,650),16,muted)
		_text("使用中のGPU："+adapter_name,Vector2(140,790),14,muted)
	elif mode == "win":
		_text("本当の自分を見つけた。", Vector2(330, 300), 62, lime)
		_text("同じ顔の人々の中に、あなたは確かにいた。", Vector2(398, 354), 22)
		_text("処理 %d人　／　%02d:%02d　／　残り %d AP" % [run.cleared, int(elapsed) / 60, int(elapsed) % 60, run.ap], Vector2(452, 425), 20, muted)
		_text("ほかの人々は、モールに残っています。", Vector2(479, 466), 18, muted)
	elif mode == "inventory":
		_text("探索アイテム / バッグ",Vector2(70,150),40)
		_text("宝箱で入手した使い切りアイテムです。選んで探索に戻り、Xで使用します。",Vector2(72,193),17,muted)
	elif mode == "map":
		_text("A・B・C館 / %sの案内図" % Mall.floor_title(map_level), Vector2(100, 160), 40)
		_text("訪問した案内ポイントのみ移動できます ／ Tabでファストトラベルを購入", Vector2(102, 201), 16, lime)
		var frame := Rect2(100, 270, 1240, 325)
		_draw_plan(frame)
		if map_level == 0:
			_text("フードコート", _plan_point(Vector2(49, -47),frame), 16)
			_text("食品スーパー", _plan_point(Vector2(7,36),frame),16)
			_text("お手洗い", _plan_point(Vector2(-87, 42),frame), 16)
			_text("中央通路", _plan_point(Vector2(-5, 3),frame), 16)
			_text("西駐車場",_plan_point(Vector2(-168,4),frame),16)
		elif map_level == -1:
			_text("食品街",_plan_point(Vector2(-78,0),frame),16)
		elif map_level == 3:
			_text("庭園・休憩",_plan_point(Vector2(-82,-16),frame),16)
		_text("西側階段",_plan_point(Vector2(-111,-18),frame),13)
		if map_level == Mall.level_at(player_position.y): draw_circle(_map_point(Vector2(player_position.x, player_position.z), frame), 6, lime)
		for key in Mall.HUBS:
			var p: Vector3 = Mall.hub_position(key)
			if Mall.level_at(p.y) != map_level: continue
			draw_circle(_map_point(Vector2(p.x,p.z),frame),5,lime if run.visited.has(key) else muted)
		if map_level in [0,1,2]:
			_text("B館",_plan_point(Vector2(-340,0),frame),16)
			_text("B館奥の売り場",_plan_point(Vector2(-414,0),frame),13)
		if map_level == 0: _text("C館 / 屋外広場",_plan_point(Vector2(-410,-143),frame),15)
		_text("A↔B：2階連絡通路・1階歩行路 ／ B↔C：B館1階の北西連絡通路",Vector2(120,626),15,muted)

func _draw_minimap() -> void:
	draw_rect(Rect2(30, 712, 250, 153), Color(0.035, 0.07, 0.085, 0.9))
	_text("現在地 / %s%s" % [Mall.building_name(player_position),Mall.floor_title(Mall.level_at(player_position.y))], Vector2(48, 738), 13, lime)
	var frame := Rect2(49, 751, 212, 86)
	_draw_plan(frame)
	var here := _map_point(Vector2(player_position.x, player_position.z), frame)
	draw_circle(here, 4, lime)
	_text("M / フロアマップ", Vector2(48, 854), 12, muted)

func _plan_point(p: Vector2,frame: Rect2) -> Vector2:
	var q := MallCurve.world(Vector3(p.x,0,p.y))
	return _map_point(Vector2(q.x,q.z),frame)

func _map_point(p: Vector2, frame: Rect2) -> Vector2:
	var level := map_level if mode == "map" else Mall.level_at(player_position.y)
	if not cached_map_bounds.has(level):
		var bounds := Rect2()
		for region in Mall.plan_regions(level):
			for at in MallCurve.polygon(region):
				if bounds.size == Vector2.ZERO: bounds = Rect2(at,Vector2(.001,.001))
				else: bounds = bounds.expand(at)
		cached_map_bounds[level] = bounds.grow(6)
	var bounds: Rect2 = cached_map_bounds[level]
	if frame.size.x < 400: bounds = Rect2(Vector2(player_position.x-60,player_position.z-30),Vector2(120,60))
	var scale_factor := minf(frame.size.x / bounds.size.x, frame.size.y / bounds.size.y)
	return frame.position + (frame.size - bounds.size * scale_factor) / 2 + (p - bounds.position) * scale_factor

func _draw_plan(frame: Rect2) -> void:
	draw_rect(frame, Color("14272d"))
	var level := map_level if mode == "map" else Mall.level_at(player_position.y)
	for region in CWing.regions(level): _draw_region(region,frame,Color("879781"),true)
	for region in BWing.regions(level): _draw_region(region,frame,Color("6b807e"),true)
	_draw_region(Rect2(-112,-24,22,24),frame,Color("344b50"),true)
	for x in [-107.2,-101.2]: _draw_region(Rect2(x,-20,2.4,14),frame,Color("758a84"))
	for region in MallAnnex.regions(level): _draw_region(region,frame,Color("7e897a"),true)
	if level != 0:
		if level in [1,2]:
			for region in Mall.upper_regions(): _draw_region(region,frame,Color("899387"),true)
		return
	for region in Mall.floor_regions:
		_draw_region(region,frame,Color("42535a"))
	for area in [Mall.MAIN,Mall.PROMENADE,Mall.FOOD,Mall.RESTROOM,Mall.MARKET,Mall.COURT,Mall.READING,Mall.STOCK]:
		_draw_region(area,frame,Color("677d70") if area in [Mall.FOOD,Mall.MARKET] else Color("486e82") if area == Mall.RESTROOM else Color("899387"))
	for side in [-1,1]:
		for x in Mall.SHOP_CENTERS:
			if not Mall.has_shop(x,side): continue
			var rect := Rect2(x-9,-24 if side < 0 else 8,18,16)
			_draw_region(rect,frame,Color("394f58"),true)


func _draw_region(rect: Rect2,frame: Rect2,color: Color,border: bool = false) -> void:
	if not cached_polygons.has(rect):
		cached_polygons[rect] = MallCurve.polygon(rect)
		var bounds := Rect2(cached_polygons[rect][0],Vector2(.001,.001))
		for point in cached_polygons[rect]: bounds = bounds.expand(point)
		cached_polygon_bounds[rect] = bounds
	if frame.size.x < 400 and not Rect2(Vector2(player_position.x-60,player_position.z-30),Vector2(120,60)).intersects(cached_polygon_bounds[rect]): return
	var polygon := PackedVector2Array()
	for point in cached_polygons[rect]: polygon.append(_map_point(point,frame))
	var limit := PackedVector2Array([frame.position,Vector2(frame.end.x,frame.position.y),frame.end,Vector2(frame.position.x,frame.end.y)])
	for clipped in Geometry2D.intersect_polygons(polygon,limit): draw_colored_polygon(clipped,color)
	if border and frame.size.x > 400:
		polygon.append(polygon[0]); draw_polyline(polygon,Color("839796"),1,true)

func set_map_floor(level: int) -> void:
	if level not in [-1,0,1,2,3]: return
	map_level = level
	show_mode("map")

func show_mode(next: String) -> void:
	if next == "map" and mode != "map": map_level = Mall.level_at(player_position.y)
	mode = next
	for child in buttons.get_children():
		buttons.remove_child(child)
		child.queue_free()
	match mode:
		"title":
			skin_select = _option(Vector2(82, 570), ["明るい肌", "濃い肌", "赤みのある肌"])
			hair_select = _option(Vector2(258, 570), ["黒", "茶", "銀"])
			face_slider = HSlider.new()
			face_slider.position = Vector2(434, 570)
			face_slider.size = Vector2(160, 36)
			face_slider.min_value = 0.85
			face_slider.max_value = 1.15
			face_slider.step = 0.01
			face_slider.value = 1.0
			buttons.add_child(face_slider)
			_button("探索をはじめる　→", Rect2(82, 638, 400, 58), func(): play_pressed.emit(), true)
		"pause":
			_button("探索を再開", Rect2(460, 420, 520, 58), func(): resume_pressed.emit(), true)
			_button("最初からやり直す", Rect2(460, 498, 520, 54), func(): restart_pressed.emit())
			_button("ゲームを終了", Rect2(460, 572, 520, 54), func(): exit_pressed.emit())
			var i := 0
			for key in GraphicsOptions.PRESETS:
				_button(GraphicsOptions.PRESETS[key].name,Rect2(460+i*180,670,160,45),func(): graphics_selected.emit(key),graphics_choice == key)
				i += 1
		"skills":
			SkillPanel.build(self)
		"win":
			_button("もう一度探す", Rect2(460, 530, 520, 62), func(): restart_pressed.emit(), true)
			_button("ゲームを終了", Rect2(460, 612, 520, 54), func(): exit_pressed.emit())
		"inventory":
			var index := 0
			for key in RunLoot.ITEMS:
				var item: Dictionary = RunLoot.ITEMS[key]
				var text := "%s
所持 %d

%s

%s" % [item.name,loot.inventory[key],item.detail,"選択中" if loot.selected == key else "選んで戻る"]
				var button := _button("",Rect2(70+(index%4)*330,235+(index/4)*240,312,215),func(): item_selected.emit(key))
				button.disabled = loot.inventory[key] <= 0
				var copy := Label.new()
				copy.name = "ItemCopy"
				copy.position = Vector2(12,12); copy.size = Vector2(288,191)
				copy.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
				copy.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
				copy.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
				copy.mouse_filter = Control.MOUSE_FILTER_IGNORE
				copy.add_theme_font_size_override("font_size",16)
				copy.add_theme_color_override("font_color",muted if button.disabled else ink)
				copy.text = text
				button.add_child(copy)
				index += 1
			_button("探索に戻る / I",Rect2(70,780,420,56),func(): resume_pressed.emit(),true)
		"map":
			for i in 5:
				var level := i-1
				_button(Mall.floor_title(level),Rect2(100+i*250,218,238,34),func(): set_map_floor(level),level == map_level)
			var index := 0
			for key in Mall.HUBS:
				var label: String = key + (" / 移動" if run.can_travel(key) else " / 要スキル" if run.visited.has(key) else " / 未訪問")
				var button := _button(label,Rect2(100+(index%5)*250,650+(index/5)*44,240,40),func(): travel_pressed.emit(key))
				button.add_theme_font_size_override("font_size",14)
				button.disabled = not run.can_travel(key)
				index += 1
			_button("探索に戻る / M", Rect2(510, 844, 420, 45), func(): resume_pressed.emit(), true)
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
	button.add_theme_stylebox_override("disabled", style)
	button.add_theme_color_override("font_disabled_color", Color("9ca9a8"))
	button.add_theme_color_override("font_color", Color("152b30") if primary else ink)
	button.add_theme_color_override("font_hover_color", Color("152b30") if primary else ink)
	button.add_theme_color_override("font_pressed_color", Color("152b30") if primary else ink)
	button.pressed.connect(callback)
	buttons.add_child(button)
	return button
