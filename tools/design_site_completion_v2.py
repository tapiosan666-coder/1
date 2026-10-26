"""Whole-site v2 geometry and honest design-stage integration checks. Never writes game files."""
from site_v2_common import *
from collections import Counter
O=R/'docs/site-completion-v2';O.mkdir(exist_ok=True)
A=read(R/'docs/a-detailed-design-v1/geometry.json');B=read(R/'docs/b-v4-overlap-correction/geometry.json');C=read(R/'docs/c-detailed-design-v1/geometry.json');BN=read(R/'docs/b-completion-v2/geometry.json');P=read(R/'docs/parking-blocks-v2/geometry.json');CORES=[core_world(c)for c in B['cores']]
F={w:{f['level']:f for f in d['floors']}for w,d in [('A',A),('C',C),('B',BN)]}
for f in B['floors']:
 q=floor_B_world(f,CORES if 'CORES'in globals()else[core_world(c)for c in B['cores']]);q['escalators']=[translate_geoms(e,-714,-30)for e in B['escalators']if f['floor']in e['levels']];F['B'][q['level']]=q
CHECK=[]
def ck(kind,id,ok,val=None,status='design_check'):
 CHECK.append(dict(kind=kind,id=id,pass_=bool(ok),value=val,status=status))
ROAD=[];WALK=[];BRIDGE=[];TOWER=[];GATES=[];YARDS=[];PROP=[]
def road(id,name,points,width,role='customer'):
 l=LineString(points);g=l.buffer(width/2,cap_style=2,join_style=1);q=dict(id=id,name=name,line=l,polygon=g,width_m=width,role=role,points=points,design_speed_kmh=15 if role=='customer'else 10);ROAD.append(q);return q
# Several direct arterial access points are intentional; there is no huge unused perimeter loop.
road('V-NORTH','北西来客入口→C北駐車場', [(-1120,-625),(-583,-625),(-583,-600)],6)
road('V-WEST','西側来客幹線→南来客幹線',[(-1120,-625),(-1120,220),(-740,220),(-740,500),(-130,500),(-130,530)],8)
road('V-PBW','西平面入口分岐',[(-1120,-25),(-1063,-25),(-1063,0)],6)
road('V-PBS','B南立体来客入口分岐',[(-740,220),(-740,150),(-677,150),(-677,170)],6)
road('V-PAS','A南平面入口分岐',[(-130,500),(-130,330),(-63,330)],6)
road('V-PAE','A東立体来客入口分岐',[(500,100),(500,31),(465,31)],6)
road('V-A22','A西22台小駐車場入口',[(-180,-105),(-180,-65),(-180,-39),(-171,-39)],6)
road('D-SPINE','搬入専用：東ゲート→A南・B東',[(450,245),(260,245),(-160,245),(-160,45)],8,'delivery')
road('D-NORTH','搬入専用：C東・B西分岐',[(260,245),(260,-420),(-785,-420),(-785,47.5)],8,'delivery')
road('D-C','C既存搬入ヤード接続',[(-190,-420),(-190,-250),(-205,-250)],8,'delivery')
road('D-BE','B東荷捌き車止め',[(-160,45),(-161,35.5),(-170,35.5)],8,'delivery')
road('D-BW','B西荷捌き車止め',[(-785,47.5),(-775,47.5),(-761,47.5)],8,'delivery')
road('D-A','A新荷捌き車止め',[(260,10),(237,10)],8,'delivery')
for id,p,role in [('G-NW',(-1120,-625),'customer'),('G-S',(-130,530),'customer'),('G-E',(500,100),'customer'),('G-A22',(-180,-105),'customer'),('G-D',(450,245),'delivery')]:GATES.append(dict(id=id,point=p,role=role,external_road='接続先公道はゲーム用仮定。敷地外車線計画・信号容量は未検証。'))
for id,name,g,truckstop,dock in [('Y-BE','B東既存搬入口前',box(-181,12,-142,72),(-170,35.5),(-184,35.5)),('Y-BW','B西既存搬入口前',box(-798,22,-752,75),(-761,47.5),(-749,47.5)),('Y-C','C既存荷捌き',C['loading']['polygon']if'polygon'in C['loading']else box(-235,-273,-205,-224),(-220,-248),(-235,-248)),('Y-A','A東新荷捌き（外壁扉別案）',box(218,-18,256,37),(237,10),(212,0))]:
 YARDS.append(dict(id=id,name=name,polygon=g,truck_stop=truckstop,cart_dock=dock,truck_design='12m級単車トラック、車高4.2m想定。動的軌跡・運行容量は未検証。',cart_line=LineString([truckstop,dock]),turning_reservation_m=12))
