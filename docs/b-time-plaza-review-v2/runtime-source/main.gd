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
func v3(a:Array)->Vector3:return Vector3(a[0],a[1],a[2])
func read_json(p:String):return JSON.parse_string(FileAccess.get_file_as_string(p))
func _ready()->void:
 start_usec=Time.get_ticks_usec()
 for arg:String in OS.get_cmdline_user_args():
  if arg=="--capture":mode="capture"
  if arg=="--preview":mode="capture";preview=true
  if arg=="--walk-test":mode="walk-test"
  if arg=="--animation":mode="animation"
  if arg.begins_with("--single="):only_shot=arg.trim_prefix("--single=")
  if arg.begins_with("--output="):output=arg.trim_prefix("--output=")
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(output))
 manifest=read_json("res://source/scene-manifest.json")
 font=load("res://assets/NotoSansCJKjp-Regular.otf")
 build_environment();build_materials()
 var geo:Dictionary=read_json("res://assets/geometry.json")
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
  var body=StaticBody3D.new();body.name="Collision_"+key
  var col=CollisionShape3D.new();var shape=ConcavePolygonShape3D.new();shape.backface_collision=true;shape.set_faces(points);col.shape=shape;body.add_child(col);add_child(body)
 for sign_data:Dictionary in geo.signs:build_sign(sign_data)
 var wayfinding=load("res://wayfinding.gd").new();add_child(wayfinding);wayfinding.setup(mats,font)
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
 var bottom=Label.new();bottom.add_theme_font_override("font",font);bottom.add_theme_font_size_override("font_size",14);bottom.position=Vector2(22,674);bottom.text="描画検証 v2  |  WASD 移動 / マウス 視点 / Shift 速歩 / Esc カーソル / F 扉開閉 / 1・2・3 検証階へ移動";layer.add_child(bottom)
 if mode!="interactive":player.input_enabled=false
 results={"godot_version":Engine.get_version_info(),"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"resolution":[1280,720],"msaa":"4x","source_sha256":manifest.source_sha256,"main_game_loaded":false,"graphics_revision":"v2","animation_shader_sha256":FileAccess.get_sha256("res://rubber.gdshader"),"staff_script_sha256":FileAccess.get_sha256("res://staff_doors.gd"),"animation_script_sha256":FileAccess.get_sha256("res://escalator_v2.gd"),"geometry_sha256":FileAccess.get_sha256("res://assets/geometry.json"),"main_script_sha256":FileAccess.get_sha256("res://main.gd"),"player_script_sha256":FileAccess.get_sha256("res://player.gd"),"scene_build_seconds":(Time.get_ticks_usec()-start_usec)/1000000.0}
 print("VALIDATION_READY ",JSON.stringify(results))
 await get_tree().physics_frame;await get_tree().physics_frame
 if mode=="capture":await capture()
 if mode=="walk-test":await test_walk()
 if mode=="animation":await capture_animation()
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
 env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;env.ambient_light_color=Color(.88,.86,.81);env.ambient_light_energy=.78;env.reflected_light_source=2
 env.tonemap_mode=Environment.TONE_MAPPER_FILMIC;env.tonemap_exposure=.90
 add_child(world)
 var sun=DirectionalLight3D.new();sun.name="Daylight";sun.rotation_degrees=Vector3(-58,-32,0);sun.light_energy=.65;sun.light_color=Color(1,.96,.86);sun.shadow_enabled=true;sun.directional_shadow_max_distance=95;sun.shadow_bias=.12;sun.shadow_normal_bias=1.2;sun.directional_shadow_mode=DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS;add_child(sun)
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
func capture()->void:
 var shots:Array=[
 {"id":"01-1F-time-plaza","p":Vector3(4,1.65,12),"look":Vector3(-14,7.5,-12)},
 {"id":"02-1F-west-escalators","p":Vector3(-9,1.65,22),"look":Vector3(-22,4.3,16)},
 {"id":"03-2F-crossing-bridge","p":Vector3(16,7.175,3),"look":Vector3(-14,8.2,-5)},
 {"id":"04-2F-storefront","p":Vector3(-31,7.175,27),"look":Vector3(-19,7.8,35)},
 {"id":"05-3F-void-and-roof","p":Vector3(14,12.525,0),"look":Vector3(-14,8.8,-4)},
 {"id":"06-1F-north-shopping-street","p":Vector3(-2,1.65,-28),"look":Vector3(8,2.4,-35)},
 {"id":"07-1F-cafe-interior","p":Vector3(-20.68,1.65,-34),"look":Vector3(-13,1.65,-40.5)},
 {"id":"08-1F-bookshop-interior","p":Vector3(-70.59,1.65,2.02),"look":Vector3(-72,1.6,-4)}]
 var performance:Array=[];hud.visible=false
 for shot:Dictionary in shots:
  if only_shot!="" and shot.id!=only_shot:continue
  player.set_physics_process(false);player.rotation=Vector3.ZERO;player.camera.global_position=shot.p;player.camera.look_at(shot.look)
  var measure:bool=not preview and shot.id in ["01-1F-time-plaza","03-2F-crossing-bridge","05-3F-void-and-roof"]
  for i in range(12 if measure else 8 if preview else 3):await get_tree().process_frame
  await RenderingServer.frame_post_draw
  var image=get_viewport().get_texture().get_image();var err=image.save_png(output+"/"+shot.id+".png")
  print("CAPTURE ",shot.id," ",err)
  if not measure:continue
  var samples:Array=[];var counters:Array=[]
  var last=Time.get_ticks_usec()
  for i in range(30):
   await get_tree().process_frame
   var now=Time.get_ticks_usec();samples.append((now-last)/1000.0);last=now
   counters.append({"draw_calls":Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),"objects":Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),"primitives":Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)})
  var sorted=samples.duplicate();sorted.sort();var sum_ms:float=0
  for t:float in samples:sum_ms+=t
  performance.append({"id":shot.id,"camera_eye_local":shot.p,"look_at_local":shot.look,"warmup_frames":12,"sample_frames":samples.size(),"mean_ms":sum_ms/samples.size(),"fps_from_mean_frame_time":1000.0/(sum_ms/samples.size()),"p50_ms":sorted[15],"p95_ms":sorted[28],"samples_ms":samples,"last_counters":counters.back()})
 if not preview:
  player.rotation=Vector3.ZERO;player.camera.position=Vector3(0,1.65,0);player.camera.rotation=Vector3(-.12,0,0);player.set_physics_process(true);player.belt_enabled=false
  await settle(Vector3(-3,0,28.3));player.auto_active=true;player.auto_speed=4.3;player.auto_target=Vector3(-3,0,21)
  var samples:Array=[];var last=Time.get_ticks_usec()
  for i in range(60):
   if Vector2(player.position.x-player.auto_target.x,player.position.z-player.auto_target.z).length()<.3:player.auto_target=Vector3(-3,0,28.3) if player.auto_target.z<25 else Vector3(-3,0,21)
   await get_tree().process_frame
   var now=Time.get_ticks_usec();samples.append((now-last)/1000.0);last=now
  player.auto_active=false;player.set_physics_process(false)
  var sorted=samples.duplicate();sorted.sort();var sum_ms:float=0
  for t:float in samples:sum_ms+=t
  results.walking_performance={"path":"1F plaza public floor out-and-back, CharacterBody3D movement","sample_frames":60,"mean_ms":sum_ms/60,"fps_from_mean_frame_time":60000.0/sum_ms,"p50_ms":sorted[30],"p95_ms":sorted[56],"samples_ms":samples}
 results.performance=performance;results.screenshot_kind="actual Godot 3D viewport; no image generation or retouch";results.npc_count=0;results.software_gpu="llvmpipe" in String(results.adapter).to_lower()
 write_json("render-results.json",results);print("CAPTURE_COMPLETE");get_tree().quit()
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
func test_walk()->void:
 var checks:Array=[];player.belt_enabled=false
 var routes:Array=read_json("res://source/walk-routes.json")
 for route:Dictionary in routes:
  await settle(v3(route.points[0]))
  var result=await walk_points(route.points)
  result.id=route.id;result.kind="capsule_move_and_slide_to_shop_or_public_waypoint";result.distance_m=route.distance_m;checks.append(result)
  print("WALK ",route.id," ",result["pass"])
 # Also test the actual four escalators uphill and downhill over their collidable inclines.
 for e:Dictionary in manifest.escalators:
  var a=v3(e.test_start);var b=v3(e.test_end)
  for reverse in[false,true]:
   var aa=b if reverse else a;var bb=a if reverse else b
   await settle(aa)
   # slope requires y-interpolated near endpoints, traversal uses physical slope contact
   var result=await walk_points([[bb.x,bb.y,bb.z]],2.0)
   result.id=e.id+("-down"if reverse else"-up");result.kind="physical_escalator_slope_walk";checks.append(result);print("ESC_WALK ",result.id," ",result["pass"])
 player.belt_enabled=true
 for e:Dictionary in manifest.escalators:
  var a=v3(e.test_start);var b=v3(e.test_end);var u=Vector3(e.u[0],0,e.u[1])
  var start=a+u*.85 if e.direction=="UP" else b-u*.85
  var target=b-u*.65 if e.direction=="UP" else a+u*.65
  await settle(start);player.auto_active=false
  var passed:bool=false;var ticks:int=0
  for i in range(3000):
   await get_tree().physics_frame;ticks+=1
   if Vector2(player.position.x-target.x,player.position.z-target.z).length()<.30 and abs(player.position.y-target.y)<.2:passed=true;break
  checks.append({"id":e.id+"-belt","kind":"automatic_conveyor_without_movement_input","pass":passed,"position":player.position,"target":target,"ticks":ticks})
  print("BELT ",e.id," ",passed)
 player.belt_enabled=false
 # Barrier probes: push into actual glazing/guardrail, not just source polygons.
 var probes:Array=[{"id":"2F-void-guard-west","a":Vector3(-13.5,5.525,0),"b":Vector3(-9,5.525,0)},{"id":"3F-void-guard-west","a":Vector3(-13.5,10.875,0),"b":Vector3(-9,10.875,0)}]
 for probe:Dictionary in probes:
  await settle(probe.a);player.auto_active=true;player.auto_target=probe.b;player.auto_speed=3
  for i in range(100):await get_tree().physics_frame
  player.auto_active=false
  var passed=player.position.x< -12 and abs(player.position.y-probe.a.y)<.2
  checks.append({"id":probe.id,"kind":"guardrail_prevents_fall","pass":passed,"end":player.position})
 # Actual 3D ray checks separate open atrium from crossing-bridge slab.
 var rays:Array=[
 {"id":"1F-departure-underfloor-support","a":Vector3(-20,.5,17),"b":Vector3(-20,-.5,17),"hit_expected":true},
 {"id":"2F-departure-underfloor-support","a":Vector3(23,5.9,17),"b":Vector3(23,5.0,17),"hit_expected":true},
 {"id":"2F-void-has-no-floor","a":Vector3(-1,5.9,2),"b":Vector3(-1,5.0,2),"hit_expected":false},
 {"id":"3F-void-has-no-floor","a":Vector3(-1,11.3,2),"b":Vector3(-1,10.4,2),"hit_expected":false},
 {"id":"2F-crossing-bridge-floor","a":Vector3(0,5.9,-6),"b":Vector3(0,5.0,-6),"hit_expected":true},
 {"id":"3F-crossing-bridge-floor","a":Vector3(0,11.3,-6),"b":Vector3(0,10.4,-6),"hit_expected":true},
 {"id":"1F-under-void-ground-floor","a":Vector3(-1,.5,2),"b":Vector3(-1,-.5,2),"hit_expected":true}]
 for ray:Dictionary in rays:
  var query=PhysicsRayQueryParameters3D.create(ray.a,ray.b);query.exclude=[player.get_rid()]
  var hit=get_world_3d().direct_space_state.intersect_ray(query)
  checks.append({"id":ray.id,"kind":"actual_3D_floor_or_void_raycast","pass":(not hit.is_empty())==ray.hit_expected,"hit":not hit.is_empty(),"hit_position":hit.get("position",null)})
 checks.append_array(await run_expanded_checks())
 var mechanical:Dictionary=animator.audit()
 checks.append_array(mechanical.checks)
 var passed:int=0
 for c:Dictionary in checks:
  if c["pass"]:passed+=1
 results.checks=checks;results.passed=passed;results.failed=checks.size()-passed;results.total=checks.size();results.kind="Godot CharacterBody3D collision walking, automated; not a human playtest";results.capsule_radius_m=.3;results.capsule_height_m=1.8;results.physics_hz=60;results.projection_or_teleport_during_route=false
 write_json("walk-results.json",results);print("WALK_COMPLETE ",passed,"/",checks.size());get_tree().quit(0 if passed==checks.size()else 1)

