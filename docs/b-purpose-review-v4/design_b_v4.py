"""B-wing purpose-led drawing revision. Writes docs/downloads only, never game assets."""
from pathlib import Path
import sys,json,math,csv,heapq,ast,hashlib,subprocess,collections
sys.path.append('/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
import numpy as np
import shapely
from shapely.geometry import Polygon,LineString,Point,box,mapping,shape
from shapely.ops import unary_union,nearest_points,substring
from shapely import affinity,make_valid,set_precision
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/b-purpose-review-v4';OUT.mkdir(exist_ok=True)
BASE=ROOT/'docs/b-detailed-review-v3';RAW=json.loads((BASE/'geometry.json').read_text())
BASELINE='3dfe8f5a0245dde804566ea0b3af138cebd2d78c'
def decode(o):
 if isinstance(o,dict):
  if 'type'in o and 'coordinates'in o:return shape(o)
  return{k:decode(v)for k,v in o.items()}
 if isinstance(o,list):return[decode(v)for v in o]
 return o
OLD=decode(RAW)
def enc(o):
 if hasattr(o,'geom_type'):return mapping(o)
 if isinstance(o,np.generic):return o.item()
 raise TypeError(type(o))
def polys(g):return [] if g.is_empty else[g]if g.geom_type=='Polygon'else[p for p in getattr(g,'geoms',[])if p.geom_type=='Polygon']
def clean(g):return make_valid(g).buffer(0)
def snap(g):return clean(set_precision(clean(g),.001))
def rect(c,u,l,w):
 n=(-u[1],u[0]);return Polygon([(c[0]+u[0]*a+n[0]*b,c[1]+u[1]*a+n[1]*b)for a,b in[(-l/2,-w/2),(l/2,-w/2),(l/2,w/2),(-l/2,w/2)]])
def world(p):return[p[0]-714,p[1]-30]
HEIGHT={1:0.,2:5.525,3:10.875};CHECKS=[];CHANGES=[]
def chk(k,id,ok,value=None,floor=None):CHECKS.append(dict(kind=k,id=id,pass_=bool(ok),value=value,floor=floor))
def moveall(o,dx,dz):
 if hasattr(o,'geom_type'):return affinity.translate(o,dx,dz)
 if isinstance(o,dict):return{k:moveall(v,dx,dz)for k,v in o.items()}
 if isinstance(o,list):return[moveall(v,dx,dz)for v in o]
 return o
# Keep the equipment-room specification; move the whole core, every room and every opening together.
CORES=[]
for old,new,angle in zip(OLD['cores'],[(174,25),(213,145),(388,160)],[0,180,180]):
 cx,cz=old['centre'];dx,dz=new[0]-cx,new[1]-cz;c=moveall(old,dx,dz)
 # K3 changes from south-facing to north-facing, to meet the adjoining retail gallery.
 if angle!=old['angle']:
  def rotate_obj(o):
   if hasattr(o,'geom_type'):return affinity.rotate(o,180,origin=new)
   if isinstance(o,dict):return{k:rotate_obj(v)for k,v in o.items()}
   if isinstance(o,list):return[rotate_obj(v)for v in o]
   return o
  c=rotate_obj(c)
 for key in ['doors','cubicle_doors']:
  for d,od in zip(c[key],old[key]):
   p=[od['p'][0]+dx,od['p'][1]+dz]
   if angle!=old['angle']:p=[2*new[0]-p[0],2*new[1]-p[1]]
   d['p']=p;d['axis']=[-v if angle!=old['angle']else v for v in od['axis']]
 c['centre']=list(new);c['angle']=angle;c['entry']=[new[0],new[1]+(10 if angle==0 else-10)]
 CORES.append(c);CHANGES.append(dict(id='R-'+old['id'],before=f"設備核{old['id']} {old['centre']}",after=f"{new} / 入口{c['entry']}",reason='長い無店舗の設備枝道を短縮し、店舗街の裏側へ設備核を寄せる。'))
# One long rectangular lightwell; one cross-bridge court; one curved eastern fan court.
wing=box(67,48,119,73).buffer(-3).buffer(3,quad_segs=8)
time=box(273,61,297,91)
light=Polygon([(407,76),(416,60),(434,52)]+[(434+28*math.cos(a),76+24*math.sin(a))for a in np.linspace(-math.pi/2,math.pi/2,33)]+[(417,97)])
VOIDS=[snap(v)for v in[wing,time,light]]
BRIDGE=box(255,68,315,72)
PLAZAS=[dict(id='P-W',name='翼の広場',void=VOIDS[0],court=VOIDS[0].buffer(12,join_style=2).union(box(60,28,126,48)).union(box(63,73,123,91)),gateways={'西核店':(59,74),'中央専門店街':(128,75.5),'南西専門店街':(113,84),'北側店舗列':(94,30)},role='西核店の前庭・待ち合わせ・長軸吹き抜け',landscape='長い見通しと連続する上階ギャラリー。北側1→2F、南側2→3Fの昇降機。'),dict(id='P-T',name='時の広場',void=VOIDS[1],court=box(255,43,315,109).union(box(242,98,259,114)),gateways={'中央専門店街':(260,76),'北専門店街/C館':(286,49),'東専門店街':(313,89.4),'南西専門店街':(248,103)},role='専門店街の交差・北側連絡口の案内・横断橋',landscape='偏心した矩形開口と上下階共通の4m横断橋。南側の時計・腰掛け溜まりを分離。'),dict(id='P-L',name='光の広場',void=VOIDS[2],court=VOIDS[2].buffer(13,join_style=2),gateways={'東専門店街':(402,92),'南東専門店街':(469,100),'東核店':(470,68),'A館':(450,46)},role='東核店とA館接続の分配・飲食前の休憩',landscape='東側の曲面吹き抜けと扇状の視界。湾曲する上階手すり、対角の昇降機。')]
ALL_ESC=[];BANK_MEDIANS=[]
# Banks face atria, leaving at least a separate gallery beside each bank; no coincident 12/23 shafts.
for j,(c12,u12,c23,u23) in enumerate([((88,40),(1,0),(98,81),(1,0)),((263,93),(0,1),(306,93),(0,1)),((426,46.3),(.8660254,-.5),(456,101),(.7660444,-.6427876))]):
 for levels,c,u in[([1,2],c12,u12),([2,3],c23,u23)]:
  n=(-u[1],u[0]);BANK_MEDIANS.append(dict(levels=levels,atrium=j+1,geom=rect(c,u,14.8,1.6)))
  for lane,direction in[(-2,'UP'),(2,'DOWN')]:
   mid=(c[0]+n[0]*lane,c[1]+n[1]*lane);shaft=rect(mid,u,14.8,2.4);lands=[rect((mid[0]+u[0]*sign*8.9,mid[1]+u[1]*sign*8.9),u,3,3.6)for sign in[-1,1]]
   ALL_ESC.append(dict(id=f'E{j+1}-{levels[0]}{levels[1]}-{direction}',atrium=j+1,levels=levels,direction=direction,c=mid,u=u,shaft=shaft,landings=lands,run_m=11.8,width_m=2.4,comb_m=1.5))
# Incorporate only necessary escalator aprons, without preserving the old general walk polygon.
for j,p in enumerate(PLAZAS):
 banks=unary_union([g for e in ALL_ESC if e['atrium']==j+1 for g in[e['shaft'],*e['landings']]])
 p['court']=snap(p['court'].union(banks.buffer(2,join_style=2)).buffer(1,join_style=2).buffer(-1,join_style=2))
# Every public route has named endpoints and a concrete commercial/facility reason.
ROUTES=[]
def route(id,name,points,width,role,links,levels=(1,2,3),reason='既存の店舗列に沿う共用アクセス'):
 ROUTES.append(dict(id=id,name=name,points=points,width=width,role=role,links=links,levels=list(levels),reason=reason,poly=snap(LineString(points).buffer(width/2,cap_style=3,join_style=2))))
route('M-W','西核店前専門店街',[(8,85),(59,74)],16,'店舗アクセス・核店と広場接続',['西核店','P-W'])
route('M-C1','中央専門店街・西区間',[(128,75.5),(184,95)],16,'店舗アクセス・分岐接続',['P-W','J-C'])
route('M-C2','中央専門店街・東区間',[(184,95),(260,76)],16,'店舗アクセス・広場接続',['J-C','P-T'])
route('M-E1','東専門店街・西区間',[(313,89.4),(354,109)],16,'店舗アクセス・分岐接続',['P-T','J-E'])
route('M-E2','東専門店街・東区間',[(354,109),(402,92)],16,'店舗アクセス・広場接続',['J-E','P-L'])
route('N-W','北専門店街・西区間',[(184,95),(192,35)],9,'店舗アクセス・WC/EV分岐',['J-C','J-NW'])
route('N-M','北専門店街・中央区間',[(192,35),(277,28)],9,'店舗アクセス・C館分岐',['J-NW','J-NC'])
route('N-E','北専門店街・東区間',[(277,28),(286,49)],9,'店舗アクセス・北口から広場へ分配',['J-NC','P-T'])
route('SW-1','南西専門店街・西区間',[(113,84),(136,112)],9,'店舗アクセス・広場接続',['P-W','J-SW'])
route('SW-2','南西専門店街・中央区間',[(136,112),(220,125)],9,'店舗アクセス・WC分岐',['J-SW','J-SC'])
route('SW-3','南西専門店街・東区間',[(220,125),(248,103)],9,'店舗アクセス・広場接続',['J-SC','P-T'],reason='西側店舗列から時の広場の待合前庭へ。空白だった区間にカフェ/雑貨の入口を計画し、余端を切る。')
route('SE-1','南東専門店街・西区間',[(354,109),(375,139)],9,'店舗アクセス・分岐接続',['J-E','J-SE'])
route('SE-2','南東専門店街・中央区間',[(375,139),(452,122)],9,'店舗アクセス・WC分岐',['J-SE','J-SEE'])
route('SE-3','南東専門店街・東区間',[(452,122),(469,100)],9,'店舗アクセス・広場接続',['J-SEE','P-L'])
route('A-E','東核店前アプローチ',[(470,68),(480,65)],10,'核店へのアクセス',['P-L','東核店'])
for c,points in zip(CORES,[[(192,35),(174,35)],[(213,124),(213,135)],[(388,136.13),(388,150)]]):
 route(c['id']+'-A',c['id']+' お手洗い・EV・階段前',points,8,'設備アクセス・必要な行き止まり',[c['id'],{'K1':'J-NW','K2':'SW-2中間口','K3':'SE-2中間口'}[c['id']]],reason='共用設備への最短の枝。末端は設備前室であり、探索用の袋小路ではない。')
route('AB-1','A館地上連絡',[(450,46),(474,24.5),(540,24.5)],5,'館間連絡',['P-L','A館1F'],(1,),reason='既存A館側端点World(-174,-5.5)を維持。')
route('AB-2','A館2階連絡橋',[(450,46),(474,24.5),(604,24.5)],5,'館間連絡',['P-L','A館2F'],(2,),reason='既存A館側端点World(-110,-5.5)を維持。')
route('BC-1','C館地上連絡',[(277,28),(277,-35),(344,-35),(344,-50)],8,'館間連絡',['J-NC','C館1F'],(1,),reason='既存C館側端点World(-370,-80)を維持。専門店のない部分は屋外連絡路。')
route('BC-2','C館2階連絡橋',[(277,28),(277,-35),(282,-35),(282,-87)],5,'館間連絡',['J-NC','C館2F'],(2,),reason='既存C館テラスWorld(-432,-117)へ接続。')
# The v3 lift waiting strip was only 1m deep beside the accessible WC. Re-plan the core locally.
for c in CORES:
 cx,cz=c['centre'];ang=c['angle']
 def local(g):return affinity.translate(affinity.rotate(g,ang,origin=(0,0)),cx,cz)
 c['rooms']['accessible_wc']=local(box(-4,-2,0,2))
 c['rooms']['lift_lobby']=local(box(-4,2,2,6))
 c['rooms']['ev_front_lobby']=local(box(-4,-5,2,-2))
 d=next(d for d in c['doors']if d['id']=='AWC');pp=local(Point(0,0));d['p']=[pp.x,pp.y]
 wall=unary_union([r.boundary.buffer(.10,join_style=2)for key,r in c['rooms'].items()if key not in['front_lobby','lift_access','lift_lobby','ev_front_lobby']])
 for d in c['doors']:wall=wall.difference(rect(d['p'],d['axis'],d['w'],1.0))
 c['room_wall_solids']=wall
 CHANGES.append(dict(id='R-EV-'+c['id'],reason='多目的WCを2mずらし、EV前の有効待合を奥行3mに拡大。旧1m隙間を移動経路として使わない。'))
for r in ROUTES:
 if r['id']in['M-W','A-E']:r['poly']=snap(LineString(r['points']).buffer(r['width']/2,cap_style=2,join_style=2))
 if r['id']=='A-E':r['poly']=r['poly'].union(box(472,57,482,71))
# Ground-floor protected discharge lanes. They do not become new upper-floor dead-end walkways.
EGRESS=[dict(id='EX-K1',points=[(165.5,16),(165.5,-1)],width=3,stair='K1'),dict(id='EX-K2',points=[(221.5,154),(221.5,190)],width=3,stair='K2'),dict(id='EX-K3',points=[(396.5,169),(396.5,190)],width=3,stair='K3')]
for e in EGRESS:e['poly']=LineString(e['points']).buffer(1.5,cap_style=3)
for c,e in zip(CORES,EGRESS):
 c['ground_discharge_door']=dict(p=e['points'][0],w=1.5,axis=[1,0],levels=[1])
 c['ground_room_wall_solids']=c['room_wall_solids'].difference(rect(e['points'][0],(1,0),1.5,4.))
# Reserve open plaza sightlines / movement bands before placing any furniture.
for p in PLAZAS:
 points=list(p['gateways'].values());p['sight_reservations']=unary_union([LineString([a,b]).buffer(3,cap_style=2)for i,a in enumerate(points)for b in points[i+1:]])
 p['bridges']=BRIDGE if p['id']=='P-T'else Polygon()
 p['perimeter_walk']=p['void'].buffer(6,join_style=2).boundary.buffer(2.5)
FLOORS=[];RETIRED=[]
# A robust local visibility route, executed against drawn floor geometry (not Godot movement).
def interior_path(p,start,end):
 inset=p.buffer(-.65,join_style=2);parts=polys(inset)
 if not parts:raise RuntimeError('No interior clearance')
 comp=min(parts,key=lambda q:q.distance(Point(start)));a=nearest_points(comp,Point(start))[0];b=nearest_points(comp,Point(end))[0]
 if comp.buffer(.003).covers(LineString([a,b])):return[list(start),[a.x,a.y],[b.x,b.y],list(end)]
 nodes=[(a.x,a.y),(b.x,b.y)]+list(comp.exterior.coords)[:-1]
 for hole in comp.interiors:nodes+=list(hole.coords)[:-1]
 graph=[[]for _ in nodes]
 for i,aa in enumerate(nodes):
  for j in range(i):
   seg=LineString([aa,nodes[j]])
   if comp.buffer(.003).covers(seg):graph[i].append((j,seg.length));graph[j].append((i,seg.length))
 dist={0:0};prev={};heap=[(0,0)]
 while heap:
  cc,i=heapq.heappop(heap)
  if cc!=dist[i]:continue
  if i==1:break
  for j,dd in graph[i]:
   nc=cc+dd
   if nc<dist.get(j,1e30):dist[j]=nc;prev[j]=i;heapq.heappush(heap,(nc,j))
 if 1 not in dist:raise RuntimeError('Disconnected interior')
 ids=[1]
 while ids[-1]!=0:ids.append(prev[ids[-1]])
 return[list(start)]+[list(nodes[i])for i in ids[::-1]]+[list(end)]
for old in OLD['floors']:
 floor=old['floor'];rr=[r for r in ROUTES if floor in r['levels']]
 raw=unary_union([r['poly']for r in rr]+[p['court']for p in PLAZAS])
 bridge=BRIDGE if floor>1 else Polygon();void=unary_union(VOIDS).difference(bridge)if floor>1 else Polygon()
 shafts=unary_union([e['shaft']for e in ALL_ESC if floor in e['levels']]+[m['geom']for m in BANK_MEDIANS if floor in m['levels']])
 coreout=unary_union([c['outline']for c in CORES]);eg=unary_union([e['poly']for e in EGRESS])if floor==1 else Polygon()
 public=snap(raw.union(bridge).difference(unary_union([void,shafts,coreout]).buffer(.16)))
 # Old rectangular anchors get a normal frontage rather than a concourse finger inside the sales floor.
 stores=[]
 candidates=[]
 extra=[];aa=(220,125);bb=(248,103);length=math.dist(aa,bb);u=((bb[0]-aa[0])/length,(bb[1]-aa[1])/length);n=(-u[1],u[0])
 west_anchor=box(-35,45,8,110).union(box(-35,45,55,65))
 east_anchor=Polygon([(480,31),(530,31),(530,100),(490,100),(480,78)])
 winglots=[box(64,6,90,30),box(92,6,119,30),box(63,89,87,113),box(89,89,113,113)]
 oldlots=unary_union([s['polygon']for s in old['stores']if s['kind']=='tenant'])
 for side in[-1,1]:
  for k,t in enumerate([1.,18.]):
   def sq(a,b):return(aa[0]+u[0]*a+n[0]*b*side,aa[1]+u[1]*a+n[1]*b*side)
   lot=Polygon([sq(t,4.5),sq(t+15,4.5),sq(t+15,22.5),sq(t,22.5)]).difference(oldlots)
   extra.append(dict(id=f'B{floor}-SW{side+2}{k+1}',polygon=lot,entry=list(sq(t+7.5,4.5)),kind='tenant',category=['カフェ・焼菓子','旅行・雑貨'][k],legacy_name=''))
 for wi,lot in enumerate(winglots):extra.append(dict(id=f'B{floor}-W{wi+1}',polygon=lot,entry=[lot.centroid.x,28 if wi<2 else 91],kind='tenant',category=['生活・服飾','書籍・雑貨','カフェ','レストラン'][wi],legacy_name=''))
 for s in old['stores']+extra:
  s=s.copy();s['v3_entry']=list(s['entry']);s['v3_area_m2']=s['polygon'].area
  for stale in['previous_entry','source_area_m2','rear']:s.pop(stale,None)
  if s['kind']=='anchor':
   if'AW'in s['id']:s['polygon']=west_anchor;s['entry']=[55,57]
   else:s['polygon']=Polygon([(480,31),(530,31),(530,100),(490,100),(480,78)]);s['entry']=[480,65]
  if s['kind']=='tenant'and '-W'not in s['id']:s['polygon']=s['polygon'].difference(unary_union([west_anchor,east_anchor,*winglots]))
  if s['kind']=='anchor':s['polygon']=s['polygon'].difference(unary_union([ss['polygon']for ss in stores]).buffer(.02))
  forbidden=unary_union([public,void,shafts,coreout,eg]);parts=polys(snap(s['polygon'].difference(forbidden)))
  if not parts:RETIRED.append(dict(floor=floor,id=s['id'],reason='新しい広場/設備/連絡路と競合'));continue
  p=snap(max(parts,key=lambda a:a.area).simplify(.002,preserve_topology=True))
  if p.area<45:RETIRED.append(dict(floor=floor,id=s['id'],reason='有効売場45㎡未満。無理な小区画として残さない'));continue
  opts=[];xy=list(p.exterior.coords)
  for a,b in zip(xy,xy[1:]):
   full_edge=LineString([a,b]);interface=full_edge.intersection(public.buffer(.02));w=6 if s['kind']=='anchor'else 2.4
   for edge in([interface]if interface.geom_type=='LineString'else getattr(interface,'geoms',[])):
    if edge.geom_type!='LineString' or edge.is_empty:continue
    mid=edge.interpolate(.5,normalized=True)
    if edge.length>=w+.2:opts.append((mid.distance(Point(s['entry']))-(100 if s['kind']=='tenant'and min(pp['court'].boundary.distance(mid)for pp in PLAZAS)<.1 else 0),edge,mid))
  if not opts:RETIRED.append(dict(floor=floor,id=s['id'],reason='必要入口幅を共用通路へ確保できない'));continue
  _,front,entry=min(opts,key=lambda a:a[0]);a,b=front.coords;u=((b[0]-a[0])/front.length,(b[1]-a[1])/front.length);n=(-u[1],u[0])
  if not p.contains(Point(entry.x+n[0]*.2,entry.y+n[1]*.2)):n=(-n[0],-n[1])
  q=lambda x,z:(entry.x+u[0]*x+n[0]*z,entry.y+u[1]*x+n[1]*z)
  depth=max((x-entry.x)*n[0]+(z-entry.y)*n[1]for x,z in p.exterior.coords);bw=3.2
  while True:
   back=p.intersection(Polygon([q(-150,depth-bw),q(150,depth-bw),q(150,depth+1),q(-150,depth+1)]));safe=back.intersection(p.buffer(-.7,join_style=2))
   if safe.area>=3 or bw>depth*.7:break
   bw+=1
  if safe.is_empty:RETIRED.append(dict(floor=floor,id=s['id'],reason='店内奥への有効経路を確保できない'));continue
  end=safe.representative_point()
  try:ip=interior_path(p,[entry.x,entry.y],[end.x,end.y])
  except RuntimeError:RETIRED.append(dict(floor=floor,id=s['id'],reason='細い内部接続を売場として採用しない'));continue
  route_line=LineString(ip);sales=p.difference(back);aisles=route_line.buffer(1.2,cap_style=2).intersection(p)
  cut=rect((entry.x,entry.y),u,w,2)
  wall=unary_union([LineString([a,b]).buffer(.125,cap_style=2)for a,b in zip(xy,xy[1:])]).difference(cut)
  partition=back.boundary.intersection(sales.boundary).buffer(.10).difference(route_line.buffer(.8))
  cross=route_line.intersection(back.boundary);bp=nearest_points(cross,entry)[0]if not cross.is_empty else end
  s.update(back_door=[bp.x,bp.y],back_door_width_m=1.6,polygon=p,entry=[entry.x,entry.y],frontage_m=front.length,depth_m=depth,u=u,n=n,front=list(front.coords),backroom=back,sales=sales,aisles=aisles,main_route=ip,wall_solids=wall.union(partition),shelf_zones=sales.buffer(-.6).difference(aisles.buffer(.2)),door_width_m=w,service_mode='D-W/D-E→共用通路（閉館後）→EV→店内主路→専用バックルーム')
  if s['kind']=='anchor'and'AW'in s['id']:
   _,se,sp=min(opts,key=lambda o:o[2].distance(Point(8,85)))
   aa,bb=se.coords;su=((bb[0]-aa[0])/se.length,(bb[1]-aa[1])/se.length)
   s['secondary_entry']=[sp.x,sp.y];s['secondary_front']=list(se.coords);s['secondary_u']=su
   s['wall_solids']=s['wall_solids'].difference(rect((sp.x,sp.y),su,6.,2.))
  sweep=substring(route_line,min(.8,route_line.length/2),route_line.length).buffer(.45)
  if sweep.difference(p).area>.025 or sweep.intersection(s['wall_solids']).area>.025:
   RETIRED.append(dict(floor=floor,id=s['id'],reason='再区画後に店内有効幅を確保できないため独立店舗として採用しない'));continue
  if sales.area<20 or s['shelf_zones'].area<8:
   RETIRED.append(dict(floor=floor,id=s['id'],reason='売場/陳列の有効面積不足。数合わせの薄い店舗にしない'));continue
  s['glazed_frontages']=[]
  for a,b in zip(xy,xy[1:]):
   edge=LineString([a,b]);mid=edge.interpolate(.5,normalized=True)
   if edge.length>=2 and public.distance(mid)<.25:
    glazing=edge.intersection(sales.buffer(.01))
    if not glazing.is_empty:s['glazed_frontages'].append(glazing)
  stores.append(s)
 # Loading doors lie in the anchors' dedicated stockroom strips; cut their real outer wall.
 if floor==1:
  for ss in stores:
   if ss['kind']!='anchor':continue
   desired=Point(-35,64)if'AW'in ss['id']else Point(530,92)
   options=[];coords=list(ss['polygon'].exterior.coords)
   for a,b in zip(coords,coords[1:]):
    edge=LineString([a,b]);mid=edge.interpolate(.5,normalized=True)
    if edge.length>=3 and ss['backroom'].buffer(.01).covers(mid)and abs(mid.x-(-35 if'AW'in ss['id']else 530))<.1:options.append((mid.distance(desired),edge,mid))
   if not options:raise RuntimeError('Loading door must enter a stockroom')
   _,edge,dp=min(options,key=lambda o:o[0]);dock=[dp.x,dp.y];a,b=edge.coords;du=((b[0]-a[0])/edge.length,(b[1]-a[1])/edge.length)
   ss['loading_door']=dict(point=dock,width=1.8,u=du)
   ss['wall_solids']=ss['wall_solids'].difference(rect(dock,du,1.8,2.))
   chk('loading_door_enters_stockroom',ss['id'],ss['backroom'].buffer(.01).covers(dp),None,1)
 f=dict(floor=floor,height=HEIGHT[floor],stores=stores,public=public,void=void,shafts=shafts,connectors=[dict(id=r['id'],route=r['points'],width=r['width'])for r in rr if r['id'].startswith(('AB','BC'))],egress=eg,route_ids=[r['id']for r in rr],furniture=[],waiting=[],route_associations={})
 FLOORS.append(f)
# Preserve each existing game catalog identity even when a v3 proposal is retired.
legacy=[]
for old in OLD['floors']:
 for s in old['stores']:
  if s.get('legacy_id'):legacy.append(dict(floor=old['floor'],id=s['legacy_id'],name=s.get('legacy_name',''),kind=s.get('legacy_kind',''),v3=s['id'],pos=s['entry']))
for f in FLOORS:
 used=set()
 for l in[l for l in legacy if l['floor']==f['floor']]:
  same=next((s for s in f['stores']if s['id']==l['v3']),None)
  if same is None:
   avail=[s for s in f['stores']if s['id']not in used and not s.get('legacy_id')]
   same=min(avail,key=lambda s:Point(s['entry']).distance(Point(l['pos'])))
  same.update(legacy_id=l['id'],legacy_name=l['name'],legacy_kind=l['kind']);used.add(same['id'])
 # Grouped rest islands stay off the retained clear route reservations. Exact positions are ledgered.
 for j,p in enumerate(PLAZAS):
  if f['floor']==1:
   candidates=[[(78,53),(109,54),(83,68),(107,69)],[(277,100),(296,101),(305,56)],[(433,91),(447,90),(421,77)]][j]
  else:
   candidates=[[(76,83),(111,37),(72,38),(123,60)],[(279,101),(289,49),(307,58),(280,100)],[(429,109),(410,89),(443,42),(471,82)]][j]
  allowed=f['public'].intersection(p['court']).buffer(-.45)
  forbidden=unary_union([p['sight_reservations']if f['floor']==1 else p['perimeter_walk'],unary_union([Point(s['entry']).buffer(2.5)for s in f['stores']]),unary_union([land.buffer(1)for e in ALL_ESC if f['floor']in e['levels']for land in e['landings']])])
  placed=0
  # Candidate design positions are preferred; boundary samples are fallback rest bays, not new corridors.
  pts=candidates+[(q.x,q.y)for q in[p['void'].buffer(10.5,join_style=2).boundary.interpolate(t,normalized=True)for t in np.linspace(0,1,41)]]
  for x,z in pts:
   bench=box(x-1.5,z-.45,x+1.5,z+.45);planter=box(x-1,z+1,x+1,z+2.2);geom=bench.union(planter)
   if not allowed.covers(geom)or forbidden.intersects(geom):continue
   if any(geom.distance(g['geom'])<4 for g in f['furniture']):continue
   idx=f"{p['id']}-{f['floor']}-{placed+1}";f['furniture']+=[dict(id=idx+'-B',plaza=p['id'],kind='bench',geom=bench,height=.85),dict(id=idx+'-P',plaza=p['id'],kind='planter',geom=planter,height=1.4)]
   waits=[Point(x+dx,z+dz)for dx,dz in[(0,-1.25),(0,1.25),(-2.2,0),(2.2,0),(-2.2,1.2),(2.2,1.2)]]
   wait=next((pt for pt in waits if allowed.covers(pt.buffer(.45))and not forbidden.intersects(pt.buffer(.45))and not geom.intersects(pt.buffer(.45))),None)
   if wait is not None:f['waiting'].append(dict(id=idx+'-WAIT',plaza=p['id'],point=[wait.x,wait.y],activity='待ち合わせ・休憩',radius=.35))
   placed+=1
   if placed==2:break
  # At least one rest bay per plaza/floor is a completion criterion, not merely a color difference.
  chk('plaza_rest_bays',p['id'],placed>=1,placed,f['floor'])
 if f['floor']==1:
  # Low sculptural marker and clock, located after the movement-band reservations.
  for id,j,pos,kind,h in[('WING-OBJECT',0,(94,54),'object',2.4),('TIME-CLOCK',1,(285,102),'clock',2.8)]:
   g=Point(pos).buffer(.8)
   if f['public'].covers(g)and not PLAZAS[j]['sight_reservations'].intersects(g):f['furniture'].append(dict(id=id,plaza=PLAZAS[j]['id'],kind=kind,geom=g,height=h))
 f['wayfinding']=[]
 for pp,key in zip(PLAZAS,['中央専門店街','北専門店街/C館','A館']):
  x,z=pp['gateways'][key];cc=pp['void'].centroid;length=math.hypot(cc.x-x,cc.y-z);normal=((cc.x-x)/length,(cc.y-z)/length);u=(-normal[1],normal[0])
  f['wayfinding'].append(dict(id=f"{pp['id']}-{floor}-SIGN",plaza=pp['id'],point=[x,z],bottom_y=HEIGHT[floor]+3.4,top_y=HEIGHT[floor]+4.2,width=2.4,u=u,kind='overhead_direction_board',mount='共用部の吊り下げ誘導案内・床に脚を置かない',text=pp['name']+' / '+ ' / '.join((name+'（他館へは2Fへ降りる）'if floor==3 and('A館'in name or'C館'in name)else name)for name in pp['gateways'])))
  chk('sign_head_clearance',pp['id'],3.4>=2.4,3.4,floor)
 obs=unary_union([g['geom']for g in f['furniture']])
 f['walkable']=snap(f['public'].difference(obs.buffer(.05)));f['reachable']=max(polys(f['walkable'].buffer(-.45)),key=lambda p:p.area)
 f['clear_public']=f['walkable'].buffer(-.45)
# Common building envelope is structural, not a collection of arbitrary public floor scraps.
used=unary_union([f['public']for f in FLOORS]+[s['polygon']for f in FLOORS for s in f['stores']]+[c['outline']for c in CORES]+[p['void']for p in PLAZAS])
BODY=snap(used.intersection(box(-40,-5,535,181)).buffer(1.25,join_style=2).buffer(5,join_style=2).buffer(-5,join_style=2).simplify(.6))
for f in FLOORS:
 f['shell']=BODY;f['residual']=BODY.difference(unary_union([f['public'],f['void'],f['shafts']]+[s['polygon']for s in f['stores']]+[c['outline']for c in CORES]))
 f['floor_plate']=BODY.union(f['public']).union(f['egress']).difference(f['void'].union(f['shafts']))
 f['guardrails']=f['void'].boundary.buffer(.05).union(f['shafts'].boundary.buffer(.05)).difference(unary_union([land for e in ALL_ESC if f['floor']in e['levels']for land in e['landings']]).buffer(.1))if f['floor']>1 else Polygon()
 # Provide specific, accessible common stores; do not turn every construction pocket into a tiny room.
 f['service_zones']=[]
 pockets=[p for p in polys(f['residual'].buffer(-1.5).buffer(1.5))if p.area>=100]
 for sector,lo,hi in[('W',-100,170),('T',170,330),('L',330,600)]:
  choices=sorted([p for p in pockets if lo<=p.centroid.x<hi],key=lambda p:p.area,reverse=True)
  for p in choices:
   doors=[];xy=list(p.exterior.coords)
   for a,b in zip(xy,xy[1:]):
    edge=LineString([a,b]);mid=edge.interpolate(.5,normalized=True)
    if edge.length>=1.8 and f['public'].distance(mid)<.05:doors.append((edge.length,edge,mid))
   if not doors:continue
   _,edge,mid=max(doors,key=lambda d:d[0]);end=p.buffer(-.7).representative_point()
   try:ip=interior_path(p,[mid.x,mid.y],[end.x,end.y])
   except RuntimeError:continue
   a,b=edge.coords;u=((b[0]-a[0])/edge.length,(b[1]-a[1])/edge.length)
   zone=dict(id=f"S-{f['floor']}-{sector}",name={'W':'西共用倉庫','T':'管理・清掃資材庫','L':'東共用倉庫'}[sector],polygon=p,entry=[mid.x,mid.y],door_width_m=1.5,u=u,main_route=ip)
   f['service_zones'].append(zone)
   chk('service_room_entry_reaches_common',zone['id'],f['reachable'].distance(mid)<.8,f['reachable'].distance(mid),f['floor'])
   chk('service_room_route_inside',zone['id'],LineString(ip).difference(p.buffer(.003)).length<.01,None,f['floor'])
   break
 for r in ROUTES:
  if f['floor']not in r['levels']:continue
  assoc=[s['id']for s in f['stores']if min(Point(pt).distance(LineString(r['points']))for pt in[s['entry']]+([s['secondary_entry']]if'secondary_entry'in s else[]))<=r['width']/2+1.0]
  f['route_associations'][r['id']]=assoc
  chk('route_has_explicit_role_and_endpoints',r['id'],bool(r['role'])and len(r['links'])==2,assoc,f['floor'])
 for i,s in enumerate(f['stores']):
  p=s['polygon'];entry=Point(s['entry']);line=LineString(s['main_route']);sweep=substring(line,min(.8,line.length/2),line.length).buffer(.45)
  if'secondary_entry'in s:
   chk('secondary_door_on_lot',s['id'],p.boundary.distance(Point(s['secondary_entry']))<.01,None,f['floor'])
   chk('secondary_door_reaches_common',s['id'],f['reachable'].distance(Point(s['secondary_entry']))<.8,None,f['floor'])
  chk('door_on_own_lot',s['id'],p.boundary.distance(entry)<.01,p.boundary.distance(entry),f['floor'])
  chk('door_reaches_clear_common',s['id'],f['reachable'].distance(entry)<.8,f['reachable'].distance(entry),f['floor'])
  chk('interior_route_within_lot',s['id'],sweep.difference(p).area<.025,sweep.difference(p).area,f['floor'])
  chk('interior_route_clear_of_walls',s['id'],sweep.intersection(s['wall_solids']).area<.025,sweep.intersection(s['wall_solids']).area,f['floor'])
  chk('interior_route_clear_of_shelves',s['id'],line.intersection(s['shelf_zones']).length<.01,None,f['floor'])
  for t in f['stores'][i+1:]:
   a=p.intersection(t['polygon']).area;chk('store_pair_no_overlap',s['id']+'/'+t['id'],a<.02,a,f['floor'])
 chk('common_clear_single_component','B',len(polys(f['clear_public']))==1,len(polys(f['clear_public'])),f['floor'])
 chk('public_excludes_atrium','B',f['walkable'].intersection(f['void']).area<.01,None,f['floor'])
 chk('public_excludes_shafts','B',f['walkable'].intersection(f['shafts']).area<.01,None,f['floor'])
 for c in CORES:chk('core_front_access',c['id'],f['reachable'].distance(Point(c['entry']))<.8,f['reachable'].distance(Point(c['entry'])),f['floor'])
 for e in ALL_ESC:
  if f['floor']not in e['levels']:continue
  for k,land in enumerate(e['landings']):chk('escalator_landing_access',e['id']+f'/{k}',f['reachable'].distance(land.centroid)<.01,f['reachable'].distance(land.centroid),f['floor'])
 for p in PLAZAS:
  for name,gateway in p['gateways'].items():chk('plaza_gateway_access',p['id']+'/'+name,f['reachable'].distance(Point(gateway))<1.0,f['reachable'].distance(Point(gateway)),f['floor'])
  destinations=[name for name in p['gateways']if not(f['floor']==3 and name=='A館')]
  chk('plaza_has_3_or_more_destinations',p['id'],len(destinations)>=3,destinations,f['floor'])
 for g in f['furniture']:chk('furniture_within_common',g['id'],f['public'].covers(g['geom']),None,f['floor'])
 # An unassigned old public fringe cannot survive: public originates solely in the named route/court program.
 program=unary_union([r['poly']for r in ROUTES if f['floor']in r['levels']]+[p['court']for p in PLAZAS]+([BRIDGE]if f['floor']>1 else[]))
 chk('no_unassigned_public_floor','B',f['public'].difference(program.buffer(.002)).area<.001,f['public'].difference(program.buffer(.002)).area,f['floor'])
for i,e in enumerate(ALL_ESC):
 for t in ALL_ESC[i+1:]:chk('escalators_do_not_overlap',e['id']+'/'+t['id'],e['shaft'].intersection(t['shaft']).area<.01)
chk('upper_void_alignment','2F/3F',FLOORS[1]['void'].equals(FLOORS[2]['void']))
# Old public pieces removed by this revision are measured, not merely relabeled.
for f,old in zip(FLOORS,OLD['floors']):
 CHANGES.append(dict(id=f"R-PUBLIC-{f['floor']}",before_area_m2=old['public'].area,after_area_m2=f['public'].area,removed_area_m2=old['public'].difference(f['public']).area,added_area_m2=f['public'].difference(old['public']).area,reason='旧walk領域を引き継がず、名前・用途・終点を持つルートと広場から共用部を再構成。'))
for r in RETIRED:CHANGES.append(dict(id='RETIRED-'+r['id'],reason=r['reason'],floor=r['floor']))
# Distance / path graph: measured at 1m sampling with exact segment checks on reconstructed paths.
class Grid:
 def __init__(self,free,step=1.):
  self.free=free;self.step=step;a,b,c,d=free.bounds;self.x0=math.floor(a);self.z0=math.floor(b);self.nx=math.ceil(c-a)+3;self.nz=math.ceil(d-b)+3
  xx,zz=np.meshgrid(np.arange(self.nx)+self.x0,np.arange(self.nz)+self.z0);self.mask=shapely.contains_xy(free,xx,zz);self.cells=list(zip(*np.where(self.mask)));self.set=set(self.cells)
  pairs=[];coords=[]
  for n in self.cells:
   for dy,dx in[(0,1),(1,0),(1,1),(1,-1)]:
    q=(n[0]+dy,n[1]+dx)
    if q not in self.set:continue
    if dx and dy and((n[0],n[1]+dx)not in self.set or(n[0]+dy,n[1])not in self.set):continue
    pairs.append((n,q));coords.append([self.pt(n),self.pt(q)])
  covered=shapely.covered_by(shapely.linestrings(np.array(coords)),free.buffer(.002))
  self.edges=set()
  for (n,q),ok in zip(pairs,covered):
   if ok:self.edges.add((n,q));self.edges.add((q,n))
 def pt(self,n):return[n[1]+self.x0,n[0]+self.z0]
 def near(self,p):return min(self.cells,key=lambda n:(n[1]+self.x0-p[0])**2+(n[0]+self.z0-p[1])**2)
 def tree(self,p):
  start=self.near(p);dist={start:0.};prev={};heap=[(0.,start)]
  while heap:
   cost,n=heapq.heappop(heap)
   if cost!=dist[n]:continue
   for dy,dx in[(0,1),(0,-1),(1,0),(-1,0),(1,1),(-1,-1),(1,-1),(-1,1)]:
    q=(n[0]+dy,n[1]+dx)
    if(n,q)not in self.edges:continue
    if dx and dy and ((n[0],n[1]+dx)not in self.set or(n[0]+dy,n[1])not in self.set):continue
    nd=cost+(1.41421356 if dx and dy else 1.)
    if nd<dist.get(q,1e30):dist[q]=nd;prev[q]=n;heapq.heappush(heap,(nd,q))
  return start,dist,prev
NAV=[]
for f in FLOORS:
 grid=Grid(f['reachable']);trees={c['id']:grid.tree(c['entry'])for c in CORES}
 for s in f['stores']:
  node=grid.near(s['entry']);targets={}
  for cid,(start,dist,prev)in trees.items():
   path=[];n=node
   if n in dist:
    path=[grid.pt(n)]
    while n!=start:n=prev[n];path.append(grid.pt(n))
   valid=bool(path)and f['reachable'].buffer(.002).covers(LineString(path))
   chk('sampled_route_to_stair',s['id']+'/'+cid,valid,dist.get(node),f['floor'])
   targets[cid]=dict(sampled_distance_m=dist.get(node),polyline=path)
  NAV.append(dict(floor=f['floor'],store=s['id'],targets=targets))
 for r in ROUTES:
  if f['floor']not in r['levels']:continue
  # Route centre endpoints may sit inside a designated escalator landing; nearest clear grid is recorded.
  for j,p in enumerate([r['points'][0],r['points'][-1]]):chk('named_route_endpoint_near_walk',r['id']+f'/{j}',f['reachable'].distance(Point(p))<1.0,f['reachable'].distance(Point(p)),f['floor'])
for c in CORES:
 fixtures=unary_union([p['geom']for p in c['fixtures']if p['kind']in['SINK','URINAL']])
 walls=c['room_wall_solids'].union(unary_union(c['cubicle_wall_solids'])).union(unary_union([s.buffer(.08)for s in c['vestibule_screens']]))
 free=c['outline'].buffer(-.125).difference(walls.union(fixtures)).buffer(-.45)
 comp=min(polys(free),key=lambda p:p.distance(Point(c['entry'])))
 for d in c['doors']:
  if d['id']=='CORE':continue
  chk('equipment_portal_reachable',c['id']+'/'+d['id'],comp.distance(Point(d['p']))<.7,comp.distance(Point(d['p'])))
 for level in[1,2,3]:
  for p in PLAZAS:
   benches=[g for g in FLOORS[level-1]['furniture']if g['plaza']==p['id']and g['kind']=='bench']
   chk('seated_rest_positions',p['id'],len(benches)>=1,2*len(benches),level)
for c,e in zip(CORES,EGRESS):
 fixtures=unary_union([p['geom']for p in c['fixtures']if p['kind']in['SINK','URINAL']])
 free=c['outline'].buffer(-.125).difference(c['ground_room_wall_solids'].union(unary_union(c['cubicle_wall_solids'])).union(fixtures)).buffer(-.45)
 comp=min(polys(free),key=lambda p:p.distance(Point(c['entry'])))
 chk('ground_stair_discharge_door',e['id'],comp.distance(Point(e['points'][0]))<.7,comp.distance(Point(e['points'][0])),1)
 chk('discharge_reaches_outside_body',e['id'],not BODY.covers(Point(e['points'][-1])),None,1)
# Exact coordinate source; old/new world transform remains rigid.
PLAZAS[2]['overhead_object']=dict(name='光のモビール',centre=[434,76],lowest_y=14.0,highest_y=15.0,floor_footprint=None)
DATA=dict(version='B purpose review v4',design_only=True,game_implemented=False,baseline_commit=BASELINE,transform=OLD['transform'],floors=FLOORS,cores=CORES,escalators=ALL_ESC,bank_medians=BANK_MEDIANS,plazas=PLAZAS,routes=ROUTES,egress=EGRESS,retired=RETIRED,changes=CHANGES,delivery=dict(west_dock=next(s['loading_door']['point']for s in FLOORS[0]['stores']if s['kind']=='anchor'and'AW'in s['id']),east_dock=next(s['loading_door']['point']for s in FLOORS[0]['stores']if s['kind']=='anchor'and'AE'in s['id']),mode='地上搬入口→核店バックルーム→店内主路→共用部（閉館後）→K1/K2/K3兼用EV→各店',cart_width_m=.8,ev_door_m=1.4))
(OUT/'geometry.json').write_text(json.dumps(DATA,default=enc,ensure_ascii=False,indent=2))
(OUT/'checks.json').write_text(json.dumps(CHECKS,ensure_ascii=False,indent=2));(OUT/'changes.json').write_text(json.dumps(CHANGES,ensure_ascii=False,indent=2));(OUT/'route-paths.json').write_text(json.dumps(NAV,default=enc,ensure_ascii=False,indent=2))
for name,headers,rows in[
 ('route-register.csv',['階','ID','名称','用途','接続先','幅m','延長m','隣接店舗数','店舗ID','理由'],[[f['floor'],r['id'],r['name'],r['role'],'→'.join(r['links']),r['width'],round(LineString(r['points']).length,1),len(f['route_associations'][r['id']]),' / '.join(f['route_associations'][r['id']]),r['reason']]for f in FLOORS for r in ROUTES if f['floor']in r['levels']]),
 ('plaza-register.csv',['ID','名称','用途','接続先','構造・景観','開口㎡','広場床㎡'],[[p['id'],p['name'],p['role'],' / '.join(p['gateways']),p['landscape'],round(p['void'].area,1),round(p['court'].area,1)]for p in PLAZAS]),
 ('tenant-ledger.csv',['階','ID','旧ゲームID','用途','区画㎡','間口m','最大奥行m','入口幅m','localX','localZ','worldX','worldY','worldZ','バックルーム㎡','搬入'],[[f['floor'],s['id'],s.get('legacy_id',''),s.get('legacy_name')or s['category'],round(s['polygon'].area,1),round(s['frontage_m'],2),round(s['depth_m'],2),s['door_width_m'],*s['entry'],world(s['entry'])[0],f['height'],world(s['entry'])[1],round(s['backroom'].area,1),s['service_mode']]for f in FLOORS for s in f['stores']]),
 ('furniture-register.csv',['階','ID','広場','種別','localX','localZ','高さm'],[[f['floor'],g['id'],g['plaza'],g['kind'],g['geom'].centroid.x,g['geom'].centroid.y,g['height']]for f in FLOORS for g in f['furniture']])]:
 with(OUT/name).open('w',encoding='utf-8-sig',newline='')as fp:w=csv.writer(fp);w.writerow(headers);w.writerows(rows)
print('COUNTS',[(f['floor'],len(f['stores']),len(f['furniture']))for f in FLOORS]);print('CHECKS',len(CHECKS),'FAILED',sum(not c['pass_']for c in CHECKS))
for c in CHECKS:
 if not c['pass_']:print(c)

if any(not c["pass_"]for c in CHECKS):sys.exit(1)
