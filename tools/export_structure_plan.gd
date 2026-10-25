extends SceneTree
## Export floor/map definitions, without generating or saving a 3D world.
func world_polygon(points:PackedVector2Array)->Array:
 var result:Array=[]
 for i in points.size():
  var steps:=maxi(1,ceili(points[i].distance_to(points[(i+1)%points.size()])/5.0))
  for step in steps:
   var p:Vector2=points[i].lerp(points[(i+1)%points.size()],float(step)/steps)
   var q:=MallCurve.world(Vector3(p.x,0,p.y));result.append([q.x,q.z])
 return result
func _initialize()->void:
 var floors:Array=[]
 for building in ["A","B","C"]:
  for level in [0,1,2]:
   if not MallLayout.floor_data(building,level).implemented:continue
   var f:={"building":building,"level":level,"base":[],"structure":[],"shops":[],"plazas":[]}
   for r:Rect2 in MallLayout.floor_data(building,level).regions:
    if r==MallStructure.bounds(building,level):continue
    f.base.append(world_polygon(PackedVector2Array([r.position,Vector2(r.end.x,r.position.y),r.end,Vector2(r.position.x,r.end.y)])))
   for p:Dictionary in MallStructure.floor_packets(building,level):
    var packet:={"outer":world_polygon(p.outer),"holes":[]}
    for hole:PackedVector2Array in p.holes:packet.holes.append(world_polygon(hole))
    f.structure.append(packet)
   for u:Dictionary in RetailDensity.units():
    if u.building!=building or u.level!=level or u.legacy=="counter":continue
    var points:=PackedVector2Array()
    for p in [Vector3(-u.half,0,-u.front),Vector3(u.half,0,-u.front),Vector3(u.half,0,-u.back),Vector3(-u.half,0,-u.back)]:
     var q:Vector3=u.t*p;points.append(Vector2(q.x,q.z))
    f.shops.append({"id":u.id,"kind":u.kind,"polygon":world_polygon(points)})
   if building=="A":f.private=world_polygon(PackedVector2Array([Vector2(-30,-36),Vector2(60,-36),Vector2(60,-24),Vector2(-30,-24)]))
   for plaza:Dictionary in MallStructureData.DATA[building].plazas:
    if building=="C" and level==1 and plaza.id=="terrace":continue
    var p:=MallCurve.world(Vector3(plaza.at[0],0,plaza.at[1]));f.plazas.append({"name":plaza.name,"at":[p.x,p.z]})
   if building in ["A","B"]:
    f.escalators=[]
    for bank:Dictionary in MallStructureData.DATA[building].escalator_banks:
     for lane in [0,1]:
      var x:float=bank.at[0]+bank.side*[13.5,16.5][lane]
      f.escalators.append({"up":lane==0,"points":world_polygon(PackedVector2Array([Vector2(x,bank.at[1]-6),Vector2(x,bank.at[1]+6)]))})
   if building=="B":
    f.destinations=[]
    for station:Dictionary in BConcourse.stations(level):f.destinations.append({"name":station.name,"at":[station.at.x,station.at.y]})
   if building=="C" and level in [0,1]:f.stairs=[[-382,-89],[-357,-89]]
   floors.append(f)
 var out:=FileAccess.open("res://docs/structure-floor-plans.json",FileAccess.WRITE);out.store_string(JSON.stringify(floors,"  "));out.close();print("FLOOR_PLAN_EXPORT ",floors.size());quit()
