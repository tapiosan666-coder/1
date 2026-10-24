class_name FloorContacts
extends RefCounted
## Offline approximation of static furniture/wall contact on A's three shop floors.
## One RGB mask stores floors 1/2/3. No physics or light work during cached play.
const AREA := Rect2(-91,-64,182,120)
const SIZE := 1024
static func bake(root: Node3D) -> void:
	var values := PackedFloat32Array(); values.resize(SIZE*SIZE*3); values.fill(1.0)
	var count := 0
	for shape_node in root.find_children("*","CollisionShape3D",true,false):
		if not shape_node.shape is BoxShape3D: continue
		var size: Vector3 = shape_node.shape.size
		var bounds: AABB = shape_node.global_transform*AABB(-size*.5,size)
		var center := bounds.get_center()
		if not AREA.has_point(Vector2(center.x,center.z)): continue
		if bounds.size.y < .18 or (bounds.size.x > 8 and bounds.size.z > 8): continue
		for level in [0,1,2]:
			var clearance := bounds.position.y-Mall.floor_height(level)
			if clearance < -.25 or clearance > .85: continue
			var rect := Rect2(bounds.position.x,bounds.position.z,bounds.size.x,bounds.size.z)
			var softness := .24+maxf(0,clearance)*.24
			var strength := .28/(1.0+maxf(0,clearance)*1.5)
			_stamp(values,rect,level,softness,strength); count += 1
	var bytes := PackedByteArray(); bytes.resize(values.size())
	for i in values.size(): bytes[i] = roundi(values[i]*255)
	var image := Image.create_from_data(SIZE,SIZE,false,Image.FORMAT_RGB8,bytes)
	var texture := ImageTexture.create_from_image(image)
	var shaders := ["res://assets/terrazzo.gdshader","res://assets/oak_floor.gdshader"]
	for node in root.find_children("*","MeshInstance3D",true,false):
		var material: Material = node.material_override
		if material is ShaderMaterial and material.shader.resource_path in shaders:
			material.set_shader_parameter("contact_map",texture)
			material.set_shader_parameter("has_contacts",true)
	root.set_meta("floor_contacts",{"static_footprints":count,"width":SIZE,"height":SIZE,"floors":3})

static func _stamp(values: PackedFloat32Array,rect: Rect2,level: int,softness: float,strength: float) -> void:
	var region := rect.grow(softness*3.0).intersection(AREA)
	if not region.has_area(): return
	var from_uv := (region.position-AREA.position)/AREA.size*SIZE
	var to_uv := (region.end-AREA.position)/AREA.size*SIZE
	for y in range(maxi(0,floori(from_uv.y)),mini(SIZE,ceili(to_uv.y))):
		var z := AREA.position.y+(y+.5)*AREA.size.y/SIZE
		var dz := maxf(0,maxf(rect.position.y-z,z-rect.end.y))
		for x in range(maxi(0,floori(from_uv.x)),mini(SIZE,ceili(to_uv.x))):
			var px := AREA.position.x+(x+.5)*AREA.size.x/SIZE
			var dx := maxf(0,maxf(rect.position.x-px,px-rect.end.x))
			var distance := sqrt(dx*dx+dz*dz)
			var shade := 1.0-strength*exp(-distance/softness)
			var index := (y*SIZE+x)*3+level
			values[index] = minf(values[index],shade)
