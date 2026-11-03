extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="surface-isolation";root.add_child(g)
 while g.ui==null:await process_frame
 g.player.set_physics_process(false);g.player.input_enabled=false;g.hud.visible=false;g.staff.set_all_open(true);g.elevators.set_physics_process(false);g.animator.paused=true;root.size=Vector2i(1920,1080)
 var shot=g.read_json("res://source/v12/final-retail-cameras.json")[0];g.player.position=g.v3(shot.eye)-Vector3(0,1.65,0);g.player.rotation=Vector3.ZERO;g.player.camera.position=Vector3(0,1.65,0);g.player.camera.fov=shot.fov;g.player.camera.look_at(g.v3(shot.look));g.player.reset_physics_interpolation()
 var out="res://evidence/v14/surface-isolation";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out))
 for stage in range(2):
  if stage==1:
   var replacements:Dictionary={}
   for node in g.get_children():
    if not node is MeshInstance3D:continue
    for i in range(node.mesh.get_surface_count()):
     var mat=node.mesh.surface_get_material(i)
     if not mat is ShaderMaterial or mat.shader.resource_path!="res://surface_v14.gdshader":continue
     if not replacements.has(mat):
      var proxy=StandardMaterial3D.new();proxy.albedo_texture=mat.get_shader_parameter("colour_map");proxy.albedo_color=mat.get_shader_parameter("tint");proxy.roughness=mat.get_shader_parameter("roughness_value");proxy.cull_mode=BaseMaterial3D.CULL_DISABLED;var rep:float=mat.get_shader_parameter("texture_repeat");proxy.uv1_scale=Vector3.ONE/max(.1,rep);replacements[mat]=proxy
     node.set_surface_override_material(i,replacements[mat])
  for i in range(12):await process_frame
  await RenderingServer.frame_post_draw;root.get_texture().get_image().save_png(out+"/stage-"+str(stage)+".png");print("SURFACE_ISOLATION ",stage)
 quit()
