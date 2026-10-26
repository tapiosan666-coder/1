from pathlib import Path
import sys,collections
sys.path.insert(0,'/workspace/1/tools');from site_v2_common import *
from retail_v2 import fit_shop
P=Path(__file__).resolve().parents[1];d=read(P/'source/design-extract.json');fronts=read(P/'source/constructed-fronts.json');ctx={'rect':rect,'CROP':box(-512,-16,-349,124),'lines':lines,'meta':{},'lights':[],'fronts':fronts}
for k in ['extrude','surf','bar','cylinder','tri','quad']:ctx[k]=lambda *a,**kw:None
ctx['pos']=lambda *a:a
for f in d['floors']:
 ctx['f']=f
 for i,s in enumerate([s for s in f['stores']if s['polygon'].intersects(ctx['CROP'])]):
  if s['id']not in ['B1-017','B1-040','B1-043']:continue
  fit_shop(ctx,s,f['level'],f['height'],i,s['polygon'].intersection(ctx['CROP']),s['shelf_zones'])
for q in ctx['meta']['detailed_fitouts']:print(q['id'],collections.Counter(x['kind']for x in q['features']))
