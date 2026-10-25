extends SceneTree
## Full-game evidence. Cutaway shots temporarily clip roofs/upper floors and hide tiny merchandise.
const CUT := "shader_type spatial; render_mode unshaded,cull_disabled; uniform vec4 tint:source_color=vec4(.65,.70,.66,1.0); uniform sampler2D color_map:source_color; uniform bool has_texture=false; uniform vec4 clip_bounds=vec4(-10000.0,-10000.0,10000.0,10000.0); uniform int region_mode=0; varying vec3 cut_p; varying vec4 vcolor; void vertex(){cut_p=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz;vcolor=COLOR;} void fragment(){if(cut_p.y>2.8||cut_p.y<-.4||cut_p.x<clip_bounds.x||cut_p.z<clip_bounds.y||cut_p.x>clip_bounds.z||cut_p.z>clip_bounds.w)discard;if(region_mode==2&&cut_p.z> -80.0&&abs(cut_p.x+370.0)>4.5)discard;if(region_mode==1&&cut_p.z< -26.0&&cut_p.x> -374.1&&cut_p.x< -365.9)discard;ALBEDO=tint.rgb*vcolor.rgb*(has_texture?texture(color_map,UV).rgb:vec3(1.0));ROUGHNESS=.9;}"

func _initialize()->void:call_deferred("capture")
func capture()->void:
 var game=load("res://scenes/main.tscn").instantiate();root.add_child(game)
 game.start_run(300,912);game.set_physics_process(false);game.crowd.set_physics_process(false);game.player.set_physics_process(false)
 GraphicsOptions.apply(game,"balanced",false);game.hud.visible=false;game.player.handheld.visible=false;game.player.gun.visible=false;game.crowd.clock=2.0
 var tag:="before" if "--before" in OS.get_cmdline_user_args() else "after"
 var shots=[
  ["a-junction",Vector3(-39,1.7,-8),Vector3(-39,6,-38)],
  ["b-entry",Vector3(-194,1.7,-5.5),Vector3(-325,4,43)],
  ["c-entry",Vector3(-370,1.7,-84),Vector3(-390,2,-123)]
 ]
 if tag=="after":shots.append(["b-plaza",Vector3(-325,1.7,43),Vector3(-400,6,13)])
 for shot in shots:
  game.player.camera.global_position=MallCurve.world(shot[1]);game.player.camera.look_at(MallCurve.world(shot[2]));game.crowd._render()
  await save_image("/tmp/fy020-%s-%s.png"%[tag,shot[0]])
 if tag=="after":
  game.hud.visible=true;game.set_mode("map")
  for level in [0,1,2]:
   game.hud.set_map_floor(level)
   await save_image("/tmp/fy020-after-map-%df.png"%(level+1))
  game.set_mode("play");game.hud.visible=false
 var shader:=Shader.new();shader.code=CUT
 var cut_materials:Array[ShaderMaterial]=[]
 for node:MeshInstance3D in game.mall.find_children("*","MeshInstance3D",true,false):
  node.visibility_range_end=0;node.visibility_range_begin=0
  if node.get_meta("retail_detail",false):node.visible=false;continue
  for index in node.mesh.get_surface_count():
   var original:Material=node.get_active_material(index);var material:=ShaderMaterial.new();material.shader=shader;cut_materials.append(material)
   if original is StandardMaterial3D:
    material.set_shader_parameter("tint",original.albedo_color)
    if original.albedo_texture!=null:material.set_shader_parameter("color_map",original.albedo_texture);material.set_shader_parameter("has_texture",true)
   elif original is ShaderMaterial:
    var source:String=original.shader.resource_path
    material.set_shader_parameter("tint",Color("93a99a") if "terrazzo" in source else Color("aa8f70") if "wood" in source else Color("d8d6cc"))
   node.set_surface_override_material(index,material)
  node.material_override=null
 for node:MultiMeshInstance3D in game.mall.find_children("*","MultiMeshInstance3D",true,false):node.visible=false
 for label:Label3D in game.mall.find_children("*","Label3D",true,false):label.visible=false
 game.store_signs.visible=false
 for node:WorldEnvironment in game.find_children("*","WorldEnvironment",true,false):
  node.environment=node.environment.duplicate();node.environment.background_mode=Environment.BG_COLOR;node.environment.background_color=Color("14272d")
 var maps=[
  ["a-cutaway",Vector3(10,220,85),Vector3(10,0,15),230.0,Vector4(-174,-85,195,165),0],
  ["b-cutaway",Vector3(-335,220,95),Vector3(-335,0,25),210.0,Vector4(-505,-65,-174,115),1],
  ["c-cutaway",Vector3(-375,220,-55),Vector3(-375,0,-125),220.0,Vector4(-480,-215,-280,-25),2]
 ]
 game.player.camera.projection=Camera3D.PROJECTION_ORTHOGONAL;game.player.camera.far=1000
 for shot in maps:
  for material:ShaderMaterial in cut_materials:material.set_shader_parameter("clip_bounds",shot[4]);material.set_shader_parameter("region_mode",shot[5])
  game.player.camera.size=shot[3];game.player.camera.global_position=shot[1];game.player.camera.look_at(shot[2]);game.crowd._render()
  await save_image("/tmp/fy020-%s-%s.png"%[tag,shot[0]])
 print("STRUCTURE_CAPTURE_OK ",tag);game.queue_free();await process_frame;quit()
func save_image(path:String)->void:
 for frame in 4:await process_frame
 await RenderingServer.frame_post_draw
 root.get_texture().get_image().save_png(path)
