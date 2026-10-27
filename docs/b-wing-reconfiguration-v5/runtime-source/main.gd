extends Node3D
var player:CharacterBody3D
var font:Font
var manifest:Dictionary
var mats:Dictionary={}
var hud:Label
var frame_times:Array=[]
var results:Dictionary={}
var mode:String="interactive"
var preview:bool=false
var output:String="res://evidence"
var mesh_count:int=0
var start_usec:int=0
var animator:Node3D
var animation_capture:bool=false
var only_shot:String=""
var staff:Node3D
var baseline:bool=false
func v3(a:Array)->Vector3:return Vector3(a[0],a[1],a[2])
func read_json(p:String):return JSON.parse_string(FileAccess.get_file_as_string(p))
func _ready()->void:
 start_usec=Time.get_ticks_usec()
 for arg:String in OS.get_cmdline_user_args():
  if arg=="--capture":mode="capture"
  if arg=="--baseline":baseline=true
  if arg=="--preview":mode="capture";preview=true
  if arg=="--walk-test":mode="walk-test"
  if arg=="--animation":mode="animation"
  if arg.begins_with("--single="):only_shot=arg.trim_prefix("--single=")
  if arg.begins_with("--output="):output=arg.trim_prefix("--output=")
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(output))
 manifest=read_json("res://source/scene-manifest-before.json"if baseline else"res://source/scene-manifest.json")
 font=load("res://assets/NotoSansCJKjp-Regular.otf")
 build_environment();build_materials()
 var geometry_path="res://assets/geometry-before.json.gz"if baseline else"res://assets/geometry.json.gz"
 var geo:Dictionary=JSON.parse_string(FileAccess.get_file_as_bytes(geometry_path).decompress_dynamic(1800000000,FileAccess.COMPRESSION_GZIP).get_string_from_utf8())
 for key:String in geo.surfaces:
  var material_key:String=key.split("@@")[0]
  var data:Dictionary=geo.surfaces[key];var a:Array=[];a.resize(Mesh.ARRAY_MAX)
  var vs=PackedVector3Array();var ns=PackedVector3Array();var uvs=PackedVector2Array();var cs=PackedColorArray()
  for i in range(0,data.v.size(),3):vs.append(Vector3(data.v[i],data.v[i+1],data.v[i+2]));ns.append(Vector3(data.n[i],data.n[i+1],data.n[i+2]))
  for i in range(0,data.uv.size(),2):uvs.append(Vector2(data.uv[i],data.uv[i+1]))
  for i in range(0,data.c.size(),4):cs.append(Color(data.c[i],data.c[i+1],data.c[i+2],data.c[i+3]))
  a[Mesh.ARRAY_VERTEX]=vs;a[Mesh.ARRAY_NORMAL]=ns;a[Mesh.ARRAY_TEX_UV]=uvs;a[Mesh.ARRAY_COLOR]=cs
  var mesh=ArrayMesh.new();mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,a);mesh.surface_set_material(0,mats.step_support if material_key=="step"else mats[material_key])
  if mats[material_key] is ShaderMaterial and material_key not in["glass","roof_glass"]:
   var st=SurfaceTool.new();st.create_from(mesh,0);st.generate_tangents();mesh=st.commit();mesh.surface_set_material(0,mats.step_support if material_key=="step"else mats[material_key])
  var instance=MeshInstance3D.new();instance.mesh=mesh;instance.name="Architecture_"+key
  var room_group:String=key.split("@@")[-1]
  if room_group.begins_with("B"):
   var room_index:int=0
   for si in range(manifest.shops.size()):
    if manifest.shops[si].id==room_group:room_index=si;break
   instance.layers=1|(1<<((room_index%18)+1))
  if material_key in ["glass","roof_glass","light"]:instance.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
  if material_key=="yellow"and room_group.begins_with("ARCH"):instance.visible=false
  add_child(instance);mesh_count+=1
 for key:String in geo.colliders:
  var data:Array=geo.colliders[key];var points=PackedVector3Array()
  for i in range(0,data.size(),3):points.append(Vector3(data[i],data[i+1],data[i+2]))
  var body=StaticBody3D.new();body.name="Collision_"+key;body.collision_layer=3 if key in ["plaster","wall_sand","wall_sage","wall_chalk","wall_taupe","dark_stone"]else 1
  var col=CollisionShape3D.new();var shape=ConcavePolygonShape3D.new();shape.backface_collision=true;shape.set_faces(points);col.shape=shape;body.add_child(col);add_child(body)
 for sign_data:Dictionary in geo.signs:build_sign(sign_data)
 
 # Low, local fixtures on three levels, after spatially grouping storefronts.
 for i in range(geo.lights.size()):
  var d:Dictionary=geo.lights[i]
  if d.get("type","")=="common" and i%8!=0:continue
  var light:SpotLight3D=SpotLight3D.new();light.position=v3(d.p);light.rotation_degrees.x=-90;light.light_color=Color(1,.91,.78)if d.get("type","")=="shop"else Color(1,.97,.89);light.light_energy=float(d.get("energy",.3));light.spot_range=8;light.spot_angle=62;light.spot_attenuation=1.2;light.shadow_enabled=false
  if d.get("type","")=="shop":light.light_cull_mask=1<<(int(d.get("room_index",0))%18+1)
  add_child(light)
 staff=load("res://staff_doors.gd").new();add_child(staff);staff.setup(manifest.get("staff_doors",[]),mats)
 animator=load("res://escalator_v2.gd").new();add_child(animator);animator.setup(manifest,mats)
 if mode!="interactive":animator.paused=true;animator.set_time(1.75)
 if mode!="walk-test":
  var probe=ReflectionProbe.new();probe.name="Atrium_Box_Reflection";probe.position=Vector3(0,7,3);probe.size=Vector3(82,19,105);probe.interior=false;probe.box_projection=true;probe.intensity=.6;probe.max_distance=100;probe.enable_shadows=false;probe.ambient_mode=0;probe.update_mode=0;add_child(probe)
 player=load("res://player.gd").new();player.name="WalkCapsule";add_child(player);player.position=Vector3(-3,.06,22.3)
 for e:Dictionary in manifest.escalators:
  e.low_y=manifest.floors[int(e.levels[0])].height;e.high_y=manifest.floors[int(e.levels[1])].height;player.escalators.append(e)
 var layer=CanvasLayer.new();add_child(layer)
 hud=Label.new();hud.add_theme_font_override("font",font);hud.add_theme_font_size_override("font_size",17);hud.position=Vector2(22,16);hud.add_theme_color_override("font_outline_color",Color(.08,.1,.09,.85));hud.add_theme_constant_override("outline_size",5);layer.add_child(hud)
 var bottom=Label.new();bottom.add_theme_font_override("font",font);bottom.add_theme_font_size_override("font_size",14);bottom.position=Vector2(22,674);bottom.text="独立・再構成検証 v5（未承認）  |  WASD 移動 / マウス 視点 / Shift 速歩 / Esc カーソル / F 扉開閉 / 1・2・3 検証階へ移動";layer.add_child(bottom)
 if mode!="interactive":player.input_enabled=false
 results={"godot_version":Engine.get_version_info(),"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"resolution":[1280,720],"msaa":"4x","source_sha256":manifest.source_original_sha256,"main_game_loaded":false,"graphics_revision":manifest.revision,"animation_shader_sha256":FileAccess.get_sha256("res://rubber.gdshader"),"staff_script_sha256":FileAccess.get_sha256("res://staff_doors.gd"),"animation_script_sha256":FileAccess.get_sha256("res://escalator_v2.gd"),"geometry_sha256":FileAccess.get_sha256(geometry_path),"main_script_sha256":FileAccess.get_sha256("res://main.gd"),"player_script_sha256":FileAccess.get_sha256("res://player.gd"),"scene_build_seconds":(Time.get_ticks_usec()-start_usec)/1000000.0}
 print("VALIDATION_READY ",JSON.stringify(results))
 await get_tree().physics_frame;await get_tree().physics_frame
 if mode=="capture":await load("res://validation.gd").new().capture(self)
 if mode=="walk-test":await load("res://validation.gd").new().walk(self)
 
func _process(dt:float)->void:
 if player==null:return
 hud.text="B館 / 時の広場   建築検証\n位置 %.1f / %.2f / %.1f m   FPS %.1f\n%s"%[player.position.x,player.position.y,player.position.z,Engine.get_frames_per_second(),"ESCALATOR "+player.belt_id if player.belt_id!="" else ""]
 if mode=="interactive":
  if Input.is_physical_key_pressed(KEY_1):player.position=Vector3(-3,.08,28.3)
  if Input.is_physical_key_pressed(KEY_2):player.position=Vector3(-3,5.605,28.3)
  if Input.is_physical_key_pressed(KEY_3):player.position=Vector3(-3,10.955,28.3)
func build_environment()->void:
 var world=WorldEnvironment.new();var env=Environment.new();world.environment=env
 env.background_mode=Environment.BG_SKY
 var sky=Sky.new();var sky_mat=ProceduralSkyMaterial.new();sky_mat.sky_top_color=Color(.38,.52,.67);sky_mat.sky_horizon_color=Color(.87,.89,.85);sky_mat.ground_bottom_color=Color(.38,.35,.30);sky_mat.ground_horizon_color=Color(.77,.75,.67);sky.sky_material=sky_mat;env.sky=sky
 env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;env.ambient_light_color=Color(.88,.89,.88);env.ambient_light_energy=.70;env.reflected_light_source=2
 env.tonemap_mode=Environment.TONE_MAPPER_FILMIC;env.tonemap_exposure=.90
 add_child(world)
 var sun=DirectionalLight3D.new();sun.name="Daylight";sun.rotation_degrees=Vector3(-58,-32,0);sun.light_energy=.12;sun.light_color=Color(1,.98,.93);sun.shadow_enabled=true;sun.directional_shadow_max_distance=95;sun.shadow_bias=.12;sun.shadow_normal_bias=1.2;sun.directional_shadow_mode=DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS;add_child(sun)
 var fill=DirectionalLight3D.new();fill.rotation_degrees=Vector3(-30,140,0);fill.light_color=Color(.72,.82,1);fill.light_energy=.08;fill.shadow_enabled=false;add_child(fill)
func plain(color:Color,rough:float=.5,metal:float=0)->StandardMaterial3D:
 var m=StandardMaterial3D.new();m.albedo_color=color;m.roughness=rough;m.metallic=metal;m.vertex_color_use_as_albedo=true;m.cull_mode=BaseMaterial3D.CULL_DISABLED;m.texture_filter=BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC;return m
func build_materials()->void:
 mats=load("res://material_library.gd").new().build()
func build_sign(d:Dictionary)->void:
 var mesh=QuadMesh.new();mesh.size=Vector2(d.w,d.h)
 var m=plain(Color.WHITE,.6);m.albedo_texture=load("res://assets/"+d.file);m.emission_enabled=true;m.emission=m.albedo_color;m.emission_texture=m.albedo_texture;m.emission_energy_multiplier=.12;mesh.material=m
 var n=MeshInstance3D.new();n.mesh=mesh;n.position=v3(d.p)
 var dir=Vector3(d.n[0],0,d.n[1]);n.basis=Basis(Vector3.UP.cross(dir),Vector3.UP,dir);add_child(n)
func write_json(name:String,data)->void:
 var file=FileAccess.open(output+"/"+name,FileAccess.WRITE);file.store_string(JSON.stringify(data,"  "))
func _unhandled_input(e:InputEvent)->void:
 if e is InputEventKey and e.pressed and e.keycode==KEY_F:staff.interact(player.position,player.get_rid())
func collision_diagnostics()->Array:
 var a:Array=[]
 for i in range(player.get_slide_collision_count()):
  var c=player.get_slide_collision(i);a.append({"collider":str(c.get_collider().name),"normal":str(c.get_normal()),"position":str(c.get_position())})
 return a
func settle(p:Vector3)->void:
 player.auto_active=false;player.velocity=Vector3.ZERO;player.position=p+Vector3(0,.06,0)
 for i in range(14):await get_tree().physics_frame
func walk_points(points:Array,speed:float=5.0)->Dictionary:
 var max_error:float=0;var ticks:int=0;var contacts:int=0
 player.auto_speed=speed;player.auto_active=true
 for pp in points:
  var target=v3(pp);player.auto_target=target
  var start=player.position;var budget=int((start.distance_to(target)/speed+4.0)*60);var reached:bool=false
  for i in range(budget):
   await get_tree().physics_frame;ticks+=1
   var flat=Vector2(player.position.x-target.x,player.position.z-target.z).length()
   max_error=max(max_error,abs(player.position.y-target.y))
   if player.get_slide_collision_count()>0:contacts+=1
   if flat<.16 and abs(player.position.y-target.y)<.22:reached=true;break
   if player.position.y< -1.5:return {"pass":false,"reason":"fell below floor","position":player.position,"target":target,"ticks":ticks,"colliders":collision_diagnostics()}
  if not reached:
   player.auto_active=false
   return {"pass":false,"reason":"not reached within physical tick budget","position":player.position,"target":target,"ticks":ticks,"colliders":collision_diagnostics()}
 player.auto_active=false
 return {"pass":true,"ticks":ticks,"contact_ticks":contacts,"max_vertical_difference_m":max_error,"position":player.position}
