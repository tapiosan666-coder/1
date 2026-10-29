from pathlib import Path
P=Path(__file__).resolve().parents[1];exec((P/'authoring/retail_models_v10.py').read_text().split('def book(')[0]);OUT=P/'assets/v17/models'
clear();bark=material('Connected_ficus_bark',(.16,.105,.055),.95);leaves=[material('Broad_curved_ficus_'+str(i),c,.83)for i,c in enumerate([(.025,.09,.025),(.055,.16,.04),(.10,.23,.055),(.16,.28,.08)])]
tube('Main_trunk',[(0,0,0),(.03,.01,1.3),(-.04,.02,2.8),(.06,-.04,4.65)],.09,bark)
for j in range(22):
 a=j*2.39996;z=2.8+(j%7)*.28;radius=1.2 if j%3 else.8;tip=(radius*math.cos(a),radius*math.sin(a),z+.4)
 tube('Crown_branch',[(0,0,1.8+j*.065),(.5*tip[0],.5*tip[1],z-.2),tip],.022,bark)
 for k in range(38):
  az=k*2.4;rr=.12+(k%8)*.065;cx=tip[0]+rr*math.cos(az);cy=tip[1]+rr*math.sin(az);cz=tip[2]+rng.uniform(-.27,.38);length=rng.uniform(.28,.43);wide=length*.35;angle=rng.uniform(0,math.tau)
  petiole=tube('Leaf_petiole',[tip,(cx,cy,cz)],.0028,bark);petiole.data.bevel_resolution=1;petiole.data.resolution_u=1
  q=[]
  for xx,yy,zz in[(0,0,0),(-wide,length*.4,.035),(0,length,.03),(wide,length*.4,.035),(0,length*.47,.09)]:q.append((cx+xx*math.cos(angle)-yy*math.sin(angle),cy+xx*math.sin(angle)+yy*math.cos(angle),cz+zz))
  mesh('Broad_bowed_leaf',q,[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],leaves[(j+k)%4])
finish('atrium_ficus_dense')
