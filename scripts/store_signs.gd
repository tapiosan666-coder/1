class_name StoreSigns
extends Node3D
## Brand lightboxes share one atlas and are batched by nearby floor/sector.
## A cosmetic overlay: no collision, navigation, identity or cached-world edits.
var boards := 0
var hidden_labels: Array[Label3D] = []
var batches: Array[MeshInstance3D] = []
var _groups: Dictionary = {}

static func specifications() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for side in [-1,1]:
		for index in Mall.SHOP_CENTERS.size():
			var x: float=Mall.SHOP_CENTERS[index]
			if Mall.has_shop(x,side):
				result.append({"id":"a_0_%d_%d"%[index,side],"text":StoreSignCatalog.DATA.ground_names[index],"at":Vector3(x,4.25,side*8.31),"yaw":PI if side>0 else 0.0,"width":9.2})
	for level in [1,2]:
		for spec in TenantCatalog.all_for_floor(level):
			result.append({"id":"a_%d_%d_%d"%[level,spec.index,spec.side],"text":spec.name,"at":TenantCatalog.transform(spec)*Vector3(0,4.22,-8.30),"yaw":PI if spec.side>0 else 0.0,"width":9.2})
	for level in [0,1,2]:
		for store in BWing.STORES:
			result.append({"id":"b_%d_%d_%d"%[level,int(store.x),store.side],"text":store.name,"at":Vector3(store.x,Mall.floor_height(level)+4.15,store.side*8.34),"yaw":PI if store.side>0 else 0.0,"width":minf(10.4,store.w*.45)})
	for i in CWing.SHOPS.size():
		var store: Dictionary=CWing.SHOPS[i]
		result.append({"id":"c_0_%d"%i,"text":store.name,"at":store.at+Basis(Vector3.UP,store.yaw)*Vector3(0,3.8,.17),"yaw":store.yaw,"width":9.2})
	for source: Dictionary in StoreSignCatalog.DATA.additional_boards:
		var spec := source.duplicate()
		spec.at=Vector3(source.at[0],source.at[1],source.at[2])
		spec.yaw=deg_to_rad(source.yaw)
		result.append(spec)
	return result

func setup(mall: Node3D) -> void:
	var labels := mall.find_children("*","Label3D",true,false)
	var atlas: Texture2D=preload("res://assets/retail/store_signs.png")
	var material := ShaderMaterial.new(); material.shader=preload("res://assets/store_signs.gdshader");material.set_shader_parameter("sign_atlas",atlas)
	for spec in specifications():
		if spec.get("replace_label",true):
			var anchor := MallCurve.world(spec.at)
			var found := false
			for label: Label3D in labels:
				if label.text==spec.text and label.global_position.distance_squared_to(anchor)<.001:
					label.visible=false;hidden_labels.append(label);found=true;break
			if not found: push_error("Facade sign label not found: "+spec.id)
		_add_board(spec)
	for key: Vector3i in _groups:
		var record: Dictionary=_groups[key]
		var builder: SurfaceTool=record.builder
		builder.index()
		var node := MeshInstance3D.new();add_child(node)
		node.mesh=builder.commit();node.material_override=material;node.position=record.origin
		node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		node.visibility_range_end=75;node.visibility_range_end_margin=5
		batches.append(node)
	_groups.clear()

func _add_board(spec: Dictionary) -> void:
	var yaw := Basis(Vector3.UP,spec.yaw)
	var at: Vector3=spec.at+yaw*Vector3(0,0,.15)
	var world := MallCurve.world(at)
	var cell := Vector3i(floori(world.x/28),floori(world.y/5.35),floori(world.z/24))
	if not _groups.has(cell):
		var builder := SurfaceTool.new();builder.begin(Mesh.PRIMITIVE_TRIANGLES)
		_groups[cell]={"builder":builder,"origin":Vector3((cell.x+.5)*28,(cell.y+.5)*5.35,(cell.z+.5)*24)}
	var builder: SurfaceTool=_groups[cell].builder
	var tile: int=StoreSignCatalog.DATA.aliases[spec.text]
	var columns: int=StoreSignCatalog.DATA.columns
	var rows: int=StoreSignCatalog.DATA.rows
	var u0: float=(float(tile%columns)+2.0/1024)/columns
	var u1: float=(float(tile%columns+1)-2.0/1024)/columns
	var v0: float=(float(tile/columns)+2.0/128)/rows
	var v1: float=(float(tile/columns+1)-2.0/128)/rows
	var width: float=spec.width;var height: float=width/8.0
	var segments := 8 if at.x+width*.5>MallCurve.START else 1
	for step in segments:
		var left := -width*.5+width*float(step)/segments
		var right := -width*.5+width*float(step+1)/segments
		var a := Vector3(left,-height*.5,0);var b := Vector3(right,-height*.5,0)
		var c := Vector3(right,height*.5,0);var d := Vector3(left,height*.5,0)
		for local in [a,c,b,a,d,c]:
			var plan: Vector3=at+yaw*local
			builder.set_normal((MallCurve.jacobian(plan).inverse().transposed()*yaw.z).normalized())
			builder.set_uv(Vector2(lerpf(u0,u1,local.x/width+.5),lerpf(v1,v0,local.y/height+.5)))
			builder.add_vertex(MallCurve.world(plan)-_groups[cell].origin)
	boards+=1
