from pathlib import Path
import sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import *
p=read(P/'source/v21/retail-plan.json');kinds={s['id']:s['category']for s in p['stores']};changes=[]
for r in p['fixtures']:
 kind=kinds[r['store_id']];old=r['model'];model=None
 if kind in['electronics','mobile']and old in['fixture_table','fixture_low_island']:model='fixture_electronics_counter'
 elif kind in['electronics','mobile']and old=='fixture_wall_bay':model='fixture_electronics_wall'
 elif kind=='beauty'and old=='fixture_table':model='fixture_beauty_counter'
 elif kind=='beauty'and old=='fixture_wall_bay':model='fixture_beauty_wall'
 if model:r['model']=model;r['asset']='../v21/models/'+model;changes.append({'id':r['id'],'old':old,'new':model,'footprint_and_host_supports':'Original placement and support heights retained'})
p['instances']=p['fixtures']+p['products'];write(P/'source/v21/retail-plan.json',p);write(P/'source/v21/specialty-fixture-application.json',changes);print('DEDICATED_JOINERY',len(changes))
