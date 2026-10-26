"""Independent geometric checks of v3. No nearest-point replacement for failed navigation targets."""
from site_v2_common import *
from shapely.strtree import STRtree
from collections import Counter,deque
O=R/'docs/site-correction-v3';D=read(O/'geometry.json');P=read(O/'parking-geometry.json');S=D['site'];F={(f['wing'],f['level']):f for f in D['floors']};CHECK=[];TARGETS=[];GRAPH=[];NODES={};COMP={}
def ck(kind,id,ok,value=None):CHECK.append(dict(kind=kind,id=id,pass_=bool(ok),value=value,scope='drawing_geometry_only'))
def node(id,kind,**kwargs):NODES[id]=dict(id=id,kind=kind,**kwargs)
def edge(a,b,kind,verified=True,**kw):GRAPH.append(dict(a=a,b=b,kind=kind,verified=verified,**kw))
def membership(g,point,margin=.001):return g.buffer(margin).covers(Point(point))
def solids(f):return f['envelope_walls'].union(f['vestibule_walls']).union(unary_union([d['frames'].union(d['open_leaves'])for d in f['doors_v3']]))
for (w,lev),f in F.items():
 id=w+'-'+LABEL[lev];node(id,'mall_floor',height=f['height']);free=f['nav_free'].buffer(-.3);parts=polys(free);main=max(parts,key=lambda p:p.area);COMP[id]=main
 for name in ['public','floor_plate','nav_free','shafts']:ck('valid_polygon',id+'/'+name,f[name].is_valid)
 ck('public_supported',id,f['public'].difference(f['floor_plate']).area<EPS,f['public'].difference(f['floor_plate']).area)
 ck('navigation_supported',id,f['nav_free'].difference(f['floor_plate']).area<EPS)
 ck('floor_excludes_openings',id,f['floor_plate'].intersection(f['shafts'].union(f['void'])).area<EPS)
 ck('public_excludes_closed_band',id,f['public'].intersection(f.get('residual',Polygon())).area<EPS,f['public'].intersection(f.get('residual',Polygon())).area)
 prs=[s['polygon']for s in f['stores']];tree=STRtree(prs);ck('public_not_in_stores',id,f['public'].intersection(unary_union(prs)).area<EPS,f['public'].intersection(unary_union(prs)).area)
 for i,s in enumerate(f['stores']):
  for j in tree.query(s['polygon']):
   if j<=i:continue
   area=s['polygon'].intersection(prs[j]).area;ck('stores_do_not_overlap',s['id']+'/'+f['stores'][j]['id'],area<EPS,area)
  ck('store_entry_on_public',s['id'],f['public'].distance(Point(s['entry']))<.01,f['public'].distance(Point(s['entry'])))
  anchor=[s['entry'][j]-s['n'][j]*.5 for j in[0,1]];ok=membership(main,anchor);ck('store_public_anchor_in_connected_free_floor',s['id'],ok,dict(anchor=anchor,distance_m=main.distance(Point(anchor))));TARGETS.append(dict(id=s['id'],floor=id,anchor=anchor,pass_=ok,avatar_radius_m=.3))
  path=LineString(s['main_route']);outside=path.difference(s['polygon'].buffer(1e-7)).length;ck('store_internal_path_in_unit',s['id'],outside<.01,outside)
  for k in['backroom','sales','shelf_zones','aisles','wall_solids']:
   if k in s and (k!='wall_solids'or(w=='B'and lev in[0,1,2])):ck('store_detail_clipped_to_revised_unit',s['id']+'/'+k,s[k].difference(s['polygon'].buffer(1e-7)).area<EPS,s[k].difference(s['polygon'].buffer(1e-7)).area)
 # Navigation of every core access anchor, rather than treating a named floor edge as an operational lift.
 for v in f.get('vertical_devices',[]):
  for typ,anchor in [('lift',v['lift_anchor']),('stair',v['stair_anchor'])]:ck('core_anchor_connected',v['id']+'/'+typ,membership(main,anchor),main.distance(Point(anchor)))
  for typ,g in [('lift_landing',v['lift_landing']),('front_landing',v['front_landing'])]:ck('landing_on_solid_floor',v['id']+'/'+typ,g.difference(f['floor_plate']).area<EPS,g.difference(f['floor_plate']).area)
  if lev<3:
   ck('mid_landing_joins_both_flights',v['id'],v['mid_landing'].intersection(v['lower_flight_projection']).area>EPS and v['mid_landing'].intersection(v['upper_flight_projection']).area>EPS)
   ck('mid_landing_headroom',v['id'],(HEIGHT[lev+1]-HEIGHT[lev])/2-v['mid_landing_slab_thickness_m']>=2.4,(HEIGHT[lev+1]-HEIGHT[lev])/2-v['mid_landing_slab_thickness_m'])
  ck('lift_landing_free_of_fixed_obstacles',v['id'],v['lift_landing'].difference(f['nav_free']).area<EPS,v['lift_landing'].difference(f['nav_free']).area)
  ck('lift_shaft_open',v['id'],f['floor_plate'].intersection(v['lift_opening']).area<EPS)
  ck('stair_shaft_open_above_basement',v['id'],lev==-1 or f['floor_plate'].intersection(v['stair_opening']).area<EPS)
 for d in f['doors_v3']:
  obs=solids(f);ck('customer_clear_opening_not_blocked',d['id'],d['clear_path'].intersection(obs).area<EPS,d['clear_path'].intersection(obs).area)
  ck('customer_landing_supported',d['id'],all(g.difference(f['floor_plate']).area<EPS for g in d['landings']))
  for side in['inside_anchor','outside_anchor']:ck('customer_both_sides_connected',d['id']+'/'+side,membership(main,d[side]),main.distance(Point(d[side])))
  ck('customer_door_frame_fits_vestibule',d['id'],d['overall_frame_width_m']<=d['vestibule_width_m'])
  ck('customer_door_no_step',d['id'],d['threshold_step_m']==0)
  u=d['u'];c=d['center'];line=LineString([(c[0]+u[0]*a,c[1]+u[1]*a)for a in[-d['vestibule_width_m']/2,d['vestibule_width_m']/2]]);covered=d['frames'].union(d['infill_panels']).union(d['open_leaves']).union(d['clear_path']);ck('no_unfilled_gap_at_door_frame',d['id'],line.difference(covered).length<EPS,line.difference(covered).length)
