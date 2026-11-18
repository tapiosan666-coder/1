extends Control

signal close_requested

const FILTERS = [
 ["すべて", []],
 ["店舗", ["店舗"]],
 ["トイレ", ["トイレ"]],
 ["上下階の移動", ["EV", "階段", "エスカレーター"]],
 ["広場・設備", ["広場", "庭園", "催事", "休憩・施設", "休憩所", "ロッカー"]],
 ["駐車場", ["駐車場"]],
]
const COLORS = {
 "庭園": Color("#66856c"), "休憩所": Color("#73998b"), "ロッカー": Color("#6e8c99"),
 "店舗": Color("#346481"), "広場": Color("#527d68"), "EV": Color("#94ab79"),
 "階段": Color("#d9ba73"), "エスカレーター": Color("#d9ba73"),
 "トイレ": Color("#ab80aa"), "吹抜": Color("#17242c"), "催事": Color("#c99167"),
 "休憩・施設": Color("#73998b"), "駐車場": Color("#697581"),
}
const PANEL_COLOR = Color("#12232c")
const MAP_COLOR = Color("#172a34")
const INK = Color("#f3f6f4")
const MUTED = Color("#afc4cb")
const ACCENT = Color("#f4c46c")

var data: Array = []
var player: CharacterBody3D
var font: Font
var wing: String = "B"
var floor_label: String = "1F"
var selected: Dictionary = {}
var scale_m: float = 1.0
var offset := Vector2.ZERO
var map_rect := Rect2(407, 163, 1469, 789)
var wing_select: OptionButton
var floor_select: OptionButton
var search: LineEdit
var filter_select: OptionButton
var scope_select: OptionButton
var results: ItemList
var result_rows: Array[Dictionary] = []
var summary_label: Label
var location_label: Label
var details_label: Label
var item_index: Array[Dictionary] = []
var current_floor: Dictionary = {}
var pinned: Dictionary = {}
var result_floor_only: bool = true
var destination_index_ready: bool = false
var brand_registry: Dictionary = {}
var geometry_cache: Dictionary = {}
var map_labels: Array[Dictionary] = []

func setup(floors: Array, body: CharacterBody3D, interface_font: Font, brands: Dictionary = {}) -> void:
 data = floors
 player = body
 font = interface_font
 brand_registry = brands
 set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
 # The viewport uses a 1920 x 1080 canvas at all supported resolutions.
 var backdrop := ColorRect.new()
 backdrop.show_behind_parent = true
 backdrop.color = Color("#0c1a22")
 backdrop.mouse_filter = Control.MOUSE_FILTER_IGNORE
 add_child(backdrop)
 backdrop.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)

 add_at(make_label("館内マップ", 42), Rect2(39, 23, 600, 57))
 location_label = make_label("", 21, MUTED)
 add_at(location_label, Rect2(43, 87, 650, 37))
 var close_button := make_button("閉じる  Esc")
 close_button.pressed.connect(func(): close_requested.emit())
 add_at(close_button, Rect2(1722, 43, 154, 55))
 var locate_button := make_button("現在地へ")
 locate_button.pressed.connect(return_to_location)
 add_at(locate_button, Rect2(1556, 43, 146, 55))

 add_at(make_label("表示する館・階", 20, MUTED), Rect2(46, 166, 309, 37))
 wing_select = OptionButton.new()
 var wings := {}
 for f: Dictionary in data:
  wings[str(f.wing)] = true
 for id: String in wings:
  wing_select.add_item(wing_title(id))
  wing_select.set_item_metadata(wing_select.item_count - 1, id)
 wing_select.item_selected.connect(func(index: int):
  wing = str(wing_select.get_item_metadata(index))
  refresh_floors()
 )
 add_at(wing_select, Rect2(46, 206, 184, 54))

 floor_select = OptionButton.new()
 floor_select.item_selected.connect(func(index: int):
  floor_label = floor_select.get_item_text(index)
  choose()
 )
 add_at(floor_select, Rect2(245, 206, 111, 54))

 add_at(make_label("店名・施設を探す", 20, MUTED), Rect2(46, 286, 313, 35))
 search = LineEdit.new()
 search.placeholder_text = "店名、ID、設備名"
 search.clear_button_enabled = true
 search.text_changed.connect(func(_text: String): refresh_directory())
 search.text_submitted.connect(func(_text: String):
  if not result_rows.is_empty():
   results.select(0)
   pin_directory_item(0)
 )
 add_at(search, Rect2(46, 327, 310, 52))

 filter_select = OptionButton.new()
 for filter: Array in FILTERS:
  filter_select.add_item(filter[0])
 filter_select.item_selected.connect(func(_index: int): refresh_directory())
 add_at(filter_select, Rect2(46, 396, 310, 48))

 scope_select = OptionButton.new()
 scope_select.add_item("この階から探す")
 scope_select.add_item("全館から探す")
 scope_select.item_selected.connect(func(index: int):
  result_floor_only = index == 0
  refresh_directory()
 )
 add_at(scope_select, Rect2(46, 457, 310, 46))

 summary_label = make_label("", 17, MUTED)
 add_at(summary_label, Rect2(47, 508, 300, 33))
 results = ItemList.new()
 results.fixed_icon_size = Vector2i(12, 12)
 results.add_theme_constant_override("v_separation", 13)
 results.add_theme_font_size_override("font_size", 18)
 results.item_selected.connect(pin_directory_item)
 add_at(results, Rect2(46, 549, 310, 275))

 var clear_button := make_button("ピンを外す")
 clear_button.pressed.connect(clear_pin)
 add_at(clear_button, Rect2(46, 842, 310, 47))
 details_label = make_label("", 17, ACCENT)
 details_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
 details_label.vertical_alignment = VERTICAL_ALIGNMENT_TOP
 add_at(details_label, Rect2(46, 908, 310, 107))

