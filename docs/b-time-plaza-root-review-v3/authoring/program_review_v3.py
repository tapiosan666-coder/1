"""Evidence-based roles for residual floor, 18 large-unit fitout studies, unapproved mergers."""
from pathlib import Path
import sys,json,csv,math,collections,hashlib,itertools
sys.path.insert(0,'/workspace/1/tools');from site_v2_common import *
import numpy as np
from shapely import maximum_inscribed_circle
P=Path(__file__).resolve().parents[1];OUT=P/'source/program-review-v3';OUT.mkdir(exist_ok=True)
D=read(R/'docs/site-correction-v3/geometry.json');B=[f for f in D['floors']if f['wing']=='B'and f['level']in[0,1,2]];CROP=box(-512,-16,-349,124);audit=read(P/'source/audit/full-audit.json')
def save(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,default=encode))
def csvwrite(name,rows):
 with open(OUT/name,'w',newline='',encoding='utf-8-sig')as o:w=csv.DictWriter(o,list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def svgpath(g):return' '.join(' '.join('M'+' L'.join(f'{x:.3f},{z:.3f}'for x,z in ring.coords)+' Z'for ring in [p.exterior,*p.interiors])for p in polys(g))
spaces=[];summaries=[]
for f in B:
 occ=unary_union([s['polygon']for s in f['stores']]);core=unary_union([c['outline']for c in f['cores']]);service=unary_union([z['polygon']for z in f['service_zones']]);g=f['floor_plate'].intersection(CROP).difference(f['public'].union(occ).union(core).union(service));parts=sorted([p for p in polys(g)if p.area>.5],key=lambda p:-p.area);small=g.difference(unary_union(parts));rolearea=collections.Counter()
 for i,p in enumerate(parts+[small]):
  if p.is_empty:continue
  aggregate=i==len(parts);width=0 if aggregate else maximum_inscribed_circle(p,tolerance=.025).length*2
  shares=[(p.boundary.intersection(z['polygon'].buffer(.005)).length,z)for z in f['service_zones']];share,z=max(shares,key=lambda a:a[0]);near=sorted([(p.distance(s['backroom']),s)for s in f['stores']],key=lambda a:a[0])[0]
  if aggregate or width<.60:role='納まり・境界充填候補';need='利用可能な部屋・通路として計上しない';reason='最大内接幅が小さい、または0.5㎡以下の端数集約。用途のある部屋への自動転換は禁止。'
  elif width<1.50:role='保守用ふところ候補';need='設備経路の必要量は未確定';reason='客用・搬入通路に必要な余裕が取れない。点検口の位置・手入れ方法を要設計。'
  elif share>1.5:role='既存共用倉庫への編入案';need='面積需要と搬入経路の承認待ち';reason=f"{z['id']} {z['name']}と境界共有{share:.2f}m。新しい客用通路を作らず既存裏方機能へ編入を検討。"
  elif near[0]<.02 and p.area<300:role='隣接店舗の在庫・従業員室への編入案';need='店舗用途に応じた必要量の確認待ち';reason=f"{near[1]['id']}のバックヤードに隣接。売場への動線と間仕切り・保守扉の再設計が必要。"
  else:role='余剰建築床・外郭縮減候補';need='維持すべき用途を裏付ける設備計画なし';reason='外郭の包絡演算で残った床。必要性が証明されない限り機械室や空白広場として正当化しない。外郭変更は別案として承認待ち。'
  rolearea[role]+=p.area;spaces.append({'id':f"R-{f['label']}-{i+1:02}",'floor':f['label'],'polygon':p,'area_m2':p.area,'bounds':p.bounds,'max_inscribed_diameter_m':width,'source_residual_fraction':p.intersection(f['residual']).area/p.area,'source_nav_free_m2':p.intersection(f['nav_free']).area,'public_contact_length_m':p.boundary.intersection(f['public'].buffer(.005)).length,'role_proposal':role,'necessity':need,'reason':reason,'source_status':'geometric residual, no individually named equipment or load schedule','implementation_status':'NOT_APPLIED; no new doors, routes, store boundaries or envelope changes','access_status':'NOT_VERIFIED; no reachability pass assigned','small_fragments_aggregated':aggregate})
 summaries.append({'floor':f['label'],'area_m2':g.area,'source_residual_m2':g.intersection(f['residual']).area,'source_nav_free_m2':g.intersection(f['nav_free']).area,'role_area_m2':dict(rolearea),'difference_to_v2_unassigned_m2':g.area-audit['floors'][f['level']]['unassigned_candidate_total_m2']})
 palette={'納まり・境界充填候補':'#b0b5b3','保守用ふところ候補':'#c1baa6','既存共用倉庫への編入案':'#b5cdbb','隣接店舗の在庫・従業員室への編入案':'#c4cbe0','余剰建築床・外郭縮減候補':'#dfa993'}
 pieces=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-520 -26 183 162" width="1400" height="1200"><rect x="-520" y="-26" width="183" height="162" fill="#faf9f5"/>',f'<path d="{svgpath(f["public"].intersection(CROP))}" fill="#e0eeeb" stroke="#70857c" stroke-width=".16"/>']
 for s in f['stores']:
  pieces.append(f'<path d="{svgpath(s["polygon"].intersection(CROP))}" fill="#e4e2d7" stroke="#7c8177" stroke-width=".1"/>')
 for q in spaces:
  if q['floor']!=f['label']or q['small_fragments_aggregated']:continue
  p=q['polygon'];c=p.representative_point();pieces.append(f'<path d="{svgpath(p)}" fill="{palette[q["role_proposal"]]}" stroke="#5e655e" stroke-width=".15"/><text x="{c.x}" y="{c.y}" font-size="1.3" text-anchor="middle">{q["id"]}</text>')
 pieces.append('</svg>');(OUT/f'residual-{f["label"]}.svg').write_text(''.join(pieces))
save('space-program.json',{'source_sha256':hashlib.sha256((R/'docs/site-correction-v3/geometry.json').read_bytes()).hexdigest(),'findings':'Source residual is formed by building-envelope minus assigned programs. Nav excludes it; it is not evidence of a necessary MEP room. v2 3D does not fully detail or enclose every such area.','summaries':summaries,'spaces':spaces})
csvwrite('space-program.csv',[{k:v for k,v in q.items()if k not in ['polygon']}for q in spaces])
# Occupancy programming: zones remain inside existing sales or backroom; NOT applied to 3D.
large=[]
programs={
 '家電・生活大型店':[('体験・モバイル','入口の開放展示・受付'),('PC・映像','壁面TV・音響試聴'),('家電・住設','給排水デモ・大型商品'),('受取・修理受付','バックヤードとサービス接続')],
 '食品大型店':[('青果・旬','入口付近の低い平台'),('常温食品','奥まで見通せる1.8m棚間通路'),('冷蔵・冷凍','外周冷ケース・補充作業'),('精肉・鮮魚・惣菜','衛生前室・下処理・排水を裏側へ')],
 '書店・生活大型店':[('新刊・情報','入口平台・検索端末'),('一般書・文具','壁面書架と低い島'),('児童・学び','低い書架・読書席'),('専門書・生活','静かな奥のコレクション')],
 '大型衣料':[('季節・スタイリング','入口の低い商品台'),('衣料コレクション','複数の売場街区'),('試着・相談','倉庫側の試着室群'),('レジ・受取','入口から見える袋詰め・待ち列')],
 'フードホール':[('飲食テナント','厨房・排気・バックヤード側'),('共用客席','主通路3.6m・多様な卓'),('家族・静かな客席','大テーブル・植栽の席境界'),('返却・清掃','下膳・ごみ・手洗いを客の列と分離')],
 '生活・服飾':[('主力商品','入口ショーケース'),('壁面陳列','奥行きのある棚・生活提案'),('試着・サービス','鏡・椅子・相談'),('レジ・在庫受取','バックヤード接続')],
 '書籍・雑貨':[('新刊平台','低い平台・サイン'),('コレクション','壁面棚・回遊書架'),('文具・ギフト','体験台・包装'),('読書・レジ','座席・受付・作業台')],
 'カフェ':[('注文・受取','列と受取を交差させない'),('調理・洗浄','作業台・冷蔵・シンク'),('ラウンジ客席','ソファ・個人席'),('窓側客席','ベンチ・大テーブル')],
 'レストラン':[('受付・待合','入口前室・案内'),('テーブル席','主動線と配膳動線'),('半個室・多人数席','視線と音の緩衝'),('厨房・洗浄','排水・排気・搬入に近接')],
}
for f in B:
 for s in f['stores']:
  if s['polygon'].area<500:continue
  category=s['category'];sales=s['sales'];u=np.array(s['u']);n=np.array(s['n']);e=np.array(s['entry']);spine=LineString(s['main_route']).buffer(1.8,cap_style=2).intersection(sales);usable=sales.difference(spine);zones=[];rooms=[]
  coords=[np.array(c)for p in polys(sales)for c in p.exterior.coords];aa=[float(np.dot(q-e,u))for q in coords];bb=[float(np.dot(q-e,n))for q in coords];alo,ahi=min(aa),max(aa);blo,bhi=min(bb),max(bb)
  def localbox(a0,b0,a1,b1):return Polygon([tuple(e+u*a+n*b)for a,b in[(a0,b0),(a1,b0),(a1,b1),(a0,b1)]]).intersection(usable)
  if category=='シネマ複合':
   # Concrete, smaller halls fit the existing clear height; no silent giant-screen roof change.
   for bb0 in np.arange(blo,bhi-18,2):
    for aa0 in np.arange(alo,ahi-12,2):
     r=rect(e+u*(aa0+6)+n*(bb0+9),u,12,18)
     if usable.buffer(-.3).covers(r)and all(r.distance(t)>1.5 for t in rooms):rooms.append(r)
     if len(rooms)>=4:break
    if len(rooms)>=4:break
   for i,r in enumerate(rooms):zones.append({'id':f'HALL-{i+1}','name':f'小型上映室{i+1}','polygon':r,'use':'12×18m、10列×8席の検討。段床上昇0.72m、音響天井0.35m。確認は平面収まりのみ。','capacity_proposal':80})
   remainder=usable.difference(unary_union(rooms));zones.append({'id':'CINEMA-LOBBY','name':'ロビー・売店・音響緩衝・投映設備の詳細化対象','polygon':remainder,'use':'残り全てが客席ではない。防音前室・避難・投映・設備区画は次の詳細設計。'})
  else:
   seq=programs[category];am=(alo+ahi)/2;bm=blo+(bhi-blo)*.45
   ranges=[(alo,blo,am,bm),(am,blo,ahi,bm),(alo,bm,am,bhi),(am,bm,ahi,bhi)]
   for i,((name,use),r)in enumerate(zip(seq,ranges)):
    poly=localbox(*r)
    if not poly.is_empty:zones.append({'id':f'Z{i+1}','name':name,'polygon':poly,'use':use})
  zones.append({'id':'STOCK','name':'既存バックヤード','polygon':s['backroom'],'use':'既存の受口・在庫領域。食品・飲食は衛生区分、映画は運用室の個別設計が必要。'})
  union=unary_union([z['polygon']for z in zones]);zoneoverlap=sum(z['polygon'].area for z in zones)-union.area;outside=union.difference(s['polygon']).area
  critical=[]
  if category in ['食品大型店','カフェ','レストラン','フードホール']:critical.append('冷蔵能力・給排水・排気・ごみ回収・衛生区分は未計算。厨房の運用可能判定はしない。')
  if category=='シネマ複合':critical.append(f'平面上に12×18m小型室{len(rooms)}室を配置。4.825mの既存内法から音響天井0.35m・最奥段床0.72mを引くと3.755m。大スクリーンの大型上映室は現在断面では保証できない。遮音・避難・バリアフリー・投映視線は未検証。')
  critical.append('6m核店入口または既存専門店入口、既存の主経路・在庫受口を維持。外観・給排水・構造変更は未適用。')
  study={'id':s['id'],'floor':f['label'],'category':category,'plot':s['polygon'],'entry':s['entry'],'back_door':s['back_door'],'door_width_m':s['door_width_m'],'loading_door':s.get('loading_door'),'area_m2':s['polygon'].area,'sales_m2':sales.area,'height_clear_m':[4.825,4.65,4.825][f['level']],'main_spine':spine,'spine_width_m':3.6,'zones':zones,'shared_zone_overlap_m2':zoneoverlap,'outside_plot_m2':outside,'geometry_check':outside<1e-6 and zoneoverlap<.01,'circulation_status':'Main-spine reservation only; fixture faces, all zone accesses, evacuation, MEP and Godot walking NOT VERIFIED','notes':critical,'implementation_status':'DESIGN STUDY ONLY; outside current 3D validation crop'};large.append(study)
  x0,z0,x1,z1=s['polygon'].bounds;margin=3;pieces=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0-margin} {z0-margin} {x1-x0+2*margin} {z1-z0+2*margin}" width="1200" height="900"><path d="{svgpath(s["polygon"])}" fill="#f7f6ef" stroke="#3b4b43" stroke-width=".15"/>']
  cols=['#c9d9cb','#e6d5b6','#c6d1df','#dcc5ba','#d4d0b6']
  for i,z in enumerate(zones):
   p=z['polygon'];pieces.append(f'<path d="{svgpath(p)}" fill="{cols[i%len(cols)]}" stroke="#6f766c" stroke-width=".10"/>')
   if not p.is_empty:c=p.representative_point();pieces.append(f'<text x="{c.x}" y="{c.y}" font-size=".9" text-anchor="middle">{z["id"]}</text>')
  pieces.append(f'<path d="{svgpath(spine)}" fill="#fcfbf6" stroke="#508070" stroke-width=".12"/>');e0=s['entry'];pieces.append(f'<circle cx="{e0[0]}" cy="{e0[1]}" r=".7" fill="#b74434"/></svg>');(OUT/(s['id']+'.svg')).write_text(''.join(pieces))
