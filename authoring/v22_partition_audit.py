"""Independent whole-floor ownership/shared-boundary audit. Diagnostic candidates are not declared architectural defects."""
from pathlib import Path
import sys,json,math,collections
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import *
from shapely.validation import make_valid,explain_validity
from shapely.strtree import STRtree
F=read(P/'source/v11/floors-updated.json');W=lambda g:affinity.translate(g,429,-46);invalid=[];joints=[];floorrows=[];residuals=[];narrow=[]
def valid(g):return g if g.is_valid else make_valid(g)
for f in F:
 ids=[s['id']for s in f['stores']];plots=[]
 for s in f['stores']:
  for name in ['polygon','sales','backroom','wall_solids','aisles']:
   g=s.get(name)
   if g is not None and not g.is_valid:invalid.append({'floor':f['wing']+f['label'],'store_id':s['id'],'field':name,'reason':explain_validity(g),'original_area':g.area,'valid_area':make_valid(g).area,'source_changed':False,'runtime_footprint_repaired_for_layout':name in ['sales','aisles']})
  plots.append(valid(s['polygon']))
 tree=STRtree(plots);overlap=0.;shared=0.
 for i,a in enumerate(plots):
  for j in tree.query(a.buffer(.06)):
   if j<=i:continue
   b=plots[j];length=a.boundary.intersection(b.boundary).length;ov=a.intersection(b).area;gap=a.distance(b)
   if length>.15 or ov>.0001 or .0001<gap<.06:
    geom=a.boundary.intersection(b.boundary)if length else nearest_points(a,b)[0];p=geom.representative_point();joints.append({'wing':f['wing'],'floor':f['label'],'store_A':ids[i],'store_B':ids[j],'world_xz':[p.x+429,p.y-46],'shared_length_m':length,'plot_overlap_m2':ov,'closest_gap_m':gap,'classification':'EXACT_SHARED_BOUNDARY'if length and ov<.0001 else'OVERLAP_REQUIRES_REVIEW'if ov>.0001 else'NEAR_BOUNDARY_REQUIRES_3D_REVIEW','physical_seam_verified':False});overlap+=ov;shared+=length
 public=valid(f['public']);plate=valid(f['floor_plate']);plotunion=unary_union(plots);core=valid(f.get('core_free',Polygon()));res=plate.difference(plotunion.union(public).union(core));explicit=valid(f.get('residual',Polygon()));unassigned=res.difference(explicit)
 for i,p in enumerate(polys(unassigned)):
  if p.area<.02:continue
  q=p.representative_point();residuals.append({'id':f['wing']+f['label']+'-UNOWNED-'+str(i),'wing':f['wing'],'floor':f['label'],'world_xz':[q.x+429,q.y-46],'area_m2':p.area,'minimum_rotated_rectangle_area_m2':p.minimum_rotated_rectangle.area,'geometry_world':W(p),'status':'OWNERSHIP_REVIEW_REQUIRED; not automatically a customer corridor','automatic_wall_added':False})
 # Morphological thin connections: a shape candidate screen, NOT a certified passage width test.
 thin=public.difference(public.buffer(-1.0).buffer(1.0)).buffer(-.02)
 for i,p in enumerate(polys(thin)):
  if p.area<1.0:continue
  q=p.representative_point();near=sorted([(p.distance(g),sid)for g,sid in zip(plots,ids)])[:3];narrow.append({'id':f['wing']+f['label']+'-THIN-'+str(i),'wing':f['wing'],'floor':f['label'],'world_xz':[q.x+429,q.y-46],'area_m2':p.area,'nearest_stores':[s for d,s in near],'geometry_world':W(p),'status':'MORPHOLOGICAL_CANDIDATE; corner strips may be false positives; physical/visual role review required'})
 floorrows.append({'wing':f['wing'],'floor':f['label'],'stores':len(ids),'floor_m2':plate.area,'public_m2':public.area,'store_union_m2':plotunion.area,'pair_overlap_sum_m2':overlap,'shared_boundary_length_m':shared,'unowned_candidate_m2':unassigned.area,'explicit_residual_m2':explicit.area})
write(P/'source/v22/partition-audit.json',{'floors':floorrows,'invalid_source_geometries':invalid,'shared_boundaries':joints,'unowned_candidates':residuals,'thin_public_candidates':narrow,'no_store_or_entrance_relocated':True,'safety_or_art_completion_claimed':False,'warning':'Morphology, ownership and exact plot joints do not prove rendered wall joints or architectural naturalness. Named facilities, support zones, outdoor landscaping and service spaces need semantic review.'});print('PARTITION_AUDIT',len(F),'floors',len(joints),'joints',len(invalid),'invalid fields',len(residuals),'unowned candidates',len(narrow),'thin candidates')
