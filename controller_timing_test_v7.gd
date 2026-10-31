extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var root3d=Node3D.new();root.add_child(root3d);var body=StaticBody3D.new();var col=CollisionShape3D.new();var shape=BoxShape3D.new();shape.size=Vector3(1000,1,1000);col.shape=shape;col.position.y=-.5;body.add_child(col);root3d.add_child(body)
 var p=load("res://player.gd").new();root3d.add_child(p);p.input_enabled=false;p.belt_enabled=false
 var results:Array=[]
 for cap in [30,60,120,144,0]:
  Engine.max_fps=cap;p.auto_active=false;p.position=Vector3(0,.05,0);p.velocity=Vector3.ZERO
  for k in range(15):await physics_frame
  var start=p.position;p.auto_speed=4.3;p.auto_target=Vector3(0,0,-100);p.auto_active=true;var tick=p.ticks
  for k in range(120):await physics_frame
  p.auto_active=false;var distance=Vector2(p.position.x-start.x,p.position.z-start.z).length();results.append({"requested_cap":cap,"physics_ticks":p.ticks-tick,"distance_m":distance,"pass":abs(distance-8.6)<.1})
 var file=FileAccess.open("res://evidence/controller-fixed-tick-v7.json",FileAccess.WRITE);file.store_string(JSON.stringify({"checks":results,"not_actual_render_FPS_measurement":true,"fixed_physics_Hz":60,"NPCs_present":false},"  "));print("CONTROLLER_TIMING ",results);quit()
