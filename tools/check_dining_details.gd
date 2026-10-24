extends SceneTree
## Isolated fixture: never writes the production world cache.
class DiningFixture extends Node3D:
	var identity_slots:Array[Dictionary]=[]
var checks:=0
var failures:=0
func expect(ok:bool,message:String)->void:
	checks+=1
	if not ok:failures+=1;push_error(message)
func _initialize()->void:call_deferred("verify")
func fixture()->DiningFixture:
	var scene:=DiningFixture.new();root.add_child(scene)
	var wood:=Shapes.timber();var dark:=Shapes.material(Color("25363d"));var cream:=Shapes.material(Color("dedbd0"))
	var retained:=0
	for x in DiningDetails.TABLE_X:
		for z in DiningDetails.TABLE_Z:
			Shapes.box(scene,Vector3(x,.78,z),Vector3(2.6,.1,1.4),wood,true)
			Shapes.cylinder(scene,Vector3(x,.365,z),.15,.73,cream)
			for offset in DiningDetails.CHAIR_OFFSETS:
				var pos:=Vector3(x+offset.x,0,z+offset.y);var yaw:=atan2(offset.x,offset.y)
				var chair:=Node3D.new();scene.add_child(chair);chair.position=pos;chair.rotation.y=yaw
				Shapes.box(chair,Vector3(0,.47,0),Vector3(.6,.1,.6),wood,true)
				Shapes.box(chair,Vector3(0,.85,.27),Vector3(.6,.7,.07),wood)
				for a in [-.23,.23]:
					for b in [-.23,.23]:Shapes.box(chair,Vector3(a,.22,b),Vector3(.04,.44,.04),dark)
				var tray:=Shapes.box(scene,Vector3(x+offset.x*.38,.85,z+offset.y*.35),Vector3(.5,.025,.35),dark);tray.rotation.y=yaw
				Shapes.cylinder(scene,tray.position+Vector3(.1,.08,0),.055,.14,cream)
				if retained<10:scene.identity_slots.append({"pos":pos,"yaw":yaw,"role":"seated"})
				retained+=1
	for i in 4:
		scene.identity_slots.append({"pos":Vector3(62.35 if i<2 else 77.65,0,-20.9+(i%2)*1.6),"yaw":0.,"role":"seated","activity":"food_wait"})
	for x in DiningDetails.TENANT_X:
		Shapes.box(scene,Vector3(x,.5,-59.5),Vector3(9,1,1),wood,true)
		for dx in [-2.,0.,2.]:Shapes.cylinder(scene,Vector3(x+dx,1.06,-59.4),.24,.08,cream)
		for dx in [-2.8,2.8]:
			for n in 4:Shapes.soft_box(scene,Vector3(x+dx,1.06+n*.022,-59.45),Vector3(.6,.018,.4),dark)
	return scene
func verify()->void:
	var scene:=fixture()
	if "--before" in OS.get_cmdline_user_args():
		await capture(scene,"before");print("DINING_BASELINE_CAPTURED");quit();return
	var identities:=var_to_str(scene.identity_slots)
	var collider_count:=scene.find_children("*","CollisionShape3D",true,false).size()
	var detail:=DiningDetails.new();detail.build(scene)
	var node:MeshInstance3D=scene.get_node("DiningFitout")
	expect(var_to_str(scene.identity_slots)==identities,"Visual dining replacement never moves or changes NPC slots")
	expect(scene.find_children("*","CollisionShape3D",true,false).size()==collider_count and collider_count==49,"Every original table, seat and counter collider remains; no extra obstacles")
	expect(detail.counts.tables==9 and detail.counts.chairs==36 and detail.counts.meals==10 and detail.counts.counters==4,"Nine tables, 36 chairs and four counters use meals at only the ten occupied seats")
	expect(node.mesh.get_surface_count()==3,"All furniture, food and counter graphics use three shared materials")
	expect(detail.counts.hidden_placeholders==350,"Old wooden shells, floating placeholder trays/cups/plates and stacks are replaced once")
	var within:=true;var finite:=true;var triangles:=0
	for s in node.mesh.get_surface_count():
		var arrays:Array=node.mesh.surface_get_arrays(s);triangles+=arrays[Mesh.ARRAY_INDEX].size()/3
		for p:Vector3 in arrays[Mesh.ARRAY_VERTEX]:
			if not p.is_finite():finite=false
			var found:=false
			for envelope:Rect2 in detail.envelopes:
				if envelope.grow(.03).has_point(Vector2(p.x,p.z)):found=true;break
			if not found:within=false
	expect(finite and within,"Added geometry stays finite and inside the existing furniture envelopes (3 cm finish allowance)")
	expect(triangles<50000,"Furniture replacement stays below a 50,000-triangle budget")
	if "--capture" in OS.get_cmdline_user_args():await capture(scene,"after")
	print("DINING DETAILS RESULT: %d checks, %d failures; %d triangles"%[checks,failures,triangles]);quit(1 if failures else 0)
func capture(scene:Node3D,tag:String)->void:
	Shapes.box(scene,Vector3(69,-.1,-47),Vector3(46,.2,30),MallFinishes.stone(),true)
	for z in [-62.,-32.]:Shapes.box(scene,Vector3(69,2.5,z),Vector3(46,5,.2),Shapes.material(Color("d4d2c9")))
	var env:=WorldEnvironment.new();env.environment=Environment.new();env.environment.background_mode=Environment.BG_COLOR;env.environment.background_color=Color("b7c2c0");env.environment.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;env.environment.ambient_light_energy=.45;root.add_child(env)
	var sun:=DirectionalLight3D.new();sun.rotation_degrees=Vector3(-55,-30,0);sun.light_energy=.9;root.add_child(sun)
	var camera:=Camera3D.new();root.add_child(camera);camera.current=true;camera.fov=65
	for shot in [["meal",Vector3(51.6,1.55,-37.1),Vector3(52.3,.9,-39)],["chair",Vector3(49.6,1.25,-38),Vector3(51.1,.65,-39)],["counter",Vector3(49.1,1.6,-56.5),Vector3(51,1.13,-59.5)],["terminal",Vector3(47.55,1.45,-58.2),Vector3(47.55,1.30,-59.57)],["court",Vector3(58.5,1.75,-34),Vector3(66,1.5,-59.5)]]:
		camera.position=shot[1];camera.look_at(shot[2]);await create_timer(.3).timeout;await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/fy15-dining-%s-%s.png"%[tag,shot[0]])
