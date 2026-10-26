"""Independent source/protection/construction validation. Architectural review flags never become PASS."""
from pathlib import Path
import sys,json,hashlib,struct,csv,re,collections
sys.path.insert(0,'/workspace/1/tools')
from site_v2_common import *
P=Path(__file__).resolve().parents[1];V1=Path('/workspace/FIND_YOURSELF-B-Time-Plaza-v1');V2=Path('/workspace/FIND_YOURSELF-B-Time-Plaza-v2');D=P/'evidence';checks=[]
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ck(id,condition,**detail):checks.append({'id':id,'status':'PASS'if condition else'FAIL',**detail})
for file,root in[('protected-originals.json',R),('protected-v1-project.json',V1),('protected-v2-project.json',V2)]:
 old=json.load(open(P/'source'/file));bad=[str(p)for p,v in old.items()if not(root/p).is_file()or h(root/p)!=v];ck(file+'-unchanged',not bad,files=len(old),changed=bad)
meta=read(P/'source/scene-manifest.json');extract=read(P/'source/design-extract.json');base=read(V2/'source/design-extract.json');crop=shape(mapping(box(*meta['crop_world_xz'])))
proposal=read(P/'source/root-gap-review/refined-enclosure-proposals.json');expected={c['store']:c for c in proposal['changes']}
ck('production-export-is-correctly-blocked',not meta['production_export_gate']['can_export_production'],unresolved_floors=meta['production_export_gate']['unresolved'])
for a,b in zip(extract['floors'],base['floors']):
 for field in['shell','public','void','shafts','floor_plate']:
  ck(f'{a["label"]}-{field}-layout-unchanged',a[field].equals_exact(b[field],1e-8))
 for s,t in zip(a['stores'],b['stores']):
  target=expected[s['id']]['new_polygon']if s['id']in expected else t['polygon'];ck(s['id']+'-plot-matches-declared-proposal-and-entry-fixed',s['polygon'].equals_exact(target,1e-8)and s['entry']==t['entry'],intentional_proposal=s['id']in expected)
  ck(s['id']+'-original-sales-area-retained',t['sales'].difference(s['sales']).area<1e-6,sales_delta_m2=s['sales'].area-t['sales'].area)
  if s['id']in expected:ck(s['id']+'-no-proposal-public-overlap',s['polygon'].intersection(b['public']).area<1e-6)
# Explicitly check contact footprints / declared protected circulation rather than generic shape counts.
e=read(P/'source/expanded-qa-inputs.json')
for c in e['clearance_checks']:ck(c['id'],c['pass'],intersection_m2=c['intersection_m2'])
g=json.load(open(P/'assets/geometry.json'));render_hash={}
for key,v in g['surfaces'].items():
 role=key.split('@@')[0]
 if role not in g['colliders']:continue
 data=v['v'];dest=render_hash.setdefault(role,set())
 for i in range(0,len(data),9):dest.add(hashlib.blake2b(struct.pack('<9f',*data[i:i+9]),digest_size=10).digest())