func make_label(value: String, size_px: int, ink: Color = INK) -> Label:
 var label := Label.new()
 label.text = value
 label.add_theme_font_size_override("font_size", size_px)
 label.add_theme_color_override("font_color", ink)
 label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
 label.mouse_filter = Control.MOUSE_FILTER_IGNORE
 return label

func make_button(value: String) -> Button:
 var button := Button.new()
 button.text = value
 return button

func add_at(control: Control, rect: Rect2) -> void:
 add_child(control)
 control.position = rect.position
 control.size = rect.size

func prepare_to_show() -> void:
 if not destination_index_ready:
  index_destinations()
  destination_index_ready = true
 follow_current_floor()
 results.deselect_all()

func search_has_focus() -> bool:
 return is_instance_valid(search) and search.has_focus()

func return_to_location() -> void:
 if not is_instance_valid(wing_select):
  return
 follow_current_floor()
 if is_instance_valid(search):
  search.release_focus()

func wing_title(id: String) -> String:
 return id + "館" if id in ["A", "B", "C"] else id

func floor_title(floor: Dictionary) -> String:
 return wing_title(str(floor.wing)) + "  " + str(floor.label)

func index_destinations() -> void:
 item_index.clear()
 for f: Dictionary in data:
  for item: Dictionary in f.get("items", []):
   if item.kind == "吹抜":
    continue
   var brand: Dictionary = brand_registry.get(item.id, {})
   var title := str(brand.get("name", item.get("name", item.kind)))
   var category := str(brand.get("category", item.kind))
   var key := str(item.id)
   var lookup := (title + " " + category + " " + key + " " + floor_title(f) + " " + str(item.kind)).to_lower()
   if item.kind == "トイレ":
    lookup += " wc お手洗い"
   if item.kind == "EV":
    lookup += " エレベーター"
   if item.kind == "エスカレーター":
    lookup += " es"
   item_index.append({"floor": f, "item": item, "title": title, "category": category, "lookup": lookup})

