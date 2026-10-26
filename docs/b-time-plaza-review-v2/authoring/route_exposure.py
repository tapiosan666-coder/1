from pathlib import Path
import sys,csv,json,math
sys.path.insert(0,'/workspace/1/tools')
from site_v2_common import *
P=Path(__file__).resolve().parents[1];D=read(R/'docs/site-correction-v3/geometry.json');old=read(R/'docs/b-v4-overlap-correction/geometry.json');rows=[]
for f in D['floors']:
 if f['wing']!='B'or f['level']not in[0,1,2]:continue
 for r in old['routes']:
  if f['level']+1 not in r['levels']:continue
  path=LineString([(x-714,z-30)for x,z in r['points']]);width=r['width'];near=[]
  for s in f['stores']:
   p=Point(s['entry'])
   if path.distance(p)<=width/2+1:near.append((path.project(p),s['id']))
  positions=[0,*sorted(x[0]for x in near),path.length];gaps=[(b-a,a,b)for a,b in zip(positions,positions[1:])];gap,a,b=max(gaps)
  c=path.interpolate((a+b)/2)
  rows.append({'floor':f['label'],'route':r['id'],'name':r['name'],'role':r['role'],'length_m':round(path.length,2),'width_m':width,'entries_near_route':len(near),'maximum_interval_between_projected_entries_m':round(gap,2),'interval_mid_x':round(c.x,2),'interval_mid_z':round(c.y,2),'status':'VISUAL_REVIEW'if gap>25 and'店舗'in r['role']else'INFORMATION','note':'中心線への投影距離。壁の無店舗長の実測ではない。広場・設備・館間接続は用途を考慮。'})
with open(P/'source/audit/route-exposure.csv','w',newline='',encoding='utf-8-sig')as out:
 w=csv.DictWriter(out,list(rows[0]));w.writeheader();w.writerows(rows)
print('ROUTES',len(rows),'visual review',sum(r['status']=='VISUAL_REVIEW'for r in rows))
