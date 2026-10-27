"""Local B1/RF/bridge consistency proposals, no master-site or game writes. Structural reservations are NOT capacity calculations."""
from pathlib import Path
import sys,math,copy,csv
sys.path.insert(0,str(Path(__file__).resolve().parent));from site_v2_common import *
import numpy as np,shapely
P=Path(__file__).resolve().parents[1];D=read(P/'source/design-v6.json');site=read(P/'source/master-site-v3.json');b1=copy.deepcopy(next(f for f in site['floors']if f['wing']=='B'and f['label']=='B1'));rf=copy.deepcopy(next(f for f in site['floors']if f['wing']=='B'and f['label']=='RF'));connections=[]
vehicle=read(P/'source/vehicle-sweep-v6.json');rf['parking']['vehicle_aisles']=vehicle['new_roof_vehicle_aisles']
for f in D['floors']:
 for c in f['connectors']:
  pts=[(q[0]-714,q[1]-30)for q in c['route']];target='A'if c['id'].startswith('AB')else'C';other=next(g for g in site['floors']if g['wing']==target and g['label']==f['label']);tube=LineString(pts).buffer(c['width']/2,cap_style=2,join_style=2);landing=other['public'].intersection(Point(pts[-1]).buffer(8));joint_added=tube.difference(f['floor_plate']);f['public']=f['public'].union(tube);f['floor_plate']=f['floor_plate'].union(tube).difference(f['floor_openings_v5']);f['building_envelope_v5']=f['building_envelope_v5'].union(tube)
  connections.append({'id':c['id'],'target':target,'level':f['level'],'height':f['height'],'target_height':other['height'],'width_m':c['width'],'world_route':pts,'polygon':tube,'landing':landing,'joint_addition_m2':joint_added.area,'target_entry':pts[-1],'scope':'Bridge and a clipped actual target-public landing only; other-wing interior not built','height_error_m':abs(f['height']-other['height']),'floor_before_missing_m2':tube.difference(read(P/'source/baseline-v5.json')['floors'][f['level']]['floor_plate'].union(other['floor_plate'])).area})
# Trim only the roof equipment overhang, keep the real parking/roads/pedestrian facilities.
env=D['floors'][2]['building_envelope_v5'];oldrf=rf['floor_plate'];mandatory=unary_union([rf['parking']['vehicle_aisles'],rf['parking']['protected_pedestrian'],*[s['polygon']for s in rf['parking']['stalls']],*[q['polygon']for q in rf['gardens']],*[q['outline']for q in rf['cores']]]);keep=env.union(mandatory.buffer(.35,join_style=2));rf['floor_plate']=oldrf.intersection(keep);rf['shell']=rf['shell'].intersection(keep);rf['removed_slab']=oldrf.difference(rf['floor_plate']);rf['equipment_zones']=[{**q,'polygon':q['polygon'].intersection(rf['floor_plate'])}for q in rf['program']];rf['overhang']=rf['floor_plate'].difference(env);reserves=[];unplaced=[]
# Clear exterior support reservations, not a fabricated engineering PASS.
upper=unary_union([f['shell']for f in D['floors']]);forbidden=b1['public'].union(unary_union([q['outline']for q in b1['cores']]+[s['polygon']for s in b1['stores']])).buffer(.35);safe=b1['floor_plate'].buffer(-.5).difference(upper.buffer(.35)).difference(forbidden)
for i,patch in enumerate(sorted([g for g in polys(rf['overhang'])if g.area>.03],key=lambda g:-g.area),1):
 area=patch.buffer(3).intersection(safe);pts=[]
 if not area.is_empty:
  x0,z0,x1,z1=area.bounds
  for x in np.arange(x0,x1,.7):
   for z in np.arange(z0,z1,.7):
    fp=box(x-.225,z-.225,x+.225,z+.225)
    if area.covers(fp):pts.append((Point(x,z).distance(patch.representative_point()),[float(x),float(z)]))
 chosen=[]
 for _,point in sorted(pts):
  if all(math.dist(point,q)>2.4 for q in chosen):chosen.append(point)
  if len(chosen)>=2:break
 if len(chosen)<2:
  private_protected=unary_union([f['public'].buffer(.4)for f in D['floors']]+[s['work_rectangle'].buffer(.4)for f in D['floors']for s in f['stores']]+[LineString(s['main_route']).buffer(.7)for f in D['floors']for s in f['stores']]+[Point(s['entry']).buffer(2)for f in D['floors']for s in f['stores']]);wall_reserve=env.boundary.buffer(.7).intersection(b1['floor_plate'].buffer(-.5)).difference(forbidden).difference(private_protected).intersection(patch.buffer(6));candidates=[]
  if not wall_reserve.is_empty:
   ax,az,bx,bz=wall_reserve.bounds
   for xx in np.arange(ax,bx,.4):
    for zz in np.arange(az,bz,.4):
     if wall_reserve.covers(box(xx-.225,zz-.225,xx+.225,zz+.225)):candidates.append((Point(xx,zz).distance(patch.representative_point()),[float(xx),float(zz)]))
  for _,point in sorted(candidates):
   if all(math.dist(point,q)>2.4 for q in chosen):chosen.append(point)
   if len(chosen)>=2:break
 r={'id':f'RF-SUPPORT-{i:02}','polygon':patch,'area_m2':patch.area,'column_centres':chosen,'column_size_m':[.45,.45],'base_y':-5.35,'beam_underside_y':15.65,'beam_depth_m':.75,'geometry_clear_of_customer_and_store_basement':len(chosen)>=2,'capacity_verified':False,'foundation_verified':False,'status':'game-scale support reservation, requires structural engineer / foundation / wind / seismic / vehicle load design'};reserves.append(r)
 depth=max([Point(q).distance(env)for po in polys(patch)for q in po.exterior.coords],default=0);r['maximum_overhang_depth_m']=depth
 if len(chosen)<2 and depth<=.65:r['alternative']='edge-beam / short corbel reservation, no capacity calculation';r['geometry_clear_of_customer_and_store_basement']=True
 elif len(chosen)<2:unplaced.append(r['id'])
