import json,hashlib,math
from pathlib import Path
r=Path(__file__).resolve().parents[1]
read=lambda p:json.loads((r/p).read_text())
a=read('source/v25/commons.json');b=read('source/v27/commons.json');rows=[]
for key in ['instances','gates','pads','zones','boards']:
 old={v['id']:v for v in a[key]}
 for n in b[key]:
  if n.get('zone')!='C-DOG-RUN'and n.get('id')!='C-DOG-RUN':continue
  o=old.get(n['id']);pkey='p' if 'p'in n else'preferred'if'preferred'in n else'geometry'
  rows.append(dict(id=n['id'],kind=key,before=o.get(pkey)if o else None,after=n.get(pkey),decision='移設'if o else'追加',reason='実在L-3緑地へ柵・門・設備・表示を一体移設し旧位置の実体を除去'if o else'庭園全体を芝生に整え自然な外周を接続'))
rows.append(dict(id='V9-PARKLIGHT-L-3',kind='lamp',before=[-79.675,0,-248.065],after=[-90.175,0,-248.065],decision='柵外へ移設',reason='走行面の障害を解消。外装・発光・衝突すべてを同じ差分で移動'))
for id,p in [('V27_dog_waste_bin',[-73.5,.4,-253.8]),('V27_DOG_RULES',[-74.5,1.7,-256.48])]:rows.append(dict(id=id,kind='new_equipment',before=None,after=p,decision='追加',reason='前室と主要走行面を避けた周辺サービス'))
es=read('source/v15/ES-site-proposal.json')['escalators']
for e in es:rows.append(dict(id=e['id']+'_V27_soffit_cassettes',kind='ES_FINISH',before=e['c'],after=e['c'],decision='同位置で外装更新',reason='下面・側面・端部を連続した金属カセットで覆う。支持面とベルト制御は保持'))
(r/'source/v27/changed-equipment.json').write_text(json.dumps(dict(changes=rows,engineering_approved=False,formal_architecture_modified=False),ensure_ascii=False,indent=2))
print(len(rows),'changed-ID records')
