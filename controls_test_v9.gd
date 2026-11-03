extends SceneTree
var checks:Array=[]
func _initialize()->void:call_deferred("run")
func key(code:int,down:bool,physical:bool=false)->void:
 var e=InputEventKey.new();e.pressed=down
 if physical:e.physical_keycode=code
 else:e.keycode=code
 Input.parse_input_event(e)
func run()->void:
 var g=load("res://main.tscn").instantiate();root.add_child(g)
 while g.ui==null:await process_frame
 for i in range(5):await physics_frame
 for index in range(3):
  key(KEY_F1+index,true);await process_frame;key(KEY_F1+index,false)
  for i in range(14):await physics_frame
  var shot:Dictionary=g.read_json("res://source/cameras-v8.json")[[0,2,4][index]]
  var expected=g.v3(shot.look)-g.v3(shot.eye);expected.y=0;expected=expected.normalized()
  var view=-g.player.camera.global_basis.z;view.y=0;view=view.normalized();var forward=-g.player.global_basis.z
  checks.append({"id":"F%d-map-arrow-body-and-camera-heading"%(index+1),"pass":view.dot(expected)>.999 and forward.dot(view)>.999,"body_camera_dot":forward.dot(view)})
  var start:Vector3=g.player.position;key(KEY_W,true,true)
  for i in range(15):await physics_frame
  key(KEY_W,false,true);var delta:Vector3=g.player.position-start;delta.y=0
  checks.append({"id":"F%d-W-moves-toward-view"%(index+1),"pass":delta.length()>.7 and delta.normalized().dot(view)>.98,"metres":delta.length(),"view_dot":delta.normalized().dot(view)})
 key(KEY_M,true);await process_frame;key(KEY_M,false);var start:Vector3=g.player.position;var ticks:int=g.player.ticks;key(KEY_W,true,true)
 for i in range(40):await physics_frame
 key(KEY_W,false,true);checks.append({"id":"M-freezes-controller","pass":g.ui.overlay=="map"and g.player.position.distance_to(start)<.00001 and g.player.ticks==ticks})
 key(KEY_M,true);await process_frame;await process_frame;key(KEY_M,false)
 checks.append({"id":"M-closes","pass":g.ui.overlay==""and g.player.input_enabled,"overlay":g.ui.overlay,"input_enabled":g.player.input_enabled})
 key(KEY_F10,true);await process_frame;key(KEY_F10,false)
 checks.append({"id":"F10-opens-settings","pass":g.ui.overlay=="settings"})
 var config:Dictionary=g.ui.settings.snapshot();checks.append({"id":"default-1080p-144-vsync-60Hz","pass":config.requested_resolution==[1920,1080]and config.fps_limit==144 and config.vsync_requested and config.physics_ticks==60,"snapshot":config})
 var mechanics:Dictionary=g.animator.audit();checks.append({"id":"escalator-animation-assembly","pass":mechanics.failed==0,"mechanical_checks":mechanics.total})
 var result={"checks":checks,"passed":checks.filter(func(c):return c["pass"]).size(),"failed":checks.filter(func(c):return not c["pass"]).size(),"human_playtest":false,"runtime":g.results}
 var file=FileAccess.open("res://evidence/v9/controls.json",FileAccess.WRITE);file.store_string(JSON.stringify(result,"  "));print("V9_CONTROLS ",JSON.stringify(result));quit(0 if result.failed==0 else 2)
