extends CanvasLayer
var game
var map:Control
var settings_panel:PanelContainer
var lift_panel:PanelContainer
var lift_buttons:VBoxContainer
var settings
var resolution:OptionButton
var caps:OptionButton
var vsync:CheckButton
var overlay:String=""
var lift_index:int=-1
func setup(g)->void:
 game=g;settings=load("res://settings_v7.gd").new();settings.restore()
 var theme=Theme.new();theme.default_font=g.font;theme.default_font_size=22
 var root=Control.new();root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);root.mouse_filter=Control.MOUSE_FILTER_IGNORE;root.theme=theme;add_child(root)
 map=load("res://map_v7.gd").new();root.add_child(map);map.setup(g.read_json("res://source/v22/map-data-integrated.json"if g.a_continuous_v22 else"res://source/v22/map-data-combined.json"if g.c_open_proposal and g.es_site_proposal else"res://source/v15/map-data-C-option.json"if g.c_open_proposal else"res://source/v15/map-data-ES-option.json"if g.es_site_proposal else"res://source/v13/map-data.json"),g.player,g.font);map.visible=false
 settings_panel=PanelContainer.new();settings_panel.position=Vector2(555,235);settings_panel.size=Vector2(810,600);root.add_child(settings_panel);var style=StyleBoxFlat.new();style.bg_color=Color(.045,.065,.08,.98);style.content_margin_left=24;style.content_margin_right=24;style.content_margin_top=24;style.content_margin_bottom=24;style.corner_radius_top_left=12;style.corner_radius_top_right=12;style.corner_radius_bottom_left=12;style.corner_radius_bottom_right=12;settings_panel.add_theme_stylebox_override("panel",style)
 var v=VBoxContainer.new();v.add_theme_constant_override("separation",18);settings_panel.add_child(v)
 var title=Label.new();title.text="画面設定 / F10で閉じる";v.add_child(title)
 resolution=OptionButton.new()
 for text in ["1920 × 1080","2560 × 1440","3840 × 2160"]:resolution.add_item(text)
 resolution.select(settings.resolution_index);v.add_child(resolution)
 caps=OptionButton.new()
 for text in ["30 FPS","60 FPS","120 FPS","144 FPS","無制限"]:caps.add_item(text)
 caps.select(settings.LIMITS.find(settings.fps_limit));v.add_child(caps)
 vsync=CheckButton.new();vsync.text="VSync";vsync.button_pressed=settings.vsync;v.add_child(vsync)
 var apply=Button.new();apply.text="適用して保存";apply.pressed.connect(func():settings.resolution_index=resolution.selected;settings.fps_limit=settings.LIMITS[caps.selected];settings.vsync=vsync.button_pressed;settings.apply();close());v.add_child(apply)
 var note=Label.new();note.text="設定は独立検証版に保存します。\nVSync ON時は、画面の更新速度が実際の上限にもなります。\n物理更新は60 Hz、描画FPSとは分離しています。";note.add_theme_font_size_override("font_size",18);v.add_child(note);settings_panel.visible=false
 lift_panel=PanelContainer.new();lift_panel.position=Vector2(710,180);lift_panel.size=Vector2(500,650);root.add_child(lift_panel);lift_buttons=VBoxContainer.new();lift_buttons.add_theme_constant_override("separation",12);lift_panel.add_child(lift_buttons);lift_panel.visible=false
func pause_player(value:bool)->void:
 if game.hud!=null:game.hud.visible=not value
 game.player.input_enabled=not value;game.player.velocity=Vector3.ZERO;game.player.set_physics_process(not value);game.elevators.set_physics_process(not value);game.animator.paused=value
 Input.mouse_mode=Input.MOUSE_MODE_VISIBLE if value else Input.MOUSE_MODE_CAPTURED
func close()->void:
 overlay="";map.visible=false;settings_panel.visible=false;lift_panel.visible=false;pause_player(false)
func show_map()->void:
 if overlay=="map":close();return
 close();overlay="map";map.follow_current_floor();map.visible=true;pause_player(true)
func show_settings()->void:
 if overlay=="settings":close();return
 close();overlay="settings";settings_panel.visible=true;pause_player(true)
