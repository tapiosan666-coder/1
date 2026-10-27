"""Move the actual opening on its existing customer street, not just the route target."""
from pathlib import Path
import sys,ast,math,copy
sys.path.insert(0,str(Path(__file__).resolve().parent));from site_v2_common import *
from shapely.ops import linemerge
import numpy as np
P=Path(__file__).resolve().parents[1];D=read(P/'source/design-v6.json');original={s['id']:s for f in read((Path(__file__).resolve().parents[1]/'source/baseline-v4.json'))['floors']for s in f['stores']}
def poly(g):return unary_union(polys(g))
def merge(g):return g if g.geom_type=='LineString'else linemerge(g)
source=ast.parse((P/'authoring/complete_v5.py').read_text());fn=next(n for n in source.body if isinstance(n,ast.FunctionDef)and n.name=='door_for');code=ast.unparse(fn).replace('buffer(-0.29)','buffer(-0.46)').replace('n * 0.9','n * 1.0');exec(code)
changes=[]
for f in D['floors']:
 for s in f['stores']:
  a=np.array(s['entry'])+np.array(s['n']);good=s['sales'].buffer(-.44).buffer(.002).covers(Point(a))
  if good and s['id']!='B3-046':continue
  t=copy.copy(s);t['polygon']=s['sales'];q=door_for(t,f)
  if q is None:print('DOOR_UNRESOLVED',s['id']);continue
  _,e,u,n,w,front=q;changes.append({'id':s['id'],'old_actual_entry':s['entry'],'new_actual_entry':e,'width_m':w,'reason':'customer doorway approach must connect to the 0.88m-clear sales route'});s['entry']=e;s['u']=u;s['n']=n;s['door_width_m']=w;s['frontage_m']=front;s['front']=[(e[0]+u[0]*a,e[1]+u[1]*a)for a in[-w/2,w/2]]
D.setdefault('actual_frontage_revisions',[]).extend(changes);write(P/'source/design-v6.json',D);print('ACTUAL_FRONTAGE_REVISIONS',changes)
