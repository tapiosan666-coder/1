"""Sampled rigid-body swept envelopes. PASS_2D does not certify untested manoeuvres or 3D vehicles."""
from site_v2_common import *
import numpy as np
from collections import Counter
O=R/'docs/site-correction-v3';D=read(O/'geometry.json');P=read(O/'parking-geometry.json');S=D['site'];ORIG=read(R/'docs/site-completion-v2/geometry.json');CH=[]
def change_road(id,pts):
 q=next(q for q in S['roads']if q['id']==id);old=next(x['line']for x in ORIG['roads']if x['id']==id);q['line']=LineString(pts);q['points']=pts;q['polygon']=q['line'].buffer(q['width_m']/2,cap_style=2,join_style=1);CH.append(dict(id=id,old=old,new=q['line'],reason='入口法線に進行方向を合わせる／搬入口への不要な直角切返しをなくす'))
# Maintain stall positions and all building footprints. Only two local approach lines change.
change_road('V-PAS',[(-130,500),(-130,318),(-63,318),(-63,330)])
S['turn_reservations']=[q for q in S['turn_reservations']if not q['id'].startswith(('V-PAS-TURN','D-BE-TURN'))]
for i,p in enumerate([(-130,318),(-63,318)],1):S['turn_reservations'].append(dict(id=f'V-PAS-TURN-{i}',role='customer',centre=p,polygon=Point(p).buffer(9),reservation_radius_m=9,not_a_dynamic_swept_path=True))
change_road('D-BE',[(-160,45),(-160,35.5)])
y=next(q for q in S['loading_yards']if q['id']=='Y-BE');y['truck_stop']=[-160,35.5];y['cart_line']=LineString([y['truck_stop'],y['cart_dock']]);y=next(q for q in S['loading_yards']if q['id']=='Y-BW');y['truck_stop']=[-761.3,47.5];y['cart_line']=LineString([y['truck_stop'],y['cart_dock']]);y=next(q for q in S['loading_yards']if q['id']=='Y-C');y['truck_stop']=[-220,-250];y['cart_line']=LineString([y['truck_stop'],y['cart_dock']])
# Add only the changed approaches to the existing managed ROW; no unexplained new road is invented.
newarea=unary_union([q['polygon']for q in S['roads']]+[q['polygon']for q in S['turn_reservations']]);S['managed_parcels']=S['managed_parcels'].union(newarea);S['site_boundary']=S['site_boundary'].union(newarea.buffer(12));S['landscape_buffer']=S['site_boundary'].difference(S['managed_parcels']);D['vehicle_approach_changes']=CH
MODEL={'car':dict(length_m=4.8,width_m=1.9,wheelbase_m=2.8,rear_overhang_m=1.0,radius_m=6,height_m=2.1),'truck':dict(length_m=12.,width_m=2.5,wheelbase_m=6.,rear_overhang_m=3.,radius_m=12,height_m=4.2)}
RESULT=[];SWEEPS=[]
def record(id,scope,status,**kwargs):RESULT.append(dict(id=id,scope=scope,status=status,**kwargs))
def normalize(v):
 ll=math.hypot(*v);return(v[0]/ll,v[1]/ll)
def pose_body(pt,heading,m):
 u=(math.cos(heading),math.sin(heading));n=(-u[1],u[0]);rear=m['rear_overhang_m'];front=m['length_m']-rear;return Polygon([(pt[0]+u[0]*a+n[0]*b,pt[1]+u[1]*a+n[1]*b)for a,b in[(-rear,-m['width_m']/2),(front,-m['width_m']/2),(front,m['width_m']/2),(-rear,m['width_m']/2)]])
