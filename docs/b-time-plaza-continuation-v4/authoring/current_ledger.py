from pathlib import Path
import json,csv,sys
sys.path.insert(0,'/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
from shapely.geometry import shape
P=Path(__file__).resolve().parents[1];O=P/'source/followup';old=json.load(open(P/'source/backroom-review/area-review.json'))['stores'];new={q['id']:q for q in json.load(open(O/'backroom-layout-proposals.json'))};routes={q['id']:q for q in csv.DictReader(open(O/'corrected-warehouse-routes.csv',encoding='utf-8-sig'))};rooms={q['id']:q for f in json.load(open(O/'coordinate-role-source.json'))['floors']for q in f.get('service_zones',[])};rows=[]
for q in old:
 q=q.copy();r=routes[q['id']];n=new.get(q['id']);q['nearest_existing_shared_warehouse']=r['nearest_corrected_warehouse'];q['warehouse_plan_m2']=shape(rooms[r['nearest_corrected_warehouse']]['polygon']).area if r['nearest_corrected_warehouse'] else None;q['warehouse_public_approach_distance_m']=r['public_entry_distance_m'];q['warehouse_route_status']=r['status'];q['layout_work_geometry_pass']=n['layout_geometry_pass'] if n else q['working_space_screen_pass'];q['followup_status']=n['status'] if n else 'PREVIOUS_FIXED_AXIS_SCREEN_PASSED; operation unverified';q['annex_not_applied_m2']=n['annex_candidate_m2'] if n else 0;rows.append(q)
with open(O/'all-191-current-area-ledger.csv','w',encoding='utf-8-sig',newline='')as f:w=csv.DictWriter(f,rows[0].keys(),lineterminator='\n');w.writeheader();w.writerows(rows)
print('CURRENT_LEDGER',len(rows),'remaining geometric work-screen failures',sum(not q['layout_work_geometry_pass']for q in rows))
