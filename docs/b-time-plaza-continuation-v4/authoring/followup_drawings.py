"""Dimensioned stock/annex studies and warehouse routes. No approved design overwrite."""
from pathlib import Path
import sys,json,html
sys.path.insert(0,'/workspace/1/tools');from site_v2_common import *
P=Path(__file__).resolve().parents[1];O=P/'source/followup';studies=read(O/'backroom-layout-proposals.json');D=read(P/'source/design-extract.json');byid={s['id']:s for f in D['floors']for s in f['stores']}
def path(g):return' '.join(' '.join('M'+' L'.join(f'{x:.3f},{z:.3f}'for x,z in ring.coords)+' Z'for ring in[p.exterior,*p.interiors])for p in polys(g))
for q in studies:
 s=byid[q['id']];poly=s['polygon'];show=poly.union(q['annex']);x0,z0,x1,z1=show.bounds;svg=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0-2} {z0-2} {x1-x0+4} {z1-z0+4}" width="900" height="700">']
 for g,col in [(poly,'#e9ece7'),(s['sales'],'#edf1eb'),(s['backroom'],'#c5d9cc'),(q['annex'],'#efc48b'),(q['rectangle'],'#92b8d1')]:svg.append(f'<path d="{path(g)}" fill="{col}" fill-opacity=".85" stroke="#52635c" stroke-width=".08"/>')
 # Existing portals stay fixed, label equipment dimensions directly in the proposal.
 for key,col in [('entry','#b44333'),('back_door','#33688b')]:
  e=s[key];svg.append(f'<circle cx="{e[0]}" cy="{e[1]}" r=".28" fill="{col}"/>')
 if not q['rectangle'].is_empty:
  pp=q['rectangle'].representative_point();svg.append(f'<text x="{pp.x}" y="{pp.y}" font-family="sans-serif" font-size=".65" text-anchor="middle">{q["rotation_deg"] or 0} deg / work module</text>')
 svg.append('</svg>');(O/(q['id']+'-stock-proposal.svg')).write_text(''.join(svg))
# Whole-floor route example from source stores to corrected warehouse doors.
R=read(O/'warehouse-route-polylines.json');F=read(O/'coordinate-role-source.json')
for f in F['floors']:
 if f['wing']!='B'or f['level']not in[0,1,2]:continue
 x0,z0,x1,z1=f['shell'].bounds;svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="650" viewBox="{x0-4} {z0-6} {x1-x0+8} {z1-z0+12}"><path d="{path(f["shell"])}" fill="#eeeee7" stroke="#6a766b" stroke-width=".3"/><path d="{path(f["public"])}" fill="#fff"/>']
 for z in f['service_zones']:
  svg.append(f'<path d="{path(z["polygon"])}" fill="'+('#afd0bd'if'共用倉庫'in z['name']else'#b8bfc1')+'" stroke="#63766a" stroke-width=".2"/>');e=z['entry'];svg.append(f'<circle cx="{e[0]}" cy="{e[1]}" r="1.3" fill="#b04032"/><text x="{e[0]}" y="{e[1]-2}" font-family="sans-serif" font-size="3">{z["id"]}</text>')
 rr=[q for q in R if q['floor']==f['label']];rr=sorted(rr,key=lambda q:q['distance_m']);examples=[rr[0],rr[len(rr)//2],rr[-1]]
 for q in examples:
  pts=q['world_polyline'];svg.append('<polyline points="'+' '.join(f'{x},{z}'for x,z in pts)+'" fill="none" stroke="#9b6941" stroke-width=".6"/>');x,z=pts[0];svg.append(f'<text x="{x}" y="{z-2}" font-family="sans-serif" font-size="3">{q["id"]}: {q["distance_m"]:.1f}m</text>')
 svg.append('</svg>');(O/(f['label']+'-warehouse-route-plan.svg')).write_text(''.join(svg))
print('DRAWINGS',len(studies),'stock studies +3 corrected warehouse plans')
