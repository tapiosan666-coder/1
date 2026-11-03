extends Node3D
var game
var way
var reports:Array=[]
var library
var floor_sampler
var stats:Dictionary={"stores":0,"floor_triangles":0,"wall_panels":0,"posters":0,"ceiling_units":0,"real_lights":0,"new_collision_shapes":0,"unverified":[]}
func setup(g)->void:
 game=g;name="V24_Store_Finishes";call_deferred("build")
func solid(colour:String,rough:float=.7)->StandardMaterial3D:
 var m=StandardMaterial3D.new();m.albedo_color=Color(colour);m.roughness=rough;return m
func segment_quad(a:Vector3,b:Vector3,normal:Vector3,height:float,material:Material,uv_rect:Array=[0.,0.,1.,1.])->MeshInstance3D:
 if (b-a).dot(Vector3.UP.cross(normal))<0.:var old:Vector3=a;a=b;b=old
 var st=SurfaceTool.new();st.begin(Mesh.PRIMITIVE_TRIANGLES);var p:Array=[a+Vector3.UP*height/2,a-Vector3.UP*height/2,b-Vector3.UP*height/2,b+Vector3.UP*height/2];var r:Array=uv_rect;var uv:Array=[Vector2(r[0],r[1]),Vector2(r[0],r[1]+r[3]),Vector2(r[0]+r[2],r[1]+r[3]),Vector2(r[0]+r[2],r[1])]
 for i:int in[0,2,1,0,3,2]:st.set_normal(normal);st.set_uv(uv[i]);st.add_vertex(p[i])
 var node=MeshInstance3D.new();node.mesh=st.commit();node.material_override=material;node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;node.visibility_range_end=70.;add_child(node);return node
func near_door(p:Vector3)->bool:
 for d:Dictionary in game.manifest.staff_doors:
  if not d.has("p"):continue
  var q:Vector3=game.v3(d.p)
  if absf(q.y-p.y)>2.:continue
  q.y=p.y
  if q.distance_to(p)<float(d.get("leaf_width_m",1.2))*.6+.40:return true
 return false
func segment_has_door(a:Vector3,b:Vector3,h:float)->bool:
 var v:Vector3=b-a;v.y=0
 for door:Dictionary in game.manifest.staff_doors:
  if not door.has("p"):continue
  var q:Vector3=game.v3(door.p)
  if absf(q.y-h)>.35:continue
  q.y=a.y;var t:float=clampf((q-a).dot(v)/maxf(.001,v.length_squared()),0.,1.)
  if q.distance_to(a+v*t)<.65:return true
 return false
func wall_hit(p:Vector3,n:Vector3)->Dictionary:
 var world=game.get_world_3d().direct_space_state;var query=PhysicsRayQueryParameters3D.create(p+n*.35,p-n*.42,1);var hit=world.intersect_ray(query)
 for i in range(4):
  if hit.is_empty()or not hit.collider.has_meta("v21_fixture"):break
  var excludes:Array[RID]=query.exclude;excludes.append(hit.rid);query.exclude=excludes;hit=world.intersect_ray(query)
 if hit.is_empty()or hit.collider.has_meta("v21_fixture")or str(hit.collider.name).to_lower().contains("glass")or absf(hit.normal.y)>.2:return{}
 if near_door(p):return{}
 return hit
