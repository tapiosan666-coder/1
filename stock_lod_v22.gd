extends RefCounted
# Far merchandise silhouettes only; imported original meshes remain authoritative at shopping distances.
static func build(g,owner:Node3D,plan:Dictionary)->Dictionary:
 var bounds:Dictionary=g.read_json("res://source/v21/model-bounds.json");bounds.merge(g.read_json("res://source/v22/model-bounds.json"));bounds.merge(g.read_json("res://source/v23/model-bounds.json"));bounds.merge(g.read_json("res://source/v24/model-bounds.json"));var batches:Dictionary={};var colours:Array=[Color(.18,.27,.30),Color(.59,.39,.23),Color(.74,.69,.55),Color(.28,.39,.29),Color(.48,.20,.17),Color(.32,.27,.40)];var instances:int=0
 for d:Dictionary in plan.products:
  if not bounds.has(d.model):continue
  var b:Dictionary=bounds[d.model];var lo=g.v3(b.min);var hi=g.v3(b.max);var size:Vector3=(hi-lo).max(Vector3.ONE*.004);var n=Vector3(d.n[0],0,d.n[1]);var basis=Basis(Vector3.UP.cross(n),Vector3.UP,n)
  if d.get("pitch_deg",0.)!=0.:basis=basis*Basis(Vector3.RIGHT,deg_to_rad(float(d.pitch_deg)))
  var transform=Transform3D(basis,g.v3(d.p));var key:String="%d,%d,%d"%[floor(d.p[0]/16.),floor(d.p[1]/5.35),floor(d.p[2]/16.)]
  if not batches.has(key):batches[key]=[]
  batches[key].append({"t":Transform3D(basis.scaled_local(size),transform*((lo+hi)*.5)),"colour":colours[posmod(str(d.model).hash(),colours.size())]});instances+=1
 var cube=BoxMesh.new();cube.size=Vector3.ONE;var mat=StandardMaterial3D.new();mat.vertex_color_use_as_albedo=true;mat.albedo_color=Color.WHITE;mat.roughness=.76;cube.material=mat
 for key:String in batches:
  var rows:Array=batches[key];var mm=MultiMesh.new();mm.transform_format=MultiMesh.TRANSFORM_3D;mm.use_colors=true;mm.mesh=cube;mm.instance_count=rows.size()
  for i in rows.size():mm.set_instance_transform(i,rows[i].t);mm.set_instance_color(i,rows[i].colour)
  var mesh=MultiMeshInstance3D.new();mesh.name="Merchandise_Far_LOD_"+key.validate_node_name();mesh.multimesh=mm;mesh.visibility_range_begin=45.;mesh.visibility_range_end=110.;mesh.visibility_range_begin_margin=2.;mesh.visibility_range_end_margin=6.;mesh.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;owner.add_child(mesh)
 return{"instances":instances,"batches":batches.size(),"near_original_meshes_end_m":45.,"far_silhouettes_begin_m":45.,"far_silhouettes_end_m":110.,"scope":"Low-detail bounding silhouettes with per-SKU palette, not detailed product art; no character or architecture simplification. LOD switches use per-batch AABB distance and require visual pop-in review."}
