"""Confirmation views: original v4 geometry, explicit closed faces, flush finish overlay."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'docs/b-purpose-review-v4';OUT=ROOT/'docs/b-v4-final-confirmation'
sourcepath=ROOT/'tools/prepare_b_v4_views.py';s=sourcepath.read_text()
s=s.replace("OUT=ROOT/'docs/b-purpose-review-v4'","OUT=ROOT/'docs/b-v4-final-confirmation'").replace("raw=json.loads((OUT/'geometry.json').read_text())","raw=json.loads((ROOT/'docs/b-purpose-review-v4/geometry.json').read_text())")
s=s.replace("r=dec(raw)","r=dec(raw)\naudit=dec(json.loads((OUT/'frontage-audit.json').read_text()))\nCAMERA_CHECKS=[]")
s=s.replace("extent=p['void'].buffer(55).envelope","extent=p['void'].buffer(85 if j==0 else 70).envelope")
needle="  prism(f['guardrails'],y,y+1.2,'railglass')"
insert='''  # Closed belts were omitted in the earlier reference illustration: add their actual public faces.
  top={1:5.205,2:10.555,3:16.0}[f['floor']]
  for wall in audit['walls']:
   if wall['floor']!=f['floor']:continue
   prism(wall['line'].buffer(.125,cap_style=2).intersection(f['residual']),y,top,'closed')
  # Model the facility enclosure without implying that equipment operation has been verified.
  for core in r['cores']:
   frame=core['outline'].boundary.buffer(.125).intersection(core['outline'])
   door=next(d for d in core['doors']if d['id']=='CORE');ux,uz=door['axis'];x,z=door['p']
   cut=LineString([(x-ux*2,z-uz*2),(x+ux*2,z+uz*2)]).buffer(.6,cap_style=2)
   prism(frame.difference(cut),y,y+2.6,'plaster');prism(frame,y+2.6,top,'plaster')
  def surface(line,bottom,upper,mat,normal,offset=.006):
   for seg in ([line]if line.geom_type=='LineString'else getattr(line,'geoms',[])):
    if seg.is_empty or not seg.intersects(extent):continue
    points=list(seg.coords);m=mesh(mat)
    for a,b in zip(points,points[1:]):
     k=len(m['vertices']);m['vertices'] +=[[a[0]+normal[0]*offset-cx,a[1]+normal[1]*offset-cz,bottom],[b[0]+normal[0]*offset-cx,b[1]+normal[1]*offset-cz,bottom],[b[0]+normal[0]*offset-cx,b[1]+normal[1]*offset-cz,upper],[a[0]+normal[0]*offset-cx,a[1]+normal[1]*offset-cz,upper]];m['faces'].append([k,k+1,k+2,k+3])
  for zone in f.get('service_zones',[]):
   x,z=zone['entry'];u=zone['u'];n=(-u[1],u[0])
   if not f['public'].covers(Point(x+n[0]*.1,z+n[1]*.1)):n=(-n[0],-n[1])
   line=LineString([(x-u[0]*.75,z-u[1]*.75),(x+u[0]*.75,z+u[1]*.75)])
   surface(line,y,y+2.1,'staff',n)
  for finish in audit['treatments']:
   if finish['floor']!=f['floor']:continue
   line=finish['line'];n=finish['normal_to_public'];length=line.length
   for start in np.arange(3,length,6):
    a=line.interpolate(start);b=line.interpolate(min(start+3,length));surface(LineString([a,b]),y+.25,y+2.6,'finish',n)
   for position in([length*.25,length*.75]if length>30 else[length*.5]):
    pt=line.interpolate(position)
    if any(Point(z['entry']).distance(pt)<2.5 for z in f.get('service_zones',[])):continue
    a=line.interpolate(max(0,position-1.2));b=line.interpolate(min(length,position+1.2));surface(LineString([a,b]),y+.9,y+2.1,'finish_panels',n,.009)
    u=((b.x-a.x)/a.distance(b),(b.y-a.y)/a.distance(b))
    text='TIME COURT / INFO'if'P-T-SOUTH'in finish['routes']else 'WC / EV >'if'N-W'in finish['routes']else 'LIGHT COURT >'if'M-E2'in finish['routes']else 'TIME COURT >'if any(k in finish['routes']for k in['M-C2','SW-2'])else 'WING / INFO >'if'M-W'in finish['routes']else 'NORTH / INFO >'
    labels.append(dict(text=text,p=[pt.x+n[0]*.012-cx,pt.y+n[1]*.012-cz,y+1.45],u=u,n=n,finish_only=True))
'''
assert needle in s;s=s.replace(needle,insert+needle)
start=s.index(' eyes=[');end=s.index("(OUT/'view-model.json')",start)
s=s[:start]+''' # A → B → C uses actual entry streets, court edge, and onward street; upper floors are separate checks.
 routes={rr['id']:LineString(rr['points'])for rr in r['routes']}
 def at(id,d):q=routes[id].interpolate(d);return[q.x,q.y]
 sets=[[
  ('approach',1,at('M-W',20),[94,61],'M-W → 翼の広場'),('court',1,[64,67],[99,61],'翼の広場入口'),('exit',1,at('M-C1',20),[184,95],'翼 → 中央専門店街'),('upper2',2,[126,60],[75,61],'2F回廊から西側店頭'),('upper3',3,at('M-C1',12),[175,92],'3F中央専門店街へ')],
 [('approach',1,at('N-E',2),[285,78],'北専門店街 → 時の広場'),('court',1,[285,57],[285,83],'時の広場入口'),('exit',1,at('M-E1',17),[354,109],'時 → 東専門店街'),('upper2',2,[263,70],[306,75],'2F横断橋と東回廊'),('upper3',3,[306,80],[286,49],'3F北街側（他館は2F経由）')],
 [('approach',1,at('M-E2',18),[436,76],'東専門店街 → 光の広場'),('court',1,[410,88],[436,76],'光の広場入口'),('exit',1,at('SE-3',12),[435,126],'光 → 南東専門店街'),('upper2',2,[470,75],[435,76],'2F東核店前と曲面回廊'),('upper3',3,[470,68],[448,46],'3F案内側（A館へは2Fへ）')]]
 configs=sets[j]
 if j==0:configs +=[('nw-before',1,at('N-W',24),at('N-W',52),'北専門店街・閉鎖面補完/未仕上げ'),('nw-after',1,at('N-W',24),at('N-W',52),'北専門店街・仕上げ追補')]
 if j==2:configs +=[('approach-before',1,at('M-E2',18),[436,76],'東専門店街・閉鎖面補完/未仕上げ')]
 cameras=[]
 for id,level,nominal,target,caption in configs:
  free=r['floors'][level-1]['walkable'].buffer(-.5);point=Point(nominal)
  if not free.covers(point):point=nearest_points(free,point)[0]
  shift=point.distance(Point(nominal));assert shift<1.,(id,shift)
  height=r['floors'][level-1]['height']+1.65
  cameras.append(dict(id=id,p=[point.x-cx,point.y-cz,height],target=[target[0]-cx,target[1]-cz,height+1.0],lens=23,phase='before'if id.endswith('before')else'after',floor=level,caption=caption))
  CAMERA_CHECKS.append(dict(plaza=p['id'],id=id,floor=level,nominal=nominal,actual=[point.x,point.y],world=[point.x-714,height,point.y-30],eye_above_floor=1.65,adjustment_m=shift,within_half_metre_eroded_walk=True,phase='before'if id.endswith('before')else'after',caption=caption))
 courts.append(dict(id=p['id'],name=p['name'],groups=groups,props=props,labels=labels,cameras=cameras,model_origin=[cx,cz]))
(OUT/'camera-checks.json').write_text(json.dumps(CAMERA_CHECKS,ensure_ascii=False,indent=2))
''' +s[end:]
s=s.replace('from shapely.ops import triangulate,unary_union','from shapely.ops import triangulate,unary_union,nearest_points')
exec(compile(s,str(sourcepath),'exec'),{'__file__':str(sourcepath)})
