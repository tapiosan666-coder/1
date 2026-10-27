"""2F 1.5m-wide repeated-body strip is exterior roof, not a disconnected shop annex; retain old sales budget with one shared wall shift."""
from pathlib import Path
import sys,copy,shapely
sys.path.insert(0,str(Path(__file__).resolve().parent));from site_v2_common import *
P=Path(__file__).resolve().parents[1];p=P/'source/design-v5.json';D=read(p)
if D.get('bridge_edge_fixed'):raise SystemExit
f=D['floors'][1];ss={s['id']:s for s in f['stores']};s=ss['B2-062'];t=ss['B2-057'];main=max(polys(s['polygon']),key=lambda g:g.area);removed=s['polygon'].difference(main)
def net(s):return s['sales'].difference(s['polygon'].boundary.buffer(.12)).difference(s['backroom'].boundary.buffer(.1)).area
s['polygon']=main;s['sales']=main.difference(s['backroom']);shared=main.boundary.intersection(t['polygon'].buffer(.003));found=False
for dep in[.3,.5,.7,.9,1.1,1.3,1.5,1.7,2,2.5,3]:
 patch=shared.buffer(dep,cap_style=2).intersection(t['sales']).difference(t['backroom'].buffer(.2)).difference(Point(t['entry']).buffer(2));a=copy.copy(s);b=copy.copy(t);a['polygon']=main.union(patch).buffer(1e-8).buffer(-1e-8);a['sales']=a['polygon'].difference(a['backroom']);b['polygon']=t['polygon'].difference(patch);b['sales']=b['polygon'].difference(b['backroom'])
 if len([q for q in polys(a['polygon'])if q.area>1e-5])!=1 or len([q for q in polys(b['polygon'])if q.area>1e-5])!=1:continue
 if net(a)<s['old_net_sales_m2']+.3 or net(b)<t['old_net_sales_m2']+.3:continue
 s.update(a);t.update(b);found=True;break
assert found,'Need a real local wall revision, not a phantom annex'
f['floor_plate']=f['floor_plate'].difference(removed);f['building_envelope_v5']=f['building_envelope_v5'].difference(removed);f['per_level_external_floor_cuts']=f['per_level_external_floor_cuts'].union(removed);f['slab_removed_v5']=f['old_floor_plate'].difference(f['floor_plate']);f['slab_added_v5']=f['floor_plate'].difference(f['old_floor_plate']);occ=Polygon()
for q in f['floor_roles']:
 g=unary_union([q['polygon']for q in f['stores']])if q['role']=='店舗区画'else q['polygon'];g=unary_union(polys(g.intersection(f['floor_plate'])));q['polygon']=shapely.difference(g,occ,grid_size=1e-7);q['area_m2']=q['polygon'].area;occ=unary_union([occ,q['polygon']])
D['bridge_edge_fixed']={'id':'B2-062','detached_1_5m_strip_externalized_m2':removed.area,'neighbour':'B2-057','shared_wall_shift_m':dep,'retail_area_transfer_m2':patch.area,'old_sales_budget_preserved':True};write(p,D);print('BRIDGE_EDGE_FIX',D['bridge_edge_fixed'])