func refresh_directory() -> void:
 if not is_instance_valid(results):
  return
 results.clear()
 result_rows.clear()
 var category_filter: Array = FILTERS[maxi(filter_select.selected, 0)][1]
 var words := search.text.strip_edges().to_lower().replace("　", " ").split(" ", false)
 for record: Dictionary in item_index:
  var item: Dictionary = record.item
  var floor: Dictionary = record.floor
  if result_floor_only and (floor.wing != wing or floor.label != floor_label):
   continue
  if not category_filter.is_empty() and item.kind not in category_filter:
   continue
  var matches := true
  for word: String in words:
   if not String(record.lookup).contains(word):
    matches = false
    break
  if not matches:
   continue
  var location_suffix := "" if result_floor_only else "  " + floor_title(floor)
  var title := str(record.title)
  if item.kind != "店舗":
   title += "  " + str(item.id)
  var index := results.add_item(title + location_suffix + ("" if item.implemented else "  ×"))
  results.set_item_tooltip(index, "%s\n%s  %s\n%s" % [title, floor_title(floor), record.category, item.id])
  result_rows.append(record)
  if not pinned.is_empty() and pinned.floor.wing == floor.wing and pinned.floor.label == floor.label and pinned.item.id == item.id:
   results.select(index)
 var count_text := "%d件" % result_rows.size()
 if result_rows.is_empty():
  count_text = "該当する行き先がありません"
 summary_label.text = count_text

func pin_directory_item(index: int) -> void:
 if index < 0 or index >= result_rows.size():
  return
 pinned = result_rows[index]
 var floor: Dictionary = pinned.floor
 if floor.wing != wing or floor.label != floor_label:
  select_floor(floor)
  return
 update_pin_caption()
 queue_redraw()

func clear_pin() -> void:
 pinned = {}
 results.deselect_all()
 update_pin_caption()
 queue_redraw()

func update_pin_caption() -> void:
 if pinned.is_empty():
  details_label.text = "一覧や地図を選ぶとピンを表示"
  return
 var item: Dictionary = pinned.item
 var location_text := floor_title(pinned.floor)
 var label := str(pinned.title)
 if label.length() > 32:
  label = label.substr(0, 31) + "…"
 var extra := "" if item.implemented else " / 未公開"
 details_label.text = label + "\n" + location_text + "　" + str(item.id) + extra

func select_floor(floor: Dictionary) -> void:
 wing = str(floor.wing)
 floor_label = str(floor.label)
 for i in wing_select.item_count:
  if wing_select.get_item_metadata(i) == wing:
   wing_select.select(i)
   break
 refresh_floors()

func refresh_floors() -> void:
 floor_select.clear()
 var active := -1
 for f: Dictionary in data:
  if f.wing != wing:
   continue
  floor_select.add_item(str(f.label))
  if f.label == floor_label:
   active = floor_select.item_count - 1
 if floor_select.item_count > 0:
  floor_select.select(maxi(active, 0))
  floor_label = floor_select.get_item_text(floor_select.selected)
 choose()

func choose() -> void:
 selected = {}
 for f: Dictionary in data:
  if f.wing == wing and f.label == floor_label:
   selected = f
   break
 if selected.is_empty():
  queue_redraw()
  return
 var bb: Array = selected.bounds
 var w := float(bb[2]) - float(bb[0])
 var h := float(bb[3]) - float(bb[1])
 scale_m = minf(map_rect.size.x / (w + 24.0), map_rect.size.y / (h + 24.0))
 offset = map_rect.get_center() - Vector2((bb[0] + bb[2]) / 2.0, (bb[1] + bb[3]) / 2.0) * scale_m
 bake_selected_floor()
 refresh_directory()
 update_pin_caption()
 queue_redraw()

func point(q: Array) -> Vector2:
 return Vector2(q[0], q[1]) * scale_m + offset

func ring_points(ring: Array) -> PackedVector2Array:
 var points := PackedVector2Array()
 for p: Array in ring:
  points.append(Vector2(p[0], p[1]))
 if points.size() > 3 and points[0].is_equal_approx(points[-1]):
  points.remove_at(points.size() - 1)
 return points

func covers(pos: Vector2, geometry: Array) -> bool:
 for polygon: Array in geometry:
  if polygon.is_empty() or not Geometry2D.is_point_in_polygon(pos, ring_points(polygon[0])):
   continue
  var in_hole := false
  for i in range(1, polygon.size()):
   if Geometry2D.is_point_in_polygon(pos, ring_points(polygon[i])):
    in_hole = true
    break
  if not in_hole:
   return true
 return false