func collision_diagnostics()->Array:
 var out:Array=[]
 for i in range(player.get_slide_collision_count()):
  var c=player.get_slide_collision(i);out.append({"name":c.get_collider().name,"normal":c.get_normal(),"point":c.get_position()})
 return out

func capture_animation()->void:
 hud.visible=false;player.set_physics_process(false);player.rotation=Vector3.ZERO
 player.camera.global_position=Vector3(-16,1.65,12);player.camera.look_at(Vector3(-21,2.9,17))
 animator.paused=true
 var frames:Array=[]
 for i in range(24):
  var t=i/8.0;animator.set_time(t)
  for j in range(2):await get_tree().process_frame
  await RenderingServer.frame_post_draw
  var path=output+"/animation-%03d.png"%i;get_viewport().get_texture().get_image().save_png(path)
  frames.append({"frame":i,"simulation_seconds":t,"sha256":FileAccess.get_sha256(path)})
 var audit:Dictionary=animator.audit();audit.frames=frames;audit.capture_fps=8;audit.kind="Actual Godot viewport sampled at 8 Hz simulation clock, not measured realtime playback FPS";write_json("animation-results.json",audit)
 print("ANIMATION_CAPTURE_COMPLETE");get_tree().quit()

func _unhandled_input(event:InputEvent)->void:
 if mode=="interactive"and event is InputEventKey and event.pressed and not event.echo and event.keycode==KEY_F:staff.interact(player.global_position,player.get_rid())

