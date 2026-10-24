class_name CivilianBody
extends RefCounted
## One shared mesh and one pose texture; no Skeleton3D/animation tree per person.
var instances:MultiMesh
var pose_texture:ImageTexture
var pose_bytes:PackedByteArray
var pose_width:=CivilianRig.BONE_COUNT*6
var capacity:int
var mesh:Mesh
var face:CivilianFace
func _init(parent:Node3D,population:int,skin:Color,width:float)->void:
	capacity=maxi(1,population)
	pose_bytes.resize(pose_width*capacity*16)
	var identity_pose:Array[Transform3D]=[];identity_pose.resize(CivilianRig.BONE_COUNT)
	for bone in CivilianRig.BONE_COUNT:identity_pose[bone]=Transform3D.IDENTITY
	for row in capacity:write_pose(row,identity_pose)
	pose_texture=ImageTexture.create_from_image(Image.create_from_data(pose_width,capacity,false,Image.FORMAT_RGBAF,pose_bytes))
	mesh=load("res://assets/characters/civilian_body.res").duplicate()
	for s in mesh.get_surface_count():
		var mat:=ShaderMaterial.new();mat.shader=preload("res://assets/civilian_body.gdshader")
		var channel:int=["overshirt","trousers","neck","details","shoes","sole","tee"].find(mesh.surface_get_material(s).resource_name)
		mat.set_shader_parameter("joint_palette",pose_texture);mat.set_shader_parameter("surface_kind",channel)
		mat.set_shader_parameter("skin_tint",skin);mat.set_shader_parameter("face_width",width)
		mat.set_shader_parameter("fabric_detail",preload("res://assets/characters/textures/fabric_detail.png"));mat.set_shader_parameter("fabric_normal",preload("res://assets/characters/textures/fabric_normal.png"))
		var outline:=ShaderMaterial.new();outline.shader=preload("res://assets/civilian_body_outline.gdshader");outline.set_shader_parameter("joint_palette",pose_texture);outline.set_shader_parameter("face_width",width);if channel!=2:mat.next_pass=outline
		mesh.surface_set_material(s,mat)
	instances=MultiMesh.new();instances.transform_format=MultiMesh.TRANSFORM_3D;instances.use_custom_data=true;instances.use_colors=true;instances.mesh=mesh;instances.instance_count=population
	var node:=MultiMeshInstance3D.new();node.name="ContinuousCivilianBody";node.multimesh=instances;parent.add_child(node)
	face=CivilianFace.new(population)
	var attachments:Variant=parent.get("parts")
	if attachments is Array:face.install(attachments)
func write_pose(row:int,transforms:Array)->void:
	for bone in transforms.size():
		var t:Transform3D=transforms[bone]
		for axis in 3:
			var offset:=((row*pose_width)+(bone*6)+axis)*16
			pose_bytes.encode_float(offset,t.basis.x[axis]);pose_bytes.encode_float(offset+4,t.basis.y[axis]);pose_bytes.encode_float(offset+8,t.basis.z[axis]);pose_bytes.encode_float(offset+12,t.origin[axis])
		var normal:=t.basis.inverse().transposed()
		for axis in 3:
			var offset:=((row*pose_width)+(bone*6)+3+axis)*16
			pose_bytes.encode_float(offset,normal.x[axis]);pose_bytes.encode_float(offset+4,normal.y[axis]);pose_bytes.encode_float(offset+8,normal.z[axis]);pose_bytes.encode_float(offset+12,0)
func render(crowd:Node3D,ids:Array[int],motions:Dictionary,bounds:AABB)->void:
	face.update(ids,motions)
	instances.visible_instance_count=ids.size();instances.custom_aabb=bounds
	for slot in ids.size():
		var id:=ids[slot];var role:String="walking" if crowd.attracted.has(id) else crowd.roles[id]
		var moving:bool=role=="walking" and ((crowd.waits[id]<=0 and not crowd.paths[id].is_empty()) or crowd.attracted.has(id)) and crowd.death_times[id]<0
		write_pose(slot,CivilianRig.matrices(role,motions[id],crowd.clock,id,moving))
		var at:Vector3=crowd.positions[id]
		if crowd.death_times[id]>=0:at.y-=pow(crowd.death_times[id]/.8,2)*4
		instances.set_instance_color(slot,Color.WHITE)
		instances.set_instance_transform(slot,Transform3D(Basis(Vector3.UP,crowd.headings[id]),at))
		var color:Color=crowd.clothing_palette[id%crowd.clothing_palette.size()]
		instances.set_instance_custom_data(slot,Color(color.r,color.g,color.b,float(slot)))
	pose_texture.update(Image.create_from_data(pose_width,capacity,false,Image.FORMAT_RGBAF,pose_bytes))
static func apron_mesh()->ArrayMesh:
	var b:=SurfaceTool.new();b.begin(Mesh.PRIMITIVE_TRIANGLES)
	for x in 10:
		for y in 6:
			var points:Array[Vector3]=[]
			for p in [Vector2(x/10.0,y/6.0),Vector2((x+1)/10.0,y/6.0),Vector2((x+1)/10.0,(y+1)/6.0),Vector2(x/10.0,(y+1)/6.0)]:
				var width:=lerpf(.15,.12,p.y);var px:float=(p.x-.5)*width*2
				points.append(Vector3(px,lerpf(.95,1.35,p.y),-.156+px*px*.8))
			for i in [0,2,1,0,3,2]:b.set_normal(Vector3.FORWARD);b.set_uv(Vector2.ZERO);b.add_vertex(points[i])
	for side in [-1,1]:
		var a:=Vector3(side*.085,1.35,-.15);var z:=Vector3(side*.06,1.47,-.075)
		var d:=Vector3(.013,0,0)
		for p in [a-d,z+d,a+d,a-d,z-d,z+d]:b.set_normal(Vector3.FORWARD);b.set_uv(Vector2.ZERO);b.add_vertex(p)
	var mat:=Shapes.material(Color("273c33"));mat.cull_mode=BaseMaterial3D.CULL_DISABLED;b.set_material(mat)
	return b.commit()