func bake_polygons(geometry: Array, fill: Color, output: Array[Dictionary]) -> void:
 for polygon: Array in geometry:
  for i in polygon.size():
   var outline := ring_points(polygon[i])
   if outline.size() < 3:
    continue
   for j in outline.size():
    outline[j] = outline[j] * scale_m + offset
   var valid := not Geometry2D.triangulate_polygon(outline).is_empty()
   var fill_points := outline.duplicate()
   outline.append(outline[0])
   output.append({"outline": outline, "points": fill_points, "valid": valid, "color": fill if i == 0 else MAP_COLOR})

func bake_selected_floor() -> void:
 var cache_key := wing + ":" + floor_label
 if geometry_cache.has(cache_key):
  map_labels = geometry_cache[cache_key].labels
  return
 var shapes: Array[Dictionary] = []
 bake_polygons(selected.floor, Color("#364955"), shapes)
 bake_polygons(selected.public, Color("#52737f"), shapes)
 map_labels = []
 var visited := {}
 for item: Dictionary in selected.items:
  bake_polygons(item.geometry, COLORS.get(item.kind, Color("#64737c")), shapes)
  if item.kind in ["店舗", "駐車場", "吹抜"]:
   continue
  var key := str(item.id)
  var caption := str(item.kind)
  if item.kind == "トイレ":
   key = key.trim_suffix("-women").trim_suffix("-men") + "-WC"
   caption = "WC"
  elif item.kind == "エスカレーター":
   key = key.trim_suffix("-UP").trim_suffix("-DOWN")
   caption = "ES"
  if visited.has(key):
   continue
  visited[key] = true
  var map_point := point(item.point)
  var width := font.get_string_size(caption, HORIZONTAL_ALIGNMENT_LEFT, -1, 14).x + 12.0
  var tag := Rect2(map_point + Vector2(7, -16), Vector2(width, 20))
  tag.position.x = clampf(tag.position.x, map_rect.position.x + 5, map_rect.end.x - width - 5)
  for attempt in 14:
   var conflict := false
   for old: Dictionary in map_labels:
    if tag.grow(2).intersects(old.rect):
     conflict = true
     break
   if not conflict:
    break
   tag.position.y += 22
  if map_rect.encloses(tag):
   map_labels.append({"rect": tag, "point": map_point, "caption": caption, "available": item.implemented})
 # Keep only the most recently visited six floors in memory.
 if geometry_cache.size() >= 6:
  geometry_cache.erase(geometry_cache.keys()[0])
 geometry_cache[cache_key] = {"shapes": shapes, "labels": map_labels}

