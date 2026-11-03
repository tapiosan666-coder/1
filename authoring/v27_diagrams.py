"""Readable measured plans and sections. Diagrams are not Godot screenshots."""
import json,math,html,os
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=Path(os.environ.get('FY27_REVIEW_OUTPUT',root/'evidence/v27-review'))/'diagrams';out.mkdir(exist_ok=True)
read=lambda p:json.loads((root/p).read_text())
font='Arial,sans-serif'
def wrap(title,body,view='-330 -100 600 250'):
 return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view}"><style>text{{font-family:{font};fill:#132f3b}}.small{{font-size:4px}}</style><rect x="-2000" y="-2000" width="4000" height="4000" fill="#f5f5ed"/>{body}</svg>'
def rings(g):
 if not isinstance(g,list)or not g:return []
 if isinstance(g[0],list)and g[0]and isinstance(g[0][0],(int,float)):return [g]
 return sum((rings(q)for q in g),[])
def path(geom,colour,stroke='none',offset=(429,-46)):
 b=[]
 for ring in rings(geom):
  pts=' '.join(f'{p[0]+offset[0]:.3f},{p[1]+offset[1]:.3f}'for p in ring);b.append(f'<polygon points="{pts}" fill="{colour}" stroke="{stroke}" stroke-width=".25"/>')
 return ''.join(b)
inv=read('source/v27/equipment-inventory.json')['records'];data=read('source/v15/ES-site-proposal.json');old=read('source/scene-manifest.json')['escalators'];ev=[e for e in read('source/elevators-v7.json')if e['wing']=='B']
for f in read('source/v22/map-data-integrated.json'):
 if f['wing']!='B':continue
 b=path(f['floor'],'#d3d1c3')+path(f['public'],'#f9f9f4')
 for item in f['items']:
  if item['kind']=='店舗':b+=path(item['geometry'],'#bac5c3','#81969b')
  elif item['kind']=='階段':b+=path(item['geometry'],'#c29bc1','#725a72')
 for e in old+data['escalators']:
  if f['level'] not in e['levels']:continue
  x,_,z=e['c'];u=e['u'];lat=[u[1],-u[0]];pts=[[x+u[0]*s+lat[0]*t,z+u[1]*s+lat[1]*t]for s,t in [(-7.35,-.9),(-7.35,.9),(7.35,.9),(7.35,-.9)]]
  retired=e['id']in data['retired_machine_ids'];colour='#ffffff'if retired else '#1b8cbb'if e['id'].startswith('B-WEST')else'#d7a344'
  b+=path(pts,colour,'#ba554c'if retired else'#23576b',offset=(0,0))
  if retired:b+=f'<path d="M{x-3},{z-3}l6,6m-6,0l6,-6" stroke="#c34e47" stroke-width=".5"/>'
 for e in ev:
  x,_,z=e['center'];b+=f'<rect x="{x-2}" y="{z-2}" width="4" height="4" fill="#4d8b65"/><text x="{x+3}" y="{z}" class="small">{e["id"]}</text>'
 b+=f'<text x="-321" y="-81" font-size="9">B {f["label"]} / y={f["height"]} m / measured v26 plan, v27 retained structure</text><text x="-321" y="-72" font-size="5">BLUE: continuous WEST ES / GOLD: independent ES retained / GREEN: EV / PURPLE: stairs / RED X: retired in v26, remains absent</text><text x="-321" y="-63" font-size="4">No equipment relocation. B1 access via retained EV and stairs. NORTH = -Z. Architectural engineering remains unapproved.</text>'
 (out/f'B-{f["label"]}-plan.svg').write_text(wrap('',b))
# Measured detailed west station plans (below the next floor, corresponding native views supplied separately).
for i,y in enumerate([0,5.525,10.875,16.4]):
 b='<rect x="-204" y="-26.5" width="24" height="22" fill="#dddacb" stroke="#56646b" stroke-width=".12"/>'
 for e in data['escalators']:
  if i not in e['levels']:continue
  x,_,z=e['c'];u=e['u'];pts=[[x+u[0]*s,z+t]for s,t in [(-7.35,-.88),(-7.35,.88),(7.35,.88),(7.35,-.88)]]
  b+=path(pts,'#669caf','#294f5f',offset=(0,0));b+=f'<text x="-195.5" y="{z+.2}" font-size=".55">{e["direction"]} {e["levels"][0]+1}F-{e["levels"][1]+1 if e["levels"][1]!=3 else "R"}F</text>'
 for t in data['transfers']:
  if abs(t['points'][0][1]-y)<.01:
   pts=' '.join(f'{p[0]},{p[2]}'for p in t['points']);b+=f'<polyline points="{pts}" stroke="#42845d" stroke-width=".18" fill="none"/>'
 b+=f'<text x="-204" y="-28" font-size=".8">B WEST / {["1F","2F","3F","RF"][i]} / unchanged structural footprint</text>'
 (out/f'B-west-{i+1}-detail.svg').write_text(wrap('',b,'-206 -30 29 28'))
