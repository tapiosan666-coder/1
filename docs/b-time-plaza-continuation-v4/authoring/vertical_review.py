"""Elevator access and escalator transfer studies. All facility changes are proposals, not runtime relocations."""
from pathlib import Path
import sys,json,math,itertools,csv,collections
sys.path.insert(0,'/workspace/1/tools');from site_v2_common import *
import numpy as np
import shapely
from shapely import maximum_inscribed_circle
from shapely.ops import nearest_points
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
P=Path(__file__).resolve().parents[1];O=P/'source/vertical-review';O.mkdir(exist_ok=True)
D=read(R/'docs/site-correction-v3/geometry.json');B=[f for f in D['floors']if f['wing']=='B'];mid=[f for f in B if f['level']in[0,1,2]];byl={f['level']:f for f in B}
def save(name,obj):(O/name).write_text(json.dumps(obj,default=encode,ensure_ascii=False,indent=2))
def svgpath(g):return' '.join(' '.join('M'+' L'.join(f'{x:.3f},{z:.3f}'for x,z in ring.coords)+' Z'for ring in [p.exterior,*p.interiors])for p in polys(g))
# Source lift groups and level consistency. These are NOT claims that runtime has functional lifts.
existing=[]
for c in mid[0]['cores']:
 stops=[]
 for f in B:
  cc=next(q for q in f['cores']if q['id']==c['id']);dev=next(q for q in f['vertical_devices']if q['core']==c['id']);target=cc['rooms']['ev_front_lobby'].representative_point();stops.append({'floor':f['label'],'height':f['height'],'shaft':dev['lift_opening'],'lobby':cc['rooms']['ev_front_lobby'],'target':[target.x,target.y],'opening_xz_consistent':dev['lift_opening'].equals_exact(next(q for q in B[0]['vertical_devices']if q['core']==c['id'])['lift_opening'],1e-7)})
 existing.append({'id':c['id'],'source_shaft':c['rooms']['lift'],'stops':stops,'runtime_usable_lifts':0,'runtime_status':'current independent scene seals core access; only K2 outline intersects crop, partly cut; no elevator controller/cabin installed'})
# Find a shaft footprint free of all middle-floor public/retail/core programs and all five-floor sales.
common=None
for f in mid:
 protected=unary_union([f['public'],f['void'],f['shafts'],*[s['polygon']for s in f['stores']],*[c['outline']for c in f['cores']],*[q['polygon']for q in f.get('service_zones',[])]]);free=f['floor_plate'].difference(protected);common=free if common is None else common.intersection(free)
all_vehicle=unary_union([f.get('parking',{}).get('vehicle_aisles',Polygon())for f in B if f.get('parking')]);all_stalls=unary_union([q['polygon']for f in B if f.get('parking')for q in f['parking'].get('stalls',[])]);all_staff=unary_union([q['line'].buffer(q['width_m']/2)for f in B for q in f.get('staff_routes',[])])
common=common.difference(unary_union([*[s['sales']for f in B for s in f['stores']],*[f['public']for f in B],all_vehicle,all_stalls,all_staff]));parts=[]
for g in polys(common.buffer(-2.85)):
 if not g.is_empty:parts.append(g)
