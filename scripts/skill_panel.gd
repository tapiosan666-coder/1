class_name SkillPanel
extends RefCounted
const BRANCHES := [
 {"name":"01 / 装備・スキャン銃","keys":["gun","focus","magazine","reload","range","pierce"]},
 {"name":"02 / 猫の探索","keys":["cat","cat_speed"]},
 {"name":"03 / 探索・移動","keys":["sonar","sprint","double_jump","travel"]},
 {"name":"04 / 特殊スキャン","keys":["pulse","chain"]}
]
static func copy(hud: Control,text: String,rect: Rect2,size: int,color: Color,name: String = "") -> Label:
	var label := Label.new(); label.text = text; label.position = rect.position; label.size = rect.size
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART; label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.add_theme_font_size_override("font_size",size); label.add_theme_color_override("font_color",color)
	if not name.is_empty(): label.name = name
	hud.buttons.add_child(label); return label
static func effect(run: IdentityRun,key: String,level: int) -> String:
	match key:
		"gun": return "銃を使用可能" if level > 0 else "初期スキャナーのみ"
		"focus": return "%d発で銃のスキャン完了" % (5-level)
		"magazine": return "弾倉 %d発" % (30+15*level)
		"reload": return "リロード %.2f秒" % pow(.8,level)
		"range": return "銃の射程 %dm" % (30+15*level)
		"pierce": return "1発で最大3人に命中" if level > 0 else "1発で1人に命中"
		"cat": return "猫1匹が自動探索" if level > 0 else "猫は未配備"
		"cat_speed": return "接近後 %d秒でスキャン" % [20,12,6][level]
		"sonar": return "探知半径 %dm" % [0,15,30,50,80,120][level]
		"sprint": return "ダッシュ速度 %d%%" % (100+25*level)
		"double_jump": return "空中で追加ジャンプ1回" if level > 0 else "地上ジャンプのみ"
		"travel": return "訪問済み地点へ移動可能" if level > 0 else "ファストトラベル未解放"
		"pulse": return "半径 %dmを解析" % [0,8,12,16][level]
		"chain": return "最大8人へ連鎖 / Eキー" if level > 0 else "連鎖スキャン未解放"
	return ""
static func build(hud: Control) -> void:
	var run: IdentityRun = hud.run
	for index in BRANCHES.size():
		var branch: Dictionary = BRANCHES[index]
		var owned := 0
		for key in branch.keys: if run.upgrades[key] > 0: owned += 1
		var button: Button = hud._button("%s\n取得 %d / %d" % [branch.name,owned,branch.keys.size()],Rect2(70+index*330,190,312,62),func():
			hud.skill_branch = index; hud.skill_selected = BRANCHES[index].keys[0]; hud.show_mode("skills"),index == hud.skill_branch)
		button.name = "SkillBranch_%d" % index; button.add_theme_font_size_override("font_size",17)
	var keys: Array = BRANCHES[hud.skill_branch].keys
	if not hud.skill_selected in keys: hud.skill_selected = keys[0]
	for index in keys.size():
		var key: String = keys[index]; var skill: Dictionary = IdentityRun.SKILLS[key]
		var level: int = run.upgrades[key]; var reason := run.purchase_reason(key)
		var selected: bool = key == hud.skill_selected
		var rect := Rect2(70+(index%2)*402,278+(index/2)*150,386,134)
		var button: Button = hud._button("",rect,func(): hud.skill_selected = key; hud.show_mode("skills"))
		button.name = "SkillCard_"+key
		var style: StyleBoxFlat = button.get_theme_stylebox("normal").duplicate()
		style.border_color = hud.lime if selected else Color("4e686b"); style.set_border_width_all(2 if selected else 1)
		button.add_theme_stylebox_override("normal",style)
		copy(hud,skill.name,Rect2(rect.position+Vector2(16,12),Vector2(355,32)),21,hud.ink)
		copy(hud,"レベル %d / %d" % [level,skill.max],Rect2(rect.position+Vector2(16,48),Vector2(180,24)),15,hud.lime if level > 0 else hud.muted)
		var state := "最大レベル" if level >= skill.max else "前提スキルが必要" if not IdentityRun.prerequisite(key).is_empty() and run.upgrades[IdentityRun.prerequisite(key)] == 0 else "AP不足" if not reason.is_empty() else "購入できます"
		copy(hud,state,Rect2(rect.position+Vector2(16,80),Vector2(240,35)),16,hud.lime if reason.is_empty() else hud.muted)
		if level < skill.max: copy(hud,"%d AP" % run.price(key),Rect2(rect.position+Vector2(250,48),Vector2(120,30)),19,hud.orange)
	var key: String = hud.skill_selected; var skill: Dictionary = IdentityRun.SKILLS[key]
	var level: int = run.upgrades[key]; var maximum: bool = level >= skill.max
	copy(hud,skill.name,Rect2(920,278,445,65),28,hud.lime,"SkillDetailTitle")
	copy(hud,skill.detail,Rect2(920,350,430,65),18,hud.ink)
	copy(hud,"現在："+effect(run,key,level),Rect2(920,430,430,45),18,hud.muted)
	copy(hud,"次へ："+effect(run,key,mini(level+1,skill.max)) if not maximum else "すべての段階を取得しました",Rect2(920,480,430,48),18,hud.ink)
	copy(hud,"レベル %d / %d" % [level,skill.max],Rect2(920,540,430,30),17,hud.lime)
	var reason := run.purchase_reason(key)
	copy(hud,reason if not reason.is_empty() else "購入後、今回の探索中は継続して使えます",Rect2(920,580,430,50),17,hud.orange if not reason.is_empty() else hud.muted,"SkillPurchaseReason")
	var purchase: Button = hud._button("最大レベル" if maximum else "%s / %d AP" % ["購入する" if level == 0 else "強化する",run.price(key)],Rect2(920,650,430,60),func(): hud.skill_pressed.emit(key),reason.is_empty())
	purchase.name = "SkillPurchase"; purchase.disabled = not reason.is_empty()
	hud._button("探索に戻る / Tab",Rect2(70,788,386,56),func(): hud.resume_pressed.emit(),true)
	copy(hud,"系統とスキルを選び、右側で購入します。",Rect2(490,790,840,44),18,hud.muted)
