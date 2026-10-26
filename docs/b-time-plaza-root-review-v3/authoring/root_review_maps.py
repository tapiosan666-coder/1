from pathlib import Path
import sys,xml.etree.ElementTree as ET
sys.path.insert(0,'/workspace/1/tools');from site_v2_common import *
ET.register_namespace('', 'http://www.w3.org/2000/svg')
P=Path(__file__).resolve().parents[1];O=P/'source/root-gap-review';D=read(R/'docs/site-correction-v3/geometry.json');proposal=read(O/'refined-enclosure-proposals.json')
def path(g):return' '.join(' '.join('M'+' L'.join(f'{x:.5f},{z:.5f}'for x,z in ring.coords)+' Z'for ring in [p.exterior,*p.interiors])for p in polys(g))
for floor in ['B1','1F','2F','3F','RF']:
 old=ET.parse(O/f'B-{floor}-ownership.svg');root=old.getroot()
 for child in list(root):
  if child.get('fill')=='#668eaf':root.remove(child)
 for c in proposal['changes']:
  if c['floor']==floor:ET.SubElement(root,'{http://www.w3.org/2000/svg}path',{'d':path(c['assigned_pocket']),'fill':'#668eaf'})
 old.write(O/f'B-{floor}-refined.svg',encoding='unicode')
for c in proposal['changes']:
 f=next(f for f in D['floors']if f['wing']=='B'and f['level']==c['level']);s=next(s for s in f['stores']if s['id']==c['store']);x0,z0,x1,z1=c['new_polygon'].bounds;m=2
 for after in [False,True]:
  p=c['new_polygon']if after else c['old_polygon'];stock=c['new_backroom']if after else c['old_backroom'];parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0-m} {z0-m} {x1-x0+2*m} {z1-z0+2*m}" width="1000" height="900"><rect x="{x0-m}" y="{z0-m}" width="{x1-x0+2*m}" height="{z1-z0+2*m}" fill="#faf9f5"/><path d="{path(f["public"].intersection(box(x0-m,z0-m,x1+m,z1+m)))}" fill="#d1e4dc"/><path d="{path(p)}" fill="#efe2c7" stroke="#47584c" stroke-width=".09"/><path d="{path(stock)}" fill="#b5c6d0" stroke="#647888" stroke-width=".07"/>']
  if after:parts.append(f'<path d="{path(c["nonoccupiable_enclosure_allowance"])}" fill="#c6b4aa"/>')
  else:parts.append(f'<path d="{path(c["assigned_pocket"])}" fill="#d99974" stroke="#a7674d" stroke-width=".07"/>')
  for key,col in[('old_entry','#b44738'),('old_back_door','#a78837')]:x,z=c[key];parts.append(f'<circle cx="{x}" cy="{z}" r=".23" fill="{col}"/>')
  parts.append('</svg>');(O/(c['store']+('-after.svg'if after else'-before.svg'))).write_text(''.join(parts))
print('ROOT_MAPS',len(proposal['changes']))
