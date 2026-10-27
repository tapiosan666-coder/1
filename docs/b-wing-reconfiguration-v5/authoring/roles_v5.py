"""Exact, disjoint floor-role account tied to constructed zones and actual footprint removals."""
from pathlib import Path
import sys,json,copy,csv,math,collections
sys.path.insert(0,str(Path(__file__).resolve().parent));from site_v2_common import *
from shapely import maximum_inscribed_circle
P=Path(__file__).resolve().parents[1];S=P/'source';D=read(S/'design-working.json');base=read((Path(__file__).resolve().parents[1]/'source/baseline-v4.json'));B={f['label']:f for f in base['floors']};rows=[];beforeparts=[];afterleft=[]
def csvout(name,rr):
 with open(S/name,'w',encoding='utf-8-sig',newline='')as out:w=csv.DictWriter(out,rr[0].keys(),lineterminator='\n');w.writeheader();w.writerows(rr)
def assigned(f):return unary_union([f['public'],f['void'],f['shafts'],f.get('egress',Polygon()),*[c['outline']for c in f['cores']],*[s['polygon']for s in f['stores']],*[z['polygon']for z in f['service_zones']]])
newids={0:['インテリア・家電','生活雑貨・デザイン','モバイル・家電小物','旅行用品'],1:['児童書・絵本','書籍・文具','ライフスタイル書店'],2:['スポーツ・アウトドア','楽器・クラフト','親子読書カフェ']}
for f in D['floors']:
 old=B[f['label']];f['original_shell']=old['shell'];f['exterior_removed']=old['shell'].difference(f['shell']);f['old_floor_plate']=old['floor_plate'];
 newshops=sorted([s for s in f['stores']if'-N'in s['id']],key=lambda s:s['id'])
 for i,s in enumerate(newshops):s['category']=newids[f['level']][min(i,len(newids[f['level']])-1)]
 # Only the receiving floor gets an escalator run opening. Lower combs and the ground under rising flights remain supported.
 coreholes=unary_union([q[k]for q in f['vertical_devices']for k in ['lift_opening','stair_opening']if k in q]);receiving=unary_union([rect(e['c'],e['u'],e['run_m'],2.4)for e in f['escalators']if e['levels'][1]==f['level']]);f['floor_openings_v5']=unary_union([f['void'],coreholes,receiving]);outside=old['floor_plate'].difference(old['shell']);tenant_slabs=unary_union([s['polygon']for s in f['stores']]+[z['polygon']for z in f['service_zones']]);floor=old['floor_plate'].intersection(f['shell']).union(outside).union(tenant_slabs).difference(f['floor_openings_v5']);f['machine_islands']=[]
 for p in polys(f['public']):
  for ring in p.interiors:
   island=Polygon(ring);esc=[e for e in f['escalators']if island.buffer(.03).intersects(Point(e['c']))]
   if esc and island.area<160:f['machine_islands'].append({'id':'ES-'+','.join(sorted({e['id']for e in esc})),'polygon':island.intersection(floor),'reason':'paired escalator equipment / guard / maintenance spine; not a passage'})
 equipment=unary_union([q['polygon']for q in f['machine_islands']]);rim=f['void'].buffer(.28).difference(f['void']).intersection(floor);walls=unary_union([f['shell'].boundary.buffer(.125),*[s['polygon'].boundary.buffer(.125)for s in f['stores']],*[s['backroom'].boundary.buffer(.10)for s in f['stores']],*[z['polygon'].boundary.buffer(.125)for z in f['service_zones']],*[c['outline'].boundary.buffer(.125)for c in f['cores']]]).intersection(floor)
 zones=[('設備核',unary_union([c['outline']for c in f['cores']]),'existing toilet/stair/lift/core programme'),('機器・手すり支持',equipment.union(rim),'explicit escalator islands and 0.28m atrium balustrade bases'),('店舗区画',unary_union([s['polygon']for s in f['stores']]),'frontage plots with sales / working stock / real doors'),('運営・共用在庫',unary_union([z['polygon']for z in f['service_zones']]),'120sqm operations and two 160sqm receiving/store-specific stock rooms'),('共用・避難',f['public'].union(f.get('egress',Polygon())),'protected customer concourse, plazas and named egress'),('壁・構造納まり',walls,'actual wall footprint, not arbitrary closed equipment volume')]
 covered=unary_union([g for _,g,_ in zones]);left=floor.difference(covered);poche=[];localcuts=[]
 for g in polys(left):
  if g.area<1e-7:continue
  width=maximum_inscribed_circle(g,tolerance=.005).length*2
  if width<.30 and g.area<5 and g.distance(walls)<.25:
   poche.append(g);continue
  canopies=unary_union([q.get('vestibule_floor',Polygon())for q in base['floors'][0].get('doors_v3',[])])
  coreedge=unary_union([c['outline'].boundary for c in f['cores']])
  bc=next(q for q in base['floors'][0]['connectors']if q['id']=='BC-1');bc_inside=LineString([(p[0]-714,p[1]-30)for p in bc['route']]).buffer(bc['width']/2+.02,cap_style=2)
  unused_upper_bridge=(f['level']>0 and g.intersection(bc_inside).area>g.area*.99)
  if g.boundary.intersection(f['shell'].boundary.buffer(.01)).length>.05 or (f['level']>0 and g.intersection(canopies.buffer(.02)).area>g.area*.7) or (g.area<10 and g.distance(coreedge)<1.5) or unused_upper_bridge:
   # Source BODY ledges and the 1F entry canopy are not unprogrammed rooms on upper floors.
   localcuts.append(g);continue
  # All non-public islands must have a real device or structural neighbour. Larger interior remainder blocks the export.
  if g.area<.1 and g.distance(walls)<.08:poche.append(g);continue
  afterleft.append({'floor':f['label'],'area':g.area,'width':width,'polygon':g})
 f['construction_poche']=unary_union(poche);f['per_level_external_floor_cuts']=unary_union(localcuts);floor=floor.difference(f['per_level_external_floor_cuts']);f['floor_plate']=floor;f['building_envelope_v5']=f['shell'].difference(f['per_level_external_floor_cuts']).union(outside);f['slab_added_v5']=floor.difference(old['floor_plate']);f['slab_removed_v5']=old['floor_plate'].difference(floor)
 zones[-1]=('壁・構造納まり',walls.union(f['construction_poche']),'actual walls / sealed construction joints under .30m, not occupiable warehouse');role=[];occupied=Polygon()
 for name,g,reason in zones:
  p=g.intersection(floor).difference(occupied);role.append({'role':name,'polygon':p,'area_m2':p.area,'purpose':reason});occupied=occupied.union(p)
 f['floor_roles']=role;missing=floor.difference(occupied);overlap=sum(q['area_m2']for q in role)-occupied.area
 for q in role:rows.append({'floor':f['label'],'role':q['role'],'area_m2':q['area_m2'],'purpose':q['purpose']})
 rows.append({'floor':f['label'],'role':'床合計','area_m2':floor.area,'purpose':'physical slab, excluding atrium / shafts and declared external cutback'});rows.append({'floor':f['label'],'role':'未帰属','area_m2':missing.area,'purpose':'must be zero within numerical tolerance'});rows.append({'floor':f['label'],'role':'役割重複','area_m2':overlap,'purpose':'disjoint role account, must be zero'})
 unowned_before=old['floor_plate'].difference(assigned(old))
 for i,p in enumerate(sorted(polys(unowned_before),key=lambda p:-p.area),1):
  actions=[]
  for q in role:
   area=p.intersection(q['polygon']).area
   if area>.00001:actions.append({'role':q['role'],'area_m2':area})
  removed=p.difference(floor).area
  if removed>.00001:actions.append({'role':'外郭縮小・開口・外部化','area_m2':removed})
  pp=p.representative_point();reason='外郭の膨張と階別の区画奥行き差'if p.boundary.intersection(old['shell'].boundary.buffer(.01)).length>.1 else'街区内の分割差分・大きな管理室と店舗の取り合い'
  if p.distance(old['void'])<.3 or any(p.distance(Point(e['c']))<15 for e in old['escalators']):reason+=' / 一部は機器・手すりの計上漏れも照合'
  beforeparts.append({'id':f'B{f["level"]+1}-U{i:03}','floor':f['label'],'world_x_m':pp.x,'world_y_m':f['height'],'world_z_m':pp.y,'old_area_m2':p.area,'cause':reason,'polygon':p,'new_actions':actions,'accounted_m2':sum(a['area_m2']for a in actions),'unaccounted_m2':p.area-sum(a['area_m2']for a in actions)})
 print('ROLE_FLOOR',f['label'],'floor',floor.area,'missing',missing.area,'outside cuts',f['per_level_external_floor_cuts'].area,'poche',f['construction_poche'].area,flush=True)
write(S/'design-v5.json',{**D,'floors':D['floors'],'unresolved_floor_areas':afterleft,'architecture_complete':False,'review_status':'Independent revised plan and validation model; not integrated; engineering/operation/human walk pending'})
write(S/'unowned-full-inventory.json',beforeparts);csvout('unowned-full-inventory.csv',[{**{k:v for k,v in p.items()if k not in ['polygon','new_actions']},'new_actions':'; '.join(f"{a['role']}:{a['area_m2']:.6f}"for a in p['new_actions'])}for p in beforeparts]);csvout('floor-role-areas.csv',rows)
print('INTERIOR_REMAINDERS',len(afterleft),[(q['floor'],round(q['area'],5),q['polygon'].bounds)for q in afterleft],flush=True)
