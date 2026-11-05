"""Populate the actual feature-table surface with varied face-out titles; no fixture/path changes."""
from pathlib import Path
import json,math
P=Path(__file__).resolve().parents[1]
p=P/'source/v21/retail-plan.json';d=json.loads(p.read_text());b=json.loads((P/'source/v21/model-bounds.json').read_text())
hosts=[h for h in d['fixtures']if h['store_id']=='A1F-007'and h['model']=='fixture_table'];keys={h['id']for h in hosts};d['products']=[r for r in d['products']if r['host']not in keys]
for hi,h in enumerate(hosts):
 n=h['n'];u=[n[1],-n[0]]
 for i,(x,z)in enumerate(( (x,z)for z in[-.10,.25]for x in[-.70,-.35,0.,.35,.70])):
  sku=f'sku_book_{(i+hi)%6}_{i%2}';d['products'].append({'id':h['id']+'-faceout-'+str(i),'store_id':h['store_id'],'host':h['id'],'sku':sku,'model':sku,'asset':'../v21/models/'+sku,'p':[h['p'][0]+u[0]*x+n[0]*z,h['p'][1]+.81-b[sku]['min'][2],h['p'][2]+u[1]*x+n[1]*z],'n':n,'pitch_deg':-90.,'scale':1.,'scale_x':1.,'collision':'none','activation':'always','role':'faceout_recommendation','department':'new-and-recommended','support':'host shelf top','wing':h['wing'],'level':h['level'],'floor':h['floor']})
d['instances']=d['fixtures']+d['products']
for s in d['stores']:s['sku_count']=sum(r['store_id']==s['id']for r in d['products'])
p.write_text(json.dumps(d,ensure_ascii=False,indent=2));print('FACEOUT_TABLES',len(hosts),'products',len(d['products']))
