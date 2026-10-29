extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="diagnose-render-v14";root.add_child(g)
 while g.ui==null:await process_frame
 for i in range(3):await physics_frame
 g.staff.set_all_open(true);g.player.set_physics_process(false);g.player.input_enabled=false;g.hud.visible=false;g.elevators.set_physics_process(false);g.animator.paused=true;root.size=Vector2i(960,540)
 var shot=g.read_json("res://source/v12/final-retail-cameras.json")[1];g.player.position=g.v3(shot.eye)-Vector3(0,1.65,0);g.player.rotation=Vector3.ZERO;g.player.camera.position=Vector3(0,1.65,0);g.player.camera.fov=shot.fov;g.player.camera.look_at(g.v3(shot.look));g.player.reset_physics_interpolation()
 var env:Environment
 for node in g.get_children():
  if node is WorldEnvironment:env=node.environment
 var out="res://evidence/v14/renderer-diagnosis";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out))
 for stage in range(4):
  if stage==1:env.ssr_enabled=false
  if stage==2:env.ssil_enabled=false
  if stage==3:
   for node in g.get_children():
    if node is ReflectionProbe:node.visible=false
    for child in node.get_children():
     if child is VoxelGI:child.visible=false
  for i in range(4):await process_frame
  await RenderingServer.frame_post_draw;root.get_texture().get_image().save_png(out+"/stage-"+str(stage)+".png");print("DIAGNOSE_STAGE ",stage)
 quit()
