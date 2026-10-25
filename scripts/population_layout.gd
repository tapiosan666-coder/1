class_name PopulationLayout
extends RefCounted
## Additional identities use the existing connected floor samples; no geometry
## or true-ID random draw is changed. The 300-person regression layout is frozen.
const DEFAULT_COUNT:=1000
const WALKERS:=100
const BUILDING_TOTALS:={"A":300,"B":450,"C":150}
static var cached:Array[Dictionary]=[]
static var occupied:Dictionary={}
static func slots(mall:Node3D,count:int)->Array[Dictionary]:
 if count!=DEFAULT_COUNT:
  var original:Array[Dictionary]=[];original.assign(mall.identity_slots.slice(0,mini(mall.identity_slots.size(),maxi(0,count-12))));return original
 if not cached.is_empty():return cached.duplicate(true)
 occupied.clear()
 var result:Array[Dictionary]=[];result.assign(mall.identity_slots.duplicate(true))
 var present:={"A":0,"B":0,"C":0}
 for slot:Dictionary in result:
  _occupy(slot.pos)
  var building:=MallLayout.floor_at(slot.pos).get_slice("/",0)
  assert(present.has(building),"Original identity must belong to a public building")
  present[building]+=1
 # Keep teleport landings and the initial player spawn clear.
 var hubs:Array[Vector3]=[]
 for hub:Dictionary in MallLayout.travel_points():hubs.append(hub.position)
 var shop_pools:={"A":[],"B":[],"C":[]};var public_pools:={"A":[],"B":[],"C":[]};var by_level:={}
 for unit:Dictionary in RetailDensity.units():
  if unit.legacy=="counter":continue
  var pool:Array[Dictionary]=[];var info:={"unit":unit,"inverse":unit.t.affine_inverse(),"pool":pool,"cursor":0}
  if not by_level.has(unit.level):by_level[unit.level]=[]
  by_level[unit.level].append(info);shop_pools[unit.building].append(info)
 for point:Vector3 in mall.spawn_points:
  var reserved:=false
  for hub:Vector3 in hubs:
   if point.distance_squared_to(hub)<5.76:reserved=true;break
  if reserved:continue
  var plan:=MallCurve.plan(point);var level:=Mall.level_at(point.y);var owner:=""
  for info:Dictionary in by_level.get(level,[]):
   var unit:Dictionary=info.unit;var q:Vector3=info.inverse*plan
   if absf(q.x)>unit.half-.85 or -q.z<unit.front+1.3 or -q.z>unit.back-1.0:continue
   var direction:Vector3=unit.t.basis*Vector3(-signf(q.x),0,0) if absf(q.x)>unit.half*.65 else -unit.t.basis.z
   info.pool.append({"pos":point,"yaw":atan2(-direction.x,-direction.z),"role":"browsing","activity":"book" if unit.kind=="books" else "inspect"})
   owner=unit.building;break
  if owner.is_empty():
   owner=MallLayout.floor_at(point).get_slice("/",0)
   if public_pools.has(owner):public_pools[owner].append({"pos":point,"yaw":fposmod(float(hash(point)),TAU),"role":"resting","activity":"resting"})
 for building:String in BUILDING_TOTALS:
  var needed:int=BUILDING_TOTALS[building]-present[building]
  # Shop pools are interleaved so a long first store cannot absorb the crowd.
  for info:Dictionary in shop_pools[building]:info.pool.sort_custom(_ordered)
  public_pools[building].sort_custom(_ordered)
  var shop_goal:=roundi(needed*.75);var added:=0;var progress:=true
  while added<shop_goal and progress:
   progress=false
   for info:Dictionary in shop_pools[building]:
    while info.cursor<info.pool.size():
     var slot:Dictionary=info.pool[info.cursor];info.cursor+=1
     if not _space(slot.pos):continue
     result.append(slot);_occupy(slot.pos);added+=1;progress=true;break
    if added>=shop_goal:break
  for slot:Dictionary in public_pools[building]:
   if added>=needed:break
   if not _space(slot.pos):continue
   result.append(slot);_occupy(slot.pos);added+=1
  if added<needed:
   for info:Dictionary in shop_pools[building]:
    for slot:Dictionary in info.pool:
     if added>=needed:break
     if _space(slot.pos):result.append(slot);_occupy(slot.pos);added+=1
  assert(added==needed,"Connected floor has insufficient spaced population samples: "+building)
 assert(result.size()==DEFAULT_COUNT-WALKERS,"Trial population has 900 fixed identities and 100 walking identities")
 cached=result.duplicate(true);occupied.clear();return result
static func _ordered(a:Dictionary,b:Dictionary)->bool:return hash(a.pos)<hash(b.pos)
static func _cell(at:Vector3)->Vector3i:return Vector3i(floori(at.x/2),Mall.level_at(at.y),floori(at.z/2))
static func _occupy(at:Vector3)->void:
 var cell:=_cell(at)
 if not occupied.has(cell):occupied[cell]=[]
 occupied[cell].append(at)
static func _space(at:Vector3)->bool:
 var cell:=_cell(at)
 for x in [-1,0,1]:
  for z in [-1,0,1]:
   for other:Vector3 in occupied.get(cell+Vector3i(x,0,z),[]):
    if at.distance_squared_to(other)<2.56:return false
 return true