save('large-store-studies.json',large)
csvwrite('large-store-program.csv',[{'id':s['id'],'floor':s['floor'],'category':s['category'],'plot_m2':s['area_m2'],'sales_m2':s['sales_m2'],'clear_height_m':s['height_clear_m'],'door_m':s['door_width_m'],'zone':z['id'],'zone_name':z['name'],'zone_m2':z['polygon'].area,'program':z['use'],'status':s['implementation_status']}for s in large for z in s['zones']])
# Refine rather than apply the two previous mergers: retaining a primary entry and staff access.
mergers=[]
for old in audit['proposals_not_applied']:
 floor=1 if'2F'in old['id']else 2;f=B[floor];ss=[next(s for s in f['stores']if s['id']==id)for id in old['stores']];p=unary_union([s['polygon']for s in ss]);byentry=sorted(ss,key=lambda s:-p.boundary.intersection(f['public'].buffer(.03)).intersection(Point(s['entry']).buffer(6)).length);main=byentry[0];others=[s for s in ss if s['id']!=main['id']]
 # Proposed sales uses the existing combined sales, stock remains separate. No public cut.
 sales=unary_union([s['sales']for s in ss]);stock=unary_union([s['backroom']for s in ss]);contact=p.boundary.intersection(f['public'].buffer(.03));neighbor=[s for s in f['stores']if s['id']not in old['stores']and p.distance(s['polygon'])<.03]
 connections=[]
 for a,b in itertools.combinations(ss,2):
  line=a['polygon'].boundary.intersection(b['polygon'].boundary)
  if line.length>1.5:
   seg=max(lines(line),key=lambda q:q.length);pt=seg.interpolate(.5,normalized=True);connections.append({'a':a['id'],'b':b['id'],'shared_length_m':line.length,'proposed_internal_portal_center':[pt.x,pt.y],'portal_width_proposal_m':min(3.6,max(1.5,seg.length-.5)),'status':'Not cut; structural wall and sales/stock topology review pending'})
 merger={**old,'primary_entry_store':main['id'],'primary_entry':main['entry'],'entry_width_m':main['door_width_m'],'secondary_customer_entries_retained':[{'store':s['id'],'entry':s['entry'],'width_m':s['door_width_m']}for s in others[:1]],'remaining_entry_treatment':'残る入口は案内・ショーウィンドウ化を検討。未適用。避難出入口数の合格とはしない。','all_existing_staff_entries_retained':[{'store':s['id'],'p':s['back_door']}for s in ss],'public_contact_length_m':contact.length,'sales_m2':sales.area,'stock_m2':stock.area,'adjacent_store_ids':[s['id']for s in neighbor],'adjacent_area_range_m2':[min(s['polygon'].area for s in neighbor),max(s['polygon'].area for s in neighbor)]if neighbor else[],'internal_portal_studies':connections,'recommended_use':'中型ライフスタイル書店（文具・読書席）'if floor==1 else'中型スポーツ・ホビー店（体験台・相談）','balance_assessment':'大型核店の移設は不要。周辺の小・中型区画を残し、途中に1か所だけ長い滞在型店舗を加える。3区画分の店種と入口リズムを失うトレードオフあり。','status':'PROPOSAL_ONLY; no polygons, IDs, entries or walls changed','checks':'連結・共有境界・公道不侵入は平面で確認。店舗内部の全到達性、壁の構造、避難・MEPは未検証。'};mergers.append(merger)
