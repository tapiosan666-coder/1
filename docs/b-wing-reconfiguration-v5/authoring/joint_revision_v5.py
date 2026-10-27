"""One deliberate three-parcel correction at the central operations island. No extra corridor or shop merger."""
from pathlib import Path
import sys,copy,math
sys.path.insert(0,str(Path(__file__).resolve().parent));from site_v2_common import *
from shapely.ops import linemerge
P=Path(__file__).resolve().parents[1];p=P/'source/design-v5.json';D=read(p)
if D.get('joint_central_revision_complete'):print('JOINT_REVISION_ALREADY_APPLIED');raise SystemExit(0)
f=D['floors'][2];ss={s['id']:s for s in f['stores']};s=ss['B3-046'];recipient=ss['B3-N01'];old_union=unary_union([s['polygon']for s in f['stores']]);right=s['polygon'].intersection(box(-491,-100,0,200));left=s['polygon'].difference(right)
assert left.geom_type=='Polygon'and recipient['polygon'].union(right).buffer(1e-8).buffer(-1e-8).geom_type=='Polygon'
s['polygon']=left;s['sales']=s['sales'].difference(right);recipient['polygon']=recipient['polygon'].union(right).buffer(1e-8).buffer(-1e-8);recipient['sales']=recipient['sales'].union(right).buffer(1e-8).buffer(-1e-8)
def net(q):return q['sales'].difference(q['polygon'].boundary.buffer(.12)).difference(q['backroom'].boundary.buffer(.1)).area
candidates=[]
for name in ['B3-037','B3-031','B3-N01','B3-041']:
 t=ss[name];line=s['polygon'].boundary.intersection(t['polygon'].buffer(.002));segments=lines(line)
 if not segments:continue
 merged=unary_union(segments);merged=merged if merged.geom_type=='LineString'else linemerge(merged)
 for ln in lines(merged):
  if ln.length>2:candidates.append((ln.length,t,ln))
fixed=False
for _,t,ln in sorted(candidates,key=lambda q:-q[0]):
 for depth in[.5,1,1.5,2,2.5,3,3.5,4,5]:
  patch=ln.buffer(depth,cap_style=2).intersection(t['sales']).difference(t['backroom'].buffer(.2)).difference(Point(t['entry']).buffer(2));a=s['polygon'].union(patch);b=t['polygon'].difference(patch)
  if a.geom_type!='Polygon'or b.geom_type!='Polygon':continue
  s0=copy.deepcopy(s);t0=copy.deepcopy(t);s0['polygon']=a;s0['sales']=s['sales'].union(patch);t0['polygon']=b;t0['sales']=t['sales'].difference(patch)
  if net(s0)<s['old_net_sales_m2']+2 or net(t0)<t.get('old_net_sales_m2',0)+4:continue
  s.update(s0);t.update(t0);fixed=True;D.setdefault('manual_architectural_revisions',[]).append({'ids':['B3-046','B3-N01',t['id']],'reason':'operations-room corner caused a sub-0.88m neck; transfer the entry alcove to the adjacent new unit and shift one shared wall to retain the existing sales programme','alcove_transferred_m2':right.area,'shared_wall_shift_m':depth,'programme_transfer_m2':patch.area,'new_corridor_added':False,'existing_shop_removed':False,'existing_sales_net_preserved':True});break
 if fixed:break
assert fixed,'No legitimate joint wall adjustment found'
original=read((Path(__file__).resolve().parents[1]/'source/baseline-v4.json'));o=next(q for q in original['floors'][2]['stores']if q['id']=='B3-046');s['entry']=o['entry'];s['u']=o['u'];s['n']=o['n'];
for q in[s,recipient,t]:q['net_sales_m2']=net(q)
assert old_union.symmetric_difference(unary_union([s['polygon']for s in f['stores']])).area<1e-4
for q in f['stores']:assert q['polygon'].buffer(.0001).covers(q['backroom'])and q['polygon'].buffer(.0001).covers(q['work_rectangle'])
D['joint_central_revision_complete']=True;write(p,D);print('JOINT_CENTRAL_REVISION',D['manual_architectural_revisions'],flush=True)