def walk(id,name,pts,width=4.,height=0.,role='customer',kind='grade',target=None):
 l=LineString(pts);q=dict(id=id,name=name,line=l,polygon=l.buffer(width/2,cap_style=2,join_style=1),width_m=width,height=height,role=role,kind=kind,target=target);(BRIDGE if kind=='bridge'else WALK).append(q);return q
# Local facade additions leave source floor files untouched. Their prerequisites remain explicit.
def arrival(id,w,level,ep,n,width=4):
 q=(ep[0]-n[0]*1.5,ep[1]-n[1]*1.5);out=(ep[0]+n[0]*4,ep[1]+n[1]*4);l=LineString([q,out]);g=l.buffer(width/2,cap_style=2);f=F[w][level];private=unary_union([s['polygon']for s in f['stores']]+[c['outline']for c in f['cores']]);
 PROP.append(dict(id=id,wing=w,level=level,height=HEIGHT[level],entry=ep,normal=n,width_m=width,polygon=g,wall_cut=g.intersection(f['shell'].difference(f['public'])),new_floor=g.difference(f['floor_plate']),existing_store_overlap_m2=g.intersection(private).area,old_geometry_modified=False,applied=False,status='要承認：外壁・閉鎖境界の局所開口と玄関床。店舗/広場/通路網を維持。'))
 ck('arrival_no_private_overlap',id,g.intersection(private).area<EPS,g.intersection(private).area,'conditional_proposal')
 ck('arrival_reaches_original_public',id,g.intersection(f['public']).area>1,g.intersection(f['public']).area,'conditional_proposal')
 return q,out
b_in,b_out=arrival('B-NEW-SW-CUSTOMER-1F','B',0,[-669.01233249,55.20613054],[.2108378723,.9775210441],6)
ae_in,ae_out=arrival('A-NEW-EAST-2F','A',1,[178.26824881,46.24391706],[.316227766,.948683298],4)
as_in,as_out=arrival('A-NEW-SOUTH-2F','A',1,[85.60340380,193.01279775],[.5098023903,.8602915336],4)
walk('W-PBS','B南立体地上→翼広場南新玄関',[(-630,170),(-630,150),(-663,85),b_out,b_in],4,target='B-NEW-SW-CUSTOMER-1F')
walk('W-PBW-1','B西平面→西歩道橋塔',[(-872,60),(-845,60),(-820,100)],4)
walk('W-PBW-2','B西歩道橋→翼広場南新玄関',[(-755,100),(-725,100),(-663,85),b_out,b_in],4,target='B-NEW-SW-CUSTOMER-1F')
walk('W-PCN-1','C北平面→北歩道橋塔',[(-468,-498),(-468,-448)],4)
walk('W-PCN-2','C北歩道橋→北側棟間通路',[(-468,-392),(-445,-392),(-445,-325)],4,target='C北棟間公開通路')
walk('W-PAS','A南平面→南歩道橋塔',[(38,330),(38,315),(120,315)],4)
walk('W-OFFSITE-A','駅/周辺街区からの歩行者正面到着',[(190,315),(120,315)],5,target='TW-PAS→A2F南玄関')
GATES.append(dict(id='G-P-A',point=[190,315],role='pedestrian',external_road='駅/周辺街区側の接続端。敷地外歩道/駅は未設計。'))
walk('W-A22','A西小駐車場→既存歩行到着',[(-153,-20),(-153,-16)],3,target='A既存西到着')
walk('BR-PAE','A東立体P3→A2F東玄関',[(315,100),(280,100),(230,54),ae_out,ae_in],4,5.525,kind='bridge',target='A-NEW-EAST-2F')
walk('BR-PAS','A南歩道橋塔→A2F南玄関',[(120,315),(120,215),(90,200),as_out,as_in],4,5.525,kind='bridge',target='A-NEW-SOUTH-2F')
walk('BR-PCN','C北歩道橋：搬入幹線横断',[(-468,-448),(-468,-392)],4,5.525,kind='bridge',target='C地上公開通路')
walk('BR-PBW','B西歩道橋：搬入幹線横断',[(-820,100),(-755,100)],4,5.525,kind='bridge',target='B-NEW-SW-CUSTOMER-1F')
walk('BR-PBS-RF-PED','B南立体RF→B屋上歩行橋',[(-548,170),(-548,110)],4,16.4,kind='bridge',target='B RF新公開通路')
CARBRIDGE=dict(id='BR-PBS-RF-CAR',name='B南立体RF→B屋上双方向車路橋',line=LineString([(-540,170),(-540,110)]),polygon=LineString([(-540,170),(-540,110)]).buffer(3.5,cap_style=2),height=16.4,width_m=7.,lanes=2,role='customer_vehicle',status='新規設計。既存B1〜3F床を変更しない。')
# Standalone overpass towers, with two-flight stairs, landing and lift shaft/door shown.
for id,pt in [('TW-PAS',(120,315)),('TW-PCN-N',(-468,-448)),('TW-PCN-S',(-468,-392)),('TW-PBW-W',(-820,100)),('TW-PBW-E',(-755,100))]:
 x,z=pt;shell=box(x-6,z-10,x+6,z+3);stair=box(x-5.3,z-7.8,x+.2,z-1);lift=box(x+1,z-5,x+4,z-2);landing=box(x-5.3,z-1,x+4,z+2);shaft=box(x+1.15,z-4.85,x+3.85,z-2.15)
 TOWER.append(dict(id=id,point=pt,outline=shell,stair=stair,stair_flights=[box(x-5,z-5.8,x-3,z-1),box(x-2.7,z-5.8,x-.7,z-1)],stair_opening=box(x-5,z-5.8,x-.7,z-1),return_landing=box(x-5,z-7.8,x-.7,z-5.8),lift=lift,lift_opening=shaft,lift_door=LineString([(x+1.5,z-2),(x+2.5,z-2)]),landing=landing,levels=[0,5.525],landing_clear_width_m=2,stair_clear_width_m=2.,riser_count=34,riser_m=5.525/34,tread_m=.3,headroom_design_m=2.4,door_m=1.,status='新規の敷地付属設備。構造/実歩行/機器は未検証。'))