def fillet_poses(coords,m):
 # Rear axle follows tangent circular arcs, with radius fixed by the stated model.
 pts=[tuple(p)for p in coords];clean=[pts[0]]
 for p in pts[1:]:
  if math.dist(p,clean[-1])>.001:clean.append(p)
 pts=clean;turns=[]
 for i in range(1,len(pts)-1):
  a,b,c=pts[i-1:i+2];uin=normalize((b[0]-a[0],b[1]-a[1]));uout=normalize((c[0]-b[0],c[1]-b[1]));angle=math.acos(max(-1,min(1,uin[0]*uout[0]+uin[1]*uout[1])))
  if angle<1e-6:turns.append(None);continue
  if angle>math.pi-.01:return None,'180-degree reversal has no modelled turning path'
  tangent=m['radius_m']*math.tan(angle/2);cross=uin[0]*uout[1]-uin[1]*uout[0];sign=1 if cross>0 else -1;start=(b[0]-uin[0]*tangent,b[1]-uin[1]*tangent);end=(b[0]+uout[0]*tangent,b[1]+uout[1]*tangent);centre=(start[0]-uin[1]*sign*m['radius_m'],start[1]+uin[0]*sign*m['radius_m']);turns.append(dict(t=tangent,start=start,end=end,centre=centre,sign=sign,angle=angle))
 for i in range(len(pts)-1):
  left=turns[i-1]['t']if i>0 and turns[i-1]else 0;right=turns[i]['t']if i<len(turns)and turns[i]else 0
  if left+right>math.dist(pts[i],pts[i+1])+.001:return None,f'insufficient straight run {i}: tangent demand {left+right:.3f}m > {math.dist(pts[i],pts[i+1]):.3f}m'
 poses=[];last=pts[0];distance=0.
 def straight(a,b):
  nonlocal distance
  length=math.dist(a,b)
  if length<.001:return
  h=math.atan2(b[1]-a[1],b[0]-a[0]);steps=max(1,math.ceil(length/.25))
  for j in range(steps+1):
   t=j/steps;p=(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t)
   if distance+length*t>=m['rear_overhang_m']+.05:poses.append((p,h))
  distance+=length
 for tr in turns:
  if tr is None:continue
  straight(last,tr['start']);cen=tr['centre'];a0=math.atan2(tr['start'][1]-cen[1],tr['start'][0]-cen[0]);steps=max(2,math.ceil(tr['angle']/math.radians(.5)))
  for j in range(steps+1):
   a=a0+tr['sign']*tr['angle']*j/steps;p=(cen[0]+m['radius_m']*math.cos(a),cen[1]+m['radius_m']*math.sin(a));poses.append((p,a+tr['sign']*math.pi/2))
  distance+=m['radius_m']*tr['angle'];last=tr['end']
 straight(last,pts[-1]);return poses,None

