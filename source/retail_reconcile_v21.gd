extends RefCounted
# Remove legacy MERCHANDISING inside selected sales, retaining floors, facade boundaries,
# backrooms, structural wall materials and ceiling equipment. Exact same volume selects physics.
static var ranges:Array=[]
static func in_retired_sales(p:Vector3,plan:Dictionary)->bool:
 var point=Vector2(p.x,p.z)
 for item:Dictionary in ranges:
  if p.y<item.y+.005 or p.y>item.y+2.65 or not item.bounds.has_point(point):continue
  if not Geometry2D.is_point_in_polygon(point,item.outer):continue
  var hole:bool=false
  for inner:PackedVector2Array in item.holes:
   if Geometry2D.is_point_in_polygon(point,inner):hole=true;break
  if not hole:return true
 return false
# Old v8 120mm display plinth proxies can outlive the retired GLB display.
# Keep structural floor materials; retire only this known fixture material inside selected sales.
static func low_plinth(p:Vector3,top:float,bottom:float,plan:Dictionary)->bool:
 for store:Dictionary in plan.stores:
  if bottom<float(store.height)-.002 or top>float(store.height)+.125:continue
  if in_retired_sales(p+Vector3.UP*.15,plan):return true
 return false
static func reconcile(geo:Dictionary,plan:Dictionary)->Dictionary:
 ranges=[]
 for store:Dictionary in plan.stores:
  var geom:Dictionary=store.sales_world;var polygons:Array=geom.coordinates if geom.type=="MultiPolygon"else[geom.coordinates]
  for rings:Array in polygons:
   var outer=PackedVector2Array();var holes:Array=[]
   for q:Array in rings[0]:outer.append(Vector2(q[0],q[1]))
   var inset:Array=Geometry2D.offset_polygon(outer,-.15)
   for polygon:PackedVector2Array in inset:
    var bounds=Rect2(polygon[0],Vector2.ZERO)
    for point:Vector2 in polygon:bounds=bounds.expand(point)
    for ring:Array in rings.slice(1):
     var h=PackedVector2Array()
     for q:Array in ring:h.append(Vector2(q[0],q[1]))
     holes.append(h)
    ranges.append({"outer":polygon,"holes":holes,"bounds":bounds,"y":float(store.height)})
 var removed_centres:Dictionary={}
 var safe_materials:Array=["oak","walnut","wood","metal","v8_oak","v8_bronze","v8_slate","v8_dark","v8_led","v10_darkstone","fabric_cream","fabric_dark","fabric_rust","leather"]
 var audit:Dictionary={"retired_display_triangles":0,"orphan_120mm_fixture_proxy_triangles":0,"retired_fixture_collision_triangles":0,"surfaces":[],"floor_wall_glass_materials_not_selected":true,"rule":"Explicit old fixture-material classes within selected inset sales and height range. Replaces brittle independently-triangulated centroid equality. Upholstery included; structural plaster/glass/floor classes excluded.","replacement_store_ids":plan.replacement_store_ids}
 for key:String in geo.surfaces.keys():
  var material:String=key.split("@@")[0];var group:String=key.split("@@")[-1]
  if not material in safe_materials:continue
  var selected:bool=group in plan.replacement_store_ids or ((group.begins_with("A")or group.begins_with("B")or group.begins_with("C"))and group.contains("-")and not group.begins_with("ARCH"))
  if not selected:
   for id:String in plan.replacement_store_ids:
    if group.contains(id)and (group.begins_with("V8")or group.begins_with("V9")or group.begins_with("V11-FIXTURE")or group.begins_with("V12")):selected=true
  if not selected:continue
  var d:Dictionary=geo.surfaces[key];var ids=PackedInt32Array()
  if d.has("i"):ids=d.i
  else:
   for i in range(d.v.size()/3):ids.append(i)
  var kept=PackedInt32Array();var removed:int=0
  for j in range(0,ids.size(),3):
   var centre=Vector3.ZERO
   for k in range(3):var t:int=ids[j+k]*3;centre+=Vector3(d.v[t],d.v[t+1],d.v[t+2])/3.
   if in_retired_sales(centre,plan):
    removed+=1;removed_centres[material+"|%d,%d,%d"%[round(centre.x*1000),round(centre.y*1000),round(centre.z*1000)]]=true
   else:
    for k in range(3):kept.append(ids[j+k])
  if removed:
   if kept.is_empty():geo.surfaces.erase(key)
   else:d.i=kept
   audit.retired_display_triangles+=removed;audit.surfaces.append({"key":key,"removed":removed})
 for material:String in geo.colliders.keys():
  if material not in["oak","walnut","wood","metal","v8_oak","v8_slate","v8_bronze","v8_dark","v8_led","v12_fixture_proxy","v10_oak","v10_darkstone","fabric_cream","fabric_dark","fabric_rust","leather"]:continue
  var data:PackedFloat32Array=geo.colliders[material];var kept=PackedFloat32Array();var removed:int=0
  for i in range(0,data.size(),9):
   var centre=Vector3.ZERO
   for j in range(3):centre+=Vector3(data[i+j*3],data[i+j*3+1],data[i+j*3+2])/3.
   var selected:bool=in_retired_sales(centre,plan)
   if not selected and material in["v8_slate","walnut","v10_darkstone"]:
    var bottom:float=minf(data[i+1],minf(data[i+4],data[i+7]));var top:float=maxf(data[i+1],maxf(data[i+4],data[i+7]))
    if low_plinth(centre,top,bottom,plan):selected=true;audit.orphan_120mm_fixture_proxy_triangles+=1
   if selected:removed+=1
   else:
    for j in range(9):kept.append(data[i+j])
  if kept.is_empty():geo.colliders.erase(material)
  else:geo.colliders[material]=kept
  audit.retired_fixture_collision_triangles+=removed
 return audit