# Match actual 3m pedestrian ports; widen over the first 8m without opening the garage edge further.
for q in WALK+BRIDGE:
 if q['id']in['W-PBS','W-PBW-1','W-PCN-1','W-PAS','BR-PAE']:
  l=q['line'];p0=l.coords[0];p8=l.interpolate(8).coords[0];u=((p8[0]-p0[0])/8,(p8[1]-p0[1])/8);n=(-u[1],u[0]);w=q['width_m'];taper=Polygon([(p0[0]-n[0]*1.5,p0[1]-n[1]*1.5),(p0[0]+n[0]*1.5,p0[1]+n[1]*1.5),(p8[0]+n[0]*w/2,p8[1]+n[1]*w/2),(p8[0]-n[0]*w/2,p8[1]-n[1]*w/2)]);q['polygon']=taper.union(substring(l,8,l.length).buffer(w/2,cap_style=2,join_style=1));q['terminal_port_width_m']=3.;q['taper_run_m']=8.
# The existing C loading yard is B1, not ground. Its new open-air truck ramp reaches that exact datum.
cr=next(r for r in ROAD if r['id']=='D-C');cr.update(kind='open_air_delivery_ramp',start_height=0.,end_height=-5.35,straight_ramp_length_m=150.,flat_bottom_length_m=20.,max_gradient=5.35/140.,transition_m=10.,profile=[dict(station_m=t,world_y=y)for t,y in[(0,0),(10,-5.35/140*5),(140,-5.35+5.35/140*5),(150,-5.35),(170,-5.35),(185,-5.35)]],retaining_walls=unary_union([cr['line'].offset_curve(4.2),cr['line'].offset_curve(-4.2)]).buffer(.2),vehicle_height_design_m=4.2,open_to_sky=True)
for yard in YARDS:yard.update(level=-1 if yard['id']=='Y-C'else 0,height=-5.35 if yard['id']=='Y-C'else 0.)
# Preserve all old 22 stalls; supplement only exterior pedestrian strips and crossings.
old=A['outdoor_site'][0];oldped=unary_union([old['protected_pedestrian'],box(-173,-55,-171.5,-20),box(-173,-55,-140,-52),box(-173,-26,-140,-23)]);oldvehicle=old['vehicle_aisle'].union(box(-171,-47,-143.5,-45)).union(box(-171,-33,-143.5,-31)).union(box(-174,-42,-171,-36))
OLD=dict(id='P-A-OLD22',shell=old['polygon'],vehicle_aisles=oldvehicle,protected_pedestrian=oldped,crossings=oldped.intersection(oldvehicle),stalls=[dict(id=s['id'],facility='P-A-OLD22',level=0,height=0,category='general',polygon=s['geom'],width_m=s['width_m'],length_m=s['depth_m'],vehicle_entry=[s['geom'].centroid.x,-47 if s['geom'].centroid.y<-39 else-31],pedestrian_entry=[s['geom'].centroid.x,-52 if s['geom'].centroid.y<-39 else-26])for s in old['parking_stalls']],original_stall_geometry_unchanged=True,exterior_pedestrian_strip_proposal=True)
# Explicitly register all road bends as compact junction/turning reservations, not unexplained empty plazas.
TURNS=[]
for r in ROAD:
 for i,pt in enumerate(r['points'][1:-1],1):
  rad=9 if r['role']=='customer'else 15;g=Point(pt).buffer(rad);TURNS.append(dict(id=r['id']+f'-TURN-{i}',role=r['role'],polygon=g,centre=pt,reservation_radius_m=rad,not_a_dynamic_swept_path=True))
