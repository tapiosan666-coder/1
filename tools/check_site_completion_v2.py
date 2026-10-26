"""Independent reread of delivered design data; geometric checks are not runtime tests."""
from site_v2_common import *
from shapely.strtree import STRtree
from collections import Counter
O=R/'docs/site-completion-v2';A=read(R/'docs/a-detailed-design-v1/geometry.json');B=read(R/'docs/b-v4-overlap-correction/geometry.json');C=read(R/'docs/c-detailed-design-v1/geometry.json');BN=read(R/'docs/b-completion-v2/geometry.json');S=read(O/'geometry.json');P=read(R/'docs/parking-blocks-v2/geometry.json');CHECK=[];CONDITIONS=[]
def ck(kind,id,ok,v=None):CHECK.append(dict(kind=kind,id=id,pass_=bool(ok),value=v))
F={w:{f['level']:f for f in d['floors']}for w,d in [('A',A),('C',C),('B',BN)]}
for f in B['floors']:q=floor_B_world(f,[core_world(c)for c in B['cores']]);F['B'][q['level']]=q
for w,ff in F.items():
 for lev,f in ff.items():
  id=w+'-'+LABEL[lev];public=f['public'];plate=f['floor_plate'];shafts=f['shafts'];void=f['void'];pr=[s['polygon']for s in f['stores']];tree=STRtree(pr);main=max(polys(public.buffer(-.25)),key=lambda p:p.area)
  for k,g in [('public',public),('plate',plate),('shafts',shafts),('void',void)]:ck('valid_polygon',id+'/'+k,g.is_valid)
  ck('public_supported',id,public.difference(plate).area<EPS,public.difference(plate).area)
  ck('declared_openings_excluded',id,plate.intersection(shafts.union(void)).area<EPS,plate.intersection(shafts.union(void)).area)
  ck('public_not_in_stores',id,public.intersection(unary_union(pr)).area<EPS,public.intersection(unary_union(pr)).area)
  for i,p in enumerate(pr):
   for j in tree.query(p):
    if j<=i:continue
    ck('stores_do_not_overlap',f['stores'][i]['id']+'/'+f['stores'][j]['id'],p.intersection(pr[j]).area<EPS,p.intersection(pr[j]).area)
  for st in f['stores']:
   ck('store_entry_on_public',st['id'],public.distance(Point(st['entry']))<.01,public.distance(Point(st['entry'])))
   ck('store_entry_connected',st['id'],main.distance(Point(st['entry']))<.55,main.distance(Point(st['entry'])))
   path=LineString(st['main_route']);ck('store_internal_path_in_unit',st['id'],path.difference(st['polygon'].buffer(1e-7)).length<.01,path.difference(st['polygon'].buffer(1e-7)).length)
  if f.get('parking'):
   pp=f['parking'];vmain=max(polys(pp['vehicle_aisles'].buffer(-1)),key=lambda p:p.area);ps=[s['polygon']for s in pp['stalls']];tree=STRtree(ps)
   for i,s in enumerate(pp['stalls']):
    ck('B_parking_front_connected',s['id'],vmain.distance(Point(s['vehicle_entry']))<1.01)
    ck('B_parking_rear_connected',s['id'],main.distance(Point(s['pedestrian_entry']))<.3)
    ck('B_parking_not_in_shafts',s['id'],s['polygon'].intersection(shafts.union(void)).area<EPS)
    for j in tree.query(s['polygon']):
     if j<=i:continue
     ck('B_stalls_no_overlap',s['id']+'/'+pp['stalls'][j]['id'],s['polygon'].intersection(ps[j]).area<EPS)
   ck('B_car_ped_overlap_only_designated',id,public.intersection(pp['vehicle_aisles']).symmetric_difference(pp['crossings']).area<EPS)
# All floor elevations and old-source core layouts remain fixed.
for w,ff in F.items():
 for lev,f in ff.items():ck('height_agrees',w+LABEL[lev],abs(f['height']-HEIGHT[lev])<EPS)
# Restricted plant/warehouse circulation is independently connected to the public core.
for f in BN['floors']:
 maint=unary_union([f['public'],f.get('staff_walk',Polygon())]+[q['service_walk']for q in f['program']if q['accessible_room']]);main=max(polys(maint.buffer(-.15)),key=lambda p:p.area)
 for q in f['program']:
  if q['accessible_room']:ck('staff_program_connected',q['id'],main.distance(q['service_walk'].representative_point())<.5,main.distance(q['service_walk'].representative_point()))
for t in S['pedestrian_towers']:
 ck('overpass_tower_stair_rise',t['id'],abs(t['riser_m']*t['riser_count']-5.525)<EPS)
 ck('overpass_tower_lift_opening_inside',t['id'],t['lift'].covers(t['lift_opening']))
