"""Restore source-declared service rooms/doors, not new circulation or moved equipment."""
import math
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from coordinate_roles_v4 import correct_service

def build(f,crop,meta,pos,extrude,rect,bar,routing_solids):
 lev=f['level'];y=f['height'];top=[5.525,10.875,16.4][lev];clear=top-y-.7
 for zone in f.get('service_zones',[]):
  correct_service(zone);poly=zone['polygon'];part=poly.intersection(crop)
  if part.is_empty:continue
  door=Point(zone['entry']);u=tuple(zone['u']);n=(-u[1],u[0]);inside=poly.covers(Point(door.x+n[0]*.3,door.y+n[1]*.3))
  if not inside:n=(-n[0],-n[1])
  available=crop.buffer(-1).covers(door)and poly.boundary.distance(door)<.01
  if not available:
   # Do not invent a side entrance for a room clipped away from its source door.
   extrude(part,y,clear,'plaster',True);routing_solids[lev].append(part);meta.setdefault('service_rooms_v4',[]).append({'id':zone['id'],'status':'clipped proxy retained; source door outside validation crop','level':lev,'door_world':zone['entry']});continue
  width=zone['door_width_m'];opening=rect(zone['entry'],u,width,.9);full=poly.boundary.buffer(.12).intersection(crop);wall=full.difference(opening)
  extrude(wall,y,clear,'plaster',True);routing_solids[lev].append(wall)
  extrude(full.intersection(opening),y+2.218,clear-2.218,'plaster',True)
  meta['staff_doors'].append({'id':zone['id']+'-SERVICE','store':zone['id'],'level':lev,'p':pos(door.x,y,door.y),'u':u,'n':n,'clear_width_m':width,'leaf_width_m':width-.006,'height_m':2.2,'source':'existing service-zone entry; explicit local-to-world metadata correction','service_room':True,'room_label':zone['name']+' / '+zone['id']})
  path=LineString(zone['main_route']);reserved=path.buffer(.8,cap_style=2);racks=[]
  # Source warehouse and maintenance-room roles remain distinct. Provisional equipment, no capacity claim.
  c0,c1,c2,c3=poly.bounds
  for xx in range(math.ceil(c0+2),math.floor(c2-2),4):
   for zz in range(math.ceil(c1+2),math.floor(c3-2),4):
    footprint=rect((xx,zz),u,2.4,.6)
    if not poly.buffer(-.5).covers(footprint)or footprint.intersects(reserved)or not crop.buffer(.6).covers(footprint):continue
    if len(racks)>=10:break
    racks.append(footprint);extrude(footprint,y,.10,'metal',True)
    for h in[.7,1.35,1.95]:
     extrude(footprint,y+h,.045,'metal',True)
     for aa in[-.75,0,.75]:
      c=(xx+u[0]*aa,zz+u[1]*aa);b=rect(c,u,.52,.48);extrude(b,y+h+.05,.38,'wood',False)
    for aa in[-1.14,1.14]:
     for bb in[-.26,.26]:
      p=(xx+u[0]*aa+n[0]*bb,zz+u[1]*aa+n[1]*bb);extrude(rect(p,u,.045,.045),y,2.1,'metal',True)
  # Keep actual equipment footprints in routing solids; do not count decorative boxes as structural.
  routing_solids[lev].extend(racks)
  meta.setdefault('service_rooms_v4',[]).append({'id':zone['id'],'name':zone['name'],'level':lev,'status':'existing source room restored as hollow service room; not a public shortcut','door_world':zone['entry'],'door_width_m':width,'entry_inside_world_boundary_error_m':poly.boundary.distance(door),'polygon':poly,'reserved_staff_route':path,'rack_footprints':racks,'route_width_m':1.6,'equipment_status':'provisional rack placement; no stock allocation, operational capacity or hygiene certification','public_geometry_changed':False})
