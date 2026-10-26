"""C wing five-level design data. Does not import or write Godot files."""
from pathlib import Path
import sys,json,math,csv,collections,hashlib,heapq
sys.path.append('/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
import shapely
from shapely.geometry import Polygon,LineString,Point,box,mapping
from shapely.ops import unary_union,nearest_points,substring
R=Path(__file__).resolve().parents[1];O=R/'docs/c-detailed-design-v1';O.mkdir(exist_ok=True)
HEIGHT={-1:-5.35,0:0.,1:5.525,2:10.875,3:16.4};LABEL={-1:'B1',0:'1F',1:'2F',2:'3F',3:'RF'};EPS=1e-8
CHECKS=[]
def ck(kind,id,ok,value=None,level=None):CHECKS.append(dict(kind=kind,id=id,pass_=bool(ok),value=value,level=level))
def enc(v):
 if hasattr(v,'geom_type'):return mapping(v)
 if hasattr(v,'item'):return v.item()
 raise TypeError(type(v))
def ps(g):return[]if g.is_empty else[g]if g.geom_type=='Polygon'else[p for p in getattr(g,'geoms',[])if p.geom_type=='Polygon']
CENTER=(-450,-245)
PAV=[]
# The changing facade directions create six independent buildings and three commercial streets.
for id,name,a,b in[
 ('CW','西のファッション棟',(-590,-290),(-570,-200)),
 ('CNW','北西の生活棟',(-565,-320),(-470,-350)),
 ('CNE','北東のスポーツ棟',(-425,-350),(-315,-300)),
 ('CE','東のアクティブ棟',(-280,-275),(-300,-180)),
 ('CSE','南東ダイニング棟',(-330,-150),(-430,-150)),
 ('CSW','南西ライフスタイル棟',(-465,-155),(-555,-175))]:
 length=math.dist(a,b);u=((b[0]-a[0])/length,(b[1]-a[1])/length);n=(-u[1],u[0]);mid=((a[0]+b[0])/2,(a[1]+b[1])/2)
 if (mid[0]-CENTER[0])*n[0]+(mid[1]-CENTER[1])*n[1]<0:n=(-n[0],-n[1])
 def tp(x,z,a=a,u=u,n=n):return(a[0]+u[0]*x+n[0]*z,a[1]+u[1]*x+n[1]*z)
 def tr(x0,z0,x1,z1):return Polygon([tp(x,z)for x,z in[(x0,z0),(x1,z0),(x1,z1),(x0,z1)]])
 PAV.append(dict(id=id,name=name,a=a,b=b,u=u,n=n,length=length,footprint=tr(-.3,-6.3,length+.3,25),front_corridor=tr(-.1,-6.6,length+.1,.15),core_origin=tp(length-24,0),front_mid=tp(length/2,-3),core_entry=tp(length-12,0),store_length=length-24,loading=tp(length-12,25)))
# Each pavilion has a specifically planned stair / EV / WC core. No anonymous service boxes.
CORES=[]
for v in PAV:
 a=v['core_origin'];u=v['u'];n=v['n']
 def tp(x,z):return[a[0]+u[0]*x+n[0]*z,a[1]+u[1]*x+n[1]*z]
 def tr(x0,z0,x1,z1):return Polygon([tp(x,z)for x,z in[(x0,z0),(x1,z0),(x1,z1),(x0,z1)]])
 rooms={'front_lobby':tr(.25,.25,23.75,4),'stair':tr(.25,4,8,23.75),'lift':tr(8,4,12,8),'accessible_wc':tr(8,11,12,15),'lift_access':tr(12,4,14,16),'accessible_access':tr(8,8,14,11),'women':tr(14,4,19,23.75),'men':tr(19,4,23.75,23.75)}
 door_specs=[('CORE',(12,0),4,(1,0)),('ST',(4,4),1.8,(1,0)),('EV',(10,4),1.6,(1,0)),('AWC',(12,13),1.2,(0,1)),('W',(16.5,4),1.6,(1,0)),('M',(21.5,4),1.6,(1,0))]
 doors=[]
 for id,p,w,axis in door_specs:doors.append(dict(id=id,p=tp(*p),w=w,axis=[u[0]*axis[0]+n[0]*axis[1],u[1]*axis[0]+n[1]*axis[1]]))
 wall=unary_union([rooms[k].boundary.buffer(.1,join_style=2)for k in['stair','lift','accessible_wc','women','men']])
 for d in doors:
  x,z=d['p'];du=d['axis'];wall=wall.difference(LineString([(x-du[0]*d['w']/2,z-du[1]*d['w']/2),(x+du[0]*d['w']/2,z+du[1]*d['w']/2)]).buffer(.4,cap_style=2))
 fixtures=[];cubicles=[]
 for sex,x0,x1 in[('W',14,19),('M',19,23.75)]:
  for k in range(2):
   q=tr(x0+.25+k*2.2,20.5,x0+2.2+k*2.2,23.5);fixtures.append(dict(kind='WC-'+sex,geom=tr(x0+.85+k*2.2,21.1,x0+1.55+k*2.2,22.4)));cubicles.append(dict(room=sex,polygon=q,door=tp(x0+1+k*2.2,20.5),door_width_m=.9))
  fixtures.append(dict(kind='SINK',geom=tr(x0+.15,6,x0+.75,10)))
 fixtures.append(dict(kind='AWC',geom=tr(8.5,13.6,9.2,14.6)))
 fixtures.append(dict(kind='URINAL',geom=tr(23,12,23.5,13)))
 fixtures.append(dict(kind='URINAL',geom=tr(23,14,23.5,15)))
 shafts=tr(8.1,4.1,11.9,7.9).union(tr(.5,7,7.5,22.8))
 stair_landings=[tr(.5,4.2,7.5,7),tr(.5,20,7.5,22.8)]
 outline=tr(0,0,24,24)
 # Public core area includes WC rooms; fixture and wall footprints are excluded from walkable.
 core_floor=outline.difference(shafts)
 free=core_floor.difference(wall.union(unary_union([f['geom']for f in fixtures])))
 CORES.append(dict(id='K-'+v['id'],pavilion=v['id'],outline=outline,rooms=rooms,doors=doors,entry=tp(12,0),room_wall_solids=wall,fixtures=fixtures,cubicles=cubicles,shafts=shafts,public=core_floor,walkable=free,stair_landings=stair_landings,stair_width_m=2.,stair_tread_m=.30,stair_risers_per_storey=32,stair_run_m=4.5,landing_m=2.8,lift_shaft_m=[4,4],lift_door_m=1.6,accessible_wc_m=[4,4],u=u,n=n))
# Footpaths connect real facade streets and facilities; their names describe the destinations.
ROUTES=[]
def route(id,name,points,width,role,levels=(-1,0,1,2,3)):
 ROUTES.append(dict(id=id,name=name,points=points,width=width,role=role,levels=list(levels),poly=LineString(points).buffer(width/2,cap_style=2,join_style=2)))
front=[v['front_mid']for v in PAV]
for i in range(6):
 a=front[i];b=front[(i+1)%6]
 route('C-LOOP-'+str(i+1),'街路接続 '+PAV[i]['id']+'→'+PAV[(i+1)%6]['id'],[a,b],10 if i in[0,2,4]else 8,'隣接する独立棟の前廊・広場を接続',(-1,0))
route('C-NORTH','北の生活・スポーツ街',[front[1],(-462,-315),front[2]],10,'北西・北東棟の店頭と北庭を接続',(-1,0))
route('C-CENTRE','中央庭園プロムナード',[front[0],(-465,-245),(-400,-220),front[3]],10,'西棟から中央庭園を経て東棟へ',(-1,0))
route('C-SOUTH','南のダイニング街',[front[5],(-435,-170),front[4]],12,'南西棟・南東飲食棟とB館玄関を接続',(-1,0))
route('C-RADIAL-N','北庭への短絡',[(-465,-245),(-462,-315)],8,'中央庭園と北の店頭・昇降設備を接続',(-1,0))
route('C-RADIAL-S','南門への短絡',[(-465,-245),(-435,-170)],8,'中央庭園と南の飲食街・B館接続を接続',(-1,0))
# Upper levels use only pavilion frontage and necessary peripheral bridges; gardens stay open to sky.
for i in range(6):
 points=[front[i],front[(i+1)%6]]
 if i==1:points=[front[1],[-500,-295],[-432,-293],front[2]]
 if i==4:points=[front[4],[-397,-183],[-465,-198],front[5]]
 route('C-DECK-'+str(i+1),'上階デッキ '+PAV[i]['id']+'→'+PAV[(i+1)%6]['id'],points,6,'独立棟の前廊同士を接続。庭の中心を覆わない周縁の歩行橋',(1,2,3))

# Fixed B-wing ends: C-side routes begin with a short overlap, not just point contact.
route('BC-1-C','B館1F受け口',[(-370,-79),(-370,-94),(-312,-107),(-312,-142),(-320,-160),front[4]],8,'B館の固定地上接続→南東飲食棟・南庭',(0,))
route('BC-2-C','B館2F受け口',[(-432,-116),(-432,-123),(-454,-128),(-457,-140),(-457,-165),(-472,-181),front[5]],5,'B館の固定橋→上階デッキ→南西/南東棟',(1,))
# Outdoor escalators sit alongside real shop streets; only 1F-2F and 2F-3F, stairs/EV serve all five levels.
ESC=[];BANK_MEDIANS=[]
for id,center,u,levels in [('CE12',(-324,-235),(0,1),[0,1]),('CN23',(-500,-316),(1,0),[1,2])]:
 n=(-u[1],u[0]);BANK_MEDIANS.append(dict(id=id+'-MEDIAN',levels=levels,geom=Polygon([(center[0]+u[0]*a+n[0]*b,center[1]+u[1]*a+n[1]*b)for a,b in[(-7.4,-.8),(7.4,-.8),(7.4,.8),(-7.4,.8)]])))
 for side,direction in[(-2,'UP'),(2,'DOWN')]:
  c=[center[0]+n[0]*side,center[1]+n[1]*side]
  def rect(c,l,w):return Polygon([(c[0]+u[0]*a+n[0]*b,c[1]+u[1]*a+n[1]*b)for a,b in[(-l/2,-w/2),(l/2,-w/2),(l/2,w/2),(-l/2,w/2)]])
  lands=[rect([c[0]+u[0]*q*8.9,c[1]+u[1]*q*8.9],3,3.6)for q in[-1,1]]
  ESC.append(dict(id=id+'-'+direction,c=c,u=u,direction=direction,levels=levels,shaft=rect(c,14.8,2.4),landings=lands,width_m=2.4,run_m=11.8,comb_m=1.5))
 # Access apron follows existing commercial street, not an arbitrary new branching path.
 target=front[3]if id=='CE12'else front[1]
 for q in[-1,1]:route(id+'-ACCESS-'+str(q),id+'乗降口アクセス',[[center[0]+u[0]*q*10.4,center[1]+u[1]*q*10.4],(-474,-294)if id=='CN23'and q==1 else target],5,'昇降機の乗降口と同じ棟の前廊を接続',levels)
PLAZAS=[dict(id='C-GATE',name='南の迎賓庭',polygon=Polygon([(-458,-177),(-430,-187),(-405,-171),(-399,-147),(-430,-132),(-459,-147)]),role='B館玄関から南の店舗街へ分配する待合・休憩'),dict(id='C-CENTRAL',name='木陰の中庭',polygon=Point(-465,-245).buffer(24,quad_segs=10).union(box(-474,-245,-440,-230)),role='東西プロムナードと北庭・南庭をつなぐ庭園中継'),dict(id='C-NORTH-GARDEN',name='北のテラス庭',polygon=Polygon([(-490,-333),(-462,-342),(-438,-325),(-445,-306),(-475,-303),(-493,-315)]),role='北の2棟の店頭・昇降機・休憩の合流')]
for p in PLAZAS:
 p['court']=p['polygon']
 p['sky_void_reservation']=(p['polygon'].difference(unary_union([v['footprint']for v in PAV]).buffer(.25)).buffer(-7)if p['id']!='C-CENTRAL'else Point(-465,-245).buffer(18))
# Ground planting beds preserve garden space; upper deck does not fill the entire courtyard.
LANDSCAPE=[dict(id='L-1',geom=Polygon([(-545,-250),(-525,-290),(-492,-280),(-493,-253)]),kind='planted_garden'),dict(id='L-2',geom=Polygon([(-422,-290),(-363,-279),(-350,-257),(-405,-260)]),kind='rain_garden'),dict(id='L-3',geom=Polygon([(-500,-215),(-530,-205),(-532,-184),(-475,-190)]),kind='low_planting')]
RETAIL_PROGRAM={
 0:{'CW':['ファッション','ファッション','靴・鞄'],'CNW':['生活雑貨','書籍・文具','生活雑貨'],'CNE':['スポーツ','アウトドア','スポーツ'],'CE':['靴・鞄','スポーツ','キッズ'],'CSE':['カフェ','レストラン','フードショップ'],'CSW':['生活雑貨','家具','ベーカリー・カフェ']},
 1:{'CW':['ファッション','キッズ服飾','靴・鞄'],'CNW':['生活雑貨','書籍・文具','ホビー'],'CNE':['アウトドア','スポーツ','リユース'],'CE':['スポーツ','キッズ体験','玩具'],'CSE':['カフェ','レストラン','ファミリー飲食'],'CSW':['家具','生活雑貨','ギャラリー・カフェ']},
 2:{'CW':['ファッション特集','ファッションリペア','靴・鞄'],'CNW':['書店・学習','ホビー工房','生活雑貨'],'CNE':['屋内スポーツ体験','アウトドア','キッズアクティブ'],'CE':['アミューズ','玩具','スポーツ体験'],'CSE':['レストラン','ビュッフェ','カフェ'],'CSW':['家具','リユース','ギャラリー']}}

FLOORS=[];ledger=[]
CATEGORIES={-1:['サービス・修理','アウトレット生活雑貨','物流受取カウンター'],0:['ファッション','靴・鞄','スポーツ'],1:['生活雑貨','書籍・ホビー','キッズ・カフェ'],2:['レストラン','体験・アミューズ','家具・リユース'],3:['屋上ラウンジ','庭園管理・休憩','展望カフェ']}
for level in[-1,0,1,2,3]:
 stores=[];pavs=[]
 for j,v in enumerate(PAV):
  a=v['a'];u=v['u'];n=v['n'];length=v['store_length'];cut=[0,length*.29,length*.65,length]
  def tp(x,z):return[a[0]+u[0]*x+n[0]*z,a[1]+u[1]*x+n[1]*z]
  def tr(x0,z0,x1,z1):return Polygon([tp(x,z)for x,z in[(x0,z0),(x1,z0),(x1,z1),(x0,z1)]])
  # RF keeps real enclosed pavilion lounge/management rooms and outdoor decks; never calls the sky a store.
  for k in range(3):
   if level==3 and k>0:continue
   depth=12. if level==3 else 24.5
   x0=cut[k]+.25;x1=cut[k+1]-.25;poly=tr(x0,.15,x1,depth);entry=tp((x0+x1)/2,.15);back=tr(x0+.15,depth-4,x1-.15,depth-.2)
   line=LineString([entry,tp((x0+x1)/2,depth-2.5)]);aisle=line.buffer(1.2,cap_style=2).intersection(poly);sales=poly.difference(back);shelves=sales.buffer(-.6).difference(aisle.buffer(.2));id=f'C{LABEL[level]}-{v["id"]}-{k+1}'
   doorshape=LineString([tp((x0+x1)/2-1.5,.15),tp((x0+x1)/2+1.5,.15)]).buffer(.5,cap_style=2);wall=poly.boundary.buffer(.125,join_style=2).difference(doorshape)
   partition=back.boundary.intersection(sales.boundary).buffer(.1).difference(line.buffer(.85));wall=wall.union(partition)
   item=dict(id=id,pavilion=v['id'],category=RETAIL_PROGRAM[level][v['id']][k]if level in RETAIL_PROGRAM else CATEGORIES[level][(j+k)%3],kind='retail'if level in[0,1,2]else'facility',polygon=poly,entry=entry,u=u,n=n,door_width_m=3.,frontage_m=x1-x0,depth_m=depth-.15,backroom=back,sales=sales,shelf_zones=shelves,aisles=aisle,main_route=list(line.coords),back_door=tp((x0+x1)/2,depth-4),back_door_width_m=1.7,wall_solids=wall,legacy_id=None,service_route='館内EV→棟内前廊（閉店後）→店内主路→専用バックルーム')
   stores.append(item)
  pavs.append(dict(id=v['id'],name=v['name'],footprint=v['footprint'],front_corridor=v['front_corridor'],roof_accessible=level==3))
 corridors=unary_union([v['front_corridor']for v in PAV]);rr=[r for r in ROUTES if level in r['levels']]
 # Deck squares are smaller than 1F plazas: preserve views into the garden rather than filling all sky gaps.
 courts=unary_union([p['polygon']for p in PLAZAS])if level in[-1,0]else Polygon()
 routefloor=unary_union([r['poly']for r in rr]);corepublic=unary_union([c['public']for c in CORES]);shaft=unary_union([c['shafts']for c in CORES]+[e['shaft']for e in ESC if level in e['levels']]+[m['geom']for m in BANK_MEDIANS if level in m['levels']]);aprons=unary_union([q.buffer(.2)for e in ESC if level in e['levels']for q in e['landings']]);allbuild=unary_union([v['footprint']for v in PAV]);public=routefloor.union(courts).union(aprons).difference(allbuild).union(corridors).union(corepublic).difference(shaft)
 roofbeds=[]
 if level==3:
  for v in PAV:
   a=v['a'];u=v['u'];n=v['n'];l=v['store_length'];tp=lambda x,z:(a[0]+u[0]*x+n[0]*z,a[1]+u[1]*x+n[1]*z)
   garden=Polygon([tp(x,z)for x,z in[(l*.29+2,6),(l-2,6),(l-2,19),(l*.29+2,19)]])
   roofbeds.append(dict(id='ROOF-'+v['id'],kind='roof_garden',geom=garden))
  roofopen=allbuild.buffer(-.3).difference(unary_union([s['polygon']for s in stores]+[g['geom']for g in roofbeds]))
  public=public.union(roofopen).difference(shaft)
 # Separate the basement from the outdoor landscape, upper decks from ground gardens.
 outdoors=(public.difference(corepublic)if level==3 else public.difference(unary_union([v['footprint']for v in PAV])))if level>=0 else Polygon()
 indoor=public.difference(outdoors)
 furniture=[]
 for plaza in PLAZAS:
  center=plaza['polygon'].centroid
  for sign in[-1,1]:
   x,z=center.x+sign*14,center.y+9;bench=box(x-1.6,z-.4,x+1.6,z+.4);plant=box(x-1,z+1,x+1,z+2.2);g=bench.union(plant)
   # Preserve at least 3m to primary route centerline and 1m from platform edges.
   if public.buffer(-1).covers(g)and min(LineString(r['points']).distance(g)for r in rr)>3:
    furniture +=[dict(id=f'{plaza["id"]}-{level}-{sign}-B',kind='bench',geom=bench,height=.85),dict(id=f'{plaza["id"]}-{level}-{sign}-P',kind='planter',geom=plant,height=1.3)]
 obstacles=unary_union([c['room_wall_solids']for c in CORES]+[q['geom']for c in CORES for q in c['fixtures']]+[f['geom']for f in furniture]);walk=public.difference(obstacles.buffer(.03));allbuild=unary_union([v['footprint']for v in PAV]);plate=allbuild.union(public).difference(shaft);void=Polygon()if level in[-1,0]else box(-660,-380,-240,-100).difference(allbuild.union(public))
 residual=allbuild.difference(public.union(unary_union([s['polygon']for s in stores])).union(shaft))
 f=dict(level=level,label=LABEL[level],height=HEIGHT[level],shell=allbuild,public=public,walkable=walk,floor_plate=plate,void=void,shafts=shaft,residual=residual,stores=stores,cores=CORES,escalators=[e for e in ESC if level in e['levels']],pavilions=pavs,outdoor_deck=outdoors if level>0 else Polygon(),outdoor_ground=outdoors if level==0 else Polygon(),indoor_public=indoor,landscape=LANDSCAPE if level==0 else roofbeds if level==3 else[],furniture=furniture,route_ids=[r['id']for r in rr],weather='屋内地下連絡'if level==-1 else'屋外・庇下の歩行路/デッキ',service_access='棟裏の管理用動線は一般客と時間分離。搬入車は地下東側ヤードで荷下ろししEVへ。')
 if level>0:
  edges=(outdoors.boundary.difference(allbuild.buffer(.2))if level<3 else outdoors.boundary.difference(unary_union([s['polygon']for s in stores]).buffer(.2)))
  if level==1:edges=edges.difference(Point(-432,-117).buffer(4))
  f['guardrails']=edges.buffer(.04,cap_style=2).difference(unary_union([q.buffer(.1)for e in f['escalators']for q in e['landings']]))
 else:f['guardrails']=Polygon()
 f['guardrail_height_m']=1.2
 FLOORS.append(f)
# Ground planting remains outside the assigned public footpaths, with a 0.5m management margin.
ground=next(f for f in FLOORS if f['level']==0)
for garden in LANDSCAPE:
 pieces=ps(garden['geom'].difference(ground['public'].buffer(.5)))
 garden['geom']=max(pieces,key=lambda q:q.area)if pieces else Polygon()

# Old catalog identities: nearest new same-floor retail unit, all old IDs remain aliases.
old=json.loads((R/'docs/map-master-floor-plans.json').read_text());migrations=[]
for prior in old:
 if prior['building']!='C':continue
 floor=next(f for f in FLOORS if f['level']==prior['level']);used=set()
 for s in prior['shops']:
  poly=Polygon(s['polygon']);p=poly.centroid;terms={'clothes':['ファッション','服飾'],'sport':['スポーツ'],'home':['生活雑貨','家具'],'books':['書籍','書店'],'shoes':['靴'],'cafe':['カフェ']}[s['kind']];eligible=[t for t in floor['stores']if t['id']not in used and any(term in t['category']for term in terms)];assert eligible,s;target=min(eligible,key=lambda t:Point(t['entry']).distance(p));used.add(target['id']);target['legacy_id']=s['id'];migrations.append(dict(old_id=s['id'],old_level=prior['level'],old_reference='旧区画の重心（入口座標ではない）',old_x=p.x,old_z=p.y,new_id=target['id'],new_reference='新店舗入口',new_x=target['entry'][0],new_z=target['entry'][1],kind=s['kind'],new_category=target['category']))
for m in migrations:
 terms={'clothes':['ファッション','服飾'],'sport':['スポーツ'],'home':['生活雑貨','家具'],'books':['書籍','書店'],'shoes':['靴'],'cafe':['カフェ']}[m['kind']]
 ck('legacy_function_retained',m['old_id'],any(term in m['new_category']for term in terms),m['new_category'],m['old_level'])
# Checks are exact-area geometric tests plus explicitly bounded portal distance, not dynamic Godot walking.
ROUTEPATHS=[]
for f in FLOORS:
 lev=f['level'];pub=f['public'];walk=f['walkable'];main=max(ps(walk.buffer(-.35)),key=lambda q:q.area)
 ck('public_shape_valid',f['label'],pub.is_valid,None,lev);ck('floor_plate_valid',f['label'],f['floor_plate'].is_valid,None,lev)
 ck('public_excludes_shafts',f['label'],pub.intersection(f['shafts']).area<EPS,pub.intersection(f['shafts']).area,lev)
 ck('plate_excludes_shafts',f['label'],f['floor_plate'].intersection(f['shafts']).area<EPS,f['floor_plate'].intersection(f['shafts']).area,lev)
 ck('plate_covers_public',f['label'],pub.difference(f['floor_plate']).area<EPS,pub.difference(f['floor_plate']).area,lev)
 ck('all_front_corridors_connected',f['label'],all(main.distance(Point(v['front_mid']))<.6 for v in PAV),None,lev)
 for i,s in enumerate(f['stores']):
  ck('entrance_on_lot',s['id'],s['polygon'].boundary.distance(Point(s['entry']))<1e-7,None,lev)
  ck('entrance_reaches_main_component',s['id'],main.distance(Point(s['entry']))<.7,main.distance(Point(s['entry'])),lev)
  swept=substring(LineString(s['main_route']),.8,LineString(s['main_route']).length).buffer(.4)
  ck('interior_path_inside',s['id'],swept.difference(s['polygon']).area<EPS,swept.difference(s['polygon']).area,lev)
  ck('interior_path_no_wall',s['id'],swept.intersection(s['wall_solids']).area<EPS,swept.intersection(s['wall_solids']).area,lev)
  ck('interior_path_no_shelves',s['id'],LineString(s['main_route']).intersection(s['shelf_zones']).length<EPS,None,lev)
  ck('retail_no_public_overlap',s['id'],s['polygon'].intersection(pub).area<EPS,s['polygon'].intersection(pub).area,lev)
  for t in f['stores'][i+1:]:ck('stores_do_not_overlap',s['id']+'/'+t['id'],s['polygon'].intersection(t['polygon']).area<EPS,None,lev)
 for c in CORES:
  ck('core_entry_reaches_common',c['id'],main.distance(Point(c['entry']))<.7,main.distance(Point(c['entry'])),lev)
  # Front lobby / lift / stair entry and accessible access follow drawn partitions, no fictitious direct ray through walls.
  corefree=c['walkable'].buffer(-.3);parts=ps(corefree);comp=min(parts,key=lambda p:p.distance(Point(c['entry'])))
  for d in c['doors']:
   ck('core_portal_access',c['id']+'/'+d['id'],comp.distance(Point(d['p']))<.65,comp.distance(Point(d['p'])),lev)
 for e in f['escalators']:
  for j,land in enumerate(e['landings']):ck('escalator_landing_connected',e['id']+'/'+str(j),main.distance(land.centroid)<.01,main.distance(land.centroid),lev)
 for piece in f['furniture']:ck('furniture_on_public_floor',piece['id'],pub.covers(piece['geom']),None,lev)
 for r in[r for r in ROUTES if lev in r['levels']]:
  ck('route_has_purpose',r['id'],bool(r['role']),r['role'],lev)
  ck('route_centerline_in_public',r['id'],LineString(r['points']).difference(pub.buffer(1e-7)).length<.01,LineString(r['points']).difference(pub.buffer(1e-7)).length,lev)
  for i,p in enumerate([r['points'][0],r['points'][-1]]):ck('route_endpoint_connected',r['id']+'/'+str(i),main.distance(Point(p))<1,main.distance(Point(p)),lev)
 ck('residual_excludes_public',f['label'],f['residual'].intersection(pub).area<EPS,None,lev)
 for s in f['stores']:
  for c in CORES:ck('store_and_stair_same_component',s['id']+'/'+c['id'],main.distance(Point(s['entry']))<.7 and main.distance(Point(c['entry']))<.7,None,lev)
for f in FLOORS:
 if f['level']<=0:continue
 for plaza in PLAZAS:
  reserve=plaza['polygon'].difference(unary_union([v['footprint']for v in PAV]).buffer(.25)).buffer(-7)if plaza['id']!='C-CENTRAL'else Point(-465,-245).buffer(18)
  ck('upper_garden_open_to_sky',plaza['id'],f['floor_plate'].intersection(reserve).area<EPS,f['floor_plate'].intersection(reserve).area,f['level'])
for i,v in enumerate(PAV):
 for w in PAV[i+1:]:ck('independent_pavilions_disjoint',v['id']+'/'+w['id'],v['footprint'].intersection(w['footprint']).area<EPS,None)
for level,point,width in[(0,(-370,-80),8),(1,(-432,-117),5)]:
 f=next(f for f in FLOORS if f['level']==level);ck('B_fixed_endpoint_in_public',f['label'],f['public'].covers(Point(point)),point,level)
 ck('B_end_width_cross_section',f['label'],f['public'].buffer(1e-7).covers(LineString([(point[0]-width/2,point[1]-.2),(point[0]+width/2,point[1]-.2)])),width,level)
# A loading yard is a specific reserved area rather than an invisible road under public paths.
LOADING=dict(id='C-LOAD',polygon=box(-235,-273,-205,-224),truck_gate=[-205,-250],pedestrian_gate=[-235,-248],vehicle_route=[[-200,-250],[-220,-250]],hours='閉店後の台車搬送。一般歩行と運用分離。道路/トラック旋回の実車検討は未検証。')
# Draw the enclosed basement and its separate delivery yard explicitly.
for f in FLOORS:
 if f['level']!=-1:continue
 staff_points=[[-235,-248],[-243,-284],[-276,-287],[-288,-270]]
 f['staff_corridor']=LineString(staff_points).buffer(1.5,cap_style=2,join_style=2)
 f['loading_yard']=LOADING['polygon'];f['staff_route_points']=staff_points
 f['shell']=f['shell'].union(f['public']).union(f['staff_corridor']).union(f['loading_yard']).buffer(.3,join_style=2)
 f['floor_plate']=f['shell'].difference(f['shafts'])
 f['residual']=f['shell'].difference(f['public'].union(unary_union([s['polygon']for s in f['stores']])).union(f['shafts']))
 f['enclosure']='地下共用ホールの外周は壁で閉鎖。搬入ヤードは管理ゲートで客動線と分離。地上の独立棟群と外周は一致させない。'
 ck('basement_yard_outside_public','C-LOAD',f['loading_yard'].intersection(f['public']).area<EPS,f['loading_yard'].intersection(f['public']).area,-1)
 ck('basement_support_covers_public','B1',f['public'].difference(f['floor_plate']).area<EPS,None,-1)

DATA=dict(wing='C',version='C detailed design v1',coordinate_system='World XZ metres',design_only=True,game_implemented=False,floors=FLOORS,pavilions=PAV,cores=CORES,escalators=ESC,bank_medians=BANK_MEDIANS,routes=ROUTES,plazas=PLAZAS,landscape=LANDSCAPE,loading=LOADING,connections=[dict(id='BC-1-C',level=0,point=[-370,-80],width=8,height=0),dict(id='BC-2-C',level=1,point=[-432,-117],width=5,height=5.525)],vertical_links=[dict(id=c['id'],kind='stair_and_EV',levels=[-1,0,1,2,3],entry=c['entry'],lift_door=next(d['p']for d in c['doors']if d['id']=='EV'),stair_door=next(d['p']for d in c['doors']if d['id']=='ST'),heights=HEIGHT)for c in CORES],view_cameras=[dict(id='C-south-eye',plaza='C-GATE',level=0,p=[-438,-145,1.65],target=[-452,-210,3.5]),dict(id='C-garden-eye',plaza='C-CENTRAL',level=0,p=[-459,-225,1.65],target=[-465,-275,6]),dict(id='C-deck-eye',plaza='C-NORTH-GARDEN',level=1,p=[-474,-294,7.175],target=[-467,-327,8.7])],view_camera_axis_order='World X, World Z, World Y',reference=dict(source='AEON_LAKETOWN_OFFICIAL_FLOOR_GUIDE_202610.pdf pages7-8',visual_read=True,adopted='独立棟・1st/2nd/3rd街路と合流広場・上階デッキ・屋外の庭',original_game_design='6棟配置、ゲーム用寸法、B1/3F/RFと階高。実在施設を測量/完全再現していない。'),unverified=['Godot実歩行/コリジョン','群衆/猫/宝箱経路と描画負荷','避難・構造・防水・雨風/積雪/法規','搬入車旋回/地下駐車の車両シミュレーション','最終サインの視認性・夜間照明','B館B1/3F/RFは現時点で未設計のため直接館間接続を作らない'])
(O/'geometry.json').write_text(json.dumps(DATA,default=enc,ensure_ascii=False,indent=2));(O/'checks.json').write_text(json.dumps(CHECKS,default=enc,ensure_ascii=False,indent=2));(O/'id-migration.json').write_text(json.dumps(migrations,ensure_ascii=False,indent=2))
for name,headers,rows in[
 ('tenant-ledger.csv',['階','新ID','棟','用途','区画㎡','間口m','奥行m','入口幅m','入口WorldX','入口WorldZ','高さm','バックルーム㎡','旧ID'],[[f['label'],s['id'],s['pavilion'],s['category'],s['polygon'].area,s['frontage_m'],s['depth_m'],s['door_width_m'],*s['entry'],f['height'],s['backroom'].area,s['legacy_id']or'']for f in FLOORS for s in f['stores']]),
 ('id-migration.csv',['旧ID','旧階level','旧比較点','旧WorldX','旧WorldZ','新ID','新比較点','新WorldX','新WorldZ','旧用途','新用途'],[[m[k]for k in['old_id','old_level','old_reference','old_x','old_z','new_id','new_reference','new_x','new_z','kind','new_category']]for m in migrations]),
 ('route-register.csv',['ID','名称','用途','階level','幅m','延長m','全座標JSON'],[[r['id'],r['name'],r['role'],str(r['levels']),r['width'],LineString(r['points']).length,json.dumps(r['points'])]for r in ROUTES]),
 ('equipment-register.csv',['核','入口','WorldX','WorldZ','幅m','全階高さm'],[[c['id'],d['id'],*d['p'],d['w'],str(list(HEIGHT.values()))]for c in CORES for d in c['doors']])]:
 with(O/name).open('w',encoding='utf-8-sig',newline='')as fp:w=csv.writer(fp);w.writerow(headers);w.writerows(rows)
failed=[c for c in CHECKS if not c['pass_']];summary=dict(checks=len(CHECKS),passed=len(CHECKS)-len(failed),failed=failed,shop_counts={f['label']:len(f['stores'])for f in FLOORS},retail_counts={f['label']:sum(s['kind']=='retail'for s in f['stores'])for f in FLOORS},legacy_count=len(migrations),design_only=True,runtime_walk_tests=0,view_cameras=len(DATA['view_cameras']))
with(O/'dead-end-review.csv').open('w',encoding='utf-8-sig',newline='')as fp:
 w=csv.writer(fp);w.writerow(['通路ID','末端の役割','用途','判断'])
 for r in ROUTES:w.writerow([r['id'],'B館固定接続端'if r['id'].startswith('BC')else'昇降機乗降口と店舗街'if'ACCESS'in r['id']else'店舗街/広場の接続節点',r['role'],'維持（用途あり・主成分へ接続）'])
(O/'verification.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False,indent=2))
