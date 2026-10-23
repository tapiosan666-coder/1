class_name CacheField
extends Node3D
var state: RunLoot
var lids: Array[Node3D] = []
var labels: Array[Label3D] = []

func setup(loot: RunLoot) -> void:
	state = loot
	for chest in loot.chests:
		var root := Node3D.new(); add_child(root); root.position = chest.pos
		var color := Color("a88f65") if chest.rarity == "通常" else Color("8577b5") if chest.rarity == "レア" else Color("d5b36a")
		var body := Shapes.material(Color("283f45"))
		var trim := Shapes.material(color,.25)
		Shapes.box(root,Vector3(0,.23,0),Vector3(.72,.42,.50),body)
		for x in [-.28,.28]: Shapes.box(root,Vector3(x,.24,0),Vector3(.045,.45,.53),trim)
		Shapes.box(root,Vector3(0,.32,-.262),Vector3(.10,.13,.035),trim)
		var lid := Node3D.new(); root.add_child(lid); lid.position = Vector3(0,.46,.25)
		Shapes.box(lid,Vector3(0,0,-.25),Vector3(.76,.10,.54),trim)
		lids.append(lid)
		var label := Shapes.sign_text(root,Vector3(0,.94,0),chest.rarity+"宝箱",24,color)
		label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		label.pixel_size = .005
		labels.append(label)

func nearest(camera: Camera3D) -> int:
	var closest := -1
	var distance := 2.2
	for index in state.chests.size():
		var chest: Dictionary = state.chests[index]
		if chest.opened: continue
		var point: Vector3 = chest.pos+Vector3.UP*.45
		var d := camera.global_position.distance_to(point)
		if d > distance: continue
		var query := PhysicsRayQueryParameters3D.create(camera.global_position,point,1)
		if get_world_3d().direct_space_state.intersect_ray(query).is_empty():
			closest = index; distance = d
	return closest

func opened(index: int) -> void:
	lids[index].rotation.x = 1.2
	labels[index].text = "開封済み"
	labels[index].modulate = Color("829392")
