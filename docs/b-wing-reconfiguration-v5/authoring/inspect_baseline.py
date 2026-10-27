from pathlib import Path
import sys,json,collections
sys.path.insert(0,str(Path(__file__).resolve().parent));from site_v2_common import *
import fitz
V4=Path('/workspace/FIND_YOURSELF-B-Time-Plaza-v4');P=Path(__file__).resolve().parents[1];D=read(V4/'source/design-extract.json');S=P/'source'
def path(g):return' '.join(' '.join('M'+' L'.join(f'{x:.3f},{z:.3f}'for x,z in ring.coords)+' Z'for ring in[p.exterior,*p.interiors])for p in polys(g))
for f in D['floors']:
 used=unary_union([f['public'],f['void'],f['shafts'],*[s['polygon']for s in f['stores']],*[c['outline']for c in f['cores']],*[z['polygon']for z in f.get('service_zones',[])],f.get('egress',Polygon())]);free=f['floor_plate'].difference(used);parts=sorted(polys(free),key=lambda p:-p.area);x0,z0,x1,z1=f['shell'].bounds;svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="2400" height="920" viewBox="{x0-3} {z0-10} {x1-x0+6} {z1-z0+18}"><rect x="{x0-3}" y="{z0-10}" width="{x1-x0+6}" height="{z1-z0+18}" fill="white"/><path d="{path(f["shell"])}" fill="#f3f4ed" stroke="#374a40" stroke-width=".4"/><path d="{path(f["public"])}" fill="#def0e2"/>']
 for s in f['stores']:
  svg.append(f'<path d="{path(s["polygon"])}" fill="#dadee1" stroke="#444" stroke-width=".12"/><path d="{path(s["backroom"])}" fill="#a8bbca"/>');q=s['polygon'].representative_point();svg.append(f'<text x="{q.x}" y="{q.y}" font-family="sans-serif" font-size="2.0" text-anchor="middle">{s["id"]}</text>');e=s['entry'];svg.append(f'<circle cx="{e[0]}" cy="{e[1]}" r=".4" fill="#124f2f"/>')
 for z in f.get('service_zones',[]):
  q=z['polygon'].representative_point();svg.append(f'<path d="{path(z["polygon"])}" fill="#cfb2d6" stroke="#65446f" stroke-width=".2"/><text x="{q.x}" y="{q.y}" font-family="sans-serif" font-size="3">{z["id"]}</text>')
 for i,q in enumerate(parts):
  if q.area<.5:continue
  c=q.representative_point();svg.append(f'<path d="{path(q)}" fill="#e6a378" fill-opacity=".75" stroke="#ad5527" stroke-width=".1"/><text x="{c.x}" y="{c.y}" font-family="sans-serif" font-size="3">U{i+1}:{q.area:.0f}</text>')
 svg.append('</svg>');name=S/f'baseline-{f["label"]}.svg';name.write_text(''.join(svg));doc=fitz.open(stream=name.read_bytes(),filetype='svg');doc[0].get_pixmap(matrix=fitz.Matrix(1,1),alpha=False).save(str(name.with_suffix('.png')))
 print(f['label'],'shell',f['shell'].area,'floor',f['floor_plate'].area,'public',f['public'].area,'shops',sum(s['polygon'].area for s in f['stores']),'service',sum(z['polygon'].area for z in f['service_zones']),'unowned',free.area,'parts',len(parts),flush=True)
 for i,q in enumerate(parts[:12]):print(i+1,round(q.area,2),tuple(round(x,1)for x in q.bounds),'ext-contact',round(q.boundary.intersection(f['shell'].boundary.buffer(.01)).length,1),flush=True)
