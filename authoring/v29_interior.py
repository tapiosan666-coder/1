from pathlib import Path
import sys,math,json,collections
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import read,write,Point
plan=read(P/'source/v29/retail-plan.json');focus=read(P/'source/v29/focus-stores.json');rows=[]
for s in plan['stores']:
 if s['id']not in focus:continue
 fixtures=[f for f in plan['fixtures']if f['store_id']==s['id']];e=np.array(s['entry_world']);v=np.array(s['main_route_world'][1])[[0,2]]-e;n=v/np.linalg.norm(v)
 candidates=[]
 for f in fixtures:
  p=np.array(f['p'])[[0,2]]
  if not s['sales_world'].buffer(-.8).contains(Point(p)):continue
  candidates.append((p,f))
 count=min(20,max(3,math.ceil(s['sales_m2']/260)));chosen=[]
 for i in range(min(count,len(candidates))):
  if not chosen:best=min(candidates,key=lambda q:np.linalg.norm(q[0]-e))
  else:best=max(candidates,key=lambda q:min(np.linalg.norm(q[0]-c[0])for c in chosen))
  if chosen and min(np.linalg.norm(best[0]-c[0])for c in chosen)<5.5:break
  chosen.append(best);candidates=[q for q in candidates if q is not best]
 seen=set()
 for p,f in chosen:
  label=f.get('department_label','')
  if not label or label in seen:label=''
  else:seen.add(label)
  rows.append({'store_id':s['id'],'wing':s['wing'],'category':s['category'],'brand':s['brand'],'p':[float(p[0]),0.,float(p[1])],'n':n.tolist(),'actual_department_label':label,'source_fixture':f['id'],'sales_m2':s['sales_m2']})
write(P/'source/v29/interior-stations.json',rows);print('INTERIOR STATIONS',len(rows))
