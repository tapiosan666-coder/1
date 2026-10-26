"""Re-run drawing checks against the serialized v4.1 data. No generator/game execution."""
from pathlib import Path
import sys,json,ast,math,heapq,collections,hashlib,csv,copy
sys.path.append('/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
import numpy as np
import shapely
from shapely.geometry import shape,Point,LineString,Polygon,box
from shapely.ops import unary_union,substring,nearest_points
R=Path(__file__).resolve().parents[1];O=R/'docs/b-v4-overlap-correction';B=R/'docs/b-purpose-review-v4';EPS=1e-8
raw=json.loads((O/'geometry.json').read_text());baseline=json.loads((B/'geometry.json').read_text())
def dec(v):
 if isinstance(v,dict):return shape(v)if'type'in v and('coordinates'in v or'geometries'in v)else{k:dec(x)for k,x in v.items()}
 if isinstance(v,list):return[dec(x)for x in v]
 return v
D=dec(raw);FLOORS=D['floors'];CORES=D['cores'];PLAZAS=D['plazas'];ALL_ESC=D['escalators'];ROUTES=D['routes'];EGRESS=D['egress'];BODY=FLOORS[0]['shell'];BRIDGE=PLAZAS[1]['bridges'];CHECKS=[];NAV=[]
def polys(g):return[]if g.is_empty else[g]if g.geom_type=='Polygon'else[p for p in getattr(g,'geoms',[])if p.geom_type=='Polygon']
def chk(kind,id,ok,value=None,floor=None):CHECKS.append(dict(kind=kind,id=id,pass_=bool(ok),value=value,floor=floor))
# Execute only pure validation nodes and the pure Grid class from the reviewed v4 checker.
# Explicit AST selection refuses any changed line layout rather than executing generation or output code.
source=(R/'tools/design_b_v4.py').read_text();tree=ast.parse(source)
selected=[]
for n in tree.body:
 if isinstance(n,ast.For)and n.lineno==296:
  assert n.end_lineno==351
  q=copy.deepcopy(n);q.body=[x for x in q.body if x.lineno>=320];selected.append(q)
 if isinstance(n,ast.For)and n.lineno in[352,390,407,419]:selected.append(n)
 if isinstance(n,ast.ClassDef)and n.name=='Grid':selected.append(n)
# Maintain original source order: Grid precedes navigation validation loop.
assert len(selected)==6,len(selected)
for n in selected:exec(compile(ast.Module(body=[n],type_ignores=[]),'reviewed_v4_validation_nodes','exec'),globals())
chk('upper_void_alignment','2F/3F',FLOORS[1]['void'].equals(FLOORS[2]['void']))
for f in FLOORS:
 for p in PLAZAS:
  bays=sum(1 for x in f['furniture']if x['plaza']==p['id']and x['kind']=='bench');chk('plaza_rest_bays',p['id'],bays>=1,bays,f['floor'])
 for s in f['wayfinding']:chk('sign_head_clearance',s['plaza'],s['bottom_y']-f['height']>=2.4,s['bottom_y']-f['height'],f['floor'])
 for z in f['service_zones']:
  chk('service_room_entry_reaches_common',z['id'],f['reachable'].distance(Point(z['entry']))<.8,f['reachable'].distance(Point(z['entry'])),f['floor'])
  chk('service_room_route_inside',z['id'],LineString(z['main_route']).difference(z['polygon'].buffer(.003)).length<.01,None,f['floor'])
 if f['floor']==1:
  for s in f['stores']:
   if'loading_door'in s:chk('loading_door_enters_stockroom',s['id'],s['backroom'].buffer(.01).covers(Point(s['loading_door']['point'])),None,1)
expected=collections.Counter(x['kind']for x in json.loads((B/'checks.json').read_text()));actual=collections.Counter(x['kind']for x in CHECKS);assert expected==actual,(expected-actual,actual-expected)
original_count=len(CHECKS)
# Additional correction-specific checks. EPS is a floating-point area tolerance, not a construction allowance.
for bf,f in zip(baseline['floors'],FLOORS):
 level=f['floor'];pub=f['public'];forbidden=unary_union([pub,f['void'],f['shafts']]+[s['polygon']for s in f['stores']]+[c['outline']for c in CORES])
 for key,geom in [('public',pub),('void',f['void']),('shafts',f['shafts']),('stores',unary_union([s['polygon']for s in f['stores']])),('cores',unary_union([c['outline']for c in CORES]))]:
  overlap=f['residual'].intersection(geom).area;chk('corrected_residual_no_overlap',key,overlap<EPS,overlap,level)
 for key in['void','shafts']:
  overlap=f['floor_plate'].intersection(f[key]).area;chk('corrected_plate_excludes_opening',key,overlap<EPS,overlap,level)
 for key in['residual','floor_plate']:
  before=shape(bf[key]);removed=before.difference(f[key]);added=f[key].difference(before).area
  chk('correction_polygon_valid',key,f[key].is_valid,None,level);chk('correction_no_unrelated_growth',key,(added if key=='residual'else f[key].difference(before).difference(pub).area)<EPS,added,level)
  outside=removed.difference(forbidden if key=='residual'else f['void'].union(f['shafts'])).area
  chk('correction_only_conflict_faces',key,outside<EPS,outside,level)
 for key in bf:
  if key in['residual','floor_plate']:continue
  chk('protected_floor_field_identical',key,bf[key]==raw['floors'][level-1][key],None,level)
 # Shared floor and store lots are separate interfaces: preserve prior v4 tolerances and report their nonzero maxima.
 for s in f['stores']:
  area=s['polygon'].intersection(pub).area;chk('existing_tenant_public_tolerance_0_06',s['id'],area<.06,area,level)
 for c in f['connectors']:
  expected_end={'AB-1':[-174,-5.5],'AB-2':[-110,-5.5],'BC-1':[-370,-80],'BC-2':[-432,-117]}[c['id']];pt=c['route'][-1];chk('existing_connector_endpoint',c['id'],[pt[0]-714,pt[1]-30]==expected_end,pt,level)
 # Opening/shaft topology is fixed between versions; only the slab gets trimmed.
 for key in['void','shafts','guardrails','public','walkable','clear_public','reachable','shell']:
  chk('protected_polygon_exact',key,shape(bf[key]).equals_exact(f[key],0),None,level)
 # Basic surface coverage remains complete despite local trimming (no unassigned new holes).
 must_have=pub.difference(f['void'].union(f['shafts']));gap=must_have.difference(f['floor_plate']).area
 chk('corrected_plate_covers_public',str(level),gap<EPS,gap,level)
for key in baseline:
 if key!='floors':chk('protected_root_field_identical',key,baseline[key]==raw[key])
protected=json.loads((B/'game-file-hashes.json').read_text());bad=[]
for path,h in protected.items():
 actual=hashlib.sha256((R/path).read_bytes()).hexdigest();chk('game_file_hash_unchanged',path,actual==h)
 if actual!=h:bad.append(path)
# Export measured routes. This is 2D sampling, not an FPS walk or dynamic navigation test.
(O/'route-paths.json').write_text(json.dumps(NAV,ensure_ascii=False,indent=2,default=lambda v:v.item()if isinstance(v,np.generic)else str(v)));(O/'checks.json').write_text(json.dumps(CHECKS,ensure_ascii=False,indent=2))
counts=collections.Counter(x['kind']for x in CHECKS)
with(O/'check-summary.csv').open('w',encoding='utf-8-sig',newline='')as fp:
 w=csv.writer(fp);w.writerow(['検査種別','件数','合格','不合格'])
 for k,n in sorted(counts.items()):w.writerow([k,n,sum(x['kind']==k and x['pass_']for x in CHECKS),sum(x['kind']==k and not x['pass_']for x in CHECKS)])
failed=[x for x in CHECKS if not x['pass_']]
proof={'design_only':True,'runtime_walking_tests':0,'v4_checks_freshly_rerun':original_count,'total_assertions':len(CHECKS),'passed':len(CHECKS)-len(failed),'failed':failed,'area_epsilon_for_new_zero_checks_m2':EPS,'protected_game_files':len(protected),'protected_game_mismatches':bad,'store_counts':[len(f['stores'])for f in FLOORS],'primary_entrances':sum(len(f['stores'])for f in FLOORS),'secondary_entrances':sum('secondary_entry'in s for f in FLOORS for s in f['stores']),'sampled_store_to_stair_routes':len(NAV)*3,'navigation_grid_m':1.,'navigation_clearance_radius_m':.45,'baseline_check_thresholds_preserved':True,'v4_validation_source_sha256':hashlib.sha256(source.encode()).hexdigest(),'corrected_geometry_sha256':hashlib.sha256((O/'geometry.json').read_bytes()).hexdigest(),'all_other_geometry_fields_unchanged':all(q['pass_']for q in CHECKS if q['kind'].startswith('protected_')),'remaining_unchanged_tenant_public_intersections_max_m2':{f['floor']:max(s['polygon'].intersection(f['public']).area for s in f['stores'])for f in FLOORS},'note':'Existing tenant/public interfaces retain the prior v4 0.06 m² area criterion; store-pair, interior wall, portal and navigation criteria are also unchanged. New residual/opening checks use 1e-8 m². This is not a claim that every intentional polygon intersection in the mall is zero.'}
(O/'verification.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2));print(json.dumps(proof,ensure_ascii=False,indent=2));assert not failed,failed[:10]
