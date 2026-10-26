"""External parking modules only. No mall/game resources are modified."""
from pathlib import Path
import sys,json,math,csv,copy,hashlib,collections
sys.path.append('/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
import numpy as np
from shapely.geometry import Polygon,LineString,Point,box,mapping
from shapely.ops import unary_union,nearest_points
R=Path(__file__).resolve().parents[1];O=R/'docs/parking-blocks-v2';O.mkdir(exist_ok=True)
H=[0.,2.75,5.525,8.2,10.875,13.625,16.4];EPS=1e-8
SPECS=[dict(id='P-A-E',name='A東立体駐車場',kind='garage',block=(300,-20,480,220),x=315,z=20,w=120,h=156,vehicle=(465,31),vehicle_normal=(1,0),ped=(315,100),ped_normal=(-1,0),bridge=None),dict(id='P-B-S',name='B南立体駐車場',kind='garage',block=(-700,170,-460,350),x=-684,z=170,w=144,h=120,vehicle=(-677,170),vehicle_normal=(0,-1),ped=(-630,170),ped_normal=(0,-1),bridge=(-540,170)),dict(id='P-C-N',name='C北平面駐車場',kind='surface',block=(-650,-650,-260,-440),x=-590,z=-600,w=244,h=102,vehicle=(-583,-600),vehicle_normal=(0,-1),ped=(-468,-498),ped_normal=(0,1),bridge=None),dict(id='P-B-W',name='B西平面駐車場',kind='surface',block=(-1110,-40,-820,190),x=-1070,z=0,w=198,h=120,vehicle=(-1063,0),vehicle_normal=(0,-1),ped=(-872,60),ped_normal=(1,0),bridge=None),dict(id='P-A-S',name='A南平面駐車場',kind='surface',block=(-100,300,230,490),x=-70,z=330,w=216,h=138,vehicle=(-63,330),vehicle_normal=(0,-1),ped=(38,330),ped_normal=(0,-1),bridge=None)]
CHECKS=[]
def ck(k,id,ok,val=None):CHECKS.append(dict(kind=k,id=id,pass_=bool(ok),value=val))
def polys(g):return[]if g.is_empty else[g]if g.geom_type=='Polygon'else[p for p in getattr(g,'geoms',[])if p.geom_type=='Polygon']
def enc(v):
 if hasattr(v,'geom_type'):return mapping(v)
 if isinstance(v,np.generic):return v.item()
 raise TypeError(type(v))
def rect(c,u,l,w):
 n=(-u[1],u[0]);return Polygon([(c[0]+u[0]*a+n[0]*b,c[1]+u[1]*a+n[1]*b)for a,b in[(-l/2,-w/2),(l/2,-w/2),(l/2,w/2),(-l/2,w/2)]])
FAC=[]
for s in SPECS:
 x,z,w,h=s['x'],s['z'],s['w'],s['h'];fid=s['id'];garage=s['kind']=='garage';main=box(x,z,x+w,z+h);annex=unary_union([box(x+w,z+4,x+w+30,z+18.5),box(x+w+7.5,z+18.5,x+w+19.5,z+46.5),box(x+w,z+46.5,x+w+30,z+60)])if garage else Polygon();shell=main.union(annex);levels=range(7)if garage else[0]
 aislez=list(np.arange(z+14,z+h-11.99,19.6))
 accessible_row=(2*(len(aislez)-1)-1 if fid=='P-C-N'else 2*min(range(len(aislez)-1),key=lambda k:abs((aislez[k]+9.8)-s['ped'][1]))if fid=='P-B-W'else 0)
 spur=box(x+w/2-1,z+1,x+w/2+1,aislez[0]+10.8)if fid=='P-A-S'else box(x+w/2-1,aislez[-2]+8.8,x+w/2+1,z+h-1)if fid=='P-C-N'else Polygon()
 aisles=[box(x+4,zz-3,x+w-4,zz+3)for zz in aislez]+[box(x+4,z+3,x+10,z+h-3),box(x+w-10,z+3,x+w-4,z+h-3)];pedparts=[box(x+12,z+1,x+14,z+h-1),box(x+w-14,z+1,x+w-12,z+h-1),box(x+12,z+1,x+w-12,z+3),box(x+12,z+h-3,x+w-12,z+h-1)];rows=[];columns=[];side_access=[];stalls=[];pedparts.append(spur)
 for band,(a,b)in enumerate(zip(aislez,aislez[1:])):
  pedparts.append(box(x+12,a+8.8,x+w-12,a+10.8))
  for side,front in[(1,a+3),(-1,b-3)]:
   ri=len(rows);cursor=x+20;rowstalls=[]
   while cursor+2.5<=x+w-20+1e-9:
    i=len(rowstalls);cat='general';width=2.5;length=5.
    if ri==accessible_row and((cursor>=x+w-60)if fid=='P-B-W'else(abs(cursor-(x+w/2))<=25)if fid in['P-C-N','P-A-S']else(i<4 or cursor>=x+w-40)):cat='accessible';width=3.5
    elif ri in[0,1]and i<6:cat='EV';width=2.7;length=5.2
    elif ri%3==2:cat='comfort';width=2.7;length=5.2
    elif ri>=2*(len(aislez)-1)-2 and i<6:cat='staff'
    extra=1.2 if cat=='accessible'else 0.
    if cursor+width+extra>x+w-20+1e-8:break
    low,high=(front,front+length)if side==1 else(front-length,front);p=box(cursor,low,cursor+width,high);entry=[cursor+width/2,front];rear=[entry[0],front+side*length];rear_target=[entry[0],a+8.8 if side==1 else a+10.8];access=box(cursor+width,min(front,front+side*5.8),cursor+width+1.2,max(front,front+side*5.8))if extra else Polygon()
    if not spur.is_empty and p.intersection(spur.buffer(.2)).area>EPS:
     cursor+=width+extra;continue
    if extra:side_access.append(access)
    rowstalls.append(dict(id=f'{fid}-TEMP-{ri}-{i}',facility=fid,row=ri,category=cat,polygon=p,entry=entry,vehicle_entry=entry,pedestrian_entry=rear,pedestrian_access_link=LineString([rear,rear_target]),width_m=width,length_m=length,u=[1,0],parking_direction=[0,side],side_access_aisle=access,side_access_width_m=extra,charging=cat=='EV',marked=True));cursor+=width+extra
   rows.append(dict(id=f'{fid}-ROW-{ri}',front_z=front,side=side,band=band,stalls=len(rowstalls)));stalls+=rowstalls
   # Posts sit in the 0.6m service curb, behind parked cars and outside the protected rear walkway.
   bounds=sorted(set([p['polygon'].bounds[0]for p in rowstalls]+[p['polygon'].bounds[2]for p in rowstalls]));curbz=a+8.5 if side==1 else a+11.1
   for nominal in np.arange(x+20,x+w-19,12.5):
    if not bounds:continue
    cx=min(bounds,key=lambda v:abs(v-nominal));column=box(cx-.2,curbz-.2,cx+.2,curbz+.2)
    if any(column.intersects(q)for q in side_access)or column.intersects(spur):continue
    columns.append(column)
 pedparts+=side_access
 cores=[]
 for ci,(cx,cz,ev,frontside)in enumerate([(x+16,z+3,True,1),(x+w-28,z+3,True,1),(x+16,z+h-11,False,-1),(x+w-28,z+h-11,False,-1)]if garage else[]):
  outline=box(cx,cz,cx+12,cz+8);stair=box(cx+.4,cz+.4,cx+5.6,cz+6.8);lift=box(cx+6,cz+.4,cx+9,cz+3.4)if ev else Polygon();lobby=box(cx+5.5,cz+3.3,cx+12,cz+8);entry=[cx+11,cz+6];stair_entry=[cx+5.6,cz+5.3];lift_entry=[cx+7.5,cz+3.4]if ev else None
  # Lobbies connect sideways to an existing protected spine; they do not require crossing parking bays.
  px=x+13 if ci%2==0 else x+w-13
  points=([entry,[cx+13,entry[1]],[cx+13,z+2]]if ci==0 else[entry,[cx+13,entry[1]],[cx+13,z+h-2]]if ci==2 else[entry,[px,entry[1]]])
  link=LineString(points).buffer(1,cap_style=2,join_style=2);pedparts.extend([lobby,link]);cores.append(dict(id=f'{fid}-K{ci+1}',outline=outline,stair=stair,elevator=lift,public_lobby=lobby,entry=entry,stair_entry=stair_entry,elevator_entry=lift_entry,stair_clear_width_m=2.,tread_m=.30,landing_m=1.5,risers_per_storey=16,flights=2,risers_per_flight=8,levels=list(levels)))
 # Landings occupy separate up/down lanes in an annex. A floor must circulate back to the low end to climb another flight.
 ramp_lanes=[];ramps=[]
 if garage:
  for lane,cx in[('UP',x+w+10),('DOWN',x+w+17)]:
   shaft=box(cx-2,z+18.5,cx+2,z+46.5);landlow=box(cx-2,z+8,cx+2,z+18.5);landhigh=box(cx-2,z+46.5,cx+2,z+56);ramp_lanes.append(dict(direction=lane,shaft=shaft,landings=[landlow,landhigh],lower_port=[cx,z+11],upper_port=[cx,z+53],width_m=4.))
   aisles.extend([landlow,landhigh,box(x+w-10,z+8,x+w+26,z+14),box(x+w-10,z+50,x+w+26,z+56)])
   for lo in range(6):
    rise=H[lo+1]-H[lo];grade=rise/25.;stations=sorted(set([*np.linspace(0,3,13),*np.linspace(3,25,23),*np.linspace(25,28,13)]));heights=[grade*t*t/6 if t<=3 else grade*(1.5+t-3)if t<=25 else grade*(23.5+(t-25)-(t-25)**2/6)for t in stations];profile=[[cx,H[lo]+yy,z+18.5+rr]for rr,yy in zip(stations,heights)]
    ramps.append(dict(id=f'{fid}-R{lo}-{lane}',from_level=lo if lane=='UP'else lo+1,to_level=lo+1 if lane=='UP'else lo,direction=lane,shaft=shaft,landings=[landlow,landhigh],lower_port=[cx,z+11],upper_port=[cx,z+53],lower_y=H[lo],upper_y=H[lo+1],width_m=4.,transition_run_m=3.,constant_run_m=22.,horizontal_run_m=28.,rise_m=rise,max_grade_percent=grade*100.,profile_xyz=profile,profile_note='緩和3m/直線22m/緩和3m。下端10.5m/上端9.5m水平平場。DOWNは同じ低→高断面を逆向きに走る。'))
 # Ground vehicle entry and protected pedestrian entry, separated by location. All crossings remain explicit.
 vehicle_port=s['vehicle'];ped_port=s['ped'];vehicle_ext=LineString([vehicle_port,[x+7,z+12]]).buffer(3,cap_style=2)if fid!='P-A-E'else box(x+w-10,z+8,x+w+30,z+14)
 aisles.append(vehicle_ext)
 if s['ped_normal'][0]:px=x+13 if s['ped_normal'][0]<0 else x+w-13;pedparts.append(LineString([ped_port,[px,ped_port[1]]]).buffer(1.5,cap_style=2))
 elif s['ped_normal'][1]<0:pedparts.append(LineString([ped_port,[ped_port[0],z+2]]).buffer(1.5,cap_style=2))
 else:pedparts.append(LineString([ped_port,[ped_port[0],z+h-2]]).buffer(1.5,cap_style=2))
 vehicle=unary_union(aisles);ped=unary_union(pedparts).difference(unary_union(columns));shaftunion=unary_union([q['shaft']for q in ramp_lanes]);core_shafts=unary_union([q['stair'].union(q['elevator'])for q in cores]);cross=ped.intersection(vehicle);protected=ped.difference(vehicle);columngeo=unary_union(columns)
 floors=[]
 for level in levels:
  floorvehicle=vehicle;floorshell=shell;bridge=None
  if garage and fid=='P-B-S'and level in[0,6]:
   bridge=box(-543.5,z,-536.5,z+6).union(LineString([[-540,z+6],[-547,z+12]]).buffer(3.5,cap_style=2,join_style=2));floorvehicle=floorvehicle.union(bridge);floorshell=floorshell.union(bridge)
   if level==6:
    ped_rf=box(-550,z,-546,z+4).union(box(-554,z+1,-546,z+4));ped=ped.union(ped_rf)
  terminal=unary_union([box(l['shaft'].bounds[0]-.2,(z+46.5 if level==0 else z+18.3),l['shaft'].bounds[2]+.2,(z+46.7 if level==0 else z+18.5))for l in ramp_lanes])if garage and level in[0,6]else Polygon()
  floorvehicle=floorvehicle.difference(terminal)
  mouth_rules=[dict(direction=l['direction'],lower_port=l['lower_port'],upper_port=l['upper_port'],lower_role=('closed-no-upper-deck'if level==6 else'departure-to-next'if l['direction']=='UP'else'arrival-from-next'),upper_role=('closed-no-lower-deck'if level==0 else'arrival-from-below'if l['direction']=='UP'else'departure-to-below'))for l in ramp_lanes]
  floorcross=ped.intersection(floorvehicle);floorstalls=[]
  for k,st in enumerate(stalls,1):
   st=copy.deepcopy(st);st['id']=f'{fid}-L{level:02}-{k:04}';st['level']=level;st['height']=H[level]if garage else 0.;floorstalls.append(st)
  # Floor plate excludes the real vertical circulation/open ramps; landings remain physical floor.
  plate=floorshell.difference(shaftunion.union(core_shafts));pedfree=ped.difference(core_shafts)
  guardbase=floorshell.boundary.buffer(.12).intersection(floorshell);carcuts=vehicle_ext.buffer(.1)if level==0 else Polygon()
  if bridge is not None:carcuts=carcuts.union(bridge.buffer(.1))
  normal=s['ped_normal'];axis=(-normal[1],normal[0]);pedcut=rect(s['ped'],axis,3.,1.)if level==0 or(garage and level in[2,4,6])else Polygon()
  if fid=='P-B-S'and level==6:pedcut=pedcut.union(box(-550.1,z-.5,-545.9,z+.5))
  guard=guardbase.difference(carcuts.union(pedcut));temporary=guardbase.intersection(pedcut)if level>0 else Polygon()
  fr=dict(level=level,label=f'P{level+1}'if garage else'GROUND',height=H[level]if garage else 0.,mall_level={0:0,2:1,4:2,6:3}.get(level)if garage else 0,shell=floorshell,main=main,vehicle_aisles=floorvehicle,pedestrian=pedfree,protected_pedestrian=pedfree.difference(floorvehicle),crossings=floorcross,ramp_openings=shaftunion,ramp_terminal_barriers=terminal,ramp_mouth_rules=mouth_rules,vertical_shafts=core_shafts,floor_plate=plate,stalls=floorstalls,cores=cores,columns=columngeo,rows=rows,roof=garage and level==6,roof_vehicle_bridge_portal=dict(point=s['bridge'],width_m=7.,normal=[0,-1])if bridge is not None and level==6 else None,ground_basement_ramp_portal=dict(point=s['bridge'],width_m=7.,normal=[0,-1])if bridge is not None and level==0 else None,edge_guard=guard,temporary_guard_until_bridge_built=temporary,ramp_side_barriers=unary_union([box(l['shaft'].bounds[0]-.2,l['shaft'].bounds[1],l['shaft'].bounds[0],l['shaft'].bounds[3]).union(box(l['shaft'].bounds[2],l['shaft'].bounds[1],l['shaft'].bounds[2]+.2,l['shaft'].bounds[3]))for l in ramp_lanes]),ramp_barrier_height_m=1.1,wheelstop_height_m=.15,edge_guard_height_m=1.2 if garage else.15,assumed_structure_depth_m=.30,assumed_service_zone_m=.15,vehicle_height_limit_m=2.0 if garage else None)
  floors.append(fr)
  # Each aisle network and each pedestrian network is connected; access endpoints belong to those same components.
  comp=max(polys(floorvehicle.buffer(.001)),key=lambda p:p.area);pedcomp=max(polys(pedfree.buffer(.001)),key=lambda p:p.area)
  ck('vehicle_network_single_component',f'{fid}/{level}',len(polys(floorvehicle.buffer(.001)))==1,len(polys(floorvehicle.buffer(.001))))
  ck('pedestrian_network_single_component',f'{fid}/{level}',len(polys(pedfree.buffer(.001)))==1,len(polys(pedfree.buffer(.001))))
  ck('ped_vehicle_overlap_only_marked_crossing',f'{fid}/{level}',pedfree.intersection(floorvehicle).difference(floorcross).area<EPS,pedfree.intersection(floorvehicle).difference(floorcross).area)
  ck('pedestrian_not_in_open_ramp',f'{fid}/{level}',pedfree.intersection(shaftunion).area<EPS,pedfree.intersection(shaftunion).area)
  ck('vehicle_excludes_closed_ramp_mouth',f'{fid}/{level}',floorvehicle.intersection(terminal).area<EPS,floorvehicle.intersection(terminal).area)
  ck('plate_excludes_openings',f'{fid}/{level}',plate.intersection(shaftunion.union(core_shafts)).area<EPS)
  for st in floorstalls:
   p=st['polygon'];ve=Point(st['vehicle_entry']);line=st['pedestrian_access_link'];rear=Point(st['pedestrian_entry']);ck('stall_vehicle_access',st['id'],comp.distance(ve)<.01,comp.distance(ve));ck('stall_pedestrian_rear_access',st['id'],pedcomp.distance(rear)<=.81,pedcomp.distance(rear));ck('stall_no_vehicle_lane_overlap',st['id'],p.intersection(floorvehicle).area<EPS,p.intersection(floorvehicle).area);ck('stall_no_core_ramp_overlap',st['id'],p.intersection(shaftunion.union(core_shafts)).area<EPS);ck('stall_column_clear',st['id'],p.intersection(columngeo).area<EPS);ck('ped_rear_link_column_clear',st['id'],line.intersection(columngeo).length<EPS)
  for c in cores:
   ck('core_lobby_reachable',f'{fid}/{level}/{c["id"]}',pedcomp.distance(Point(c['entry']))<.01,pedcomp.distance(Point(c['entry'])))
   ck('stair_door_reachable',f'{fid}/{level}/{c["id"]}',pedcomp.distance(Point(c['stair_entry']))<.01,pedcomp.distance(Point(c['stair_entry'])))
   if c['elevator_entry']:ck('lift_door_reachable',f'{fid}/{level}/{c["id"]}',pedcomp.distance(Point(c['elevator_entry']))<.01,pedcomp.distance(Point(c['elevator_entry'])))
  if garage:
   for lane in ramp_lanes:
    for j,pt in enumerate([lane['lower_port'],lane['upper_port']]):ck('ramp_port_reachable',f'{fid}/{level}/{lane["direction"]}/{j}',comp.distance(Point(pt))<.01,comp.distance(Point(pt)))
  if bridge is not None:
   carspan=LineString([[-543.5,z],[-536.5,z]]);ck('vehicle_receiver_full_width_supported',fid+str(level),floorshell.buffer(1e-8).covers(carspan));ck('vehicle_receiver_connected',fid+str(level),comp.distance(Point(s['bridge']))<.01)
   if level==6:
    pedspan=LineString([[-550,z],[-546,z]]);ck('RF_ped_receiver_full_width_supported',fid,floorshell.buffer(1e-8).covers(pedspan));ck('RF_vehicle_ped_receivers_separated',fid,ped_rf.intersection(bridge).area<EPS,ped_rf.intersection(bridge).area)
  ck('all_marked_stalls_inside_facility',f'{fid}/{level}',all(floorshell.buffer(.001).covers(q['polygon'])for q in floorstalls))
 # Exact corner-turn footprint checks for a 4.8x2.0m design car, R6m axle-centre template. Not a driving simulation.
 turns=[]
 for zz in aislez:
  for right in[False,True]:
   for below in[-1,1]:
    cx=x+w-13 if right else x+13;sign=-1 if right else 1;cz=zz+below*6;poses=[]
    for t in np.linspace(0,math.pi/2,25):
     px=cx-sign*6*math.cos(t);pz=cz-below*6*math.sin(t);u=[sign*math.sin(t),-below*math.cos(t)];poses.append(rect((px,pz),u,4.8,2.0))
    swept=unary_union(poses);outside=swept.difference(vehicle.buffer(.001)).area;ck('corner_car_envelope_R6',fid+f'/{zz}/{right}/{below}',outside<EPS,outside);turns.append(dict(centre=[cx,cz],radius_m=6.,car_length_m=4.8,car_width_m=2.,swept=swept))
 for lane in ramp_lanes:
  cx=lane['lower_port'][0];low=lane['lower_port'][1];high=lane['upper_port'][1];allowed=vehicle.union(shaftunion).buffer(.001)
  for name,poses in[('LOW',[rect((cx-6+6*math.sin(t),low+6-6*math.cos(t)),(math.cos(t),math.sin(t)),4.8,2.)for t in np.linspace(0,math.pi/2,33)]),('HIGH',[rect((cx-6+6*math.cos(t),high-6+6*math.sin(t)),(-math.sin(t),math.cos(t)),4.8,2.)for t in np.linspace(0,math.pi/2,33)])]:
   swept=unary_union(poses);outside=swept.difference(allowed).area;ck('ramp_landing_car_envelope_R6',fid+'/'+lane['direction']+'/'+name,outside<EPS,outside);turns.append(dict(type='ramp-'+name,direction=lane['direction'],radius_m=6.,car_length_m=4.8,car_width_m=2.,swept=swept))
 for r in ramps:
  ck('ramp_design_grade_under_12_percent',r['id'],r['max_grade_percent']<=12.,r['max_grade_percent']);ck('ramp_connects_real_adjacent_decks',r['id'],0<=r['from_level']<=6 and 0<=r['to_level']<=6 and abs(r['from_level']-r['to_level'])==1)
 if garage:
  for lo in range(6):ck('planned_clearance_2_2m',fid+str(lo),H[lo+1]-H[lo]-.30-.15>=2.2,H[lo+1]-H[lo]-.30-.15)
 ports=[dict(id=fid+'-VEH-G',type='vehicle',level=0,height=0.,point=list(s['vehicle']),width_m=6.,normal=list(s['vehicle_normal'])),dict(id=fid+'-PED-G',type='pedestrian',level=0,height=0.,point=list(s['ped']),width_m=3.,normal=list(s['ped_normal']))]
 if garage:
  for l in[2,4,6]:ports.append(dict(id=fid+f'-PED-L{l}',type='pedestrian_bridge_receiver',level=l,height=H[l],point=list(s['ped']),width_m=3.,normal=list(s['ped_normal']),status='受け口のみ。モールへの橋線形はroot統合設計'))
 if garage and s['bridge']:
  ports.append(dict(id=fid+'-VEH-B1-G0',type='vehicle_basement_ramp_receiver',level=0,height=0.,point=list(s['bridge']),width_m=7.,normal=[0,-1],status='B館新地下への外部車両スロープ受け口。斜路本体はroot設計'))
  ports.append(dict(id=fid+'-PED-RF-NEAR-B',type='pedestrian_bridge_receiver',level=6,height=16.4,point=[-548,170],width_m=4.,normal=[0,-1],status='B館RF歩行橋受口、車口と分離'));ports.append(dict(id=fid+'-VEH-RF',type='vehicle_bridge_receiver',level=6,height=16.4,point=list(s['bridge']),width_m=7.,normal=[0,-1],status='B館RF車両橋の受け口'))
 FAC.append(dict(id=fid,name=s['name'],kind=s['kind'],block=box(*s['block']),shell=shell,coordinate_system='World XZ metres',floors=floors,ramps=ramps,ramp_lanes=ramp_lanes,portals=ports,turn_templates=turns,design_car=dict(length_m=4.8,width_m=2.,height_limit_m=2.0),module=dict(standard=[2.5,5.],comfort=[2.7,5.2],accessible=[3.5,5.],accessible_side_aisle_m=1.2,vehicle_aisle_m=6.,protected_pedestrian_m=2.,module_pitch_m=19.6,pedestrian_level='床と同じフラット。緑塗装/防護ポール・柱の保護帯で分離し、指定横断部だけ車路を横断。'),notes=['標準車路は双方向6m。上下斜路は各4m一方向、専用の平場で接続。','大型配送トラック・バス待機は含めずrootの別系統へ。','列末端の余白は転回視認/構造柱/歩道の緩衝帯。敷地ブロック全体を架空の占有義務として舗装しない。']))
D=dict(version='Parking blocks v2',coordinate_system='World XZ metres',design_only=True,game_implemented=False,facilities=FAC,existing_A_22_stalls_unchanged_excluded_from_count=True,heavy_loading_excluded=True,structural_and_actual_vehicle_tests=False)
(O/'geometry.json').write_text(json.dumps(D,default=enc,ensure_ascii=False,indent=2));(O/'checks.json').write_text(json.dumps(CHECKS,default=enc,ensure_ascii=False,indent=2))
from shapely.strtree import STRtree
for fac in FAC:
 for floor in fac['floors']:
  ss=floor['stalls'];tree=STRtree([st['polygon']for st in ss]);ids=[st['id']for st in ss];ck('stall_ids_unique',fac['id']+'/'+str(floor['level']),len(ids)==len(set(ids)))
  for i,st in enumerate(ss):
   for j in tree.query(st['polygon'],predicate='intersects'):
    if int(j)<=i:continue
    area=st['polygon'].intersection(ss[int(j)]['polygon']).area;ck('stall_pair_overlap_zero',st['id']+'/'+ss[int(j)]['id'],area<EPS,area)
(O/'checks.json').write_text(json.dumps(CHECKS,default=enc,ensure_ascii=False,indent=2))
SUMMARY=[]
with(O/'stall-ledger.csv').open('w',encoding='utf-8-sig',newline='')as fp:
 out=csv.writer(fp);out.writerow(['facility','level','id','category','height_m','width_m','length_m','vehicle_entry_X','vehicle_entry_Z','ped_entry_X','ped_entry_Z','side_access_width_m','polygon_GeoJSON'])
 for fac in FAC:
  for f in fac['floors']:
   count=collections.Counter(st['category']for st in f['stalls']);SUMMARY.append(dict(facility=fac['id'],level=f['level'],height=f['height'],count=len(f['stalls']),categories=dict(count)))
   for st in f['stalls']:out.writerow([st['facility'],st['level'],st['id'],st['category'],st['height'],st['width_m'],st['length_m'],*st['vehicle_entry'],*st['pedestrian_entry'],st['side_access_width_m'],json.dumps(mapping(st['polygon']))])
(O/'capacity.json').write_text(json.dumps(SUMMARY,ensure_ascii=False,indent=2));(O/'ports.json').write_text(json.dumps([dict(facility=f['id'],**p)for f in FAC for p in f['portals']],ensure_ascii=False,indent=2))
fail=[c for c in CHECKS if not c['pass_']];print('CAPACITY',[(f['id'],sum(len(l['stalls'])for l in f['floors']))for f in FAC]);print('TOTAL',sum(q['count']for q in SUMMARY),'CHECKS',len(CHECKS),'FAILED',len(fail))
for q in fail[:25]:print(q)
