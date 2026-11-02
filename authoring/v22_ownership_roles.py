from pathlib import Path
import sys,collections
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import *
from shapely.validation import make_valid
from shapely import set_precision
F=read(P/'source/v11/floors-updated.json');d=read(P/'source/v22/partition-audit.json');lookup={(f['wing'],f['label']):f for f in F};summary=[]
def valid(g):
 g=g if g.is_valid else make_valid(g)
 g=unary_union(polys(g))
 return set_precision(g,.0001)if not g.is_empty else Polygon()
def collect(v,path):
 if hasattr(v,'geom_type'):return[(path,valid(affinity.translate(v,429,-46)))]
 if isinstance(v,dict):return[pair for k,x in v.items()for pair in collect(x,path+'/'+str(k))]
 if isinstance(v,list):return[pair for i,x in enumerate(v)for pair in collect(x,path+'/'+str(i))]
 return[]
for f in F:
 semantic=[]
 for name in ['parking','program','cores','staff_walk','service_access','outdoor_ground','outdoor_deck','indoor_public','landscape','gardens','equipment_zones','plant_beds','envelope_walls','vestibule_walls','guardrails']:
  semantic+=collect(f.get(name,{}),name)
 total=0.;classified=0.;unresolved=0.
 for r in d['unowned_candidates']:
  if r['wing']!=f['wing']or r['floor']!=f['label']:continue
  g=valid(r['geometry_world']);remaining=g;sources=[]
  for name,geom in semantic:
   overlap=remaining.intersection(geom).area
   if overlap>.001:sources.append({'source_field':name,'area_m2':overlap});remaining=remaining.difference(geom)
  r['existing_semantic_owners']=sources;r['unexplained_remainder_m2']=remaining.area;r['status']='CLASSIFIED_FROM_EXISTING_PROGRAM_OR_STRUCTURE'if remaining.area<.05 else'PARTIAL_OR_UNRESOLVED_REQUIRES_ROLE_REVIEW';total+=g.area;classified+=g.area-remaining.area;unresolved+=remaining.area
 summary.append({'wing':f['wing'],'floor':f['label'],'original_candidate_m2':total,'assigned_existing_program_m2':classified,'unexplained_remainder_m2':unresolved})
d['ownership_semantic_summary']=summary;d['query_precision_m']=.0001;d['source_geometry_changed']=False;d['ownership_method']='Partition screen subtracts exact stored parking/program/core/landscape/structure geometries with source field paths; never assigns empty floors by invented labels.';write(P/'source/v22/partition-audit.json',d);print('OWNERSHIP',sum(r['original_candidate_m2']for r in summary),sum(r['assigned_existing_program_m2']for r in summary),sum(r['unexplained_remainder_m2']for r in summary))