for s in S['old_A22']['stalls']:
 ck('old22_car_front_access',s['id'],S['old_A22']['vehicle_aisles'].buffer(1e-7).covers(Point(s['vehicle_entry'])))
 ck('old22_rear_foot_access',s['id'],S['old_A22']['protected_pedestrian'].buffer(1e-7).covers(Point(s['pedestrian_entry'])))
# Existing AB/BC connection points and endpoint strips; fixed bridge width and datum.
CONNECT=[]
for f in B['floors'][:2]:
 lev=f['floor']-1
 for c in f['connectors']:
  coords=[[p[0]-714,p[1]-30]for p in c['route']];end=coords[-1];recipient='A'if c['id'].startswith('AB')else'C';line=LineString(coords);band=line.buffer(c['width']/2,cap_style=2);rf=F[recipient][lev];delta=rf['public'].distance(Point(end));overlap=band.intersection(rf['public']).area;ck('fixed_connection_endpoint',c['id'],delta<.01,delta);ck('fixed_connection_has_full_width_floor',c['id'],rf['floor_plate'].union(F['B'][lev]['floor_plate']).buffer(1e-6).covers(rect(end,[(coords[-1][0]-coords[-2][0])/math.dist(coords[-1],coords[-2]),(coords[-1][1]-coords[-2][1])/math.dist(coords[-1],coords[-2])],.1,c['width'])),None)
  CONNECT.append(dict(id=c['id'],from_wing='B',to_wing=recipient,level=lev,height=HEIGHT[lev],width_m=c['width'],world_points=coords,source_changed=False,public_overlap_m2=overlap,endpoint_distance_m=delta))
# New escalator bank projections versus fixed v4.1 openings.
for e in BN['escalators']:
 old=next(q for q in B['escalators']if q['id']==e['source_existing_opening']);fixed=affinity.translate(old['shaft'],-714,-30);ck('new_ESC_exact_old_plan',e['id'],fixed.symmetric_difference(e['shaft']).area<EPS)
 for land in e['landings']:
  newlev=-1 if-1 in e['levels']else 3;ck('new_ESC_landing_support',e['id']+str(land.bounds),land.difference(F['B'][newlev]['floor_plate']).area<EPS,land.difference(F['B'][newlev]['floor_plate']).area)
# Missing old shaft holes are approval conditions, never quietly counted as passes or applied.
for p in BN['existing_core_opening_proposals']:
 if p['requires_approval']:CONDITIONS.append(dict(id=p['id'],issue='既存構造床にEV/階段の穴が未反映',overlap_m2=p['solid_baseline_overlap_m2'],proposed_action='別図の局所切欠き案をユーザー承認後に設計原本へ反映',baseline_modified=False))
for p in S['arrival_proposals']+S.get('loading_door_proposals',[]):CONDITIONS.append(dict(id=p['id'],issue='新規駐車場からの局所玄関案は未適用',proposed_action='承認後に外壁/玄関床だけ変更。店舗/広場/通路網を維持',baseline_modified=False))
# Source A/C/B exact byte hashes and all protected files.
protected=read(O/'protected-baseline-hashes.json')
for path,h in protected.items():ck('baseline_unchanged',path,(R/path).is_file()and sha(R/path)==h)
sourcefiles=[R/'docs/a-detailed-design-v1/geometry.json',R/'docs/b-v4-overlap-correction/geometry.json',R/'docs/c-detailed-design-v1/geometry.json',R/'docs/b-completion-v2/geometry.json',R/'docs/parking-blocks-v2/geometry.json',O/'geometry.json']
write(O/'independent-checks.json',CHECK);write(O/'approval-conditions.json',CONDITIONS);write(O/'connection-checks.json',CONNECT)
report=dict(design_only=True,game_modified=False,floors=15,source_units=sum(len(f['stores'])for ff in F.values()for f in ff.values()),checks=len(CHECK),passed=sum(q['pass_']for q in CHECK),failed=[q for q in CHECK if not q['pass_']],approval_conditions=len(CONDITIONS),conditions_are_not_applied=True,actual_walk_tests=0,actual_vehicle_tests=0,protected_files=len(protected),source_sha256={str(p.relative_to(R)):sha(p)for p in sourcefiles})
write(O/'independent-verification.json',report);print(json.dumps({k:v for k,v in report.items()if k!='source_sha256'},ensure_ascii=False,indent=2))
csvwrite(O/'connection-ledger.csv',['ID','from','to','floor','height_m','width_m','endpoint_world_X','endpoint_world_Z','distance_to_public_m','source_changed'],[[c['id'],c['from_wing'],c['to_wing'],LABEL[c['level']],c['height'],c['width_m'],*c['world_points'][-1],c['endpoint_distance_m'],False]for c in CONNECT])
