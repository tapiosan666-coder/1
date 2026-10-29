from pathlib import Path
import json,shutil,collections
P=Path(__file__).resolve().parents[1];R=Path('/workspace/v17-review');rows=[]
def read(p):return json.loads(Path(p).read_text())
def add(name,path,keys,method):
 d=read(path);checks=[]
 for key in keys:checks+=d.get(key,[])
 if not checks:return
 passed=sum(bool(q.get('pass',q.get('passed',False)))for q in checks);rows.append({'name':name,'passed':passed,'failed':len(checks)-passed,'method':method,'source':str(Path(path).relative_to(R))if Path(path).is_relative_to(R)else str(path),'failures':[q for q in checks if not q.get('pass',q.get('passed',False))]})
T=R/'tests';T.mkdir(exist_ok=True)
for p in(P/'evidence/v16').rglob('*.json'):
 dst=T/'retained-test-output'/p.relative_to(P/'evidence/v16');dst.parent.mkdir(exist_ok=True,parents=True);shutil.copy2(p,dst)
if(P/'evidence/settings-save-restore-v7.json').exists():shutil.copy2(P/'evidence/settings-save-restore-v7.json',T/'settings.json')
for name,k in [('Defined pedestrian routes','all'),('Escalator routes','ES'),('EV / access routes','EV')]:
 p=T/'core-final'/('physics-'+k+'.json')
 if p.exists():add(name,p,['checks'],'60Hz CharacterBody3D auto steering / actual collisions, NOT human play')
for name,file,keys in [('C F4 connectors','physics-C.json',['checks','transfers']),('F6 equipment + transfers + public connectors','physics-ES.json',['checks','transfers']),('C F4 edge guard input','edges-C.json',['cases']),('F6 opening guard input','edges-ES.json',['cases'])]:
 p=T/'retained-test-output'/file
 if p.exists():add(name,p,keys,'Automated physical W input with per-tick steering; not human operation')
for name,p,keys in [('New fitted bays / floor support / event linked graphics',T/'scenery.json',['checks']),('F4/F6 keyboard scene navigation',T/'navigation.json',['checks']),('Settings save and restore',T/'settings.json',['checks']),('F9 / M / F11 controls',T/'retained-test-output/controls/controls-amenities.json',['checks'])]:
 if p.exists():add(name,p,keys,'Automated test; see individual method / no human operation')
for label in['normal','C','ES']:
 p=T/'fresh'/(label+'.json')
 if p.exists():add('Fresh standalone ZIP startup '+label,p,['checks'],'Imported and booted from a fresh extracted folder with Godot 4.6.3')
if(R/'F6-route-candidates.json').exists():
 d=read(R/'F6-route-candidates.json');w=read(R/'F6-route-width-and-belt.json');rnd=read(R/'F6-rounded-width-and-belt.json');records=[]
 for q in d['checks']:records.append({k:q[k]for k in['id','option','design_length_m','pass']})
 report={'status':'UNAPPROVED; no machine/floor/guard relocation in normal scene','candidates':records,'direct_shortest_rejected':True,'direct_margin_failures':[q for q in w['checks']if not q['pass']],'rounded_margin_checks':rnd['checks'],'recommendation':'Keep the protected 8.4m routing. Rounded-corner centreline is 7.53m and passed centre / middle offsets +/-0.35m in these tests; carry as the next candidate. Straight 6.4m passed centre but fails one offset on each floor: do not adopt it based on length alone. Human wayfinding and full crowd clearance remain unverified.','measured_type':'designed polyline lengths + actual automated collision tests; not measured human walking distances'}
 (R/'proposals/F6-candidate-evaluation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
summary={'tests':rows,'reported_regression_failures':sum(r['failed']for r in rows),'all_scene_quality_complete':False,'human_playtest':False,'Windows_GPU_FPS_measured':False,'144FPS_confirmed':False,'FF16_quality_confirmed':False,'F6_rejected_candidates_are_not_regression_passes':True,'limits':['Defined-route tests do not prove every possible player movement or every architectural joint','Wall support rays are sampled, not exact topology proofs','No structural-engineering approval for decks, roof loads or RF-SUPPORT-16','C F4 / B F6 remain unapproved separate variants; water garden remains design only']}
(R/'検査結果.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print('RESULTS',len(rows),'categories',sum(r['passed']for r in rows),'passed',summary['reported_regression_failures'],'failed')
