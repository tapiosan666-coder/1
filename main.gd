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
var brand_registry:Dictionary={}
var elevators:Node3D
var ui:CanvasLayer
var baseline:bool=false
var visual_v7:bool=false
var fitout:Dictionary={}
var showcase:Node
var with_context:bool=true
var context_only:bool=false
@export var c_open_proposal:bool=false
@export var es_site_proposal:bool=false
var commons_v16
var scenery_v17
var retail_v18_plan:Dictionary={}
var retail_v18
var shoppers_v18
var draft:bool=false
var art_v10:Dictionary={}
var interaction_notice:String=""
var notice_seconds:float=0.0
func v3(a:Array)->Vector3:return Vector3(a[0],a[1],a[2])
func data_hash(p:String)->String:return FileAccess.get_sha256(p if FileAccess.file_exists(p)else p+".zst")
func read_json(p:String):
 if not FileAccess.file_exists(p)and FileAccess.file_exists(p+".zst"):
  var bytes=FileAccess.get_file_as_bytes(p+".zst");var raw=bytes.slice(8).decompress(bytes.decode_u32(4),FileAccess.COMPRESSION_ZSTD);return JSON.parse_string(raw.get_string_from_utf8())
 return JSON.parse_string(FileAccess.get_file_as_string(p))
func load_geometry(path:String)->Dictionary:
 var packed=FileAccess.get_file_as_bytes(path)
 var raw=packed.slice(8).decompress(packed.decode_u32(4),FileAccess.COMPRESSION_ZSTD)if path.ends_with(".pack.zst")else packed.decompress_dynamic(1800000000,FileAccess.COMPRESSION_GZIP)
 if not path.ends_with(".pack.gz")and not path.ends_with(".pack.zst"):return JSON.parse_string(raw.get_string_from_utf8())
 var count=raw.decode_u32(4);var head:Dictionary=JSON.parse_string(raw.slice(8,8+count).get_string_from_utf8());var start=8+count
 for key:String in head.surfaces:
  for field:String in head.surfaces[key]:
   var slot:Array=head.surfaces[key][field];head.surfaces[key][field]=raw.slice(start+int(slot[0]),start+int(slot[0])+int(slot[1])).to_int32_array()if field=="i"else raw.slice(start+int(slot[0]),start+int(slot[0])+int(slot[1])).to_float32_array()
 for key:String in head.colliders:
  var slot:Array=head.colliders[key];head.colliders[key]=raw.slice(start+int(slot[0]),start+int(slot[0])+int(slot[1])).to_float32_array()
 return head
