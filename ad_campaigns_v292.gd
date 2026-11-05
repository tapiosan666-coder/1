extends RefCounted
func apply(game,mount:Node3D,panel:MeshInstance3D,sid:String,detail:bool=false)->Dictionary:
 if not game.v292_enabled():return{}
 # Printed face must sit in front of the existing frame backing, not inside it.
 panel.position.z=maxf(panel.position.z,.007)
 var data:Dictionary=game.read_json("res://source/v292/advertisements.json")
 if not data.stores.has(sid)or not sid in data.selected_store_ids or detail:return{}
 var d:Dictionary=data.stores[sid];var size:Vector2=panel.mesh.size;var material=ShaderMaterial.new();material.shader=load("res://campaign_v292.gdshader");material.set_shader_parameter("illustration",load(data.illustration_atlas));material.set_shader_parameter("region",Vector4(d.region[0],d.region[1],d.region[2],d.region[3]));material.set_shader_parameter("paper",Color(d.paper));material.set_shader_parameter("ink",Color(d.ink));material.set_shader_parameter("variant",1. if detail else 0.);panel.material_override=material
 var helper=game.get_node("V26_Mall_Architecture");var x:float=panel.position.x;var z:float=panel.position.z+.004
 var labels:Array=[]
 labels.append(helper.text(mount,d.brand,Vector3(x,size.y*.449,z),size.y*.046,size.x*.90,Color(d.ink)))
 labels.append(helper.text(mount,d.copy,Vector3(x,-size.y*.395,z),size.y*.043,size.x*.90,Color(d.ink)))
 labels.append(helper.text(mount,d.subtitle,Vector3(x,-size.y*.460,z),size.y*.023,size.x*.86,Color(d.ink)))
 for l:Label3D in labels:l.double_sided=false
 var wp:Vector3=mount.to_global(panel.position);var normal:Vector3=mount.global_basis.z.normalized()
 return{"world_p":[wp.x,wp.y,wp.z],"normal":[normal.x,normal.y,normal.z],"store_id":sid,"brand":d.brand,"genre":d.genre,"atlas_region":d.region,"size":[size.x,size.y],"original_art_unmodified":true,"product_based_ad_replaced_only_here":true}
