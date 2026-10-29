from pathlib import Path
import sys,math,json
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'))
from site_v2_common import *
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as Patch
OUT=Path('/workspace/v17-review/proposals');OUT.mkdir(exist_ok=True)
F=read(P/'source/v11/floors-updated.json');f=next(f for f in F if f['wing']=='C'and f['level']==3)
clear=f['public'].intersection(f['floor_plate']).difference(f['shafts'].buffer(7)).difference(unary_union([c['outline'].buffer(7)for c in f['cores']])).buffer(-4)
chosen=None
for po in sorted(polys(clear),key=lambda p:-p.area):
 minx,minz,maxx,maxz=po.bounds
 for x in np.arange(minx+6,maxx-6,3)if False else range(math.ceil(minx+6),math.floor(maxx-6),3):
  for z in range(math.ceil(minz+8),math.floor(maxz-8),3):
   if po.covers(box(x-6,z-8,x+6,z+8)):chosen=(x,z);break
  if chosen:break
 if chosen:break
# No valid 12x16m contiguous garden footprint under these explicit clearances.
# Do not invent a roof location: the detail is local and shown separately from the actual roof.
water=box(-6,-10,6,10);walk=box(-10,-14,10,14).difference(water.buffer(1));candidate={'status':'UNAPPROVED DESIGN ONLY; site fit NOT established; no scene implementation','coordinate_system':'Detail-local metres; NO world placement assigned','site_fit_for_60m2_with_3m_walk':chosen is not None,'water_polygon_local':water,'dry_loop_local':walk,'water_area_m2':240,'depth_options':[{'depth_m':d,'water_mass_tonnes':240*d,'water_load_kPa':d*9.81}for d in[.04,.08,.12]],'dry_loop_width_m':3,'structural_capacity_verified':False,'waterproofing_verified':False,'overflow_and_drainage_verified':False,'escape_traffic_verified':False,'actual_route_to_EV_verified':False,'site_screen':'Axis-aligned 12x16m footprint search, public AND structural floor, 4m inward margin and 7m core/shaft clearance; negative result is not proof of impossibility under all orientations','conditions':['240m2 is a concept module only; the current public roof is fragmented and no location is approved','Do not fill roof voids or displace tenant/escape paths without a separate structural proposal','Structural engineer must check water, lining, planting, people, sloshing and foundations','Resolve supply, emergency overflow, drainage, maintenance and accessible dry circuit','RF-SUPPORT-16 remains UNAPPROVED','Normal and F4 roof geometry unchanged']}
write(OUT/'C-roof-water-garden-design.json',candidate)
fig,ax=plt.subplots(figsize=(12,9))
def draw(g,color,alpha=1):
 for p in polys(g):ax.add_patch(Patch(list(p.exterior.coords),facecolor=color,edgecolor='#454c50',linewidth=.4,alpha=alpha))
draw(f['floor_plate'],'#dadbd5');draw(f['void'],'#ffffff');draw(f['public'],'#f2eee1',.7)
for s in f['stores']:draw(s['polygon'],'#b9bdaf')
for c in f['cores']:draw(c['outline'],'#9b786d')
# Roof image shows only real geometry and screened free regions, not a fictional installed pond.
draw(clear,'#b7cfa2',.8)
ax.text(.02,.98,'DESIGN ONLY / NO WORLD PLACEMENT\nPublic roof + real floor screened with declared clearances.\nNo 12 x 16 m candidate found in the tested axis-aligned search.\nThis does not establish structural capacity.',transform=ax.transAxes,va='top',fontsize=9,bbox={'facecolor':'white','alpha':.95})
ax.set_aspect('equal');ax.autoscale_view();ax.set_title('C RF: candidate on actual roof plan / not implemented');ax.set_xlabel('Plan X metres (Godot +429)');ax.set_ylabel('Plan Z metres (Godot -46)');fig.savefig(OUT/'C-roof-water-garden-design.pdf');fig.savefig(OUT/'C-roof-water-garden-design.svg');plt.close(fig)
fig,ax=plt.subplots(figsize=(8,9));draw(walk,'#b2c89c');draw(water,'#77b0be');ax.set_aspect('equal');ax.autoscale_view();ax.set_title('Concept detail only / 240 m2 water + 3 m dry loop');ax.set_xlabel('Local metres: no world position assigned');ax.text(.02,.02,'0.08m water = 19.2 tonnes, excluding all other loads.\nSupport, drainage, accessibility, emergency escape: UNVERIFIED.',transform=ax.transAxes,fontsize=9);fig.savefig(OUT/'C-water-garden-local-detail.pdf');plt.close(fig)
print('WATER_GARDEN_SITE_UNCONFIRMED',len(polys(clear)))
