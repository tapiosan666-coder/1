from pathlib import Path
import sys,json
sys.path.insert(0,'/workspace/1/tools');from site_v2_common import *
P=Path(__file__).resolve().parents[1];m=read(P/'source/scene-manifest.json');d=read(P/'source/design-extract.json');byid={s['id']:s for f in d['floors']for s in f['stores']};choices=[]
for door in m.get('staff_doors',[]):
 if door.get('service_room'):
  f=next(f for f in d['floors']if f['level']==door['level']);z=next(z for z in f['service_zones']if z['id']==door['store']);bp=z['entry'];u=door['u'];n=door['n'];s={'polygon':z['polygon'],'backroom':z['polygon']};sweep=LineString(z['main_route']).buffer(.34)
 else:
  s=byid[door['store']];bp=s['back_door'];u=s['u'];n=s['n'];sweep=LineString(s['main_route']).buffer(.34)
 w=door['leaf_width_m'];options=[]
 for side in[-1,1]:
  hinge=(bp[0]+u[0]*side*w/2,bp[1]+u[1]*side*w/2);c=(hinge[0]+n[0]*w/2,hinge[1]+n[1]*w/2);open_leaf=rect(c,n,w,.042)
  score=open_leaf.intersection(sweep).area+open_leaf.difference(s['backroom'].buffer(.08)).area*10
  options.append((score,side,open_leaf))
 score,side,leaf=min(options,key=lambda q:q[0]);mechanism='hinged'
 if leaf.intersection(sweep).area>1e-6:
  sliding=[]
  for sign_side in[-1,1]:
   c=(bp[0]+u[0]*sign_side*w+n[0]*.08,bp[1]+u[1]*sign_side*w+n[1]*.08);q=rect(c,u,w,.042)
   if q.difference(s['polygon'].buffer(.01)).area<1e-4:sliding.append((q.intersection(sweep).area,sign_side,q))
  if sliding:
   overlap,slide_side,sl=min(sliding,key=lambda q:q[0])
   if overlap<1e-6:leaf=sl;mechanism='sliding';door['slide_side']=slide_side
 door['mechanism']=mechanism;door['hinge_side']=side;door['open_leaf_world_xz']=leaf
 choices.append({'id':door['id'],'hinge_side':side,'mechanism':mechanism,'canonical_route_overlap_m2':leaf.intersection(sweep).area,'status':'VERIFIED_2D_ZERO_ROUTE_INTERFERENCE'if leaf.intersection(sweep).area<1e-6 else'PHYSICAL_REVIEW','open_leaf':leaf})
(P/'source/scene-manifest.json').write_text(json.dumps(m,default=encode,ensure_ascii=False,separators=(',',':')));(P/'source/door-hinge-selection.json').write_text(json.dumps(choices,default=encode,ensure_ascii=False,indent=2));print('DOOR_HINGES',len(choices),'interfering',sum(c['canonical_route_overlap_m2']>1e-6 for c in choices))