func _ready()->void:
 start_usec=Time.get_ticks_usec()
 for required:String in ["base-b","base-site","fitout","art","architecture"]:
  var data_path="res://assets/v10/"+required+".pack.zst"
  if not FileAccess.file_exists(data_path):
   push_error("配布データが不足しています: "+data_path)
   OS.alert("マップデータが不足しています。統合版ZIPを新しいフォルダにすべて展開し、そこにあるproject.godotを開いてください。", "FIND YOURSELF：データ不足")
   get_tree().quit(2);return
 for required_path:String in ["res://assets/v11/repairs.pack.zst","res://assets/v12/es-safety.pack.zst","res://assets/v12/retail.pack.zst","res://assets/v12/boundary-physics.pack.zst","res://assets/v12/es-unbuilt-safety.pack.zst","res://assets/v12/es-transfer-study.pack.zst","res://assets/v12/es-landing-plates.pack.zst","res://assets/v13/amenities.pack.zst","res://assets/v13/public-areas.pack.zst","res://assets/v13/basement-retail.pack.zst","res://assets/v13/roof-retail.pack.zst","res://assets/v15/C-finish-replacement.pack.zst","res://assets/v15/ES-site-replacement.pack.zst","res://assets/v15/retail-services.pack.zst"]:
  var bytes=FileAccess.get_file_as_bytes(required_path)
  if bytes.size()<12 or bytes.slice(0,4).get_string_from_ascii()!="FYZ1":
   push_error("検証版データの欠落または破損: "+required_path);OS.alert("データが不足または破損しています。v18 ZIPを新しいフォルダへすべて展開してください。\n"+required_path,"FIND YOURSELF：データ不足");get_tree().quit(2);return
 for arg:String in OS.get_cmdline_user_args():
  if arg=="--capture":mode="capture"
  if arg=="--draft":draft=true
  if arg=="--bake-gi":mode="bake-gi"
  if arg=="--c-open-proposal":c_open_proposal=true
  if arg=="--es-site-proposal":es_site_proposal=true
  if arg=="--v7-visual":visual_v7=true
  if arg=="--benchmark-v8":mode="benchmark-v8"
  if arg=="--walk-v8":mode="walk-v8"
  if arg=="--baseline":
   push_error("v7 does not reconstruct the v6 comparison. Open the preserved v6 project for that baseline.");get_tree().quit(2);return
  if arg=="--no-context":with_context=false
  if arg=="--context-only":context_only=true
  if arg=="--preview":mode="capture";preview=true
  if arg=="--walk-test":mode="walk-test"
  if arg=="--vehicle-test":mode="vehicle-test"
  if arg=="--ui-test":mode="ui-test"
  if arg=="--animation":mode="animation"
  if arg.begins_with("--single="):only_shot=arg.trim_prefix("--single=")
  if arg.begins_with("--output="):output=arg.trim_prefix("--output=")
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(output))
 manifest=read_json("res://source/scene-manifest-before.json"if baseline else"res://source/scene-manifest.json")
 if not FileAccess.file_exists("res://assets/v11/repairs.pack.zst"):
  OS.alert("改修用マップデータが不足しています。v20の完全ZIPを新しいフォルダへ展開し直してください。","FIND YOURSELF：データ不足");get_tree().quit(2);return
 font=load("res://assets/NotoSansCJKjp-Regular.otf")
 retail_v18_plan=read_json("res://source/v19/retail-plan.json")
 var v21_plan:Dictionary=read_json("res://source/v21/retail-plan.json");retail_v18_plan.stores=v21_plan.retirement_stores;retail_v18_plan.replacement_store_ids=v21_plan.retirement_stores.map(func(d):return str(d.id))
 build_environment();build_materials()
 var v17_colours:Dictionary={"ink":Color(.055,.10,.12),"bronze":Color(.39,.26,.13),"oak":Color(.43,.31,.18),"sage":Color(.16,.25,.20),"porcelain":Color(.68,.66,.60),"plum":Color(.23,.15,.23)}
 for key:String in v17_colours:
  var mat=StandardMaterial3D.new();mat.albedo_color=v17_colours[key];mat.roughness=.38 if key=="bronze"else .60;mat.metallic=.7 if key=="bronze"else 0.;mats["v17_"+key]=mat
 if not visual_v7:fitout=read_json("res://source/fitout-v11.json");load("res://finish_v8.gd").new().extend(mats);load("res://finish_v9.gd").new().extend(mats);load("res://finish_v10.gd").new().extend(mats);art_v10=read_json("res://source/v12/scene-art-C.json"if c_open_proposal else"res://source/v12/scene-art.json")
 if not visual_v7:
  art_v10=load("res://commons_v16.gd").reconcile_ground_planting(art_v10,read_json("res://source/v16/commons.json"))
  for retail_item:Dictionary in art_v10.instances:
   if str(retail_item.group)=="C1F-CSW-3"and str(retail_item.asset)=="retail/cafe_counter":retail_item.asset="../v15/models/cafe_order_counter"
 if not visual_v7:
  load("res://finish_v14.gd").new().extend(mats)
  mats.v17_oak=mats.v10_oak.duplicate();mats.v17_oak.set_shader_parameter("tint",Color(.85,.79,.68))
 var geometry_path="res://assets/geometry-before.json.gz"if baseline else("res://assets/baseline-b-v7.pack.gz"if visual_v7 else"res://assets/v10/base-b.pack.zst")
 var geo:Dictionary=load_geometry(geometry_path)
 if context_only:
  geometry_path="res://assets/site-v7.json.gz";geo=load_geometry(geometry_path);manifest.escalators=[];manifest.staff_doors=[]
 elif with_context:
  var ctx:Dictionary=load_geometry("res://assets/baseline-site-v7.pack.gz"if visual_v7 else"res://assets/v10/base-site.pack.zst")
  geo.surfaces.merge(ctx.surfaces)
  for key:String in ctx.colliders:
   if geo.colliders.has(key):geo.colliders[key].append_array(ctx.colliders[key])
   else:geo.colliders[key]=ctx.colliders[key]
 
 if not visual_v7:
  var dress:Dictionary=load_geometry("res://assets/v10/fitout.pack.zst")
  geo.surfaces.merge(dress.surfaces)
  for k:String in dress.colliders:
   if geo.colliders.has(k):geo.colliders[k].append_array(dress.colliders[k])
   else:geo.colliders[k]=dress.colliders[k]
 if not visual_v7:
  var art:Dictionary=load_geometry("res://assets/v10/art.pack.zst")
  geo.surfaces.merge(art.surfaces)
  for k:String in art.colliders:
   if geo.colliders.has(k):geo.colliders[k].append_array(art.colliders[k])
   else:geo.colliders[k]=art.colliders[k]
 if not visual_v7:
  var extra:Dictionary=load_geometry("res://assets/v10/architecture.pack.zst");geo.surfaces.merge(extra.surfaces)
  for k:String in extra.colliders:
   if geo.colliders.has(k):geo.colliders[k].append_array(extra.colliders[k])
   else:geo.colliders[k]=extra.colliders[k]
 if not visual_v7:
  var repaired:Dictionary=load_geometry("res://assets/v11/repairs.pack.zst");geo.surfaces.merge(repaired.surfaces)
  for k:String in repaired.colliders:
   if geo.colliders.has(k):geo.colliders[k].append_array(repaired.colliders[k])
   else:geo.colliders[k]=repaired.colliders[k]
 for extra_path:String in["res://assets/v12/es-safety.pack.zst","res://assets/v12/retail.pack.zst","res://assets/v12/boundary-physics.pack.zst","res://assets/v12/es-unbuilt-safety.pack.zst","res://assets/v12/es-landing-plates.pack.zst"]:
  if FileAccess.file_exists(extra_path):
   var patched:Dictionary=load_geometry(extra_path);geo.surfaces.merge(patched.surfaces)
   for k:String in patched.colliders:
    if geo.colliders.has(k):geo.colliders[k].append_array(patched.colliders[k])
    else:geo.colliders[k]=patched.colliders[k]

 var amenity_geometry:Dictionary=load_geometry("res://assets/v13/amenities.pack.zst");var public_finish:Dictionary=load_geometry("res://assets/v13/public-areas.pack.zst");var basement_geometry:Dictionary=load_geometry("res://assets/v13/basement-retail.pack.zst");var roof_geometry:Dictionary=load_geometry("res://assets/v13/roof-retail.pack.zst");basement_geometry.surfaces.merge(roof_geometry.surfaces)
 for mat:String in roof_geometry.colliders:
  if basement_geometry.colliders.has(mat):basement_geometry.colliders[mat].append_array(roof_geometry.colliders[mat])
  else:basement_geometry.colliders[mat]=roof_geometry.colliders[mat]
 public_finish.surfaces.merge(basement_geometry.surfaces)
 for mat:String in basement_geometry.colliders:
  if public_finish.colliders.has(mat):public_finish.colliders[mat].append_array(basement_geometry.colliders[mat])
  else:public_finish.colliders[mat]=basement_geometry.colliders[mat]
 amenity_geometry.surfaces.merge(public_finish.surfaces)
 for material_key:String in public_finish.colliders:
  if amenity_geometry.colliders.has(material_key):amenity_geometry.colliders[material_key].append_array(public_finish.colliders[material_key])
  else:amenity_geometry.colliders[material_key]=public_finish.colliders[material_key]
 geo.surfaces.merge(amenity_geometry.surfaces)
 for key:String in amenity_geometry.colliders:
  if geo.colliders.has(key):geo.colliders[key].append_array(amenity_geometry.colliders[key])
  else:geo.colliders[key]=amenity_geometry.colliders[key]
 if c_open_proposal or es_site_proposal:
  var patch_path:String="res://assets/v15/C-finish-replacement.pack.zst"if c_open_proposal else"res://assets/v15/ES-site-replacement.pack.zst"
  var patch_info:Dictionary=read_json("res://source/v15/C-finish-audit.json"if c_open_proposal else"res://source/v15/ES-site-proposal.json")
  for erased:String in patch_info.erase_surfaces:geo.surfaces.erase(erased)
  var coordinated_patch:Dictionary=load_geometry(patch_path)
  geo.surfaces.merge(coordinated_patch.surfaces,true)
  # Replace each changed aggregate material layer; retain proven-identical layers from normal geometry.
  geo.colliders.merge(coordinated_patch.colliders,true)
 var service_bays:Dictionary=load_geometry("res://assets/v15/retail-services.pack.zst")
 for bay_mat:String in service_bays.colliders:
  if geo.colliders.has(bay_mat):geo.colliders[bay_mat].append_array(service_bays.colliders[bay_mat])
  else:geo.colliders[bay_mat]=service_bays.colliders[bay_mat]
 var retirement_audit:Dictionary=load("res://retail_reconcile_v21.gd").reconcile(geo,retail_v18_plan);write_json("v18-retired-retail.json",retirement_audit)
 var v17_elevations:Dictionary=load_geometry("res://assets/v17/elevations.pack.zst");geo.surfaces.merge(v17_elevations.surfaces)
 var landscape_audit:Dictionary=load("res://commons_v16.gd").reconcile_legacy_landscape(geo,read_json("res://source/v16/commons.json"));write_json("v16-legacy-landscape-cleanup.json",landscape_audit)
 for key:String in geo.surfaces:
  var material_key:String=key.split("@@")[0]
  var room_key:String=key.split("@@")[-1]
  if room_key=="SITE-TERRAIN"and material_key=="soil":material_key="v10_groundcover"
  if room_key.begins_with("C")and room_key.contains("F-")and material_key in["plaster","wall_sand","wall_chalk","wall_sage","wall_taupe"]:
   material_key="v10_brickwall"if "-CW-"in room_key or"-CNW-"in room_key else"v10_clay"if"-CSW-"in room_key else"v10_sage"if"-CNE-"in room_key else"v10_chalk"

  if material_key=="glass"and(room_key.begins_with("V11-WALL-")or room_key.split("-")[0]in["B1","B2","B3"]or((room_key.begins_with("A")or room_key.begins_with("C"))and room_key.contains("F-"))):material_key="v10_glass"
  var data:Dictionary=geo.surfaces[key];var a:Array=[];a.resize(Mesh.ARRAY_MAX)
  var vs=PackedVector3Array();var ns=PackedVector3Array();var uvs=PackedVector2Array();var cs=PackedColorArray()
  for i in range(0,data.v.size(),3):vs.append(Vector3(data.v[i],data.v[i+1],data.v[i+2]));ns.append(Vector3(data.n[i],data.n[i+1],data.n[i+2]))
  for i in range(0,data.uv.size(),2):uvs.append(Vector2(data.uv[i],data.uv[i+1]))
  for i in range(0,data.c.size(),4):cs.append(Color(data.c[i],data.c[i+1],data.c[i+2],data.c[i+3]))
  a[Mesh.ARRAY_VERTEX]=vs;a[Mesh.ARRAY_NORMAL]=ns;a[Mesh.ARRAY_TEX_UV]=uvs;a[Mesh.ARRAY_COLOR]=cs
  if data.has("i"):a[Mesh.ARRAY_INDEX]=data.i
  var mesh=ArrayMesh.new();mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,a);mesh.surface_set_material(0,mats.step_support if material_key=="step"else mats[material_key])
  if (mats[material_key] is ShaderMaterial and material_key not in["glass","roof_glass"])or material_key=="v12_landing_plate":
   var st=SurfaceTool.new();st.create_from(mesh,0);st.generate_tangents();mesh=st.commit();mesh.surface_set_material(0,mats.step_support if material_key=="step"else mats[material_key])
  var instance=MeshInstance3D.new();instance.mesh=mesh;instance.name="Architecture_"+key;instance.gi_mode=GeometryInstance3D.GI_MODE_STATIC
  var room_group:String=key.split("@@")[-1]
  if room_group.begins_with("B"):
   var room_index:int=0
   for si in range(manifest.shops.size()):
    if manifest.shops[si].id==room_group:room_index=si;break
   instance.layers=1|(1<<((room_index%18)+1))
  if material_key in ["glass","roof_glass","light","v10_glass","v10_guard_glass","v10_emitter"]:instance.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;instance.gi_mode=GeometryInstance3D.GI_MODE_DISABLED
  if material_key=="yellow"and room_group.begins_with("ARCH"):instance.visible=false
  if not visual_v7 and (material_key.begins_with("v8_")or material_key.begins_with("v9_")):
   instance.visibility_range_end=155.0;instance.visibility_range_end_margin=20.0
  add_child(instance);mesh_count+=1
 for key:String in geo.colliders:
  var data=geo.colliders[key];var points=PackedVector3Array()
  for i in range(0,data.size(),3):points.append(Vector3(data[i],data[i+1],data[i+2]))
  var body=StaticBody3D.new();body.name="Collision_"+key;body.collision_layer=3 if key in ["plaster","wall_sand","wall_sage","wall_chalk","wall_taupe","dark_stone"]else 1
  var col=CollisionShape3D.new();var shape=ConcavePolygonShape3D.new();shape.backface_collision=true;shape.set_faces(points);col.shape=shape;body.add_child(col);add_child(body)
 for sign_data:Dictionary in geo.signs:build_sign(sign_data)
 var sm=read_json("res://source/site-manifest-v7.json")
 manifest.staff_doors.append_array(sm.staff_doors)
 manifest.escalators.append_array(sm.escalators)
 if es_site_proposal:
  var site_es:Dictionary=read_json("res://source/v15/ES-site-proposal.json")
  manifest.escalators=manifest.escalators.filter(func(e):return not str(e.id)in site_es.retired_machine_ids)
  manifest.escalators.append_array(site_es.escalators)
 for sd:Dictionary in sm.signs:add_vector_sign(sd)
 for brand:Dictionary in read_json("res://source/brands-v7.json"if visual_v7 else"res://source/v17/brands.json"):
  brand_registry[brand.store_id]=brand
  if visual_v7:add_brand_slot(brand)
 if not visual_v7:
  for sd:Dictionary in fitout.signs:
   if str(sd.id).contains("-wall-art"):build_store_sign(sd)
  for d:Dictionary in fitout.lights:
   var l=SpotLight3D.new();l.position=v3(d.p);l.rotation_degrees.x=-90;l.light_color=Color(1,.85,.66)if d.warm else Color(1,.95,.84);l.light_energy=float(d.energy);l.spot_range=float(d.range);l.spot_angle=65;l.spot_attenuation=1.1;l.distance_fade_enabled=true;l.distance_fade_begin=50;l.distance_fade_length=20;add_child(l)
 # v6 scope-boundary markers removed: full A/C destinations now generated.
 
 # Low, local fixtures on three levels, after spatially grouping storefronts.
 for i in range(geo.lights.size()):
  var d:Dictionary=geo.lights[i]
  if d.get("type","")=="common" and i%8!=0:continue
  var light:SpotLight3D=SpotLight3D.new();light.position=v3(d.p);light.rotation_degrees.x=-90;light.light_color=Color(1,.91,.78)if d.get("type","")=="shop"else Color(1,.97,.89);light.light_energy=float(d.get("energy",.3));light.spot_range=8;light.spot_angle=62;light.spot_attenuation=1.2;light.shadow_enabled=false
  if d.get("type","")=="shop":light.light_cull_mask=1<<(int(d.get("room_index",0))%18+1)
  if not visual_v7:light.distance_fade_enabled=true;light.distance_fade_begin=55;light.distance_fade_length=20
  add_child(light)
 if not visual_v7:
  var furnishings=load("res://retail_v10.gd").new();add_child(furnishings);furnishings.setup(self,art_v10)
  var specialist=load("res://retail_v10.gd").new();add_child(specialist);specialist.setup(self,read_json("res://source/v15/retail-services.json"))
 if not visual_v7:
  var pendants=load("res://pendants_v11.gd").new();add_child(pendants);pendants.setup(self)
 if not visual_v7:
  for d:Dictionary in read_json("res://source/ceiling-lights-v8.json"):
   var light=OmniLight3D.new();light.position=v3(d.position);light.omni_range=9;light.omni_attenuation=1.3;light.light_color=Color(1,.93,.80);light.light_energy=2.3;light.shadow_enabled=false;light.distance_fade_enabled=true;light.distance_fade_begin=35;light.distance_fade_length=15;add_child(light)
 manifest.staff_doors.append_array(read_json("res://source/v13/amenities.json").doors)
 staff=load("res://staff_doors.gd").new();add_child(staff);staff.setup(manifest.get("staff_doors",[]),mats)
 animator=load("res://escalator_v2.gd").new();add_child(animator);animator.setup(manifest,mats)
 if mode!="interactive":animator.paused=true;animator.set_time(1.75)
 if visual_v7 and mode not in["walk-test","walk-v8","ui-test","bake-gi"]:
  var probe=ReflectionProbe.new();probe.name="Atrium_Box_Reflection";probe.position=Vector3(0,7,3);probe.size=Vector3(82,19,105);probe.interior=false;probe.box_projection=true;probe.intensity=.6;probe.max_distance=100;probe.enable_shadows=false;probe.ambient_mode=0;probe.update_mode=0;add_child(probe)
 player=load("res://player.gd").new();player.name="WalkCapsule";add_child(player);player.position=Vector3(325.43976,.06,-63.75212)if not visual_v7 else Vector3(-3,.06,22.3)
 if not visual_v7:interactive_pose(read_json("res://source/cameras-v8.json")[4 if c_open_proposal else 0])
 if es_site_proposal:player.position=Vector3(-202,0.06,-15.5)
 for e:Dictionary in manifest.escalators:
  if not e.has("low_y"):
   e.low_y=manifest.floors[int(e.levels[0])].height;e.high_y=manifest.floors[int(e.levels[1])].height
  player.escalators.append(e)
 elevators=load("res://elevators_v11.gd").new();add_child(elevators);elevators.setup(read_json("res://source/elevators-v7.json"),player,mats,font)
 ui=load("res://ui_v7.gd").new();add_child(ui);ui.setup(self)
 var amenity_finish=load("res://amenities_v13.gd").new();add_child(amenity_finish);amenity_finish.setup(self)
 var roof_beds=load("res://roof_finish_v14.gd").new();add_child(roof_beds);roof_beds.setup(self)
 var landscape=load("res://retail_v10.gd").new();add_child(landscape);landscape.name="V14_Existing_Roof_Beds";landscape.setup(self,{"instances":read_json("res://source/v14/roof-planting.json").instances,"signs":[],"lights":[]})
 commons_v16=load("res://commons_v16.gd").new();add_child(commons_v16);commons_v16.setup(self)
 scenery_v17=load("res://scenery_v17.gd").new();add_child(scenery_v17);scenery_v17.setup(self)
 retail_v18=load("res://retail_v19.gd").new();add_child(retail_v18);retail_v18.setup(self)
 var programme_v21=load("res://retail_v21.gd").new();add_child(programme_v21);programme_v21.setup(self)
 var wayfinding_v21=load("res://wayfinding_v21.gd").new();add_child(wayfinding_v21);wayfinding_v21.setup(self)
 shoppers_v18=load("res://shoppers_v20.gd").new();add_child(shoppers_v18);shoppers_v18.setup(self)
 if mode=="interactive":
  for shot:Dictionary in read_json("res://source/v15/compare-cameras.json"):
   if str(shot.id)==("C-yard-open-sky"if c_open_proposal else"ES-west-site"if es_site_proposal else"01-A-plaza"):interactive_pose(shot);break
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--resolution="):
   var val=arg.trim_prefix("--resolution=");ui.settings.resolution_index=1 if val=="1440" else 2 if val=="2160" else 0;ui.settings.apply(false)
 if draft:get_viewport().scaling_3d_scale=.5
 if not visual_v7:build_unbuilt_signs()
 var layer=CanvasLayer.new();add_child(layer)
 hud=Label.new();hud.add_theme_font_override("font",font);hud.add_theme_font_size_override("font_size",17);hud.position=Vector2(22,16);hud.add_theme_color_override("font_outline_color",Color(.08,.1,.09,.85));hud.add_theme_constant_override("outline_size",5);layer.add_child(hud)
 var bottom=Label.new();bottom.add_theme_font_override("font",font);bottom.add_theme_font_size_override("font_size",14);bottom.position=Vector2(22,1015);bottom.text=("C館 構造別案・未承認 | "if c_open_proposal else"B館西ES 敷地別案・未承認 | "if es_site_proposal else"")+"v21 店舗・誘導検証 | WASD 移動 / Shift 速歩 / F 扉・EV / M マップ / N 人物比較 / P 表情 / F12 NPC / Esc カーソル\nF1 A / F2 B / F3 C | F4 C館別案・未承認 / F6 B館ES別案・未承認 / F7 ES検討 / F8 店舗 / F9 確認地点 / F10 設定 / F11 催事";layer.add_child(bottom)
 if not visual_v7 and bool(ProjectSettings.get_setting("rendering/quality/v14_local_probe_reflections",false))and mode not in ["walk-test","walk-v8","ui-test","bake-gi"]:
  for d in [[Vector3(350,3,-32),Vector3(110,12,110)],[Vector3(0,3,8),Vector3(110,12,110)]]:
   var probe=ReflectionProbe.new();probe.position=d[0];probe.size=d[1];probe.interior=true;probe.box_projection=true;probe.max_distance=60;probe.intensity=.7;probe.enable_shadows=false;probe.update_mode=ReflectionProbe.UPDATE_ONCE;probe.ambient_mode=ReflectionProbe.AMBIENT_DISABLED;add_child(probe)
 if not visual_v7:
  var gi=load("res://lighting_v10.gd").new();add_child(gi);gi.setup(self,mode=="bake-gi")
  if mode=="bake-gi":get_tree().quit();return
 if mode!="interactive":player.input_enabled=false
 results={"godot_version":Engine.get_version_info(),"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"resolution":[1920,1080],"msaa":"4x","source_sha256":manifest.source_original_sha256,"context_included":with_context,"context_geometry_sha256":FileAccess.get_sha256("res://assets/baseline-site-v7.pack.gz"if visual_v7 else"res://assets/v10/base-site.pack.zst"),"main_game_loaded":false,"graphics_revision":"v7-preserved-baseline"if visual_v7 else"v21-independent-retail-and-wayfinding","animation_shader_sha256":FileAccess.get_sha256("res://rubber.gdshader"),"staff_script_sha256":FileAccess.get_sha256("res://staff_doors.gd"),"animation_script_sha256":FileAccess.get_sha256("res://escalator_v2.gd"),"proposal_C":c_open_proposal,"draft":draft,"render_scale":.5 if draft else 1.0,"retail_v10_sha256":FileAccess.get_sha256("res://source/v12/scene-art.json"),"architecture_v10_sha256":FileAccess.get_sha256("res://assets/v10/architecture.pack.zst"),"art_v10_sha256":FileAccess.get_sha256("res://assets/v10/art.pack.zst"),"fitout_sha256":""if visual_v7 else FileAccess.get_sha256("res://assets/v10/fitout.pack.zst"),"geometry_sha256":FileAccess.get_sha256(geometry_path),"main_script_sha256":FileAccess.get_sha256("res://main.gd"),"player_script_sha256":FileAccess.get_sha256("res://player.gd"),"scene_build_seconds":(Time.get_ticks_usec()-start_usec)/1000000.0}
 results.proposal_ES=es_site_proposal;results.v15_C_patch_sha256=FileAccess.get_sha256("res://assets/v15/C-finish-replacement.pack.zst");results.v15_ES_patch_sha256=FileAccess.get_sha256("res://assets/v15/ES-site-replacement.pack.zst");results.v15_services_sha256=FileAccess.get_sha256("res://assets/v15/retail-services.pack.zst");results.C_supported_finish_sha256=FileAccess.get_sha256("res://assets/v15/C-finish-replacement.pack.zst")if c_open_proposal else"";results.es_unbuilt_v12_sha256=FileAccess.get_sha256("res://assets/v12/es-unbuilt-safety.pack.zst");results.es_safety_v12_sha256=FileAccess.get_sha256("res://assets/v12/es-safety.pack.zst");results.boundary_v12_sha256=FileAccess.get_sha256("res://assets/v12/boundary-physics.pack.zst");results.retail_v12_sha256=FileAccess.get_sha256("res://assets/v12/retail.pack.zst");results.repairs_v11_sha256=FileAccess.get_sha256("res://assets/v11/repairs.pack.zst");results.EV_v11_sha256=FileAccess.get_sha256("res://elevators_v11.gd");results.map_v12_sha256=data_hash("res://source/v12/map-data-C-option.json"if c_open_proposal else"res://source/v12/map-data.json")
 results.map_v13_sha256=data_hash("res://source/v15/map-data-C-option.json"if c_open_proposal else"res://source/v15/map-data-ES-option.json"if es_site_proposal else"res://source/v13/map-data.json")
 results.v13_packs={}
 for item:String in ["amenities","public-areas","basement-retail","roof-retail"]:results.v13_packs[item]=FileAccess.get_sha256("res://assets/v13/"+item+".pack.zst")
 results.amenity_instances_v13_sha256=FileAccess.get_sha256("res://source/v13/amenities-public.json");results.basement_instances_v13_sha256=FileAccess.get_sha256("res://source/v13/basement-retail.json");results.roof_instances_v13_sha256=FileAccess.get_sha256("res://source/v13/roof-retail.json")
 results.v14_gi_cache_sha256=FileAccess.get_sha256("res://source/v14/gi-cache.json")if FileAccess.file_exists("res://source/v14/gi-cache.json")else "not-baked-for-current-materials"
 results.v14_surface_sha256=FileAccess.get_sha256("res://surface_v14.gdshader");results.v14_finish_sha256=FileAccess.get_sha256("res://finish_v14.gd");results.v14_model_bounds_sha256=FileAccess.get_sha256("res://source/v14/asset-bounds.json");results.v14_roof_sha256=FileAccess.get_sha256("res://source/v14/roof-planting.json")
 print("VALIDATION_READY ",JSON.stringify(results))
 await get_tree().physics_frame;await get_tree().physics_frame
 if mode=="capture":await load("res://showcase_v10.gd").new().capture(self)
 if mode=="benchmark-v8":await load("res://showcase_v10.gd").new().benchmark(self)
 if mode=="walk-v8":await load("res://showcase_v10.gd").new().walk(self)
 if mode=="walk-test":await load("res://validation_v7.gd").new().walk(self)
 if mode=="vehicle-test":await load("res://validation_v7.gd").new().vehicle(self)
 if mode=="ui-test":await load("res://validation_v7.gd").new().ui_test(self)
 
func _process(dt:float)->void:
 if player==null or hud==null:return
 hud.text="FIND YOURSELF  アニメ調人物検証 v20\n位置 %.1f / %.2f / %.1f m   FPS %.1f\n%s"%[player.position.x,player.position.y,player.position.z,Engine.get_frames_per_second(),"ESCALATOR "+player.belt_id if player.belt_id!="" else ""]
 if notice_seconds>0:
  notice_seconds-=dt;hud.text+="\n"+interaction_notice
 if mode=="interactive" and ui.overlay=="":
  if Input.is_physical_key_pressed(KEY_1):player.position=Vector3(-3,.08,28.3)
  if Input.is_physical_key_pressed(KEY_2):player.position=Vector3(-3,5.605,28.3)
  if Input.is_physical_key_pressed(KEY_3):player.position=Vector3(-3,10.955,28.3)
  if Input.is_physical_key_pressed(KEY_4):player.position=Vector3(-118.99913,16.48,63.99970)
  if Input.is_physical_key_pressed(KEY_B):player.position=Vector3(-111.00000,-5.27,-40.00000)
func build_environment()->void:
 var world=WorldEnvironment.new();var env=Environment.new();world.environment=env
 env.background_mode=Environment.BG_SKY
 var sky=Sky.new();var sky_mat=ProceduralSkyMaterial.new();sky_mat.sky_top_color=Color(.25,.46,.74);sky_mat.sky_horizon_color=Color(.81,.88,.93);sky_mat.ground_bottom_color=Color(.14,.13,.11);sky_mat.ground_horizon_color=Color(.45,.45,.42);sky.sky_material=sky_mat;env.sky=sky
 env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;env.ambient_light_color=Color(.88,.89,.88);env.ambient_light_energy=.70;env.reflected_light_source=2
 env.tonemap_mode=Environment.TONE_MAPPER_FILMIC;env.tonemap_exposure=.90
 if not visual_v7:
  env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;env.ambient_light_color=Color(.94,.94,.90);env.ambient_light_energy=.40;env.ambient_light_sky_contribution=.25;env.reflected_light_source=Environment.REFLECTION_SOURCE_SKY;env.tonemap_mode=Environment.TONE_MAPPER_ACES;env.tonemap_exposure=.95;env.tonemap_white=5.0;env.ssao_enabled=true;env.ssao_radius=1.4;env.ssao_intensity=1.5;env.ssil_enabled=true;env.ssil_intensity=.45;env.ssr_enabled=true;env.glow_enabled=true;env.glow_intensity=.18
 add_child(world)
 var sun=DirectionalLight3D.new();sun.name="Daylight";sun.rotation_degrees=Vector3(-58,-32,0);sun.light_energy=.12;sun.light_color=Color(1,.98,.93);sun.shadow_enabled=true;sun.directional_shadow_max_distance=95;sun.shadow_bias=.12;sun.shadow_normal_bias=1.2;sun.directional_shadow_mode=DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS;add_child(sun)
 if not visual_v7:sun.light_energy=1.10;sun.light_color=Color(1,.96,.88);sun.shadow_bias=.018;sun.shadow_normal_bias=.12
 var fill=DirectionalLight3D.new();fill.rotation_degrees=Vector3(-30,140,0);fill.light_color=Color(.72,.82,1);fill.sky_mode=DirectionalLight3D.SKY_MODE_LIGHT_ONLY;fill.light_energy=.08;fill.shadow_enabled=false;add_child(fill)
func plain(color:Color,rough:float=.5,metal:float=0)->StandardMaterial3D:
 var m=StandardMaterial3D.new();m.albedo_color=color;m.roughness=rough;m.metallic=metal;m.vertex_color_use_as_albedo=true;m.cull_mode=BaseMaterial3D.CULL_DISABLED;m.texture_filter=BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC;return m
func build_materials()->void:
 mats=load("res://material_library.gd").new().build(baseline)
func old_sign_hidden(d:Dictionary)->bool:
 for pp:Array in art_v10.get("hidden_sign_positions",[]):
  if v3(d.p).distance_to(v3(pp))<2.5:return true
 if visual_v7 or fitout.is_empty():return false
 for sd:Dictionary in fitout.signs:
  if str(sd.id).ends_with("-window"):continue
  if v3(d.p).distance_to(v3(sd.p))<1.5:return true
 return false
func build_sign(d:Dictionary)->void:
 if not str(d.file).begins_with("v8/")and old_sign_hidden(d):return
 var mesh=QuadMesh.new();mesh.size=Vector2(d.w,d.h)
 var m=plain(Color.WHITE,.6);m.albedo_texture=load("res://assets/"+d.file);m.emission_enabled=true;m.emission=m.albedo_color;m.emission_texture=m.albedo_texture;m.emission_energy_multiplier=.12;mesh.material=m
 var n=MeshInstance3D.new();n.mesh=mesh;n.position=v3(d.p)
 var dir=Vector3(d.n[0],0,d.n[1]);n.basis=Basis(Vector3.UP.cross(dir),Vector3.UP,dir);add_child(n)
func write_json(name:String,data)->void:
 var file=FileAccess.open(output+"/"+name,FileAccess.WRITE);file.store_string(JSON.stringify(data,"  "))
func _unhandled_input(e:InputEvent)->void:
 if e is InputEventKey and e.pressed and e.keycode==KEY_F7:get_tree().change_scene_to_file("res://ES_transfer_study_v12.tscn");return
 if e is InputEventKey and e.pressed and e.keycode==KEY_F and ui.overlay=="":
  var index=elevators.nearest()
  if index>=0:
   if elevators.is_inside(index):ui.show_lift(index)
   else:
    var stop=elevators.landing_stop(index)
    if stop>=0:
     elevators.call_to(index,stop);interaction_notice="乗車してFキーで行先を選択"if elevators.records[index].state=="open"and int(elevators.records[index].current)==stop else"エレベーターを呼びました。扉が開くまでお待ちください。";notice_seconds=4.0
   return
  if staff.interact(player.position,player.get_rid()):return
func collision_diagnostics()->Array:
 var a:Array=[]
 for i in range(player.get_slide_collision_count()):
  var c=player.get_slide_collision(i);a.append({"collider":str(c.get_collider().name),"normal":str(c.get_normal()),"position":str(c.get_position())})
 return a
func add_scope_markers()->void:
 for d:Dictionary in read_json("res://source/preview-markers.json"):
  var root=Node3D.new();root.position=v3(d.position);var normal=Vector3(d.normal[0],0,d.normal[1]);root.basis=Basis(Vector3.UP.cross(normal),Vector3.UP,normal);add_child(root)
  var mesh=QuadMesh.new();mesh.size=Vector2(d.width,.85);var m=StandardMaterial3D.new();m.albedo_color=Color(.055,.14,.12);m.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;m.cull_mode=BaseMaterial3D.CULL_DISABLED;mesh.material=m;var board=MeshInstance3D.new();board.mesh=mesh;root.add_child(board)
  var label=Label3D.new();label.font=font;label.text=d.text;label.font_size=56;label.pixel_size=.0028;label.outline_size=0;label.modulate=Color.WHITE;label.position.z=.012;root.add_child(label)
func settle(p:Vector3)->void:
 player.auto_active=false;player.velocity=Vector3.ZERO;player.position=p+Vector3(0,.06,0)
 for i in range(14):await get_tree().physics_frame
func walk_points(points:Array,speed:float=5.0)->Dictionary:
 var max_error:float=0;var ticks:int=0;var contacts:int=0;var checkpoints:Array=[]
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
   if player.position.y<min(start.y,target.y)-1.5:return {"pass":false,"reason":"fell below floor","position":player.position,"target":target,"ticks":ticks,"colliders":collision_diagnostics()}
  if not reached:
   player.auto_active=false
   return {"pass":false,"reason":"not reached within physical tick budget","position":player.position,"target":target,"ticks":ticks,"colliders":collision_diagnostics()}
  checkpoints.append({"position":[player.position.x,player.position.y,player.position.z],"on_floor":player.is_on_floor()})
 player.auto_active=false
 return {"checkpoints":checkpoints,"pass":true,"ticks":ticks,"contact_ticks":contacts,"max_vertical_difference_m":max_error,"position":player.position}

func add_vector_sign(d:Dictionary)->void:
 if old_sign_hidden(d):return
 var n=Label3D.new();n.font=font;n.text=d.text;n.font_size=38;n.pixel_size=min(.009,float(d.w)/max(font.get_string_size(str(d.text),HORIZONTAL_ALIGNMENT_LEFT,-1,38).x,1.));n.outline_size=4;n.modulate=Color(.2,.30,.28);n.position=v3(d.p);var normal=Vector3(d.n[0],0,d.n[1]);n.basis=Basis(Vector3.UP.cross(normal),Vector3.UP,normal);add_child(n)
func _input(e:InputEvent)->void:
 if ui==null or mode!="interactive":return
 if e is InputEventKey and e.pressed and not e.echo and e.keycode==KEY_F6:
  get_tree().change_scene_to_file("res://main.tscn"if es_site_proposal else"res://ES_site_proposal_v15.tscn");return
 if e is InputEventKey and e.pressed and not e.echo and e.keycode==KEY_F4:
  get_tree().change_scene_to_file("res://main.tscn"if c_open_proposal else"res://C_proposal_v12.tscn");return
 if e is InputEventKey and e.pressed and not e.echo and ui.overlay=="":
  if e.keycode in [KEY_F1,KEY_F2,KEY_F3]:
   var idx=int(e.keycode)-int(KEY_F1);var shots=read_json("res://source/cameras-v8.json");var shot=shots[[0,2,4][idx]];interactive_pose(shot);get_viewport().set_input_as_handled();return
 if e is InputEventKey and e.pressed and not e.echo:
  if e.keycode==KEY_M:ui.show_map();get_viewport().set_input_as_handled()
  elif e.keycode==KEY_F10:ui.show_settings();get_viewport().set_input_as_handled()
  elif e.keycode==KEY_F8:ui.show_pilots();get_viewport().set_input_as_handled()
  elif e.keycode==KEY_F9:ui.show_amenities();get_viewport().set_input_as_handled()
  elif e.keycode==KEY_ESCAPE and ui.overlay!="":ui.close();get_viewport().set_input_as_handled()

func add_brand_slot(d:Dictionary)->void:
 var slot=Node3D.new();slot.name="BrandSlot_"+d.store_id;slot.position=v3(d.sign_position);slot.set_meta("brand",d);add_child(slot)
 if not visual_v7:return
 # Final sign work is deferred. A per-ID asset activates immediately when supplied; no global duplicated brand texture.
 if d.get("logo_asset")!=null and FileAccess.file_exists("res://assets/"+str(d.logo_asset)):
  build_sign({"file":d.logo_asset,"p":d.sign_position,"n":d.normal,"w":d.max_width_m,"h":.75})
 elif d.get("show_provisional_name",false):
  add_vector_sign({"text":d.name,"p":d.sign_position,"n":d.normal,"w":d.max_width_m,"h":.65})

func interactive_pose(shot:Dictionary)->void:
 var eye=v3(shot.eye);var direction=v3(shot.look)-eye
 player.position=eye-Vector3(0,1.65,0);player.velocity=Vector3.ZERO;player.auto_active=false
 player.rotation=Vector3(0,atan2(-direction.x,-direction.z),0)
 player.camera.rotation=Vector3(atan2(direction.y,Vector2(direction.x,direction.z).length()),0,0)
 player.reset_physics_interpolation()

func build_store_sign(data:Dictionary)->void:
 var sign_data=data.duplicate(true)
 var id:String=str(sign_data.get("id",""))
 if brand_registry.has(id):
  var brand:Dictionary=brand_registry[id]
  if brand.get("logo_asset")!=null:sign_data.file=str(brand.logo_asset)
  var placement:Dictionary=brand.get("sign_override",{})
  for key:String in ["p","n","w","h"]:
   if placement.has(key):sign_data[key]=placement[key]
  if not FileAccess.file_exists("res://assets/"+str(sign_data.file)):
   add_vector_sign({"text":str(brand.name),"p":sign_data.p,"n":sign_data.n,"w":sign_data.w});return
 build_sign(sign_data)

func build_unbuilt_signs()->void:
 for d:Dictionary in read_json("res://source/v12/es-unbuilt-signs.json"):
  var holder=Node3D.new();holder.position=v3(d.p);var normal=Vector3(d.n[0],0,d.n[1]);holder.basis=Basis(Vector3.UP.cross(normal),Vector3.UP,normal);add_child(holder)
  var face=MeshInstance3D.new();var board=BoxMesh.new();board.size=Vector3(1.95,.56,.045);board.material=plain(Color(.04,.12,.15),.6);face.mesh=board;holder.add_child(face)
  for x:float in[-.74,.74]:
   var post=MeshInstance3D.new();var tube=BoxMesh.new();tube.size=Vector3(.045,1.75,.045);tube.material=plain(Color(.28,.31,.32),.35,.65);post.mesh=tube;post.position=Vector3(x,-.625,-.035);holder.add_child(post)
  var text=Label3D.new();text.font=font;text.text=d.text;text.font_size=32;text.pixel_size=.0037;text.position.z=.026;text.outline_size=0;text.modulate=Color(.95,.96,.92);text.double_sided=false;holder.add_child(text)
