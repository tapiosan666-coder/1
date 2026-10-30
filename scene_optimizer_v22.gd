extends Node3D
# Conservative occluders from the very same final opaque wall/floor triangles that are rendered.
# No guessed boxes, closed shop entrances, or occluders from superseded structural variants.
var game
var stats:Dictionary={"occluders":0,"source_triangles":0,"opaque_nodes":0,"skipped_small_triangles":0,"rendered_geometry_modified":false,"effects_disabled":false}
func structural(label:String)->bool:
 if label.contains("glass")or label.contains("leaf")or label.contains("light")or label.contains("emitter"):return false
 return label in["plaster","wall_sand","wall_sage","wall_chalk","wall_taupe","dark_stone","stone","floor","concrete","ceiling","roof"]or label.contains("floor_")or label.ends_with("_floor")or label.contains("concrete")or label.contains("ceiling")
func setup(g)->void:
 game=g;name="V22_Exact_Architectural_Occlusion";var buckets:Dictionary={};var root_inverse:Transform3D=g.global_transform.affine_inverse()
 for node:Node in g.get_children():
  if node.is_queued_for_deletion()or not node is MeshInstance3D or not str(node.name).begins_with("Architecture_"):continue
  var key:String=str(node.name).trim_prefix("Architecture_").split("@@")[0]
  if not structural(key)or node.mesh==null:continue
  var points:PackedVector3Array=node.mesh.get_faces();var transform:Transform3D=root_inverse*node.global_transform;var accepted:int=0
  for i in range(0,points.size(),3):
   var a:Vector3=transform*points[i];var b:Vector3=transform*points[i+1];var c:Vector3=transform*points[i+2]
   if (b-a).cross(c-a).length()*.5<.35:stats.skipped_small_triangles+=1;continue
   var centre:Vector3=(a+b+c)/3.;var bucket:String="%d,%d,%d"%[floor(centre.x/48.),floor(centre.y/5.35),floor(centre.z/48.)]
   if not buckets.has(bucket):buckets[bucket]={"vertices":PackedVector3Array(),"indices":PackedInt32Array()}
   var data:Dictionary=buckets[bucket];var j:int=data.vertices.size();data.vertices.append_array(PackedVector3Array([a,b,c]));data.indices.append_array(PackedInt32Array([j,j+1,j+2,j+2,j+1,j]));accepted+=1
  if accepted>0:stats.opaque_nodes+=1;stats.source_triangles+=accepted
 for key:String in buckets:
  var data:Dictionary=buckets[key];var occluder=ArrayOccluder3D.new();occluder.set_arrays(data.vertices,data.indices);var node=OccluderInstance3D.new();node.occluder=occluder;node.name="ExactOpaque_"+key.validate_node_name();add_child(node);stats.occluders+=1
 var enabled:bool=true
 for a:String in OS.get_cmdline_user_args():
  if a=="--v22-no-occlusion":enabled=false
 set_enabled(enabled);g.write_json("v22-occlusion-build.json",stats);print("V22_OCCLUSION ",JSON.stringify(stats))
func set_enabled(enabled:bool)->void:
 visible=enabled;get_viewport().use_occlusion_culling=enabled;stats.enabled=enabled
func _exit_tree()->void:game=null
