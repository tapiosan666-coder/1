"""Prepare separate architectural view models from delivered A/C design data, never Godot."""
from pathlib import Path
import sys,json,math,hashlib,gzip
sys.path.append('/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
import numpy as np
from shapely.geometry import shape,Polygon,Point,LineString,box
from shapely.ops import triangulate,unary_union,nearest_points
R=Path(__file__).resolve().parents[1];O=R/'docs/ac-detailed-design-v1';O.mkdir(exist_ok=True)
def dec(v):
 if isinstance(v,dict):return shape(v)if'type'in v and('coordinates'in v or'geometries'in v)else{k:dec(x)for k,x in v.items()}
 if isinstance(v,list):return[dec(x)for x in v]
 return v

def polygons(g):return[]if g.is_empty else[g]if g.geom_type=='Polygon'else[p for p in getattr(g,'geoms',[])if p.geom_type=='Polygon']
def segments(g):return[]if g.is_empty else[g]if g.geom_type in['LineString','LinearRing']else[s for s in getattr(g,'geoms',[])if s.geom_type in['LineString','LinearRing']]
def rect(c,u,l,w):
 n=(-u[1],u[0]);return Polygon([(c[0]+a*u[0]+b*n[0],c[1]+a*u[1]+b*n[1])for a,b in[(-l/2,-w/2),(l/2,-w/2),(l/2,w/2),(-l/2,w/2)]])
models=[];camcheck=[]
for wing in['A','C']:
 source=R/f'docs/{wing.lower()}-detailed-design-v1/geometry.json';D=dec(json.loads(source.read_text()));floors=D['floors'];plazas=D.get('plazas',[])[:3]
 for pi,p in enumerate(plazas):
  court=p.get('court',p.get('polygon',p.get('geom')))
  if court is None:raise ValueError(('Missing plaza shape',wing,p.keys()))
  cx,cz=court.centroid.coords[0];extent=court.buffer(58 if wing=='A'else 90).envelope;groups={};props=[];labels=[]
  def mesh(name):return groups.setdefault(name,dict(vertices=[],faces=[]))
  def prism(g,bottom,top,mat):
   g=g.intersection(extent);m=mesh(mat)
   for poly in polygons(g):
    for t in triangulate(poly):
     if not poly.covers(t.representative_point())or poly.intersection(t).area<t.area-1e-6:continue
     q=list(t.exterior.coords)[:3];n=len(m['vertices']);m['vertices'] +=[[x-cx,z-cz,top]for x,z in q]+[[x-cx,z-cz,bottom]for x,z in q];m['faces'] +=[[n,n+1,n+2],[n+5,n+4,n+3]]
    for ring in[poly.exterior,*poly.interiors]:
     for a,b in zip(ring.coords,list(ring.coords)[1:]):
      n=len(m['vertices']);m['vertices'] +=[[a[0]-cx,a[1]-cz,bottom],[b[0]-cx,b[1]-cz,bottom],[b[0]-cx,b[1]-cz,top],[a[0]-cx,a[1]-cz,top]];m['faces'].append([n,n+1,n+2,n+3])
  def cube(x,z,w,d,y,h,mat):prism(box(x-w/2,z-d/2,x+w/2,z+d/2),y,y+h,mat)
  fs=[f for f in floors if f['level']>=0]
  for f in fs:
   y=f['height'];level=f['level'];top=next((g['height']-.32 for g in fs if g['level']==level+1),y+3.8);public=f['public'];slab=f['floor_plate']
   prism(slab,y-.32,y,'ground'if level==0 else 'slab')
   prism(public,y+.006,y+.015,'paving'if wing=='C'else'public')
   for planting in f.get('landscape',[]):
    geom=planting.get('geom',planting.get('polygon'))
    if geom is not None:prism(geom,y+.01,y+.04,'grass')
   for zone in f.get('program',[]):
    if 'GARDEN'in zone.get('id','')and zone.get('polygon')is not None:prism(zone['polygon'],y+.01,y+.04,'grass')
   for si,s in enumerate(f['stores']):
    poly=s['polygon']
    if not poly.intersects(extent):continue
    ep=s['entry'];u=s.get('u',[1,0]);width=s.get('door_width_m',2.4);opening=rect(ep,u,width,1.2);boundary=poly.boundary
    front=LineString(s['front'])if s.get('front')and not isinstance(s['front'],dict)else None
    if front is None:front=LineString([(ep[0]-u[0]*5,ep[1]-u[1]*5),(ep[0]+u[0]*5,ep[1]+u[1]*5)])
    glazing=boundary.intersection(public.buffer(.25)).buffer(.35)
    walls=s.get('wall_solids',boundary.buffer(.125,join_style=2).difference(opening))
    if'secondary_entry'in s:walls=walls.difference(rect(s['secondary_entry'],s.get('secondary_u',[1,0]),s.get('secondary_door_width_m',4.),1.2))
    prism(walls.difference(glazing),y,top,'wall'+str(si%4))
    # Transparent shopfront is omitted, while the genuine frame and fascia remain.
    for seg in segments(boundary.intersection(glazing)):
     for t in np.arange(0,seg.length,4):
      q=seg.interpolate(t)
      if Point(ep).distance(q)>width/2+.3:cube(q.x,q.y,.07,.07,y+.25,2.95,'metal')
    prism(glazing.intersection(poly).difference(opening.buffer(.1)),y, y+.23,'wall0')
    prism(glazing.intersection(poly),y+3.2,top,'fascia')
    if extent.covers(Point(ep)):labels.append(dict(text=s['id'],p=[ep[0]-cx,ep[1]-cz,y+3.35],u=u))
    shelves=s.get('shelf_zones',Polygon()).intersection(extent)
    if not shelves.is_empty:
     x0,z0,x1,z1=shelves.bounds
     for x in np.arange(x0+.7,x1,4.5):
      for z in np.arange(z0+1,z1,4.5):
       g=box(x-.45,z-1,x+.45,z+1)
       if shelves.covers(g):prism(g,y,y+1.15,'fixture')
    if'backroom'in s:prism(s['backroom'].boundary.buffer(.08).difference(LineString(s['main_route']).buffer(.9)),y,y+2.6,'wall0')
   # Conservatively close service/structural bands at their public boundary, so views do not invent a view through them.
   closed=f.get('residual',Polygon());faces=[]
   # Guardrail offsets and tiny construction seams are not full-height enclosure walls.
   for pg in polygons(public):
    for ring in[pg.exterior,*pg.interiors]:
     points=list(ring.coords)
     for aa,bb in zip(points,points[1:]):
      ll=math.dist(aa,bb)
      if ll<1e-8:continue
      ux,uz=(bb[0]-aa[0])/ll,(bb[1]-aa[1])/ll;n=(-uz,ux);parts=max(1,math.ceil(ll))
      for kk in range(parts):
       a=[aa[0]+(bb[0]-aa[0])*kk/parts,aa[1]+(bb[1]-aa[1])*kk/parts];b=[aa[0]+(bb[0]-aa[0])*(kk+1)/parts,aa[1]+(bb[1]-aa[1])*(kk+1)/parts];mid=[(a[0]+b[0])/2,(a[1]+b[1])/2]
       normal=n if public.covers(Point(mid[0]+n[0]*.08,mid[1]+n[1]*.08))else(-n[0],-n[1]);behind=Point(mid[0]-normal[0]*.65,mid[1]-normal[1]*.65)
       if closed.covers(behind):faces.append(LineString([a,b]).buffer(.13,cap_style=2).intersection(closed))
   prism(unary_union(faces),y,top,'closed')
   cores=f.get('cores',D.get('cores',[]))
   for core in cores:
    outline=core.get('outline')
    if outline is None:continue
    frame=outline.boundary.buffer(.125);cut=Polygon()
    for door in core.get('doors',[]):
     if door.get('id')in['CORE','ENTRY']or door.get('kind')=='entry':cut=cut.union(rect(door['p'],door.get('axis',[1,0]),door.get('w',4),1))
    if cut.is_empty and core.get('entry'):cut=Point(core['entry']).buffer(2)
    prism(frame.difference(cut),y,y+2.6,'closed');prism(frame,y+2.6,top,'closed')
   rails=f.get('guardrails',Polygon());prism(rails.buffer(.025),y+1.14,y+1.2,'metal')
   for part in segments(rails.boundary):
    for station in np.arange(0,part.length,5):
     q=part.interpolate(station);cube(q.x,q.y,.07,.07,y,1.2,'metal')
   # Upper outdoor decks receive their own edge rails if not supplied as geometry.
   if wing=='C'and level>0 and rails.is_empty:
    edge=f['floor_plate'].boundary.intersection(public.boundary.buffer(.025)).difference(unary_union([s['polygon'].buffer(.3)for s in f['stores']]+[c['outline'].buffer(.3)for c in cores if'outline'in c])).buffer(.035)
    for connection in D.get('connections',[]):
     if connection['level']==level:edge=edge.difference(Point(connection['point']).buffer(connection.get('width',5)/2+.5))
    prism(edge,y+1.14,y+1.2,'metal')
   for prop in f.get('furniture',[]):
    geom=prop.get('geom',prop.get('polygon'))
    if geom is None or not geom.intersects(extent):continue
    x,z=geom.centroid.coords[0];x0,z0,x1,z1=geom.bounds;kind=prop.get('kind','bench')
    if kind=='bench':
     prism(geom,y+.35,y+.46,'wood');cube(x,z+.3,max(.8,x1-x0),.12,y+.46,.4,'wood')
    elif kind in['planter','tree','plant']:
     prism(geom,y,y+.5,'stone');props.append(dict(kind='plant',p=[x-cx,z-cz,y+.9]))
    else:prism(geom,y,y+prop.get('height',1),'stone')
  # Physical steps are illustrated along exact design axes; they are not movable game devices.
  allesc=D.get('escalators',[])
  for e in allesc:
   levels=e.get('levels',[])
   if len(levels)!=2 or min(levels)<0:continue
   lo=next(f['height']for f in floors if f['level']==min(levels));hi=next(f['height']for f in floors if f['level']==max(levels));c=e.get('c',e['shaft'].centroid.coords[0]);u=e.get('u',[1,0]);n=(-u[1],u[0]);run=e.get('run_m',11.8)
   for k in range(40):
    station=-run/2+(k+.5)*run/40;pos=(c[0]+u[0]*station,c[1]+u[1]*station);yy=lo+(hi-lo)*(k+1)/40;prism(rect(pos,u,run/40,1),yy-.15,yy,'steps')
   m=mesh('metal')
   for side in[-1,1]:
    kk=len(m['vertices']);pts=[]
    for along,yy in[(-run/2,lo),(run/2,hi)]:
     for h in[yy-.35,yy+.95]:pts.append([c[0]+u[0]*along+n[0]*side*1.05-cx,c[1]+u[1]*along+n[1]*side*1.05-cz,h])
    m['vertices']+=pts;m['faces'].append([kk,kk+2,kk+3,kk+1])
  # Scale figures are reference props at the first store fronts, not added NPC records.
  free=next(f['walkable']for f in floors if f['level']==0).buffer(-.55)
  for ang in[.3,1.5,3.4]:
   nominal=Point(cx+math.cos(ang)*17,cz+math.sin(ang)*17);q=nearest_points(free,nominal)[0]
   if court.buffer(15).covers(q):props.append(dict(kind='person',p=[q.x-cx,q.y-cz,0]))
  # Eye camera is deliberately within the actual first-floor walkable area.
  desired=p.get('cameras',[]);eye=None;target=[cx,cz];camera_level=0;target_height=3.2
  if wing=='C'and pi<len(D.get('view_cameras',[])):
   cc=D['view_cameras'][pi];camera_level=cc.get('level',0);eye=cc['p'][:2];target=cc['target'][:2];target_height=cc['target'][2]
  camera_floor=next(f for f in floors if f['level']==camera_level);free=camera_floor['walkable'].buffer(-.55)
  if wing=='A':
   specified=[([-92,15],[-73,-8]),([145,15],[181,12]),([50,178],[35,148])][pi];eye,target=specified;target_height=10.0
  if isinstance(desired,list):
   for c in desired:
    if isinstance(c,dict)and c.get('id',c.get('kind',''))in['eye','approach']:
     eye=c.get('position',c.get('p',c.get('point')));target=c.get('target',target);break
  if eye is None:nominal=Point(cx-22,cz+16)
  else:nominal=Point(eye[0],eye[1])
  candidates=free.intersection(court.buffer(20));q=nearest_points(candidates if not candidates.is_empty else free,nominal)[0]
  eye_world=[q.x,q.y];camcheck.append(dict(wing=wing,plaza=p['id'],nominal=[nominal.x,nominal.y],actual_world_xz=eye_world,level=camera_level,eye_world_y=camera_floor['height']+1.65,eye_height=1.65,adjustment_m=q.distance(nominal),inside_walkable_with_clearance=True))
  if len(target)==3:target_height=target[2];target=target[:2]
  if math.dist(target,eye_world)<5:target=[cx+8,cz-3]
  cameras=[dict(id='axon',p=[75,-85,65]if wing=='A'else[105,-130,90],target=[0,0,6],orthographic=True,ortho_scale=150 if wing=='A'else 220),dict(id='eye',p=[q.x-cx,q.y-cz,camera_floor['height']+1.65],target=[target[0]-cx,target[1]-cz,target_height],orthographic=False,lens=24)]
  models.append(dict(id=p['id'],wing=wing,name=p['name'],source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),model_origin=[cx,cz],extent_world=list(extent.bounds),groups=groups,props=props,labels=labels,cameras=cameras,design_only=True,not_game_screenshot=True,glass_omitted=True,roof_and_structure_simplified=True))
(O/'view-model.json.gz').write_bytes(gzip.compress(json.dumps({'models':models},ensure_ascii=False).encode(),compresslevel=6,mtime=0));(O/'view-camera-checks.json').write_text(json.dumps(camcheck,ensure_ascii=False,indent=2));print([(m['id'],sum(len(g['vertices'])for g in m['groups'].values()))for m in models])
