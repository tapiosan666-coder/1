extends Node3D
# v16: separately authored fit-out. No architectural pack or player controller mutation.
var game
var data:Dictionary
var library
var batches:Dictionary={}
var shapes:Dictionary={}
var groups:Dictionary={}
var fair_enabled:bool=true
var gates:Dictionary={}
var stats:Dictionary={"placements":0,"boards":0,"colliders":0,"batches":0,"missing":[]}
func group_for(key:String)->Node3D:
 if not groups.has(key):
  var n=Node3D.new();n.name=key;add_child(n);groups[key]=n
 return groups[key]
func placement_transform(d:Dictionary)->Transform3D:
 var n=Vector3(d.n[0],0,d.n[1]);var b=Basis(Vector3.UP.cross(n),Vector3.UP,n).scaled_local(Vector3(float(d.get("scale",1))*float(d.get("scale_x",1)),float(d.get("scale",1)),float(d.get("scale",1))))
 return Transform3D(b,game.v3(d.p))
func setup(g)->void:
 game=g;name="V17_Architectural_Composition";data=g.read_json("res://source/v17/scene-design.json");library=load("res://retail_v10.gd").new()
 if g.get("retail_v18_plan")!=null:data.instances=data.instances.filter(func(d):return str(d.get("store_id",""))not in g.retail_v18_plan.replacement_store_ids)
 for d:Dictionary in data.instances:
  if d.activation=="es_option"and not g.es_site_proposal:continue
  var lib:Dictionary=library.get_asset("../v17/models/"+str(d.model),false)
  if lib.is_empty():stats.missing.append(d.id);continue
  if d.model in["shade_sail","fair_food_booth","fair_craft_booth","kids_play_tower"]:
   for part:Dictionary in lib.parts:
    for surface in range(part.mesh.get_surface_count()):
     var material=part.mesh.surface_get_material(surface)
     if material is StandardMaterial3D:material.cull_mode=BaseMaterial3D.CULL_DISABLED
  var t=placement_transform(d);var keybase=str(d.model)+"|"+str(d.activation)+"|%d,%d"%[floor(float(d.p[0])/28),floor(float(d.p[2])/28)]
  for i in range(lib.parts.size()):
   var k=keybase+"|"+str(i)
   if not batches.has(k):batches[k]={"mesh":lib.parts[i].mesh,"transforms":[],"activation":d.activation,"small":d.collision=="none"}
   batches[k].transforms.append(t*lib.parts[i].transform)
  if d.collision!="none":
   var cache=str(d.model)+"|"+str(d.scale)+"|"+str(d.get("scale_x",1))
   if not shapes.has(cache):
    if d.collision=="trunk":
     var cylinder=CylinderShape3D.new();cylinder.radius=.13*float(d.scale);cylinder.height=2.5*float(d.scale);shapes[cache]=cylinder
    else:
     var faces=PackedVector3Array();var scale_basis=Basis.from_scale(Vector3(float(d.scale)*float(d.get("scale_x",1)),float(d.scale),float(d.scale)))
     for part:Dictionary in lib.parts:
      for v:Vector3 in part.mesh.get_faces():faces.append(scale_basis*(part.transform*v))
     var shape=ConcavePolygonShape3D.new();shape.set_faces(faces);shape.backface_collision=true;shapes[cache]=shape
   var body=StaticBody3D.new();body.name=str(d.id).validate_node_name();body.position=t.origin;body.basis=Basis(Vector3.UP.cross(Vector3(d.n[0],0,d.n[1])),Vector3.UP,Vector3(d.n[0],0,d.n[1]));var collision=CollisionShape3D.new();collision.shape=shapes[cache]
   if d.collision=="trunk":collision.position.y=1.25*float(d.scale)
   body.add_child(collision);group_for(d.activation).add_child(body);stats.colliders+=1
  stats.placements+=1
 for key:String in batches:
  var b:Dictionary=batches[key];var mm=MultiMesh.new();mm.transform_format=MultiMesh.TRANSFORM_3D;mm.mesh=b.mesh;mm.instance_count=b.transforms.size()
  for i in range(b.transforms.size()):mm.set_instance_transform(i,b.transforms[i])
  var mesh=MultiMeshInstance3D.new();mesh.multimesh=mm;mesh.gi_mode=GeometryInstance3D.GI_MODE_DISABLED if b.activation=="aichi_fair"else GeometryInstance3D.GI_MODE_STATIC;mesh.visibility_range_end=55 if b.small else 140;mesh.visibility_range_end_margin=12;mesh.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF;group_for(b.activation).add_child(mesh);stats.batches+=1
 var board_batches:Dictionary={}
 for d:Dictionary in data.boards:
  if d.activation=="es_option"and not g.es_site_proposal:continue
  var k=str(d.tile)+"|"+str(d.activation)+"|%d,%d,%d"%[floor(float(d.p[0])/35),floor(float(d.p[1])/5.35),floor(float(d.p[2])/35)]
  if not board_batches.has(k):
   var st=SurfaceTool.new();st.begin(Mesh.PRIMITIVE_TRIANGLES);board_batches[k]={"surface":st,"tile":d.tile,"activation":d.activation}
  var st:SurfaceTool=board_batches[k].surface;var t=placement_transform(d);var r:Array=d.uv if d.get("uv")!=null else[0.,0.,1.,1.]
  var corners:Array=[Vector3(-d.w/2,d.h/2,0),Vector3(-d.w/2,-d.h/2,0),Vector3(d.w/2,-d.h/2,0),Vector3(d.w/2,d.h/2,0)];var uv:Array=[Vector2(r[0],r[1]),Vector2(r[0],r[1]+r[3]),Vector2(r[0]+r[2],r[1]+r[3]),Vector2(r[0]+r[2],r[1])]
  for index:int in[0,1,2,0,2,3]:st.set_normal(t.basis.z);st.set_uv(uv[index]);st.add_vertex(t*corners[index])
  stats.boards+=1
 for k:String in board_batches:
  var d:Dictionary=board_batches[k];var mat=StandardMaterial3D.new();mat.albedo_texture=load("res://assets/v17/signs/"+str(d.tile));mat.roughness=.62;mat.cull_mode=BaseMaterial3D.CULL_DISABLED;mat.emission_enabled=true;mat.emission=Color(.7,.7,.7);mat.emission_energy_multiplier=.16
  var mesh=MeshInstance3D.new();mesh.mesh=d.surface.commit();mesh.material_override=mat;mesh.visibility_range_end=120;group_for(d.activation).add_child(mesh)
 stats.board_draw_batches=board_batches.size()
 for d:Dictionary in data.lights:
  var light=SpotLight3D.new();light.position=game.v3(d.p);light.rotation_degrees.x=-90;light.light_color=Color(d.color[0],d.color[1],d.color[2]);light.light_energy=d.energy;light.spot_range=d.range;light.spot_angle=75;light.shadow_enabled=false;light.distance_fade_enabled=true;light.distance_fade_begin=28;light.distance_fade_length=8;add_child(light)
 library.free()
 print("V17_SCENE ",JSON.stringify(stats));g.write_json("v17-scene-build.json",stats)
func set_fair(enabled:bool)->void:
 fair_enabled=enabled
 if groups.has("aichi_fair"):groups.aichi_fair.visible=enabled
