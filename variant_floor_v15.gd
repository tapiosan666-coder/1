extends RefCounted
var floors:Array=[]
func setup()->void:
 var path="res://source/v15/map-data-C-option.json";var raw:String
 if FileAccess.file_exists(path):raw=FileAccess.get_file_as_string(path)
 else:
  var bytes=FileAccess.get_file_as_bytes(path+".zst");raw=bytes.slice(8).decompress(bytes.decode_u32(4),FileAccess.COMPRESSION_ZSTD).get_string_from_utf8()
 floors=JSON.parse_string(raw).filter(func(f):return f.wing=="C"and int(f.level)>=1)
func covered(p:Vector3,half:Vector2=Vector2.ZERO,u:Vector2=Vector2.RIGHT,n:Vector2=Vector2.UP)->bool:
 if p.z> -170 or p.z< -425 or p.x< -195 or p.x>185:return true
 var found:Dictionary={}
 for f:Dictionary in floors:
  if abs(float(f.height)-p.y)<.25:found=f;break
 if found.is_empty():return true
 for x:float in[-1.,0.,1.]:
  for z:float in[-1.,0.,1.]:
   var point=Vector2(p.x-429,p.z+46)+u*half.x*x+n*half.y*z;var inside:bool=false
   for polygon:Array in found.floor:
    if not Geometry2D.is_point_in_polygon(point,PackedVector2Array(polygon[0].map(func(q):return Vector2(q[0],q[1])))):continue
    var hole:bool=false
    for ring:Array in polygon.slice(1):
     if Geometry2D.is_point_in_polygon(point,PackedVector2Array(ring.map(func(q):return Vector2(q[0],q[1])))):hole=true;break
    if not hole:inside=true;break
   if not inside:return false
 return true
