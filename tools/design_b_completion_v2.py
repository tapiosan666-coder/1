"""B basement/roof supplement, with read-only v4.1 inputs and separate approval proposals."""
from site_v2_common import *
import copy,collections,ast,heapq,shapely
import numpy as np
O=R/'docs/b-completion-v2';O.mkdir(exist_ok=True)
B=read(R/'docs/b-v4-overlap-correction/geometry.json');BODY=affinity.translate(B['floors'][0]['shell'],-714,-30);CORES=[core_world(c)for c in B['cores']];CHECKS=[]
def ck(k,id,ok,value=None,level=None):CHECKS.append(dict(kind=k,id=id,pass_=bool(ok),value=value,level=level))
def cg(c,g):return affinity.translate(affinity.rotate(g,c['angle'],origin=(0,0)),*c['centre'])
def core_openings(c):
 # Two 2m stair flights, 0.30m treads, 16 risers each, front/return landings retained.
 return c['rooms']['lift'].buffer(-.1,join_style=2),cg(c,box(-11.65,-6.2,-6.35,-1.65))
OPENINGS=[];PROPOSALS=[]
for wing,path,levels in [('B',R/'docs/b-v4-overlap-correction/geometry.json',[0,1,2]),('A',R/'docs/a-detailed-design-v1/geometry.json',[-1,0,1,2,3])]:
 d=read(path);cs=CORES if wing=='B'else d['cores']
 for c in cs:
  ev,st=core_openings(c)
  for level in levels:
   orig=d['floors'][level]if wing=='B'else next(f for f in d['floors']if f['level']==level)
   plate=affinity.translate(orig['floor_plate'],-714,-30)if wing=='B'else orig['floor_plate'];cut=ev.union(st if level>-1 else Polygon());overlap=plate.intersection(cut).area
   PROPOSALS.append(dict(id=f'{wing}-CORE-{c["id"]}-{LABEL[level]}',wing=wing,level=level,label=LABEL[level],core=c['id'],kind='EV pit/shaft and two-flight stair opening'if level>-1 else 'EV shaft/pit',opening=cut,lift_opening=ev,stair_opening=st if level>-1 else Polygon(),solid_baseline_overlap_m2=overlap,requires_approval=overlap>EPS,applied_to_baseline=False,change_scope='既存室割り/扉/共用通路を維持し、構造床の穴だけを別案として分離',note='下端B1は階段下の基礎床を残す。EV内法の壁厚0.1mを保持。'))
# Existing clear escalator footprints can receive another stacked flight without enlarging a v4.1 opening.
NEW_ESC=[];BANKS=[]
for level,oldpair in[(-1,[1,2]),(3,[2,3])]:
 for src in B['escalators']:
  if src['levels']!=oldpair:continue
  e=translate_geoms(copy.deepcopy(src),-714,-30);e['c']=[src['c'][0]-714,src['c'][1]-30];e['levels']=[-1,0]if level==-1 else[2,3];e['id']=src['id']+('-B1-1F'if level==-1 else'-3F-RF');e['source_existing_opening']=src['id'];NEW_ESC.append(e)
 for src in B['bank_medians']:
  if src['levels']==oldpair:BANKS.append({**translate_geoms(copy.deepcopy(src),-714,-30),'levels':[-1,0]if level==-1 else[2,3]})
BASE_AXIS=LineString([(-706,55),(-655,44),(-620,31),(-586,45.5),(-530,65),(-454,46),(-429,40),(-401,59.4),(-360,79),(-312,62),(-280,46),(-244,38),(-234,35)])
CAR_AXIS=BASE_AXIS.offset_curve(3.7,join_style=2);PED_AXIS=BASE_AXIS.offset_curve(-3.5,join_style=2)
# A gentle, two-lane basement ramp from the new PB garage G0 north-east apron.
RAMP_LINE=LineString([(-540,170),(-540,100)]);RAMP=RAMP_LINE.buffer(3.5,cap_style=2);run=70.;grade=5.35/65.
RAMP_PROFILE=[dict(station_m=0,world_y=0),dict(station_m=5,world_y=-grade*2.5),dict(station_m=65,world_y=-5.35+grade*2.5),dict(station_m=70,world_y=-5.35)]
RAMPS=[dict(id='B1-CAR-RAMP',levels=[0,-1],width_m=7.,two_lane_width_m=3.25,median_m=.5,line=RAMP_LINE,polygon=RAMP,profile=RAMP_PROFILE,max_gradient=grade,transition_m=5,entry=[-540,170],exit=[-540,100],headroom_design_m=2.4,vehicle_height_limit_m=2.1,source_facility='P-B-S',status='new proposal, does not cut existing B 1F floor')]
# Reuse only the pure drawing grid class; no old generator is imported or executed.
_gsrc=(R/'tools/design_b_v4.py').read_text()
for _node in ast.parse(_gsrc).body:
 if isinstance(_node,ast.ClassDef)and _node.name=='Grid':exec(compile(ast.Module(body=[_node],type_ignores=[]),'read_only_grid','exec'),globals())