# C core lift-side landing anchors, including the locally cleared furniture approach.
for lev in[-1,0,1,2,3]:
 f=F['C',lev];main=COMP['C-'+LABEL[lev]]
 for c in f['cores']:
  d=next(q for q in c['doors']if q['id']=='EV');axis=d['axis'];normal=[-axis[1],axis[0]];centre=c['rooms']['lift'].centroid;v=[d['p'][0]-centre.x,d['p'][1]-centre.y]
  if sum(normal[j]*v[j]for j in[0,1])<0:normal=[-normal[0],-normal[1]]
  anchor=[d['p'][j]+normal[j]*.6 for j in[0,1]];ck('C_lift_landing_connected',c['id']+'/'+LABEL[lev],membership(main,anchor),main.distance(Point(anchor)))
# Every one of the old 65 criteria is explicitly replayed, not just an aggregate count.
lookup={(q['kind'],q['id']):q for q in CHECK}
resolved=[]
for old in read(R/'docs/site-completion-v2/independent-verification.json')['failed']:
 key=(old['kind'],old['id']);new=lookup.get(key);resolved.append(dict(kind=old['kind'],id=old['id'],old_value=old['value'],new_value=new['value']if new else None,pass_=bool(new and new['pass_'])))
write(O/'65-replayed-checks.json',resolved)
# Validated vertical edges: anchor connectivity and exactly aligned holes/landings.
for w in ['A','B']:
 for lev in[-1,0,1,2]:
  lo=F[w,lev];hi=F[w,lev+1]
  for v in lo['vertical_devices']:
   u=next(q for q in hi['vertical_devices']if q['core']==v['core']);a=w+'-'+LABEL[lev];b=w+'-'+LABEL[lev+1]
   for typ in['lift','stair']:
    same=v['lift_opening'].symmetric_difference(u['lift_opening']).area<EPS if typ=='lift'else v['lower_flight_projection'].symmetric_difference(u['lower_flight_projection']).area<EPS
    ok=same and membership(COMP[a],v[typ+'_anchor'])and membership(COMP[b],u[typ+'_anchor']);ck('vertical_alignment_and_access',v['core']+f'/{lev}/{typ}',ok);edge(a,b,typ,ok,core=v['core'],runtime_verified=False)
for lev in[-1,0,1,2]:
 lo=F['C',lev];hi=F['C',lev+1];ok=True
 for c in lo['cores']:
  upper=next(q for q in hi['cores']if q['id']==c['id']);ok=ok and c['shafts'].symmetric_difference(upper['shafts']).area<EPS and membership(COMP['C-'+LABEL[lev]],c['entry'])and membership(COMP['C-'+LABEL[lev+1]],upper['entry'])
 ck('C_preserved_vertical_cores',str(lev),ok);edge('C-'+LABEL[lev],'C-'+LABEL[lev+1],'C_stair_lift',ok,runtime_verified=False)