def audit_route(id,coords,model,allowed):
 m=MODEL[model];poses,error=fillet_poses(coords,m)
 if error:record(id,'forward_arrival_2D','FAIL',reason=error);return
 shapes=[pose_body(p,h,m)for p,h in poses];swept=unary_union([a.union(b).convex_hull for a,b in zip(shapes,shapes[1:])]).buffer(.02);outside=swept.difference(allowed);ok=outside.area<EPS;record(id,'forward_arrival_2D','PASS_2D_SAMPLED'if ok else'FAIL',model=model,poses=len(poses),outside_m2=outside.area,radius_m=m['radius_m'],scope_limit='rear-axle planar arrival only; outbound/reversing/steering dynamics/3D not certified');SWEEPS.append(dict(id=id,model=model,line=LineString(coords),swept=swept,outside=outside,poses=poses[::max(1,len(poses)//80)],allowed=allowed.intersection(swept.buffer(5))))
customer=unary_union([q['polygon']for q in S['roads']if q['role']=='customer']+[q['polygon']for q in S['turn_reservations']if q['role']=='customer']+[f['vehicle_aisles']for fac in P['facilities']for f in fac['floors']if f['level']==0]+[S['old_A22']['vehicle_aisles']]);delivery=unary_union([q['polygon']for q in S['roads']if q['role']=='delivery']+[q['polygon']for q in S['turn_reservations']if q['role']=='delivery']+[q['polygon']for q in S['loading_yards']])
ROUTES=[('CAR-C-N',[(-1120,-625),(-583,-625),(-583,-600)]),('CAR-B-W',[(-1120,-625),(-1120,-25),(-1063,-25),(-1063,0)]),('CAR-B-S',[(-130,530),(-130,500),(-740,500),(-740,150),(-677,150),(-677,170)]),('CAR-A-S',[(-130,530),(-130,318),(-63,318),(-63,330)]),('CAR-A-E',[(500,100),(500,31),(465,31)]),('CAR-A-OLD22',[(-180,-105),(-180,-39),(-171,-39)])]
for id,pts in ROUTES:audit_route(id,pts,'car',customer)
TRUCKS=[('TRUCK-A',[(450,245),(260,245),(260,10),(237,10)]),('TRUCK-B-E',[(450,245),(-160,245),(-160,35.5)]),('TRUCK-B-W',[(450,245),(260,245),(260,-420),(-785,-420),(-785,47.5),(-761.3,47.5)]),('TRUCK-C',[(450,245),(260,245),(260,-420),(-190,-420),(-190,-250),(-220,-250)])]
for id,pts in TRUCKS:audit_route(id,pts,'truck',delivery)
# Check approach normals at actual car portals, not just touching the boundary tangentially.
for (id,pts),fac in zip(ROUTES[:5],['P-C-N','P-B-W','P-B-S','P-A-S','P-A-E']):
 q=next(q for q in P['facilities']if q['id']==fac);port=next(q for q in q['portals']if q['type']=='vehicle'and q['level']==0);u=normalize((pts[-1][0]-pts[-2][0],pts[-1][1]-pts[-2][1]));dot=sum(u[j]*port['normal'][j]for j in[0,1]);record(id+'-PORT','entry_normal_and_width','PASS_DIMENSION'if dot<-.999 else'FAIL',normal_dot=dot,port_width_m=port['width_m'])
# Every external parking ramp gets a numeric profile check; this is not an untested 3D swept pass.
for fac in P['facilities']:
 for ramp in fac['ramps']:
  profile=ramp['profile_xyz'];grade=max(abs(b[1]-a[1])/math.hypot(b[0]-a[0],b[2]-a[2])for a,b in zip(profile,profile[1:])if math.hypot(b[0]-a[0],b[2]-a[2])>.001);ok=grade<=.12 and ramp['width_m']>=MODEL['car']['width_m']+.5
  record(ramp['id'],'ramp_numeric_profile','PASS_DIMENSION'if ok else'FAIL',actual_max_grade=grade,width_m=ramp['width_m'],assumed_limit_grade=.12)
  record(ramp['id']+'-3D','pitch_ground_clearance_and_turns','NOT_TESTED',reason='crest/sag clearance, under-beam clearance, moving suspension and transition turning are not simulated')
for q in [read(R/'docs/b-completion-v2/geometry.json')['car_ramps'][0],next(q for q in S['roads']if q['id']=='D-C')]:
 record(q['id'],'ramp_width_gradient','PASS_DIMENSION'if q['max_gradient']<.12 and q['width_m']>=7 else'FAIL',max_gradient=q['max_gradient'],width_m=q['width_m']);record(q['id']+'-3D','3D_vehicle_sweep','NOT_TESTED',reason='only numeric grade/width and planar routes checked')
# Record each unverified bay, outbound path and B internal route honestly.
for fac in P['facilities']:
 for f in fac['floors']:
  for st in f['stalls']:record(st['id'],'individual_bay_in_out_reversing','NOT_TESTED',reason='no individual kinematic bay trajectory or opposite-traffic model executed')
for f in D['floors']:
 if f.get('parking'):
  for st in f['parking']['stalls']:record(st['id'],'individual_bay_in_out_reversing','NOT_TESTED',reason='B internal steering and individual bay reversing not simulated')
for st in S['old_A22']['stalls']:record(st['id'],'individual_bay_in_out_reversing','NOT_TESTED',reason='legacy bay geometry preserved; no reversing trajectory')
for id,_ in ROUTES+TRUCKS:record(id+'-OUT','outbound_exit_and_turnaround','NOT_TESTED',reason='arrival sweep is not proof of outbound/turnaround feasibility')
for f in D['floors']:
 if f.get('parking'):record('B-'+f['label']+'-INTERNAL','internal_car_steering','NOT_TESTED',reason='continuous aisle polygons do not establish a minimum-radius drivable path')
for id,g in [('customer_delivery',customer.intersection(delivery)),('roads_mall',customer.union(delivery).intersection(unary_union([f['shell']for f in D['floors']if f['level']==0]))),('truck_grade_ped',delivery.intersection(unary_union([q['polygon']for q in S['walks']])) )]:record(id,'network_separation','PASS_DIMENSION'if g.area<EPS else'FAIL',overlap_m2=g.area)
D['site']=S;write(O/'geometry.json',D);write(O/'vehicle-checks.json',RESULT);write(O/'vehicle-sweeps.json',SWEEPS);write(O/'vehicle-approach-changes.json',CH)
summary=dict(status_counts=dict(Counter(q['status']for q in RESULT)),checks=len(RESULT),failures=[q for q in RESULT if q['status']=='FAIL'],all_vehicle_movements_verified=False,unverified_is_not_pass=True,models=MODEL,sampling=dict(straight_step_m=.25,arc_step_degrees=.5,conservative_envelope_buffer_m=.02),original_parking_capacity=6699,vehicle_verified_capacity=None,arrival_routes=len(ROUTES)+len(TRUCKS),actual_vehicle_tests=0)
write(O/'vehicle-verification.json',summary);csvwrite(O/'vehicle-status-ledger.csv',['ID','検査範囲','状態','未検証/制限'],[[q['id'],q['scope'],q['status'],q.get('reason',q.get('scope_limit','寸法検査のみ'))]for q in RESULT]);print(json.dumps(summary,ensure_ascii=False,indent=2))
