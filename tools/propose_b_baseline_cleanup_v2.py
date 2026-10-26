"""Unapplied minimum-boundary fixes for newly discovered immutable v4.1 issues."""
from site_v2_common import *
import copy
from shapely.strtree import STRtree
O=R/'docs/site-completion-v2';B=read(R/'docs/b-v4-overlap-correction/geometry.json');OLD=read(O/'independent-verification.json');PRO=[];TEST=[]
for raw in B['floors']:
 f=floor_B_world(raw,[core_world(c)for c in B['cores']]);old=copy.deepcopy(f);public=f['public'];patches=[]
 for st in f['stores']:
  ep=Point(st['entry']);front=nearest_points(st['polygon'].difference(public).boundary,ep)[0];n=st['n'];probe=Point(front.x+n[0]*.05,front.y+n[1]*.05)
  if not st['polygon'].covers(probe):n=[-n[0],-n[1]]
  inside=[front.x+n[0]*.0002,front.y+n[1]*.0002];gap=public.distance(front);outside=[front.x-n[0]*(gap+.001),front.y-n[1]*(gap+.001)];mid=((inside[0]+outside[0])/2,(inside[1]+outside[1])/2);length=math.dist(inside,outside);patch=rect(mid,n,length,st['door_width_m']);st['proposed_door_target']=inside
  patches.append(dict(id=st['id'],polygon=patch,distance_m=ep.distance(public),old_entry=st['entry']))
 public=public.union(unary_union([q['polygon']for q in patches]));assigned=Polygon();delta=[]
 for st,orig in zip(f['stores'],old['stores']):
  new=st['polygon'].difference(public.union(assigned));assigned=assigned.union(new);change=st['polygon'].symmetric_difference(new);delta.append(dict(id=st['id'],old_area_m2=st['polygon'].area,new_area_m2=new.area,changed_m2=change.area,removed=change,entry_kept=True));st['polygon']=new
  q=nearest_points(new.boundary,Point(st['proposed_door_target']))[0]
  delta[-1].update(old_entry=st['entry'],proposed_entry=list(q.coords[0]),entry_displacement_m=q.distance(Point(st['entry'])),entry_kept=q.distance(Point(st['entry']))<1e-8);st['entry']=list(q.coords[0])
  for k in['backroom','sales','shelf_zones','aisles','wall_solids']:
   if k in st:st[k]=st[k].intersection(new)
 f['public']=public;prs=[s['polygon']for s in f['stores']];tree=STRtree(prs);pairs=[]
 for i,p in enumerate(prs):
  for j in tree.query(p):
   if j<=i:continue
   area=p.intersection(prs[j]).area
   if area>EPS:pairs.append([f['stores'][i]['id'],f['stores'][j]['id'],area])
 pu=public.intersection(unary_union(prs)).area;entry_bad=[s['id']for s in f['stores']if public.distance(Point(s['entry']))>EPS or s['polygon'].distance(Point(s['entry']))>EPS]
 TEST.extend([dict(id=f['label']+'-store-pair',pass_=not pairs,value=pairs),dict(id=f['label']+'-public-store',pass_=pu<EPS,value_m2=pu),dict(id=f['label']+'-entry',pass_=not entry_bad,value=entry_bad)])
 oldpairs=[]
 for q in OLD['failed']:
  if q['kind']=='stores_do_not_overlap'and q['id'].startswith('B'+str(raw['floor'])+'-'):oldpairs.append(q)
 PRO.append(dict(id='B-v4.1-local-cleanup-'+f['label'],floor=f['level'],height=f['height'],status='UNAPPLIED_PROPOSAL_ONLY',source_sha256=sha(R/'docs/b-v4-overlap-correction/geometry.json'),source_modified=False,public_before=old['public'],public_proposed=public,stores_before=[dict(id=s['id'],polygon=s['polygon'],entry=s['entry'])for s in old['stores']],stores_proposed=[dict(id=s['id'],polygon=s['polygon'],entry=s['entry'])for s in f['stores']],entrance_gap_patches=patches,store_boundary_changes=delta,proposed_public_infill_m2=public.difference(old['public']).area,old_public_store_overlap_m2=old['public'].intersection(unary_union([s['polygon']for s in old['stores']])).area,old_pair_overlap_items=oldpairs,aggregate_unit_removed_m2=sum(q['changed_m2']for q in delta),no_new_route_or_store=True))
write(O/'B-v4.1-local-cleanup-UNAPPLIED.json',PRO);write(O/'B-v4.1-local-cleanup-proposal-checks.json',TEST)
csvwrite(O/'B-v4.1-local-cleanup-proposal-ledger.csv',['提案','階','旧店舗共用重複㎡','旧店舗間重複件数','入口床局所充填㎡','店舗境界除去合計㎡','原本適用'],[[p['id'],LABEL[p['floor']],p['old_public_store_overlap_m2'],len(p['old_pair_overlap_items']),p['proposed_public_infill_m2'],p['aggregate_unit_removed_m2'],False]for p in PRO])
print(json.dumps(dict(proposals=3,after_checks=len(TEST),failed=[q for q in TEST if not q['pass_']],original_issues_unapplied=len(OLD['failed'])),ensure_ascii=False))
