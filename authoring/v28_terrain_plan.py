import json,math,hashlib
from pathlib import Path
r=Path(__file__).resolve().parents[1]
p=json.loads((r/'source/v27/dog-access.json').read_text());garden=p['original_garden_world'][:-1]
neck=[[-77.95,-288],[-76.05,-288],[-76.05,-254.5],[-77.95,-254.5]]
fences=[[-89,-254.6,-65,-254.6],[-89,-235.4,-65,-235.4],[-89,-254.6,-89,-235.4],[-65,-254.6,-65,-235.4],[-77.9,-258.2,-77.9,-254.6],[-76.1,-258.2,-76.1,-254.6],[-77.9,-258.2,-76.1,-258.2]]
def dist(x,z,a,b):
 vx,vz=b[0]-a[0],b[1]-a[1];t=max(0,min(1,((x-a[0])*vx+(z-a[1])*vz)/(vx*vx+vz*vz)));return math.hypot(x-a[0]-t*vx,z-a[1]-t*vz)
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def height(x,z):
 d=min(dist(x,z,a,b)for a,b in zip(garden,garden[1:]+garden[:1]));h=-.012+.032*smooth(0,3.2,d)
 fd=min(dist(x,z,q[:2],q[2:])for q in fences);h*=1+(smooth(.12,1.05,fd)-1)*smooth(0,.15,d)
 if -78.15<x<-75.85 and z< -254.5:
  h=.04+(-.012-.04)*smooth(-288.,-280.,z) if z< -280 else -.012*(1-smooth(-264.,-258.2,z))
 return h
c=json.loads((r/'source/v27/commons.json').read_text())
for q in c['instances']:
 if q.get('zone')=='C-DOG-RUN':q['p'][1]=height(q['p'][0],q['p'][2])
for q in c['gates']:q['p'][1]=height(q['p'][0],q['p'][2])
for q in c['pads']:
 if q['id']in ['C-DOG-TURF','C-L3-LAWN','C-ACCESS-DOG']:q['terrain_replacement_v28']=True
for wing,pref in [('B',[7.,30.87]),('C',[-103.2036425,-220.4416535])]:
 c['zones'].append(dict(id=wing+'-ENTRANCE-V28',wing=wing,level=0,floor='1F',height=.04,title=wing+'館 二重自動ドア・出入口',preferred=pref,store_id=None,activation='always',role='entrance',placed_models=[],display_surfaces=[],implemented=True))
plan=dict(garden=garden,neck=neck,fence_segments=fences,grid_m=.5,base_boundary_y=-.012,maximum_crown_y=.02,closed_gate_y=0.,same_dog_position=True,policy='Remove old outdoor ground faces and colliders inside garden+neck. One graded visible mesh is the collision source. No rectangular overlay.',authoritative_enclosure=[-89,-254.6,-65,-235.4])
for name,d in [('commons',c),('terrain-plan',plan)]: (r/f'source/v28/{name}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2))
w=json.loads((r/'source/v27/wayfinding.json').read_text());w['source_hashes']['source/v28/commons.json']=hashlib.sha256((r/'source/v28/commons.json').read_bytes()).hexdigest();
for name in ['terrain-plan','entrances','scene-design']:
 path=r/f'source/v28/{name}.json'
 if path.exists():w['source_hashes'][f'source/v28/{name}.json']=hashlib.sha256(path.read_bytes()).hexdigest()
(r/'source/v28/wayfinding.json').write_text(json.dumps(w,ensure_ascii=False,indent=2))
print('same L-3 location; unified terrain and grade plan authored')
