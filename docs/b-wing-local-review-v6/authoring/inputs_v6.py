from pathlib import Path
import sys,math,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent));from site_v2_common import *
P=Path(__file__).resolve().parents[1];D=read(P/'source/design-v6.json');B=read(P/'source/baseline-v5.json');A=read(P/'source/annex-v6.json');oldroutes=read(P/'source/retained-public-and-service-v5.json');routes=[q for q in oldroutes if q['id'].startswith(('PUBLIC-','S-'))];shots=[]
def xyz(q,y):return[q[0]+429,y,q[1]-46]
for f in D['floors']:
 for s in f['stores']:
  e=np.array(s['entry']);n=np.array(s['n']);routes.append({'id':s['id'],'kind':'customer doorway -> sales -> staff door -> stock module','points':[xyz(q,f['height'])for q in[(e-n*.9).tolist(),*s['main_route']]]})
for c in A['connections']:
 pp=[xyz(q,c['height'])for q in c['world_route']]
 for reverse in[False,True]:routes.append({'id':c['id']+('-return'if reverse else'-outbound'),'kind':'B public -> full-width actual bridge -> actual A/C target landing; preview boundary only','points':list(reversed(pp))if reverse else pp})
for q in A['roof']['routes'][:3]:
 pts=q.get('points',[])
 if len(pts)>1:routes.append({'id':'RF-'+q['id'],'kind':'source protected roof route, not a vehicle test','points':[xyz(p,16.4)for p in pts]})
routes.append({'id':'RF-PED-BRIDGE','kind':'source roof pedestrian bridge from parking structure to B roof landing','points':[xyz(q,16.4)for q in[(-548,160),(-548,110)]]})
# Stable camera positions chosen from the final layout, identical before/after.
for lev,id,kind in[(0,'B1-010','entry'),(1,'B2-024','entry'),(0,'B1-034','backroom'),(0,'B1-053','backroom'),(1,'B2-047','corner'),(2,'B3-054','backroom'),(0,'B1-022','entry')]:
 f=D['floors'][lev];s=next(s for s in f['stores']if s['id']==id);e=np.array(s['entry']);n=np.array(s['n']);u=np.array(s['u'])
 if kind=='backroom':
  eye=np.array(s['work_rectangle'].centroid.coords[0]);event=next(q for q in read(P/'source/corner-revisions.json')['events']if q['id']==id);look=np.array(event['position_world_xz'])
 elif kind=='corner':
  point=Point(next(q for q in read(P/'source/corner-revisions.json')['events']if q['id']==id)['position_world_xz']);p0=nearest_points(f['public'].buffer(-.7),point)[0];eye=np.array(p0.coords[0]);look=np.array(point.coords[0])
 else:
  eye=e-n*4+u;look=e+n*4
  if not f['public'].buffer(-.4).covers(Point(eye)):eye=e-n*1.2
 shots.append({'id':f'{len(shots)+1:02}-{id}-{kind}','scope':'main','eye_local':xyz(eye,f['height']+1.65),'look_local':xyz(look,f['height']+1.6),'label':id+' / '+kind})
shots.append({'id':'08-2F-time-plaza','scope':'main','eye_local':[4,7.175,12],'look_local':[-14,9.5,-12],'label':'時の広場・開放感と床の視認性'})
for c in A['connections']:
 if not c['id'].endswith('2'):continue
 pts=c['world_route'];eye=np.array(pts[0])*.6+np.array(pts[1])*.4;look=pts[2];shots.append({'id':f'{len(shots)+1:02}-{c["id"]}-bridge','scope':'main','eye_local':xyz(eye,c['height']+1.65),'look_local':xyz(look,c['height']+1.65),'label':c['id']+' 実連絡通路・他館内部は未施工'})
rf=A['roof'];safe=rf['public'].buffer(-.6);p0=nearest_points(safe,Point(-548,110))[0];shots.append({'id':'11-RF-pedestrian','scope':'context','after_only':True,'eye_local':xyz(p0.coords[0],18.05),'look_local':xyz((-540,145),18.1),'label':'RF 歩車分離と連絡橋（既存立体P内部は未施工）'})
shots.append({'id':'12-RF-parking-aerial','scope':'context','after_only':True,'eye_local':xyz((-605,105),42),'look_local':xyz((-605,65),16.4),'label':'RF115台と屋上通路・実Godot俯瞰'})
b=A['basement'];s=b['stores'][0];e=np.array(s['entry']);n=np.array(s['n']);shots.append({'id':'13-B1-market','scope':'context','after_only':True,'eye_local':xyz(e-n*3,-3.7),'look_local':xyz(e+n*5,-3.7),'label':'B1躯体・入口の整合検証。詳細内装未施工'})
frame=next(q for q in A['support_reservations']if len(q['column_centres'])>=2);c=np.array(frame['column_centres'][0]);shots.append({'id':'14-support-reservation','scope':'context','after_only':True,'eye_local':xyz(c+np.array([4,4]),1.65),'look_local':xyz(c,12),'label':'橙色は支持位置の検討用。耐荷重・基礎未検証'})
for s in A['basement']['stores']:
 e=np.array(s['entry']);n=np.array(s['n']);routes.append({'id':'B1-BASEMENT-'+s['id'],'kind':'basement retail entrance only; no vertical stair/elevator traversal','points':[xyz(q,-5.35)for q in[e-n,e,e+n*3]]})
for q in shots:
 if q['id'].startswith(('13-','14-')):q['scope']='main'
 if q['id']=='14-support-reservation':
  frame=next(r for r in A['support_reservations']if len(r['column_centres'])>=2);cc=np.array(frame['column_centres'][0]);env=unary_union([g['shell']for g in D['floors']]);near=np.array(nearest_points(Point(cc),env)[1].coords[0]);direction=cc-near;direction=direction/np.linalg.norm(direction)if np.linalg.norm(direction)>1e-6 else np.array([1.,0.]);eye=cc+direction*5;q['eye_local']=xyz(eye,1.65);q['look_local']=xyz(cc,10.)
 if q['id']=='09-AB-2-bridge':q['eye_local']=[273,7.175,-51.5];q['look_local']=[309,7.175,-51.5];q['label']='AB-2 actual bridge / A-wing landing preview'
 if q['id']=='05-B2-047-corner':
  f=D['floors'][1];cc=np.array(next(e for e in read(P/'source/corner-revisions.json')['events']if e['id']=='B2-047')['position_world_xz']);old=np.array([q['eye_local'][0]-429,q['eye_local'][2]+46]);direction=(old-cc)/np.linalg.norm(old-cc)
  for dist in[4,3,2]:
   eye=cc+direction*dist
   if f['public'].buffer(-.4).covers(Point(eye)):q['eye_local']=xyz(eye,7.175);break

write(P/'source/physical-routes.json',routes);write(P/'source/cameras.json',shots);print('INPUTS',len(routes),'routes plus24 escalators',len(shots),'camera poses')
