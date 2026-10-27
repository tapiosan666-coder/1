extends CharacterBody3D
var camera:Camera3D
var input_enabled:bool=true
var auto_target:Vector3
var auto_active:bool=false
var auto_speed:float=5.0
var previous:Vector3
var ticks:int=0
var landed:bool=false
var escalators:Array=[]
var belt_enabled:bool=true
var belt_id:String=""
func _ready()->void:
 floor_snap_length=.45
 floor_constant_speed=true
 floor_max_angle=deg_to_rad(38)
 var shape=CollisionShape3D.new()
 var capsule=CapsuleShape3D.new();capsule.radius=.3;capsule.height=1.8
 shape.shape=capsule;shape.position.y=.9;add_child(shape)
 camera=Camera3D.new();camera.position.y=1.65;camera.fov=75;camera.near=.08;camera.far=800
 add_child(camera);camera.current=true
func _unhandled_input(e:InputEvent)->void:
 if not input_enabled:return
 if e is InputEventMouseButton and e.pressed:Input.mouse_mode=Input.MOUSE_MODE_CAPTURED
 if e is InputEventKey and e.pressed and e.keycode==KEY_ESCAPE:Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
 if e is InputEventMouseMotion and Input.mouse_mode==Input.MOUSE_MODE_CAPTURED:
  rotate_y(-e.relative.x*.0022);camera.rotation.x=clamp(camera.rotation.x-e.relative.y*.0022,-1.4,1.4)
func _physics_process(dt:float)->void:
 previous=global_position;ticks+=1
 var motion=Vector3.ZERO
 if auto_active:
  var d=auto_target-global_position;d.y=0
  if d.length()>.06:motion=d.normalized()*min(auto_speed,d.length()/dt)
 elif input_enabled:
  var x=float(Input.is_physical_key_pressed(KEY_D))-float(Input.is_physical_key_pressed(KEY_A))
  var z=float(Input.is_physical_key_pressed(KEY_S))-float(Input.is_physical_key_pressed(KEY_W))
  motion=global_basis*Vector3(x,0,z).normalized()*(7.0 if Input.is_physical_key_pressed(KEY_SHIFT) else 4.3)
 velocity.x=motion.x;velocity.z=motion.z
 velocity.y=-1.0 if is_on_floor() else max(velocity.y-20*dt,-30)
 # Conveyor follows an actual collidable inclined support, not teleportation.
 belt_id=""
 if belt_enabled:
  for e:Dictionary in escalators:
   var c=Vector3(e.c[0],0,e.c[2]);var u=Vector3(e.u[0],0,e.u[1]);var delta=global_position-c
   var s=delta.dot(u);var lateral=delta.dot(Vector3(-u.z,0,u.x));var lo=float(e.low_y);var hi=float(e.high_y)
   var half=float(e.run_m)*.5;var height=lerp(lo,hi,clamp((s+half)/float(e.run_m),0.0,1.0))
   if abs(lateral)<.65 and s>=-half-1.45 and s<=half+1.45 and abs(global_position.y-height)<.55:
    var sign_dir=1.0 if e.direction=="UP" else -1.0
    var slope=float(e.rise_m)/float(e.run_m)
    var ground_speed=.50/sqrt(1+slope*slope)
    var conveyor=u*(ground_speed*sign_dir)
    velocity.x+=conveyor.x;velocity.z+=conveyor.z
    if is_on_floor():
     var active_slope=slope if s>=-half and s<=half else 0.0
     velocity.y=(velocity.x*u.x+velocity.z*u.z)*active_slope
    # Rise comes from slope contact via move_and_slide. Gravity / snap retains contact.
    belt_id=e.id;break
 move_and_slide()
 landed=is_on_floor()
