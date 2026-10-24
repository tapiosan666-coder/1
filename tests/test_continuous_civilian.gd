extends SceneTree
## Renderer/rig contract checks without Main, navigation or a world-cache rebuild.
class PoseFixture extends Node3D:
	var run:=IdentityRun.new(300,912)
	var positions:Array[Vector3]=[]
	var roles:Array[String]=[]
	var headings:Array[float]=[]
	var waits:Array[float]=[]
	var paths:Array[PackedVector3Array]=[]
	var death_times:Array[float]=[]
	var attracted:Dictionary={}
	var clothing_palette:Array=[Color("c58a6b"),Color("667e8a")]
	var clock:=0.0
	func _init()->void:
		for id in run.population:
			positions.append(Vector3(id*2,0,0));roles.append("walking" if id%2==0 else "seated")
			headings.append(0);waits.append(0);paths.append(PackedVector3Array([positions[id]+Vector3.FORWARD]));death_times.append(-1)
var checks:=0
var failures:=0
var foot_vertices:Array[Dictionary]=[]
func expect(ok:bool,message:String)->void:
	checks+=1
	if not ok:failures+=1;push_error(message)
func _initialize()->void:
	if DisplayServer.get_name()=="headless":
		printerr("Continuous character checks require a real renderer for instance colours and float pose textures.");quit(2);return
	call_deferred("verify")
func verify()->void:
	var source_mesh:Mesh=load("res://assets/characters/civilian_body.res")
	check_mesh(source_mesh)
	check_bind_endpoints()
	check_seated_context()
	check_gait_floor()
	await check_renderer()
	print("CONTINUOUS CIVILIAN RESULT: %d checks, %d failures"%[checks,failures]);quit(1 if failures else 0)
func check_mesh(mesh:Mesh)->void:
	var finite:=true;var weights_valid:=true;var normals_valid:=true;var foot_bones:Dictionary={}
	for surface in mesh.get_surface_count():
		var arrays:Array=mesh.surface_get_arrays(surface)
		var vertices:PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
		var normals:PackedVector3Array=arrays[Mesh.ARRAY_NORMAL]
		var packed:PackedVector2Array=arrays[Mesh.ARRAY_TEX_UV2]
		if vertices.size()!=normals.size() or vertices.size()!=packed.size():
			expect(false,"Every body vertex has a normal and two-weight skin data");return
		var footwear:bool=mesh.surface_get_material(surface).resource_name in ["shoes","sole"]
		for index in vertices.size():
			var data:Vector2=packed[index]
			finite=finite and vertices[index].is_finite() and normals[index].is_finite() and data.is_finite()
			var first:=floori(data.x);var other:=roundi(data.y);var amount:float=(data.x-first)*2
			weights_valid=weights_valid and first>=0 and first<CivilianRig.BONE_COUNT and other>=0 and other<CivilianRig.BONE_COUNT and amount>=-.0001 and amount<=1.0001
			normals_valid=normals_valid and normals[index].length_squared()>.25
			if footwear:
				foot_vertices.append({"point":vertices[index],"packed":data})
				if amount>.01:foot_bones[first]=true
				if amount<.99:foot_bones[other]=true
	expect(finite and weights_valid,"All mesh positions and skin weights are finite, normalized and address valid pose bones")
	expect(normals_valid,"Imported body normals never collapse to zero, including the neck")
	expect(foot_vertices.size()>100 and foot_bones.has(10) and foot_bones.has(11) and foot_bones.size()==2,"Both real shoes use the corrected foot bones rather than uncorrected shin motion")
func body_transform(motion:Dictionary,seated:bool)->Transform3D:
	var hip:=Vector3(0,CivilianRig.HIP_Y,0)
	return Transform3D(motion.body,hip-motion.body*hip+Vector3.UP*(motion.breath-(CivilianRig.SEAT_DROP if seated else 0)))