# Explicit two alternative placements: central access first, eastern access second. No existing shaft moves.
proposed=[]
for id,ref in [('K4-TIME',Point(-464,62)),('K5-EAST',Point(-235,58))]:
 candidates=sorted([(nearest_points(ref,g)[1],common)for g in parts],key=lambda p:p[0].distance(ref));selected=None
 for center,zone in candidates:
  shaft=rect((center.x,center.y),(1,0),4,4)
  if not zone.buffer(.0001).covers(shaft):continue
  if any(shaft.intersects(q['shaft'])for q in proposed):continue
  options=[]
  for normal in[(1,0),(-1,0),(0,1),(0,-1)]:
   tangent=(-normal[1],normal[0]);door=np.array([center.x,center.y])+np.array(normal)*2;lobby_c=door+np.array(normal)*1.35;lobby=rect(lobby_c,tangent,3.6,2.4);goals=[];valid=True
   if shaft.union(lobby).intersection(all_vehicle.union(all_stalls)).area>1e-6:continue
   for f in mid:
    mask=f['nav_free'].buffer(-.31);target=nearest_points(Point(*lobby_c),mask)[1];line=LineString([tuple(lobby_c),(target.x,target.y)]);access=line.buffer(1.2,cap_style=2).union(lobby);allowed=f['floor_plate'].difference(unary_union([s['polygon']for s in f['stores']]+[c['outline']for c in f['cores']]+[q['polygon']for q in f.get('service_zones',[])]+[f['void'],f['shafts']]))
    ok=access.difference(allowed.buffer(.002)).area<.001 and line.length<12
    if not ok:valid=False;break
    goals.append({'level':f['level'],'floor':f['label'],'connection':[target.x,target.y],'target_lobby':[float(lobby_c[0]),float(lobby_c[1])],'line':line,'corridor':access,'corridor_width_m':2.4,'extra_distance_m':line.length,'design_geometry_check':ok})
   if valid:options.append((sum(g['extra_distance_m']for g in goals),normal,lobby,goals))
  if options:
   _,normal,lobby,goals=min(options,key=lambda q:q[0]);selected=(center,shaft,normal,lobby,goals);break
 if selected is None:
  proposed.append({'id':id,'status':'NO_FEASIBLE_4x4_SHAFT_AND_LOBBY_FOUND','shaft':Polygon(),'floors':[]});continue
 center,shaft,normal,lobby,goals=selected;floors=[]
 for f in B:
  sales=unary_union([s['sales']for s in f['stores']]);stock=unary_union([s['backroom']for s in f['stores']]);parking=f.get('parking')or{};vehicle=parking.get('vehicle_aisles',Polygon());stalls=unary_union([q['polygon']for q in parking.get('stalls',[])]);program=unary_union([q['polygon']for q in f.get('program',[])]);corr=next((q for q in goals if q['level']==f['level']),None)
  floors.append({'floor':f['label'],'level':f['level'],'height':f['height'],'opening':shaft,'floor_covers_opening':f['floor_plate'].buffer(.001).covers(shaft),'sales_overlap_m2':shaft.union(lobby).intersection(sales).area,'stock_overlap_m2':shaft.union(lobby).intersection(stock).area,'program_reallocation_m2':shaft.union(lobby).intersection(program).area,'named_service_overlap_m2':shaft.union(lobby).intersection(unary_union([q['polygon']for q in f.get('service_zones',[])])).area,'vehicle_overlap_m2':shaft.union(lobby).intersection(vehicle).area,'stall_overlap_m2':shaft.union(lobby).intersection(stalls).area,'lobby':lobby,'mid_floor_access':corr,'other_level_access':'B1/RF landing access and parking crossings need detailed design; not marked as reachable'if corr is None else None})
 proposed.append({'id':id,'center':[center.x,center.y],'shaft':shaft,'normal':normal,'lobby':lobby,'shaft_size_m':[4,4],'lobby_size_m':[3.6,2.4],'floors':floors,'status':'UNAPPROVED PROPOSAL ONLY. No current Godot elevator or drawing changed.','car_size_design_target_m':[2.0,2.4],'door_clear_design_target_m':1.4,'capacity':'manufacturer, queue demand, pit, overhead, structure, fire and controls NOT VERIFIED'})
# Planned escalator quartet around west side of TIME, adjacent transfer pairs, no major atrium change.
f2=byl[1];oldesc={e['id']:e for f in mid for e in f['escalators']if e['atrium']==2};escalators=[]
for id,cx in [('E2-12-UP',-455.3),('E2-23-UP',-452.3),('E2-12-DOWN',-449.3),('E2-23-DOWN',-446.3)]:
 e=oldesc[id];u=(0,1)if e['levels']==[0,1]else(0,-1);c=(cx,63);run=e['run_m'];shaft=rect(c,u,run,2.4);lands=[rect((cx,63+u[1]*sgn*8.9),u,3,3.6)for sgn in[-1,1]];body=rect(c,u,14.8,2.4);tests=[]
 for level in e['levels']:
  f=byl[level];support=f['floor_plate'].union(unary_union([ee['shaft']for ee in oldesc.values()])).difference(f['void'])
  tests.append({'level':level,'floor':f['label'],'unsupported_landing_m2':sum(l.difference(support).area for l in lands),'sales_overlap_m2':body.intersection(unary_union([s['sales']for s in f['stores']])).area,'furniture_interference_m2':body.union(unary_union(lands)).intersection(unary_union([q['geom']for q in f.get('furniture',[])])).area})
 escalators.append({'id':id,'old_center':e['c'],'new_center':c,'old_u':e['u'],'new_u':u,'levels':e['levels'],'direction':e['direction'],'run_m':run,'width_m':2.4,'inclination_deg':math.degrees(math.atan((byl[e['levels'][1]]['height']-byl[e['levels'][0]]['height'])/run)),'upper_floor_opening':shaft,'lower_floor_opening':Polygon(),'supported_lower_and_upper_comb_and_landings':lands,'body_projection':body,'tests':tests,'status':'PROPOSAL ONLY; not relocated in Godot','rule':'Opening only in the receiving upper floor ramp span. Do not cut the departure floor; keep combs and landings supported.'})
