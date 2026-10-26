"""A-wing five-level design proposal. Documentation outputs only; no Godot writes."""
from pathlib import Path
import json,sys,math,csv,copy,hashlib,ast,heapq,collections,re
sys.path.append('/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
import numpy as np
from shapely.geometry import Polygon,LineString,Point,box,shape,mapping
from shapely.ops import unary_union,nearest_points,substring
from shapely import affinity
R=Path(__file__).resolve().parents[1];O=R/'docs/a-detailed-design-v1';O.mkdir(exist_ok=True)
B=json.loads((R/'docs/b-v4-overlap-correction/geometry.json').read_text());legacy=json.loads((R/'docs/map-master-floor-plans.json').read_text())
def dec(x):
 if isinstance(x,dict):return shape(x)if'type'in x and('coordinates'in x or'geometries'in x)else{k:dec(v)for k,v in x.items()}
 if isinstance(x,list):return[dec(v)for v in x]
 return x
def enc(x):
 if hasattr(x,'geom_type'):return mapping(x)
 if isinstance(x,np.generic):return x.item()
 raise TypeError(type(x))
def polys(g):return[]if g.is_empty else[g]if g.geom_type=='Polygon'else[p for p in getattr(g,'geoms',[])if p.geom_type=='Polygon']
def rect(c,u,l,w):
 n=(-u[1],u[0]);return Polygon([(c[0]+u[0]*a+n[0]*b,c[1]+u[1]*a+n[1]*b)for a,b in[(-l/2,-w/2),(l/2,-w/2),(l/2,w/2),(-l/2,w/2)]])
def moved(obj,origin,target,angle):
 if hasattr(obj,'geom_type'):return affinity.translate(affinity.rotate(affinity.translate(obj,-origin[0],-origin[1]),angle,origin=(0,0)),*target)
 if isinstance(obj,dict):return{k:moved(v,origin,target,angle)for k,v in obj.items()}
 if isinstance(obj,list):return[moved(v,origin,target,angle)for v in obj]
 return obj
SIGNDATA=json.JSONDecoder().raw_decode((R/'scripts/store_sign_catalog.gd').read_text().split('const DATA :=',1)[1].lstrip())[0]
TENANTROWS={};section=None
for line in(R/'scripts/tenant_catalog.gd').read_text().splitlines():
 if line.startswith('const NORTH'):section='N'
 if line.startswith('const SOUTH'):section='S'
 match=re.match(r'\s+([12]):(\[.*\]),?$',line)
 if match and section:TENANTROWS[(section,int(match.group(1)))]=json.loads(match.group(2))
KINDJP={'books':'書店','clothes':'服飾','fashion':'服飾','shoes':'靴・鞄','daily':'生活用品','digital':'家電','cafe':'カフェ','home':'家具インテリア','sport':'スポーツ','grocery':'大型食品スーパー','kitchen':'キッチン用品','beauty':'化粧品','optical':'眼鏡','travel':'旅行・鞄','jewelry':'アクセサリー','stationery':'文具','kids':'子供服','toys':'玩具','hobby':'ホビー','music':'楽器','arcade':'ゲームセンター','outdoor':'アウトドア'}
def old_semantic(s,level):
 id=s['id'];kind=s['kind'];name=''
 if id=='a_market':return'grocery','LIFE MARKET / 食品スーパー'
 if id.startswith('a_extension_'):return['daily','fashion','hobby'][level],['暮らしの道具','NOVA / レディース','HOBBY BASE / 模型'][level]
 m=re.match(r'a_([0-2])_([0-9])_(-?1)$',id)
 if m:
  index=int(m.group(2));side=int(m.group(3))
  if level==0:kind=['books','clothes','shoes','daily','digital','cafe','home','daily','sport'][index];name=SIGNDATA['ground_names'][index]
  else:
   row=TENANTROWS.get(('N'if side<0 else'S',level),[])
   if index<len(row)and row[index]:name,kind=row[index]
 return kind,name or id
BASECORE=dec(B['cores'][0]);CORES=[]
for id,centre,angle in [('A-KW',(-95,74),-90),('A-KE',(168,75),90),('A-KS',(50,212),180)]:
 c=moved(BASECORE,BASECORE['centre'],centre,angle)
 def pt(p):q=affinity.rotate(Point(p[0]-174,p[1]-25),angle,origin=(0,0));return[q.x+centre[0],q.y+centre[1]]
 for k in['doors','cubicle_doors']:
  for d,old in zip(c[k],BASECORE[k]):
   d['p']=pt(old['p']);a=math.radians(angle);u=old['axis'];d['axis']=[u[0]*math.cos(a)-u[1]*math.sin(a),u[0]*math.sin(a)+u[1]*math.cos(a)]
 c.update(id=id,centre=list(centre),entry=pt(BASECORE['entry']),angle=angle,ground_discharge_door=None);CORES.append(c)
coreout=unary_union([c['outline']for c in CORES])
voids=[affinity.scale(Point(-90,14).buffer(1,quad_segs=24),17,12),Polygon([(128,6),(137,-2),(159,0),(169,14),(159,29),(135,29),(125,18)]).buffer(-2).buffer(2),box(35,167,65,190).buffer(-4).buffer(4)]
PLAZAS=[]
for id,name,void,court,gates,desc in[
 ('A-PW','風のゲート',voids[0],box(-122,-19,-54,46),{'B館':[-130,-5.5],'北街':[-54,4],'西街':[-80,43]},'西の核店前庭。横長開口と北南の昇降機。'),
 ('A-PE','空のテラス',voids[1],Polygon([(115,-17),(173,-17),(190,8),(182,45),(140,59),(111,33)]),{'北街':[115,6],'東街':[143,52],'東核店':[184,12]},'斜めの店頭と面を振った回廊、屋外テラスに向かう端部。'),
 ('A-PS','光のコート',voids[2],Polygon([(19,156),(47,144),(87,164),(89,191),(62,207),(24,199)]),{'東街':[88,160],'西街':[23,159],'南核店':[50,207]},'広がった南端で飲食街と休憩を受ける。南北で異なる店頭。')]:PLAZAS.append(dict(id=id,name=name,void=void,court=court,gateways=gates,landscape=desc,cameras=[]))
ESC=[]
for j,(ca,cb,u)in enumerate([((-86,-9),(-86,38),(1,0)),((145,-12),(145,45),(1,0)),((24,177),(79,177),(0,1))]):
 for lo in[-1,0,1,2]:
  centre=ca if lo in[-1,1]else cb;n=(-u[1],u[0])
  for lane,direction in[(-2,'UP'),(2,'DOWN')]:
   c=[centre[0]+n[0]*lane,centre[1]+n[1]*lane];lands=[rect((c[0]+u[0]*sign*8.9,c[1]+u[1]*sign*8.9),u,3.,3.6)for sign in[-1,1]]
   ESC.append(dict(id=f'A-E{j+1}-{lo}-{direction}',plaza=PLAZAS[j]['id'],levels=[lo,lo+1],direction=direction,c=c,u=u,shaft=rect(c,u,14.8,2.4),landings=lands,run_m=11.8,width_m=2.4,comb_m=1.5,step_clear_m=1.))
 for p in[PLAZAS[j]]:p['court']=p['court'].union(unary_union([q for e in ESC if e['plaza']==p['id']for q in[e['shaft'],*e['landings']]]).buffer(2,join_style=2))
ROUTES=[]
def route(id,name,pts,w,role,links,levels=[-1,0,1,2,3]):ROUTES.append(dict(id=id,name=name,points=pts,width=w,role=role,links=links,levels=levels,poly=LineString(pts).buffer(w/2,cap_style=2,join_style=2)))
route('A-N','ノース・ファッション街',[(-90,10),(-20,-2),(65,-1),(145,15)],16,'北側専門店街・風/空の広場接続',['A-PW','A-PE'])
route('A-E','イースト・ライフ街',[(145,15),(140,75),(105,135),(50,180)],15,'東側専門店街・空/光の広場接続',['A-PE','A-PS'])
route('A-W','ウエスト・カルチャー街',[(50,180),(-15,135),(-68,78),(-90,10)],15,'西側専門店街・光/風の広場接続',['A-PS','A-PW'])
route('A-CENTRE','中央核店アプローチ',[(30,-1),(25,55),(50,125),(50,156)],12,'中央大型店群の店頭・三角回遊の短絡',['A-N','A-PS'],[-1,0,1,2])
for c,pts in zip(CORES,[[(-68,78),(-85,74)],[(140,75),(158,75)],[(50,190),(50,202)]]):route(c['id']+'-A',c['id']+' 共用設備前',pts,8,'トイレ・階段・EVアクセス',['専門店街',c['id']])
route('A-B1','B館1階接続',[(-174,-5.5),(-130,-5.5),(-110,5)],5,'B館固定口から風のゲートへ',['B-AB1','A-PW'],[0])
route('A-PARK','西駐車場歩行者ゲート',[(-153,-5.5),(-153,-20)],3,'駐車場の保護歩道から西到着ロビーへ',['西駐車場','A-B1'],[0])
route('A-B2','B館2階接続',[(-110,-5.5),(-103,2)],5,'B館固定口から風のゲートへ',['B-AB2','A-PW'],[1])
HEIGHT={-1:-5.35,0:0.,1:5.525,2:10.875,3:16.4};LABEL={-1:'B1',0:'1F',1:'2F',2:'3F',3:'RF'}
ENVELOPE=Polygon([(-140,-44),(-82,-60),(165,-50),(214,-1),(201,74),(98,223),(48,235),(-6,206),(-144,51)])
# Pure visibility path helper. Never execute the source generator.
src=(R/'tools/design_b_v4.py').read_text()
for node in ast.parse(src).body:
 if isinstance(node,ast.FunctionDef)and node.name=='interior_path':exec(compile(ast.get_source_segment(src,node),'pure_interior_path','exec'),globals())
CHECKS=[]
def ck(k,id,ok,val=None,level=None):CHECKS.append(dict(kind=k,id=id,pass_=bool(ok),value=val,level=level))
FLOORS=[]
for level in[-1,0,1,2,3]:
 routes=[r for r in ROUTES if level in r['levels']];rawpub=unary_union([r['poly']for r in routes]+[p['court']for p in PLAZAS])
 bpublic=affinity.translate(shape(B['floors'][level]['public']),-714,-30)if level in[0,1]else Polygon()
 if level==1:rawpub=rawpub.union(bpublic.intersection(ENVELOPE))
 void=unary_union(voids)if level in[1,2,3]else Polygon();es=[e for e in ESC if level in e['levels']];shafts=unary_union([e['shaft']for e in es]);public=rawpub.difference(unary_union([void,shafts,coreout]).buffer(.16));stores=[]
 # Central anchor has a real 8m access branch; it is not an unused island inside the circulation loop.
 central=Polygon([(-90,10),(145,15),(50,180)]).buffer(-12,join_style=2)
 centreline=next(r['poly']for r in ROUTES if r['id']=='A-CENTRE');centralparts=sorted(polys(central.difference(centreline)),key=lambda q:q.centroid.x)
 centralcats={-1:['食品市場','生活・ホームセンター'],0:['大型食品スーパー','生活・家電大型店'],1:['大型ファッション','家具インテリア'],2:['映画館','屋内遊園地・娯楽'],3:['屋上カフェ','庭園']}
 candidate=[('CENTRAL-'+str(i),lot,[25,60],centralcats[level][0 if i==0 else 1])for i,lot in enumerate(centralparts)]
 if level==3:candidate=[]
 # Programmed nonuniform frontage/depth pattern along all three streets. Route bends split shop rows.
 widths=[16,22,13,28,18,17,25,14];depths=[22,30,24,27,19]
 for ri,rr in enumerate(ROUTES[:3]):
  pts=rr['points']
  for segi,(a,b)in enumerate(zip(pts,pts[1:])):
   length=math.dist(a,b);u=((b[0]-a[0])/length,(b[1]-a[1])/length);n=(-u[1],u[0]);t=3.;si=0
   while t<length-12:
    front=min(widths[(si+ri+segi+level)%len(widths)],length-t-1.);dep=depths[(si+segi+ri)%len(depths)];offset=rr['width']/2
    for side in[-1,1]:
     if level==3 and (si+segi+ri+side)%3:continue
     if level==-1 and (si+ri+segi)%2:continue
     def q(k,d):return(a[0]+u[0]*k+n[0]*d*side,a[1]+u[1]*k+n[1]*d*side)
     lot=Polygon([q(t,offset),q(t+front,offset),q(t+front,offset+dep),q(t,offset+dep)])
     cat=['服飾','靴・鞄','雑貨','書店','カフェ','化粧品','スポーツ','家電','生活用品'][(si+ri*3+segi+level*2)%9]
     if level==-1:cat=['食品専門店','生活用品','医薬品','地下サービス'][si%4]
     if level==3:cat=['屋上カフェ','ガーデンショップ','軽食テラス'][si%3]
     candidate.append((f'{rr["id"]}-{segi}-{si}-{side}',lot,list(q(t+front/2,offset)),cat))
    t+=front+.8;si+=1
 # External corner anchors turn towards the court rather than offering their back walls.
 if level!=3:
  for id,lot,entry,cat in [('WEST',box(-138,-40,-85,-19),[-100,-19],'書籍・生活大型店'),('EAST',box(182,-12,212,45),[182,12],'家電大型店'if level==0 else'スポーツ大型店'),('SOUTH',box(12,205,93,231),[50,205],'フードホール'if level in[0,2]else'レストラン・体験店')]:candidate.append((id,lot,entry,cat))
 for hint,lot,desired,category in candidate:
  avoid=unary_union([public,void,shafts,coreout]+[s['polygon']for s in stores]);parts=polys(lot.intersection(ENVELOPE).difference(avoid));parts=[q for q in parts if q.area>55]
  if not parts:continue
  p=max(parts,key=lambda q:q.area);opts=[]
  for a,b in zip(p.exterior.coords,list(p.exterior.coords)[1:]):
   edge=LineString([a,b]);interface=edge.intersection(public.buffer(.025))
   for seg in([interface]if interface.geom_type=='LineString'else getattr(interface,'geoms',[])):
    if seg.geom_type=='LineString'and seg.length>2.8:opts.append((seg.interpolate(.5,normalized=True).distance(Point(desired)),seg))
  if not opts:continue
  edge=min(opts,key=lambda q:q[0])[1];entry=edge.interpolate(.5,normalized=True);a,b=edge.coords[0],edge.coords[-1];u=((b[0]-a[0])/edge.length,(b[1]-a[1])/edge.length);n=(-u[1],u[0])
  if not p.covers(Point(entry.x+n[0]*.1,entry.y+n[1]*.1)):n=(-n[0],-n[1])
  depth=max((x-entry.x)*n[0]+(z-entry.y)*n[1]for x,z in p.exterior.coords)
  def q(a,b):return(entry.x+u[0]*a+n[0]*b,entry.y+u[1]*a+n[1]*b)
  back=p.intersection(Polygon([q(-500,max(3,depth-4)),q(500,max(3,depth-4)),q(500,depth+1),q(-500,depth+1)]));safe=back.buffer(-.5)
  if safe.is_empty:continue
  end=safe.representative_point()
  try:ip=interior_path(p,[entry.x,entry.y],[end.x,end.y])
  except RuntimeError:continue
  routegeom=LineString(ip);w=6. if hint.startswith('CENTRAL')or hint in['WEST','EAST','SOUTH']else 2.4
  if edge.length<w+.2:w=2.4
  wall=p.boundary.buffer(.125,join_style=2).difference(rect((entry.x,entry.y),u,w,1.5));sales=p.difference(back);partition=back.boundary.intersection(sales.boundary).buffer(.1).difference(routegeom.buffer(.8));wall=wall.union(partition)
  sweep=substring(routegeom,min(.8,routegeom.length/2),routegeom.length).buffer(.45)
  if sweep.difference(p).area>.025 or sweep.intersection(wall).area>.025:continue
  shelves=sales.buffer(-.6).difference(routegeom.buffer(1.4));aisles=routegeom.buffer(1.2).intersection(p)
  if shelves.area<8:continue
  stores.append(dict(id=f'A{LABEL[level]}-{len(stores)+1:03}',category=category,kind='anchor'if w==6 else'tenant',polygon=p,entry=[entry.x,entry.y],door_width_m=w,u=u,n=n,front=list(edge.coords),frontage_m=edge.length,depth_m=depth,backroom=back,sales=sales,shelf_zones=shelves,aisles=aisles,main_route=ip,wall_solids=wall,legacy_ids=[],delivery='地上搬入口→兼用貨客EV→閉館後共用通路→店内主路→専用バックルーム',hint=hint))
 # Large central anchors have a second real entry along the southern commercial street.
 for st in stores:
  if not st['hint'].startswith('CENTRAL'):continue
  options=[]
  for a,b in zip(st['polygon'].exterior.coords,list(st['polygon'].exterior.coords)[1:]):
   full=LineString([a,b]);edge=full.intersection(public.buffer(.025))
   for seg in([edge]if edge.geom_type=='LineString'else getattr(edge,'geoms',[])):
    if seg.geom_type=='LineString'and seg.length>=4.4:
     pt=seg.interpolate(.5,normalized=True)
     if pt.distance(Point(st['entry']))>25:options.append((pt.distance(Point(50,127)),seg,pt))
  if not options:continue
  _,edge,entry=min(options,key=lambda v:v[0]);a,b=edge.coords[0],edge.coords[-1];u=((b[0]-a[0])/edge.length,(b[1]-a[1])/edge.length)
  ip=interior_path(st['polygon'],[entry.x,entry.y],st['main_route'][-1]);line=LineString(ip);cuts=rect(st['entry'],st['u'],st['door_width_m'],1.5).union(rect((entry.x,entry.y),u,4.,1.5));outer=st['polygon'].boundary.buffer(.125,join_style=2).difference(cuts);partition=st['backroom'].boundary.intersection(st['sales'].boundary).buffer(.1).difference(LineString(st['main_route']).buffer(.8)).difference(line.buffer(.8));st['wall_solids']=outer.union(partition)
  st.update(secondary_entry=[entry.x,entry.y],secondary_front=list(edge.coords),secondary_u=u,secondary_door_width_m=4.,secondary_main_route=ip);st['aisles']=st['aisles'].union(line.buffer(1.2).intersection(st['polygon']));st['shelf_zones']=st['shelf_zones'].difference(line.buffer(1.4))
 for st in stores:
  st['glazed_frontages']=[]
  for a,b in zip(st['polygon'].exterior.coords,list(st['polygon'].exterior.coords)[1:]):
   edge=LineString([a,b]);gl=edge.intersection(public.buffer(.03)).intersection(st['sales'].buffer(.001))
   if gl.length>1:st['glazed_frontages'].append(gl)
 # Every old catalog ID survives as an explicit alias; comparison is centroid vs new entrance, not a false same-point transform.
 oldstores=[s for f in legacy if f['building']=='A'and f['level']==level for s in f['shops']];used=set()
 for s in sorted(oldstores,key=lambda q:0 if q['id']=='a_market'else 1):
  prev=Polygon(s['polygon']).centroid;oldkind,oldname=old_semantic(s,level);kindjp=KINDJP.get(oldkind,oldkind)
  choices=[q for q in stores if q['id']not in used and q['kind']!='anchor']
  if s['id']=='a_market':choices=[q for q in stores if q['hint']=='CENTRAL-0']
  elif s['id']=='a_0_0_-1':choices=[q for q in stores if q['hint']=='WEST']
  elif any(q['category']==kindjp for q in choices):choices=[q for q in choices if q['category']==kindjp]
  if not choices:choices=[q for q in stores if q['id']not in used]
  to=min(choices,key=lambda q:Point(q['entry']).distance(prev));to['legacy_ids'].append(s['id']);to['legacy_kind']=oldkind;to['legacy_name']=oldname;to['category']=kindjp;used.add(to['id'])
 # Rest islands stay off door / landing / circulation reserves.
 furniture=[]
 for j,p in enumerate(PLAZAS):
  paths=unary_union([LineString([a,b]).buffer(2.5)for i,a in enumerate(p['gateways'].values())for b in list(p['gateways'].values())[i+1:]])
  forbidden=unary_union([paths,unary_union([land.buffer(.5)for e in es for land in e['landings']]),unary_union([Point(s['entry']).buffer(2.5)for s in stores])])
  for t in np.linspace(0,1,80):
   pt=p['court'].buffer(-2).boundary.interpolate(t,normalized=True);bench=box(pt.x-1.4,pt.y-.45,pt.x+1.4,pt.y+.45);planter=box(pt.x-1,pt.y+1.2,pt.x+1,pt.y+2.3);geo=bench.union(planter)
   if public.buffer(-.4).covers(geo)and not forbidden.intersects(geo)and not any(geo.distance(x['geom'])<3 for x in furniture):
    furniture.extend([dict(id=f'{p["id"]}-{level}-B{len(furniture)}',plaza=p['id'],kind='bench',geom=bench,height=.9),dict(id=f'{p["id"]}-{level}-P{len(furniture)}',plaza=p['id'],kind='planter',geom=planter,height=1.4)]);break
 if level==0:
  ps=PLAZAS[2];movement=unary_union([LineString([a,b]).buffer(2.0)for i,a in enumerate(ps['gateways'].values())for b in list(ps['gateways'].values())[i+1:]]);busy=unary_union([q['geom'].buffer(1)for q in furniture]+[land.buffer(.5)for e in es for land in e['landings']])
  for i,(x,z)in enumerate([(39,173),(41,179),(43,185),(59,173),(61,179),(63,185),(35,189),(66,190)]):
   footprint=Point(x,z).buffer(1.25)
   if public.buffer(-.4).covers(footprint)and not movement.intersects(footprint)and not busy.intersects(footprint):
    furniture.append(dict(id=f'A-FOOD-TABLE-{i}',plaza='A-PS',kind='table',geom=footprint,height=.75,seats=4));busy=busy.union(footprint.buffer(.6))
 # Fill remaining non-commercial surface with specified structure, plant/storage zones; no public maze.
 used=unary_union([public,coreout,void]+[s['polygon']for s in stores]);compact=used.buffer(1.2,join_style=2).buffer(3,join_style=2).buffer(-3,join_style=2);shell=Polygon(max(polys(compact),key=lambda p:p.area).exterior).intersection(ENVELOPE.union(public).union(coreout))
 if level==3:shell=FLOORS[-1]['shell']
 shell=shell.union(public).union(coreout).union(unary_union([s['polygon']for s in stores]))
 slab=shell.difference(void.union(shafts));private=unary_union([s['polygon']for s in stores]);residual=shell.difference(unary_union([public,void,shafts,private,coreout]));program=[]
 if level==-1:
  park=Polygon([(1,35),(87,38),(48,122),(-18,82)]).difference(public.union(private).union(coreout));
  if park.area>100:program.append(dict(id='A-B1-PARK',name='地下荷捌き区画',polygon=park,access=[30,28],public=False,mode='車両路は探索用共用床と分離、歩行者は南北の店舗前とEVへ'))
 if level==3:
  roofgreen=residual.buffer(-1).buffer(1).intersection(shell);public=public.union(roofgreen).difference(void.union(shafts).union(coreout).union(private).union(shell.boundary.buffer(.12)));residual=shell.difference(public.union(void).union(shafts).union(coreout).union(private));program.append(dict(id='A-RF-GARDEN',name='屋上庭園・散策芝生',polygon=roofgreen,public=True,mode='外周に連続パラペット、天窓・設備核を非歩行域として分離'))
 # Nonpublic remaining components are actual structure/management blocks with declared maintenance use and service entry.
 for j,p in enumerate(sorted(polys(residual),key=lambda p:p.area,reverse=True)):
  if p.area<12:continue
  interface=p.boundary.intersection(public.buffer(.03));entry=interface.representative_point()if not interface.is_empty else p.representative_point();name=('設備機械・防災管理'if j%3==0 else'搬入待機・共用商品庫'if j%3==1 else'清掃・保守作業室')
  program.append(dict(id=f'A-{LABEL[level]}-S{j+1}',name=name,polygon=p,entry=[entry.x,entry.y],public=False,door_width_m=1.5,mode='施錠スタッフ扉。機器割付と防火区画は実施設計未検証'))
 walkable=public.difference(unary_union([q['geom']for q in furniture]).buffer(.05));reachable=polys(walkable.buffer(-.45));main=max(reachable,key=lambda p:p.area)
 f=dict(level=level,label=LABEL[level],height=HEIGHT[level],shell=shell,public=public,walkable=walkable,floor_plate=slab,void=void,shafts=shafts,residual=residual,stores=stores,cores=CORES,escalators=es,furniture=furniture,program=program,guardrails=void.boundary.buffer(.05),routes=[r['id']for r in routes],reachable=main,roof_edge_parapet=shell.boundary.buffer(.12).intersection(shell)if level==3 else Polygon(),roof_edge_parapet_height_m=1.2 if level==3 else 0)
 f['fixed_B_public_in_site']=bpublic.intersection(shell);f['facade_wall_solids']=shell.boundary.buffer(.125).intersection(shell).difference(bpublic.buffer(.02))
 if level==0:f['facade_wall_solids']=f['facade_wall_solids'].difference(box(-155,-21,-151,-19))
 FLOORS.append(f)
 for kind,geom in [('closed',residual),('core',coreout),('facade',f['facade_wall_solids']),('stores',private),('store_walls',unary_union([s['wall_solids']for s in stores]))]:ck('fixed_B_corridor_no_conflict',kind,bpublic.intersection(geom).area<1e-8,bpublic.intersection(geom).area,level)
 ck('common_single_component',LABEL[level],len(reachable)==1,len(reachable),level)
 ck('public_excludes_openings',LABEL[level],public.intersection(void.union(shafts)).area<1e-8,public.intersection(void.union(shafts)).area,level)
 ck('closed_excludes_public',LABEL[level],residual.intersection(public).area<1e-8,residual.intersection(public).area,level)
 ck('slab_excludes_openings',LABEL[level],slab.intersection(void.union(shafts)).area<1e-8,slab.intersection(void.union(shafts)).area,level)
 ck('slab_covers_public',LABEL[level],public.difference(slab).area<1e-8,public.difference(slab).area,level)
 for i,s in enumerate(stores):
  if'secondary_entry'in s:
   line=LineString(s['secondary_main_route']);sweep2=substring(line,min(.8,line.length/2),line.length).buffer(.45);ck('secondary_entry_reachable',s['id'],main.distance(Point(s['secondary_entry']))<.8,main.distance(Point(s['secondary_entry'])),level);ck('secondary_interior_route_lot',s['id'],sweep2.difference(s['polygon']).area<.025,sweep2.difference(s['polygon']).area,level);ck('secondary_interior_route_walls',s['id'],sweep2.intersection(s['wall_solids']).area<.025,sweep2.intersection(s['wall_solids']).area,level)
  ck('store_entry_on_lot',s['id'],s['polygon'].boundary.distance(Point(s['entry']))<.01,None,level);ck('store_entry_reachable',s['id'],main.distance(Point(s['entry']))<.8,main.distance(Point(s['entry'])),level)
  ck('store_public_no_overlap',s['id'],s['polygon'].intersection(public).area<1e-8,s['polygon'].intersection(public).area,level)
  sweep=substring(LineString(s['main_route']),min(.8,LineString(s['main_route']).length/2),LineString(s['main_route']).length).buffer(.45)
  ck('interior_route_lot',s['id'],sweep.difference(s['polygon']).area<.025,None,level);ck('interior_route_walls',s['id'],sweep.intersection(s['wall_solids']).area<.025,None,level)
  for t in stores[i+1:]:ck('store_pair_no_overlap',s['id']+'/'+t['id'],s['polygon'].intersection(t['polygon']).area<1e-8,None,level)
 for c in CORES:ck('core_entry_reachable',c['id'],main.distance(Point(c['entry']))<.8,main.distance(Point(c['entry'])),level)
 for e in es:
  for i,land in enumerate(e['landings']):ck('escalator_landing_reachable',e['id']+f'/{i}',main.distance(land.centroid)<.01,main.distance(land.centroid),level)
ck('upper_void_alignment','2F/3F',FLOORS[2]['void'].equals(FLOORS[3]['void']))
for level,pt in[(0,(-174,-5.5)),(1,(-110,-5.5))]:ck('fixed_B_port',str(level),FLOORS[level+1]['public'].buffer(.001).covers(Point(pt)),None,level)
D=dict(wing='A',version='A detailed design v1',coordinate_system='World XZ metres',design_only=True,game_implemented=False,floors=FLOORS,cores=CORES,escalators=ESC,plazas=PLAZAS,routes=ROUTES,heights=HEIGHT,game_design_dimensions=True,reference='AEON_LAKETOWN_OFFICIAL_FLOOR_GUIDE_202610.pdf pp1-3: three distinct court/nuclear stores/layered retail and entertainment. Triangle geometry, dimensions, basement and RF are original game design.')
# Verify the reused and rigidly positioned sanitary cores against their actual internal geometry.
for c in CORES:
 fixtures=unary_union([q['geom']for q in c['fixtures']if q['kind']in['SINK','URINAL']]);wall=c['room_wall_solids'].union(unary_union(c['cubicle_wall_solids'])).union(unary_union([q.buffer(.08)for q in c['vestibule_screens']]))
 free=c['outline'].buffer(-.125).difference(wall.union(fixtures)).buffer(-.45);comp=min(polys(free),key=lambda p:p.distance(Point(c['entry'])))
 for d in c['doors']:
  if d['id']!='CORE':ck('internal_core_portal',c['id']+'/'+d['id'],comp.distance(Point(d['p']))<.7,comp.distance(Point(d['p'])))
for f in FLOORS:
 for program in f['program']:
  if program.get('public',False)or'entry'not in program:continue
  pt=Point(program['entry'])
  try:program['main_route']=interior_path(program['polygon'],program['entry'],list(program['polygon'].buffer(-.7).representative_point().coords)[0])
  except Exception:program['main_route']=[];program['internal_service_access_unverified']=True
  if program.get('internal_service_access_unverified'):
   program['name']='外壁・配管保守帯（非室）';program['staff_occupiable']=False;program['inspection_point']=program.pop('entry');program['door_width_m']=0.;program['mode']='通行できる部屋として採用しない。共用側からの点検パネルで保守。';program.pop('internal_service_access_unverified');kind='inspection_panel_near_public'
  else:program['staff_occupiable']=True;kind='staff_door_near_public'
  ck(kind,program['id'],f['public'].distance(pt)<.05,f['public'].distance(pt),f['level'])
  items=[];p=program['polygon'];a,b,c,d=p.bounds;path=LineString(program['main_route']).buffer(1.)if program['main_route']else Polygon()
  for z in np.arange(b+2,d-2,7):
   for x in np.arange(a+2,c-2,7):
    q=box(x-1.5,z-1,x+1.5,z+1)
    if p.buffer(-.5).covers(q)and not path.intersects(q):items.append(dict(kind='空調機/貯蔵ラック'if'設備'in program['name']else'商品保管ラック',geom=q))
    if len(items)>=12:break
   if len(items)>=12:break
  program['fixtures']=items
ADDITIONAL=json.loads((R/'docs/ac-detailed-design-v1/legacy-additional-a-ids.json').read_text())
role_links=[]
for old in ADDITIONAL:
 if old['id']in['a_market_rear','a_reading']:
  parent='a_market'if old['id']=='a_market_rear'else'a_0_0_-1';target=next(s for f in FLOORS for s in f['stores']if parent in s['legacy_ids'])
  if old['id']=='a_reading':
   free=target['sales'].difference(target['aisles'].buffer(.8)).buffer(-1.6);point=free.representative_point();bay=box(point.x-1.5,point.y-1.2,point.x+1.5,point.y+1.2);target['shelf_zones']=target['shelf_zones'].difference(bay.buffer(.25));target['reading_lounge']=dict(geom=bay,seats=4,public=True,mode='売場内・主路外の読書コーナー。バックルームに置かない。');np=[point.x,point.y]
  else:point=target['sales'].representative_point();np=[point.x,point.y]
  role_links.append(dict(old_id=old['id'],role='売場後方補助サイン（取付面未設計）'if old['id']=='a_market_rear'else'店内読書コーナー',new_store=target['id'],new_point=np));continue
 f=next(f for f in FLOORS if f['level']==old['level']);options=[q for q in f['stores']if not q['legacy_ids']and q['kind']!='anchor']
 if not options:options=f['stores']
 reference=Point(50,180)if old['id'].startswith('a_food_')else Point(old['old_world_xyz_source_derived'][0],old['old_world_xyz_source_derived'][2]);target=min(options,key=lambda q:Point(q['entry']).distance(reference));target['legacy_ids'].append(old['id']);target['category']='食品専門店'if old['level']==-1 else'フードコート独立売場';target['legacy_type']='counter';target['legacy_name']=next((q['brand']for q in SIGNDATA['additional_boards']if q.get('id')==old['id']),old['id'])
VERTICAL=[]
for c in CORES:
 c['levels']=[-1,0,1,2,3];c['floor_portals']=[dict(level=k,height=HEIGHT[k],entry=[c['entry'][0],HEIGHT[k],c['entry'][1]],elevator=next(d['p']for d in c['doors']if d['id']=='EV'))for k in[-1,0,1,2,3]]
 for lo in[-1,0,1,2]:VERTICAL.append(dict(id=c['id']+f'-{lo}',core=c['id'],from_level=lo,to_level=lo+1,type='stairs-and-elevator',entry_xz=c['entry'],lower_y=HEIGHT[lo],upper_y=HEIGHT[lo+1],rise_m=HEIGHT[lo+1]-HEIGHT[lo],stair_risers=32,stair_tread_m=.30,flight_width_m=2.,landing_depth_m=1.8,elevator_door_m=1.4))
D['vertical_links']=VERTICAL;D['role_links']=role_links
market=next(s for f in FLOORS for s in f['stores']if'a_market'in s['legacy_ids']);ck('legacy_market_function','a_market',market['category']=='大型食品スーパー'and market['polygon'].area>3000,market['polygon'].area,0)
ck('legacy_commercial_ids_retained','all',sum(len(s['legacy_ids'])for f in FLOORS for s in f['stores'])==51)
D['food_court']=dict(level=0,plaza='A-PS',counter_stores=[s['id']for f in FLOORS for s in f['stores']if any(id.startswith('a_food_')for id in s['legacy_ids'])],shared_tables=[q['id']for q in FLOORS[1]['furniture']if q['kind']=='table'],seats=sum(q.get('seats',0)for q in FLOORS[1]['furniture']))

D['outdoor_site']=[dict(id='A-WEST-PARK',name='西駐車場・歩行者到着',level=0,polygon=box(-174,-55,-140,-20),public=False,parking_stalls=[dict(id=f'AP-{row}-{i}',geom=box(-171+i*2.5,-52+row*21,-168.5+i*2.5,-47+row*21),width_m=2.5,depth_m=5.)for row in[0,1]for i in range(11)],vehicle_aisle=box(-173,-45,-141,-33),protected_pedestrian=box(-173,-23,-141,-20),gate=[-153,-20],mode='屋外地上駐車。22台・車両動線と歩行者ゲートを分ける。旧a.parking訪問キーの移行先候補。')]
D['travel_hubs']=[dict(legacy_key='a.parking',level=0,point=[-153,-16],name='西駐車場歩行者ゲート')]

(O/'geometry.json').write_text(json.dumps(D,default=enc,ensure_ascii=False,indent=2));(O/'checks.json').write_text(json.dumps(CHECKS,default=enc,ensure_ascii=False,indent=2))
with(O/'tenant-ledger.csv').open('w',encoding='utf-8-sig',newline='')as fp:
 w=csv.writer(fp);w.writerow(['階','新ID','旧ID別名','用途','区画㎡','間口m','奥行m','入口幅m','WorldX','WorldY','WorldZ','裏室㎡','搬入'])
 for f in FLOORS:
  for s in f['stores']:w.writerow([f['label'],s['id'],' / '.join(s['legacy_ids']),s['category'],s['polygon'].area,s['frontage_m'],s['depth_m'],s['door_width_m'],s['entry'][0],f['height'],s['entry'][1],s['backroom'].area,s['delivery']])
with(O/'legacy-id-coordinate-map.csv').open('w',encoding='utf-8-sig',newline='')as fp:
 w=csv.writer(fp);w.writerow(['階','旧ID','旧参照点','旧WorldX','旧WorldY','旧WorldZ','新ID','新参照点','新WorldX','新WorldY','新WorldZ','変換方式','旧用途','新用途','旧店名','継承店名'])
 for old in legacy:
  if old['building']!='A':continue
  f=next(f for f in FLOORS if f['level']==old['level'])
  for os in old['shops']:
   c=Polygon(os['polygon']).centroid;ns=next(s for s in f['stores']if os['id']in s['legacy_ids']);w.writerow([f['label'],os['id'],'旧区画重心',c.x,f['height'],c.y,ns['id'],'新店舗入口',ns['entry'][0],f['height'],ns['entry'][1],'用途優先で旧ブランド機能を継承。剛体変換ではない',old_semantic(os,f['level'])[0],ns['category'],old_semantic(os,f['level'])[1],ns.get('legacy_name','')])
with(O/'legacy-id-coordinate-map.csv').open('a',encoding='utf-8-sig',newline='')as fp:
 w=csv.writer(fp)
 for old in ADDITIONAL:
  point=old['old_world_xyz_source_derived'];f=next(f for f in FLOORS if f['level']==old['level'])
  if old['id']in['a_market_rear','a_reading']:
   role=next(q for q in role_links if q['old_id']==old['id']);newid=role['new_store'];np=role['new_point'];kind=role['role']
  else:
   ns=next(q for q in f['stores']if old['id']in q['legacy_ids']);newid=ns['id'];np=ns['entry'];kind='新店舗入口'
  w.writerow([f['label'],old['id'],old['basis']+' / source-derived World (not runtime)',point[0],point[1],point[2],newid,kind,np[0],f['height'],np[1],'機能再配置。旧Worldは静的ソース計算、実入口実測ではない',old['kind'],next(q['category']for q in f['stores']if q['id']==newid),next((q['brand']for q in SIGNDATA['additional_boards']if q.get('id')==old['id']),old['id']),next(q.get('legacy_name',old['id'])for q in f['stores']if q['id']==newid)])
(O/'summary.json').write_text(json.dumps(dict(floors=[dict(level=f['level'],label=f['label'],stores=len(f['stores']),shell_area_m2=f['shell'].area,public_area_m2=f['public'].area)for f in FLOORS],checks=len(CHECKS),failed=[c for c in CHECKS if not c['pass_']],legacy_ids=51,auxiliary_role_links=2,runtime_walking_tests=0),default=enc,ensure_ascii=False,indent=2))
print('COUNTS',[(f['label'],len(f['stores']))for f in FLOORS],'CHECKS',len(CHECKS),'FAILED',len([c for c in CHECKS if not c['pass_']]))
for c in CHECKS:
 if not c['pass_']:print(c)