# Section from the actual generated profile.
for i,rise in enumerate([5.525,5.35,5.525]):
 b='<path d="M-9,1 L9,1" stroke="#a9aa9d" stroke-width=".15"/><path d="M5.9,-'+str(rise)+' L9,-'+str(rise)+'" stroke="#a9aa9d" stroke-width=".25"/>'
 p=[(-7.35,0),(-5.9,0),(5.9,-rise),(7.35,-rise)];bottom=[(x,y+.91)for x,y in p]
 b+='<polygon points="'+' '.join(f'{x},{y}'for x,y in p+bottom[::-1])+'" fill="#75867b"/>'
 for k in range(10):
  x=-5.9+k*11.8/9;y=-rise*(x+5.9)/11.8;b+=f'<path d="M{x},{y+.15}L{x},{y+.91}" stroke="#344d43" stroke-width=".014"/>'
 b+='<text x="-8" y="-7" font-size=".42">Actual ES section: run 11.80 m / rise '+str(rise)+' m</text><text x="-8" y="-6.4" font-size=".32">0.91 m closed soffit depth / 1.76 m skin width / 12 mm cassette joints</text><text x="-8" y="2" font-size=".32">Existing ramp collision + machinery housing retained. New skin has no duplicate ramp collider.</text><text x="-8" y="2.6" font-size=".32">Side guards exclude low-headroom pockets. Supports/structural capacity not certified.</text>'
 (out/f'B-section-{i+1}.svg').write_text(wrap('',b,'-9 -8 18 12'))
# Dog-run measured plan, translated into actual L-3 garden.
garden=read('source/v27/dog-access.json')['original_garden_world']
b=path(garden,'#a4b97d','#6a7d51',offset=(0,0))
b+='<rect x="-89" y="-254.6" width="24" height="19.2" fill="#779a51" stroke="#304b38" stroke-width=".18"/>'
for x in range(-88,-65):
 for z in range(-254,-235,2):b+=f'<path d="M{x},{z}l.1,-.22m0,.22l-.1,-.15" stroke="#526c39" stroke-width=".025"/>'
b+='<rect x="-77.9" y="-258.2" width="1.8" height="3.6" fill="#b1ad99" stroke="#304b38" stroke-width=".10"/>'
for z,label in [(-258.2,'outer gate'),(-254.6,'inner gate')]:b+=f'<path d="M-77.6,{z}H-76.4" stroke="#db9a42" stroke-width=".15"/><text x="-83" y="{z-.3}" font-size=".6">{label}</text>'
for x,z,w,d,label in [(-84,-239,2.4,.6,'bench'),(-70,-239,2.4,.6,'bench'),(-69,-250,1.2,.5,'water / wash'),(-73.5,-253.8,.42,.42,'waste'),(-74.5,-256.1,.86,.54,'rules')]:
 b+=f'<rect x="{x-w/2}" y="{z-d/2}" width="{w}" height="{d}" fill="#c69f67"/><text x="{x+.2}" y="{z-.5}" font-size=".52">{label}</text>'
b+='<text x="-91" y="-262" font-size=".85">C DOG RUN / L-3 REAL GARDEN</text><text x="-88" y="-245" font-size=".9">24 x 19.2 m grass running field</text><text x="-91" y="-232" font-size=".46">Public approach → outer → 3.6 m vestibule → inner → grass. Gates interlocked.</text>'
(out/'C-dog-plan.svg').write_text(wrap('',b,'-93 -265 32 36'))
b=path(garden,'#9fbf79','#537a4b',offset=(0,0))+path([[-89,-254.6],[-65,-254.6],[-65,-235.4],[-89,-235.4]],'#487847',offset=(0,0))
route=read('source/v27/dog-access.json')['route_world'];pts=' '.join(f'{p[0]},{p[2]}'for p in route)
b+=f'<polyline points="{pts}" fill="none" stroke="#b07336" stroke-width="1.3"/>'
for x,z,label in [(-77,-245,'DOG RUN / L-3'),(-111,-312,'KIDS retained'),(-88,-324,'FOOD TRUCK retained'),(-1,-204,'OLD DOG RUN: removed')]:
 b+=f'<circle cx="{x}" cy="{z}" r="2" fill="#173b45"/><text x="{x+3}" y="{z}" font-size="3">{label}</text>'
b+='<text x="-148" y="-337" font-size="4">C courtyard: actual WORLD x/z / facilities and new walking route</text>'
(out/'C-courtyard-context.svg').write_text(wrap('',b,'-152 -343 185 162'))
print('diagrams',len(list(out.glob('*.svg'))))
