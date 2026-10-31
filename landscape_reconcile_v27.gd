extends RefCounted
func apply(geo:Dictionary)->Dictionary:
 var rows:Array=[];var collision_triangles:int=0
 # Existing L-3 garden lamp lies on the new running line. Move its complete assembly to the west garden edge.
 for k:String in geo.surfaces:
  if not k.ends_with("@@V9-PARKLIGHT-L-3"):continue
  var vertices=geo.surfaces[k].v
  for i in range(0,vertices.size(),3):vertices[i]-=10.5
  geo.surfaces[k].v=vertices;rows.append(k)
 for k:String in geo.colliders:
  var faces=geo.colliders[k]
  for i in range(0,faces.size(),9):
   var inside:bool=true
   for j in [0,3,6]:
    if faces[i+j]< -80.1 or faces[i+j]> -79.2 or faces[i+j+2]< -248.5 or faces[i+j+2]> -247.5 or faces[i+j+1]< -.001 or faces[i+j+1]>4.1:inside=false
   if inside:
    for j in [0,3,6]:faces[i+j]-=10.5
    collision_triangles+=1
  geo.colliders[k]=faces
 return {"id":"V9-PARKLIGHT-L-3","delta_world":[-10.5,0,0],"old_centre":[-79.675,0,-248.065],"new_centre":[-90.175,0,-248.065],"surfaces":rows,"collision_triangles_moved":collision_triangles,"reason":"既存庭園灯が新しい芝生走行線にあるため柵外の緑地縁へ移設。メッシュ・発光部・衝突を同時移設"}
