extends RefCounted
func apply(geo:Dictionary)->Dictionary:
 var faces=PackedFloat32Array();var rows:Array=[]
 for key:String in geo.surfaces:
  if not key.begins_with("v10_floor_"):continue
  var room:String=key.split("@@")[-1]
  if not(room.begins_with("V10-PUBLIC-")or room.begins_with("V15-B-WEST-")or room.begins_with("V22-A-WEST-")):continue
  var d:Dictionary=geo.surfaces[key];var ix=d.get("i",PackedInt32Array());var count:int=0
  if ix.is_empty():
   for i in range(d.v.size()/3):ix.append(i)
  for i in range(0,ix.size(),3):
   var a=Vector3(d.v[ix[i]*3],d.v[ix[i]*3+1],d.v[ix[i]*3+2]);var b=Vector3(d.v[ix[i+1]*3],d.v[ix[i+1]*3+1],d.v[ix[i+1]*3+2]);var c=Vector3(d.v[ix[i+2]*3],d.v[ix[i+2]*3+1],d.v[ix[i+2]*3+2])
   if absf((b-a).cross(c-a).normalized().y)<.99:continue
   for p in[a,b,c]:faces.append_array(PackedFloat32Array([p.x,p.y,p.z]))
   count+=1
  if count>0:rows.append({"surface":key,"visible_finish_collision_triangles":count})
 geo.colliders["v28_public_finish"]=faces
 return {"surfaces":rows,"triangle_count":faces.size()/9,"structural_slabs_unchanged":true,"scope":"Real finish wearing-course collision exactly follows retained visible public finish. Existing structural slab remains below as a separate physical substrate."}
