"""Semantic floor ownership contract. An unresolved draft cannot be a production export."""
from pathlib import Path
import json

def production_gate(audit):
 unresolved=[{'floor':q['floor'],'unowned_m2':q['unallocated_after_proposed_small_annex_m2']}for q in audit['summaries']if q['unallocated_after_proposed_small_annex_m2']>.001]
 return {'can_export_production':not unresolved,'unresolved':unresolved,'rule':'Every slab region needs an explicit, reviewed owner/use. Remaining geometry is not automatically a corridor, stock room or equipment room.','review_draft_allowed_only_explicitly':True}
def apply_review_proposals(fs,proposals,rect,Polygon,unary_union):
 applied=[]
 for c in proposals['changes']:
  f=next((f for f in fs if f['level']==c['level']),None)
  if f is None:continue
  s=next(s for s in f['stores']if s['id']==c['store']);s['polygon']=c['new_polygon'];s['backroom']=c['new_backroom'];s['nonoccupiable_enclosure_allowance']=c['nonoccupiable_enclosure_allowance'];s['wall_solids']=s['polygon'].boundary.buffer(.125).intersection(s['polygon'])
  openings=[rect(s['entry'],s['u'],s['door_width_m'],.8)]
  if s.get('secondary_entry'):openings.append(rect(s['secondary_entry'],s.get('secondary_u',s['u']),s.get('secondary_door_width_m',6),.8))
  s['wall_solids']=s['wall_solids'].difference(unary_union(openings));f['residual']=f['residual'].difference(c['assigned_pocket']);applied.append({k:v for k,v in c.items()if k not in['old_polygon','new_polygon','old_backroom','new_backroom','nonoccupiable_enclosure_allowance']})
 return applied
