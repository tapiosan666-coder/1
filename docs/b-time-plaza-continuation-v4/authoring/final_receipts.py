"""Bind the deliverable to actual current runtime, camera PNGs, reviewed data and declared limits."""
from pathlib import Path
import json,hashlib,csv,shutil
from PIL import Image
P=Path(__file__).resolve().parents[1];E=P/'evidence';S=P/'source';O=S/'followup';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();get=lambda p:json.load(open(p));checks=[]
def same(a,b):return len(a)==len(b) and all(abs(x-y)<1e-9 for x,y in zip(a,b))
def ck(id,ok):checks.append({'id':id,'pass':bool(ok)});assert ok,id
runtime=get(E/'profile-results.json');walk=get(E/'walk-results.json');room=get(E/'service-room-walk.json');ind=get(E/'followup-independent-checks.json');glass=get(E/'stock-glass-results.json');s=get(O/'summary.json');studies=get(O/'backroom-layout-proposals.json')
for name,d in [('profile',runtime),('walk',walk),('service',room)]:
 for key,path in [('geometry_sha256','assets/geometry.json'),('main_script_sha256','main.gd'),('staff_script_sha256','staff_doors.gd')]:ck(name+'-'+key,d[key]==sha(P/path))
ck('walk-all-pass',walk['failed']==0 and walk['total']==1279);ck('service-including-racks-all-pass',room['failed']==0 and room['total']==34);ck('independent-all-pass',ind['failed']==0);ck('privacy-all-80-no-residual',glass['audited_stores']==80 and not glass['remaining_failure_ids']);ck('privacy-current-geometry',glass['geometry_sha256']==sha(P/'assets/geometry.json'))
ck('layout-recovery-split-4-rotation-4-refined-grid',sum(q['layout_geometry_pass']and q['rotation_deg']!=0 for q in studies)==4 and sum(q['layout_geometry_pass']and q['rotation_deg']==0 for q in studies)==4);ck('boundary-candidate-count-two',s['annex_candidates']==2 and s['annex_rejected_boundary_complexity']==22)
poses=get(S/'followup-all-cameras.json');after={q['id']:q for q in get(E/'after/inspection-capture.json')};before={q['id']:q for q in get(E/'before-v3/inspection-capture.json')};records=[]
for q in poses:
 p=E/'after'/(q['id']+'.png');ck(q['id']+'-camera-proof',same(q['p'],after[q['id']]['p'])and same(q['look'],after[q['id']]['look'])and q['fov_deg']==after[q['id']]['fov_deg']);ck(q['id']+'-PNG-proof',sha(p)==after[q['id']]['image_sha256']and Image.open(p).size==(1280,720));record={'id':q['id'],'camera':q,'after_sha256':sha(p)}
 if q['id']in before:
  old=before[q['id']];ck(q['id']+'-same-before-camera',same(q['p'],old['p'])and same(q['look'],old['look'])and q['fov_deg']==old['fov_deg']);record['before_sha256']=sha(E/'before-v3'/(q['id']+'.png'));ck(q['id']+'-before-PNG-proof',record['before_sha256']==old['image_sha256'])
 elif(E/'before-v3'/(q['id']+'.png')).exists():
  record['before_sha256']=sha(E/'before-v3'/(q['id']+'.png'));ck(q['id']+'-protected-v3-copied-before',record['before_sha256']==sha(Path('/workspace/FIND_YOURSELF-B-Time-Plaza-v3/evidence/after')/(q['id']+'.png')))
 else:record['before_status']='after only; room was a sealed proxy in v3'
 records.append(record)
ck('fourteen-actual-viewport-captures',len(records)==14)
ledger=list(csv.DictReader(open(O/'all-191-current-area-ledger.csv',encoding='utf-8-sig')));ck('all-191-ledger',len(ledger)==191);ck('188-corrected-warehouse-plan-routes',sum(bool(q['warehouse_public_approach_distance_m'])for q in ledger)==188);ck('all-sales-preserved',all(float(q['sales_delta_m2'])>=-1e-6 for q in ledger));ck('remaining-48-not-marked-complete',sum(q['layout_work_geometry_pass']=='False'for q in ledger)==48)
receipt={'date_jst':'2026-10-27','checks':checks,'passed':len(checks),'failed':0,'camera_metadata_float_tolerance_m':1e-9,'actual_Godot_Viewport_records':records,'runtime':runtime,'architecture_complete':False,'human_operation_tested':False,'main_game_modified':False,'original_drawings_modified':False,'integration_performed':False,'unapproved_equipment_moved':False,'limitations':['188 warehouse paths are CAD only','room capacity and operational logistics unverified','2 annex plans not implemented; 22 rejected','remaining unassigned floor approximately 22000m2','Windows RTX4060 / 1000-5000 NPC not measured']};(E/'delivery-consistency.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
rows=[]
for p in sorted((P/'assets').iterdir()):
 if p.is_file()and p.suffix!='.import':rows.append({'file':str(p.relative_to(P)),'license':'SIL OFL1.1'if p.suffix=='.otf'else'Original project work; no separate public reuse license assigned','sha256':sha(p)})
with open(S/'asset-license-ledger.csv','w',encoding='utf-8-sig',newline='')as f:w=csv.DictWriter(f,rows[0].keys(),lineterminator='\n');w.writeheader();w.writerows(rows)
logs=E/'capture-logs';logs.mkdir(exist_ok=True)
for name in ['before-capture','after','profile','final-service','final-walk','final-independent','final-privacy']:
 p=Path('/tmp/find-v4-'+name+'.log')
 if p.exists():shutil.copy2(p,logs/p.name)
print('DELIVERY_CONSISTENCY',len(checks),0)