def prepare_grid(free,seed):
 parts=polys(free);component=min(parts,key=lambda p:p.distance(Point(seed)));grid=Grid(component);tree=grid.tree(seed);return grid,tree

def routed(grid,tree,end,free):
 start,dist,prev=tree;n=grid.near(end)
 if n not in dist:return None
 path=[grid.pt(n)]
 while n!=start:n=prev[n];path.append(grid.pt(n))
 path=path[::-1]
 # Greedy visibility pulling removes grid stair-steps while preserving exact centreline containment.
 out=[path[0]];i=0
 while i<len(path)-1:
  k=len(path)-1
  while k>i+1 and not free.buffer(.002).covers(LineString([path[i],path[k]])):k-=1
  out.append(path[k]);i=k
 ep=nearest_points(free,Point(end))[0]
 if math.dist(out[-1],[ep.x,ep.y])>.0001:out.append([ep.x,ep.y])
 if math.dist(out[-1],end)>.0001:out.append(list(end))
 return LineString(out)
FLOORS=[]
def make_store(id,poly,ep,u,n,name):
 front=rect(ep,u,6,1);q=lambda a,b:(ep[0]+u[0]*a+n[0]*b,ep[1]+u[1]*a+n[1]*b)
 depth=max((x-ep[0])*n[0]+(z-ep[1])*n[1]for x,z in poly.exterior.coords);back=poly.intersection(Polygon([q(-300,depth-5),q(300,depth-5),q(300,depth+1),q(-300,depth+1)]));end=back.buffer(-.6).representative_point();path=LineString([ep,end.coords[0]]);aisle=path.buffer(1.3).intersection(poly);sales=poly.difference(back);wall=poly.boundary.buffer(.125).difference(front)
 return dict(id=id,kind='retail',category=name,polygon=poly,entry=ep,door_width_m=6.,u=u,n=n,front=list(rect(ep,u,6,.01).exterior.coords)[:2],backroom=back,sales=sales,aisles=aisle,shelf_zones=sales.buffer(-.6).difference(aisle.buffer(.2)),main_route=list(path.coords),wall_solids=wall,back_door=list(path.intersection(back.boundary).representative_point().coords[0])if not path.intersection(back.boundary).is_empty else list(end.coords[0]))
