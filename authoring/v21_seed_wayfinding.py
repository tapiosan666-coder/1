"""Seed source plans with paths physically checked in this same build; runtime still rechecks all segments."""
from pathlib import Path
import json,copy
P=Path(__file__).resolve().parents[1];R=Path('/workspace/v21-review');path=P/'source/v21/wayfinding.json';d=json.loads(path.read_text());changes=[]
for variant,folder in [('normal','normal'),('C','C'),('ES','ES')]:
 report=json.loads((R/('physics-'+folder)/'v21-wayfinding-physics.json').read_text());lookup={(x['sign'],x['kind']):x for x in report['checks']if x['pass']}
 for board in d[variant]:
  for row in board['rows']:
   q=lookup.get((board['id'],row['kind']))
   if not q:continue
   old=copy.deepcopy(row)
   if row['target_id']!=q['target']:
    alt=next(x for x in row['alternate_targets']if x['id']==q['target']);row.update(target_id=alt['id'],target_point=alt['point'],label=alt['label'],target_source=alt['source'])
   row['path']=q['actual_path'];row['front_arrow']=q['front_arrow'];row['back_arrow']=q['back_arrow'];row['distance_m']=q['distance_m'];row['physics_seed_note']='Seed from actual Godot capsule/floor validation; every launch rechecks against current collision before showing arrows.'
   if old['path']!=row['path']or old['target_id']!=row['target_id']:changes.append({'variant':variant,'board':board['id'],'kind':row['kind'],'original':old,'verified_seed':row})
path.write_text(json.dumps(d,ensure_ascii=False,indent=2));(P/'source/v21/route-seed-history.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2));print('SEEDS_UPDATED',len(changes))
