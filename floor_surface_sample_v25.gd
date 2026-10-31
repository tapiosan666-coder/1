extends RefCounted
var triangles:Array=[]
var cells:Dictionary={}
var heights:Array=[]
func build(g,levels:Array)->void:
 heights=levels
 for node:Node in g.find_children("*","MeshInstance3D",true,false):
  if node.mesh==null or not str(node.name).begins_with("Architecture_"):continue
  var label:String=str(node.name).to_lower()
  if not(label.contains("stone")or label.contains("quartz")or label.contains("terrazzo")or label.contains("floor")or label.contains("pavers")or label.contains("marble")or label.contains("paving")):continue
  var bounds:AABB=node.global_transform*node.mesh.get_aabb();var relevant:bool=false
  for h:float in heights:
   if bounds.position.y<=h+.018 and bounds.end.y>=h-.018:relevant=true;break
  if not relevant:continue
  var vertices:PackedVector3Array=node.mesh.get_faces()
  for i in range(0,vertices.size(),3):
   var a:Vector3=node.global_transform*vertices[i];var b:Vector3=node.global_transform*vertices[i+1];var c:Vector3=node.global_transform*vertices[i+2]
   if absf(a.y-b.y)>.0005 or absf(a.y-c.y)>.0005:continue
   var area:float=absf((b-a).cross(c-a).y)*.5
   if area<.0001:continue
   var band:int=-1
   for j in heights.size():
    if absf(a.y-float(heights[j]))<.018:band=j;break
   if band<0:continue
   var polygon=PackedVector2Array([Vector2(a.x,a.z),Vector2(b.x,b.z),Vector2(c.x,c.z)]);var id:int=triangles.size();triangles.append({"polygon":polygon,"y":a.y});var lo=Vector2(minf(a.x,minf(b.x,c.x)),minf(a.z,minf(b.z,c.z)));var hi=Vector2(maxf(a.x,maxf(b.x,c.x)),maxf(a.z,maxf(b.z,c.z)))
   for x in range(floori(lo.x/8.),floori(hi.x/8.)+1):
    for z in range(floori(lo.y/8.),floori(hi.y/8.)+1):
     var key:String="%d,%d,%d"%[band,x,z]
     if not cells.has(key):cells[key]=[]
     cells[key].append(id)
func surface_y(p:Vector3,fallback:float)->float:
 var band:int=-1
 for i in heights.size():
  if absf(p.y-float(heights[i]))<.1:band=i;break
 if band<0:return fallback
 var maximum:float=fallback
 for id:int in cells.get("%d,%d,%d"%[band,floori(p.x/8.),floori(p.z/8.)],[]):
  var t:Dictionary=triangles[id]
  if t.y>maximum and t.y<fallback+.065 and Geometry2D.is_point_in_polygon(Vector2(p.x,p.z),t.polygon):maximum=t.y
 return maximum
