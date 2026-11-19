"""Model three original parked cars in metres and paint the two surveyed B parking aisles."""
from array import array
from collections import defaultdict
from pathlib import Path
import json
import math
import struct
from PIL import Image,ImageDraw,ImageFont

BASE=Path(__file__).resolve().parents[2]
DEST=BASE/'assets/v36/parking'
DEST.mkdir(exist_ok=True)
PAINT=[('body',[.20,.38,.37],.52,.27),('trim',[.035,.047,.05],.38,.38),
       ('glazing',[.11,.20,.23],.42,.19),('tire',[.035,.036,.037],.03,.87),
       ('alloy',[.51,.54,.52],.78,.26),('headlamp',[.82,.89,.84],.24,.18),
       ('stop',[.57,.045,.035],.14,.24),('plate',[.73,.71,.61],.15,.52)]
PROFILES={
 'estate':(4.33,1.78,1.53,[(0,.43),(.10,.59),(.28,.62),(.44,.96),(.75,1),(.87,.98),(.97,.76),(1,.57)]),
 'compact':(3.77,1.69,1.49,[(0,.42),(.10,.58),(.24,.60),(.43,.94),(.61,1),(.75,.99),(.91,.88),(1,.54)]),
 'cross':(4.47,1.87,1.70,[(0,.46),(.09,.60),(.29,.63),(.44,.97),(.66,1),(.85,.97),(.96,.80),(1,.60)])}
class Coach:
 def __init__(self):
  self.surfaces=defaultdict(lambda:[[],[],[]])
 def tri(self,material,a,b,c,ref):
  n=cross(sub(b,a),sub(c,a));m=math.sqrt(sum(t*t for t in n))
  if m<.0000001:return
  if sum(v*t for v,t in zip(n,ref))<0: b,c=c,b;n=tuple(-v for v in n)
  n=tuple(v/m for v in n);positions,normals,indices=self.surfaces[material]
  start=len(positions)//3
  for p in (a,b,c):positions.extend(p);normals.extend(n)
  indices.extend([start,start+1,start+2])
 def quad(self,m,a,b,c,d,ref):
  self.tri(m,a,b,c,ref);self.tri(m,a,c,d,ref)
 def strip(self,m,a,b,width,normal):
  axis=sub(b,a);v=cross(axis,normal);l=math.sqrt(sum(x*x for x in v))
  if l<=0:return
  d=tuple(width*.5*x/l for x in v)
  self.quad(m,sub(a,d),add(a,d),add(b,d),sub(b,d),normal)
 def panel(self,polys,m,normal):
  for i in range(1,len(polys)-1):self.tri(m,polys[0],polys[i],polys[i+1],normal)
 def tyre(self,x,y,z,r,side):
  spans=[(-.17,.92),(-.145,1),(-.018,1),(.012,.93),(.018,.68)]
  for i in range(32):
   a=i*math.tau/32;b=(i+1)*math.tau/32
   def point(w,ratio,t):return(x+side*w,y+r*ratio*math.sin(t),z+r*ratio*math.cos(t))
   ref=(side*.35,math.sin((a+b)/2),math.cos((a+b)/2))
   for j in range(len(spans)-1):
    self.quad(3,point(*spans[j],a),point(*spans[j],b),point(*spans[j+1],b),point(*spans[j+1],a),ref)
   self.tri(1,(x+side*.020,y,z),point(.02,.70,a),point(.02,.70,b),(side,0,0))
   self.quad(4,point(.025,.68,a),point(.025,.68,b),point(.026,.59,b),point(.026,.59,a),(side,0,0))
  for i in range(8):
   t=i*math.tau/8
   self.quad(4,point(.029,.14,t-.2),point(.029,.16,t+.23),point(.029,.61,t+.23),point(.029,.59,t+.055),(side,0,0))
 def export(self,path,color):
  blob=bytearray();views=[];access=[];prims=[]
  def acc(v,kind,typ,component,dimension,normalize=False):
   raw=array(kind,v).tobytes();offset=len(blob);blob.extend(raw);blob.extend(b'\x00'*(-len(blob)%4))
   view=len(views);views.append(dict(buffer=0,byteOffset=offset,byteLength=len(raw)))
   a=dict(bufferView=view,componentType=component,count=len(v)//dimension,type=typ)
   if normalize:a.update(min=[min(v[i::3]) for i in range(3)],max=[max(v[i::3]) for i in range(3)])
   access.append(a);return len(access)-1
  for m,(p,n,ix) in sorted(self.surfaces.items()):
   prims.append(dict(attributes=dict(POSITION=acc(p,'f','VEC3',5126,3,True),NORMAL=acc(n,'f','VEC3',5126,3)),indices=acc(ix,'I','SCALAR',5125,1),material=m))
  materials=[dict(name=name,pbrMetallicRoughness=dict(baseColorFactor=(color if i==0 else rgb)+[1],metallicFactor=metal,roughnessFactor=rough)) for i,(name,rgb,metal,rough) in enumerate(PAINT)]
  doc=dict(asset=dict(version='2.0',generator='FIND YOURSELF parking workshop'),scene=0,scenes=[dict(nodes=[0])],nodes=[dict(mesh=0)],meshes=[dict(primitives=prims)],buffers=[dict(byteLength=len(blob))],bufferViews=views,accessors=access,materials=materials)
  desc=json.dumps(doc,separators=(',',':')).encode();desc+=b' '*(-len(desc)%4)
  path.write_bytes(struct.pack('<4sII',b'glTF',2,28+len(desc)+len(blob))+struct.pack('<I4s',len(desc),b'JSON')+desc+struct.pack('<I4s',len(blob),b'BIN\x00')+blob)
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def cross(a,b):return(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])