for r in ROAD:
 pt=r['points'][0]
 if any(q['id']!=r['id']and q['role']==r['role']and q['line'].distance(Point(pt))<1e-8 for q in ROAD)and not any(math.dist(pt,t['centre'])<1 for t in TURNS):
  rad=9 if r['role']=='customer'else 15;TURNS.append(dict(id=r['id']+'-JUNCTION',role=r['role'],polygon=Point(pt).buffer(rad),centre=pt,reservation_radius_m=rad,not_a_dynamic_swept_path=True))
CUSTOM=unary_union([r['polygon']for r in ROAD if r['role']=='customer']+[t['polygon']for t in TURNS if t['role']=='customer']);DEL=unary_union([r['polygon']for r in ROAD if r['role']=='delivery']+[t['polygon']for t in TURNS if t['role']=='delivery']+[q['polygon']for q in YARDS]);BODY0=unary_union([F[w][0]['shell']for w in F]);PSHELL=unary_union([q['shell']for q in P['facilities']]+[old['polygon']]);private=unary_union([s['polygon']for w in F for s in F[w][0]['stores']]+[c['outline']for w in F for c in F[w][0]['cores']])
# New A service door connects directly into an existing east anchor backroom; it is a separate unapplied proposal.
astore=next(q for q in F['A'][0]['stores']if q['id']=='A1F-052');cart=LineString([(237,10),(218,10),(218,0),(211,0)]).buffer(1,cap_style=2);others=unary_union([q['polygon']for q in F['A'][0]['stores']if q['id']!=astore['id']]+[q['outline']for q in F['A'][0]['cores']]);next(y for y in YARDS if y['id']=='Y-A')['cart_line']=LineString([(237,10),(218,10),(218,0),(211,0)]);LOADING_DOORS=[dict(id='A-NEW-DELIVERY-1F',wing='A',level=0,entry=[212,0],width_m=2,polygon=cart,wall_cut=cart.intersection(F['A'][0]['shell'].difference(F['A'][0]['public'])),receiver_store=astore['id'],receiver_backroom=astore['backroom'],applied=False,status='未適用：東核店バックルーム外壁の局所搬入扉。基準区画不変更。')];ck('A_loading_route_no_other_private',LOADING_DOORS[0]['id'],cart.intersection(others).area<EPS,cart.intersection(others).area,'conditional_proposal');ck('A_loading_route_enters_backroom',LOADING_DOORS[0]['id'],cart.intersection(astore['backroom']).area>.5,cart.intersection(astore['backroom']).area,'conditional_proposal')
for yard in YARDS:
 ck('yard_to_service_external_gate',yard['id'],any(p.distance(Point((450,245)))<EPS and p.intersection(yard['polygon']).area>1 for p in polys(DEL)))
