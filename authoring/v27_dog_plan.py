import json,hashlib,math
from pathlib import Path
root=Path(__file__).resolve().parents[1]
read=lambda p:json.loads((root/p).read_text())
write=lambda p,d:(root/p).write_text(json.dumps(d,ensure_ascii=False,indent=2))
dx,dz=-76.,-41.
def geo(g):
 if g.get('type')=='GeometryCollection':
  for x in g['geometries']:geo(x)
 elif 'coordinates'in g:
  def rec(c):
   if c and isinstance(c[0],(int,float)):c[0]+=dx;c[1]+=dz
   else:
    for q in c:rec(q)
  rec(g['coordinates'])
d=read('source/v25/commons.json')
for key in ['zones','instances','pads','boards','gates']:
 for r in d[key]:
  if r.get('zone')!='C-DOG-RUN' and r.get('id')!='C-DOG-RUN':continue
  for k in ['p','preferred']:
   if k in r:
    r[k][0]+=dx;r[k][2 if len(r[k])==3 else 1]+=dz
  for k in ['footprint','geometry']:
   if k in r:geo(r[k])
route=[[-118.5,0.,-289.5],[-97.5,0.,-289.5],[-76.5,0.,-288.],[-77.,0.,-266.],[-77.,0.,-259.2]]
strips=[]
for a,b in zip(route,route[1:]):
 vx,vz=b[0]-a[0],b[2]-a[2];n=math.hypot(vx,vz);ux,uz=-vz/n*.85,vx/n*.85
 strips.append([[[a[0]+ux,a[2]+uz],[b[0]+ux,b[2]+uz],[b[0]-ux,b[2]-uz],[a[0]-ux,a[2]-uz],[a[0]+ux,a[2]+uz]]])
for r in d['pads']:
 if r['id']=='C-ACCESS-DOG':r['geometry']={'type':'MultiPolygon','coordinates':strips};r['y']=.035
garden=[[-101,-251],[-101.5598855980894,-245.12120122006135],[-89.6121566151743,-231.4092466720869],[-46,-236],[-71,-261],[-101,-251]]
d['pads'].append(dict(id='C-L3-LAWN',zone='C-DOG-RUN',geometry={'type':'Polygon','coordinates':[garden]},y=.012,material='turf',activation='always',kind='既存L-3庭園の芝生仕上げ',structural_floor=False))
write('source/v27/commons.json',d)
write('source/v27/dog-access.json',dict(route_world=route,target=[-77.,-259.2],baseline_old_target=[-1.,-218.2],status='PENDING_REVALIDATION',enclosure_translation=[dx,dz],real_garden_id='L-3',original_garden_world=[[-101,-251],[-101.5598855980894,-245.12120122006135],[-89.6121566151743,-231.4092466720869],[-46,-236],[-71,-261],[-101,-251]],reason='旧柵内の舗装と建物張出しを避け、実在するL-3緑地内へ移設。店舗や建物は移設しない',new_enclosed_bounds=[-89,-254.6,-65,-235.4],old_enclosed_bounds=[-13,-213.6,11,-194.4]))
w=read('source/v22/wayfinding.json');w['source_hashes']['source/v27/commons.json']=hashlib.sha256((root/'source/v27/commons.json').read_bytes()).hexdigest();write('source/v27/wayfinding.json',w)
# Old public guide artwork has no dog-run icon; interactive map is refreshed from commons zones.
print('Dog facilities translated',dx,dz,'into actual L-3 garden; route regenerated')
