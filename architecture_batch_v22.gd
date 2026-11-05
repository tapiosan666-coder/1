extends RefCounted
# Join only static opaque architecture with exactly matching material, light layers,
# GI/shadow/visibility state. Positions, attributes and every rendered triangle are retained.
func run(g)->Dictionary:
 var started:int=Time.get_ticks_usec();var buckets:Dictionary={};var stats:Dictionary={"source_nodes":0,"output_nodes":0,"source_triangles":0,"output_triangles":0,"skipped":0,"effects_disabled":false,"collision_modified":false}
 for node:Node in g.get_children():
  if not node is MeshInstance3D or not str(node.name).begins_with("Architecture_")or not node.visible:continue
  if node.mesh==null or node.mesh.get_surface_count()!=1 or not node.transform.is_equal_approx(Transform3D.IDENTITY):stats.skipped+=1;continue
  var name_key:String=str(node.name).trim_prefix("Architecture_").split("@@")[0];var material:Material=node.mesh.surface_get_material(0)
  if material==null or name_key.contains("glass")or name_key.contains("leaf")or name_key in["step","yellow","roof_glass"]:stats.skipped+=1;continue
  if material is BaseMaterial3D and material.transparency!=BaseMaterial3D.TRANSPARENCY_DISABLED:stats.skipped+=1;continue
  if material is ShaderMaterial and material.shader!=null and material.shader.code.contains("ALPHA"):stats.skipped+=1;continue
  var aabb:AABB=node.mesh.get_aabb()
  if aabb.size.x>70 or aabb.size.z>70:stats.skipped+=1;continue
  var centre:Vector3=aabb.get_center();var key:String="%d|%d|%d|%d|%s|%s|%d|%d|%d|%d"%[material.get_instance_id(),node.layers,node.cast_shadow,node.gi_mode,str(node.visibility_range_end),str(node.visibility_range_end_margin),floor(centre.x/48.),floor(aabb.position.y/5.35),floor(centre.z/48.),node.mesh.surface_get_format(0)]
  if not buckets.has(key):buckets[key]={"nodes":[],"material":material,"material_key":name_key}
  buckets[key].nodes.append(node)
 for key:String in buckets:
  var row:Dictionary=buckets[key]
  if row.nodes.size()<2:stats.skipped+=row.nodes.size();continue
  var merged:Array=[];merged.resize(Mesh.ARRAY_MAX);var ids=PackedInt32Array();var offset:int=0
  for node:MeshInstance3D in row.nodes:
   var data:Array=node.mesh.surface_get_arrays(0);var vertices:PackedVector3Array=data[Mesh.ARRAY_VERTEX];var indices=data[Mesh.ARRAY_INDEX]
   if indices!=null and indices.size()>0:
    for index:int in indices:ids.append(index+offset)
    stats.source_triangles+=indices.size()/3
   else:
    for index in vertices.size():ids.append(index+offset)
    stats.source_triangles+=vertices.size()/3
   for slot in range(Mesh.ARRAY_MAX):
    if slot==Mesh.ARRAY_INDEX or data[slot]==null:continue
    if merged[slot]==null:merged[slot]=data[slot].duplicate()
    else:merged[slot].append_array(data[slot])
   offset+=vertices.size()
  merged[Mesh.ARRAY_INDEX]=ids;var mesh=ArrayMesh.new();mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,merged);mesh.surface_set_material(0,row.material);var first:MeshInstance3D=row.nodes[0];var instance=MeshInstance3D.new();instance.mesh=mesh;instance.name="Architecture_"+row.material_key+"@@V22-BATCH-"+str(stats.output_nodes);instance.layers=first.layers;instance.cast_shadow=first.cast_shadow;instance.gi_mode=first.gi_mode;instance.visibility_range_end=first.visibility_range_end;instance.visibility_range_end_margin=first.visibility_range_end_margin;g.add_child(instance);stats.output_nodes+=1;stats.output_triangles+=ids.size()/3
  for node:MeshInstance3D in row.nodes:node.visible=false;node.queue_free();stats.source_nodes+=1
 stats.triangles_preserved=stats.source_triangles==stats.output_triangles;stats.build_seconds=(Time.get_ticks_usec()-started)/1000000.;g.write_json("v22-architecture-batching.json",stats);print("V22_ARCHITECTURE_BATCH ",JSON.stringify(stats));return stats