# Existing interwing endpoints are read from their original local coordinate system.
B=read(R/'docs/b-v4-overlap-correction/geometry.json')
for raw in B['floors'][:2]:
 lev=raw['floor']-1
 for link in raw['connectors']:
  p=[[q[0]-714,q[1]-30]for q in link['route']];w='A'if link['id'].startswith('AB')else'C';end=p[-1];joint=F['B',lev]['nav_free'].union(F[w,lev]['nav_free']).buffer(-.3);connect=max(polys(joint),key=lambda x:x.area);ok=membership(connect,p[0])and membership(connect,end);ck('interwing_joint_continuous',link['id'],ok);edge('B-'+LABEL[lev],w+'-'+LABEL[lev],'interwing',ok)
# All parking decks: rear-foot-path anchors and original stall geometry/count.
PARK={};COUNTS=Counter()
for fac in P['facilities']:
 for f in fac['floors']:
  id=fac['id']+':'+str(f['level']);node(id,'parking_deck',height=f['height']);ped=f['pedestrian'].difference(f.get('edge_guard',Polygon())).difference(f.get('temporary_guard_until_bridge_built',Polygon()));parts=polys(ped.buffer(-.3));main=max(parts,key=lambda q:q.area);PARK[id]=main
  for s in f['stalls']:
   link=list(s['pedestrian_access_link'].coords);a,b=link[-2:];ll=math.dist(a,b);anchor=[b[j]+(b[j]-a[j])/ll*.35 for j in[0,1]];ck('parking_stall_rear_to_connected_pedestrian',s['id'],membership(main,anchor),dict(anchor=anchor,distance_m=main.distance(Point(anchor))));COUNTS[fac['id']]+=1
  for c in f['cores']:
   ck('parking_core_entry_connected',id+'/'+c['id'],main.distance(Point(c['entry']))<.55,main.distance(Point(c['entry'])))
   for typ,room,entrykey in[('stair',c['stair'],'stair_entry'),('lift',c['elevator'],'elevator_entry')]:
    ep=c.get(entrykey)
    if ep is None:continue
    a,b,x,z=room.bounds;choices=[(abs(ep[0]-a),[-1,0]),(abs(ep[0]-x),[1,0]),(abs(ep[1]-b),[0,-1]),(abs(ep[1]-z),[0,1])];normal=min(choices,key=lambda q:q[0])[1];anchor=[ep[j]+normal[j]*.6 for j in[0,1]];ck('parking_equipment_landing_connected',id+'/'+c['id']+'/'+typ,membership(main,anchor),main.distance(Point(anchor)))
    if f['level']>0:ck('parking_equipment_opening',id+'/'+c['id']+'/'+typ,room.buffer(-.15 if typ=='lift'else 0).intersection(f['floor_plate']).area<EPS)
  ck('rear_apron_does_not_cross_car_lane',id,f['rear_access_aprons'].intersection(f['vehicle_aisles']).area<EPS)

 for k in range(len(fac['floors'])-1):edge(fac['id']+':'+str(k),fac['id']+':'+str(k+1),'parking_stair_lift',True,runtime_verified=False)
# Cross-site path support and links are geometry-based, with tower levels declared separately.
pathmap={q['id']:q for q in S['walks']+S['bridges']}
for q in pathmap.values():node(q['id'],'site_walk',height=q['height'])
for t in S['pedestrian_towers']:
 for level in[0,1]:node(t['id']+':'+str(level),'tower_landing',height=5.525 if level else 0)
 edge(t['id']+':0',t['id']+':1','tower_stair_lift',True,runtime_verified=False)
links=[('P-A-E:2','BR-PAE'),('BR-PAE','A-2F'),('P-A-S:0','W-PAS'),('W-PAS','TW-PAS:0'),('TW-PAS:1','BR-PAS'),('BR-PAS','A-2F'),('P-C-N:0','W-PCN-1'),('W-PCN-1','TW-PCN-N:0'),('TW-PCN-N:1','BR-PCN'),('BR-PCN','TW-PCN-S:1'),('TW-PCN-S:0','W-PCN-2'),('W-PCN-2','C-1F'),('P-B-W:0','W-PBW-1'),('W-PBW-1','TW-PBW-W:0'),('TW-PBW-W:1','BR-PBW'),('BR-PBW','TW-PBW-E:1'),('TW-PBW-E:0','W-PBW-2'),('W-PBW-2','B-1F'),('P-B-S:0','W-PBS'),('W-PBS','B-1F'),('P-B-S:6','BR-PBS-RF-PED'),('BR-PBS-RF-PED','B-RF')]
# At each junction require a shared positive-area walk floor with a 0.6m avatar corridor.
def node_geom(id):
 if id in COMP:return next(f['nav_free']for f in D['floors']if f['wing']+'-'+LABEL[f['level']]==id)
 if id in pathmap:return pathmap[id]['polygon']
 if id in PARK:
  fac,lev=id.rsplit(':',1);f=next(f for q in P['facilities']if q['id']==fac for f in q['floors']if f['level']==int(lev));return f['pedestrian'].difference(f['edge_guard']).difference(f['temporary_guard_until_bridge_built'])
 tower,lev=id.rsplit(':',1);return next(t['landing']for t in S['pedestrian_towers']if t['id']==tower)
