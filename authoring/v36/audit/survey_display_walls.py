"""Choose long rear/side wall segments inside a leased sales polygon, away from entry openings."""
import json,math,subprocess
from pathlib import Path
import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('output',type=Path,help='Candidate JSON for the Godot support probe')
output=parser.parse_args().output
base=Path(__file__).resolve().parents[3]/'source'
plan=json.loads(subprocess.run(['zstd','-dc'],input=(base/'v294/retail-plan.json.zst').read_bytes()[8:],capture_output=True,check=True).stdout)
poses=json.loads(Path(__file__).with_name('store-cameras.json').read_bytes())
by={s['id']:s for s in plan['stores']}
allrows=[]
for shot in poses:
    s=by[shot['id']]; geom=s['sales_world']
    parts=geom.get('geometries',[geom])
    polys=[poly for part in parts for poly in ([part['coordinates']] if part['type']=='Polygon' else part.get('coordinates',[]) if part['type']=='MultiPolygon' else [])]
    px,_,pz=shot['entry'];nx,_,nz=shot['inward'];cs=[]
    for poly in polys:
        ring=poly[0]
        signed=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(ring,ring[1:]))
        for a,b in zip(ring,ring[1:]):
            dx,dz=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dz)
            if length<4.7:continue
            dx/=length;dz/=length
            ux,uz=(-dz,dx) if signed>0 else (dz,-dx)
            if ux*nx+uz*nz>.43:continue
            for fraction in [.32,.62,.5]:
                cx,cz=a[0]+fraction*(b[0]-a[0]),a[1]+fraction*(b[1]-a[1]);depth=(cx-px)*nx+(cz-pz)*nz
                if depth<2.4:continue
                sight=math.hypot(cx-px,cz-pz)
                # Prefer readily visible walls facing the visitor. Avoid a forty-metre sign inside a large anchor.
                score=depth/sight - .012*sight - .3*(ux*nx+uz*nz) + min(length,10)*.018
                width=min(7.2, length*min(fraction,1-fraction)*2-.8, max(2.8,s['sales_m2']**.5*.36))
                cs.append((score,dict(p=[round(cx,4),s['height'],round(cz,4)],normal=[round(ux,6),round(uz,6)],width=round(width,3))))
    cs.sort(key=lambda e:-e[0]);allrows.append(dict(id=s['id'],category=s['category'],brand=s['brand'],wing=s['wing'],floor=s['floor'],entry=shot['entry'],candidates=[c[1] for c in cs[:18]]))
output.write_text(json.dumps(allrows,separators=(',',':')))
