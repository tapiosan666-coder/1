from pathlib import Path
import json,math
p=Path(__file__).resolve().parents[1];shots=json.load(open(p/'source/cameras.json'));shots=[q for q in shots if not q['id'].startswith('WALK-')];d=json.load(open(p/'evidence/after/physical-results.json'));rs={q['id']:q for q in d['checks']};sources={q['id']:q for q in json.load(open(p/'source/physical-routes.json'))}
for id in['B1-010','B2-047']:
 q=rs[id];points=q['checkpoints'];assert q['pass']
 for typ,idx in[('entry',1),('stock',len(points)-1)]:
  cp=points[idx];eye=cp['position'].copy();eye[1]+=1.65;target=sources[id]['points'][idx+1 if idx<len(points)-1 else idx-2].copy();target[1]+=1.6
  if math.dist(eye,target)<.2:target[2]+=1
  shots.append({'id':'WALK-'+id+'-'+typ,'scope':'main','after_only':True,'eye_local':eye,'look_local':target,'label':id+' / 自動歩行到達点 '+typ,'grounded_checkpoint':cp,'source_actual_physics_run':'evidence/after/physical-results.json','human_control':False})
(p/'source/cameras.json').write_text(json.dumps(shots,ensure_ascii=False,indent=2))
