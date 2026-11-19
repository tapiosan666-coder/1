"""Assign travel displays only to ledger entries originally marked as travel.

Pass the result of the dedicated v35 baseline support/overlap/browse survey.
An existing B1-SW32 wall bay may be refit only if its volume and frontage were
both checked with the former owner loaded and excluded from the probe.
"""
from pathlib import Path
import json, math, sys
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'source/v36'
def load(p):return json.loads(p.read_bytes())
def save(path,content):path.write_text(json.dumps(content,ensure_ascii=False,separators=(',',':'))+'\n')
def main():
    stores=load(SRC/'store-studios.json')
    refits=load(SRC/'store-refits.json')
    raw=load(ROOT/'source/v32/sales-design.json')['stores']
    probes=load(Path(sys.argv[1]))
    choices=[q for q in probes if q['id']=='B1-SW32' and not q['issue'] and q['former_loaded']]
    for s in stores:
        if '旅行' not in s['original_category']:continue
        s['display_trade']='luggage'
        if s['id']=='B1-SW32' and not s['placements'] and choices:
            shop=next(r for r in raw if r['id']==s['id'])
            # A wall fixture in the middle third, facing the open interior.
            q=min(choices,key=lambda t:abs(math.dist(t['p'][::2],shop['entry'][::2])-12.0))
            f=next(o for o in shop['placements'] if o['id']==q['refit_id'])
            w,h,d=f['bounds']['size'];bx,_,bz=f['bounds']['p']
            sc=[min(1.,(w-.025)/2.58), min(1.,(h-.008)/1.49),min(1.,(d-.025)/.74)]
            yy=round(q['floor']+.002,3);dx=bx+w/2;dz=bz+d/2
            bay=dict(role='gallery',p=[round(q['p'][0],3),yy,round(q['p'][2],3)],yaw=f['yaw'],
                     width=sc[0]*2.58,distance_to_entry=round(math.dist(q['p'][::2],shop['entry'][::2]),2),refit=f['id'])
            s['placements'].append(bay)
            refits[f['id']]={'scale':sc,'offset':[dx,yy-f['p'][1],dz],'old_asset':f['asset'],'role':'gallery','variant':s['variant']}
        for bay in s['placements']:
            bay['mesh']='luggage-'+bay['role']
            if 'refit' in bay:refits[bay['refit']]['mesh']=bay['mesh']
    save(SRC/'store-studios.json',stores);save(SRC/'store-refits.json',refits)
if __name__=='__main__':main()