for a,b in links:
 ga=node_geom(a);gb=node_geom(b);combined=ga.union(gb).buffer(-.3);ca=ga.buffer(-.3).representative_point();cb=gb.buffer(-.3).representative_point();ok=any(part.distance(ca)<.01 and part.distance(cb)<.01 for part in polys(combined));ck('site_walk_junction_continuity',a+'/'+b,ok,ga.distance(gb));edge(a,b,'site_walk',ok)
for id,w,lev in [('P-A-OLD22','A',0),('P-B-B1','B',-1),('P-B-RF','B',3)]:node(id,'parking_zone');edge(id,w+'-'+LABEL[lev],'attached_parking',True,runtime_verified=False)
oldpark=read(R/'docs/parking-blocks-v2/geometry.json');oldslots={st['id']:st['polygon']for fac in oldpark['facilities']for f in fac['floors']for st in f['stalls']}
for fac in P['facilities']:
 for pf in fac['floors']:
  for st in pf['stalls']:ck('parking_stall_geometry_unchanged',st['id'],st['polygon'].symmetric_difference(oldslots[st['id']]).area<EPS)
  ck('rear_access_aprons_supported',fac['id']+str(pf['level']),pf['rear_access_aprons'].difference(pf['floor_plate']).area<EPS)
  ck('rear_access_aprons_not_in_stalls',fac['id']+str(pf['level']),pf['rear_access_aprons'].intersection(unary_union([st['polygon']for st in pf['stalls']])).area<EPS)
for f in D['floors']:
 if not f.get('parking'):continue
 main=COMP[f['wing']+'-'+LABEL[f['level']]]
 for st in f['parking']['stalls']:
  anchor=[st['pedestrian_entry'][j]+st['parking_direction'][j]*.4 for j in[0,1]];ck('attached_B_stall_rear_connected',st['id'],membership(main,anchor),main.distance(Point(anchor)))
for st in S['old_A22']['stalls']:
 ck('old_22_rear_access',st['id'],S['old_A22']['protected_pedestrian'].buffer(.001).covers(Point(st['pedestrian_entry'])))
ck('total_parking_slots','all',sum(COUNTS.values())+22+193+115==6699,sum(COUNTS.values())+22+193+115)
# Reachability across verified design edges; disconnected targets are failures, never auto-projected.
adj={n:[]for n in NODES}
for e in GRAPH:
 if e['verified']:adj[e['a']].append(e['b']);adj[e['b']].append(e['a'])
parking_nodes=[n for n,v in NODES.items()if v['kind'].startswith('parking')];routes=[]
for start in parking_nodes:
 prev={start:None};queue=deque([start])
 while queue:
  a=queue.popleft()
  for b in adj[a]:
   if b not in prev:prev[b]=a;queue.append(b)
 for target in [w+'-'+LABEL[l]for w in['A','B','C']for l in[-1,0,1,2,3]]:
  path=[];q=target
  if q in prev:
   while q is not None:path.append(q);q=prev[q]
   path.reverse()
  ck('parking_to_all_15_floors',start+'/'+target,bool(path));routes.append(dict(start=start,target=target,path=path,actual_walk_test=False))
protected=read(O/'protected-inputs.json')
for path,h in protected.items():ck('original_file_unchanged',path,(R/path).is_file()and sha(R/path)==h)
write(O/'independent-checks.json',CHECK);write(O/'store-reachability.json',TARGETS);write(O/'reachability-graph.json',dict(nodes=list(NODES.values()),edges=GRAPH,parking_to_floor_routes=routes,actual_walk_test=False))
report=dict(checks=len(CHECK),passed=sum(q['pass_']for q in CHECK),failed=[q for q in CHECK if not q['pass_']],old_65_replayed=len(resolved),old_65_remaining=sum(not q['pass_']for q in resolved),floors=len(F),stores=len(TARGETS),parking_slots=6699,protected_originals=len(protected),avatar_radius_m=.30,actual_walk_tests=0,actual_vehicle_tests=0,source_geometry_sha256=sha(O/'geometry.json'),parking_sha256=sha(O/'parking-geometry.json'))
write(O/'independent-verification.json',report);print(json.dumps({k:v for k,v in report.items()if k!='failed'},ensure_ascii=False));print('FAILED',len(report['failed']));print(json.dumps(report['failed'][:50],ensure_ascii=False,indent=2))
