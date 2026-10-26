"""Checks artifact consistency, never promotes unresolved architecture to a pass."""
from pathlib import Path
import json,hashlib,csv
P=Path(__file__).resolve().parents[1];E=P/'evidence';S=P/'source';get=lambda p:json.load(open(p));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();checks=[]
def ck(n,v):checks.append({'id':n,'pass':bool(v)});assert v,n
w=get(E/'walk-results.json');r=get(E/'after/render-results.json');t=get(E/'escalator-transfer-walk.json');i=get(E/'independent-verification.json');pr=get(E/'screenshot-provenance.json');a=get(S/'backroom-review/area-review.json');g=get(E/'stock-glass-results.json');v=get(S/'vertical-review/vertical-review.json');m=get(S/'scene-manifest.json')
for name,d in [('walking',w),('render',r),('transfer',t)]:
 for k,p in [('geometry_sha256','assets/geometry.json'),('main_script_sha256','main.gd')]:ck(name+'-'+k,d[k]==sha(P/p))
ck('all-physical-samples-pass',w['passed']==1273 and w['failed']==0)
ck('independent-results-no-fail',i.get('fail',0)==0 and i['pass']==510)
ck('privacy-80-stores-five-corrections-zero-residual',g['audited_stores']==80 and len(g['affected_baseline_ids'])==5 and not g['remaining_failure_ids'])
ck('privacy-real-mesh-version',g['geometry_sha256']==sha(P/'assets/geometry.json'))
ck('all-191-ledger-no-sales-loss',len(a['stores'])==191 and a['summary']['all_existing_sales_preserved'])
ck('all-80-private-audit-IDs',len(g['stores'])==len(set(x['id']for x in g['stores']))==80)
ck('exact-current-20-cameras',pr['normal_count']==20 and pr['diagnostic_count']==3)
for q in pr['normal']:ck(q['id']+'-PNG-provenance',q['after_sha256']==sha(E/'after'/(q['id']+'.png')))
ck('no-runtime-lift-misreport',v['actual_functional_lifts_in_validation']==0)
ck('vertical-proposals-not-implemented',not v['changes_applied_to_Godot']and not v['changes_applied_to_drawings'])
ck('production-export-remains-blocked',not m['production_export_gate']['can_export_production'])
ck('functional-stock-requirement-failures-retained',a['summary']['working_geometry_screen_fail']==56)
ck('shared-protected-original-source-hash',m['source_sha256']==sha(Path('/workspace/1/docs/site-correction-v3/geometry.json')))
receipt={'checks':checks,'passed':len(checks),'failed':0,'architecture_complete':False,'human_operation_tested':False,'integration_performed':False,'physical_clock':'--fixed-fps 60, physics 60 Hz. Automated deterministic simulation; not realtime FPS measurement.','date_jst':'2026-10-27'}
(E/'release-consistency.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2));print('RELEASE_CONSISTENCY',len(checks),0)