ck('customer_delivery_roads_separate','all',CUSTOM.intersection(DEL).area<EPS,CUSTOM.intersection(DEL).area)
ck('customer_roads_outside_mall','all',CUSTOM.intersection(BODY0).area<EPS,CUSTOM.intersection(BODY0).area)
ck('delivery_roads_outside_mall','all',DEL.intersection(BODY0).area<EPS,DEL.intersection(BODY0).area)
# All grade pedestrian crossings with delivery roads must be zero; bridge projection overlap is intentional.
for w in WALK:ck('grade_walk_delivery_separation',w['id'],w['polygon'].intersection(DEL).area<EPS,w['polygon'].intersection(DEL).area)
for b in BRIDGE:
 x=b['polygon'].intersection(DEL);clear=b['height']-.32
 ck('overpass_truck_clearance',b['id'],x.is_empty or clear>=4.7,dict(road_projection_overlap_m2=x.area,clear_height_m=clear,minimum_m=4.7))
 if b['id']in['BR-PAE','BR-PAS']:
  f=F['A'][1];pr=unary_union([s['polygon']for s in f['stores']]+[c['outline']for c in f['cores']]);ck('upper_bridge_no_store_overlap',b['id'],b['polygon'].intersection(pr).area<EPS,b['polygon'].intersection(pr).area,'conditional_proposal')
for w in WALK:
 ck('walk_does_not_enter_private','all-'+w['id'],w['polygon'].intersection(private).area<EPS,w['polygon'].intersection(private).area,'conditional_proposal'if w['target']and'NEW'in w['target']else'design_check')
# Real grade car ports: each has a continuous road to an explicitly external gate.
components=polys(CUSTOM)
for fac in P['facilities']:
 port=next(q for q in fac['portals']if q['level']==0 and q['type']=='vehicle')
 point=Point(port['point']);parts=[q for q in components if q.distance(point)<1e-6];ok=bool(parts)and any(any(q.distance(Point(g['point']))<1e-6 for g in GATES if g['role']=='customer')for q in parts);ck('parking_port_to_external_gate',fac['id'],ok,port['point'])
for facid,pathid,lev in[('P-A-E','BR-PAE',2),('P-B-S','W-PBS',0),('P-B-W','W-PBW-1',0),('P-C-N','W-PCN-1',0),('P-A-S','W-PAS',0)]:
 fac=next(q for q in P['facilities']if q['id']==facid);port=next(q for q in fac['portals']if q['level']==lev and q['type'].startswith('pedestrian'));q=next(q for q in WALK+BRIDGE if q['id']==pathid);pt=port['point'];n=port['normal'];u=(-n[1],n[0]);probe=rect((pt[0]-.2*n[0],pt[1]-.2*n[1]),u,port['width_m'],.2);pf=next(q for q in fac['floors']if q['level']==lev);ck('actual_walk_port_width_matched',pathid,q['terminal_port_width_m']<=port['width_m'],[q['terminal_port_width_m'],port['width_m']]);ck('actual_walk_port_receiver_supported',pathid,pf['floor_plate'].buffer(1e-6).covers(probe),probe.difference(pf['floor_plate']).area)
ck('C_truck_ramp_matches_B1_yard','D-C',cr['end_height']==F['C'][-1]['height']and next(q for q in YARDS if q['id']=='Y-C')['height']==F['C'][-1]['height'])
# Roof and basement connection surfaces are required across the full port width, not just touching at one point.
pb=next(q for q in P['facilities']if q['id']=='P-B-S')
for id,geom,level,end in [('B1-car-ramp-PB',BN['car_ramps'][0]['polygon'],0,[-540,170]),('RF-car-PB',CARBRIDGE['polygon'],6,[-540,170]),('RF-ped-PB',next(q['polygon']for q in BRIDGE if q['id']=='BR-PBS-RF-PED'),6,[-548,170])]:
 pf=next(q for q in pb['floors']if q['level']==level);probe=box(end[0]-(3.5 if'car'in id else 2),170,end[0]+(3.5 if'car'in id else 2),170.5);ck('PB_full_width_bridge_apron',id,pf['floor_plate'].buffer(1e-7).covers(probe),probe.difference(pf['floor_plate']).area);kind='vehicle_aisles'if'car'in id else'protected_pedestrian';ck('PB_bridge_matches_correct_surface',id,pf[kind].buffer(1e-7).covers(probe),probe.difference(pf[kind]).area)
ck('RF_car_ped_bridges_separate','B-S',CARBRIDGE['polygon'].intersection(next(q['polygon']for q in BRIDGE if q['id']=='BR-PBS-RF-PED')).area<EPS)
# All new floors and existing floors share the exact declared level datum.
for w,ff in F.items():
 for lev,f in ff.items():ck('mall_level_datum',w+'-'+LABEL[lev],abs(f['height']-HEIGHT[lev])<1e-9,[f['height'],HEIGHT[lev]])