for level in[-1,3]:
 label=LABEL[level];height=HEIGHT[level];esc=[e for e in NEW_ESC if level in e['levels']];evs=unary_union([core_openings(c)[0]for c in CORES]);stairs=unary_union([core_openings(c)[1]for c in CORES])if level==3 else Polygon();escalator_holes=unary_union([e['shaft']for e in esc]+[m['geom']for m in BANKS if level in m['levels']]);shafts=unary_union([evs,stairs,escalator_holes]);coreout=unary_union([c['outline']for c in CORES]);atrium=unary_union([affinity.translate(p['void'],-714,-30)for p in B['plazas']])if level==3 else Polygon();stores=[];program=[];gardens=[]
 if level==-1:
  stores=[make_store('BB1-MARKET',box(-747,16,-711,49),[-711,37],[0,1],[-1,0],'地下食品スーパー'),make_store('BB1-PICKUP',box(-232,7,-192,52),[-232,30],[0,1],[1,0],'食料品・大型受取カウンター')]
 else:
  # Roof gardens surround the existing lightwell projections; cars are kept away from the glass roof.
  for i,p in enumerate(B['plazas']):
   v=affinity.translate(p['void'],-714,-30);garden=v.buffer(9).difference(v.buffer(2));gardens.append(dict(id='BRF-GARDEN-'+str(i+1),name=p['name']+'屋上前庭',polygon=garden.intersection(BODY).difference(coreout),kind='roof_garden'))
  stores=[make_store('BRF-CAFE',box(-736,19,-712,37),[-712,28],[0,1],[-1,0],'屋上カフェ・休憩ラウンジ')]
 sky=atrium;private=unary_union([s['polygon']for s in stores]);gardenarea=unary_union([g['polygon']for g in gardens]);forbid=unary_union([coreout,shafts,sky.buffer(2),private,gardenarea])
 shell=BODY;vehicleaxis=CAR_AXIS.intersection(BODY.buffer(-3.6));pedaxis=PED_AXIS.intersection(BODY.buffer(-2.2));base_vehicle=vehicleaxis.buffer(3.25,cap_style=2).intersection(BODY).difference(forbid)
 # Ingress meets the garage/ramp at the same north-east bay, avoiding a new 1F opening.
 inlet=[(-540,100),(-540,66)]if level==-1 else[(-540,110),(-540,66)];inlet_line=LineString(inlet);base_vehicle=base_vehicle.union(inlet_line.buffer(3.5,cap_style=2)).intersection(BODY).difference(forbid)
 # Connected walking paths are routed inside the actual nonconvex body, not straight through its missing parts.
 ped_domain=BODY.difference(unary_union([coreout,private,shafts,sky])).buffer(-2.05)
 pg,ptree=prepare_grid(ped_domain,[-540,60]);pedparts=[];routes=[]
 targetspec=[]
 for k,point in enumerate(BASE_AXIS.coords):targetspec.append((label+f'-SPINE-{k}','地下買物/屋上前庭',point))
 for c in CORES:targetspec.append((label+'-'+c['id'],'トイレ・EV・階段前',c['entry']))
 for e in esc:
  for j,land in enumerate(e['landings']):targetspec.append((label+'-'+e['id']+f'-L{j}','エスカレーター乗降口',list(land.centroid.coords[0])))
 for st in stores:targetspec.append((st['id']+'-ACCESS',st['category']+'入口',st['entry']))
 if level==3:targetspec.append(('BRF-PB-PED','南立体屋上歩行橋',[-548,110]))
 for rid,name,point in targetspec:
  path=routed(pg,ptree,point,ped_domain)
  if path is not None:
   pedparts.append(path.buffer(2.,cap_style=2));routes.append(dict(id=rid,name=name,points=list(path.coords),width=4.,role='指定された店舗/乗降口/コア/前庭への保護歩行アクセス'))
 for e in esc:pedparts.extend(e['landings'])
 pedaxis=unary_union([LineString(r['points'])for r in routes]);car_domain=allowed_domain=BODY.difference(forbid).buffer(-3.55)
 vg,vtree=prepare_grid(car_domain,inlet[0]);vehicleaxis=LineString(inlet)
 base_vehicle=vehicleaxis.buffer(3.5,cap_style=2).intersection(BODY).difference(forbid)
 publicbase=unary_union(pedparts).intersection(BODY).difference(unary_union([coreout,private,shafts,sky]))
 allowed=BODY.difference(forbid);tiles=[];vparts=[base_vehicle];fparts=[publicbase]
 # A regular parking module is deliberately distinct from the irregular retail concourse.
 for ix,x in enumerate(range(-740,-220,40)):
  for iz,z in enumerate(range(-20,120,24)):
   tile=box(x,z,x+40,z+20.5)
   if not allowed.covers(tile):continue
   choices=[]
   for side in[0,40]:
    endpt=[x+side,z+10.25];nearest=nearest_points(car_domain,Point(endpt))[0]
    if nearest.distance(Point(endpt))>.25:continue
    conn=routed(vg,vtree,endpt,car_domain)
    if conn is not None and allowed.buffer(.003).covers(conn.buffer(3.25,cap_style=2)):choices.append((conn.length,side,conn))
   if not choices:continue
   _,side,conn=min(choices,key=lambda q:q[0]);aisle=box(x,z+7,x+40,z+13.5);sidecar=LineString([(x+side,z),(x+side,z+20.5)]).buffer(3.25,cap_style=2)
   vpoly=aisle.union(sidecar).union(conn.buffer(3.25,cap_style=2))
   if not allowed.buffer(.003).covers(vpoly):continue
   sx=x+4.1 if side==0 else x+35.9;footconn=routed(pg,ptree,[sx,z+10.25],ped_domain)
   if footconn is None:continue
   fp=footconn.buffer(.7,cap_style=2).union(LineString([(sx,z+1),(sx,z+19.5)]).buffer(.7,cap_style=2)).union(box(x+4.1,z,x+35.9,z+2)).union(box(x+4.1,z+18.5,x+35.9,z+20.5))
   if fp.difference(BODY).area>EPS or fp.intersection(forbid.difference(gardenarea)).area>EPS:continue
   tiles.append(dict(id=f'{label}-ROW-{ix:02}-{iz:02}',x=x,z=z,side=side,vehicle=vpoly,pedestrian=fp));vparts.append(vpoly);fparts.append(fp)
 vehicle=unary_union(vparts).difference(forbid);public=unary_union(fparts).difference(unary_union([coreout,shafts,sky,private]));crossings=public.intersection(vehicle);stalls=[]
 for tile in tiles:
  x,z=tile['x'],tile['z']
  for row in[0,1]:
   for k in range(12):
    p=box(x+5+k*2.5,z+2 if row==0 else z+13.5,x+7.5+k*2.5,z+7 if row==0 else z+18.5)
    if p.intersection(vehicle.union(public).union(forbid)).area>EPS:continue
    ep=[p.centroid.x,z+7 if row==0 else z+13.5];pe=[p.centroid.x,z+2 if row==0 else z+18.5];cat='EV'if len(stalls)%24==0 else'staff'if len(stalls)%13==0 else'standard'
    stalls.append(dict(id=f'P-B-{label}-{len(stalls)+1:04}',facility='P-B-'+label,level=level,height=height,row=tile['id'],category=cat,polygon=p,entry=ep,vehicle_entry=ep,pedestrian_entry=pe,width_m=2.5,length_m=5.0,u=[1,0],parking_direction=[0,-1]if row==0 else[0,1],marked=True))
 # A few 3.5m accessible bays with 1.5m lateral access replace pairs of ordinary bays, never overlap them.
 changed=[]
 for c in CORES:
  options=sorted(stalls,key=lambda s:Point(s['pedestrian_entry']).distance(Point(c['entry'])))
  done=False
  for s in options:
   if s not in stalls or s['category']=='accessible':continue
   p=s['polygon'];x0,z0,x1,z1=p.bounds;other=next((t for t in stalls if t['id']!=s['id']and abs(t['polygon'].bounds[0]-x1)<1e-8 and abs(t['polygon'].bounds[1]-z0)<1e-8),None)
   if other is None:continue
   ap=box(x0,z0,x0+3.5,z1);access=box(x0+3.5,z0,x0+5,z1)
   if ap.intersection(vehicle.union(public).union(forbid)).area>EPS:continue
   stalls.remove(other);s.update(category='accessible',polygon=ap,width_m=3.5,entry=[x0+1.75,s['entry'][1]],vehicle_entry=[x0+1.75,s['entry'][1]],pedestrian_entry=[x0+1.75,s['pedestrian_entry'][1]],side_access_aisle=access,side_access_width_m=1.5);public=public.union(access);changed.append(s['id']);done=True;break
  ck('accessible_bay_provided',c['id'],done,None,level)
 # Unique final IDs are assigned after paired bays were replaced.
 for i,s in enumerate(stalls,1):s['id']=f'P-B-{label}-{i:04}'
 # Unused building strips are non-public structure/MEP, not invented accessible rooms.
 used=unary_union([public,vehicle,private,coreout,shafts,sky]+[s['polygon']for s in stalls]+[g['polygon']for g in gardens]);residual=BODY.difference(used)
 program=[dict(id=f'{label}-SERVICE-{i+1}',name='設備・防水/配管・点検帯（非公開）',polygon=p,public=False,accessible_room=False)for i,p in enumerate(polys(residual))if p.area>.5]
 slab=BODY.difference(shafts.union(sky));guardrails=shafts.boundary.buffer(.05).union(sky.boundary.buffer(.05))
 f=dict(wing='B',level=level,label=label,height=height,shell=BODY,floor_plate=slab,public=public,walkable=public,void=sky,shafts=shafts,stores=stores,cores=CORES,escalators=esc,parking=dict(stalls=stalls,vehicle_aisles=vehicle,protected_pedestrian=public,crossings=crossings,rows=tiles,design_speed_kmh=10,vehicle_turn_radius_m=6),gardens=gardens,program=program,residual=residual,routes=routes,guardrails=guardrails,existing_middle_floors_modified=False)
 FLOORS.append(f)
 # Serialize and independently re-read later; current generation checks expose any issue immediately.
 ck('floor_geometry_valid',label,public.is_valid and vehicle.is_valid and slab.is_valid,None,level)
 ck('floor_excludes_openings',label,slab.intersection(shafts.union(sky)).area<EPS,slab.intersection(shafts.union(sky)).area,level)
 ck('public_on_supported_floor',label,public.difference(slab).area<EPS,public.difference(slab).area,level)
 main=max(polys(public.buffer(-.35)),key=lambda p:p.area)
 for c in CORES:ck('core_reaches_public',c['id'],main.distance(Point(c['entry']))<.8,main.distance(Point(c['entry'])),level)
 for e in esc:
  for j,land in enumerate(e['landings']):ck('escalator_landing_access',e['id']+str(j),main.distance(land.centroid)<.6,main.distance(land.centroid),level)
 for st in stores:ck('retail_entry_access',st['id'],main.distance(Point(st['entry']))<.8,main.distance(Point(st['entry'])),level)
 for s in stalls:
  ck('parking_vehicle_front_access',s['id'],vehicle.buffer(1e-7).covers(Point(s['vehicle_entry'])),None,level)
  ck('parking_rear_ped_access',s['id'],public.buffer(1e-7).covers(Point(s['pedestrian_entry'])),None,level)
  ck('parking_not_in_aisle',s['id'],s['polygon'].intersection(vehicle.union(public)).area<EPS,s['polygon'].intersection(vehicle.union(public)).area,level)
