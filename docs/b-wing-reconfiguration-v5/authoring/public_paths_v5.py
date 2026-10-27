"""One west-to-east physical concourse route on each floor, plus store and service routes. Props remain real obstacles."""
from pathlib import Path
import sys,ast,math
sys.path.insert(0,str(Path(__file__).resolve().parent));from site_v2_common import *
import numpy as np,shapely
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
P=Path(__file__).resolve().parents[1];D=read(P/'source/design-v5.json');routes=read(P/'source/physical-routes.json');routes=[q for q in routes if not q['id'].startswith('PUBLIC-')];source=ast.parse((P/'authoring/paths_v5.py').read_text());fn=next(q for q in source.body if isinstance(q,ast.FunctionDef)and q.name=='path_in');exec(ast.unparse(fn));public=[]
for f in D['floors']:
 west=next(s for s in f['stores']if s['id'].endswith('-AW1'));east=next(s for s in f['stores']if s['id'].endswith('-AE1'))
 def outside(s):return(np.array(s['entry'])-np.array(s['n'])*.9).tolist()
 props=unary_union([o['geom'].buffer(.1)for o in f.get('furniture',[])]);free=f['public'].difference(props);pts=path_in(free,outside(west),outside(east));assert pts is not None,f['label']
 q={'id':'PUBLIC-'+f['label']+'-WEST-TO-EAST','kind':'entire public concourse west anchor -> all three plaza districts -> east anchor, source bench/planter footprints avoided','points':[[p[0]+429,f['height'],p[1]-46]for p in pts],'distance_m':LineString(pts).length};routes.append(q);public.append(q);print(q['id'],q['distance_m'],len(pts),flush=True)
write(P/'source/physical-routes.json',routes);write(P/'source/public-concourse-routes.json',public)