for role,values in g['colliders'].items():
 unmatched=0
 for i in range(0,len(values),9):
  if hashlib.blake2b(struct.pack('<9f',*values[i:i+9]),digest_size=10).digest()not in render_hash.get(role,set()):unmatched+=1
 ck('static-collider-vs-model-'+role,unmatched==0,triangles=len(values)//9,unmatched_triangles=unmatched,exception='step is the explicitly documented continuous support under animated treads'if role=='step'else None)
# Actual slab collider triangles, including only the v1 departure support already carried forward.
raw=g['colliders']['stone'];slabtri=[raw[i:i+9]for i in range(0,len(raw),9)]
for f in extract['floors']:
 y=f['height'];target=f['floor_plate'].intersection(crop);adds=[shape(q['polygon'])if isinstance(q['polygon'],dict)else q['polygon']for q in meta['isolated_slab_additions']if q['level']==f['level']];target=target.union(unary_union(adds));pol=[]
 for t in slabtri:
  if max(abs(t[j]-y)for j in[1,4,7])<1e-6:pol.append(Polygon([(t[j]+meta['world_origin_xz'][0],t[j+2]+meta['world_origin_xz'][1])for j in[0,3,6]]))
 made=unary_union(pol);err=target.symmetric_difference(made).area
 ck(f['label']+'-actual-slab-geometry',err<.001,symmetric_difference_m2=err,tolerance_m2=.001)
 ck(f['label']+'-no-slab-in-void',made.intersection(f['void']).area<1e-6,intersection_m2=made.intersection(f['void']).area)
# These measured runtime results must correspond to the distributed shaders/scripts and geometry.
w=json.load(open(D/'walk-results.json'))
ck('physical-tests',w['failed']==0,passed=w['passed'],total=w['total'],failed=w['failed'])
for key,name in[('geometry_sha256','assets/geometry.json'),('main_script_sha256','main.gd'),('player_script_sha256','player.gd'),('staff_script_sha256','staff_doors.gd'),('animation_script_sha256','escalator_v2.gd')]:ck('runtime-version-'+key,w.get(key)==h(P/name))
# Pose contract is checked against BOTH scripts. Before images are the untouched approved v1 captures.
def poses(p):
 s=Path(p).read_text();return[{'id':id,'p':[float(x)for x in pv.split(',')],'look':[float(x)for x in lv.split(',')]}for id,pv,lv in re.findall(r'\{"id":"([^"]+)","p":Vector3\(([^)]+)\),"look":Vector3\(([^)]+)\)\}',s)]
ck('same-eight-camera-positions',poses(P/'main.gd')==poses(V1/'main.gd'),cameras=len(poses(P/'main.gd')))
for p in(D/'before-v1').glob('0[1-8]-*.png'):ck(p.name+'-untouched-before',h(p)==h(V1/'evidence'/p.name))
audit=read(P/'source/audit/full-audit.json');review=[]
for f in audit['floors']:
 review.append({'id':f['floor']+'-unassigned-floor-candidates','status':'REVIEW_REQUIRED','candidate_area_m2':f['unassigned_candidate_total_m2'],'note':'独自分類。用途確定と区画変更は未承認。広場はこの数値から除外。'})
 review.append({'id':f['floor']+'-short-boundary-candidates','status':'REVIEW_REQUIRED','candidates':len(f['short_corner_candidates']),'note':'入口等は除外済みだが、すべてを不要と判定していない。数値検出を目視確認・図面修正案へ回す。'})
review.extend({'id':x['id'],'status':'REVIEW_REQUIRED','reason':x['reason']}for x in e['review_required'])
review.append({'id':'B2-026-multipart-plot-outside-crop','status':'REVIEW_REQUIRED','note':'元図面に1.67048㎡の離れた部分。今回の3D範囲外。原本は変更していない。'})
review.append({'id':'anchor-internal-design','status':'NOT_TESTED','note':'6核店は3D範囲外。上映室・段床・厨房の平面案は作成済みだが、3D・営業運用・設備能力は未検証。'})
review.append({'id':'human-operation-on-Windows','status':'NOT_TESTED','note':'自動物理歩行・Viewport目視評価と区別。RTX4060の性能未測定。'})
result={'checks':checks,'pass':sum(q['status']=='PASS'for q in checks),'fail':sum(q['status']=='FAIL'for q in checks),'review_and_not_tested':review,'overall':'REVIEW_PROTOTYPE_CHECKS_PASS_BUT_FULL_B_DESIGN_UNRESOLVED'if all(q['status']=='PASS'for q in checks)else'IMPLEMENTATION_FAILURE','no_blanket_architectural_pass':True}
(D/'independent-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('INDEPENDENT',result['pass'],result['fail'],'review/not-tested',len(review))
for q in checks:
 if q['status']=='FAIL':print(q)
