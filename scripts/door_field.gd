class_name DoorField
extends Node3D
## Runtime-only doors: never merged into static world geometry or AO.
enum Interaction { NONE, STARTED, BLOCKED, BUSY }
var game: Node3D
var doors: Array[Dictionary] = []

func setup(owner_game: Node3D) -> void:
	game=owner_game; process_mode=Node.PROCESS_MODE_PAUSABLE
	for spec in RestroomWing.door_specs()+UpperRetail.door_specs():
		var body := AnimatableBody3D.new(); add_child(body)
		body.sync_to_physics=false; body.collision_layer=1; body.collision_mask=1
		body.set_meta("interactive_door",doors.size())
		var base := Transform3D(MallCurve.jacobian(spec.hinge)*Basis(Vector3.UP,spec.yaw),MallCurve.world(spec.hinge))
		body.transform=base
		var height: float=spec.get("height",2.2)
		var panel := Shapes.soft_box(body,Vector3(spec.width*.5,height*.5,0),Vector3(spec.width,height,.055),Shapes.material(spec.color))
		panel.visibility_range_end=40; panel.visibility_range_end_margin=3
		var collision := CollisionShape3D.new(); var shape := BoxShape3D.new()
		shape.size=Vector3(spec.width,height,.06); collision.shape=shape; collision.position=Vector3(spec.width*.5,height*.5,0); body.add_child(collision)
		var metal := Shapes.material(Color("b8bcb4")); metal.metallic=.75; metal.roughness=.3
		for side in [-1,1]:
			Shapes.box(body,Vector3(spec.width-.12,1.02,side*.065),Vector3(.13,.025,.045),metal).visibility_range_end=25
		var state := Shapes.sign_text(body,Vector3(spec.width*.5,1.55,-.035),"空室",19,Color("e8e6da")); state.rotation.y=PI; state.pixel_size=.003; state.visibility_range_end=20
		doors.append({"spec":spec,"body":body,"base":base,"angle":0.0,"goal":0.0,"open":false,"moving":false})
	set_physics_process(false)

func reset() -> void:
	for door in doors:
		door.body.transform=door.base; door.angle=0.0; door.goal=0.0; door.open=false; door.moving=false
	set_physics_process(false)

func focused(camera: Camera3D) -> int:
	var from := camera.global_position
	var ray := PhysicsRayQueryParameters3D.create(from,from-camera.global_basis.z*2.6,1,[game.player.get_rid()])
	var hit := get_world_3d().direct_space_state.intersect_ray(ray)
	return int(hit.collider.get_meta("interactive_door")) if not hit.is_empty() and hit.collider.has_meta("interactive_door") else -1

func hint(camera: Camera3D) -> String:
	var index := focused(camera)
	if index<0: return ""
	return "F / %sを%s" % [doors[index].spec.label,"閉める" if doors[index].open else "開ける"]

func interact(camera: Camera3D) -> Interaction:
	var index := focused(camera)
	if index<0: return Interaction.NONE
	var door: Dictionary=doors[index]
	if door.moving: return Interaction.BUSY
	var goal: float=0.0 if door.open else door.spec.open_angle
	if not _clear_between(door,door.angle,goal): return Interaction.BLOCKED
	# Stop an in-flight scan when the player operates a physical obstruction.
	game.handheld_scan.reset()
	door.open=not door.open; door.goal=goal; door.moving=true; set_physics_process(true)
	return Interaction.STARTED

func _clear_between(door: Dictionary, start: float, end: float) -> bool:
	var actors: Array[Vector3]=[game.player.global_position]
	if is_instance_valid(game.crowd):
		for id in game.crowd.positions.size():
			if not game.run.eliminated[id]: actors.append(game.crowd.positions[id])
	var inverse: Transform3D=door.base.affine_inverse()
	var steps := maxi(1,ceili(absf(end-start)/.08))
	for actor in actors:
		var p: Vector3=inverse*actor
		if p.y>door.spec.get("height",2.2)+.2 or p.y+1.85<0: continue
		var q := Vector2(p.x,p.z)
		if q.length()>door.spec.width+.6: continue
		for step in range(steps+1):
			var angle := lerpf(start,end,float(step)/steps)
			var tip: Vector2 = Vector2(cos(angle),-sin(angle))*door.spec.width
			if q.distance_to(Geometry2D.get_closest_point_to_segment(q,Vector2.ZERO,tip))<.48: return false
	return true

func _physics_process(delta: float) -> void:
	var active := false
	for door in doors:
		if not door.moving: continue
		var next := move_toward(float(door.angle),float(door.goal),delta*4.5)
		if not _clear_between(door,door.angle,next):
			door.moving=false; continue
		door.angle=next; door.body.transform=door.base*Transform3D(Basis(Vector3.UP,next),Vector3.ZERO)
		if is_equal_approx(next,door.goal): door.moving=false
		else: active=true
	set_physics_process(active)