def build(kind,color):
 l,w,h,profile=PROFILES[kind];half=w/2
 wheel=.335 if kind=='cross' else .303
 whs=(.195,.795)
 def roof(t):
  for (a,v),(b,u) in zip(profile,profile[1:]):
   if t<=b:return h*(v+(u-v)*(t-a)/(b-a))
  return h*profile[-1][1]
 def mouth(t):return .81+.19*min(1.,t/.10,(1-t)/.09)
 def belt(t):return min(.88*h/1.52,roof(t)-.038)
 def bound(t):
  arch=max([wheel+math.sqrt(max(0,(wheel+.045)**2-((t-ax)*l)**2)) if abs((t-ax)*l)<wheel+.045 else .235 for ax in whs])
  return max(.235,arch)
 def at(t,num,s):
  yy=roof(t);be=belt(t);base=bound(t);z=(t-.5)*l
  X=[.945,.994,1.,.948,.849,.738,.50,0]
  Y=[base,base+.045,be-.055,be,be+(yy-be)*.44,yy-.052,yy-.009,yy]
  return (s*half*mouth(t)*X[num],Y[num],z)
 def glass(t,u,s):
  p=at(t,3,s);q=at(t,5,s)
  return tuple(p[i]*(1-u)+q[i]*u for i in range(3))
 m=Coach()
 ts=sorted(set(round(v,5) for v in [i/80 for i in range(81)]+[t for t,_ in profile]))
 for s in (-1,1):
  for a,b in zip(ts,ts[1:]):
   t=(a+b)/2
   for k in range(7):
    normal=(s*(1-k/9),k/6,0)
    material=1 if k==0 else 0
    if k in (3,4) and .29<t<.944 and roof(t)-belt(t)>.20:
     material=2 if .016<abs(t-.585) and abs(t-.82)>.010 else 1
    if k>=5 and ((.29<t<(.421 if kind!='compact' else .405)) or (.89<t<.962)):
     material=2
    m.quad(material,at(a,k,s),at(b,k,s),at(b,k+1,s),at(a,k+1,s),normal)
  for ax in whs:m.tyre(s*(half-.010),wheel,(ax-.5)*l,wheel,s)
  for t in (.345,.583,.823):
   aa=at(t,1,s);bb=at(t,3,s)
   aa=(aa[0]+s*.006,aa[1]+.022,aa[2]);bb=(bb[0]+s*.009,bb[1]-.04,bb[2])
   m.strip(1,aa,bb,.009,(s,0,0))
  for t in (.54,.785):
   p=at(t,2,s);x=s*(half*mouth(t)+.006);m.strip(4,(x,p[1]-.02,p[2]-.07),(x,p[1]-.02,p[2]+.055),.024,(s,0,0))
  for a,b in zip(ts,ts[1:]):
   if a>.29 and b<.948 and roof(a)-belt(a)>.15:
    p=glass(a,.035,s);q=glass(b,.035,s)
    m.strip(4,(p[0]+s*.007,p[1],p[2]),(q[0]+s*.007,q[1],q[2]),.013,(s,0,0))
  # Small swept rear-view housings protrude from either front door.
  t=.375;z=(t-.5)*l;y=belt(t)+.065
  hull=[(s*(half-.018),y-.04,z+.02),(s*(half+.082),y-.04,z-.082),(s*(half+.157),y-.012,z-.045),(s*(half+.147),y+.053,z+.035),(s*(half+.063),y+.067,z+.068),(s*(half-.012),y+.028,z+.051)]
  m.panel(hull,0,(s,.4,-.2));m.panel([hull[i] for i in (1,2,3,4)],2,(s,.1,.5))
 for t,face in [(0,-1),(1,1)]:
  z=(t-.5)*l;yy=roof(t);be=belt(t);ww=half*mouth(t)
  border=[at(t,k,-1) for k in range(8)]+[at(t,k,1) for k in range(6,-1,-1)]
  m.panel(border,0,(0,0,face))
  def mark(x0,x1,y0,y1,mat):
   zz=z+face*.005
   m.quad(mat,(x0,y0,zz),(x1,y0,zz),(x1,y1,zz),(x0,y1,zz),(0,0,face))
  mark(-ww*.72,ww*.72,.30,.39,1)
  mark(-.196,.196,.40,.50,7)
  if not t:
   mark(-ww*.58,ww*.58,be-.115,be-.051,1)
   for i in range(3):mark(-ww*.53,ww*.53,be-.110+i*.018,be-.104+i*.018,4)
  for s in (-1,1):
   x0,x1=sorted((s*ww*.56,s*ww*.92));mark(x0,x1,min(be-.03,yy-.14),min(be+.05,yy-.048),5 if not t else 6)
 m.export(DEST/(kind+'.glb'),color)