func check_bind_endpoints()->void:
	var endpoint_error:=0.0;var transforms_finite:=true
	for role in ["walking","reading","seated","staff","conversation","browsing","restroom"]:
		for tick in 121:
			var time:=tick/12.0;var moving:bool=role=="walking"
			var motion:=CivilianMotion.sample(role,role,time,2,moving)
			var transforms:=CivilianRig.matrices(role,motion,time,2,moving)
			var root_motion:=body_transform(motion,role in ["seated","reading"])
			for transform:Transform3D in transforms:
				transforms_finite=transforms_finite and transform.origin.is_finite() and transform.basis.x.is_finite() and transform.basis.y.is_finite() and transform.basis.z.is_finite() and absf(transform.basis.determinant())>.01
			for side_index in 2:
				var side:float=-1 if side_index==0 else 1
				var upper_bind:=CivilianRig.arm_bind(side,false);var lower_bind:=CivilianRig.arm_bind(side,true)
				var bind_shoulder:=Vector3(side*.215,CivilianRig.SHOULDER_Y,.008)
				var bind_elbow:=upper_bind.origin*2-bind_shoulder
				var bind_wrist:=lower_bind.origin*2-bind_elbow
				var arm:Dictionary=motion.left if side_index==0 else motion.right
				var expected_shoulder:Vector3=root_motion*(arm.arm.pos+arm.arm.basis.y*.15)
				var expected_elbow:Vector3=root_motion*(arm.arm.pos-arm.arm.basis.y*.15)
				var expected_wrist:Vector3=root_motion*arm.wrist
				endpoint_error=maxf(endpoint_error,(transforms[1+side_index*2]*bind_shoulder).distance_to(expected_shoulder))
				endpoint_error=maxf(endpoint_error,(transforms[1+side_index*2]*bind_elbow).distance_to(expected_elbow))
				endpoint_error=maxf(endpoint_error,(transforms[2+side_index*2]*bind_elbow).distance_to(expected_elbow))
				endpoint_error=maxf(endpoint_error,(transforms[2+side_index*2]*bind_wrist).distance_to(expected_wrist))
	expect(transforms_finite,"All body poses provide finite, invertible point/normal transforms")
	expect(endpoint_error<.001,"Inverse-bind endpoints meet the IK shoulder, elbow and wrist within 1 mm across role poses")
func check_seated_context()->void:
	var motion:=CivilianMotion.sample("seated","seated",0,0,false)
	var transforms:=CivilianRig.matrices("seated",motion,0,0,false)
	var seated_root:=body_transform(motion,true)
	var hip_height:float=(seated_root*Vector3(0,CivilianRig.HIP_Y,0)).y
	var valid_knees:=true
	for side_index in 2:
		var side:float=-1 if side_index==0 else 1
		var knee:Vector3=transforms[5+side_index*2]*Vector3(side*.105,CivilianRig.KNEE_Y,0)
		valid_knees=valid_knees and knee.z<-.30 and knee.y>.40 and knee.y<hip_height
	var lowest:=INF
	for vertex:Dictionary in foot_vertices:lowest=minf(lowest,CivilianRig.deform(vertex.point,vertex.packed,transforms).y)
	expect(hip_height>.56 and hip_height<.68 and valid_knees and lowest>=-.001,"Seated pelvis fits a .52 m seat, thighs bend forward and the actual shoes stay above the floor")
	var left_wrist:Vector3=seated_root*motion.left.wrist
	var right_wrist:Vector3=seated_root*motion.right.wrist
	expect(left_wrist.y>=.825 and right_wrist.y>=.825 and left_wrist.y<.96 and right_wrist.y<.96,"Resting dining wrists clear the .83 m tabletop rather than passing beneath it")
func check_gait_floor()->void:
	var lowest:=INF
	for tick in 181:
		var time:=float(tick)/180*TAU/5.5
		var motion:=CivilianMotion.sample("walking","walking",time,0,true)
		var transforms:=CivilianRig.matrices("walking",motion,time,0,true)
		for vertex:Dictionary in foot_vertices:lowest=minf(lowest,CivilianRig.deform(vertex.point,vertex.packed,transforms).y)
	expect(lowest>=-.001,"Every actual shoe/sole vertex clears the floor through a complete gait cycle")
