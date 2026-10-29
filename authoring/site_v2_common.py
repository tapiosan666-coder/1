"""Read-only design helpers for the whole-site v2 supplements."""
from pathlib import Path
import sys,json,math,csv,hashlib
sys.path.append('/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
from shapely.geometry import shape,mapping,Point,Polygon,LineString,box,GeometryCollection
from shapely.ops import unary_union,nearest_points,substring
from shapely import affinity
R=Path(__file__).resolve().parents[1];EPS=1e-8;HEIGHT={-1:-5.35,0:0.,1:5.525,2:10.875,3:16.4};LABEL={-1:'B1',0:'1F',1:'2F',2:'3F',3:'RF'}
def decode(v):
 if isinstance(v,dict):return shape(v)if'type'in v and('coordinates'in v or'geometries'in v)else{k:decode(x)for k,x in v.items()}
 if isinstance(v,list):return[decode(x)for x in v]
 return v

def encode(v):
 if hasattr(v,'geom_type'):return mapping(v)
 if hasattr(v,'item'):return v.item()
 raise TypeError(type(v))
def raw_json(p):
 p=Path(p)
 if p.exists():return json.loads(p.read_text())
 packed=Path(str(p)+".zst").read_bytes()
 import zstandard
 return json.loads(zstandard.ZstdDecompressor().decompress(packed[8:]))
def read(p):
 p=Path(p)
 if not p.exists()and p.name=="floors-updated.json":
  value=raw_json(p.parents[1]/"site-v11.json")["floors"]
  for q in raw_json(p.parents[1]/"v12/floors-updated-patch.json"):
   target=value
   for k in q["path"][:-1]:target=target[k]
   if q.get("delete"):del target[q["path"][-1]]
   else:target[q["path"][-1]]=q["value"]
  return decode(value)
 return decode(raw_json(p))

def write(p,x):Path(p).parent.mkdir(exist_ok=True,parents=True);Path(p).write_text(json.dumps(x,default=encode,ensure_ascii=False,indent=2))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def polys(g):return[]if g.is_empty else[g]if g.geom_type=='Polygon'else[p for p in getattr(g,'geoms',[])if p.geom_type=='Polygon']
def lines(g):return[]if g.is_empty else[g]if g.geom_type=='LineString'else[p for p in getattr(g,'geoms',[])if p.geom_type=='LineString']
def rect(c,u,l,w):
 n=(-u[1],u[0]);return Polygon([(c[0]+a*u[0]+b*n[0],c[1]+a*u[1]+b*n[1])for a,b in[(-l/2,-w/2),(l/2,-w/2),(l/2,w/2),(-l/2,w/2)]])
def translate_geoms(v,dx,dz):
 if hasattr(v,'geom_type'):return affinity.translate(v,dx,dz)
 if isinstance(v,dict):return{k:translate_geoms(x,dx,dz)for k,x in v.items()}
 if isinstance(v,list):return[translate_geoms(x,dx,dz)for x in v]
 return v

def core_world(c):
 c=translate_geoms(c,-714,-30)
 for k in['entry','centre']:
  if k in c:c[k]=[c[k][0]-714,c[k][1]-30]
 for k in['doors','cubicle_doors']:
  for d in c.get(k,[]):d['p']=[d['p'][0]-714,d['p'][1]-30]
 if c.get('ground_discharge_door'):c['ground_discharge_door']['p']=[c['ground_discharge_door']['p'][0]-714,c['ground_discharge_door']['p'][1]-30]
 return c

def floor_B_world(f,cores):
 f=translate_geoms(f,-714,-30);f['level']=f['floor']-1;f['label']=LABEL[f['level']]
 for s in f['stores']:
  for k in['entry','back_door','secondary_entry']:
   if k in s:s[k]=[s[k][0]-714,s[k][1]-30]
  for k in['main_route','front','secondary_front']:
   if k in s:s[k]=[[p[0]-714,p[1]-30]for p in s[k]]
 f['cores']=cores;return f

def csvwrite(p,head,rows):
 with Path(p).open('w',encoding='utf-8-sig',newline='')as fp:w=csv.writer(fp);w.writerow(head);w.writerows(rows)
 Path(str(p)+'.import').write_text('[remap]\n\nimporter="keep"\n')
