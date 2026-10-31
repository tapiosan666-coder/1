extends Node3D
var player:CharacterBody3D
var manifest:Dictionary
var animator:Node3D
var mats:Dictionary
var helper
func _ready()->void:
 helper=load("res://main.gd").new();mats=load("res://material_library.gd").new().build(false);load("res://finish_v8.gd").new().extend(mats);load("res://finish_v9.gd").new().extend(mats);load("res://finish_v10.gd").new().extend(mats)
 manifest=JSON.parse_string(FileAccess.get_file_as_string("res://source/v12/es-transfer-study.json"));var geo=helper.load_geometry("res://assets/v12/es-transfer-study.pack.zst")
 for k:String in geo.surfaces:
  var d:Dictionary=geo.surfaces[k];var arrays:Array=[];arrays.resize(Mesh.ARRAY_MAX);var vv=PackedVector3Array();var nn=PackedVector3Array();var uv=PackedVector2Array()
  for i in range(0,d.v.size(),3):vv.append(Vector3(d.v[i],d.v[i+1],d.v[i+2]));nn.append(Vector3(d.n[i],d.n[i+1],d.n[i+2]))
  for i in range(0,d.uv.size(),2):uv.append(Vector2(d.uv[i],d.uv[i+1]))
  arrays[Mesh.ARRAY_VERTEX]=vv;arrays[Mesh.ARRAY_NORMAL]=nn;arrays[Mesh.ARRAY_TEX_UV]=uv
  if d.has("i"):arrays[Mesh.ARRAY_INDEX]=d.i
  var mesh=ArrayMesh.new();mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays);var material_key=k.split("@@")[0];mesh.surface_set_material(0,mats.step_support if material_key=="step"else mats[material_key]);var instance=MeshInstance3D.new();instance.mesh=mesh;add_child(instance)
 for k:String in geo.colliders:
  var vv=PackedVector3Array();var d=geo.colliders[k]
  for i in range(0,d.size(),3):vv.append(Vector3(d[i],d[i+1],d[i+2]))
  var body=StaticBody3D.new();body.name="Study_collision_"+k;var shape=ConcavePolygonShape3D.new();shape.set_faces(vv);shape.backface_collision=true;var node=CollisionShape3D.new();node.shape=shape;body.add_child(node);add_child(body)
 var env=WorldEnvironment.new();var e=Environment.new();e.background_mode=Environment.BG_SKY;var sky=Sky.new();var sky_mat=ProceduralSkyMaterial.new();sky_mat.sky_top_color=Color(.28,.46,.68);sky_mat.sky_horizon_color=Color(.74,.80,.83);sky.sky_material=sky_mat;e.sky=sky;e.reflected_light_source=Environment.REFLECTION_SOURCE_SKY;e.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;e.ambient_light_color=Color(.9,.93,1);e.ambient_light_energy=.65;e.tonemap_mode=Environment.TONE_MAPPER_ACES;env.environment=e;add_child(env)
 var sun=DirectionalLight3D.new();sun.rotation_degrees=Vector3(-55,-35,0);sun.light_energy=1.4;sun.shadow_enabled=true;add_child(sun)
 player=load("res://player.gd").new();player.position=Vector3(-9.2,0,-2.2);player.escalators=manifest.escalators;add_child(player);player.rotate_y(-PI/2)
 animator=load("res://escalator_v2.gd").new();add_child(animator);animator.setup(manifest,mats)
 var layer=CanvasLayer.new();add_child(layer);var label=Label.new();label.add_theme_font_override("font",load("res://assets/NotoSansCJKjp-Regular.otf"));label.position=Vector2(25,20);label.text="未承認：5層エスカレーター乗継ぎ構造検討（敷地には未配置）\nB1 → 1F → 2F → 3F → RF / 上下各1基・4組 / 中間階の乗継ぎ設計8.4m\nWASD・マウス：移動 / F4：全館検証へ戻る / 地下からは上下の実機で移動";layer.add_child(label)
 for f:Dictionary in manifest.floors:
  for x:float in[-10,10]:
   var text=Label3D.new();text.text=String(f.label)+"  /  NEXT FLOOR";text.font=load("res://assets/NotoSansCJKjp-Regular.otf");text.position=Vector3(x,float(f.height)+2.6,0);text.rotation_degrees.y=90 if x<0 else-90;text.font_size=54;text.pixel_size=.008;add_child(text)
func _unhandled_input(e:InputEvent)->void:
 if e is InputEventKey and e.pressed and e.keycode==KEY_F4:get_tree().change_scene_to_file("res://main.tscn")
func _exit_tree()->void:
 if is_instance_valid(helper):helper.free()