save('merger-review.json',mergers)
# Recover the old bookshop footprint count using the exact v1 placement condition; verify against metadata.
v1=read('/workspace/FIND_YOURSELF-B-Time-Plaza-v1/source/scene-manifest.json');v2=read('/workspace/FIND_YOURSELF-B-Time-Plaza-v2/source/scene-manifest.json');v3=read(P/'source/scene-manifest.json');density=[]
for f in B:
 for s in f['stores']:
  if s['category']not in ['書籍・文具','書籍・雑貨']or not s['polygon'].intersects(CROP):continue
  poly=s['polygon'].intersection(CROP);shelf=s['shelf_zones'].intersection(CROP);x0,z0,x1,z1=poly.bounds;fps=[]
  for xx in np.arange(x0+1,x1,3):
   for zz in np.arange(z0+1,z1,3.1):
    fp=rect((xx,zz),s['u'],1.7,.65)
    if shelf.buffer(-.12).covers(fp):fps.append(fp)
  a=next(q for q in v1['shops']if q['id']==s['id']);b=next(q for q in v2['shops']if q['id']==s['id']);c=next(q for q in v3['shops']if q['id']==s['id']);assert a['fixtures']==len(fps)
  density.append({'id':s['id'],'floor':f['label'],'fully_inside_crop':CROP.covers(s['polygon']),'sales_m2':s['sales'].intersection(CROP).area,'v1_recovered_fixture_count':len(fps),'v1_fixture_reserved_m2':unary_union(fps).area,'v2_fixture_count':b['fixtures'],'v2_fixture_reserved_m2':unary_union(b['fixture_footprints']).area,'v3_fixture_count':c['fixtures'],'v3_fixture_reserved_m2':unary_union(c['fixture_footprints']).area,'count_decreased_v1_to_v2':b['fixtures']<a['fixtures'],'note':'配置組数は什器種類・高さが異なり、視覚的密度の直接尺度ではない。v1値は生成条件を復元し原台帳の組数と照合。'})
csvwrite('bookshop-comparison.csv',density);save('bookshop-comparison.json',density)
print('PROGRAM_REVIEW',len(spaces),'residual entries',len(large),'large stores',len(mergers),'merger proposals',len(density),'bookshops',flush=True)
print('RESIDUAL',[(q['floor'],round(q['area_m2'],3),round(q['source_residual_m2']/q['area_m2']*100,5))for q in summaries],flush=True)