for k,c in [('estate',[.10,.27,.26]),('compact',[.51,.18,.085]),('cross',[.59,.60,.56])]:build(k,c)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',44)
atlas=Image.new('RGBA',(1024,1024));draw=ImageDraw.Draw(atlas)
for i in range(256):
 cx=(i%16)*64;cy=(i//16)*64
 # Numerals are applied per stall in the final floor mesh; the initial zero is unnecessary.
 f=font if i<10 else ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',35 if i<100 else 27)
 draw.text((cx+32,cy+32),str(i),font=f,anchor='mm',fill=(244,237,207,255),stroke_width=0)
atlas.save(DEST/'bay-numbers.png',optimize=True)
# Seamless original aggregate sample, deterministic fine grit and porous speckles.
import random
gen=random.Random(62336)
surface=Image.new("RGB",(192,192))
asphalt=[]
for _ in range(surface.width*surface.height):
 value=max(0,min(255,round(gen.gauss(82,6))+(gen.choice([-21,18]) if gen.random()<.055 else 0)))
 asphalt.append((value-1,value+2,value+3))
surface.putdata(asphalt);surface.save(DEST/'aggregate.webp',quality=94)
layers=json.loads((BASE/'source/v22/map-data-integrated.json').read_bytes());sites=[]
for label,x,z in [('B1',153.5,28.5),('RF',-65.885,-43.993)]:
 layer=next(l for l in layers if l['wing']=='B' and l['label']==label)
 slots=[]
 for item in layer['items']:
  if item['kind']!='駐車場':continue
  cx,cz=item['point'][0]+429,item['point'][1]-46
  if math.hypot(cx-x,cz-z)>39:continue
  points=[[round(a+429,3),round(b-46,3)] for a,b in item['geometry'][0][0][:-1]]
  if len(points)!=4:continue
  sx=max(p[0] for p in points)-min(p[0] for p in points);sz=max(p[1] for p in points)-min(p[1] for p in points)
  if abs(sx-2.5)>.1 or abs(sz-5)>.1:continue
  slots.append(dict(id=item['id'],c=[cx,cz],num=int(item['id'].rsplit('-',1)[1]),corners=points))
 sites.append(dict(floor=label,y=layer['height'],centre=[x,z],bays=slots))
(BASE/'source/v36/parking-bays.json').write_text(json.dumps(sites,ensure_ascii=False,separators=(',',':')))