four_lane_alternative=escalators
# Preferred: stack the 2->3 pair directly above the existing 1->2 pair, same travel axis.
# Opposite travel-axis stacking at the same comb would collide at 2F, so it is not proposed.
escalators=[]
for id in ['E2-12-UP','E2-12-DOWN','E2-23-UP','E2-23-DOWN']:
 old=oldesc[id];reference=oldesc['E2-12-'+old['direction']];cx,cz=reference['c'];u=(0,1);opening=rect((cx,cz),u,old['run_m'],2.4);lands=[rect((cx,cz+sgn*8.9),u,3,3.6)for sgn in[-1,1]]
 tests=[]
 for level in old['levels']:
  f=byl[level];support=f['floor_plate'].union(unary_union([ee['shaft']for ee in oldesc.values()])).difference(f['void']);body=rect((cx,cz),u,14.8,2.4)
  tests.append({'level':level,'floor':f['label'],'unsupported_landing_m2':sum(l.difference(support).area for l in lands),'sales_overlap_m2':body.intersection(unary_union([s['sales']for s in f['stores']])).area,'furniture_interference_m2':body.union(unary_union(lands)).intersection(unary_union([q['geom']for q in f.get('furniture',[])])).area})
 escalators.append({'id':id,'old_center':old['c'],'new_center':[cx,cz],'old_u':old['u'],'new_u':u,'levels':old['levels'],'direction':old['direction'],'run_m':old['run_m'],'width_m':2.4,'upper_floor_opening':opening,'lower_floor_opening':Polygon(),'supported_lower_and_upper_comb_and_landings':lands,'body_projection':rect((cx,cz),u,14.8,2.4),'tests':tests,'status':'PREFERRED STACKED-BANK PROPOSAL ONLY; 1->2 pair position preserved, 2->3 pair not relocated in Godot','rule':'Only receiving floor ramp opening. Departure floors, combs and landings supported. Minimum nominal inter-bank underside clearance 5.35-0.85=4.50m, detailed engineering unverified.'})
new_floorplates=[]
oldtime=unary_union([e['shaft']for e in oldesc.values()])
for f in mid:
 otherholes=f['shafts'].difference(oldtime);receiving=unary_union([e['upper_floor_opening']for e in escalators if e['levels'][1]==f['level']]);plate=f['floor_plate'].union(oldtime.intersection(f['shell'])).difference(f['void'].union(otherholes)).difference(receiving)
 new_floorplates.append({'floor':f['label'],'level':f['level'],'opening':receiving,'floor_plate':plate,'major_void_overlap_m2':plate.intersection(f['void']).area,'landings_unsupported_m2':sum(l.difference(plate).area for e in escalators if f['level']in e['levels']for l in e['supported_lower_and_upper_comb_and_landings']),'status':'DRAWING PROPOSAL ONLY, original plates and validation mesh not changed'})
