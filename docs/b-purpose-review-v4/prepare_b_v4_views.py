"""Generate a standalone drawing-model mesh; no Godot scene or runtime import."""
from pathlib import Path
import sys,json,math
sys.path.append('/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
from shapely.geometry import shape,Polygon,LineString,box,Point
from shapely.ops import triangulate,unary_union
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/b-purpose-review-v4'
raw=json.loads((OUT/'geometry.json').read_text())
def dec(o):
 if isinstance(o,dict):return shape(o)if'type'in o and('coordinates'in o or'geometries'in o) else{k:dec(v)for k,v in o.items()}
 if isinstance(o,list):return[dec(v)for v in o]
 return o
r=dec(raw)
def polys(g):return[]if g.is_empty else[g]if g.geom_type=='Polygon'else[p for p in getattr(g,'geoms',[])if p.geom_type=='Polygon']
courts=[]
for j,p in enumerate(r['plazas']):
 extent=p['void'].buffer(55).envelope;cx,cz=p['void'].centroid.coords[0];groups={};props=[];labels=[]
 def mesh(name):return groups.setdefault(name,dict(vertices=[],faces=[]))
 def prism(g,z0,z1,mat):
  g=g.intersection(extent)
  m=mesh(mat)
  for poly in polys(g):
   for t in triangulate(poly):
    if not poly.covers(t.representative_point())or poly.intersection(t).area<t.area-.0001:continue
    coords=list(t.exterior.coords)[:3];n=len(m['vertices']);m['vertices'] += [[x-cx,y-cz,z1]for x,y in coords]+[[x-cx,y-cz,z0]for x,y in coords];m['faces'] += [[n,n+1,n+2],[n+5,n+4,n+3]]
   for ring in [poly.exterior,*poly.interiors]:
    for a,b in zip(ring.coords,list(ring.coords)[1:]):
     n=len(m['vertices']);m['vertices'] += [[a[0]-cx,a[1]-cz,z0],[b[0]-cx,b[1]-cz,z0],[b[0]-cx,b[1]-cz,z1],[a[0]-cx,a[1]-cz,z1]];m['faces'].append([n,n+1,n+2,n+3])
 def cube(x,y,w,d,z,h,mat):prism(box(x-w/2,y-d/2,x+w/2,y+d/2),z,z+h,mat)
 for f in r['floors']:
  y=f['height'];prism(f['floor_plate'],y-.32,y,'floor'+str(f['floor']))
  for s in f['stores']:
   if not s['polygon'].intersects(extent):continue
   front=unary_union([LineString(s['front'])]+s.get('glazed_frontages',[])).buffer(.30)
   if'secondary_front'in s:front=front.union(LineString(s['secondary_front']).buffer(.30))
   top={1:5.205,2:10.555,3:16.0}[f['floor']]
   prism(s['wall_solids'].difference(front),y,top,'plaster')
   prism(s['wall_solids'].intersection(front),y+.35,y+3.2,'glass')
   prism(front.intersection(s['polygon']),y+3.2,top,'fascia')
   for gl in s.get('glazed_frontages',[]):
    for k in np.arange(0,gl.length,4):
     pt=gl.interpolate(k)
     if s['wall_solids'].buffer(.01).covers(pt):cube(pt.x,pt.y,.08,.08,y+.35,2.85,'metal')
   # Fit-out scale blocks show genuine aisle space, not finished merchandise.
   zone=s['shelf_zones'].intersection(extent)
   a,b,c,d=zone.bounds if not zone.is_empty else(0,0,0,0)
   for x in np.arange(a+1,c,4.):
    for z in np.arange(b+1,d,4.):
     if zone.covers(box(x-.55,z-1.2,x+.55,z+1.2)):cube(x,z,1.1,2.4,y,.95,'furniture')
   ep=s['entry']
   if extent.contains(Point(ep)):
    kind='CINEMA'if s.get('legacy_kind')=='cinema' or(s['kind']=='anchor'and f['floor']==3 and'AW'in s['id'])else 'CAFE'if'カフェ'in s['category']else'BOOKS'if'書'in s['category']else'MARKET'if'食品'in s['category']else'LIVING'
    labels.append(dict(text=kind+' / '+s['id'],p=[ep[0]-cx,ep[1]-cz,y+3.4],u=s['u'],n=s['n']))
  prism(f['guardrails'],y,y+1.2,'railglass')
  prism(f['guardrails'].buffer(.025),y+1.14,y+1.20,'metal')
  for g in f['furniture']:
   if g['plaza']!=p['id']:continue
   gp=g['geom'];x,z=gp.centroid.coords[0];x0,z0,x1,z1=gp.bounds
   if g['kind']=='bench':
    cube(x,z,x1-x0,z1-z0,y+.35,.10,'wood');cube(x,z+.35,x1-x0,.13,y+.45,.40,'wood')
    cube(x-1,z,.12,.60,y,.35,'metal');cube(x+1,z,.12,.60,y,.35,'metal')
   elif g['kind']=='planter':
    prism(gp,y,y+.50,'stone');props.append(dict(kind='plant',p=[x-cx,z-cz,y+.8],radius=.75))
   elif g['kind']=='clock':
    prism(gp,y,y+.22,'stone');cube(x,z,.25,.25,y+.2,2.3,'metal');props.append(dict(kind='clock',p=[x-cx,z-cz,y+2.45]))
   else:
    prism(gp,y,y+.22,'stone');props.append(dict(kind='wing',p=[x-cx,z-cz,y+.22]))
  for w in f['waiting']:
   if w['plaza']==p['id']:props.append(dict(kind='person',p=[w['point'][0]-cx,w['point'][1]-cz,y],height=1.75))
 for f in r['floors']:
  for board in f.get('wayfinding',[]):
   if board['plaza']==p['id']:props.append(dict(kind='board',p=[board['point'][0]-cx,board['point'][1]-cz,board['bottom_y']],u=board['u'],text=str(f['floor'])+'F  /  INFO'))
 for e in r['escalators']:
  if e['atrium']!=j+1:continue
  lo={1:0,2:5.525}[e['levels'][0]];hi={2:5.525,3:10.875}[e['levels'][1]];u=e['u'];n=(-u[1],u[0]);c=e['c']
  for k in range(40):
   s=-5.9+(k+.5)*11.8/40;pos=(c[0]+u[0]*s,c[1]+u[1]*s);g=Polygon([(pos[0]+u[0]*a+n[0]*b,pos[1]+u[1]*a+n[1]*b)for a,b in[(-.1475,-.5),(.1475,-.5),(.1475,.5),(-.1475,.5)]])
   yy=lo+(hi-lo)*(k+1)/40;prism(g,yy-.16,yy,'steps')
  for sign,height in[(-1,lo),(1,hi)]:
   pos=(c[0]+u[0]*sign*6.65,c[1]+u[1]*sign*6.65);g=Polygon([(pos[0]+u[0]*a+n[0]*b,pos[1]+u[1]*a+n[1]*b)for a,b in[(-.75,-.65),(.75,-.65),(.75,.65),(-.75,.65)]]);prism(g,height-.15,height,'steps')
  # Sloped side panels and rails share the exact plan axis and floor heights.
  m=mesh('metal')
  for side in[-1,1]:
   n0=len(m['vertices']);pts=[]
   for along,yy in[(-5.9,lo),(5.9,hi)]:
    for zz in[yy-.35,yy+.95]:pts.append([c[0]+u[0]*along+n[0]*side*1.05-cx,c[1]+u[1]*along+n[1]*side*1.05-cz,zz])
   m['vertices']+=pts;m['faces'].append([n0,n0+2,n0+3,n0+1])
 # Roof frame is a design visualization, not an engineered beam schedule.
 b=p['court'].bounds
 for x in np.arange(b[0]+3,b[2],12):cube(x,(b[1]+b[3])/2,.16,b[3]-b[1],16,.3,'roof')
 cube((b[0]+b[2])/2,b[1],b[2]-b[0],.25,16,.3,'roof');cube((b[0]+b[2])/2,b[3],b[2]-b[0],.25,16,.3,'roof')
 if j==2:
  for k in range(5):props.append(dict(kind='mobile',p=[(k-2)*1.2,0,14.8-.15*abs(k-2)]))
 eyes=[([64,67,1.65],[99,61,3.8]),([285,57,1.65],[285,83,3.8]),([410,88,1.65],[436,76,3.8])]
 eye,target=eyes[j]
 courts.append(dict(id=p['id'],name=p['name'],groups=groups,props=props,labels=labels,cameras=[dict(id='axon',p=[-56,-62,44],target=[0,0,5.5],lens=43),dict(id='eye',p=[eye[0]-cx,eye[1]-cz,eye[2]],target=[target[0]-cx,target[1]-cz,target[2]],lens=21)],model_origin=[cx,cz]))
(OUT/'view-model.json').write_text(json.dumps(dict(design_only=True,not_game_screenshot=True,courts=courts),separators=(',',':')))
print('Prepared',[(p['id'],sum(len(g['vertices'])for g in p['groups'].values()))for p in courts])
