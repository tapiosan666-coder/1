from pathlib import Path
import sys,math
sys.path.insert(0,str(Path(__file__).resolve().parent));from site_v2_common import *
import numpy as np
P=Path(__file__).resolve().parents[1];D=read(P/'source/design-v5.json');origin=(-429,46);routes=[];shots=[]
def xyz(p,y):return[p[0]-origin[0],y,p[1]-origin[1]]
for f in D['floors']:
 for s in f['stores']:
  e=np.array(s['entry']);n=np.array(s['n']);pts=[(e-n*.9).tolist(),*s['main_route']];routes.append({'id':s['id'],'kind':'customer doorway -> sales -> actual sliding staff door -> working stock module','points':[xyz(p,f['height'])for p in pts]})
 for room in f['service_zones']:
  e=np.array(room['entry']);u=np.array(room['u']);n=np.array(room['n']);local=lambda x,z:(e+u*x+n*z).tolist();pts=[local(0,-1),local(0,.6),local(0,1.5)]
  if'-T'in room['id']:pts.extend([local(0,4),local(2,4),local(0,4),local(0,7.5),local(2,7.5),local(0,7.5),local(0,7.3),local(-2,7.3),local(-2,8.8),local(0,8.8),local(0,10.5),local(2,10.5)])
  else:pts.extend([local(0,5),local(0,room['planned_depth_m']-1)])
  routes.append({'id':room['id'],'kind':'service receiving doorway and real interior working aisle','points':[xyz(p,f['height'])for p in pts]})
# These customer-floor eye locations are common to both plans; never move the camera to flatter the result.
for floor,id in [(0,'B1-N01'),(1,'B2-N01'),(2,'B3-N01'),(0,'B1-022'),(1,'B2-022'),(2,'B3-046')]:
 f=D['floors'][floor];s=next(s for s in f['stores']if s['id']==id);e=np.array(s['entry']);n=np.array(s['n']);u=np.array(s['u']);eye=e-n*6+u*2
 # Keep eye on the actual protected public concourse.
 if not f['public'].buffer(-.45).covers(Point(eye)):eye=e-n*2
 look=e+n*6;shots.append({'id':f'{len(shots)+1:02}-{f["label"]}-{id}','eye_local':xyz(eye,f['height']+1.65),'look_local':xyz(look,f['height']+1.8),'label':id+' 店舗街・旧未帰属区画'})
# All three original plaza viewpoints, exactly the previous eye axes where applicable.
for lev in[0,1,2]:
 h=D['floors'][lev]['height'];shots.append({'id':f'{len(shots)+1:02}-{lev+1}F-time-plaza','eye_local':[4,h+1.65,12],'look_local':[-14,h+4,-12],'label':'時の広場・基本構造維持'})
for lev in[0,1,2]:
 f=D['floors'][lev];room=next(z for z in f['service_zones']if'-W'in z['id']);e=np.array(room['entry']);n=np.array(room['n']);u=np.array(room['u']);shots.append({'id':f'{len(shots)+1:02}-{lev+1}F-stock-room','eye_local':xyz(e+n*1.4,f['height']+1.65),'look_local':xyz(e+n*10+u*.5,f['height']+1.6),'label':'用途を定義した共用在庫室（変更後のみ）','after_only':True})
for lev,id in[(0,'B1-001'),(0,'B1-011'),(2,'B3-054')]:
 f=D['floors'][lev];s=next(s for s in f['stores']if s['id']==id);e=np.array(s['entry']);n=np.array(s['n']);eye=e-n*2;look=e+n*8;shots.append({'id':f'{len(shots)+1:02}-{lev+1}F-{id}-wing-edge','eye_local':xyz(eye,f['height']+1.65),'look_local':xyz(look,f['height']+1.8),'label':id+' 東西の街区・未帰属床再編'})
f=D['floors'][2];eye=(-437,6);look=(-437,-27);shots.append({'id':'16-3F-BC-removed-stub','eye_local':xyz(eye,f['height']+1.65),'look_local':xyz(look,f['height']+.5),'label':'3F B/C接続側の店舗街（張出し撤去範囲は壁外・図面参照）'})
write(P/'source/physical-routes.json',routes);write(P/'source/cameras.json',shots);print('INPUTS',len(routes),len(shots))
