import sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[2];sys.path.insert(0,str(P/'authoring'));from site_v2_common import raw_json
normal=raw_json(P/'source/v13/map-data.json');C=raw_json(P/'source/v15/map-data-C-option.json');E=raw_json(P/'source/v15/map-data-ES-option.json');lookupC={(x['wing'],x['level']):x for x in C};lookupE={(x['wing'],x['level']):x for x in E};combined=[(lookupC if x['wing']=='C'else lookupE if x['wing']=='B'else{}).get((x['wing'],x['level']),x)for x in normal]
(P/'source/v22/map-data-combined.json').write_text(json.dumps(combined,separators=(',',':'),ensure_ascii=False));(P/'source/v22/map-schema.txt').unlink(missing_ok=True)
print('COMBINED_MAP',len(combined),'floors')
