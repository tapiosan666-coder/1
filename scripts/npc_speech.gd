class_name NpcSpeech
extends Node3D
## One reusable, world-occluded bubble. Text never depends on identity truth.
const LINES := {
 "resting":["少し待ってから戻ろう。","案内を確認しておこう。"],
 "staff":["いらっしゃいませ。","お探しの商品はございますか？","どうぞ、ゆっくりご覧ください。"],
 "browsing":["これも良さそうだな。","もう少し見てから決めよう。","どちらの色にしようかな。"],
 "reading":["続きが気になる……。","この本、買って帰ろうかな。"],
 "seated":["少し休んでから行こう。","ここの席、落ち着くね。","次は何を見に行こうかな。"],
 "conversation":["このあと、どこに行こうか。","さっきのお店も良かったね。","帰りに食品も買っていこう。"],
 "restroom":["手を洗ってから戻ろう。","鏡、少し曇ってるな。"],
 "walking":["次のお店はあっちかな。","案内図を確認しよう。","今日はゆっくり見て回ろう。"]
}
var current_id := -1
var panel: Node3D
var label: Label3D

func _ready() -> void:
	panel = Node3D.new(); add_child(panel); panel.visible = false
	var ink := Shapes.material(Color("293a3b")); ink.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	var paper := Shapes.material(Color("f3f0e7")); paper.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	for spec in [[Vector2(2.55,.53),ink,0.0],[Vector2(2.51,.49),paper,.003]]:
		var face := MeshInstance3D.new(); var quad := QuadMesh.new(); quad.size = spec[0]
		face.mesh = quad; face.material_override = spec[1]; panel.add_child(face); face.position.z = spec[2]
	var triangle := SurfaceTool.new(); triangle.begin(Mesh.PRIMITIVE_TRIANGLES)
	for vertex in [Vector3(-.23,-.25,.005),Vector3(-.04,-.25,.005),Vector3(-.24,-.40,.005)]: triangle.add_vertex(vertex)
	var tail := MeshInstance3D.new(); tail.mesh = triangle.commit(); tail.material_override = paper
	paper.cull_mode = BaseMaterial3D.CULL_DISABLED; panel.add_child(tail)
	label = Shapes.sign_text(panel,Vector3(0,0,.012),"",44,Color("293a3b"))
	label.pixel_size = .0032; label.outline_size = 0; label.shaded = false

func dismiss() -> void:
	current_id = -1
	if is_instance_valid(panel): panel.visible = false

func update_nearby(crowd: Crowd,camera: Camera3D,enabled: bool) -> int:
	if not enabled: dismiss(); return -1
	var best := -1
	var distance := 3.2*3.2
	for id in crowd.run.population:
		if crowd.run.eliminated[id]: continue
		var at := crowd.positions[id]
		if absf(at.y-(camera.global_position.y-1.68)) > 1.3: continue
		var head := at+Vector3.UP*(1.2 if crowd.roles[id] in ["seated","reading"] else 1.7)
		var difference := head-camera.global_position
		var d := difference.length_squared()
		var threshold := 3.6*3.6 if id == current_id else distance
		if d > threshold or -camera.global_basis.z.dot(difference.normalized()) < .1: continue
		var query := PhysicsRayQueryParameters3D.create(camera.global_position,head,1)
		if not get_world_3d().direct_space_state.intersect_ray(query).is_empty(): continue
		# Prefer the existing speaker until another is noticeably closer.
		var score := d*.75 if id == current_id else d
		if best < 0 or score < distance: best = id; distance = score
	if best < 0: dismiss(); return -1
	current_id = best
	var lines: Array = LINES.get(crowd.roles[best],LINES.walking)
	label.text = lines[best % lines.size()]
	if crowd.activities[best] == "book" and crowd.roles[best] == "browsing": label.text = "この本、面白そうだな。"
	if crowd.activities[best] == "garden": label.text = "風が気持ちいいね。" if crowd.roles[best] != "seated" else "ここで少し休もう。"
	if crowd.activities[best] == "parking": label.text = "車はこの辺りだったかな。"
	if crowd.activities[best] == "cinema": label.text = "この席からよく見えるね。"
	if crowd.activities[best] == "cinema_staff": label.text = "上映室は中央の通路からです。"
	if crowd.activities[best] == "food_wait": label.text = "ここで待ち合わせをしているんです。"
	if crowd.activities[best] == "terrace": label.text = "外のベンチも気持ちいいね。"
	if crowd.activities[best] == "outlet_cafe": label.text = "歩いたあとのお茶はおいしいね。"
	if crowd.activities[best] == "outlet_staff": label.text = "どうぞ、ゆっくりご覧ください。"
	if crowd.activities[best] == "deli": label.text = "お惣菜はいかがですか？"
	panel.global_position = crowd.positions[best]+Vector3.UP*(1.88 if crowd.roles[best] in ["seated","reading"] else 2.3)
	panel.global_basis = camera.global_basis
	panel.visible = true
	return best