b1['above_basement_grade_cover']=b1['floor_plate'].difference(D['floors'][0]['building_envelope_v5']);b1['grade_cover_status']='retain underground footprint; weatherproof roof/backfill outside revised retail facade; soil/waterproof/load design not verified'
# Refresh final roles from real geometry; the bridge has its named customer purpose.
for f in D['floors']:
 zones=[('設備核',unary_union([c['outline']for c in f['cores']])),('機器・手すり支持',unary_union([q['polygon']for q in f.get('machine_islands',[])]).union(f['void'].buffer(.28).difference(f['void']))),('店舗区画',unary_union([s['polygon']for s in f['stores']])),('運営・共用在庫',unary_union([s['polygon']for s in f['service_zones']])),('共用・避難',f['public'].union(f.get('egress',Polygon())))];occupied=Polygon();role=[]
 for name,g in zones:
  gg=unary_union(polys(g.intersection(f['floor_plate']).difference(occupied)));role.append({'role':name,'polygon':gg,'area_m2':gg.area,'purpose':'retained v5 programme with explicit v6 corner/bridge changes'});occupied=occupied.union(gg)
 left=f['floor_plate'].difference(occupied);walls=unary_union([f.get('construction_poche',Polygon()),*[s['polygon'].boundary.buffer(.13)for s in f['stores']]]+[z['polygon'].boundary.buffer(.13)for z in f['service_zones']]+[f['shell'].boundary.buffer(.13),f['building_envelope_v5'].boundary.buffer(.13),*[c['outline'].boundary.buffer(.13)for c in f['cores']]])
 unexpected=left.difference(walls.buffer(.002));print('ROLE_JOIN',f['label'],'left',left.area,'not_wall',unexpected.area,flush=True)
 role.append({'role':'壁・構造納まり','polygon':left,'area_m2':left.area,'purpose':'actual wall footprint / final numerical seam only; not a new room'});f['floor_roles']=role
D['v6_status']='local independent proposal; main game and original drawings unchanged';write(P/'source/design-v6.json',D)
A={'basement':b1,'roof':rf,'connections':connections,'support_reservations':reserves,'unplaced_support_reservations':unplaced,'old_roof_slab_m2':oldrf.area,'new_roof_slab_m2':rf['floor_plate'].area,'removed_roof_slab_m2':rf['removed_slab'].area,'remaining_roof_overhang_m2':rf['overhang'].area,'parking_stalls':len(rf['parking']['stalls']),'structural_capacity_verified':False,'roof_equipment_capacity_verified':False,'source_sha256':sha(P/'source/master-site-v3.json')};write(P/'source/annex-v6.json',A);print('ANNEX',A['removed_roof_slab_m2'],'removed',A['remaining_roof_overhang_m2'],'supported proposal areas','unplaced',unplaced,flush=True)