# Freeze all source data. Each old design remains read-only, including B v4.1.
baseline=read(O/'protected-baseline-hashes.json');changed=[p for p,h in baseline.items()if not(R/p).exists()or sha(R/p)!=h];ck('protected_files_unchanged','all',not changed,dict(checked=len(baseline),changed=changed))
# Plot honest managed parcels: facilities + rights-of-way + named buffers, not the rectangular bounding box as land area.
managed=unary_union([BODY0,PSHELL,CUSTOM,DEL]+[q['polygon']for q in WALK+BRIDGE]+[q['outline']for q in TOWER]+[CARBRIDGE['polygon'],BN['car_ramps'][0]['polygon']]);LAND=managed.buffer(12).difference(managed);site=managed.union(LAND)
# Complete deduplicated capacity ledger; garage roof stalls count once in garage totals.
STALLS=[dict(s,facility=fac['id'])for fac in P['facilities']for f in fac['floors']for s in f['stalls']]+OLD['stalls']+[s for f in BN['floors']for s in f['parking']['stalls']]
ids=[s['id']for s in STALLS];ck('stall_id_unique','all',len(ids)==len(set(ids)),len(ids))
SUM=[]
for fac in sorted(set(s['facility']for s in STALLS)):
 ss=[s for s in STALLS if s['facility']==fac];SUM.append(dict(facility=fac,count=len(ss),categories=dict(Counter(s['category']for s in ss)),levels=sorted(set(s['level']for s in ss))))
write(O/'geometry.json',dict(version='Whole site completion v2 review',design_only=True,game_modified=False,level_heights=HEIGHT,fixed_source_files={'A':str(R/'docs/a-detailed-design-v1/geometry.json'),'B':str(R/'docs/b-v4-overlap-correction/geometry.json'),'C':str(R/'docs/c-detailed-design-v1/geometry.json')},roads=ROAD,turn_reservations=TURNS,walks=WALK,bridges=BRIDGE,roof_car_bridge=CARBRIDGE,pedestrian_towers=TOWER,gates=GATES,loading_yards=YARDS,loading_door_proposals=LOADING_DOORS,arrival_proposals=PROP,old_A22=OLD,managed_parcels=managed,landscape_buffer=LAND,site_boundary=site,site_boundary_definition='建物/駐車場/道路/歩道/付属設備の実計画投影＋12m排水植栽管理帯の和集合。外接矩形は敷地面積ではない。',approval_conditions=['新来客扉3か所は局所変更提案。基準階図面に未適用。','A/B既存EV・階段床開口は別提案。承認まで従来図面を維持。','構造設計・法規・交通容量・実歩行/実車・ゲーム実装は未検証。'],parking_capacity=SUM,total_stalls=len(STALLS)))
write(O/'checks.json',CHECK);write(O/'capacity.json',SUM)
csvwrite(O/'parking-ledger.csv',['ID','facility','level','category','width_m','length_m','X','Z','polygon_geojson'],[[s['id'],s['facility'],s['level'],s['category'],s['width_m'],s['length_m'],s['polygon'].centroid.x,s['polygon'].centroid.y,json.dumps(mapping(s['polygon']))]for s in STALLS])
csvwrite(O/'road-path-register.csv',['ID','名称','用途','最大幅m','端部幅m','高さm','接続先/目的','座標列'],[[q['id'],q['name'],q['role'],q['width_m'],q.get('terminal_port_width_m',q['width_m']),('0→-5.35'if q.get('kind')=='open_air_delivery_ramp'else q.get('height',0)),q.get('target')or q['name'],json.dumps(list(q['line'].coords))]for q in ROAD+WALK+BRIDGE])
write(O/'summary.json',dict(total_stalls=len(STALLS),capacity=SUM,checks=len(CHECK),failed=[q for q in CHECK if not q['pass_']],source_files_immutable=len(baseline),site_managed_projection_m2=managed.area,drainage_green_buffer_m2=LAND.area,site_boundary_area_m2=site.area,requires_approval=[q['id']for q in PROP],game_implemented=False,physical_walk_test=False))
print(json.dumps(read(O/'summary.json'),ensure_ascii=False,indent=2))
