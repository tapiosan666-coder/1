from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parents[2];sys.path.insert(0,str(P/'authoring'));from site_v2_common import *
p=read(P/'source/v22/retail-plan.json');fail={r['id']for r in read('/workspace/v22-review/interiors-customer/v22-interior-route-physics.json')['failed']};out=[]
for s in p['stores']:
 if s['id']not in fail:continue
 g=s['sales_world'].buffer(-.38);xmin,zmin,xmax,zmax=g.bounds;cells=[];step=.6
 for ix in range(math.ceil((xmax-xmin)/step)+1):
  for iz in range(math.ceil((zmax-zmin)/step)+1):
   if g.covers(Point(xmin+ix*step,zmin+iz*step)):cells.append([ix,iz])
 out.append({'id':s['id'],'height':s['height'],'entry':s['entry_world'],'cells':cells,'origin':[xmin,zmin],'step_m':step,'walk_polygons':[[list(map(list,a.exterior.coords))]+[list(map(list,h.coords))for h in a.interiors]for a in polys(g)]})
write(P/'source/v22/interior-route-grids.json',out);print('GRIDS',len(out))