func _draw() -> void:
 draw_rect(Rect2(26, 143, 350, 892), PANEL_COLOR)
 draw_rect(Rect2(397, 143, 1489, 833), PANEL_COLOR)
 draw_rect(map_rect, MAP_COLOR)
 if selected.is_empty():
  return
 var cache_key := wing + ":" + floor_label
 for shape: Dictionary in geometry_cache[cache_key].shapes:
  if shape.valid:
   draw_colored_polygon(shape.points, shape.color)
  draw_polyline(shape.outline, Color("#78909a"), 1.0)
 for item: Dictionary in selected.items:
  if item.implemented:
   continue
  var unavailable_marker := point(item.point)
  draw_line(unavailable_marker - Vector2(4, 4), unavailable_marker + Vector2(4, 4), ACCENT, 2.0)
  draw_line(unavailable_marker + Vector2(-4, 4), unavailable_marker + Vector2(4, -4), ACCENT, 2.0)
 for tag: Dictionary in map_labels:
  draw_line(tag.point, tag.rect.get_center(), Color("#aac3cd"), 1.0)
  draw_rect(tag.rect, PANEL_COLOR)
  draw_string(font, tag.rect.position + Vector2(6, 15), tag.caption, HORIZONTAL_ALIGNMENT_LEFT, -1, 14, INK if tag.available else MUTED)
 if not pinned.is_empty() and pinned.floor.wing == wing and pinned.floor.label == floor_label:
  draw_marker_pin(point(pinned.item.point))
 if not current_floor.is_empty() and current_floor.wing == wing and current_floor.label == floor_label:
  draw_player_marker()
 draw_string(font, Vector2(407, 129), floor_title(selected), HORIZONTAL_ALIGNMENT_LEFT, -1, 29, INK)
 var legend := ["店舗", "広場", "EV", "階段", "トイレ", "駐車場"]
 var x := 410.0
 for kind: String in legend:
  draw_rect(Rect2(x, 999, 14, 14), COLORS[kind])
  draw_string(font, Vector2(x + 21, 1012), kind, HORIZONTAL_ALIGNMENT_LEFT, -1, 17, MUTED)
  x += float(font.get_string_size(kind, HORIZONTAL_ALIGNMENT_LEFT, -1, 17).x) + 50.0
 draw_string(font, Vector2(x + 6, 1012), "× 未公開", HORIZONTAL_ALIGNMENT_LEFT, -1, 17, ACCENT)
 var ruler := 50.0 * scale_m
 var ruler_x := map_rect.end.x - ruler - 8.0
 draw_line(Vector2(ruler_x, 1004), Vector2(ruler_x + ruler, 1004), MUTED, 2.0)
 draw_string(font, Vector2(ruler_x, 1027), "50 m", HORIZONTAL_ALIGNMENT_LEFT, -1, 15, MUTED)

func draw_player_marker() -> void:
 var marker := world_plan_point() * scale_m + offset
 if not map_rect.has_point(marker):
  return
 var heading := Vector2(-player.global_basis.z.x, -player.global_basis.z.z).normalized()
 var lateral := Vector2(-heading.y, heading.x)
 draw_circle(marker, 21.0, PANEL_COLOR)
 draw_colored_polygon(
  PackedVector2Array([marker + heading * 17.0, marker - heading * 8.0 + lateral * 10.0, marker - heading * 8.0 - lateral * 10.0]),
  Color("#ff7564")
 )

func draw_marker_pin(marker: Vector2) -> void:
 if not map_rect.has_point(marker):
  return
 draw_circle(marker, 18.0, Color("#10191d"))
 draw_circle(marker, 14.0, ACCENT, false, 4.0, true)
 draw_circle(marker, 4.0, ACCENT)

func world_plan_point() -> Vector2:
 return Vector2(player.global_position.x - 429.0, player.global_position.z + 46.0)

func floor_at(pos: Vector2, height: float) -> Dictionary:
 var best_score := INF
 var best: Dictionary = {}
 for f: Dictionary in data:
  var bb: Array = f.bounds
  var bounds := Rect2(bb[0], bb[1], bb[2] - bb[0], bb[3] - bb[1])
  var exact := bounds.has_point(pos) and covers(pos, f.floor)
  var nearest := pos.clamp(bounds.position, bounds.end)
  var score := absf(height - float(f.height))
  if not exact:
   score += 80.0 + nearest.distance_to(pos)
  elif not covers(pos, f.public):
   score += .12
  if score < best_score:
   best_score = score
   best = f
 return best

func follow_current_floor() -> void:
 if data.is_empty():
  return
 current_floor = floor_at(world_plan_point(), player.global_position.y)
 if current_floor.is_empty():
  return
 var label := "現在地　" + floor_title(current_floor)
 if absf(player.global_position.y - float(current_floor.height)) > .75:
  label += "   階間移動中"
 location_label.text = label
 select_floor(current_floor)

func _gui_input(event: InputEvent) -> void:
 if not (event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed):
  return
 if not map_rect.has_point(event.position) or selected.is_empty():
  return
 var world: Vector2 = (event.position - offset) / scale_m
 for record: Dictionary in item_index:
  if record.floor.wing != wing or record.floor.label != floor_label:
   continue
  if record.item.geometry.is_empty() or not covers(world, record.item.geometry):
   continue
  pinned = record
  search.release_focus()
  refresh_directory()
  update_pin_caption()
  queue_redraw()
  accept_event()
  return
