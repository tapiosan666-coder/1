extends RefCounted
var polygons:Array=[]
var signs:Array=[]
var bounds:Rect2
var stats:Dictionary={"changed_surfaces":[],"removed_collision_triangles":0,"old_floor_replaced":true,"formal_source_assets_modified":false}
func cross2(a:Vector2,b:Vector2)->float:return a.x*b.y-a.y*b.x
func initialise(data:Dictionary)->void:
 for ring in [data.garden,data.neck]:
  var p:Array=[]
  for q in ring:p.append(Vector2(q[0],q[1]))
  var area:float=0.
  for i in p.size():area+=cross2(p[i],p[(i+1)%p.size()])
  polygons.append(p);signs.append(signf(area))
  for q:Vector2 in p:
   if bounds.size==Vector2.ZERO:bounds=Rect2(q,Vector2(.00001,.00001))
   else:bounds=bounds.expand(q)
func clip(poly:Array,a:Vector2,b:Vector2,inside:bool,orientation:float)->Array:
 var result:Array=[]
 for i in poly.size():
  var p=poly[i];var q=poly[(i+1)%poly.size()];var dp:float=cross2(b-a,Vector2(p[0],p[2])-a)*orientation;var dq:float=cross2(b-a,Vector2(q[0],q[2])-a)*orientation
  var pin:bool=dp>=-.000001 if inside else dp<=.000001;var qin:bool=dq>=-.000001 if inside else dq<=.000001
  if pin:result.append(p)
  if pin!=qin:
   var t:float=dp/(dp-dq);var v=PackedFloat32Array();v.resize(p.size())
   for j in p.size():v[j]=lerpf(p[j],q[j],t)
   result.append(v)
 return result
func subtract(poly:Array,ring:Array,orientation:float)->Array:
 var parts:Array=[];var rest:Array=poly
 for i in ring.size():
  if rest.is_empty():break
  var out:Array=clip(rest,ring[i],ring[(i+1)%ring.size()],false,orientation)
  if out.size()>=3:parts.append(out)
  rest=clip(rest,ring[i],ring[(i+1)%ring.size()],true,orientation)
 return parts
func pieces(tri:Array)->Array:
 var parts:Array=[tri]
 for i in polygons.size():
  var next:Array=[]
  for p in parts:next.append_array(subtract(p,polygons[i],signs[i]))
  parts=next
 return parts
func area(poly:Array)->float:
 var a:float=0.
 for i in poly.size():
  var p=poly[i];var q=poly[(i+1)%poly.size()];a+=p[0]*q[2]-q[0]*p[2]
 return absf(a)*.5
func candidate(tri:Array)->bool:
 var lo=Vector3(INF,INF,INF);var hi=Vector3(-INF,-INF,-INF)
 for q in tri:
  var p=Vector3(q[0],q[1],q[2]);lo=lo.min(p);hi=hi.max(p)
 if hi.x<bounds.position.x or lo.x>bounds.end.x or hi.z<bounds.position.y or lo.z>bounds.end.y or lo.y< -.10 or hi.y>.15:return false
 var a=Vector3(tri[0][0],tri[0][1],tri[0][2]);var b=Vector3(tri[1][0],tri[1][1],tri[1][2]);var c=Vector3(tri[2][0],tri[2][1],tri[2][2])
 return absf((b-a).cross(c-a).normalized().y)>.95
func apply(geo:Dictionary,data:Dictionary)->Dictionary:
 initialise(data)
 for key:String in geo.surfaces.keys():
  if not key.split("@@")[0]in ["soil","leaf","v8_soil","v10_groundcover","v10_floor_C","v10_floor_B","v10_floor_A","stone","v10_paving","v8_paving"]:continue
  var d:Dictionary=geo.surfaces[key];var ix=d.get("i",PackedInt32Array());var output=PackedInt32Array();var changed:int=0
  if ix.is_empty():
   for i in range(d.v.size()/3):ix.append(i)
  for k in range(0,ix.size(),3):
   var pos:Array=[]
   for j in 3:pos.append(d.v.slice(ix[k+j]*3,ix[k+j]*3+3))
   if not candidate(pos):output.append_array(ix.slice(k,k+3));continue
   var tri:Array=[]
   for j in 3:
    var index:int=ix[k+j];var a=PackedFloat32Array()
    for row in [["v",3],["n",3],["uv",2],["c",4]]:
     for f in row[1]:a.append(d[row[0]][index*int(row[1])+f])
    tri.append(a)
   var kept:Array=pieces(tri);var kept_area:float=0.
   for poly in kept:kept_area+=area(poly)
   if kept_area>=area(tri)-.0000001:output.append_array(ix.slice(k,k+3));continue
   changed+=1
   for poly in kept:
    for j in range(1,poly.size()-1):
     if area([poly[0],poly[j],poly[j+1]])<.0000001:continue
     for v in [poly[0],poly[j],poly[j+1]]:
      var index:int=d.v.size()/3;output.append(index)
      for row in [["v",0,3],["n",3,6],["uv",6,8],["c",8,12]]:
       var arr=d[row[0]];arr.append_array(v.slice(row[1],row[2]));d[row[0]]=arr
  if changed>0:
   stats.changed_surfaces.append({"key":key,"clipped_source_triangles":changed})
   if output.is_empty():geo.surfaces.erase(key)
   else:d.i=output;geo.surfaces[key]=d
 for key:String in geo.colliders:
  var source=geo.colliders[key];var result=PackedFloat32Array();var changed:int=0
  for i in range(0,source.size(),9):
   var tri:Array=[source.slice(i,i+3),source.slice(i+3,i+6),source.slice(i+6,i+9)]
   if not candidate(tri):result.append_array(source.slice(i,i+9));continue
   var kept:Array=pieces(tri);var kept_area:float=0.
   for poly in kept:kept_area+=area(poly)
   if kept_area>=area(tri)-.0000001:result.append_array(source.slice(i,i+9));continue
   changed+=1
   for poly in kept:
    for j in range(1,poly.size()-1):
     if area([poly[0],poly[j],poly[j+1]])<.0000001:continue
     for p in [poly[0],poly[j],poly[j+1]]:result.append_array(p)
  if changed>0:geo.colliders[key]=result;stats.removed_collision_triangles+=changed
 return stats
