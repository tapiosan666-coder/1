from pathlib import Path
import math
from site_v2_common import read,Point,LineString,unary_union,lines,shape

def append_stock_probes(d,manifest,probes,local):
 baseline=read(Path(__file__).resolve().parents[1]/'source/baseline-stock-privacy.json');crop=shape(d['crop']).buffer(-.5)
 def ray(sid,p,line,y,height,kind):
  a=line.interpolate(max(0,line.length*.5-.03));b=line.interpolate(min(line.length,line.length*.5+.03));dx,dz=b.x-a.x,b.y-a.y;le=math.hypot(dx,dz)
  if le<1e-8:return
  n=(-dz/le,dx/le);aa=(p.x-n[0]*.35,p.y-n[1]*.35);bb=(p.x+n[0]*.35,p.y+n[1]*.35);probes.append({'id':sid+'-'+kind+'-'+str(height),'a':local(aa,y+height),'b':local(bb,y+height),'structural_only':True,'expected_hit':True,'kind':kind})
 for f in d['floors']:
  for s in f['stores']:
   if not crop.intersects(s['polygon']):continue
   old=baseline.get(s['id'])
   if old:
    wrong=unary_union(old['fronts']).intersection(old['backroom'].buffer(.025)).intersection(crop).difference(Point(s['back_door']).buffer(1.4));parts=[l for l in lines(wrong)if l.length>.3]
    if parts:
     line=max(parts,key=lambda l:l.length);p=line.interpolate(.5,normalized=True)
     for h in[.8,2.0]:ray(s['id'],p,line,f['height'],h,'stock_external_opaque_wall')
   boundary=s['backroom'].boundary.intersection(s['sales'].buffer(.0005)).intersection(crop).difference(Point(s['back_door']).buffer(1.4));parts=[l for l in lines(boundary)if l.length>.4]
   if parts:
    line=max(parts,key=lambda l:l.length);p=line.interpolate(.5,normalized=True)
    for h in[1.2,3.0]:ray(s['id'],p,line,f['height'],h,'stock_internal_opaque_divider')