func run_expanded_checks()->Array:
 var checks:Array=[];player.belt_enabled=false
 var definition:Dictionary=read_json("res://source/expanded-qa-inputs.json")
 # Closed leaves are actual collider/mesh assemblies. No testing through an assumed open gap.
 for i in range(min(staff.doors.size(),6)):
  staff.set_open(i,false)
  await get_tree().physics_frame
  var d:Dictionary=staff.doors[i];var n=Vector3(d.data.n[0],0,d.data.n[1]);var center:Vector3=d.center+Vector3.UP*1.1
  var query=PhysicsRayQueryParameters3D.create(center-n*.4,center+n*.4);query.exclude=[player.get_rid()]
  var hit=get_world_3d().direct_space_state.intersect_ray(query)
  checks.append({"id":d.data.id+"-closed-leaf","kind":"staff_door_actual_closed_collider","pass":not hit.is_empty()and hit.collider==d.pivot})
 staff.set_all_open(true)
 for i in range(2):await get_tree().physics_frame
 var routes:Array=definition.entrance_width_passes.duplicate();routes.append_array(definition.interior_routes);routes.append_array(definition.declared_backroom_routes)
 for route:Dictionary in routes:
  await settle(v3(route.points[0]))
  var result:Dictionary=await walk_points(route.points,3.0)
  result.id=route.id;result.kind=route.kind;checks.append(result)
  print("EXTENDED_WALK ",route.id," ",result["pass"])
 # Use actual static/dynamic physics world, not a polygon-only pass.
 for probe:Dictionary in definition.joint_ray_probes:
  var query=PhysicsRayQueryParameters3D.create(v3(probe.a),v3(probe.b));query.exclude=[player.get_rid()]
  var hit=get_world_3d().direct_space_state.intersect_ray(query)
  checks.append({"id":probe.id,"kind":probe.kind,"pass":not hit.is_empty(),"collider":str(hit.collider.name)if not hit.is_empty()else"none"})
 # Ceiling positions are checked from multiple interior points; decorative overhead surfaces are collidable.
 for j in range(0,definition.interior_routes.size(),3):
  var route:Dictionary=definition.interior_routes[j];var point:Vector3=v3(route.points.back());var floor_y=point.y
  var height:float=4.65 if route.store.begins_with("B2")else 4.825
  var a=point+Vector3.UP*2.5;var b=point+Vector3.UP*(height+.15)
  var query=PhysicsRayQueryParameters3D.create(a,b);query.exclude=[player.get_rid()]
  var hit=get_world_3d().direct_space_state.intersect_ray(query);var valid:bool=not hit.is_empty()and abs(hit.position.y-(floor_y+height))<.03
  checks.append({"id":route.id+"-ceiling-height","kind":"interior_actual_ceiling_raycast","pass":valid,"expected_world_y":floor_y+height,"hit":str(hit.get("position","none"))})
 staff.set_all_open(false)
 return checks
