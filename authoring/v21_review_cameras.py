from pathlib import Path
import sys,numpy as np,math,json
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import *
plan=read(P/'source/v21/retail-plan.json');way=read(P/'source/v21/wayfinding.json');grids=read(P/'source/v21/navigation-grids.json');F=read(P/'source/v11/floors-updated.json');source={s['id']:(f,s)for f in F for s in f['stores']};cameras=read(P/'source/v21/compare-cameras.json')
for c in cameras:c['variants']=['normal','C','ES']
for store,roles in [('A1F-007',['wall_department']),('A1F-040',['large_appliance']),('B1-030',['central_department']),('BB1-MARKET',['central_department','wall_department']),('A3F-012',['photobooth']),('C1F-CSW-3',['checkout']),('B1-W4',['kitchen'])]:
 f,s=source[store];aisles=affinity.translate(s['aisles'],429,-46);models=[r for r in plan['fixtures']if r['store_id']==store]
 for role in roles:
  host=next((r for r in models if r['role']==role),None)
  if host is None:continue
  target=np.array([host['p'][0],host['p'][2]]);preferred=target+np.array(host['n'])*2.7;eye=np.array(nearest_points(aisles,Point(*preferred))[0].coords[0]);height=f['height'];cameras.append({'id':store+'-detail-'+role,'store_id':store,'wing':f['wing'],'floor':f['label'],'category':s['category'],'eye':[float(eye[0]),height+1.65,float(eye[1])],'look':[float(target[0]),height+1.2,float(target[1])],'fov':60,'variants':['normal','C','ES'],'title':store+' / '+s['category']+' / '+role,'note':'Player-height camera on original protected store aisle. Same view in v20 and v21.'})
for wing in['A','B','C']:
 for floor in['1F','RF']+(['2F','3F']if wing=='B'else[]):
  board=next((b for b in way['normal']if b['wing']==wing and b['floor']==floor),None)
  if board is None:continue
  n=np.array(board['n']);p=np.array([board['p'][0],board['p'][2]]);walk=unary_union([Polygon(r[0],r[1:])for r in grids[board['grid_key']]['walk_polygons']]);eye=p+n*4.
  if not walk.covers(Point(*eye)):eye=np.array(nearest_points(walk,Point(*eye))[0].coords[0])
  ceiling=board['mount']=='ceiling';height=board['p'][1];id='NAV-'+wing+'-'+floor;cameras.append({'id':id,'wing':wing,'floor':floor,'category':'wayfinding','eye':[float(eye[0]),height+1.65,float(eye[1])],'look':[float(p[0]),height+(3.15 if ceiling else 1.5),float(p[1])],'fov':65,'variants':['normal'],'title':wing+'館 '+floor+' / 誘導・共用景観','note':'Normal layout sign; roof facilities preserved. No claim of a new roof structure.'})
for oldid,newid,variant in [('C-yard-open-sky','C-F4-preserved','C'),('ES-west-site','B-F6-preserved','ES')]:
 s=next(c for c in read(P/'source/v15/compare-cameras.json')if c['id']==oldid);s=s.copy();s.update(id=newid,variants=[variant],category='unapproved option preserved',title=newid+' / 未承認の構造別案・維持');cameras.append(s)
write(P/'source/v21/review-cameras.json',cameras);print('V21_CAMERAS',len(cameras))
