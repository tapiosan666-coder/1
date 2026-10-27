"""Actual Godot context mesh for roof, underground shell and bridge landings. Orange structure is an unengineered reservation."""
from pathlib import Path
import sys,math,gzip,json,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent));from site_v2_common import *
from shapely import constrained_delaunay_triangles
P=Path(__file__).resolve().parents[1];D=read(P/'source/design-v6.json');A=read(P/'source/annex-v6.json');site=read(P/'source/master-site-v3.json');pedbridge=next(q for q in site['site']['bridges']if q['id']=='BR-PBS-RF-PED');M={};coll={};ORIGIN=(-429,46);CROP=box(-1000,-500,100,400);render_group='CONTEXT';signs=[]
def pos(x,y,z):return[round(x+429,5),round(y,5),round(z-46,5)]
exec((P/'authoring/mesh_primitives.py').read_text())
rf=A['roof'];b1=A['basement'];render_group='CONTEXT-RF';extrude(rf['floor_plate'],16.02,.38,'dark_stone',True)
# Road and markings are surfaces, with actual solid deck below.
surf(rf['parking']['vehicle_aisles'],16.405,'black',True,False);surf(rf['parking']['protected_pedestrian'],16.409,'retail_terrazzo',True,False)
for stall in rf['parking']['stalls']:
 for line in lines(stall['polygon'].boundary):extrude(line.buffer(.035,cap_style=2),16.415,.006,'paper',False)
for q in rf['gardens']:surf(q['polygon'],16.408,'retail_terrazzo',True,False)
for q in rf.get('plant_beds',[]):
 extrude(q['polygon'],16.4,.42,'dark_stone',True);cc=q['polygon'].centroid;cylinder((cc.x,cc.y),16.82,.55,.8,'leaf',8,False)
# Skylight guard prevents an accidental walk onto the non-walkable glass.
extrude(rf['void'].boundary.buffer(.045),16.4,1.1,'metal',True)
# Add only the skylight difference; the main atrium already owns its glass roof.
surf(rf['void'].difference(D['floors'][2]['void']),16.4,'roof_glass',True,False)
for c in rf['cores']:
 e=c['entry'];u=[math.cos(math.radians(c['angle'])),math.sin(math.radians(c['angle']))];walls=c['outline'].boundary.buffer(.12).difference(rect(e,u,3.6,.8));extrude(walls,16.4,2.8,'plaster',True)
 # Existing shaft rooms are diagnostic enclosures, not working elevators.
 for v in c.get('doors',[]):
  if v['id']in['EV','ST']:extrude(rect(v['p'],v['axis'],v['w'],.08),16.4,2.2,'metal',True)
# Representative HVAC pads only within retained equipment programme; no claimed capacity.
count=0
for zone in rf['equipment_zones']:
 if not zone.get('accessible_room')or zone['polygon'].is_empty:continue
 g=zone['polygon'].buffer(-1)
 if g.is_empty:continue
 x0,z0,x1,z1=g.bounds
 for x in np.arange(x0,x1,12):
  for z in np.arange(z0,z1,12):
   fp=rect((x,z),(1,0),3.2,1.5)
   if g.covers(fp)and count<24:extrude(fp,16.4,1.2,'metal',True);count+=1
# Source RF car bridge has flat level16.4: the parking structure ramp itself is outside this scene.
site=read(P/'source/master-site-v3.json');bridge=site['site']['roof_car_bridge'];extrude(bridge['polygon'],16.02,.38,'dark_stone',True);surf(bridge['polygon'],16.407,'black',True,False)
# Existing source pedestrian roof bridge, distinct from the car bridge.
pedbridge=next(q for q in site['site']['bridges']if q['id']=='BR-PBS-RF-PED');extrude(pedbridge['polygon'],16.02,.38,'stone',True)
# Generate one exterior parapet for the connected deck, never barriers at internal slab/bridge joints.
connected=rf['floor_plate'].union(bridge['polygon']).union(pedbridge['polygon'])
for po in polys(connected):extrude(LineString(po.exterior.coords).buffer(.06),16.4,1.15,'plaster',True)
# Original B1 remains a wider basement; exterior grade is a waterproofed basement roof, not a new customer corridor.
render_group='CONTEXT-B1';extrude(b1['floor_plate'],-5.73,.38,'stone',True);extrude(b1['shell'].boundary.buffer(.15),-5.35,5.0,'plaster',True);extrude(b1['above_basement_grade_cover'],-.38,.38,'plaster',True)
for s in b1['stores']:
 e=s['entry'];u=s['u'];walls=s['polygon'].boundary.buffer(.12);cut=rect(e,u,3.6,.8);extrude(walls.difference(cut),-5.35,4.5,'wall_sand',True);extrude(walls.intersection(cut),-2.15,1.3,'wall_sand',True)
# Only the proposed support reserves are orange; no claim of structural safety.
render_group='CONTEXT-UNENGINEERED-FRAMES'
for q in A['support_reservations']:
 pts=q['column_centres']
 for x,z in pts:extrude(box(x-.225,z-.225,x+.225,z+.225),-5.35,21.0,'goods_rust',True)
 if len(pts)>=2:bar(pts[0],pts[1],.55,15.65,.75,'goods_rust',True)
# Bridges keep source widths/heights; landings are actual clipped A/C public floor, not invented rooms.
for c in A['connections']:
 render_group='CONTEXT-'+c['id'];y=c['height'];extrude(c['landing'],y-.38,.38,'stone',True)
 tube=c['polygon'];start=Point(c['world_route'][0]);end=Point(c['world_route'][-1]);env=D['floors'][c['level']]['shell'];edges=tube.boundary.difference(start.buffer(c['width_m']+1)).difference(end.buffer(c['width_m']+.5)).difference(env.buffer(.15))
 for ln in lines(edges):extrude(ln.buffer(.035),y,1.1,'glass',True);extrude(ln.buffer(.06),y+1.08,.05,'metal',False)
meta={'scope':'RF/B1 diagnostic context and actual terminal patches only','roof_stalls':115,'mechanical_units_visual_proxies':count,'structural_capacity_verified':False,'basement_full_fitout_complete':False,'other_wings_complete':False,'collision_triangles':sum(len(v)//9 for v in coll.values())}
with gzip.open(P/'assets/context.json.gz','wt',encoding='utf8',compresslevel=6)as f:json.dump({'surfaces':M,'colliders':coll,'lights':[],'signs':[]},f,separators=(',',':'))
write(P/'source/context-manifest.json',meta);print('CONTEXT_MODEL',meta)
