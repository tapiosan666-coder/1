"""Read-only v4 frontage audit. Outputs an addendum, never changes the plan or game."""
from pathlib import Path
import sys,json,math,csv,hashlib,collections
sys.path.append('/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
import numpy as np
from shapely.geometry import shape,LineString,Point,Polygon,box,mapping
from shapely.ops import unary_union,nearest_points,linemerge
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'docs/b-purpose-review-v4';OUT=ROOT/'docs/b-v4-final-confirmation';OUT.mkdir(exist_ok=True)
raw=json.loads((BASE/'geometry.json').read_text())
def dec(o):
 if isinstance(o,dict):return shape(o)if'type'in o and('coordinates'in o or'geometries'in o)else{k:dec(v)for k,v in o.items()}
 if isinstance(o,list):return[dec(v)for v in o]
 return o
D=dec(raw)
def enc(o):
 if hasattr(o,'geom_type'):return mapping(o)
 if isinstance(o,np.generic):return o.item()
 raise TypeError(type(o))
def lines(g):return[]if g.is_empty else[g]if g.geom_type=='LineString'else[l for l in getattr(g,'geoms',[])if l.geom_type=='LineString']
def rings(g):
 for p in([g]if g.geom_type=='Polygon'else g.geoms):
  yield p.exterior
  yield from p.interiors
ROWS=[];WALLS=[];PROFILES=[];CASES=[];CHECKS=[]
def ck(k,id,ok,val=None):CHECKS.append(dict(kind=k,id=id,pass_=bool(ok),value=val))
def runs(mask,step):
 result=[];start=None
 for i,v in enumerate([*mask,False]):
  if v and start is None:start=i
  if not v and start is not None:result.append([start*step,i*step]);start=None
 return result
for f in D['floors']:
 pub=f['public'];closed=f['residual'];private=unary_union([s['polygon']for s in f['stores']]);cores=unary_union([c['outline']for c in D['cores']]);body=f['shell'];glazed=unary_union([gl.buffer(.20)for s in f['stores']for gl in s.get('glazed_frontages',[])]+[LineString(s['front']).buffer(.2)for s in f['stores']])
 # Closed front means a true band behind the public edge, not a 1mm join beside a store.
 for ring in rings(pub):
  vertices=list(ring.coords);coords=[]
  for a,b in zip(vertices,vertices[1:]):
   length=math.dist(a,b);parts=max(1,math.ceil(length/.5))
   coords +=[(a[0]+(b[0]-a[0])*k/parts,a[1]+(b[1]-a[1])*k/parts)for k in range(parts)]
  coords.append(vertices[-1]);pending=[];lastu=None;normal=None
  def finish():
   global WALLS
   if pending:
    line=LineString(pending)
    if line.length>=2:WALLS.append(dict(id=f"F{f['floor']}-W{len(WALLS)+1:03}",floor=f['floor'],line=line,length_m=line.length,normal_to_public=normal))
  for a,b in zip(coords,coords[1:]):
   dx,dz=b[0]-a[0],b[1]-a[1];ll=math.hypot(dx,dz)
   if ll<.02:continue
   u=(dx/ll,dz/ll);n=(-u[1],u[0]);mid=((a[0]+b[0])/2,(a[1]+b[1])/2)
   if not pub.covers(Point(mid[0]+n[0]*.08,mid[1]+n[1]*.08)):n=(-n[0],-n[1])
   # n faces common floor; look 0.65m behind the face into the closed band.
   probe=Point(mid[0]-n[0]*.65,mid[1]-n[1]*.65)
   isclosed=closed.buffer(.005).covers(probe)and body.covers(probe)and not private.buffer(.08).covers(probe)and not cores.buffer(.2).covers(probe)
   if isclosed and pending and lastu[0]*u[0]+lastu[1]*u[1]>.985 and math.dist(pending[-1],a)<.01:
    pending.append(b);lastu=u
   else:
    finish();pending=[a,b]if isclosed else[];lastu=u if isclosed else None;normal=n if isclosed else None
  finish()
 walls_here=[w for w in WALLS if w['floor']==f['floor']]
 wgeom=unary_union([w['line']for w in walls_here])
 plaza_union=unary_union([p['court']for p in D['plazas']])
 for route in D['routes']:
  if f['floor']not in route['levels']:continue
  cl=LineString(route['points']);length=cl.length;door=[]
  for s in f['stores']:
   for kind,entry in[('primary',s['entry'])]+([('secondary',s['secondary_entry'])]if'secondary_entry'in s else[]):
    pt=Point(entry);t=cl.project(pt);q=cl.interpolate(t);sight=LineString([pt,q])
    if pt.distance(cl)<=route['width']/2+1 and pub.buffer(.03).covers(sight):door.append(dict(store=s['id'],portal=kind,station_m=t,point=entry))
  stations=sorted(set([0.,length]+[d['station_m']for d in door]));gaps=[[a,b]for a,b in zip(stations,stations[1:])]
  step=.5;num=math.ceil(length/step);left=[];right=[];retail=[];lcat=[];rcat=[]
  for i in range(num):
   t=min(length,(i+.5)*step);pt=cl.interpolate(t);a=cl.interpolate(max(0,t-.1));b=cl.interpolate(min(length,t+.1));dx,dz=b.x-a.x,b.y-a.y;ll=math.hypot(dx,dz);n=(-dz/ll,dx/ll)
   retail.append(not plaza_union.covers(pt))
   sidecats=[]
   for sign in[1,-1]:
    ray=LineString([(pt.x,pt.y),(pt.x+n[0]*sign*28,pt.y+n[1]*sign*28)])
    hits=ray.intersection(pub.boundary);poss=[]
    for g in getattr(hits,'geoms',[hits]):
     if g.geom_type=='Point'and g.distance(pt)>.05:poss.append(g)
     elif g.geom_type=='LineString':poss.extend([Point(x)for x in g.coords])
    if not poss:sidecats.append('open');continue
    hit=min(poss,key=lambda h:h.distance(pt));q=Point(hit.x+n[0]*sign*.65,hit.y+n[1]*sign*.65)
    if not body.covers(q):cat='exterior_or_link'
    elif closed.buffer(.005).covers(q)and not private.buffer(.08).covers(q)and not cores.buffer(.2).covers(q):cat='closed_band'
    elif private.buffer(.08).covers(q):cat='shop_glazing'if glazed.distance(hit)<.35 else'shop_opaque'
    elif cores.buffer(.2).covers(q):cat='facility'
    else:cat='atrium_or_mechanism'
    sidecats.append(cat)
   lcat.append(sidecats[0]);rcat.append(sidecats[1]);left.append(sidecats[0]=='closed_band');right.append(sidecats[1]=='closed_band')
  lr=runs([v and retail[i]for i,v in enumerate(left)],step);rr=runs([v and retail[i]for i,v in enumerate(right)],step)
  maxleft=max([b-a for a,b in lr]or[0]);maxright=max([b-a for a,b in rr]or[0]);maxgap=max([b-a for a,b in gaps]or[0]);retailgaps=[]
  for a,b in gaps:
   mask=[retail[i]and a<=(i+.5)*step<=b for i in range(num)]
   retailgaps +=runs(mask,step)
  retailmax=max([b-a for a,b in retailgaps]or[0])
  public_retail=route['id'].startswith(('M-','N-','SW-','SE-'))
  reasons=[]
  if public_retail and retailmax>=25:reasons.append('店舗入口なし区間25m以上（広場内を除く）')
  if max(maxleft,maxright)>=20:reasons.append('片側閉鎖帯20m以上')
  both=runs([a and b and retail[i]for i,(a,b)in enumerate(zip(left,right))],step)
  if max([b-a for a,b in both]or[0])>=12:reasons.append('両側閉鎖帯12m以上')
  risk='重点確認'if reasons else'維持'
  if route['id'].startswith(('AB','BC')):risk='連絡専用・維持（店頭数で判定しない）'
  if route['id'].endswith('-A'):risk='設備用の必要な行き止まり・維持'
  row=dict(floor=f['floor'],route=route['id'],name=route['name'],role=route['role'],length_m=round(length,2),visible_doors=len(door),door_stations=door,max_door_gap_including_ends_m=round(maxgap,2),max_retail_door_gap_excluding_plaza_m=round(retailmax,2),longest_closed_left_m=round(maxleft,2),longest_closed_right_m=round(maxright,2),review=risk,reasons=reasons)
  ROWS.append(row);PROFILES.append(dict(floor=f['floor'],route=route['id'],left=lcat,right=rcat,step_m=.5,retail=retail))
  if reasons and public_retail:CASES.append(row)
  for w in walls_here:
   exposure=w['line'].intersection(cl.buffer(route['width']/2+1.5,cap_style=3))
   if exposure.length>=5:
    mid=exposure.representative_point();q=nearest_points(cl,mid)[0];normal=w['normal_to_public']
    if (q.x-mid.x)*normal[0]+(q.y-mid.y)*normal[1]>0:
     w.setdefault('routes',[]).append(route['id'])
     w.setdefault('exposures',{})[route['id']]=exposure
 # Input polygons remain authoritative; the addendum changes finish requirements only.
 ck('shared_floor_valid',f"F{f['floor']}",pub.is_valid)
 ck('closed_band_disjoint_public',f"F{f['floor']}",closed.intersection(pub).area<.02,closed.intersection(pub).area)
# Rank true closed faces beside principal customer streets; no treatment to short faces for its own sake.
TREAT=[]
for w in WALLS:
 if w['line'].distance(Point(290,109))<.1:
  w.setdefault('routes',[]).append('P-T-SOUTH')
 if w['length_m']<20 or not any(id in['M-W','M-C2','M-E2','N-W','N-M','SW-2','P-T-SOUTH']for id in w.get('routes',[])):continue
 if 'N-M'in w.get('routes',[])and w['length_m']<40 and not any(id in['M-W','M-C2','M-E2','N-W','SW-2']for id in w.get('routes',[])):continue
 t=dict(id=f"FW-{len(TREAT)+1:02}",wall_id=w['id'],floor=w['floor'],line=w['line'],normal_to_public=w['normal_to_public'],length_m=w['length_m'],routes=w['routes'],mode='同一面内の仕上げのみ',spec='閉鎖を維持。3m基準の縦目地、6m以下の区画でマットな色調を切替。区間の前後に1～2枚の館内案内・館管理展示の平面パネル。等間隔で展示物を詰め込まない。架空の出入口・透過窓は作らない。',projection_m=0.,panel_bottom_m=.9,panel_top_m=2.1)
 TREAT.append(t)
 ck('finish_no_projection',t['id'],t['projection_m']==0.)
# Long opaque SHOP faces are separately reported; do not pretend the closed band is the only wall.
for row in ROWS:
 prof=next(p for p in PROFILES if p['floor']==row['floor']and p['route']==row['route'])
 opaque=max([b-a for side in[prof['left'],prof['right']]for a,b in runs([x=='shop_opaque'for x in side],.5)]or[0])
 row['longest_shop_opaque_m']=round(opaque,2)
# The current input file and all protected game resources must stay byte-for-byte unchanged.
input_sha=hashlib.sha256((BASE/'geometry.json').read_bytes()).hexdigest()
(OUT/'frontage-audit.json').write_text(json.dumps(dict(baseline_commit='0c82bc9b6250bbcba9458730db9aa76fe11f338b',geometry_sha256=input_sha,method=dict(station_step_m=.5,closed_depth_probe_m=.65,ray_length_m=28,screening_thresholds=dict(one_side_closed_m=20,both_sides_closed_m=12,retail_no_door_m=25),thresholds_are_review_triggers_not_building_standards=True),routes=ROWS,profiles=PROFILES,walls=WALLS,treatments=TREAT,checks=CHECKS),default=enc,ensure_ascii=False,indent=2))
with(OUT/'route-review.csv').open('w',encoding='utf-8-sig',newline='')as fp:
 w=csv.writer(fp);w.writerow(['階','通路ID','名称','延長m','2D直線接続の店舗入口数','最大入口間隔m（端含む）','広場内を除く入口なし最長m','左閉鎖帯最長m','右閉鎖帯最長m','店舗不透過面最長m','判定','抽出理由'])
 for r in ROWS:w.writerow([r['floor'],r['route'],r['name'],r['length_m'],r['visible_doors'],r['max_door_gap_including_ends_m'],r['max_retail_door_gap_excluding_plaza_m'],r['longest_closed_left_m'],r['longest_closed_right_m'],r['longest_shop_opaque_m'],r['review'],' / '.join(r['reasons'])])
with(OUT/'local-finish-schedule.csv').open('w',encoding='utf-8-sig',newline='')as fp:
 w=csv.writer(fp);w.writerow(['指示ID','階','対象通路','壁ID','壁長m','始点Local','終点Local','修正','通路への張出しm'])
 for t in TREAT:w.writerow([t['id'],t['floor'],' / '.join(t['routes']),t['wall_id'],round(t['length_m'],2),list(t['line'].coords)[0],list(t['line'].coords)[-1],t['spec'],0])
print('ROUTES',len(ROWS),'CASES',len(CASES),'CLOSED_FACES',len(WALLS),'TREATMENTS',len(TREAT))
for c in CASES:print({k:c[k]for k in['floor','route','visible_doors','max_retail_door_gap_excluding_plaza_m','longest_closed_left_m','longest_closed_right_m']})
print('LONG_WALLS',[(t['id'],t['floor'],round(t['length_m'],1),t['routes'])for t in TREAT])
