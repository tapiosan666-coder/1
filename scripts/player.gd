class_name ScannerPlayer
extends CharacterBody3D

signal fired
signal reload_requested
var camera: Camera3D
var gun: Node3D
var enabled := false
var sensitivity := 0.0022
var sprint_multiplier := 1.0
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
	if not is_on_floor():
		velocity.y -= 22 * delta
	elif Input.is_action_just_pressed("jump"):
		velocity.y = 7
	move_and_slide()
	if position.y < -10:
		position = Vector3(0, 0.1, 12)
	recoil = move_toward(recoil, 0, delta * 0.7)
	var target := Vector3(0.0, -0.14, -0.6) if aiming else Vector3(0.25, -0.18, -0.65)
	var bob := sin(time * 10) * 0.007 * minf(velocity.length() / 5, 1)
	gun.position = gun.position.lerp(target + Vector3(0, bob, recoil), delta * 12)
	camera.fov = lerpf(camera.fov, 57.0 if aiming else 78.0, delta * 10)
	if Input.is_action_pressed("fire"):
		fired.emit()