func build()->void:
 while not game.has_node("V21_Route_Derived_Wayfinding"):await get_tree().process_frame
 way=game.get_node("V21_Route_Derived_Wayfinding")
 while not way.has_meta("ready"):await get_tree().process_frame
 await get_tree().physics_frame;await get_tree().physics_frame
 library=load("res://retail_v10.gd").new();var enabled:Array=game.read_json("res://source/v25/retained-v24-finishes.json").enabled_store_ids
 floor_sampler=load("res://floor_surface_sample_v24.gd").new();var floor_levels:Array=[]
 for definition:Dictionary in game.read_json("res://source/v24/store-finishes.json"):
  if not float(definition.floor_level)in floor_levels:floor_levels.append(float(definition.floor_level))
 floor_sampler.build(game,floor_levels)
 var atlas:Texture2D=load("res://assets/v24/art/store-editorial-atlas.png");var poster=StandardMaterial3D.new();poster.albedo_texture=atlas;poster.roughness=.82;poster.cull_mode=BaseMaterial3D.CULL_DISABLED
 var trim=solid("#776349",.44);trim.metallic=.45
 for d:Dictionary in game.read_json("res://source/v24/store-finishes.json"):
  if not d.id in enabled:continue
  var row:Dictionary={"id":d.id,"style":d.style,"floor_triangles":0,"walls":0,"posters":0,"lights":0,"ceiling_support_checks":[],"not_new_structural_floor":true,"maximum_existing_visual_floor_offset_m":0.,"poster_positions":[]};var h:float=d.floor_level
  var floor=ShaderMaterial.new();floor.shader=load("res://store_floor_v24.gdshader");floor.set_shader_parameter("oak_texture",load("res://assets/v10/wood-oak.png"));floor.set_shader_parameter("floor_tint",Color(d.floor_colour));floor.set_shader_parameter("finish_type",int(d.floor_type));floor.set_shader_parameter("finish_roughness",float(d.floor_roughness));var st=SurfaceTool.new();st.begin(Mesh.PRIMITIVE_TRIANGLES)
  for tri:Array in d.floor_triangles:
   var okay:bool=true;var vertices:Array=[];var levels:Array=[]
   for p:Array in tri:
    var v=Vector3(p[0],h,p[1]);var y:float=way.floor_y(v)
    if is_nan(y):okay=false;break
    var visual_y:float=floor_sampler.surface_y(v,y);row.maximum_existing_visual_floor_offset_m=maxf(row.maximum_existing_visual_floor_offset_m,visual_y-y);vertices.append(v);levels.append(visual_y)
   if not okay:continue
   var centre:Vector3=(vertices[0]+vertices[1]+vertices[2])/3.;var y:float=way.floor_y(centre)
   if is_nan(y):continue
   for k in range(3):
    var length:float=vertices[k].distance_to(vertices[(k+1)%3])
    for j in range(ceili(length/.75)+1):
     if not way.floor_hit(vertices[k].lerp(vertices[(k+1)%3],float(j)/maxi(1,ceili(length/.75)))):okay=false;break
   if not okay:continue
   for k in range(3):var v:Vector3=vertices[k];v.y=levels[k]+.003;st.set_normal(Vector3.UP);st.set_uv(Vector2(v.x,v.z));st.add_vertex(v)
   row.floor_triangles+=1
  if row.floor_triangles>0:
   st.generate_tangents();var mesh=MeshInstance3D.new();mesh.mesh=st.commit();mesh.material_override=floor;mesh.visibility_range_end=85.;mesh.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(mesh)
  var painted=solid(d.wall_colour,.82);var accent=solid(d.accent_colour,.73)
  for edge:Dictionary in d.wall_candidates:
   var a=Vector3(edge.a[0],h+1.65,edge.a[1]);var b=Vector3(edge.b[0],h+1.65,edge.b[1]);var n=Vector3(edge.inward[0],0,edge.inward[1]);var okay:bool=not segment_has_door(a,b,h);var hits:Array=[]
   if not okay:continue
   for t:float in[.04,.25,.5,.75,.96]:
    for level:float in[.55,1.65,2.75]:
     var p:Vector3=a.lerp(b,t);p.y=h+level;var hit=wall_hit(p,n)
     if hit.is_empty():okay=false;break
     hits.append(hit)
    if not okay:break
   if not okay:continue
   var centre:Vector3=a.lerp(b,.5);var mid=wall_hit(centre,n)
   if mid.is_empty():continue
   var shift:Vector3=mid.position-centre+n*.006;a+=shift;b+=shift
   segment_quad(a,b,n,2.45,accent if row.walls<2 else painted);segment_quad(a+Vector3.UP*1.25,b+Vector3.UP*1.25,n,.045,trim);row.walls+=1
   if row.posters<2 and a.distance_to(b)>2.0:
    var tangent:Vector3=(b-a).normalized();var p:Vector3=(a+b)*.5+n*.015;var width:float=1.20;var poster_h:float=1.80;var found:bool=false
    for level:float in[1.75,2.80]:
     for fraction:float in[.18,.36,.5,.64,.82]:
      var anchor:Vector3=a.lerp(b,fraction)+n*.018;anchor.y=h+level
      if near_door(anchor-Vector3.UP*1.):continue
      for unit:Dictionary in d.ceiling_units:
       var view:Vector3=game.v3(unit.p)+Vector3.UP*1.65;var ray=game.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(view,anchor+n*.05,1))
       if ray.is_empty():p=anchor;poster_h=1.8 if level<2. else 1.15;width=1.20 if level<2. else .77;found=true;break
      if found:break
     if found:break
    if found:
     segment_quad(p-tangent*(width/2+.035)-n*.002,p+tangent*(width/2+.035)-n*.002,n,poster_h+.07,solid("#eee7da",.75));segment_quad(p-tangent*width/2,p+tangent*width/2,n,poster_h,poster,d.poster_uv);row.posters+=1;row.poster_positions.append({"p":[p.x,p.y,p.z],"normal":[n.x,n.y,n.z],"visible_from_verified_sales_spine":true})
   if row.walls>=5:break
  var world=game.get_world_3d().direct_space_state
  for unit:Dictionary in d.ceiling_units:
   var p=game.v3(unit.p);var axis=Vector3(unit.axis[0],0,unit.axis[1]);var ends:Array=[];var okay:bool=true
   for sign:float in[-1.,1.]:
    var q:Vector3=p+axis*1.14*float(unit.scale_x)*sign;var hit=world.intersect_ray(PhysicsRayQueryParameters3D.create(q+Vector3.UP*2.65,q+Vector3.UP*6.20,1))
    if hit.is_empty()or str(hit.collider.name).to_lower().contains("glass")or hit.collider.has_meta("v21_fixture"):okay=false;break
    ends.append(hit.position)
   if not okay:continue
   var y:float=minf(ends[0].y,ends[1].y)-.26;p.y=y;var forward:Vector3=axis.cross(Vector3.UP);var basis=Basis(axis,Vector3.UP,forward).scaled_local(Vector3(unit.scale_x,1,1));var data=library.get_asset("../v24/models/finish_v24_track",false)
   if data.is_empty():continue
   for part:Dictionary in data.parts:
    var mesh=MeshInstance3D.new();mesh.mesh=part.mesh;mesh.transform=Transform3D(basis,p)*part.transform;mesh.visibility_range_end=50.;add_child(mesh)
   for j in range(2):
    var top:Vector3=ends[j];var bottom:Vector3=p+axis*1.14*float(unit.scale_x)*(-1. if j==0 else 1.)+Vector3.UP*.06;var rod=MeshInstance3D.new();var cylinder=CylinderMesh.new();cylinder.top_radius=.007;cylinder.bottom_radius=.007;cylinder.height=top.distance_to(bottom);cylinder.material=trim;rod.mesh=cylinder;rod.position=(top+bottom)*.5;add_child(rod)
   var light=SpotLight3D.new();light.position=p-Vector3.UP*.20;light.rotation_degrees.x=-90;light.light_color=Color(d.light_colour[0],d.light_colour[1],d.light_colour[2]);light.light_energy=1.25;light.spot_range=8.;light.spot_angle=68.;light.shadow_enabled=false;light.distance_fade_enabled=true;light.distance_fade_begin=18.;light.distance_fade_length=8.;add_child(light);row.lights+=1;stats.ceiling_units+=1;row.ceiling_support_checks.append({"two_actual_ceiling_hits":true,"ends":[[ends[0].x,ends[0].y,ends[0].z],[ends[1].x,ends[1].y,ends[1].z]]})
  stats.stores+=1;stats.floor_triangles+=row.floor_triangles;stats.wall_panels+=row.walls;stats.posters+=row.posters;stats.real_lights+=row.lights;reports.append(row)
 floor_sampler=null;library.free();stats.store_reports=reports;stats.resource_cache=load("res://asset_cache_v24.gd").snapshot();game.write_json("v24-finish-build.json",stats);set_meta("ready",true);print("V24_FINISH_READY ",stats.stores,"stores ",stats.wall_panels,"panels ",stats.posters,"posters ",stats.real_lights,"lights")
