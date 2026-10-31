"""Document retained/adopted equipment from actual v26 contract, without changing it."""
import json,csv,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'source/v27';out.mkdir(exist_ok=True)
def read(p):return json.loads((root/p).read_text())
old=read('source/scene-manifest.json')['escalators'];new=read('source/v15/ES-site-proposal.json');ev=[e for e in read('source/elevators-v7.json') if e['wing']=='B'];maps=read('source/v22/map-data-integrated.json');rows=[]
for e in old+new['escalators']:
 retired=e['id'] in new['retired_machine_ids'];rows.append(dict(id=e['id'],kind='ES',position=e['c'],orientation=e['u'],levels=e['levels'],direction=e['direction'],normal='excluded' if retired else 'active',F6='excluded' if retired else 'active (ES-only structural comparison)' ,decision='退役維持' if retired else '採用維持＋外装更新' if e['id'].startswith('B-WEST') else '独立動線として維持＋外装更新',reason='西側連続ESに役割を置換済み。v27で再表示しない' if retired else '1F→RF連続ルート。既存開口・支持面・手すりを維持' if e['id'].startswith('B-WEST') else '西側とは別の中央/東側の動線。無条件撤去しない',relocated=False))
for e in ev:rows.append(dict(id=e['id'],kind='EV',position=e['center'],door=e['door_xz'],levels=[-1,0,1,2,3],decision='維持',reason='B1からRFをつなぐ既存EV。西側ESとは別位置',relocated=False))
for f in maps:
 if f['wing']!='B':continue
 for e in f['items']:
  if e['kind']=='階段':rows.append(dict(id=e['id']+'-'+f['label'],kind='STAIR',position=[e['point'][0]+429,f['height'],e['point'][1]-46],levels=[f['level']],decision='維持',reason='既存避難階段コアを変更しない',relocated=False))
report=dict(baseline_commit='8b1f0f0c8fcb3b3c343c2a708c1401750eee15ea',engineering_approved=False,coordinate_system='metres WORLD x/y/z; map local x,z +429,-46',records=rows,notes=['v26の通常起動はC/ES/A連続構造の統合候補。正式建築原本ではない','旧西側4基はv26時点ですでに退役設定。実行時検証と旧地点の床検査を別途提出','B1には西側連続ESを新設しない。既存EV/階段を維持','F6はES単独構造別案へ切替（B西連続ESあり、A/Cの統合候補なし）、再度F6で通常候補へ復帰。F4のC単独別案では旧B西ESを維持','西側中心(-192,-15.5)とEV最短距離は約90m。図の近接例を実測値と誤認しない'])
(out/'equipment-inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
with (out/'equipment-inventory.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=sorted(set().union(*(r.keys() for r in rows))));w.writeheader();w.writerows(rows)
print(len(rows),'equipment records')