func check_renderer()->void:
	var viewport:=SubViewport.new();viewport.size=Vector2i(96,96);viewport.own_world_3d=true;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	var fixture:=PoseFixture.new();viewport.add_child(fixture)
	var body:=CivilianBody.new(fixture,fixture.run.population,Color("cfaa89"),1)
	var initial_truth:=fixture.run.true_id;var initial_positions:=fixture.positions.duplicate()
	var initial_hits:PackedInt32Array=fixture.run.hits.duplicate();var initial_eliminated:PackedByteArray=fixture.run.eliminated.duplicate()
	var child_count:=fixture.get_child_count();var ids:Array[int]=[299,0,17]
	var motions:Dictionary={}
	for tick in 4:
		fixture.clock=tick*.37
		for id in ids:motions[id]=CivilianMotion.sample(fixture.roles[id],fixture.roles[id],fixture.clock,id,fixture.roles[id]=="walking")
		body.render(fixture,ids,motions,AABB(Vector3(-2,-2,-2),Vector3(605,5,5)))
	var white:=body.instances.use_colors
	for slot in ids.size():white=white and body.instances.get_instance_color(slot).is_equal_approx(Color.WHITE)
	expect(white,"Rendered body instances supply WHITE colour so mesh occlusion and the neck are not multiplied by zero")
	expect(fixture.positions==initial_positions and fixture.run.true_id==initial_truth and fixture.run.hits==initial_hits and fixture.run.eliminated==initial_eliminated and fixture.run.ap==0 and fixture.run.cleared==0 and not fixture.run.located and not fixture.run.won and fixture.get_child_count()==child_count and fixture.positions.size()==300,"Pose changes and reordered visible IDs never alter gameplay identities, progress, positions or population")
	# Exercise the final row and final bone through real GPU instance attributes
	# and the renderer's actual pose writer; a zero colour or clamped row fails.
	var pose:Array[Transform3D]=[];pose.resize(CivilianRig.BONE_COUNT)
	for bone in pose.size():pose[bone]=Transform3D.IDENTITY
	pose[CivilianRig.BONE_COUNT-1].origin.x=.63
	body.write_pose(299,pose)
	body.pose_texture.update(Image.create_from_data(body.pose_width,body.capacity,false,Image.FORMAT_RGBAF,body.pose_bytes))
	var shader:=Shader.new();shader.code="shader_type spatial;render_mode unshaded;uniform sampler2D palette:filter_nearest,repeat_disable;uniform int column;varying float row;void vertex(){row=INSTANCE_CUSTOM.a;}void fragment(){ALBEDO=COLOR.rgb*vec3(texelFetch(palette,ivec2(column,int(row+.5)),0).w,0.0,0.0);}"
	var material:=ShaderMaterial.new();material.shader=shader;material.set_shader_parameter("palette",body.pose_texture);material.set_shader_parameter("column",(CivilianRig.BONE_COUNT-1)*6)
	var quad:=QuadMesh.new();quad.material=material
	body.instances.mesh=quad;body.instances.visible_instance_count=1;body.instances.set_instance_transform(0,Transform3D.IDENTITY);body.instances.set_instance_custom_data(0,Color(.2,.3,.4,299));body.instances.custom_aabb=AABB(Vector3(-1,-1,-1),Vector3(2,2,2))
	var camera:=Camera3D.new();viewport.add_child(camera);camera.position=Vector3(0,0,3);camera.current=true
	await process_frame;await RenderingServer.frame_post_draw;await process_frame;await RenderingServer.frame_post_draw
	var image:=viewport.get_texture().get_image();var pixel:=image.get_pixel(48,48)
	expect(is_equal_approx(body.instances.get_instance_custom_data(0).a,299) and pixel.r>.55 and pixel.r<.70 and pixel.g<.05 and pixel.b<.05,"GPU retains custom alpha row 299 and reads the last bone from the six-row float pose palette")
	viewport.queue_free();await process_frame