write(O/'geometry.json',dict(version='B basement and roof supplement v2',coordinate_system='World XZ metres',design_only=True,game_implemented=False,existing_B_v4_1_modified=False,floors=FLOORS,cores=CORES,escalators=NEW_ESC,bank_medians=BANKS,car_ramps=RAMPS,existing_core_opening_proposals=PROPOSALS,unverified=['実歩行・実車・構造荷重・排水・車両/EV動作・法規適合','B/A既存階のEV/階段床開口は未適用の別提案','新たなB地上来客入口は敷地側変更案で図示、基準は未変更']))
write(O/'checks.json',CHECKS);write(O/'core-opening-proposals.json',PROPOSALS)
rows=[s for f in FLOORS for s in f['parking']['stalls']]
csvwrite(O/'parking-ledger.csv',['ID','施設','階','用途','幅m','奥行m','車路口X','車路口Z','歩道口X','歩道口Z','polygon GeoJSON'],[[s['id'],s['facility'],LABEL[s['level']],s['category'],s['width_m'],s['length_m'],*s['vehicle_entry'],*s['pedestrian_entry'],json.dumps(mapping(s['polygon']))]for s in rows])
csvwrite(O/'core-opening-proposals.csv',['提案ID','館','階','コア','基準床との交差㎡','承認必要','原本適用'],[[p['id'],p['wing'],p['label'],p['core'],p['solid_baseline_overlap_m2'],p['requires_approval'],False]for p in PROPOSALS])
summary=dict(floors=[dict(level=f['level'],label=f['label'],stalls=len(f['parking']['stalls']),categories=dict(collections.Counter(s['category']for s in f['parking']['stalls'])),public_m2=f['public'].area,vehicle_m2=f['parking']['vehicle_aisles'].area,protected_crossings_m2=f['parking']['crossings'].area)for f in FLOORS],checks=len(CHECKS),failed=[c for c in CHECKS if not c['pass_']],baseline_core_opening_proposals=len(PROPOSALS),baseline_opening_not_applied=True)
write(O/'summary.json',summary);print(json.dumps(summary,ensure_ascii=False,indent=2))
