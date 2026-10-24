extends SceneTree
var checks := 0
var failures := 0
func expect(ok: bool,message: String) -> void:
	checks += 1
	if not ok: failures += 1; push_error(message)
func _initialize() -> void:
	if DisplayServer.get_name() == "headless":
		printerr("Character rendering checks require a graphics display. Run without --headless.")
		quit(2); return
	call_deferred("run_tests")
func run_tests() -> void:
	var continuous := true; var bounded := true
	for role in ["walking","reading","seated","staff","conversation","browsing","restroom"]:
		for moving in [false,true]:
			for tick in 90:
				var motion := CivilianMotion.sample(role,role,tick/30.0,2,moving)
				for side in ["left","right"]:
					var arm: Dictionary = motion[side]
					var shoulder := Vector3(-.215 if side == "left" else .215,1.4,0)
					var upper_start: Vector3 = arm.arm.pos+arm.arm.basis.y*.15
					var upper_end: Vector3 = arm.arm.pos-arm.arm.basis.y*.15
					var lower_start: Vector3 = arm.forearm.pos+arm.forearm.basis.y*.145
					var lower_end: Vector3 = arm.forearm.pos-arm.forearm.basis.y*.145
					if upper_start.distance_to(shoulder) > .001 or upper_end.distance_to(lower_start) > .001 or lower_end.distance_to(arm.wrist) > .001: continuous = false
					if not arm.wrist.is_finite() or shoulder.distance_to(arm.wrist) > .586: bounded = false
	expect(continuous and bounded,"Idle, walking and role gestures retain connected shoulders, elbows and wrists across complete cycles")
	expect(is_zero_approx(CivilianMotion.blink_amount(0,0)) and CivilianMotion.blink_amount(.09,0) > .99 and is_zero_approx(CivilianMotion.blink_amount(.19,0)),"Blink opens, closes and reopens within a short natural cycle")
	var closes := false; var open_frames := 0
	for tick in 720:
		var blink := CivilianMotion.blink_amount(tick/60.0,3)
		closes = closes or blink > .9
		if blink < .01: open_frames += 1
	expect(closes and open_frames > 620,"Eyes spend most of the time open and still blink periodically")
	expect(not is_equal_approx(CivilianMotion.blink_amount(.09,0),CivilianMotion.blink_amount(.09,1)),"Individual blink timing does not synchronize the whole crowd")
	var game = load("res://scenes/main.tscn").instantiate(); root.add_child(game)
	game.start_run(300,912); game.set_physics_process(false); game.crowd.set_physics_process(false); game.player.set_physics_process(false)
	await physics_frame; await physics_frame
	var original: int = game.run.true_id
	game.crowd.positions[0] = MallCurve.world(Vector3(-57,0,-13)); game.crowd.roles[0] = "walking"; game.crowd.waits[0] = 30
	game.player.position = MallCurve.world(Vector3(-57,.1,-12)); game.player.camera.look_at(game.crowd.positions[0]+Vector3.UP*1.7)
	var snapshot: Array[Vector3] = game.crowd.positions.duplicate()
	var head: MultiMesh; var eyes: Array[MultiMesh] = []
	for part in game.crowd.parts:
		if part.name == "head": head = part.instances
		if part.name in ["eye_l","eye_r"]: eyes.append(part.instances)
	expect(eyes.size() == 2 and head != null,"Two articulated eyes share the character's existing identity")
	game.crowd.clock = 0; game.crowd._render(); await process_frame
	var slot: int = game.crowd.detailed_ids.find(0)
	expect(slot >= 0 and eyes[0].get_instance_transform(slot).basis.determinant() > .5,"Open eyes are rendered near the player")
	game.crowd.clock = .09; game.crowd._render(); await process_frame
	var closed := true
	for eye in eyes: closed = closed and absf(eye.get_instance_transform(slot).basis.determinant()) < .001
	expect(closed and head.get_instance_custom_data(slot).r > .99,"Blink data closes the skin lids and hides the eyeballs together")
	game.crowd.clock = .4; game.crowd._render(); await process_frame
	expect(eyes[0].get_instance_transform(slot).basis.determinant() > .5 and head.get_instance_custom_data(slot).r < .01,"Eyes restore their visible shape after blinking")
	expect(game.crowd.positions == snapshot and game.run.true_id == original and game.run.ap == 0 and game.run.cleared == 0,"Facial and body rendering never moves identities, changes truth or awards AP")
	var texture_bound := false; var common_tone := true
	for surface in head.mesh.get_surface_count():
		var material: Material = head.mesh.surface_get_material(surface)
		if material is ShaderMaterial and material.shader.resource_path == "res://assets/skin.gdshader" and not material.get_shader_parameter("lip_surface"):
			texture_bound = material.get_shader_parameter("skin_detail") is Texture2D and material.get_shader_parameter("skin_normal") is Texture2D
			common_tone = material.get_shader_parameter("skin_tint") == game.selected_skin
	expect(texture_bound and common_tone,"Authored skin maps retain the single shared skin tone rather than using clothing tint")
	var fabric_bound := false
	for part in game.crowd.parts:
		if part.name != "torso": continue
		for surface in part.instances.mesh.get_surface_count():
			var material: Material = part.instances.mesh.surface_get_material(surface)
			if material is ShaderMaterial and material.shader.resource_path == "res://assets/fabric.gdshader": fabric_bound = material.get_shader_parameter("fabric_detail") is Texture2D and material.get_shader_parameter("fabric_normal") is Texture2D
	expect(fabric_bound,"Clothing uses the authored textile and tangent-normal maps")
	for width in [.85,1.0,1.2]:
		game.selected_width = width; game.start_run(300,912); game.crowd.set_physics_process(false)
		game.crowd.positions[0] = MallCurve.world(Vector3(-57,0,-13)); game.crowd.roles[0] = "walking"; game.crowd.waits[0] = 30
		game.player.position = MallCurve.world(Vector3(-57,.1,-12)); game.player.camera.look_at(game.crowd.positions[0]+Vector3.UP*1.7); game.crowd.clock = .4; game.crowd._render(); await process_frame
		var head_transform := Transform3D.IDENTITY; var eye_transform := Transform3D.IDENTITY
		slot = game.crowd.detailed_ids.find(0)
		for part in game.crowd.parts:
			if part.name == "head": head_transform = part.instances.get_instance_transform(slot)
			if part.name == "eye_l": eye_transform = part.instances.get_instance_transform(slot)
		var relative := head_transform.basis.inverse()*(eye_transform.origin-head_transform.origin)
		expect(relative.distance_to(Vector3(-.3077*.12,0,-(1.2453-.45)*.105)) < .001,"Eye placement follows the chosen face width %.2f" % width)
	game.queue_free(); await process_frame; await create_timer(.3).timeout
	print("CHARACTER RESULT: %d checks, %d failures" % [checks,failures]); quit(1 if failures else 0)
