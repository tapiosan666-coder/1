"""Design-only B-wing coordination. Never imports or writes Godot game resources."""
from pathlib import Path
import sys, json, math, csv, hashlib, heapq, zipfile
sys.path.append('/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
import fitz
from shapely.geometry import Polygon, LineString, Point, box, mapping, shape
from shapely.ops import unary_union, nearest_points, substring
from shapely import affinity, make_valid, voronoi_polygons, set_precision
from shapely.geometry import MultiPoint
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/b-detailed-review-v3'; IN=OUT/'input'; OUT.mkdir(exist_ok=True)
SOURCE=json.loads((IN/'B_completed_plan_geometry.json').read_text())
HEIGHT={1:0.,2:5.525,3:10.875}
FONT=ROOT/'assets/fonts/NotoSansCJKjp-Regular.otf'
AUDIT=[]; CHECKS=[]
def check(kind,id,ok,value=None,floor=None):
 CHECKS.append(dict(kind=kind,id=id,pass_=bool(ok),value=value,floor=floor))
def polys(g):return [] if g.is_empty else [g] if g.geom_type=='Polygon' else [p for p in getattr(g,'geoms',[]) if p.geom_type=='Polygon']
def polyrec(g):return [dict(outer=list(p.exterior.coords),holes=[list(r.coords)for r in p.interiors])for p in polys(g)]
def readpub(f):return unary_union([Polygon(p['outer'],p['holes'])for p in f['public_walkway']])
def world(p):return (p[0]-714,p[1]-30)
def clean(g):return make_valid(g).buffer(0)
def rectcentre(c,u,l,w):
 n=(-u[1],u[0]);return Polygon([(c[0]+u[0]*a+n[0]*b,c[1]+u[1]*a+n[1]*b)for a,b in [(-l/2,-w/2),(l/2,-w/2),(l/2,w/2),(-l/2,w/2)]])
def geomdump(o):
 if hasattr(o,'geom_type'):return mapping(o)
 raise TypeError(type(o))
# Independently audit the supplied claims before making revisions.
for f in SOURCE:
 pub=readpub(f);v=unary_union([Polygon(p)for p in f['atrium_polygon']])
 for s in f['tenant_lots']:
  err=Point(s['entry']).distance(Polygon(s['polygon']))
  if err>.01:AUDIT.append(dict(floor=f['floor'],id=s['id'],issue='入口が自店舗の外',value=round(err,4),unit='m'))
 if f['floor']>1:AUDIT.append(dict(floor=f['floor'],id='PUBLIC/VOID',issue='機械可読の共用歩行域が吹き抜けを包含',value=round(pub.intersection(v).area,3),unit='m2'))
 for c in f['cores']:
  AUDIT.append(dict(floor=f['floor'],id=c['id'],issue='機械可読の共用歩行域が設備核を包含',value=round(pub.intersection(Polygon(c['outline'])).area,3),unit='m2'))
 AUDIT.append(dict(floor=f['floor'],id='ESC',issue='昇降機の軸・幅・床開口を描画記号から直交形状へ再定義',value=len(f['escalators']),unit='flights'))
# Reject the three-plaza affine as a coordinate system: it is a nonuniform deformation.
tf=json.loads((IN/'B_provisional_coordinate_transform.json').read_text())
a,b=tf['matrix'][:2];tr=a[0]**2+a[1]**2+b[0]**2+b[1]**2;det=(a[0]*b[1]-a[1]*b[0])**2
sv=[math.sqrt((tr+q*math.sqrt(tr*tr-4*det))/2)for q in [1,-1]]
AUDIT.append(dict(id='AFFINE',issue='仮変換は寸法を保たない。世界座標への平行移動に変更',singular_values=sv))
ALL_ESC=[]
for e in SOURCE[1]['escalators']:
 p=Polygon(e['shaft']);xy=list(p.exterior.coords);dx=xy[1][0]-xy[0][0];dz=xy[1][1]-xy[0][1];ll=math.hypot(dx,dz);u=(dx/ll,dz/ll);c=(p.centroid.x,p.centroid.y)
 # Mechanism run 11.8m + horizontal comb plates 1.5m at each end.
 shaft=rectcentre(c,u,14.8,2.4)
 land=[]
 for side in [-1,1]:land.append(rectcentre((c[0]+u[0]*side*8.9,c[1]+u[1]*side*8.9),u,3.0,3.6))
 ALL_ESC.append(dict(id=e['id'],atrium=e['atrium'],levels=e['levels'],direction=e['direction'],u=u,c=c,shaft=shaft,landings=land,run_m=11.8,width_m=2.4,step_clear_m=1.,comb_m=1.5))
VOIDS=[Polygon(v)for v in SOURCE[0]['atrium_polygon']]
LANDS=unary_union([p for e in ALL_ESC for p in e['landings']])
# Fixed, coordinated structural openings; small permanent landing decks match 2F/3F.
OPEN=unary_union(VOIDS).difference(LANDS)
CORES=[]
for i,(cx,cz) in enumerate([(139,28),(243,135),(379,33)]):
 angle=180 if i==1 else 0
 def trgeom(p):return affinity.translate(affinity.rotate(p,angle,origin=(0,0)),cx,cz)
 def tp(p):q=trgeom(Point(p));return [q.x,q.y]
 rooms={'stair':box(-12,-9,-5,6),'lift':box(-4,-9,0,-5),'accessible_wc':box(-4,-4,0,0),'lift_lobby':box(-4,0,2,6),'women':box(2,-9,7,6),'men':box(8,-9,12,6),'front_lobby':box(-12,6,12,9.8),'lift_access':box(0,-5,2,6)}
 doors=[dict(id='ST',p=(-8.5,6),w=1.5,axis=(1,0)),dict(id='EV',p=(-2,-5),w=1.4,axis=(1,0)),dict(id='AWC',p=(0,-2),w=1.2,axis=(0,1)),dict(id='W',p=(4.5,6),w=1.5,axis=(1,0)),dict(id='M',p=(10,6),w=1.5,axis=(1,0)),dict(id='CORE',p=(0,10),w=4.,axis=(1,0))]
 for d in doors:
  d['p']=tp(d['p']);d['axis']=tuple(-a if angle else a for a in d['axis'])
 fixtures=[]
 # Cubicles, side-mounted sink counters and screened vestibules.
 for j in range(2):
  fixtures.append(dict(kind='WC-W',geom=trgeom(box(2.25+j*2.15,-8.7,4.25+j*2.15,-6.4))))
  fixtures.append(dict(kind='WC-M',geom=trgeom(box(8.2+j*1.7,-8.7,9.8+j*1.7,-6.4))))
 for zz in [-4.5,-2.8]:fixtures.append(dict(kind='URINAL',geom=trgeom(box(11.3,zz,11.9,zz+.65))))
 for r in [box(2.2,.1,2.8,2.9),box(8.2,.1,8.8,2.9)]:fixtures.append(dict(kind='SINK',geom=trgeom(r)))
 outline=trgeom(box(-13,-10,13,10))
 screens=[trgeom(LineString([(2,3),(4.75,3)])),trgeom(LineString([(8,3),(10.2,3)]))]
 CORES.append(dict(vestibule_screens=screens,id=f'K{i+1}',centre=[cx,cz],angle=angle,outline=outline,rooms={k:trgeom(v)for k,v in rooms.items()},doors=doors,fixtures=fixtures,entry=tp((0,10))))
# Cubicle openings are explicit geometry, not merely white marks painted onto the PDF.
for c in CORES:
 c['cubicle_doors']=[]
 for i,fixture in enumerate(c['fixtures']):
  if fixture['kind']not in ['WC-W','WC-M']:continue
  x0,z0,x1,z1=fixture['geom'].bounds;zz=z0 if c['angle']else z1
  c['cubicle_doors'].append(dict(id=fixture['kind']+str(i),p=[x0+.75,zz],axis=[1,0],w=1.0))
 # Wall solids exclude actual openings; plumbing fixtures are separate planned objects.
 wall=unary_union([r.boundary.buffer(.10,join_style=2)for key,r in c['rooms'].items()if key not in ['front_lobby','lift_access','lift_lobby']])
 for d in c['doors']:
  wall=wall.difference(rectcentre(d['p'],d['axis'],d['w'],1.0))
 c['room_wall_solids']=wall
 c['cubicle_wall_solids']=[]
 for fixture,d in zip([p for p in c['fixtures']if p['kind']in ['WC-W','WC-M']],c['cubicle_doors']):
  c['cubicle_wall_solids'].append(fixture['geom'].boundary.buffer(.08,join_style=2).difference(rectcentre(d['p'],d['axis'],d['w'],1.)))
# Replace the inconsistent reverse-side A connection with an east entrance, retaining A/C endpoint world coordinates.
CONNECT={1:[dict(id='AB-1',route=[(488,62),(474,24.5),(540,24.5)],width=5.,old_endpoint=[-174,-5.5]),dict(id='BC-1',route=[(277,28),(277,-35),(344,-35),(344,-50)],width=8.,old_endpoint=[-370,-80])],2:[dict(id='AB-2',route=[(488,62),(474,24.5),(604,24.5)],width=5.,old_endpoint=[-110,-5.5]),dict(id='BC-2',route=[(277,28),(277,-35),(282,-35),(282,-87)],width=5.,old_endpoint=[-432,-117])],3:[]}
FLOORS=[]
for src in SOURCE:
 floor=src['floor'];rawpub=readpub(src)
 # Remove obsolete supplied connectors before placing the coordinated new ones.
 for c in src['connectors']:
  rawpub=rawpub.difference(LineString(c['route'][-2:]).buffer(c['width']/2,cap_style=2))
 # Restore only the branch corridors of the accepted initial scheme.
 spine=[(12,85),(98,65),(184,95),(279,77),(354,109),(488,62)]
 branches=[[(98,65),(136,112),(220,125),(279,77)],[(354,109),(375,139),(452,122),(470,68)],[(184,95),(192,35),(277,28),(302,87)]]
 public=unary_union([rawpub,LineString(spine).buffer(8,join_style=2)]+[LineString(x).buffer(4.5,join_style=2)for x in branches]+[v.buffer(9,join_style=2)for v in VOIDS]+[LANDS])
 for c in CONNECT[floor]:public=public.union(LineString(c['route']).buffer(c['width']/2,cap_style=3,join_style=2))
 for c in CORES:public=public.union(LineString([c['entry'],min(spine,key=lambda p:Point(p).distance(Point(c['entry'])))]).buffer(4,join_style=2))
 shafts=unary_union([e['shaft'] for e in ALL_ESC if floor in e['levels']])
 obstacles=unary_union([c['outline']for c in CORES]+[shafts]+([OPEN]if floor>1 else []))
 public=clean(public.difference(obstacles.buffer(.18)))
 stores=[]
 for s in src['tenant_lots']:
  original=Polygon(s['polygon']);p=clean(original.difference(public)).difference(obstacles.buffer(.35));pp=polys(p)
  if not pp:continue
  p=max(pp,key=lambda p:p.area)
  # A full 2.4m doorway must lie on the surviving shopfront and meet public space.
  edges=list(p.exterior.coords);options=[]
  for a,b in zip(edges,edges[1:]):
   line=LineString([a,b]);mid=line.interpolate(.5,normalized=True)
   if line.length>=2.6 and public.distance(mid)<.22:options.append((mid.distance(Point(s['entry'])),line,mid))
  if not options:
   # Do not fabricate a door on a clipped sliver: reclassify as building/service infill.
   AUDIT.append(dict(floor=floor,id=s['id'],issue='改訂接続線と干渉／有効間口不足のため売場から除外',area_m2=p.area));continue
  _,front,door=min(options,key=lambda t:t[0]);a,b=front.coords;u=((b[0]-a[0])/front.length,(b[1]-a[1])/front.length);n=(-u[1],u[0])
  if not p.contains(Point(door.x+n[0]*.2,door.y+n[1]*.2)):n=(-n[0],-n[1])
  def q(x,z):return (door.x+u[0]*x+n[0]*z,door.y+u[1]*x+n[1]*z)
  depth=max((x-door.x)*n[0]+(y-door.y)*n[1]for x,y in p.exterior.coords)
  back=p.intersection(Polygon([q(-100,depth-3.2),q(100,depth-3.2),q(100,depth+2),q(-100,depth+2)]))
  sales=clean(p.difference(back));main=LineString([q(0,0),q(0,max(1,depth-1.5))]);aisle=main.buffer(1.2,cap_style=2).intersection(p)
  cross=LineString([q(-front.length*.35,depth*.48),q(front.length*.35,depth*.48)]).buffer(.9,cap_style=2).intersection(sales)
  back_door=q(0,depth-3.2);rear=q(0,depth)
  # Shelf zones reserve the modeled clear aisles; furniture is design-only.
  fixtures=sales.buffer(-.6).difference(aisle.union(cross).buffer(.2))
  stores.append(dict(id=s['id'],category=s['category'],polygon=p,entry=[door.x,door.y],frontage_m=front.length,depth_m=depth,door_width_m=2.4,front=list(front.coords),u=u,n=n,backroom=back,sales=sales,aisles=aisle.union(cross),main_route=list(main.coords),back_door=back_door,rear=rear,shelf_zones=fixtures,previous_entry=s['entry'],source_area_m2=original.area,kind='tenant'))
 # Add separately counted anchor units omitted from the supplied machine-readable tenant geometry.
 for side,ap,entry in [('WEST',box(-35,55,8,110),(8,85)),('EAST',Polygon([(480,31),(530,31),(530,100),(490,100),(480,78)]),(488,62))]:
  # Anchors own their entrance lobbies, but the common concourse stays public.
  p=clean(ap.difference(public).difference(unary_union([s['polygon']for s in stores]).buffer(.25)))
  for k,pp in enumerate(polys(p)):
   if pp.area<80:continue
   edges=list(pp.exterior.coords);opts=[]
   for aa,bb in zip(edges,edges[1:]):
    edge=LineString([aa,bb]);mid=edge.interpolate(.5,normalized=True)
    if edge.length>=6.2 and public.distance(mid)<.1:opts.append((mid.distance(Point(entry)),edge,mid))
   if not opts:raise RuntimeError('Anchor needs a real doorway')
   _,edge,near=min(opts,key=lambda o:o[0]);aa,bb=edge.coords;u=((bb[0]-aa[0])/edge.length,(bb[1]-aa[1])/edge.length);n=(-u[1],u[0])
   if not pp.contains(Point(near.x+n[0]*.2,near.y+n[1]*.2)):n=(-n[0],-n[1])
   depth=max((x-near.x)*n[0]+(y-near.y)*n[1]for x,y in pp.exterior.coords)
   def aq(x,z):return(near.x+u[0]*x+n[0]*z,near.y+u[1]*x+n[1]*z)
   back=pp.intersection(Polygon([aq(-100,depth-4),aq(100,depth-4),aq(100,depth+1),aq(-100,depth+1)]))
   sales=pp.difference(back);main=LineString([aq(0,0),aq(0,depth-1.5)])
   stores.append(dict(id=f'B{floor}-A{side[0]}{k+1}',category=({'WEST':['家電・生活大型店','書店・生活大型店','シネマ複合'],'EAST':['食品大型店','大型衣料','フードホール']}[side][floor-1]),polygon=pp,entry=[near.x,near.y],frontage_m=edge.length,depth_m=depth,door_width_m=6.,front=list(edge.coords),u=u,n=n,backroom=back,sales=sales,aisles=main.buffer(2,cap_style=2).intersection(pp),main_route=list(main.coords),back_door=aq(0,depth-4),rear=aq(0,depth),shelf_zones=sales.buffer(-1).difference(main.buffer(2.5)),kind='anchor'))
 # A buildable continuous shell: close small sawtooth recesses, retain the large bends and courtyard wings.
 used=unary_union([s['polygon']for s in stores]+[c['outline']for c in CORES]+[public,unary_union(VOIDS)])
 shell=clean(used.buffer(1.5,join_style=2).buffer(4,join_style=2).buffer(-4,join_style=2).simplify(.8,preserve_topology=True))
 # One structural shell for all storeys is coordinated below. Residuals are expressly zoned, never unlabeled void.
 FLOOR=dict(floor=floor,height=HEIGHT[floor],stores=stores,public=public,shafts=shafts,void=OPEN if floor>1 else Polygon(),shell=shell,connectors=CONNECT[floor])
 FLOORS.append(FLOOR)
# Same structural building envelope 1F-3F; skybridge-only extents are not enclosed on every floor.
body=unary_union([f['shell'].intersection(box(-80,-15,537,190))for f in FLOORS]).buffer(0)
if body.geom_type!='Polygon':body=body.buffer(3).buffer(-3)
def inside_route(p,start,end):
 # Visibility graph within a 0.6m inset gives a meaningful centre route, not merely a clipped drawing.
 inset=p.buffer(-.6,join_style=2).simplify(.001,preserve_topology=True)
 comp=min(polys(inset),key=lambda a:a.distance(Point(start)))
 a=nearest_points(comp,Point(start))[0];b=nearest_points(comp,Point(end))[0]
 if comp.buffer(.002).covers(LineString([(a.x,a.y),(b.x,b.y)])):return [tuple(start),(a.x,a.y),(b.x,b.y),tuple(end)]
 nodes=[(a.x,a.y),(b.x,b.y)]+list(comp.exterior.coords)[:-1]
 for ring in comp.interiors:nodes+=list(ring.coords)[:-1]
 graph=[[]for _ in nodes]
 for i,aa in enumerate(nodes):
  for j in range(i):
   seg=LineString([aa,nodes[j]])
   if comp.buffer(.002).covers(seg):graph[i].append((j,seg.length));graph[j].append((i,seg.length))
 dist={0:0};prev={};heap=[(0,0)]
 while heap:
  cost,i=heapq.heappop(heap)
  if cost!=dist[i]:continue
  if i==1:break
  for j,w in graph[i]:
   nc=cost+w
   if nc<dist.get(j,float('inf')):dist[j]=nc;prev[j]=i;heapq.heappush(heap,(nc,j))
 if 1 not in dist:raise RuntimeError('Interior route disconnected')
 indices=[1]
 while indices[-1]!=0:indices.append(prev[indices[-1]])
 return [tuple(start)]+[nodes[i]for i in indices[::-1]]+[tuple(end)]
for f in FLOORS:
 f['shell']=body
 # Extend the actual sales/back-room depth into residual strips rather than declaring vast blanks to be storage.
 seedpoints=[s['polygon'].representative_point()for s in f['stores']]
 cells=list(voronoi_polygons(MultiPoint(seedpoints),extend_to=body.envelope).geoms)
 allocated=unary_union([s['polygon']for s in f['stores']]+[f['public'],f['void'],f['shafts']]+[c['outline']for c in CORES])
 available=body.buffer(-1.2).difference(allocated)
 for si,sr in enumerate(f['stores']):
  if sr['kind']=='anchor':continue
  p=sr['polygon'];cell=next(c for c in cells if c.covers(seedpoints[si]));ep=sr['entry'];u=sr['u'];n=sr['n'];w=sr['frontage_m']
  def q(x,z):return(ep[0]+u[0]*x+n[0]*z,ep[1]+u[1]*x+n[1]*z)
  band=Polygon([q(-w/2-1,1),q(w/2+1,1),q(w/2+1,36),q(-w/2-1,36)])
  ext=available.intersection(cell).intersection(band)
  joined=clean(p.union(ext))
  pieces=polys(joined);joined=max(pieces,key=lambda a:a.intersection(p).area)
  opened=joined.buffer(-.8,join_style=2).buffer(.8,join_style=2).intersection(joined)
  parts=polys(clean(p.union(opened)));joined=max(parts,key=lambda a:a.intersection(p).area)
  joined=clean(set_precision(joined,.0001))
  sr['polygon']=joined;depth=max((x-ep[0])*n[0]+(z-ep[1])*n[1]for x,z in joined.exterior.coords);sr['depth_m']=depth
  back=joined.intersection(Polygon([q(-100,depth-3.2),q(100,depth-3.2),q(100,depth+1),q(-100,depth+1)]))
  back_depth=3.2
  while (back.area<min(12,joined.area*.15) or back.intersection(joined.buffer(-.7,join_style=2)).area<4) and back_depth<depth*.75:
   back_depth+=1.
   back=joined.intersection(Polygon([q(-100,depth-back_depth),q(100,depth-back_depth),q(100,depth+1),q(-100,depth+1)]))
  sr['backroom']=back;sr['sales']=joined.difference(back)
  clearback=back.intersection(joined.buffer(-.7,join_style=2))
  if clearback.is_empty:raise RuntimeError('Stockroom has no clear approach')
  end=clearback.representative_point();route=inside_route(joined,ep,(end.x,end.y));sr['main_route']=route
  path=LineString(route);sr['aisles']=path.buffer(1.2,cap_style=2).intersection(joined)
  partition=back.boundary;cross=path.intersection(partition)
  if not cross.is_empty:
   pp=nearest_points(cross,Point(ep))[0];sr['back_door']=(pp.x,pp.y)
  sr['shelf_zones']=sr['sales'].buffer(-.6).difference(sr['aisles'].buffer(.2))
 occupied=unary_union([f['public'],f['void'],f['shafts']]+[s['polygon']for s in f['stores']]+[c['outline']for c in CORES])
 f['residual']=body.difference(occupied)
 # Definite service strips along backs, accessed through each shop. Shared delivery via public space is explicit.
 for s in f['stores']:
  s['service_mode']='店内搬入→専用バックルーム（共用通路は営業時間外共用）'
 # 0.45m disc swept-space test of the public route only. Slabs / steps / 3D physics are not simulated.
 free=f['public'].buffer(-.45)
 components=polys(free)
 largest=max(components,key=lambda p:p.area)
 f['clear_public']=free;f['reachable']=largest
 check('public_one_component',f"B/{f['floor']}",len(components)==1,len(components),f['floor'])
 for i,s in enumerate(f['stores']):
  p=s['polygon'];entry=Point(s['entry']);near=nearest_points(largest,entry)[0]
  check('shop_valid',s['id'],p.is_valid and p.area>10,round(p.area,3),f['floor'])
  check('door_on_own_shop',s['id'],p.boundary.distance(entry)<.01,round(p.boundary.distance(entry),5),f['floor'])
  check('door_reaches_common_space_045',s['id'],entry.distance(near)<=.72,round(entry.distance(near),4),f['floor'])
  check('shop_vs_void_shaft_core',s['id'],p.intersection(unary_union([f['void'],f['shafts']]+[c['outline']for c in CORES])).area<.01,None,f['floor'])
  check('shop_vs_public',s['id'],p.intersection(f['public']).area<.03,round(p.intersection(f['public']).area,5),f['floor'])
  check('aisles_in_own_shop',s['id'],s['aisles'].difference(p).area<.01,None,f['floor'])
  check('shop_backroom_present',s['id'],s['backroom'].area>1,round(s['backroom'].area,3),f['floor'])
  for t in f['stores'][i+1:]:
   area=p.intersection(t['polygon']).area
   check('shop_pair_no_overlap',s['id']+'/'+t['id'],area<.01,round(area,5),f['floor'])
 check('walk_not_in_void',str(f['floor']),f['public'].intersection(f['void']).area<.01,None,f['floor'])
 check('walk_not_in_shaft',str(f['floor']),f['public'].intersection(f['shafts']).area<.01,None,f['floor'])
 for c in CORES:
  check('core_front_access',c['id'],largest.distance(Point(c['entry']))<.75,round(largest.distance(Point(c['entry'])),4),f['floor'])
 for c in f['connectors']:
  end=c['route'][-1];check('connector_endpoint_preserved',c['id'],math.dist(world(end),c['old_endpoint'])<1e-6,list(world(end)),f['floor'])
  check('connector_reachable',c['id'],largest.distance(Point(end))<.01,largest.distance(Point(end)),f['floor'])
 for e in ALL_ESC:
  if f['floor'] not in e['levels']:continue
  for j,land in enumerate(e['landings']):
   # Test a landing centre, rather than the old point-touch-at-edge assertion.
   check('landing_access',e['id']+f'/{j}',largest.distance(land.centroid)<.01,round(largest.distance(land.centroid),4),f['floor'])
for c in CORES:
 for k,p in c['rooms'].items():check('core_room_in_enclosure',c['id']+'/'+k,p.difference(c['outline']).area<.01)
check('main_voids_aligned','2F/3F',FLOORS[1]['void'].equals(FLOORS[2]['void']))
for f in FLOORS:
 # Geometric adjacency checks against retained A/C, except explicit connection decks.
 old=json.loads((ROOT/'docs/map-master-floor-plans.json').read_text())
 for b in ['A','C']:
  candidates=[v for v in old if v['building']==b and v['level']==f['floor']-1]
  ps=[]
  for a in candidates:
   ps += [Polygon(p)for p in a['base']]
   ps += [Polygon(p['outer'],p.get('holes',[]))for p in a['structure']]
  if ps:
   overlap=affinity.translate(body,-714,-30).intersection(unary_union(ps)).area
   check('body_vs_existing_'+b,str(f['floor']),overlap<.1,round(overlap,3),f['floor'])
for i,e in enumerate(ALL_ESC):
 for t in ALL_ESC[i+1:]:
  area=e['shaft'].intersection(t['shaft']).area
  check('escalator_pair_no_overlap',e['id']+'/'+t['id'],area<.01,round(area,6))
 # In the plan, tread axis and side axis are perpendicular and casing width is 2.4m.
 pts=list(e['shaft'].exterior.coords);a=(pts[1][0]-pts[0][0],pts[1][1]-pts[0][1]);b=(pts[2][0]-pts[1][0],pts[2][1]-pts[1][1])
 check('escalator_orthogonal_casing',e['id'],abs(a[0]*b[0]+a[1]*b[1])<1e-7)
(OUT/'input-audit.json').write_text(json.dumps(AUDIT,ensure_ascii=False,indent=2))
(OUT/'checks.json').write_text(json.dumps(CHECKS,ensure_ascii=False,indent=2))
(OUT/'geometry.json').write_text(json.dumps(dict(status='DESIGN_REVIEW_ONLY_NOT_IMPLEMENTED',transform=dict(world_x='local_x - 714',world_z='local_z - 30',floor_y=HEIGHT,scale=1,rotation_deg=0),floors=FLOORS,cores=CORES,escalators=ALL_ESC),default=geomdump,ensure_ascii=False,indent=2))
# Ledger with explicit geometric paths and both coordinate systems.
with (OUT/'tenant-ledger.csv').open('w',encoding='utf-8-sig',newline='')as fp:
 w=csv.writer(fp);w.writerow(['新ID','階','種別','業種','区画m2','間口m','奥行m','入口幅m','入口localX','入口localZ','入口worldX','入口worldY','入口worldZ','バックルームm2','搬入方式','主路座標JSON'])
 for f in FLOORS:
  for s in f['stores']:w.writerow([s['id'],f['floor'],s['kind'],s['category'],round(s['polygon'].area,2),round(s['frontage_m'],2),round(s['depth_m'],2),s['door_width_m'],*s['entry'],world(s['entry'])[0],HEIGHT[f['floor']],world(s['entry'])[1],round(s['backroom'].area,2),s['service_mode'],json.dumps(s['main_route'])])
print('DESIGN CHECKS',len(CHECKS),'FAILED',sum(not x['pass_']for x in CHECKS))
for x in CHECKS:
 if not x['pass_']:print(x)
print('COUNTS',[(f['floor'],len(f['stores']))for f in FLOORS])
# Old IDs: use the actual v0.24 catalog, not the supplied nearest-affine assignment.
oldfloors=json.loads((ROOT/'docs/map-master-floor-plans.json').read_text())
snap=json.loads((ROOT/'docs/review-v023-snapshot.json').read_text())
names={x['id']:x.get('name','')for x in snap['outlets']}
MATCH=[]
compat={'clothes':['衣料'],'digital':['家電','生活'],'sport':['靴','生活','衣料'],'home':['生活'],'shoes':['靴'],'daily':['生活'],'books':['書籍'],'cafe':['カフェ','食品','飲食'],'kitchen':['生活'],'optical':['美容'],'jewelry':['美容'],'beauty':['美容'],'travel':['靴'],'kids':['キッズ'],'arcade':['体験'],'stationery':['ホビー','生活'],'hobby':['ホビー'],'music':['楽器'],'toys':['キッズ','ホビー']}
for f in FLOORS:
 olds=[s for a in oldfloors if a['building']=='B' and a['level']==f['floor']-1 for s in a['shops']]
 used=set()
 for s in sorted(olds,key=lambda s:('anchor'not in s['id'],s['id'])):
  p=Polygon(s['polygon']);op=(p.centroid.x,p.centroid.y)
  target_local=(op[0]+714,op[1]+30)
  def cost(t):
   preferred=any(k in t['category']for k in compat.get(s['kind'],[]))
   if 'anchor' in s['id']:preferred=t['kind']=='anchor' and 'AW' in t['id']
   return (0 if preferred else 10000)+Point(t['entry']).distance(Point(target_local))
  t=min([t for t in f['stores']if t['id']not in used],key=cost);used.add(t['id']);t['legacy_id']=s['id'];t['legacy_kind']=s['kind'];t['legacy_name']=names.get(s['id'],'')
  MATCH.append(dict(old_id=s['id'],old_point_type='v0.24区画重心（入口ではない）',old_world_xz=op,old_y=HEIGHT[f['floor']],new_id=t['id'],new_point_type='入口',new_local_xz=t['entry'],new_world_xz=world(t['entry']),new_y=HEIGHT[f['floor']],floor=f['floor'],action='ID別名を維持・内装寸法再配置',old_kind=s['kind'],new_use=t.get('legacy_name')or t['category']))
 # Cinema exists in code but not the generated catalog: never invent an existing ID.
 if f['floor']==3:
  t=next(t for t in f['stores']if t['kind']=='anchor'and'AW'in t['id']);t['legacy_name']='シネマ・星あかり';t['legacy_kind']='cinema'
  MATCH.append(dict(old_id='（旧カタログIDなし）scripts/b_wing.gd::_cinema',old_point_type='旧核区画重心',old_world_xz=(-669,0),old_y=HEIGHT[3],new_id=t['id'],new_point_type='入口',new_local_xz=t['entry'],new_world_xz=world(t['entry']),new_y=HEIGHT[3],floor=3,action='空間機能移設・新ID採番',old_kind='cinema',new_use='シネマ・星あかり'))
for f in FLOORS:
 for j,(name,op) in enumerate([('翼',(-624,0)),('時',(-414,26)),('光',(-218,0))]):
  p=VOIDS[j].centroid;new=(p.x,p.y)
  MATCH.append(dict(old_id=name+'の広場',old_point_type='広場中心',old_world_xz=op,old_y=HEIGHT[f['floor']],new_id=f'AT-{j+1}',new_point_type='吹き抜け中心（着地点不可）',new_local_xz=new,new_world_xz=world(new),new_y=HEIGHT[f['floor']],floor=f['floor'],action='名称維持・形状再設計',old_kind='atrium',new_use='広場・吹き抜け'))
for f in FLOORS:
 for c in f['connectors']:
  MATCH.append(dict(old_id=c['id'],old_point_type='既存A/C側端点',old_world_xz=c['old_endpoint'],old_y=HEIGHT[f['floor']],new_id=c['id'],new_point_type='連絡路端点',new_local_xz=c['route'][-1],new_world_xz=world(c['route'][-1]),new_y=HEIGHT[f['floor']],floor=f['floor'],action='A/C側座標維持・B側線形変更',old_kind='link',new_use='館間連絡'))
for id,op,level,target in [('b.entrance',(-194,-5.5),1,(530,24.5)),('b.lounge',(-192,-5.5),2,(522,24.5)),('b.cinema',(-654,0),3,(12,85)),('b.digital',(-676,0),1,(12,85)),('ab.skybridge',(-150,-5.5),2,(564,24.5)),('bc.walkway',(-370,-52),1,(344,-42)),('bc.skybridge',(-442,-65),2,(282,-35))]:
 f=FLOORS[level-1];check('travel_target_on_public',id,f['reachable'].distance(Point(target))<.01,f['reachable'].distance(Point(target)),level)
 MATCH.append(dict(old_id=id,old_point_type='HUBS床上基準（実着地Yは+0.1）',old_world_xz=op,old_y=HEIGHT[level]+.1,new_id=id,new_point_type='HUBS移設予定',new_local_xz=target,new_world_xz=world(target),new_y=HEIGHT[level]+.1,floor=level,action='訪問ID維持・座標のみ移設予定',old_kind='hub',new_use='ファストトラベル'))
with (OUT/'coordinate-migration.csv').open('w',encoding='utf-8-sig',newline='')as fp:
 w=csv.writer(fp);w.writerow(['旧ID','階','旧座標の意味','旧WorldX','旧WorldY','旧WorldZ','新ID','新座標の意味','新LocalX','新LocalZ','新WorldX','新WorldY','新WorldZ','移行方式','旧業種','維持する用途・名称'])
 for m in MATCH:w.writerow([m['old_id'],m['floor'],m['old_point_type'],m['old_world_xz'][0],m['old_y'],m['old_world_xz'][1],m['new_id'],m['new_point_type'],*m['new_local_xz'],m['new_world_xz'][0],m['new_y'],m['new_world_xz'][1],m['action'],m['old_kind'],m['new_use']])
# Exact wall and doorway geometry for downstream authoring, still not imported by Godot.
for f in FLOORS:
 for s in f['stores']:
  cut=rectcentre(s['entry'],s['u'],s['door_width_m'],2.)
  edges=list(s['polygon'].exterior.coords)
  wall=unary_union([LineString([a,b]).buffer(.125,cap_style=2)for a,b in zip(edges,edges[1:])]).difference(cut)
  # Backroom access uses a separate opening on the sales/back-room partition.
  partition=s['backroom'].boundary.intersection(s['sales'].boundary).buffer(.10).difference(LineString(s['main_route']).buffer(.75))
  s['wall_solids']=wall.union(partition)
  route=LineString(s['main_route']);swept=substring(route,min(.8,route.length/2),route.length).buffer(.45)
  check('interior_route_radius045',s['id'],swept.difference(s['polygon']).area<.02,round(swept.difference(s['polygon']).area,5),f['floor'])
  check('interior_route_clear_of_wall',s['id'],swept.intersection(s['wall_solids']).area<.02,round(swept.intersection(s['wall_solids']).area,5),f['floor'])
  check('main_route_inside_shop',s['id'],LineString(s['main_route']).difference(s['polygon'].buffer(.001)).length<.01,None,f['floor'])
  check('main_route_not_blocked_by_shelf',s['id'],LineString(s['main_route']).intersection(s['shelf_zones']).length<.01,None,f['floor'])
  check('front_door_clear_of_wall',s['id'],s['wall_solids'].distance(Point(s['entry']))>=min(.99,s['door_width_m']/2-.15),round(s['wall_solids'].distance(Point(s['entry'])),3),f['floor'])
# Physical-room route checks: the vestibule/wash/cubicle geometry is tested in local coordinates.
for c in CORES:
 for label in ['women','men']:
  room=c['rooms'][label];fixtures=unary_union([l.buffer(.08)for l in c['vestibule_screens']]+[p['geom']for p in c['fixtures']if (label=='women'and p['kind']=='WC-W')or(label=='men'and p['kind']=='WC-M')or p['kind']in ['SINK','URINAL']])
  free=room.buffer(-.10).difference(fixtures.buffer(.1)).buffer(-.45)
  check('wc_clear_space_single_component',c['id']+'/'+label,len(polys(free))==1,len(polys(free)))
 check('accessible_wc_clear_turning_disc',c['id'],c['rooms']['accessible_wc'].buffer(-.15).contains(Point(c['rooms']['accessible_wc'].centroid).buffer(.75)))
# Persist final annotated geometries/checks after ID and wall coordination.
(OUT/'geometry.json').write_text(json.dumps(dict(status='DESIGN_REVIEW_ONLY_NOT_IMPLEMENTED',transform=dict(world_x='local_x - 714',world_z='local_z - 30',floor_y=HEIGHT,scale=1,rotation_deg=0),floors=FLOORS,cores=CORES,escalators=ALL_ESC,migration=MATCH),default=geomdump,ensure_ascii=False,indent=2))
(OUT/'checks.json').write_text(json.dumps(CHECKS,ensure_ascii=False,indent=2))
# Vector PDF, individually selectable Japanese labels, local coordinate grid and enlarged drawings.
doc=fitz.open();TOC=[]
INK=(.12,.22,.26);MUTED=(.34,.42,.45);RED=(.72,.23,.16)
def newpage(title,subtitle='',w=1684,h=1000):
 p=doc.new_page(width=w,height=h);p.insert_font(fontname='jp',fontfile=str(FONT));text(p,40,42,title,22);text(p,40,68,subtitle,10,MUTED);text(p,40,h-20,f'FIND YOURSELF / B館 詳細設計レビュー改訂3 / 2026-10-26 / 図面のみ・未施工   •   {len(doc):02}',9,MUTED);TOC.append([1,title,len(doc)]);return p

def text(p,x,y,s,size=10,color=INK):p.insert_text((x,y),str(s),fontsize=size,fontname=('helv'if str(s).isascii()else'jp'),color=color)
def paragraphs(p,lines,x=45,y=110,size=15,gap=35):
 for line in lines:text(p,x,y,line,size);y+=gap
 return y

def drawg(p,g,xy,fill=None,color=INK,width=.6):
 for po in polys(g):
  sh=p.new_shape();sh.draw_polyline([xy(c)for c in po.exterior.coords])
  for ring in po.interiors:sh.draw_polyline([xy(c)for c in ring.coords])
  sh.finish(color=color,fill=fill,width=width,closePath=True,even_odd=True);sh.commit()

def line(p,coords,xy,color=INK,width=.6,dashes=None):p.draw_polyline([xy(c)for c in coords],color=color,width=width,dashes=dashes)
def dot(p,pt,xy,r=1.8,color=RED):p.draw_circle(xy(pt),r,color=color,fill=color)
def viewmap(p,f,extent,rect,detail=False):
 x0,z0,x1,z1=extent;r=fitz.Rect(rect);scale=min(r.width/(x1-x0),r.height/(z1-z0));ox=r.x0+(r.width-(x1-x0)*scale)/2;oz=r.y0+(r.height-(z1-z0)*scale)/2
 xy=lambda pt:fitz.Point(ox+(pt[0]-x0)*scale,oz+(pt[1]-z0)*scale)
 # Avoid raster clipping: geometries are clipped in their native metre coordinate system.
 clip=box(*extent)
 dg=lambda g,fill=None,color=INK,width=.6:drawg(p,g.intersection(clip),xy,fill,color,width)
 dg(f['shell'],(.92,.91,.87),INK,1.2)
 dg(f['residual'],(.89,.87,.82),(.67,.65,.60),.3)
 dg(f['public'],(.97,.98,.97),(.45,.57,.56),.5)
 # Retained original core outline displayed faintly only in comparison section, not new plans.
 for s in f['stores']:
  if not s['polygon'].intersects(clip):continue
  dg(s['polygon'],(.80,.88,.90)if s['kind']=='tenant'else(.72,.80,.82),INK,.65)
  dg(s['backroom'],(.92,.81,.67),(.55,.43,.31),.3)
  if detail:
   dg(s['shelf_zones'],(.70,.76,.75),(.48,.55,.54),.3)
   dg(s['aisles'],(.96,.97,.92),(.39,.61,.46),.35)
   dg(s['wall_solids'],(.16,.26,.29),(.16,.26,.29),.1)
  # A white doorway cuts the facade wall; red endpoints show real 2.4/6m opening.
  ep=s['entry'];u=s['u'];a=(ep[0]-u[0]*s['door_width_m']/2,ep[1]-u[1]*s['door_width_m']/2);b=(ep[0]+u[0]*s['door_width_m']/2,ep[1]+u[1]*s['door_width_m']/2)
  if clip.covers(Point(ep)):
   line(p,[a,b],xy,(1,1,1),2);dot(p,ep,xy,2.5 if detail else 1.4)
  c=s['polygon'].representative_point()
  if clip.covers(c):
   q=xy((c.x,c.y));text(p,q.x-12,q.y,s['id'],7 if detail else 5)
   if detail:text(p,q.x-15,q.y+10,(s.get('legacy_name')or s['category']).split(' / ')[0][:13],6)
  if detail:
   route=LineString(s['main_route']).intersection(clip)
   for seg in ([route]if route.geom_type=='LineString'else getattr(route,'geoms',[])):
    if seg.geom_type=='LineString'and not seg.is_empty:line(p,list(seg.coords),xy,(.15,.50,.30),.65)
 dg(f['void'],(.94,.91,.80),(.69,.52,.21),1.)
 if f['floor']==1:
  for v in VOIDS:dg(v,(.95,.93,.85),(.69,.52,.21),.7)
 for j,v in enumerate(VOIDS):
  c=v.centroid
  if clip.covers(c):q=xy((c.x,c.y));text(p,q.x-18,q.y,f'AT-{j+1}',9);text(p,q.x-23,q.y+12,'催事床'if f['floor']==1 else'吹き抜け',7)
 for e in ALL_ESC:
  if f['floor']not in e['levels']:continue
  dg(e['shaft'],(.60,.70,.65),(.21,.40,.33),.7)
  for land in e['landings']:dg(land,(.87,.94,.87),(.21,.40,.33),.5)
  a=e['shaft'].centroid;u=e['u'];sgn=1 if e['direction']=='UP'else-1
  if clip.covers(a):
   line(p,[(a.x-u[0]*4*sgn,a.y-u[1]*4*sgn),(a.x+u[0]*4*sgn,a.y+u[1]*4*sgn)],xy,(.1,.35,.27),1)
   tip=(a.x+u[0]*4*sgn,a.y+u[1]*4*sgn);n=(-u[1],u[0]);line(p,[(tip[0]-u[0]*sgn+n[0]*.6,tip[1]-u[1]*sgn+n[1]*.6),tip,(tip[0]-u[0]*sgn-n[0]*.6,tip[1]-u[1]*sgn-n[1]*.6)],xy,(.1,.35,.27),1)
   if detail:q=xy((a.x,a.y));text(p,q.x,q.y-4,e['id'],5)
 for c in CORES:
  if not c['outline'].intersects(clip):continue
  dg(c['outline'],(.91,.80,.80),(.62,.31,.31),.8)
  for name,room in c['rooms'].items():dg(room,None,(.62,.31,.31),.5)
  if clip.covers(Point(c['centre'])):q=xy(c['centre']);text(p,q.x-5,q.y,c['id'],8)
  if detail:
   for d in c['doors']:
    if clip.covers(Point(d['p'])):dot(p,d['p'],xy,2)
 for c in f['connectors']:
  for a,b in zip(c['route'],c['route'][1:]):
   seg=LineString([a,b]).intersection(clip)
   if seg.geom_type=='LineString'and not seg.is_empty:line(p,list(seg.coords),xy,(.62,.22,.20),.7,'[3 2]')
  if clip.covers(Point(c['route'][-1])):q=xy(c['route'][-1]);text(p,q.x-20,q.y-8,c['id'],8,RED)
 # Coordinate ticks are labelled in metres; actual PDF scale depends on sheet sizing.
 for x in range(math.ceil(x0/25)*25,math.floor(x1/25)*25+1,25):q=xy((x,z1));text(p,q.x-7,r.y1+12,str(x),7,MUTED)
 for z in range(math.ceil(z0/25)*25,math.floor(z1/25)*25+1,25):q=xy((x0,z));text(p,r.x0-24,q.y,str(z),7,MUTED)
 p.draw_rect(r,color=(.70,.74,.74),width=.3)
 return xy,scale

summary=newpage('B館 1F–3F 詳細設計レビュー：改訂3','承認対象はゲーム用の空間設計。実施設計・施工許可図ではありません。',w=1190,h=842)
counts=[len(f['stores'])for f in FLOORS];bounds=body.bounds
failed=[c for c in CHECKS if not c['pass_']]
paragraphs(summary,[
'対象：添付13ページPDF・区画JSON・店舗台帳・仮座標変換を独立検査し、図面データを改訂。',
'維持：屈曲する主軸、局所的な回遊路、3つの吹き抜け。旧SVGの楕円リングは採用しない。',
'修正：B1-068入口、歩行域と吹き抜け・設備の重複、エスカレーター軸、館間接続、設備内訳。',
'座標案：World X = Local X − 714、World Z = Local Z − 30。縮尺1:1・回転なし。',
f'計画区画数：1F {counts[0]}、2F {counts[1]}、3F {counts[2]}（各階に大型核2を含む）。',
f'平面幾何検査：{len(CHECKS):,}件、失敗 {len(failed)}件。多くは区画間重複の組合せ検査。',
'実歩行・Godot衝突・NPC経路・宝箱・猫・ソナー・ファストトラベルは改修後の試験。今回は未実施。',
'図中の棚は通路を確保する内装計画帯。完成した商品モデル・店舗装飾ではない。',
'全店に裏の専用搬入回廊を通した計画ではない。搬入は店内主路を営業時間外に共用する。',
'構造柱・耐火区画・避難計画・梁と設備配管の確定は範囲外。実建築の適法性は保証しない。',
'確認してほしい点：通路の屈曲・店舗配置・吹き抜け規模・A/C接続案・搬入方式。',
'ゲームシーン／ロジック／保存済みワールド／配布ゲームは変更していない。承認後に段階施工。'
],size=13,gap=45)
for f in FLOORS:
 p=newpage(f"B館 {f['floor']}F / 全体平面図",f"床高 +{f['height']:.3f}m / 通常区画 {sum(s['kind']=='tenant'for s in f['stores'])}＋大型核 {sum(s['kind']=='anchor'for s in f['stores'])} / Local XZ m / 茶＝専用バックルーム・灰＝共用設備・外壁サービス帯")
 viewmap(p,f,(-60,-100,615,185),(60,105,1630,820))
 paragraphs(p,['共用主軸16m・枝道9m・設備アクセス8m。赤点＝入口。入口幅は台帳参照。',
 '上階の黄土色＝共通吹き抜け、緑＝昇降機と乗降床。断面・拡大図で方向と高さを確認。',
 '灰色の余剰部分は非公開の設備・躯体帯。探索可能な空白としてNPCや宝箱を置かない。'],x=60,y=875,size=12,gap=24)
 # Enlargements include wall solids, shelves, door openings, aisles and explicit stockroom.
 for zone,(lo,hi) in enumerate([(-45,165),(155,355),(345,537)],1):
  p=newpage(f"B館 {f['floor']}F / 区画拡大 {zone}",'店舗ID・入口開口・売場主路/横断路・棚配置帯・専用バックルーム。実線壁厚0.25m。棚帯は内装計画。')
  viewmap(p,f,(lo,-15,hi,180),(60,100,1610,885),True)
  text(p,60,935,'図示の局所座標と機械可読geometry.jsonは共通。入口は2.4m、大型核は6m（有効開口の詳細は改修時検証）。',11)
# Three independent atrium sheets; the main void is identical on 2F and 3F.
for j,v in enumerate(VOIDS):
 p=newpage(f'AT-{j+1} / 吹き抜け・エスカレーター配置と断面','共通開口を上下階で固定。12＝1F↔2F、23＝2F↔3F。上り/下りは矢印方向。')
 bx=v.buffer(18).bounds
 for f,rect in zip(FLOORS,[(50,120,545,650),(595,120,1090,650),(1140,120,1635,650)]):
  viewmap(p,f,bx,rect,True);text(p,rect[0],100,f"{f['floor']}F  +{f['height']:.3f}m",13)
 # Section panel: run / comb / clear landing. Different vertical rises are explicit.
 for i,(lo,hi) in enumerate([(1,2),(2,3)]):
  x=100+i*800;y=840;sc=24;rise=HEIGHT[hi]-HEIGHT[lo]
  coords=[(0,0),(3,0),(4.5,0),(16.3,rise),(17.8,rise),(20.8,rise)]
  p.draw_polyline([(x+a*sc,y-b*sc)for a,b in coords],color=INK,width=2)
  for a,b in [(0,0),(3,0),(4.5,0),(16.3,rise),(17.8,rise),(20.8,rise)]:p.draw_circle((x+a*sc,y-b*sc),2,color=RED)
  text(p,x,y+25,f'{lo}F → {hi}F  高差 {rise:.3f}m / 勾配 {math.degrees(math.atan(rise/11.8)):.1f}°',11)
  text(p,x,y+45,'有効乗降床3.0m ＋ 水平部1.5m ＋ 傾斜走行11.8m ＋ 水平部1.5m ＋ 乗降床3.0m',10)
 text(p,60,935,'上階手すり：吹き抜け・床開口周囲 高1.2m、厚0.10mを計画。乗降床への開口を塞がない。頭上有効2.4mは3D施工後に確認。',11)
# Core details drawn from the actual coordinated geometry, not generic room labels.
for c in CORES:
 p=newpage(c['id']+' / トイレ・階段・エレベーター詳細（各階共通）','設備核26×20m。K2のみ180°回転。床高・階段蹴上げは階ごとに異なる。')
 corebounds=c['outline'].bounds;scale=25;ox=80;oz=130;xy=lambda pt:fitz.Point(ox+(pt[0]-corebounds[0])*scale,oz+(pt[1]-corebounds[1])*scale)
 drawg(p,c['outline'],xy,(.95,.92,.89),INK,1.5)
 labels={'stair':'避難階段','lift':'EVシャフト','accessible_wc':'多目的WC','lift_lobby':'EVロビー','women':'女性用WC','men':'男性用WC','front_lobby':'共用前室','lift_access':'EV通路2.0m'}
 for k,r in c['rooms'].items():
  drawg(p,r,xy,(.98,.97,.94),INK,.8);q=xy((r.centroid.x,r.centroid.y));text(p,q.x-25,q.y,labels[k],9)
 for fixture in c['fixtures']:
  drawg(p,fixture['geom'],xy,(.82,.87,.87),INK,.7)
  if fixture['kind'].startswith('WC'):
   r=fixture['geom'];cen=r.centroid;q=xy((cen.x,cen.y));p.draw_oval(fitz.Rect(q.x-5,q.y-8,q.x+5,q.y+8),color=INK,width=.6)
 # Each WC has an offset-screened vestibule. Screens are part of the design data below.
 for key in ['women','men']:
  room=c['rooms'][key];rx,rz,ex,ez=room.bounds
  # Mirrored K2 keeps the vestibule on its public-facing side.
  zz=rz+3 if c['angle'] else ez-3
  line(p,[(rx,zz),(rx+(ex-rx)*.55,zz)],xy,INK,.8)
  for fix in [v for v in c['fixtures']if v['kind']==('WC-W'if key=='women'else'WC-M')]:
   a,b,cc,dd=fix['geom'].bounds;zz=b if c['angle']else dd
   aa=(a+.25,zz);bb=(a+1.25,zz);line(p,[aa,bb],xy,(1,1,1),2.5)
   line(p,[aa,(a+.25,zz+(1.0 if c['angle']else-1.0))],xy,INK,.6)
 for d in c['doors']:
  a=(d['p'][0]-d['axis'][0]*d['w']/2,d['p'][1]-d['axis'][1]*d['w']/2);bb=(d['p'][0]+d['axis'][0]*d['w']/2,d['p'][1]+d['axis'][1]*d['w']/2)
  line(p,[a,bb],xy,(1,1,1),3);dot(p,d['p'],xy,3);q=xy(d['p']);text(p,q.x+4,q.y-4,f"{d['id']} {d['w']:.1f}m",8,RED)
 # Draw two concrete stair flights with 15 treads each, plus intermediate landing.
 stair=c['rooms']['stair'];sx,sz,ex,ez=stair.bounds
 for zz in [sz+3+k*.30 for k in range(16)]:
  line(p,[(sx+.5,zz),(sx+2.5,zz)],xy,INK,.5);line(p,[(sx+3.5,zz),(sx+5.5,zz)],xy,INK,.5)
 line(p,[(sx+.5,sz+2.8),(sx+5.5,sz+2.8)],xy,INK,1)
 r=c['rooms']['accessible_wc'];q=xy((r.centroid.x,r.centroid.y));p.draw_circle(q,.75*scale,color=(.25,.55,.65),width=.8,dashes='[3 2]')
 paragraphs(p,[
 '上階との関係：K1/K2/K3は全階で同一XZ。B1/RFへ拡張する設備核を予約。',
 'EV：シャフト4×4m。扉1.4m。正面に幅2.0mのアクセス路を確保。',
 '多目的WC：4×4m（壁厚前）。扉1.2m、回転直径1.5mの余地を図示。',
 '女性用：5×15m、個室2（約2.0×2.3m）、前室/洗面/奥通路。',
 '男性用：4×15m、個室2（約1.6×2.3m）・小便器2、前室/洗面/奥通路。',
 '洗面は側壁カウンター。前室を隔てて個室を直接見通さない配置。',
 '設備の利用区分と個室数はゲーム用案。必要なら子ども用・授乳室を追加。',
 '階段：各階32蹴上げ。16＋16の折返し。踏面0.30m、片側有効2.0m。',
 '1F→2F：蹴上0.17266m。2F→3F：蹴上0.16719m。中間踊場1.8m。',
 '階段室の防火扉・手すり・梁下高さは3D実装時に検証。',
 'Fキー扉・EV呼び出し・経路切替は未実装。図面承認後の工事対象。'
 ],x=820,y=160,size=12,gap=43)
 text(p,80,820,f"設備中心 Local({c['centre'][0]},{c['centre'][1]}) = World{world(c['centre'])}",13)
 text(p,80,850,'共用前室の4m開口へ外部アクセス8m。トイレ扉1.5m、階段1.5m。寸法はゲーム用仮設計。',12)
p=newpage('階段断面・EV上下階対応','平面図と同じ階高を使用。階段踏面0.30m、32蹴上げ、2方向折返し。EVシャフトは全階同じXZ。')
for panel,(lo,hi) in enumerate([(1,2),(2,3)]):
 x=100+panel*800;base=580;sc=42;rise=HEIGHT[hi]-HEIGHT[lo];riser=rise/32
 # Unfold the two flights along the section axis to show all actual risers.
 pts=[(0,0),(1.8,0)]
 xx=1.8;yy=0
 for flight in range(2):
  for step in range(16):
   yy+=riser;pts.append((xx,yy))
   if step<15:xx+=.30;pts.append((xx,yy))
  xx+=1.8;pts.append((xx,yy))
 p.draw_polyline([(x+a*sc,base-b*sc)for a,b in pts],color=INK,width=1.5)
 text(p,x,650,f'{lo}F → {hi}F  高差{rise:.3f}m / 蹴上{riser:.5f}m ×32',14)
 text(p,x,685,'1段踏面0.30m ×15 / 16蹴上ごとに折返し / 踊場1.8m',12)
 text(p,x,720,'断面は折返しを展開表示。平面の階段室7×15m内に2列で収納。',11)
text(p,100,820,'EV：全階のシャフト4×4mを一致。各階の正面ロビーは幅2.0m以上。扉敷居は床高に揃える。',13)
text(p,100,860,'未検証：頭上2.4mの確保、天井梁、手すり接続、EV駆動、階段/扉コリジョンとNPC通行。',12,RED)
p=newpage('A・B・C館 / 既存配置と新B館の接続','青＝既存A/Cの床。茶＝新B館。赤破線＝新しい館間移動中心線。既存A/C本体は変更対象外。')
rect=fitz.Rect(60,110,1620,850);extent=(-780,-260,250,200);scale=min(rect.width/(extent[2]-extent[0]),rect.height/(extent[3]-extent[1]));xy=lambda p:fitz.Point(rect.x0+(p[0]-extent[0])*scale,rect.y0+(p[1]-extent[1])*scale)
for a in oldfloors:
 if a['level']!=0 or a['building']=='B':continue
 for poly in a['base']:drawg(p,Polygon(poly),xy,(.72,.83,.87),INK,.4)
 for packet in a['structure']:drawg(p,Polygon(packet['outer'],packet.get('holes',[])),xy,(.72,.83,.87),INK,.4)
drawg(p,affinity.translate(body,-714,-30),xy,(.88,.82,.70),INK,.8)
for f in FLOORS:
 for cc in f['connectors']:line(p,[world(q)for q in cc['route']],xy,RED,1.2,'[5 3]');q=xy(world(cc['route'][-1]));text(p,q.x,q.y,cc['id'],10,RED)
for name,at in [('A館（既存）',(-35,15)),('B館（改訂案）',(-440,55)),('C館（既存）',(-375,-185))]:q=xy(at);text(p,q.x-20,q.y,name,15)
text(p,60,900,'B館の本体は既存A/Cと平面上で重ならない。C側橋・歩行路は既存端点へ接続し、B側の線形を更新する案。',12)
text(p,60,930,'館間連絡路に残る既存ガラスや手すりは改修時に切り欠く。ここではシーンコリジョンの通過を保証しない。',12,RED)
# Independent per-level connectivity / old vs new overview.
p=newpage('座標整合・館間接続 / 改修境界','建物を変形させずに配置する案。旧店IDは移設先の別名として保持し、距離だけで用途を変えない。',w=1190,h=842)
paragraphs(p,[
'旧アフィン変換の主倍率は約1.096と0.229。同じ1mが方向で異なるため不採用。',
'新配置：World=(LocalX−714, FloorY, LocalZ−30)。全店舗・設備・昇降機に同じ式を適用。',
'床高：1F 0.000m / 2F 5.525m / 3F 10.875m（現行の床高を継承）。',
'A/B 1F端点：Local(540,24.5) = World(−174,−5.5)。現行歩行路のA側端を保持。',
'A/B 2F端点：Local(604,24.5) = World(−110,−5.5)。橋は幅5m。',
'B/C 1F端点：Local(344,−50) = World(−370,−80)。地上歩行路、幅8m。',
'B/C 2F端点：Local(282,−87) = World(−432,−117)。現行C側テラス端点、幅5m。',
'3Fに館間橋は新設しない。B1/RFは上下設備の予約に留め、未施工。',
'38個の既存カタログ店舗IDと、カタログにない3F映画館の空間機能を個別に対応表へ記録。',
'旧座標は区画重心、新座標は入口。意味の異なる点であることをCSVに明記。',
'現行13売場/階という集計には映画館が含まれるが、3Fのカタログは12。単純なID39件ではない。',
'A/C本体との平面重複は検査。橋端のガラス・手すり撤去、開口、床段差は3D施工時に確認。',
'旧大判内装を新しい小区画へ縮尺変形して流用しない。棚・什器を入口と主路に合わせ再配置。'
],size=12,gap=43)
p=newpage('独立検査結果 / 未検証事項','添付の「全件合格」をそのまま採用せず、別の検査を実施。',w=1190,h=842)
paragraphs(p,[
f"改訂図面の幾何アサーション {len(CHECKS):,}件 / 合格 {sum(x['pass_']for x in CHECKS):,}件 / 不合格 {sum(not x['pass_']for x in CHECKS)}件。",
'検査内容：区画相互の面積重複、入口と自店舗の一致、売場内通路、壁開口、設備核の内包。',
'共用域は半径0.45mの円を想定して内側へ縮小し、連結性と店舗/設備/乗降床への接近を検査。',
'入口への接近判定は共用域との接点から0.72m以内。家具込み3Dの到達保証ではない。',
'吹き抜けの2F/3F一致、歩行域からの開口除外、A/C端点、ファストトラベル候補を照合。',
'添付の不整合：B1-068入口が区画外2.13m、上階歩行域に開口3409m²、設備核とも重複。',
'この修正では階段・EV・トイレと共用廊下を別の領域として記録した。',
'未検証：3D頭上余裕、斜面/階段/扉コリジョン、EV動作、NPC回避、猫、宝箱の到達性。',
'未検証：GPU負荷、1000/5000人、実際の滞在時間。新図面のゲーム内実歩行は0回。',
'搬入は全店独立した裏回廊ではなく、営業時間外に売場主路を利用する運用案。',
'構造柱・梁・配管・防火/避難適合は確定していない。ゲーム設計承認と実建築の承認は別。',
'図面完成の意味：今回提示した区画・動線・設備・接続案が読める設計資料。ゲーム工事完了ではない。',
'実装順：B1F床/外壁→開口/昇降機→2/3F→店舗再配置→案内図/NPC/宝箱→実歩行と負荷試験。'
],size=12,gap=43)
# Coordinate tables remain readable vector text, not screenshots.
for start in range(0,len(MATCH),22):
 p=newpage(f'旧→新対応表 / {start//22+1}','完全な値と点の定義はcoordinate-migration.csv。旧IDの既存性と業種を照合した移設案。',w=1684,h=1000)
 text(p,40,110,'旧ID / 階',11);text(p,430,110,'旧 World X,Z',11);text(p,670,110,'新ID',11);text(p,870,110,'新 Local X,Z',11);text(p,1110,110,'新 World X,Z',11);text(p,1350,110,'維持する用途',11)
 for j,m in enumerate(MATCH[start:start+22]):
  y=145+j*34
  text(p,40,y,str(m['old_id'])[:45]+f" / {m['floor']}F",9);text(p,430,y,','.join(f'{v:.2f}'for v in m['old_world_xz']),10);text(p,670,y,m['new_id'],10);text(p,870,y,','.join(f'{v:.2f}'for v in m['new_local_xz']),10);text(p,1110,y,','.join(f'{v:.2f}'for v in m['new_world_xz']),10);text(p,1350,y,m['new_use'][:22],9)
# All tenant dimensions are printed, not just referenced in CSV.
flat=[(f,s)for f in FLOORS for s in f['stores']]
for start in range(0,len(flat),27):
 p=newpage(f'店舗台帳 / {start//27+1}','間口は入口のある現状辺の長さ。深さはその辺からの最大法線距離。大型核・不整形区画は最大寸法の参考値。',w=1684,h=1000)
 text(p,40,110,'新ID / 用途',11);text(p,450,110,'面積㎡ / 間口m / 奥行m',11);text(p,810,110,'入口 Local X,Z',11);text(p,1100,110,'入口 World X,Y,Z',11);text(p,1440,110,'バックルーム㎡',11)
 for j,(f,s)in enumerate(flat[start:start+27]):
  y=140+j*28;wx,wz=world(s['entry']);text(p,40,y,s['id']+' '+(s.get('legacy_name')or s['category'])[:30],9);text(p,450,y,f"{s['polygon'].area:.1f} / {s['frontage_m']:.1f} / {s['depth_m']:.1f}",10);text(p,810,y,f"{s['entry'][0]:.2f},{s['entry'][1]:.2f}",10);text(p,1100,y,f"{wx:.2f},{f['height']:.3f},{wz:.2f}",10);text(p,1440,y,f"{s['backroom'].area:.1f}",10)
doc.set_toc(TOC);doc.set_metadata(dict(title='FIND YOURSELF B館 詳細設計レビュー 改訂3',author='FIND YOURSELF design review',subject='Design only, not implemented; vector floor plans and independent geometric checks'))
pdf=ROOT/'downloads/FIND_YOURSELF-B-Detailed-Review-v3.pdf';doc.save(pdf,garbage=4,deflate=True);doc.close()
print('PDF',pdf.stat().st_size,'pages',len(TOC))
