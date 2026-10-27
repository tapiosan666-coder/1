"""Delete non-occupiable sub-6mm tenant boundary needles at source; explicit actual wall joints, never a warehouse or passage."""
from pathlib import Path
import sys,shapely
sys.path.insert(0,str(Path(__file__).resolve().parent));from site_v2_common import *
P=Path(__file__).resolve().parents[1];p=P/'source/design-v5.json';D=read(p)
if D.get('thin_boundary_source_repair'):print('ALREADY_REPAIRED');raise SystemExit
changes=[]
for f in D['floors']:
 repair=Polygon()
 for s in f['stores']:
  original=s['polygon'];smooth=original.buffer(-.003,join_style=2).buffer(.003,join_style=2).intersection(original);smooth=unary_union([g for g in polys(smooth)if g.area>.00001]);strip=original.difference(smooth)
  assert strip.area<.15,(s['id'],strip.area)
  if strip.area>1e-9:
   changes.append({'id':s['id'],'removed_sub6mm_spike_m2':strip.area,'reason':'collapsed Boolean boundary, not usable tenant floor; join belongs to actual party-wall footprint'});s['polygon']=smooth;s['backroom']=s['backroom'].intersection(smooth);s['sales']=smooth.difference(s['backroom']);repair=repair.union(strip)
 # Actual construction joint uses same store perimeter, bounded below 6mm, no room or route added.
 occupied=Polygon()
 for q in f['floor_roles']:
  if q['role']=='店舗区画':g=unary_union([s['polygon']for s in f['stores']])
  elif q['role']=='壁・構造納まり':g=q['polygon'].union(repair)
  else:g=q['polygon']
  q['polygon']=shapely.difference(unary_union(polys(g.intersection(f['floor_plate']))),unary_union(polys(occupied)),grid_size=1e-7);q['area_m2']=q['polygon'].area;occupied=shapely.union(occupied,q['polygon'],grid_size=1e-7)
 f['thin_boundary_joints']=repair
D['thin_boundary_source_repair']={'opening_radius_m':.003,'total_reclassified_m2':sum(q['removed_sub6mm_spike_m2']for q in changes),'changes':changes};write(p,D);print('THIN_SOURCE_REPAIR',D['thin_boundary_source_repair']['total_reclassified_m2'],len(changes))
