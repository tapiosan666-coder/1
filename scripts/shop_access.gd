class_name ShopAccess
extends RefCounted
## Readable storefronts and continuous fascia caps; openings stay physically open.
static func build(mall:Node3D)->void:
 var frame:=Shapes.material(Color("657c7b"));var stripe:=Shapes.material(Color("b6c9c6"));var fascia:=MallFinishes.plaster(Color("ddd9ce"));var floor_mat:=MallFinishes.stone()
 var count:=0
 for unit:Dictionary in RetailDensity.units():
  if unit.building not in ["A","B"] or unit.legacy not in ["a","b","upper","new"]:continue
  var t:Transform3D=unit.t;var half:float=unit.half;var front:float=unit.front
  var entry:float=6.0 if unit.legacy in ["a","b"] else TenantCatalog.entry_width(unit.kind)
  if unit.legacy=="new":entry=16.0
  var group:=Node3D.new();mall.add_child(group);group.transform=t
  for side in [-1,1]:
   var w:float=half-entry*.5;var x:float=side*(entry*.5+w*.5)
   for y in [1.05,1.2]:Shapes.box(group,Vector3(x,y,-front+.04),Vector3(w,.055,.06),stripe)
   Shapes.box(group,Vector3(side*(entry*.5+.06),1.9,-front),Vector3(.12,3.8,.24),frame)
   var depth:float=unit.back-front
   Shapes.box(group,Vector3(side*(half-.10),4.98,-front-depth*.5),Vector3(.25,.70,depth+.25),fascia,true)
  Shapes.box(group,Vector3(0,4.98,-front),Vector3(half*2,.70,.28),fascia,true)
  Shapes.box(group,Vector3(0,4.98,-unit.back),Vector3(half*2,.70,.28),fascia,true)
  # Separate curved slabs can use different edge chords. A continuous underlap
  # closes their millimetre-scale seams across the whole facade, not just the door.
  Shapes.box(group,Vector3(0,-.187,-front),Vector3(half*2+.15,.35,1.5),floor_mat,true)
  Shapes.box(group,Vector3(0,.015,-front),Vector3(entry,.025,1.3),floor_mat)
  var label:=Shapes.sign_text(group,Vector3(0,3.45,-front+.18),"入口  /  OPEN",28,Color("e7eee4"));label.pixel_size=.004;label.shaded=false
  Shapes.box(group,Vector3(0,3.45,-front+.10),Vector3(2.1,.38,.06),frame)
  count+=1
 mall.set_meta("shop_access",{"marked_entrances":count,"glass_alpha":.23,"upper_wall_caps":true})
