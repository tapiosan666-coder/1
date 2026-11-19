"""Apply measured Godot floor heights and decline obstructed sites.

Run on the uncalibrated candidate files after lay_out.py / thresholds.py, using
the two matching collision surveys. Does not reinterpret missing evidence.
"""
from pathlib import Path
from collections import Counter
import json,sys
root=Path(__file__).resolve().parents[3]
src=root/'source/v36'
def load(path):return json.loads(Path(path).read_text())
def dump(path,data):Path(path).write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
def main():
 bays=load(src/'store-studios.json');thresholds=load(src/'thresholds.json')
 refits=load(src/'store-refits.json');a=load(sys.argv[1]);b=load(sys.argv[2])
 tested_bays={(q['id'],q['role']):q for q in a if not q['refit']}
 tested_replacements={q['refit_id']:q for q in b if q['refit']}
 tested_thresholds={q['id']:q for q in b if q['role']=='threshold'}
 declined=[]
 for store in bays:
    kept=[]
    for bay in store['placements']:
        status=tested_replacements.get(bay['refit']) if bay.get('refit') else tested_bays.get((store['id'],bay['role']))
        issue=status['issue'] if status else 'unmeasured'
        if not issue and abs(status['floor']-bay['p'][1])>.095:issue='wrong_floor'
        if issue:
            declined.append({'id':store['id'],'role':bay['role'],'refit':bay.get('refit',''),'p':bay['p'],'reason':issue,
                             'other':status.get('other','') if status else ''})
            if bay.get('refit'):refits.pop(bay['refit'],None)
            continue
        h=round(status['floor']+.002,3)
        # Existing decorative flooring may extend to 18mm above its filmed
        # collision slab. The case's 80mm plinth sits through this finish.
        if bay.get('refit'):
            dt=h-bay['p'][1];refits[bay['refit']]['offset'][1]+=dt
        bay['p'][1]=h;kept.append(bay)
    store['placements']=kept
 retained=[]
 for s in thresholds:
    q=tested_thresholds.get(s['id']);bay=s['placements'][0]
    if not q or q['issue'] or abs(q['floor']-bay['p'][1])>.09:
        declined.append({'id':s['id'],'role':'threshold','p':bay['p'],'reason':q['issue'] if q and q['issue'] else 'unmeasured_or_wrong_floor'})
        continue
    # The printed top is a physical entry mat/mosaic insert. A short
    # bevel bridges the legacy non-colliding floor finish (up to ~25mm).
    bay['p'][1]=round(q['floor']+.034,3);retained.append(s)
 def counts(s):
    return {f'{w}-{f}':sum(len(a['placements']) for a in s if a['wing']==w and a['floor']==f) for w in 'ABC' for f in ('B1','1F','2F','3F','RF')}
 summary={'stores':len(bays),'retail_stores':sum(bool(s['placements']) for s in bays),'freestanding':sum(not b.get('refit') for s in bays for b in s['placements']),
          'refits':len(refits),'dining':sum(b['role']=='dining' for s in bays for b in s['placements']),
          'retail_placements':sum(len(a['placements']) for a in bays),'thresholds':len(retained),'stations_by_floor':counts(bays),'thresholds_by_floor':counts(retained),
          'no_retail':[s['id'] for s in bays if not s['placements']],'declined':declined}
 dump(src/'store-studios.json',bays);dump(src/'store-refits.json',refits);dump(src/'thresholds.json',retained);dump(sys.argv[3],summary)
 print({k:v for k,v in summary.items() if k not in ('declined','stations_by_floor','thresholds_by_floor')})
if __name__=='__main__':main()
