"""Reject annexations that worsen wall geometry. Constrained straight enclosure studies, not hole-filling walls."""
from pathlib import Path
import sys,json,itertools
sys.path.insert(0,'/workspace/1/tools');from site_v2_common import *
from shapely import maximum_inscribed_circle
P=Path(__file__).resolve().parents[1];O=P/'source/root-gap-review';base=read(O/'enclosure-proposals.json');D=read(R/'docs/site-correction-v3/geometry.json');accepted=[];rejected=[]
for c in base['changes']:
 f=next(f for f in D['floors']if f['wing']=='B'and f['level']==c['level']);s=next(s for s in f['stores']if s['id']==c['store']);protected=unary_union([f['public'],f['void'],f['shafts'],f.get('egress',Polygon()),*[q['outline']for q in f['cores']],*[q['polygon']for q in f.get('service_zones',[])],*[q['polygon']for q in f.get('program',[])],*[q['line'].buffer(q['width_m']/2)for q in f.get('staff_routes',[])]]);other=unary_union([t['polygon']for t in f['stores']if t['id']!=s['id']]);hull=s['polygon'].union(c['assigned_pocket']).convex_hull;parts=polys(hull.difference(protected.union(other)).intersection(f['shell']));candidate=next((p for p in parts if p.covers(s['polygon'].representative_point())),Polygon());added=candidate.difference(s['polygon']);v0=len(s['polygon'].simplify(.002).exterior.coords);v1=len(candidate.simplify(.002).exterior.coords)if not candidate.is_empty else 100000;perimeter_delta=candidate.length-s['polygon'].length;removed=s['polygon'].difference(candidate).area
 # Shared interfaces are preserved by clipping against all protected roles. The 2mm simplification is ONLY a complexity measurement.
 reasons=[]
 if candidate.is_empty or not candidate.is_valid:reasons.append('区画が単一の有効ポリゴンにならない')
 if removed>.00001:reasons.append('既存の売場または区画を削ってしまう')
 if added.area>100 or added.area>s['polygon'].area*.25:reasons.append('局所検証の面積限度を超える')
 if v1>v0+3:reasons.append('有効な曲がり角が増え、壁面の凹凸を悪化させる')
 if perimeter_delta>3:reasons.append('外壁長が3mを超えて増え、閉じた面を増やす')
 if reasons:rejected.append({'store':c['store'],'issue_id':c['issue_id'],'reasons':reasons,'old_effective_vertices':v0,'candidate_effective_vertices':v1,'candidate_perimeter_delta_m':perimeter_delta,'candidate_added_m2':added.area});continue
 width=maximum_inscribed_circle(added,tolerance=.025).length*2;usable=width>=1.2;newstock=s['backroom'].union(added)if usable else s['backroom']
 stockparts=polys(newstock);door=Point(s['back_door']);connected=[p for p in stockparts if p.distance(door)<.04];stray=[p for p in stockparts if p not in connected]
 if not connected or any(p.area>.5 and maximum_inscribed_circle(p,tolerance=.025).length*2>=1.2 for p in stray):
  rejected.append({'store':c['store'],'reasons':['バックヤードに専用扉へ接続しない居室規模の部分が残る。個別の内部設計が必要。']});continue
 newstock=unary_union(connected);allowance=candidate.difference(s['sales'].union(newstock));new={**c,'new_polygon':candidate,'old_polygon':s['polygon'],'old_backroom':s['backroom'],'new_backroom':newstock,'assigned_pocket':added,'nonoccupiable_enclosure_allowance':allowance,'added_plot_m2':added.area,'added_usable_stock_m2':newstock.area-s['backroom'].area,'old_effective_vertices':v0,'new_effective_vertices':v1,'perimeter_delta_m':perimeter_delta,'rule':'既存店と空隙を含む外郭を直線化し、全ての保護領域・隣店で同時に制約。既存区画を削らず、頂点数・壁長が悪化する案は棄却。2mm簡略化は評価だけで、図面へ適用していない。'};accepted.append(new)
# No order-dependent greedy ownership: reject ALL conflicting proposals for joint redesign.
conflicts=set()
for i,a in enumerate(accepted):
 for j,b in enumerate(accepted[i+1:],i+1):
  if a['level']==b['level']and a['new_polygon'].intersection(b['new_polygon']).area>1e-6:conflicts.update([i,j])
for i in conflicts:rejected.append({'store':accepted[i]['store'],'reasons':['他の修正案と競合。所有境界の共同設計が必要。']})
accepted=[c for i,c in enumerate(accepted)if i not in conflicts];audit=read(O/'full-B-root-audit.json')
for f in audit['summaries']:
 floor=next(ff for ff in D['floors']if ff['wing']=='B'and ff['level']==f['level']);assigned=unary_union([c['assigned_pocket']for c in accepted if c['level']==f['level']]);f['unallocated_after_proposed_small_annex_m2']=f['unallocated_before_m2']-assigned.area;f['proposed_annexations']=sum(c['level']==f['level']for c in accepted)
result={**base,'changes':accepted,'rejected_candidates':rejected,'unresolved_after_proposal':audit['summaries'],'method':'Simultaneous protected-domain clipping; no greedy assignment; architectural complexity guard. No design approval or full-B completion.'}
for name,obj in [('refined-enclosure-proposals.json',result),('full-B-root-audit.json',audit)]: (O/name).write_text(json.dumps(obj,default=encode,ensure_ascii=False,indent=2))
print('REFINED',len(accepted),'accepted for prototype',len(rejected),'rejected');print('IN_CROP',[(q['store'],round(q['added_plot_m2'],3),q['old_effective_vertices'],q['new_effective_vertices'])for q in accepted if q['in_current_3D']]);print('REJECTED',[(q['store'],q['reasons'])for q in rejected])
