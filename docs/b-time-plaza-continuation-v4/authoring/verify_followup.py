"""Verify the followup scope, actual meshes, source protection and proposal status."""
from pathlib import Path
import sys,json,hashlib,copy,subprocess,itertools,struct,collections
sys.path.insert(0,'/workspace/1/tools');from site_v2_common import *
from coordinate_roles_v4 import correct_service
P=Path(__file__).resolve().parents[1];V3=Path('/workspace/FIND_YOURSELF-B-Time-Plaza-v3');checks=[]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ck(id,value,**detail):checks.append({'id':id,'pass':bool(value),**detail})
for file,root in [('protected-originals.json',R),('protected-v1-project.json',Path('/workspace/FIND_YOURSELF-B-Time-Plaza-v1')),('protected-v2-project.json',Path('/workspace/FIND_YOURSELF-B-Time-Plaza-v2')),('protected-v3-project.json',V3)]:
 data=json.load(open(P/'source'/file));bad=[x for x,h in data.items()if not(root/x).is_file()or sha(root/x)!=h];ck(file+'-unchanged',not bad,files=len(data),changed=bad)
before=read(V3/'source/design-extract.json');after=read(P/'source/design-extract.json')
for a,b in zip(after['floors'],before['floors']):
 for key in ['shell','floor_plate','public','void','shafts']:ck(a['label']+'-'+key+'-unchanged',a[key].equals_exact(b[key],1e-8))
 for s,t in zip(a['stores'],b['stores']):
  for key in ['polygon','sales','backroom']:ck(s['id']+'-'+key+'-unchanged',s[key].equals_exact(t[key],1e-8))
  ck(s['id']+'-customer-entry-unchanged',s['entry']==t['entry'])
 # Source-declared service room outline is retained, point fields now match its actual boundary.
 for s,t in zip(a['service_zones'],b['service_zones']):
  ck(s['id']+'-same-outline',s['polygon'].equals_exact(t['polygon'],1e-8));ck(s['id']+'-entry-on-boundary',Point(s['entry']).distance(s['polygon'].boundary)<.01)
  raw=copy.deepcopy(t);old_u=list(raw['u']);correct_service(raw);once=copy.deepcopy(raw);correct_service(raw);ck(s['id']+'-idempotent-transform',raw['entry']==once['entry']and raw['main_route']==once['main_route']);ck(s['id']+'-direction-not-translated',raw['u']==old_u)
  bad=copy.deepcopy(raw);bad.pop('point_coordinate_frame');reject=False
  try:correct_service(bad)
  except ValueError:reject=True
  ck(s['id']+'-reject-unmarked-already-world',reject)
# Validate the saved triangle colliders against actual render meshes, independently of generator.
g=json.load(open(P/'assets/geometry.json'));sets={}
for key,surface in g['surfaces'].items():
 role=key.split('@@')[0]
 if role not in g['colliders']:continue
 raw=surface['v'];ss=sets.setdefault(role,set())
 for i in range(0,len(raw),9):ss.add(hashlib.blake2b(struct.pack('<9f',*raw[i:i+9]),digest_size=10).digest())
for role,raw in g['colliders'].items():
 missing=sum(hashlib.blake2b(struct.pack('<9f',*raw[i:i+9]),digest_size=10).digest()not in sets[role]for i in range(0,len(raw),9));ck('actual-static-collider-matches-'+role,missing==0,unmatched=missing,documented_proxy='step uses continuous ramp support'if role=='step'else None)
for name in ['walk-results.json','service-room-walk.json','profile-results.json']:
 path=P/'evidence'/name
 if not path.exists():ck(name+'-exists',False);continue
 d=json.load(open(path))
 for key,file in [('geometry_sha256','assets/geometry.json'),('main_script_sha256','main.gd'),('staff_script_sha256','staff_doors.gd')]:ck(name+'-'+key,d[key]==sha(P/file))
 if 'failed'in d:ck(name+'-no-physical-failures',d['failed']==0,passed=d['passed'],total=d['total'])
meta=json.load(open(P/'source/scene-manifest.json'));ck('unresolved-production-output-blocked',not meta['production_export_gate']['can_export_production']);ck('source-room-restoration-three-only',len([r for r in meta['service_rooms_v4']if r.get('name')])==3)
old_env=V3/'main.gd';current=P/'main.gd';import re
section=lambda p:p.read_text().split('func build_environment()->void:')[1].split('func plain(')[0]
ck('lighting-settings-identical-to-v3',section(old_env)==section(current))
base_manifest=json.load(open(V3/'source/scene-manifest.json'))
ck('escalator-equipment-definitions-unchanged',meta['escalators']==base_manifest['escalators'])
ck('existing-tenant-staff-doors-unchanged',[q for q in meta['staff_doors']if not q.get('service_room')]==base_manifest['staff_doors'])
normalize_config=lambda p:re.sub(r'config/name=.*','config/name=VERSION_LABEL',p.read_text())
ck('render-physics-configuration-unchanged',normalize_config(P/'project.godot')==normalize_config(V3/'project.godot'))

studies=read(P/'source/followup/backroom-layout-proposals.json');ready=[q for q in studies if q['status']=='ANNEX_CANDIDATE_NEEDS_APPROVAL'];ck('annex-proposals-not-implemented',all(q['sales_loss_m2']==0 and q['plan_only']for q in studies))
for a,b in itertools.combinations(ready,2):
 if a['floor']==b['floor']:ck(a['id']+'-'+b['id']+'-no-proposal-overlap',a['annex'].intersection(b['annex']).area<1e-6)
for q in ready:ck(q['id']+'-boundary-guard',q['local_boundary_guard_pass'])
ck('request-register-46-items',len(json.load(open(P/'source/followup/request-register.json')))==46)
result={'passed':sum(q['pass']for q in checks),'failed':sum(not q['pass']for q in checks),'checks':checks,'architecture_complete':False,'human_operation_tested':False,'integration_performed':False,'unapproved_equipment_moved':False,'graph_tests_are_not_actual_delivery':True};(P/'evidence/followup-independent-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('FOLLOWUP_INDEPENDENT',result['passed'],result['failed'],flush=True)
if result['failed']:print([q for q in checks if not q['pass']]);raise SystemExit(1)
