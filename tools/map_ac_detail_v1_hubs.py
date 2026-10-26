"""Propose legacy travel aliases in the new design, with no runtime edits."""
from pathlib import Path
import sys,json,csv,math,hashlib
sys.path.append('/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
from shapely.geometry import shape,Point
from shapely.ops import nearest_points
R=Path(__file__).resolve().parents[1];O=R/'docs/ac-detailed-design-v1'
def dec(v):
 if isinstance(v,dict):return shape(v)if'type'in v and('coordinates'in v or'geometries'in v)else{k:dec(x)for k,x in v.items()}
 if isinstance(v,list):return[dec(x)for x in v]
 return v
D={w:dec(json.loads((R/f'docs/{w.lower()}-detailed-design-v1/geometry.json').read_text()))for w in['A','C']};old=json.loads((O/'legacy-travel-hubs.json').read_text());rows=[]
levels={'B1':-1,'1F':0,'2F':1,'3F':2,'RF':3}
def store(w,alias):return next(s for f in D[w]['floors']for s in f['stores']if alias in s.get('legacy_ids',[])or s.get('legacy_id')==alias)
def centre(w,index):q=D[w]['plazas'][index]['court'].centroid;return[q.x,q.y]
for h in old:
 w,floor=h['old_floor_id'].split('/');level=levels[floor];id=h['id'];row={**h,'new_floor_id':h['old_floor_id'],'visited_alias_preserved':True,'implementation_status':'design proposal only; no visited flags or runtime entries edited'}
 if w=='B':row.update(new_world_xyz=None,decision='B館側のハブは今回変更しない。新設計での実装時照合はB館の承認範囲で別途実施。');rows.append(row);continue
 f=next(f for f in D[w]['floors']if f['level']==level);target=None;name=h['legacy_visited_key'];reason='同じ施設機能に対応する新しい計画地点'
 if w=='A':
  if id=='a.entrance':target=[-153,-5.5];name='A館西到着口'
  elif id=='a.central':target=centre('A',0);name='風のゲート'
  elif id=='a.market':target=store('A','a_market')['entry'];name='食品スーパー'
  elif id=='a.food':target=centre('A',2);name='光のコート・飲食側'
  elif id=='a.restroom':target=D['A']['cores'][0]['entry'];name='西トイレ・EV前'
  elif id in['a.atrium.2','a.atrium.3']:target=centre('A',0);name=f'{floor}風のゲート回廊'
  elif id=='a.basement':target=store('A','a_basement_0')['entry'];name='地下食品街'
  elif id=='a.roof':target=centre('A',2);name='屋上庭園'
  elif id=='a.parking':target=next(x['point']for x in D['A'].get('travel_hubs',[])if x['legacy_key']==id);name='西駐車場歩行者ゲート'
 else:
  if id=='bc.walkway':target=[-370,-80];name='B・C地上連絡到着口'
  elif id=='c.court':target=centre('C',0);name='南の迎賓庭'
  elif id=='c.terrace':target=centre('C',1);name='木陰の中庭'
  elif id=='bc.skybridge':target=[-432,-117];name='B・C2F連絡到着口'
  elif id=='c.terrace.2':target=D['C']['view_cameras'][2]['p'][:2];name='2F屋外デッキ・北庭側'
 assert target is not None,id
 free=f['walkable'].buffer(-.6);q=nearest_points(free,Point(target))[0];assert f['walkable'].covers(q.buffer(.59)),id
 row.update(new_display_name=name,requested_target_xz=target,new_world_xyz=[q.x,f['height']+.1,q.y],target_adjustment_m=q.distance(Point(target)),decision=reason,new_reference='新計画の共用歩行域上の足元候補、床上0.1m。Godotでのテレポート検証ではない。')
 rows.append(row)
(O/'travel-hub-migration-proposal.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
with(O/'travel-hub-migration-proposal.csv').open('w',encoding='utf-8-sig',newline='')as fp:
 w=csv.writer(fp);w.writerow(['ID','維持する旧訪問キー','旧階','旧World X','旧World Y','旧World Z','新表示提案','新階','新World X','新World Y','新World Z','候補補正m','状態'])
 for q in rows:w.writerow([q['id'],q['legacy_visited_key'],q['old_floor_id'],*q['old_world_xyz_source_derived'],q.get('new_display_name','B館対象外'),q['new_floor_id'],*(q.get('new_world_xyz')or['','','']),q.get('target_adjustment_m',''),q['implementation_status']])
print('Migration proposals',len(rows),'A/C placed',sum(q.get('new_world_xyz')is not None for q in rows))
