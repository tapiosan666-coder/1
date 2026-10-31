extends RefCounted
# Local-space merchandise packets with measured sub-millimetre template tolerance: independent product data remains authoritative.
# Only matching complete arrangements share geometry; no product or triangle is deleted.
var pool=preload("res://material_pool_v23.gd").new()
func basis_for(d:Dictionary)->Basis:
 var n=Vector3(d.n[0],0,d.n[1]);var b=Basis(Vector3.UP.cross(n),Vector3.UP,n)
 if d.get("pitch_deg",0.)!=0.:b=b*Basis(Vector3.RIGHT,deg_to_rad(float(d.pitch_deg)))
 return b
func build(g,owner:Node3D,plan:Dictionary,library)->Dictionary:
 var started:int=Time.get_ticks_usec();var hosts:Dictionary={};var by:Dictionary={};var templates:Dictionary={};var batches:Dictionary={};var fallback:Dictionary={};var choices:Dictionary={};var packet_cells:int=0;var original_cells:int=0;var source_products:int=0;var template_triangles:int=0;var rendered_products:int=0;var source_triangles:int=0;var output_triangles:int=0;var triangle_cache:Dictionary={};var max_template_error:float=0.;var fallback_products:int=0
 for r:Dictionary in plan.fixtures:hosts[r.id]=r
 for d:Dictionary in plan.products:
  if not by.has(d.host):by[d.host]=[]
  by[d.host].append(d)
 for identity:String in by:
  var host:Dictionary=hosts[identity];var ht=Transform3D(basis_for(host),g.v3(host.p));var inv=ht.affine_inverse();var content:Array=[];var signatures:PackedStringArray=[]
  for d:Dictionary in by[identity]:
   var local:Transform3D=inv*Transform3D(basis_for(d),g.v3(d.p));var nums:PackedFloat64Array=[]
   for index in range(4):
    var axis:Vector3=local.origin if index==3 else local.basis[index];var precision:float=.001 if index==3 else .00001
    nums.append(snappedf(axis.x,precision));nums.append(snappedf(axis.y,precision));nums.append(snappedf(axis.z,precision))
   var signature:String=str(d.asset)+"|"+str(nums);content.append({"row":d,"local":local,"signature":signature});source_products+=1
  for r:Dictionary in content:
   if not triangle_cache.has(r.row.asset):
    var lib:Dictionary=library.get_asset(r.row.asset,false);var triangles:int=0
    for part:Dictionary in lib.parts:triangles+=part.mesh.get_faces().size()/3
    triangle_cache[r.row.asset]=triangles
   source_triangles+=int(triangle_cache[r.row.asset])
  content.sort_custom(func(a,b):return a.signature<b.signature)
  for r:Dictionary in content:signatures.append(r.signature)
  var signature:String=";".join(signatures).sha256_text();var cell:String="%d,%d,%d"%[floor(host.p[0]/28.),floor(host.p[1]/5.35),floor(host.p[2]/28.)]
  if not templates.has(signature)and templates.size()<512:
   var groups:Dictionary={};var originals:Array=[]
   for r:Dictionary in content:
    var asset:Dictionary=library.get_asset(r.row.asset,false)
    if asset.is_empty():continue
    originals.append(r.local)
    for part:Dictionary in asset.parts:
     for surface in part.mesh.get_surface_count():
      var material:Material=pool.canonical(part.mesh.surface_get_material(surface));var key:String=str(material.get_instance_id()if material!=null else 0)+"|"+str(part.mesh.surface_get_format(surface))
      if not groups.has(key):
       var st=SurfaceTool.new();st.begin(Mesh.PRIMITIVE_TRIANGLES);groups[key]={"surface":st,"material":material}
      groups[key].surface.append_from(part.mesh,surface,r.local*part.transform)
   var pieces:Array=[]
   for key:String in groups:
    var mesh:ArrayMesh=groups[key].surface.commit();mesh.surface_set_material(0,groups[key].material);pieces.append(mesh);template_triangles+=mesh.get_faces().size()/3
   templates[signature]={"triangles":pieces.reduce(func(total,mesh):return total+mesh.get_faces().size()/3,0),"meshes":pieces,"count":content.size(),"transforms":originals}
  if not choices.has(cell):choices[cell]=[]
  choices[cell].append({"host":ht,"content":content,"signature":signature})
 for cell:String in choices:
  var packet_keys:Dictionary={};var original_keys:Dictionary={};var available:bool=true
  for item:Dictionary in choices[cell]:
   if not templates.has(item.signature):available=false
   else:
    for i in templates[item.signature].meshes.size():packet_keys[item.signature+"|"+str(i)]=true
   for r:Dictionary in item.content:
    var asset:Dictionary=library.get_asset(r.row.asset,false)
    for i in asset.parts.size():original_keys[str(r.row.asset)+"|"+str(i)]=true
  # Use packets only in a cell where they reduce the complete material/shape batch count.
  var use_packet:bool=available and packet_keys.size()<original_keys.size()
  if use_packet:packet_cells+=1
  else:original_cells+=1
  for item:Dictionary in choices[cell]:
   var content:Array=item.content;var ht:Transform3D=item.host
   if use_packet:
    var packet:Dictionary=templates[item.signature];rendered_products+=packet.count;output_triangles+=int(packet.triangles)
    for i in mini(packet.transforms.size(),content.size()):max_template_error=maxf(max_template_error,packet.transforms[i].origin.distance_to(content[i].local.origin))
    for i in packet.meshes.size():
     var key:String=item.signature+"|"+cell+"|"+str(i)
     if not batches.has(key):batches[key]={"mesh":packet.meshes[i],"transforms":[]}
     batches[key].transforms.append(ht)
   else:
    for r:Dictionary in content:
     var asset:Dictionary=library.get_asset(r.row.asset,false);var tr:Transform3D=ht*r.local;fallback_products+=1;rendered_products+=1;output_triangles+=int(triangle_cache[r.row.asset])
     var pc:String="%d,%d,%d"%[floor(r.row.p[0]/28.),floor(r.row.p[1]/5.35),floor(r.row.p[2]/28.)]
     for i in asset.parts.size():
      var key:String=str(r.row.asset)+"|"+pc+"|"+str(i)
      if not fallback.has(key):fallback[key]={"mesh":asset.parts[i].mesh,"transforms":[]}
      fallback[key].transforms.append(tr*asset.parts[i].transform)
 var count:int=0;var instance_count:int=0
 for source:Dictionary in[batches,fallback]:
  for key:String in source:
   var row:Dictionary=source[key];var mm=MultiMesh.new();mm.transform_format=MultiMesh.TRANSFORM_3D;mm.mesh=row.mesh;mm.instance_count=row.transforms.size()
   for i in row.transforms.size():mm.set_instance_transform(i,row.transforms[i])
   var node=MultiMeshInstance3D.new();node.name="Stock_Packet_"+str(count);node.multimesh=mm;node.visibility_range_end=45.;node.visibility_range_end_margin=2.;node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;node.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF;owner.add_child(node);count+=1;instance_count+=row.transforms.size()
 return{"source_triangles":source_triangles,"output_triangles":output_triangles,"all_triangles_preserved":source_triangles==output_triangles,"source_products":source_products,"accounted_products":rendered_products,"all_products_preserved":source_products==rendered_products,"host_arrangements":by.size(),"unique_packet_templates":templates.size(),"template_triangles":template_triangles,"GPU_mesh_instances":instance_count,"draw_batches":count,"packet_cells":packet_cells,"original_cells":original_cells,"fallback_products":fallback_products,"maximum_shared_template_position_error_m":max_template_error,"canonical_standard_materials":pool.materials.size(),"build_seconds":(Time.get_ticks_usec()-started)/1000000.,"collision_added":false,"quality_scope":"Exact transformed original product triangles in matching host arrangements. Template translation key rounded to1mm (basis10 micrometres); positions remain within reported tolerance. Transparent sorting remains subject to visual review."}
