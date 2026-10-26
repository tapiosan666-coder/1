from pathlib import Path
import sys,json,hashlib,subprocess,itertools
sys.path.insert(0,'/workspace/1/tools');from site_v2_common import *
P=Path(__file__).resolve().parents[1];D=read(R/'docs/site-correction-v3/geometry.json');proposal=read(P/'source/root-gap-review/refined-enclosure-proposals.json');checks=[]
def ck(id,ok,**extra):checks.append({'id':id,'pass':bool(ok),**extra})
for c in proposal['changes']:
 f=next(f for f in D['floors']if f['wing']=='B'and f['level']==c['level']);s=next(s for s in f['stores']if s['id']==c['store']);p=c['new_polygon'];stock=c['new_backroom'];allow=c['nonoccupiable_enclosure_allowance'];pub=f['public'].union(f['void']).union(f['shafts']);others=unary_union([q['polygon']for q in f['stores']if q['id']!=c['store']]);id=c['store']
 ck(id+'-single-valid-plot',p.is_valid and p.geom_type=='Polygon')
 ck(id+'-retains-original-plot',s['polygon'].difference(p).area<1e-5,removed_m2=s['polygon'].difference(p).area)
 ck(id+'-public-void-shafts-preserved',p.intersection(pub).area<1e-6,intersection_m2=p.intersection(pub).area)
 ck(id+'-no-neighbor-invasion',p.intersection(others).area<1e-6)
 ck(id+'-stock-connected-to-own-door',stock.geom_type=='Polygon'and stock.distance(Point(s['back_door']))<.04,stock_components=len(polys(stock)))
 ck(id+'-entry-and-staff-anchor-fixed',c['new_entry']==s['entry']and c['new_back_door']==s['back_door'])
 role=s['sales'].union(stock).union(allow);ck(id+'-internal-role-coverage',p.symmetric_difference(role).area<.00001,difference_m2=p.symmetric_difference(role).area)
 ck(id+'-no-sales-stock-overlap',s['sales'].intersection(stock).area<1e-6)
 ck(id+'-architectural-complexity-screen',c['new_effective_vertices']<=c['old_effective_vertices']+3 and c['perimeter_delta_m']<=3,old_vertices=c['old_effective_vertices'],new_vertices=c['new_effective_vertices'],perimeter_delta_m=c['perimeter_delta_m'],note='数値による棄却基準。建築品質の完成判定ではない。')
run=subprocess.run([sys.executable,str(P/'authoring/build.py')],cwd=P,capture_output=True,text=True);ck('actual-default-production-export-rejected',run.returncode!=0 and'PRODUCTION_EXPORT_BLOCKED'in run.stdout+run.stderr,returncode=run.returncode,output=(run.stdout+run.stderr).strip())
result={'checks':checks,'passed':sum(q['pass']for q in checks),'failed':sum(not q['pass']for q in checks),'production_design_status':'BLOCKED; unallocated floor remains on all five B-wing levels','proposal_only':True,'human_operation_tested':False};(P/'evidence/root-contract-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('ROOT_CONTRACT',result['passed'],result['failed'])
for q in checks:
 if not q['pass']:print(q)
