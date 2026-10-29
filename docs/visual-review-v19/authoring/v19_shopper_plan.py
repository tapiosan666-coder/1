from pathlib import Path
import sys,math,numpy as np,collections
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import *
data=read(P/'source/v18/shoppers.json');retail=read(P/'source/v19/retail-plan.json');props=read(P/'source/v16/commons.json');allprops={r['id']:r for r in props['instances']+retail['instances']};people=data['people'];issues=[]
for r in people:
 r['female_reference']=r['id']=='V18-A-01';r['activity_offset']=float(r['style'])*.61;r['stride_m']=.62 if r['female_reference']else .75
 if r['role']=='seated':
  front=np.array([-math.sin(r['yaw']),-math.cos(r['yaw'])]);q=np.array([r['p'][0],r['p'][2]]);r['seat_front']=front.tolist();r['seat_point']=r['p'][:];r['seat_cycle']='outdoor_bench'in str(r['seat_body']);r['stand_point']=[q[0]+front[0]*.42,0.,q[1]+front[1]*.42];r['home_point']=[q[0]+front[0]*1.82,0.,q[1]+front[1]*1.82]
  if not r['seat_cycle']:issues.append({'id':r['id'],'status':'Chair remains seated; front approach crosses a table. No false complete sit/stand loop.'})
 elif r['role']=='browsing':
  point=Point(r['p'][0],r['p'][2]);store=next((s for s in retail['stores']if s['sales_world'].buffer(.1).covers(point)),None)
  if not store:issues.append({'id':r['id'],'reason':'No store contains existing viewpoint'});continue
  items=[d for d in retail['instances']if d['store_id']==store['id']];free=store['sales_world'].buffer(-.37).difference(unary_union([d['footprint'].buffer(.40)for d in items]));r['store_id']=store['id'];r['browse_point']=r['p'][:];front=np.array([-math.sin(r['yaw']),-math.cos(r['yaw'])]);tangent=np.array([front[1],-front[0]]);target=None
  for d in[1.5,-1.5,1.0,-1.0,2.0,-2.0]:
   q=np.array([r['p'][0],r['p'][2]])+tangent*d;line=LineString([(r['p'][0],r['p'][2]),q])
   if free.covers(line):target=q;break
  r['browse_cycle']=target is not None
  if target is not None:r['home_point']=[target[0],r['p'][1],target[1]]
  else:issues.append({'id':r['id'],'status':'Browsing retained; no safe departure segment found'})
 elif r['role']=='conversation':
  other=min([q for q in people if q['role']=='conversation'and q['wing']==r['wing']and q['id']!=r['id']],key=lambda q:math.dist(q['p'],r['p']));r['partner_id']=other['id']
write(P/'source/v19/shoppers.json',{'people':people,'count':len(people),'female_reference_count':sum(r['female_reference']for r in people),'toggle':'F12','baseline_v18_preserved':True,'default_mode':'v19','no_ES_EV_stairs_AI':True,'issues':issues});print('V19_PLAN',len(people),'female',sum(r['female_reference']for r in people),'seat cycles',sum(r.get('seat_cycle',False)for r in people),'browse cycles',sum(r.get('browse_cycle',False)for r in people),'issues',len(issues))
