class_name Bookshop
extends RefCounted
var parent: Node3D
var wood := Shapes.timber()
var dark := Shapes.material(Color("393d38"))
var paper := Shapes.material(Color("e3dac5"))
var spine_transforms: Array[Transform3D] = []
var cover_transforms: Array[Array] = [[],[],[],[],[],[]]

func build(root: Node3D) -> void:
	parent = root
	Shapes.box(root,Vector3(-75,.025,-16),Vector3(17.7,.04,15.3),wood)
	for x in [-79.5,-70.5]:
		Shapes.box(root,Vector3(x,.42,-13.5),Vector3(2,.8,2.8),wood)
		Shapes.box(root,Vector3(x,.87,-13.5),Vector3(2.1,.1,2.9),paper)
		for row in 3:
			for col in 3:
				var p := Vector3(x-.65+col*.65,.95,-14.35+row*.8)
				Shapes.box(root,p,Vector3(.29,.07,.41),paper)
				cover_transforms[(row*3+col)%6].append(Transform3D(Basis(Vector3.RIGHT,-PI/2),p+Vector3.UP*.039))
		var label := Shapes.sign_text(root,Vector3(x,1.25,-12.05),"新刊・話題の本" if x < -75 else "暮らし・デザイン",24,Color("454d45"))
		label.pixel_size = .005
	for x in [-81.0,-69.0]:
		_case(Vector3(x,0,-21.9),3.5)
	Shapes.sign_text(root,Vector3(-81,2.5,-23.32),"文学・エッセイ",28,Color("4a554b")).pixel_size = .004
	Shapes.sign_text(root,Vector3(-69,2.5,-23.32),"アート・建築",28,Color("4a554b")).pixel_size = .004
	Shapes.sign_text(root,Vector3(-72,1.65,-17.4),"お会計 / ご案内",23,Color("485348")).pixel_size = .0025
	for x in [-80.0,-75.0,-70.0]:
		Shapes.box(root,Vector3(x,3.3,-16),Vector3(.02,1.4,.02),dark)
		Shapes.cylinder(root,Vector3(x,2.6,-16),.28,.16,Shapes.material(Color("e7c995"),.8))
	var poster := QuadMesh.new(); poster.size = Vector2(1.1,1.55)
	var material := Shapes.material(Color.WHITE); material.albedo_texture = preload("res://assets/books/cover0.png")
	poster.material = material
	var node := MeshInstance3D.new(); node.mesh = poster; root.add_child(node); node.position = Vector3(-83.65,2.1,-17); node.rotation.y = PI/2
	# Shared spine mesh replaces hundreds of separate book draw calls.
	var mesh := BoxMesh.new(); mesh.size = Vector3(.10,.32,.22)
	var mat := Shapes.material(Color.WHITE); mat.vertex_color_use_as_albedo = true; mesh.material = mat
	var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.use_colors = true; mm.mesh = mesh; mm.instance_count = spine_transforms.size()
	for i in mm.instance_count:
		mm.set_instance_transform(i,spine_transforms[i]); mm.set_instance_color(i,Color.from_hsv(fmod(i*.117,1),.22,.55+.06*(i%4)))
	var books := MultiMeshInstance3D.new(); books.multimesh = mm; root.add_child(books)
	for variant in 6:
		var quad := QuadMesh.new(); quad.size = Vector2(.28,.40)
		var cover := Shapes.material(Color.WHITE); cover.albedo_texture = load("res://assets/books/cover%d.png" % variant); quad.material = cover
		var instances := MultiMesh.new(); instances.transform_format = MultiMesh.TRANSFORM_3D; instances.mesh = quad; instances.instance_count = cover_transforms[variant].size()
		for index in instances.instance_count: instances.set_instance_transform(index,cover_transforms[variant][index])
		var covers := MultiMeshInstance3D.new(); covers.multimesh = instances; root.add_child(covers)

func _case(p: Vector3,width: float) -> void:
	Shapes.box(parent,p+Vector3(0,1,-.4),Vector3(width,2,.08),wood)
	for side in [-1,1]: Shapes.box(parent,p+Vector3(side*(width/2-.04),1,0),Vector3(.08,2,.9),wood)
	for tier in 4:
		var y := .12+tier*.47
		Shapes.box(parent,p+Vector3(0,y,0),Vector3(width,.055,.9),wood)
		for index in 27:
			spine_transforms.append(Transform3D(Basis.IDENTITY,p+Vector3(-width/2+.16+index*.122,y+.19,.30)))