func show_lift(index:int)->void:
 close();lift_index=index;overlay="lift";pause_player(true)
 for child in lift_buttons.get_children():child.queue_free()
 var r:Dictionary=game.elevators.records[index];var title=Label.new();title.text=r.data.id+" / 行先を選択";lift_buttons.add_child(title)
 for stop in range(r.data.stops.size()):
  var b=Button.new();b.text=r.data.stops[stop].label;b.pressed.connect(func():close();game.elevators.request(index,stop));lift_buttons.add_child(b)
 var cancel=Button.new();cancel.text="閉じる";cancel.pressed.connect(close);lift_buttons.add_child(cancel);lift_panel.visible=true
func show_pilots()->void:
 if overlay=="pilots":close();return
 close();overlay="pilots";pause_player(true)
 for child in lift_buttons.get_children():child.queue_free()
 var title=Label.new();title.text="代表店舗を確認 / F8で閉じる";lift_buttons.add_child(title)
 var names={"apparel":"アパレル","homeware":"生活雑貨","beauty":"美容・化粧品","book":"書店","electronics":"家電","cafe":"カフェ"}
 for shot:Dictionary in game.read_json("res://source/v12/cameras.json"):
  if not String(shot.id).begins_with("shop-"):continue
  var parts=String(shot.id).split("-");var b=Button.new();b.text=String(names.get(parts[1],parts[1]))+" / "+String(shot.id).trim_prefix("shop-"+parts[1]+"-")
  b.pressed.connect(func():
   game.player.position=game.v3(shot.eye)-Vector3(0,1.57,0);game.player.velocity=Vector3.ZERO;game.player.rotation=Vector3.ZERO;game.player.camera.position=Vector3(0,1.65,0);game.player.camera.look_at(game.v3(shot.look));game.player.reset_physics_interpolation();close())
  lift_buttons.add_child(b)
 var cancel=Button.new();cancel.text="閉じる";cancel.pressed.connect(close);lift_buttons.add_child(cancel);lift_panel.visible=true
func show_amenities()->void:
 if overlay=="amenities":close();return
 close();overlay="amenities";pause_player(true)
 for child in lift_buttons.get_children():child.queue_free()
 var title=Label.new();title.text="v25 代表5店舗の内装検証・既存館内誘導 / F9で閉じる";lift_buttons.add_child(title)
 var scroll=ScrollContainer.new();scroll.custom_minimum_size=Vector2(490,335);scroll.horizontal_scroll_mode=ScrollContainer.SCROLL_MODE_DISABLED;lift_buttons.add_child(scroll)
 var choices=VBoxContainer.new();choices.size_flags_horizontal=Control.SIZE_EXPAND_FILL;scroll.add_child(choices)
 for shot:Dictionary in game.read_json("res://source/v25/review-cameras.json")+game.read_json("res://source/v24/review-cameras.json")+game.read_json("res://source/v22/review-cameras.json")+game.read_json("res://source/v19/menu-cameras.json"):
  var variant:String="combined"if game.c_open_proposal and game.es_site_proposal else"C"if game.c_open_proposal else"ES"if game.es_site_proposal else"normal"
  if not variant in shot.get("variants",["normal","C","ES"]):continue
  var b=Button.new();b.text=String(shot.id)+" / "+String(shot.title)
  b.pressed.connect(func():game.interactive_pose(shot);game.player.velocity=Vector3.ZERO;game.player.reset_physics_interpolation();close());choices.add_child(b)
 var water=Button.new();water.text="水景ランドマーク｜独立設計シーン・屋上未施工";water.pressed.connect(func():game.get_tree().change_scene_to_file("res://Water_landmark_v22.tscn"));choices.add_child(water)
 var label=Label.new();label.text="全館トイレ（60か所）の入口を確認";label.add_theme_font_size_override("font_size",18);lift_buttons.add_child(label)
 var selection=OptionButton.new();var locations:Array=game.read_json("res://source/v13/toilet-locations.json")
 for d:Dictionary in locations:selection.add_item(String(d.id))
 lift_buttons.add_child(selection)
 var go=Button.new();go.text="選択したトイレへ移動";go.pressed.connect(func():game.interactive_pose(locations[selection.selected]);game.player.velocity=Vector3.ZERO;game.player.reset_physics_interpolation();close());lift_buttons.add_child(go)
 var cancel=Button.new();cancel.text="閉じる";cancel.pressed.connect(close);lift_buttons.add_child(cancel);lift_panel.visible=true
