extends Node3D
var stats:Dictionary={"fixtures":0,"products":0,"batches":0,"colliders":0,"missing":[]}
var game
var library
func setup(g)->void:
 game=g;name="V22_Separate_Fixtures_And_SKUs";var plan:Dictionary=g.read_json("res://source/v24/retail-plan.json");library=load("res://retail_v10.gd").new();var no_packets:bool=not OS.get_cmdline_user_args().has("--v23-stock-packets")or OS.get_cmdline_user_args().has("--v23-original-product-instancing");var batches:Dictionary={};var shape_cache:Dictionary={}
 for d:Dictionary in (plan.instances if no_packets else plan.fixtures):
  var lib:Dictionary=library.get_asset(d.asset,false)
  if lib.is_empty():stats.missing.append(d.id);continue
  var n=Vector3(d.n[0],0,d.n[1]);var basis=Basis(Vector3.UP.cross(n),Vector3.UP,n)
  if d.get("pitch_deg",0.)!=0.:basis=basis*Basis(Vector3.RIGHT,deg_to_rad(float(d.pitch_deg)))
  var t=Transform3D(basis,g.v3(d.p));var product:bool=d.collision=="none";var keybase:String=str(d.model)+"|%d,%d,%d"%[floor(d.p[0]/28.),floor(d.p[1]/5.35),floor(d.p[2]/28.)]
  for i in lib.parts.size():
   var key=keybase+"|"+str(i)
   if not batches.has(key):batches[key]={"mesh":lib.parts[i].mesh,"transforms":[],"product":product}
   batches[key].transforms.append(t*lib.parts[i].transform)
  if product:stats.products+=1
  else:
   stats.fixtures+=1;var body=StaticBody3D.new();body.name=str(d.id).validate_node_name();body.transform=t;body.set_meta("v21_fixture",d);var col=CollisionShape3D.new()
   if d.model not in["legacy_mannequin"]:
    if not shape_cache.has(d.asset):
     var faces=PackedVector3Array()
     for part:Dictionary in lib.parts:
      for v:Vector3 in part.mesh.get_faces():faces.append(part.transform*v)
     var shape=ConcavePolygonShape3D.new();shape.set_faces(faces);shape.backface_collision=true;shape_cache[d.asset]=shape
    col.shape=shape_cache[d.asset]
   else:
    var shape=BoxShape3D.new();shape.size=lib.bounds.size;col.shape=shape;col.position=lib.bounds.get_center()
   body.add_child(col);add_child(body);stats.colliders+=1
 for key:String in batches:
  var row:Dictionary=batches[key];var mm=MultiMesh.new();mm.transform_format=MultiMesh.TRANSFORM_3D;mm.mesh=row.mesh;mm.instance_count=row.transforms.size()
  for i in row.transforms.size():mm.set_instance_transform(i,row.transforms[i])
  var mesh=MultiMeshInstance3D.new();mesh.multimesh=mm;mesh.visibility_range_end=45. if row.product else 100.;mesh.visibility_range_end_margin=10.;mesh.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF
  if row.product:mesh.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
  add_child(mesh);stats.batches+=1
 for d:Dictionary in plan.boards:
  if d.has("atlas"):continue
  var n=Vector3(d.n[0],0,d.n[1]);var mount=Node3D.new();mount.position=g.v3(d.p);mount.basis=Basis(Vector3.UP.cross(n),Vector3.UP,n);add_child(mount);var board=MeshInstance3D.new();var box=BoxMesh.new();box.size=Vector3(d.w,d.h,.03);board.mesh=box;var mat=StandardMaterial3D.new();mat.albedo_color=Color(.045,.10,.09);mat.roughness=.5;board.material_override=mat;mount.add_child(board)
  var label=Label3D.new();label.font=g.font;label.text=d.title;label.font_size=36;label.pixel_size=.003;label.outline_size=0;label.position.z=.019;label.double_sided=false;label.visibility_range_end=55.;mount.add_child(label)
  var width:float=g.font.get_string_size(d.title,HORIZONTAL_ALIGNMENT_LEFT,-1,36).x*.003
  if width>float(d.w)-.1:label.pixel_size*=float(d.w-.1)/width
 stats.department_signs={"pending":true};call_deferred("build_departments_v23",g,plan)
 stats.products=plan.products.size()
 if not no_packets:stats.stock_packets=load("res://stock_packets_v23.gd").new().build(g,self,plan,library)
 else:stats.stock_packets={"mode":"Production default: original per-SKU MultiMesh, material/texture and mounted-sign sharing enabled. Stock packets are experimental opt-in only.","source_products":plan.products.size(),"accounted_products":plan.products.size(),"all_products_preserved":true,"collision_added":false}
 stats.far_merchandise_lod=load("res://stock_lod_v22.gd").build(g,self,plan)
 stats.missing.append_array(library.stats.missing)
 stats.shared_materials=library.material_pool_v23.materials.size();stats.shared_texture_contents=library.material_pool_v23.canonical_textures.size()
 library.free();set_meta("ready",true);print("V21_RETAIL ",JSON.stringify(stats));g.write_json("v21-retail-build.json",stats)

func build_departments_v23(g,plan:Dictionary)->void:
 await get_tree().physics_frame
 await get_tree().physics_frame
 stats.department_signs=load("res://retail_boards_v23.gd").new().build(g,self,plan);set_meta("v23_departments_ready",true);g.write_json("v23-department-sign-physics.json",stats.department_signs)