new_up_arrival=[-449,71.9];new_up_depart=[-449,54.1];old_up_arrival=[-449,71.9];old_up_depart=[-406,54.1]
# Raster + visibility injection: no failed target is projected into a passable region.
def graph(region,endpoints,aux,step=.75):
 shapely.prepare(region);x0,z0,x1,z1=region.bounds;xs=np.arange(x0+step/2,x1,step);zs=np.arange(z0+step/2,z1,step);xx,zz=np.meshgrid(xs,zs);inside=shapely.contains_xy(region,xx,zz);index=np.full(inside.shape,-1,dtype=np.int32);index[inside]=np.arange(inside.sum());coords=np.column_stack([xx[inside],zz[inside]]);nbase=len(coords);row=[];col=[];cost=[]
 for dx,dz in[(1,0),(0,1),(1,1),(1,-1)]:
  ya=slice(max(0,-dz),inside.shape[0]-max(0,dz));yb=slice(max(0,dz),inside.shape[0]-max(0,-dz));xa=slice(0,inside.shape[1]-dx);xb=slice(dx,inside.shape[1]);a=index[ya,xa].ravel();b=index[yb,xb].ravel();valid=(a>=0)&(b>=0);a=a[valid];b=b[valid]
  lines3=shapely.linestrings(np.stack([coords[a],coords[b]],axis=1));ok=shapely.covers(region,lines3);a=a[ok];b=b[ok];row.extend(a);col.extend(b);cost.extend([step*math.hypot(dx,dz)]*len(a))
 # Source door/lobby/route nodes bridge raster phase effects in narrow but geometrically valid openings.
 special=[];keys={};validity={}
 for key,pt in endpoints.items():validity[key]=region.covers(Point(pt));keys[key]=nbase+len(special);special.append(pt)
 seen={(round(p[0],5),round(p[1],5))for p in special}
 for pt in aux:
  key=(round(pt[0],5),round(pt[1],5))
  if key not in seen and region.covers(Point(pt)):special.append(pt);seen.add(key)
 extra=np.array(special,dtype=float);tree=cKDTree(coords)
 for i,p in enumerate(extra):
  if not region.covers(Point(p)):continue
  near=tree.query_ball_point(p,3.2)
  if not near:continue
  seg=shapely.linestrings(np.stack([np.repeat(p[None,:],len(near),axis=0),coords[near]],axis=1));ok=shapely.covers(region,seg)
  for j in np.array(near)[ok]:row.append(nbase+i);col.append(j);cost.append(float(np.linalg.norm(p-coords[j])))
 extree=cKDTree(extra)
 for i,j in extree.query_pairs(3.2):
  if region.covers(LineString([extra[i],extra[j]])):row.append(nbase+i);col.append(nbase+j);cost.append(float(np.linalg.norm(extra[i]-extra[j])))
 total=nbase+len(extra);rr=np.array(row+col);cc=np.array(col+row);vv=np.array(cost+cost);csr=coo_matrix((vv,(rr,cc)),shape=(total,total)).tocsr();return csr,np.vstack([coords,extra]),keys,validity
rows=[];routes=[];old_transfer=None;new_transfer=None
for f in B:
 region=f['nav_free'].buffer(-.30);end={};anchors=[];aux=[]
 for c in f['cores']:
  target=c['rooms']['ev_front_lobby'].representative_point();end[c['id']]=(target.x,target.y)
  for name in['front_lobby','lift_access','ev_front_lobby','lift_lobby']:
   p=c['rooms'][name].representative_point();aux.append((p.x,p.y))
  for door in c.get('doors',[]):
   pp=door.get('p')
   if pp:aux.append(tuple(pp))
 for route in f.get('routes',[]):
  line=LineString(route['points'])
  for distance in np.arange(0,line.length,.7):p=line.interpolate(distance);aux.append((p.x,p.y))
 for sid,p in [('PLAZA-W',(-655,30.5)),('PLAZA-T',(-449,46)),('PLAZA-L',(-314,46))]:
  if f['level']in[0,1,2]:end[sid]=p;anchors.append(sid)
 for s in f['stores']:
  if s['polygon'].area<500 and f['level']in[0,1,2]:continue
  a=(s['entry'][0]-s['n'][0]*.8,s['entry'][1]-s['n'][1]*.8);end[s['id']]=a;anchors.append(s['id'])
 for door in f.get('doors_v3',[]):end[door['id']]=tuple(door['inside_anchor']);anchors.append(door['id'])
 for p in proposed:
  if not p['floors']:continue
  detail=next(q for q in p['floors']if q['level']==f['level'])['mid_floor_access']
  if detail:end[p['id']]=tuple(detail['connection'])
 if f['level']==1:
  for key,p in [('OLD-TRANSFER-A',old_up_arrival),('OLD-TRANSFER-B',old_up_depart),('NEW-TRANSFER-A',new_up_arrival),('NEW-TRANSFER-B',new_up_depart)]:end[key]=tuple(p)
 csr,coords,keys,valid=graph(region,end,aux);sources=[id for id in['K1','K2','K3','K4-TIME','K5-EAST']if id in keys];dist,pred=dijkstra(csr,directed=False,indices=[keys[k]for k in sources],return_predecessors=True);lookup={s:i for i,s in enumerate(sources)}
 for anchor in anchors:
  options={}
  for lift in sources:
   d=dist[lookup[lift],keys[anchor]]
   if not valid[anchor]or not valid[lift]or not math.isfinite(d):options[lift]=None;continue
   extra=0
   if lift.startswith(('K4','K5')):extra=next(q for q in next(p for p in proposed if p['id']==lift)['floors']if q['level']==f['level'])['mid_floor_access']['extra_distance_m']
   options[lift]=float(d+extra)
  def pick(ids):
   vals=[(options[k],k)for k in ids if options.get(k)is not None];return min(vals)if vals else(None,None)
  before,oldid=pick(['K1','K2','K3']);central,centralid=pick(['K1','K2','K3','K4-TIME']);after,newid=pick(sources);rows.append({'floor':f['label'],'anchor':anchor,'world_x_m':end[anchor][0],'world_y_m':f['height'],'world_z_m':end[anchor][1],'old_plan_distance_m':before,'old_lift':oldid,'add_central_only_plan_m':central,'add_central_and_east_plan_m':after,'proposed_lift':newid,'plan_reduction_m':before-after if before is not None and after is not None else None,'current_Godot_lift_distance':'NOT_AVAILABLE: zero functional lifts in current validation scene','proposed_Godot_distance':'NOT_TESTED: proposal not implemented','method':'0.75m raster with exact segment containment and explicit doorway nodes; 0.30m capsule radius. No endpoint projection; invalid/disconnected points remain null.'})
 if f['level']==1:
  for mode in['OLD','NEW']:
   a,b=keys[mode+'-TRANSFER-A'],keys[mode+'-TRANSFER-B'];dd,pp=dijkstra(csr,directed=False,indices=a,return_predecessors=True);path=[]
   if math.isfinite(dd[b]):
    n=b
    while n!=a:path.append(list(coords[n]));n=pp[n]
    path.append(list(coords[a]));path.reverse()
   record={'kind':mode,'distance_m':float(dd[b])if math.isfinite(dd[b])else None,'points_world_xz':path,'status':'2D DESIGN DISTANCE, not human operation','capsule_radius_m':.3,'floor':'2F'};routes.append(record)
  old_transfer,new_transfer=routes[-2:]
 print('VERTICAL_DISTANCE_FLOOR',f['label'],'anchors',len(anchors),'nodes',csr.shape[0],flush=True)
