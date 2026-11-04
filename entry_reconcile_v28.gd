extends RefCounted
var u:Vector3
var n:Vector3
var centre:Vector3
var stats:Array=[]
func local(p)->Vector3:
 var d=Vector3(p[0],p[1],p[2])-centre;return Vector3(d.dot(u),d.y,d.dot(n))
func clip(poly:Array,axis:Vector3,limit:float,less:bool)->Array:
 var out:Array=[]
 for i in poly.size():
  var a=poly[i];var b=poly[(i+1)%poly.size()];var da:float=Vector3(a[0],a[1],a[2]).dot(axis)-limit;var db:float=Vector3(b[0],b[1],b[2]).dot(axis)-limit
  var ain:bool=da<=.000001 if less else da>=-.000001;var bin:bool=db<=.000001 if less else db>=-.000001
  if ain:out.append(a)
  if ain!=bin:
   var p=PackedFloat32Array();p.resize(a.size());var t:float=da/(da-db)
   for j in a.size():p[j]=lerpf(a[j],b[j],t)
   out.append(p)
 return out
func outside(tri:Array)->Array:
 var parts:Array=[];var rest:Array=tri
 for plane in [[u,centre.dot(u)+4.01],[-u,-centre.dot(u)+4.01],[n,centre.dot(n)+.3],[-n,-centre.dot(n)+.3],[Vector3.UP,3.35],[Vector3.DOWN,0.02]]:
  if rest.is_empty():break
  var p=clip(rest,plane[0],plane[1],false)
  if p.size()>2:parts.append(p)
  rest=clip(rest,plane[0],plane[1],true)
 return parts
func candidate(tri:Array)->bool:
 var lo=Vector3(INF,INF,INF);var hi=Vector3(-INF,-INF,-INF)
 for p in tri:var q:Vector3=local(p);lo=lo.min(q);hi=hi.max(q)
 if lo.x>4.01 or hi.x< -4.01 or lo.z>.3 or hi.z< -.3 or lo.y>3.35 or hi.y<0:return false
 if hi.x-lo.x<3.:return false # Do not cut narrow column faces.
 var a=Vector3(tri[0][0],tri[0][1],tri[0][2]);var b=Vector3(tri[1][0],tri[1][1],tri[1][2]);var c=Vector3(tri[2][0],tri[2][1],tri[2][2]);var normal=(b-a).cross(c-a).normalized()
 return absf(normal.dot(n))>.95
func apply(geo:Dictionary,data:Dictionary)->Array:
 var footprints:Array=[]
 for key:String in geo.surfaces:
  var id:int=4 if key.ends_with("@@V17-VERIFIED-WALL-4")else 5 if key.ends_with("@@V17-VERIFIED-WALL-5")else 0
  if id==0:continue
  var oldx:float=14.0628519 if id==4 else 4.26205444;var newx:float=15.1 if id==4 else .9;var scale:float=.67 if id==4 else .45
  var v=geo.surfaces[key].v
  for i in range(0,v.size(),3):v[i]=newx+(v[i]-oldx)*scale;v[i+1]=1.6502+(v[i+1]-1.6502)*scale;v[i+2]=33.16+(v[i+2]-33.16)*scale
  geo.surfaces[key].v=v

 for wing:String in data:
  var d:Dictionary=data[wing];n=Vector3(d.n[0],0,d.n[1]);u=Vector3(n.z,0,-n.x);centre=Vector3(d.facade[0],0,d.facade[1]);var changed:Array=[];var coll:int=0
  for key:String in geo.surfaces.keys():
   if key.contains("COLUMN")or not key.split("@@")[0]in["plaster","wall_sand","wall_chalk","wall_taupe","glass","v10_glass","v10_chalk"]:continue
   var s:Dictionary=geo.surfaces[key];var ix=s.get("i",PackedInt32Array());var output=PackedInt32Array();var count:int=0
   if ix.is_empty():
    for i in s.v.size()/3:ix.append(i)
   for k in range(0,ix.size(),3):
    var pos:Array=[]
    for j in 3:pos.append(s.v.slice(ix[k+j]*3,ix[k+j]*3+3))
    if not candidate(pos):output.append_array(ix.slice(k,k+3));continue
    var tri:Array=[]
    for j in 3:
     var a=PackedFloat32Array();var index:int=ix[k+j]
     for row in [["v",3],["n",3],["uv",2],["c",4]]:
      for f in row[1]:a.append(s[row[0]][index*int(row[1])+f])
     tri.append(a)
    count+=1
    for p in outside(tri):
     for j in range(1,p.size()-1):
      for a in [p[0],p[j],p[j+1]]:
       output.append(s.v.size()/3)
       for row in [["v",0,3],["n",3,6],["uv",6,8],["c",8,12]]:var buf=s[row[0]];buf.append_array(a.slice(row[1],row[2]));s[row[0]]=buf
   if count>0:s.i=output;geo.surfaces[key]=s;changed.append({"key":key,"triangles":count})
  for key:String in geo.colliders:
   var original=geo.colliders[key];var result=PackedFloat32Array();var count:int=0
   for i in range(0,original.size(),9):
    var tri:Array=[original.slice(i,i+3),original.slice(i+3,i+6),original.slice(i+6,i+9)]
    if not candidate(tri):result.append_array(original.slice(i,i+9));continue
    count+=1
    for p in outside(tri):
     for j in range(1,p.size()-1):
      for a in [p[0],p[j],p[j+1]]:result.append_array(a)
   if count>0:geo.colliders[key]=result;coll+=count
  stats.append({"wing":wing,"facade":d.facade,"wall_faces":changed,"collision_triangles_replaced":coll,"columns_untouched":true,"formal_source_unchanged":true})
  var c=Vector3(d.p[0],0,d.p[2]);var ring:Array=[]
  for q in [Vector2(-4,-5),Vector2(4,-5),Vector2(4,5),Vector2(-4,5)]:var p=c+u*q.x+n*q.y;ring.append([p.x,p.z])
  footprints.append(ring)
 var floor_report=load("res://terrain_reconcile_v28.gd").new().apply(geo,{"garden":footprints[0],"neck":footprints[1]});stats.append({"entrance_floor_replacement":floor_report})
 return stats
