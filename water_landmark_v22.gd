extends Node3D
var player:CharacterBody3D
var output:String="res://evidence/v22-water"
func material(col:Color,rough:float=.5,metal:float=0.)->StandardMaterial3D:
 var m=StandardMaterial3D.new();m.albedo_color=col;m.roughness=rough;m.metallic=metal;return m
func install_collision(node:Node)->void:
 if node is MeshInstance3D:
  var mesh:Mesh=node.mesh
  if mesh!=null:
   var body=StaticBody3D.new();var col=CollisionShape3D.new();var shape=ConcavePolygonShape3D.new();shape.set_faces(mesh.get_faces());shape.backface_collision=true;col.shape=shape;body.add_child(col);node.add_child(body)
 for c in node.get_children():
  if not c is StaticBody3D:install_collision(c)
func _ready()->void:
 Engine.max_fps=144;DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED)
 var environment=WorldEnvironment.new();var env=Environment.new();var sky=Sky.new();var atmosphere=ProceduralSkyMaterial.new();atmosphere.sky_top_color=Color(.21,.39,.57);atmosphere.sky_horizon_color=Color(.77,.83,.85);atmosphere.ground_horizon_color=Color(.65,.69,.67);sky.sky_material=atmosphere;env.sky=sky;env.background_mode=Environment.BG_SKY;env.ambient_light_source=Environment.AMBIENT_SOURCE_SKY;env.ambient_light_energy=.65;env.reflected_light_source=Environment.REFLECTION_SOURCE_SKY;env.tonemap_mode=Environment.TONE_MAPPER_FILMIC;env.ssao_enabled=true;env.ssr_enabled=true;environment.environment=env;add_child(environment)
 var sun=DirectionalLight3D.new();sun.rotation_degrees=Vector3(-44,-28,0);sun.light_color=Color(1,.95,.84);sun.light_energy=1.15;sun.shadow_enabled=true;sun.directional_shadow_max_distance=95;add_child(sun)
 var structure=load("res://assets/v22/models/water_landmark_structure.glb").instantiate();add_child(structure);install_collision(structure)
 var design:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://source/v22/water-landmark-design.json"));var poly=PackedVector2Array()
 for p:Array in design.basin_outline_xy:poly.append(Vector2(p[0],-p[1]))
 var triangles:PackedInt32Array=Geometry2D.triangulate_polygon(poly);var st=SurfaceTool.new();st.begin(Mesh.PRIMITIVE_TRIANGLES)
 for i:int in triangles:
  st.set_normal(Vector3.UP);st.set_uv(poly[i]*.10);st.add_vertex(Vector3(poly[i].x,.08,poly[i].y))
 var water=MeshInstance3D.new();water.mesh=st.commit();var shader=Shader.new();shader.code="shader_type spatial; render_mode cull_disabled; void fragment(){float a=sin(UV.x*20.0+TIME*.35)*cos(UV.y*22.0-TIME*.28);ALBEDO=vec3(.08,.20,.20)+a*.014;METALLIC=.25;ROUGHNESS=.12;NORMAL_MAP=normalize(vec3(a*.025,cos(UV.y*23.0+TIME*.4)*.018,1.0))*.5+.5;}";var water_mat=ShaderMaterial.new();water_mat.shader=shader;water.material_override=water_mat;add_child(water)
 for a:float in[.35,2.45,4.65]:
  var plant=load("res://assets/v17/models/atrium_ficus_dense.glb").instantiate();plant.position=Vector3(cos(a)*21.,0,-sin(a)*21.);plant.scale=Vector3.ONE*.9;add_child(plant)
 player=load("res://player.gd").new();player.position=Vector3(0,.25,23.0);add_child(player);player.camera.look_at(Vector3(0,1.0,0));player.collision_layer=2;player.collision_mask=1
 var canvas=CanvasLayer.new();var label=Label.new();label.text="v22 水景ランドマーク｜独立検証案・屋上未施工\nWASD 移動 / マウス 視点 / Esc カーソル / F1 モールへ戻る\n支持・荷重・排水・防水は未検証";label.add_theme_font_override("font",load("res://assets/NotoSansCJKjp-Regular.otf"));label.position=Vector2(20,20);canvas.add_child(label);add_child(canvas)
 set_meta("ready",true)
func _unhandled_input(e:InputEvent)->void:
 if e is InputEventKey and e.pressed and e.keycode==KEY_F1:get_tree().change_scene_to_file("res://main.tscn")
