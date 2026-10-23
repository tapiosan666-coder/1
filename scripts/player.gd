class_name ScannerPlayer
extends CharacterBody3D

signal fired
signal reload_requested
var camera: Camera3D
var gun: Node3D
var handheld: Node3D
var reader_screen: Label3D
var using_gun := false
var enabled := false
var sensitivity := 0.0022
var sprint_multiplier := 1.0
var double_jump_enabled := false
var air_jump_used := false
var recoil := 0.0
var time := 0.0

func _ready() -> void:
	var collision := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.radius = 0.32
	capsule.height = 1.78
	collision.shape = capsule
	collision.position.y = 0.9
	add_child(collision)
	camera = Camera3D.new()
	camera.position.y = 1.68
	camera.fov = 78
	camera.near = 0.05
	add_child(camera)
	camera.current = true
	gun = Node3D.new()
	camera.add_child(gun)
	gun.position = Vector3(0.25, -0.18, -0.65)
	var shell := Shapes.material(Color("78909d"))
	var dark := Shapes.material(Color("20363d"))
	var energy := Shapes.material(Color("b6ff94"), 1.0)
	Shapes.box(gun, Vector3.ZERO, Vector3(0.18, 0.16, 0.43), shell)
	Shapes.box(gun, Vector3(0, -0.11, 0.1), Vector3(0.11, 0.22, 0.12), dark)
	Shapes.box(gun, Vector3(0, 0.1, -0.05), Vector3(0.12, 0.055, 0.24), dark)
	Shapes.box(gun, Vector3(0, 0, -0.24), Vector3(0.1, 0.09, 0.09), dark)
	Shapes.box(gun, Vector3(0, 0, -0.291), Vector3(0.065, 0.055, 0.009), energy)
	Shapes.box(gun, Vector3(0.095, 0.01, 0.0), Vector3(0.008, 0.035, 0.19), energy)
	_make_handheld()

func _make_handheld() -> void:
	handheld = Node3D.new()
	camera.add_child(handheld)
	handheld.position = Vector3(0.24, -0.22, -0.55)
	handheld.rotation_degrees = Vector3(-12, -14, -5)
	var rubber := Shapes.material(Color("182027"))
	var metal := Shapes.material(Color("627780"))
	metal.metallic = 0.65
	metal.roughness = 0.3
	var screen := Shapes.material(Color("102d32"), 0.3)
	var light := Shapes.material(Color("93e7bb"), 0.5)
	var shell := Shapes.sphere(handheld, Vector3.ZERO, 1, rubber)
	shell.scale = Vector3(0.115, 0.18, 0.047)
	Shapes.box(handheld, Vector3(0, 0.01, 0.022), Vector3(0.19, 0.28, 0.035), metal)
	Shapes.box(handheld, Vector3(0, 0.03, 0.043), Vector3(0.158, 0.19, 0.009), screen)
	Shapes.box(handheld, Vector3(0, -0.075, 0.049), Vector3(0.12, 0.003, 0.002), light)
	for x in [-0.042, 0.0, 0.042]:
		Shapes.sphere(handheld, Vector3(x, -0.115, 0.039), 0.012, rubber)
	reader_screen = Shapes.sign_text(handheld, Vector3(0, 0.068, 0.051), "個体識別\nスキャナー", 26, Color("93e7bb"))
	reader_screen.pixel_size = 0.00065
	Shapes.box(handheld, Vector3(0, 0.19, 0), Vector3(0.09, 0.06, 0.055), rubber)
	Shapes.box(handheld, Vector3(0, 0.218, 0), Vector3(0.065, 0.003, 0.032), light)
	# A first-person gloved hand and sleeve anchor the instrument to the player.
	var glove := Shapes.material(Color("333b3d"))
	var palm := Shapes.sphere(handheld, Vector3(0.09, -0.13, -0.005), 0.055, glove)
	palm.scale = Vector3(0.65, 1.2, 0.8)
	var sleeve := Shapes.cylinder(handheld, Vector3(0.09, -0.26, -0.005), 0.045, 0.2, Shapes.material(Color("4c5756")))
	sleeve.rotation.z = -0.12

func _unhandled_input(event: InputEvent) -> void:
	if not enabled:
		return
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		rotate_y(-event.relative.x * sensitivity)
		camera.rotation.x = clampf(camera.rotation.x - event.relative.y * sensitivity, -1.45, 1.45)
	if event.is_action_pressed("reload"):
		reload_requested.emit()

func _physics_process(delta: float) -> void:
	time += delta
	if not enabled:
		velocity = Vector3.ZERO
		return
	var input := Input.get_vector("left", "right", "forward", "back")
	var direction := (transform.basis * Vector3(input.x, 0, input.y)).normalized()
	var speed := 5.0
	if Input.is_action_pressed("sprint"):
		speed = 8.5 * sprint_multiplier
	var aiming := Input.is_action_pressed("aim")
	if aiming:
		speed *= 0.55
	velocity.x = move_toward(velocity.x, direction.x * speed, delta * 40)
	velocity.z = move_toward(velocity.z, direction.z * speed, delta * 40)
	if is_on_floor():
		air_jump_used = false
	else:
		velocity.y -= 22 * delta
	if Input.is_action_just_pressed("jump"):
		if is_on_floor():
			velocity.y = 7
		elif double_jump_enabled and not air_jump_used:
			velocity.y = 7
			air_jump_used = true
	move_and_slide()
	if position.y < -10:
		position = Mall.ENTRANCE
	recoil = move_toward(recoil, 0, delta * 0.7)
	var target := Vector3(0.0, -0.14, -0.6) if aiming else Vector3(0.25, -0.18, -0.65)
	var bob := sin(time * 10) * 0.007 * minf(velocity.length() / 5, 1)
	gun.position = gun.position.lerp(target + Vector3(0, bob, recoil), delta * 12)
	handheld.position = handheld.position.lerp(Vector3(0.1, -0.15, -0.48) if aiming else Vector3(0.24, -0.22 + bob, -0.55), delta * 12)
	camera.fov = lerpf(camera.fov, 57.0 if aiming else 78.0, delta * 10)
	if Input.is_action_pressed("fire"):
		fired.emit()
