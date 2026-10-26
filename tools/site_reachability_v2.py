"""Declared design circulation graph, anchored to already checked actual portals, not a Godot navigation test."""
from site_v2_common import *
from collections import deque
O=R/'docs/site-completion-v2';S=read(O/'geometry.json');P=read(R/'docs/parking-blocks-v2/geometry.json');A=read(R/'docs/a-detailed-design-v1/geometry.json');B=read(R/'docs/b-v4-overlap-correction/geometry.json');C=read(R/'docs/c-detailed-design-v1/geometry.json');nodes={};edges=[]
def node(id,kind,**kw):nodes[id]=dict(id=id,kind=kind,**kw)
def edge(a,b,kind,conditional=None):edges.append(dict(a=a,b=b,kind=kind,requires_approval=conditional,implemented=False))
for w in ['A','B','C']:
 for lev in [-1,0,1,2,3]:node(w+':'+str(lev),'mall_floor',wing=w,level=lev,height=HEIGHT[lev])
 for lev in [-1,0,1,2]:edge(w+':'+str(lev),w+':'+str(lev+1),'escalator'if w!='C'else'stair/lift',None)
for a,b,lev in [('A','B',0),('A','B',1),('B','C',0),('B','C',1)]:edge(a+':'+str(lev),b+':'+str(lev),'fixed_interwing_bridge')
for fac in P['facilities']:
 for f in fac['floors']:node(fac['id']+':'+str(f['level']),'parking_deck',height=f['height'],stalls=len(f['stalls']))
 for f in fac['floors'][1:]:edge(fac['id']+':'+str(f['level']-1),fac['id']+':'+str(f['level']),'parking_stair/lift')
for id,point in [('P-A-OLD22:0',[-153,-20]),('P-B-B1:-1',[-540,6]),('P-B-RF:3',[-540,6])]:node(id,'parking_zone',point=point)
for w in S['walks']+S['bridges']:
 node(w['id'],'path',height=w['height'],width_m=w['width_m'],start=list(w['line'].coords[0]),end=list(w['line'].coords[-1]))
for t in S['pedestrian_towers']:
 for lev in[0,1]:node(t['id']+':'+str(lev),'tower_landing',point=t['point'],height=0 if lev==0 else 5.525)
 edge(t['id']+':0',t['id']+':1','overpass_stair/lift')
for a,b,condition in[
 ('P-A-E:2','BR-PAE',None),('BR-PAE','A:1','A-NEW-EAST-2F'),
 ('P-A-S:0','W-PAS',None),('W-PAS','TW-PAS:0',None),('TW-PAS:1','BR-PAS',None),('BR-PAS','A:1','A-NEW-SOUTH-2F'),
 ('P-C-N:0','W-PCN-1',None),('W-PCN-1','TW-PCN-N:0',None),('TW-PCN-N:1','BR-PCN',None),('BR-PCN','TW-PCN-S:1',None),('TW-PCN-S:0','W-PCN-2',None),('W-PCN-2','C:0',None),
 ('P-B-W:0','W-PBW-1',None),('W-PBW-1','TW-PBW-W:0',None),('TW-PBW-W:1','BR-PBW',None),('BR-PBW','TW-PBW-E:1',None),('TW-PBW-E:0','W-PBW-2',None),('W-PBW-2','B:0','B-NEW-SW-CUSTOMER-1F'),
 ('P-B-S:0','W-PBS',None),('W-PBS','B:0','B-NEW-SW-CUSTOMER-1F'),('P-B-S:6','BR-PBS-RF-PED',None),('BR-PBS-RF-PED','B:3',None),
 ('P-A-OLD22:0','W-A22',None),('W-A22','A:0',None),('P-B-B1:-1','B:-1',None),('P-B-RF:3','B:3',None),('W-OFFSITE-A','TW-PAS:0',None)]:edge(a,b,'pedestrian_connection',condition)
checks=[]
for w,d in [('A',A),('B',B)]:
 for lev in[-1,0,1,2]:
  if w=='B'and lev in[-1,2]:es=read(R/'docs/b-completion-v2/geometry.json')['escalators'];pair=[-1,0]if lev==-1 else[2,3]
  elif w=='B':es=d['escalators'];pair=[lev+1,lev+2]
  else:es=d['escalators'];pair=[lev,lev+1]
  checks.append(dict(kind='declared_ESC_floor_pair_exists',id=w+str(pair),pass_=any(e['levels']==pair for e in es)))
adj={id:[]for id in nodes}
for e in edges:
 assert e['a']in nodes and e['b']in nodes,e
 adj[e['a']].append(e['b']);adj[e['b']].append(e['a'])
paths=[]
for id,n in nodes.items():
 if not n['kind'].startswith('parking'):continue
 prev={id:None};queue=deque([id]);target=None
 while queue:
  q=queue.popleft()
  if nodes[q]['kind']=='mall_floor':target=q;break
  for nex in adj[q]:
   if nex not in prev:prev[nex]=q;queue.append(nex)
 path=[];q=target
 while q is not None:path.append(q);q=prev[q]
 path.reverse();paths.append(dict(from_=id,to=target,path=path,physical_walk_test=False));checks.append(dict(kind='parking_deck_to_mall_design_graph',id=id,pass_=target is not None))
write(O/'design-circulation-graph.json',dict(nodes=list(nodes.values()),edges=edges,paths=paths,design_graph_only=True,not_runtime_or_full_collision_test=True,barrier_free_condition='A/B既存EV床開口24図面案の承認が必要。ESC経路を車椅子経路の代用として合格扱いしない。'))
write(O/'design-circulation-checks.json',checks);print('graph',len(nodes),len(edges),'checks',len(checks),'failed',[q for q in checks if not q['pass_']])