# Draw all existing devices plus proposed central lift and four relocated banks.
for f in mid:
 x0,z0,x1,z1=f['shell'].bounds;parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0-8} {z0-8} {x1-x0+16} {z1-z0+16}" width="1800" height="750"><path d="{svgpath(f["public"])}" fill="#e1eae3" stroke="#71846f" stroke-width=".15"/>']
 for c in f['cores']:p=c['rooms']['lift'];q=p.centroid;parts.append(f'<path d="{svgpath(p)}" fill="#b08057"/><text x="{q.x}" y="{q.y}" font-size="3">{c["id"]}</text>')
 for p in proposed:
  if not p['floors']:continue
  q=p['shaft'].centroid;parts.append(f'<path d="{svgpath(p["shaft"])}" fill="#4f869a"/><text x="{q.x}" y="{q.y}" font-size="3">{p["id"]}</text>')
  detail=next(q for q in p['floors']if q['level']==f['level'])['mid_floor_access']
  if detail:parts.append(f'<path d="{svgpath(detail["corridor"])}" fill="#a7cbd4"/>')
 for e in f['escalators']:parts.append(f'<path d="{svgpath(e["shaft"])}" fill="#c7a381"/>')
 for e in escalators:
  if f['level']in e['levels']:parts.append(f'<path d="{svgpath(e["body_projection"])}" fill="#588e9d"/>')
 parts.append('</svg>');(O/(f['label']+'-vertical.svg')).write_text(''.join(parts))
summary={'existing_lift_shafts':len(existing),'planned_stops':sum(len(q['stops'])for q in existing),'actual_functional_lifts_in_validation':0,'existing':existing,'proposed':proposed,'escalator_proposal':escalators,'proposed_floorplates':new_floorplates,'four_lane_alternative_not_recommended':{'devices':four_lane_alternative,'reason':'About 3m transfer but compresses adjacent circulation to roughly 2.6m/4.2m. Do not adopt without traffic and frontage review. Preferred stacked banks preserve existing bay width.'},'transfer_comparison':routes,'distance_rows':rows,'changes_applied_to_drawings':False,'changes_applied_to_Godot':False,'uncertainties':['Manufacturers, queue/demand and elevator capacity','B1/RF access and parking-crossing adjustments','Structural pit/overhead and openings','New escalator machine envelope/headroom and exact physical support','All distances are plan studies, not post-relocation Godot walking']};save('vertical-review.json',summary)
with open(O/'elevator-distances.csv','w',newline='',encoding='utf-8-sig')as o:w=csv.DictWriter(o,rows[0].keys(),lineterminator='\n');w.writeheader();w.writerows(rows)
save('transfer-routes.json',routes)
print('LIFT_PROPOSALS',[(p['id'],p.get('center'),p['status'])for p in proposed]);print('TRANSFER',[(r['kind'],r['distance_m'])for r in routes])
