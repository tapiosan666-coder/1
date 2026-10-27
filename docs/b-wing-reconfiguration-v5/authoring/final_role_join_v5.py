"""Close only the final numerical area-account seam at actual wall footprints. Does not alter the slab or any generated mesh."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent));from site_v2_common import *
P=Path(__file__).resolve().parents[1];p=P/'source/design-v5.json';D=read(p)
for f in D['floors']:
 prev=unary_union([q['polygon']for q in f['floor_roles'][:-1]]);last=f['floor_roles'][-1];new=f['floor_plate'].difference(prev);delta=new.symmetric_difference(last['polygon']);assert delta.area<1e-5
 walls=unary_union([s['polygon'].boundary.buffer(.13)for s in f['stores']]+[z['polygon'].boundary.buffer(.13)for z in f['service_zones']]+[f['building_envelope_v5'].boundary.buffer(.13)]);assert delta.difference(walls.buffer(.001)).area<1e-7;last['polygon']=new;last['area_m2']=new.area
write(p,D)
