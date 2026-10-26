"""Final v3 review drawings from the corrected data only; no old uncorrected plans appended."""
from site_v2_common import *
import fitz,ast,collections
O=R/'docs/site-correction-v3';D=read(O/'geometry.json');S=D['site'];P=read(O/'parking-geometry.json');VER=read(O/'independent-verification.json');VEH=read(O/'vehicle-verification.json');F={w:{f['level']:f for f in D['floors']if f['wing']==w}for w in['A','B','C']};BN={'existing_core_opening_proposals':[],'car_ramps':read(R/'docs/b-completion-v2/geometry.json')['car_ramps']};FONT=R/'assets/fonts/NotoSansCJKjp-Regular.otf';JP=fitz.Font(fontfile=str(FONT));DOC=fitz.open();TOC=[];PAGES=[]
INK=(.14,.21,.25);GREY=(.43,.47,.49);RED=(.78,.22,.18);GREEN=(.27,.58,.36);BLUE=(.15,.45,.7);ORANGE=(.9,.58,.22)
# Reuse only pure vector drawing functions. No v2 script top-level code is run.
src=(R/'tools/draw_site_completion_v2.py').read_text().replace('全体設計 v2','修正版 v3').replace('(未適用)','(v3設計反映)').replace("if prop['wing']==w and prop['level']==f['level']:","if prop['wing']==w and prop['level']==f['level'] and clip.covers(Point(prop['entry'])):")
names=['text','page','paras','xy_map','geom','label','arrow','scale','grid','floor_plan','site_plan']
for n in ast.parse(src).body:
 if isinstance(n,ast.FunctionDef)and n.name in names:exec(compile(ast.Module(body=[n],type_ignores=[]),'drawing_functions','exec'),globals())
def plan(p,w,f,rr,ext=None):
 xy,sc=floor_plan(p,w,f,rr,ext);ext=ext or f['floor_plate'].union(f['public']).buffer(5).bounds;clip=box(*ext)
 for v in f.get('vertical_devices',[]):
  for k,col in [('front_landing',(.73,.88,.72)),('lift_landing',(.7,.86,.94))]:geom(p,v[k].intersection(clip),xy,col,GREEN,.3)
  geom(p,v['cabin_floor_when_docked'].intersection(clip),xy,(.77,.9,.98),BLUE,.5);geom(p,v['lift_sill_when_docked'].intersection(clip),xy,None,BLUE,.7)
  if v['mid_landing_elevation_m']is not None:geom(p,v['mid_landing'].intersection(clip),xy,None,ORANGE,.6)
 geom(p,f['envelope_walls'].intersection(clip),xy,INK,INK,.25);geom(p,f['vestibule_walls'].intersection(clip),xy,INK,INK,.25)
 for d in f['doors_v3']:
  for k,col in [('side_walls',INK),('frames',INK),('open_leaves',BLUE)]:geom(p,d[k].intersection(clip),xy,col,col,.6)
  geom(p,d['clear_path'].intersection(clip),xy,None,GREEN,.8)
 return xy,sc
p=page('FIND YOURSELF｜敷地全体設計 修正版 v3','原本を保護した新しい設計版。ゲーム未実装・ユーザー最終承認前。',1191,842)
paras(p,[f'B館1〜3Fの旧不合格65件を再照合し、残存{VER["old_65_remaining"]}件。全15層の独立検査{VER["checks"]:,}件、失敗{len(VER["failed"])}件。','3館の基本外形・15層・店舗/施設470区画・駐車6,699区画を維持。修正は境界、入口、設備前の局所動線と車路接続に限定しています。','追加来客入口3か所は、玄関床・躯体開口・枠・開閉パネル・有効幅・段差0・両側待機床を新設計データへ反映。従来の未適用ラベルのままではありません。','A/Bの全30コア階図で床穴と乗降床を統合。階段の中間踊場は半階の高さ、EVキャビン床/敷居は可動設備として、構造床の穴と区別しています。',f'車両は10到着路線の平面掃引と34寸法項目を確認。未検証{VEH["status_counts"]["NOT_TESTED"]:,}件をNOT_TESTEDと明記し、合格に数えません。6,699は設計区画数で、全枠の運用可能台数を保証した値ではありません。','Godotのゲーム本体、既存A/B/C原本、v2図面/データは無変更。実歩行・実車・構造・法規・対向車を含む交通運用は未検証です。'],size=14,gap=18)
p=page('v2→v3｜修正範囲と変えていない基準','建物外形・広場・店舗構成・駐車マスの位置/数を保持。必要な機能を通すための局所修正です。',1191,842)
counts=collections.Counter(q['kind']for q in D['changes']);paras(p,['B旧65：店舗境界56ペア、店舗/共用床3階分、入口と公開床の距離1cm超6件を、新設計へ反映して再検査。','A/B設備口：壁を考慮した検査で店舗境界が扉前へかかる箇所を抽出。店数や館形を変えず、扉前の小さな区画退避と既存閾部の床接続を修正。',f'設備口近傍の局所店舗調整：A {counts["A_core_threshold_local_store_recess"]}区画階、B {counts["B_core_threshold_local_store_recess"]}区画階。変更ポリゴンと面積はchange-register.json。',f'C：設備前の既存ベンチ/植栽 {counts["C_equipment_approach_furniture_shift"]}点を近傍へ移設。床・庭・デッキの形を増やさず入口を空けました。','駐車場：個別枠の後方アクセス線と共用歩道の間にあった0.8m前後の余裕帯を、幅1mの短い後方歩行エプロンとして明示。車路/駐車マスとは重ならず、既存床上に収まることを検査。','車両：A南平面の入口を敷地境界に沿う横向き接触から、入口法線に沿う12m直線アプローチへ修正。B東はトラックを西へ無理に曲げず、搬入専用縦車路上の停止へ整理。B西は停止位置を0.3m手前へ。','前回解消したB共用床/閉鎖帯の重複は0㎡を維持。今回の店舗/共用床との重複とは別の区分です。'],size=13,gap=18)
p=page('全体配置図｜修正版 v3','灰：来客車／茶：搬入車／緑：地上歩行／青：歩道橋。C搬入ヤードはB1 -5.35m。')
site_plan(p,(85,120,1595,1000))
for title,ext in [('A館周辺：新来客口2か所・A南車路修正',(-220,-100,520,550)),('B館周辺：新来客口・駐車場接続',(-1140,-100,-140,330)),('C館周辺：屋外歩行・地下搬入',(-820,-650,-170,-75))]:
 p=page(title,'建物/駐車マス配置を維持。追加入口は新設計で開口済みの表現、ゲーム本体には未実装。');site_plan(p,(85,120,1595,1000),ext,'detail')
p=page('全15層｜寸法・店舗数・共用床/実歩行用床','public＝共用通路。nav_free＝壁/什器/穴を除いた床＋設備核の利用可能床。集計範囲が異なります。',1191,842)
y=120;text(p,45,y,'館/階      Y(m)       外接X×Z(m)        区画     共用通路㎡       歩行用床㎡',12);y+=30;dim=[]
for w in['A','B','C']:
 for lev in[-1,0,1,2,3]:
  f=F[w][lev];a,b,c,d=f['shell'].bounds;row=[w,LABEL[lev],HEIGHT[lev],c-a,d-b,len(f['stores']),f['public'].area,f['nav_free'].area];dim.append(row)
  for x,v in zip([45,190,310,570,710,925],[w+' '+LABEL[lev],f'{HEIGHT[lev]:+.3f}',f'{c-a:.1f} x {d-b:.1f}',len(f['stores']),f'{f["public"].area:,.1f}',f'{f["nav_free"].area:,.1f}']):text(p,x,y,v,11)
  y+=33
paras(p,['階段/EV穴は床面積に含めず、停止時のキャビン床も構造床の埋戻しとして加算しません。屋外歩道/庭/デッキを躯体投影に混ぜません。','C館1F：躯体6棟投影18,953.028976㎡／公開床21,418.377759㎡。前回の排他的面積表は原本保持。今回の什器位置修正は公開床ポリゴンを変更しません。'],y=y+15,size=12,gap=12)
csvwrite(O/'15-floor-dimensions.csv',['館','階','Y','X外接m','Z外接m','店舗施設区画','共用通路㎡','歩行用床㎡'],dim)
# Every corrected floor, with enlargements; never append the old uncorrected v2 floor atlas.
for w in['A','B','C']:
 for lev in[-1,0,1,2,3]:
  f=F[w][lev];p=page(w+'館 '+LABEL[lev]+'｜v3詳細平面図',f'Y {HEIGHT[lev]:+.3f}m／店舗・施設 {len(f["stores"])}／ピンク：実際の構造床開口／橙線：別高さの中間踊場投影／青：停車時EV機器床')
  plan(p,w,f,(85,120,1595,1000));PAGES.append(dict(wing=w,level=lev,page=len(DOC)))
  a,b,c,d=f['floor_plate'].union(f['public']).bounds;n=3 if w=='B'else 2
  for j in range(n):
   ext=(a+(c-a)*j/n-4,b-4,a+(c-a)*(j+1)/n+4,d+4);p=page(w+'館 '+LABEL[lev]+f'｜拡大 {j+1}/{n}','入口・店内主路・バックルーム・壁・設備前を原ポリゴンで表示。全図は設計段階でありゲーム実装済みではありません。');plan(p,w,f,(85,120,1595,1000),ext)
# Customer door details include actual wall openings and physical panel states.
for door in D['doors']:
 p=page('追加来客入口｜'+door['id'],'開口/扉/枠/玄関床/待機床をv3へ統合。開扉状態の歩行可能領域を再検査。')
 x,z=door['center'];ext=(x-10,z-10,x+12,z+12);xy,sc=plan(p,door['wing'],F[door['wing']][door['level']],(90,130,1060,980),ext)
 for g in door['landings']:geom(p,g,xy,None,GREEN,1.2)
 geom(p,door['clear_path'],xy,None,GREEN,1.5);geom(p,door['frames'],xy,INK,INK,.5);geom(p,door['open_leaves'],xy,(.4,.7,.9),BLUE,.6)
 paras(p,[f'有効幅 {door["clear_width_m"]:.1f}m／躯体開口 {door["frame_opening_width_m"]:.2f}m／枠外寸 {door["overall_frame_width_m"]:.2f}m',f'扉高 {door["door_height_m"]:.1f}m／玄関幅 {door["vestibule_width_m"]:.1f}m／段差0m',f'扉中心 X {x:.6f}, Y {door["height"]:.3f}, Z {z:.6f}','躯体孔は枠外寸より左右各2cm大きく取り、取付部を充填。扉枠と玄関側壁の間も壁パネルで閉じ、隙間を残しません。','4枚テレスコピック自動引戸。開扉パネルは両側の収納部に置き、有効開口へ張り出しません。','緑矩形＝両側1.5m待機床。開扉時の壁/枠/パネルと重ならず、構造床に支持されることを確認。','閉扉時は中央をパネルが塞ぐ設計。図面検査の通行判定は開扉状態。センサーや開閉動作はGodot未実装。'],x=1120,y=150,width=500,size=14,gap=24)
 # Metric elevation of the actual clear aperture, under a separate height coordinate.
 exy,sc=xy_map((-door['overall_frame_width_m']/2,-door['door_height_m'],door['overall_frame_width_m']/2,.4),(1130,700,1590,950));geom(p,box(-door['overall_frame_width_m']/2,-door['door_height_m'],door['overall_frame_width_m']/2,0),exy,None,INK,1);geom(p,box(-door['clear_width_m']/2,-door['door_height_m'],door['clear_width_m']/2,0),exy,None,GREEN,1.2)
# Six core plans and matching vertical sections show floor and half-floor elevations explicitly.
for w in['A','B']:
 for v0 in F[w][0]['vertical_devices']:
  coreid=v0['core'];c=next(c for c in F[w][0]['cores']if c['id']==coreid);p=page(w+'館 '+coreid+'｜階段・EVの床開口/乗降/断面','全5階は同じ平面位置。中間踊場は半階に置く別スラブ。キャビン床/敷居は可動設備で、穴を埋めません。')
  ext=c['outline'].buffer(1.8).bounds;xy,sc=plan(p,w,F[w][0],(100,150,850,980),ext)
  for k,col in [('front_landing',GREEN),('mid_landing',ORANGE),('lift_landing',BLUE)]:geom(p,v0[k],xy,None,col,1.5)
  for flight in[v0['lower_flight_projection'],v0['upper_flight_projection']]:geom(p,flight,xy,None,RED,1)
  paras(p,['前方緑：その階の階段乗降床。橙：半階上の折返し踊場の投影。青：EV前1.8×1.5m乗降床。','各フライト有効幅2m、踏面0.30m、16段×2。片フライト水平長4.5m。階高に応じ蹴上を調整。','階段の底部B1は基礎床を保持し、上階の構造床には斜路用の穴を反映。別スラブの中間踊場と重ねて平床扱いしません。','EV内法開口は14.44㎡。停止時キャビンと敷居板を別部品で表示、前方隙間は設計値0.02m。稼働/安全装置/構造は未検証。'],x=930,y=135,width=650,size=13,gap=16)
  xy,sc=xy_map((-2,-18.5,14,7),(950,480,1550,1010))
  for lev in[-1,0,1,2,3]:
   yy=-HEIGHT[lev];geom(p,LineString([(-1,yy),(1,yy)]),xy,None,INK,1.4);geom(p,LineString([(10,yy),(13,yy)]),xy,None,INK,1.4);label(p,(10.2,yy),LABEL[lev]+' '+str(HEIGHT[lev])+'m',xy,8)
   if lev<3:
    mid=-(HEIGHT[lev]+HEIGHT[lev+1])/2;geom(p,LineString([(1,yy),(5.5,mid),(7.5,mid),(12,-HEIGHT[lev+1])]),xy,None,BLUE,1.2);label(p,(5.6,mid),'中間 '+str(round(-mid,4))+'m',xy,7,ORANGE)
# Old 65 issues, every item, compare original value and the NEW full-revision check result.
old=read(O/'65-replayed-checks.json')
for start in range(0,len(old),22):
 p=page(f'旧65件の修正・再照合｜{start+1}〜{min(start+22,65)}','旧原本は変更せず、新しい15層データに対する同じ検査IDで再照合。全項目の新値/状態を記録。',1191,842);y=120
 text(p,45,y,'旧項目 / ID                                             旧値              新値       結果',12);y+=32
 for q in old[start:start+22]:
  text(p,45,y,q['id'],10);text(p,575,y,f'{q["old_value"]:.9f}'if isinstance(q['old_value'],(int,float))else str(q['old_value']),9);nv=q['new_value'];text(p,790,y,f'{nv:.10g}'if isinstance(nv,(int,float))else str(nv),9);text(p,1010,y,'PASS'if q['pass_']else'FAIL',10,GREEN if q['pass_']else RED);y+=26
# Actual updated external parking floors, including rear aprons and changed active guards.
for fac in P['facilities']:
 for pf in fac['floors']:
  p=page(fac['id']+' '+pf['label']+f'｜駐車詳細 {len(pf["stalls"])}区画',f'Y {pf["height"]:+.3f}m／個別番号＋施設/駐車段接頭辞でID照合。緑：歩道と短い後方エプロン、黄：指定横断部。')
  ext=pf['shell'].buffer(3).bounds;xy,sc=xy_map(ext,(85,130,1595,1000));geom(p,pf['floor_plate'],xy,(.94,.94,.91),INK,.6);geom(p,pf['vehicle_aisles'],xy,(.77,.8,.83),GREY,.3);geom(p,pf['pedestrian'],xy,(.66,.86,.69),GREEN,.3);geom(p,pf['crossings'],xy,(.95,.85,.59),ORANGE,.3)
  for st in pf['stalls']:
   geom(p,st['polygon'],xy,(.65,.83,.94)if st['category']=='accessible'else(.84,.89,.94),BLUE,.2);label(p,st['polygon'].centroid.coords[0],st['id'].split('-')[-1],xy,4.1)
  for c in pf['cores']:
   geom(p,c['outline'],xy,None,INK,.5);geom(p,c['stair'],xy,(.85,.78,.7),INK,.4);geom(p,c['elevator'],xy,(.7,.83,.93),BLUE,.4);label(p,c['entry'],c['id'].split('-')[-1],xy,7)
  for lane in fac['ramp_lanes']:geom(p,lane['shaft'],xy,(.65,.7,.79),BLUE,.5)
  for key in['edge_guard','temporary_guard_until_bridge_built','ramp_terminal_barriers']:geom(p,pf.get(key,Polygon()),xy,(.55,.3,.3),RED,.4)
  grid(p,xy,ext,(85,130,1595,1000));scale(p,xy,sc,(85,130,1595,1000),20)
# Vehicle routes: status and a sampled body envelope, not a circular symbol labelled as proof.
p=page('車両動線｜検査範囲・車体モデル・未検証の区別','PASS_2D_SAMPLEDは指定到着方向の平面車体掃引のみ。個別駐車・出庫・対向車・3Dには適用しません。',1191,842)
paras(p,[f'結果：到着路線の平面掃引 {VEH["status_counts"].get("PASS_2D_SAMPLED",0)}路線合格、寸法 {VEH["status_counts"].get("PASS_DIMENSION",0)}項目合格、FAIL {len(VEH["failures"])}、NOT_TESTED {VEH["status_counts"]["NOT_TESTED"]:,}件。','乗用車：全長4.8m、幅1.9m、軸距2.8m、後端1.0m、後車軸半径6m。トラック：全長12m、幅2.5m、軸距6m、後端3m、後車軸半径12m。メーカー固有値ではない設計モデル。','後車軸を接線円弧へ通し、車体矩形の前端/後端振出しを含めて掃引。直線0.25m刻み、円弧0.5度刻み、連続姿勢間を凸包でつなぎ、さらに0.02mの余裕を加えて舗装内を確認。','入口法線：A南は旧横付けから12m直線で正対する入口へ。B東トラックは縦車路上停止で不要な西向き屈曲を整理。B西の停車位置は0.3m手前に修正し、車体前端の余裕を確保。','未検証：全6,699枠の前後進/切返し、10路線の出庫/ヤード反転、駐車棟の全コーナー、B地下/屋上内部の最小半径経路、斜面での車体姿勢/腹擦り/桁下、対向車・交差交通、実車。','したがって「6,699台すべての入出庫が成立」とは報告しません。設計マス実数6,699、車両検証済み運用台数は未確定です。未検証行はvehicle-status-ledger.csvに個別IDで記録。'],size=13,gap=20)
SWEEPS=read(O/'vehicle-sweeps.json')
for q in SWEEPS:
 p=page('車体掃引｜'+q['id'],'指定到着方向のみの平面検査。灰：許可された舗装／青：車体掃引＋2cm余裕／赤：はみ出し（合格時なし）。')
 ext=q['swept'].buffer(12).bounds;xy,sc=xy_map(ext,(85,130,1030,970));geom(p,q['allowed'],xy,(.87,.88,.89),GREY,.3);geom(p,q['swept'],xy,(.59,.78,.93),BLUE,.4);geom(p,q['outside'],xy,(.97,.35,.25),RED,1)
 for pt,h in q['poses']:
  # Rear-axle reference shown; full footprint is the filled sampled envelope.
  geom(p,Point(pt),xy,None,BLUE,.2)
 coords=list(q['line'].coords);centres=[coords[-1],coords[-2]]
 for j,cen in enumerate(centres):
  extent=(cen[0]-22,cen[1]-22,cen[0]+22,cen[1]+22);rr=(1110,150+j*390,1590,480+j*390);ax,s=xy_map(extent,rr);clip=box(*extent);geom(p,q['allowed'].intersection(clip),ax,(.87,.88,.89),GREY,.4);geom(p,q['swept'].intersection(clip),ax,(.59,.78,.93),BLUE,.7);geom(p,q['outside'].intersection(clip),ax,(.97,.35,.25),RED,1);grid(p,ax,extent,rr);text(p,1110,rr[1]-18,'停止/入口部 拡大'if j==0 else'最終曲がり角 拡大',12)
 text(p,90,1030,f'モデル {q["model"]} / 掃引外面積 {q["outside"].area:.10f}㎡ / PASS_2D_SAMPLED / 出庫・対向車・3D・実車はNOT_TESTED',12)
p=page('最終検査・残課題｜承認前の設計資料として提出','Godotゲーム本体への実装は開始していません。図面上の接続と実歩行/車両動作を区別。',1191,842)
paras(p,[f'建築/歩行の独立検査 {VER["checks"]:,}件、失敗 {len(VER["failed"])}件。旧65件は同じ検査IDで残存0件。15層、全470店舗/施設の入口、駐車場から全階/他館への接続を検査。','プレイヤーは半径0.30mの円を平面で通す設計基準。壁・枠・開扉パネル・什器・床穴を引いた連続領域で判定し、到達しない点を都合よく近傍へ置換していません。','階段は各階/中間階の高さ、EVは穴・乗降床・停止時可動キャビンを区別。実際の衝突・ステップ制御・EV制御・自動扉センサーは未実装。',f'原本保護：{VER["protected_originals"]}ファイルのSHA照合。既存ゲーム/既存図面/既存台帳は無変更。今回の修正版データはdocs/site-correction-v3へ分離。','残課題：NOT_TESTED車両軌跡、対向交通/需要、ゲーム内実歩行/車両/人混み、構造荷重/柱梁/基礎、EV機器/ピット/昇降路頂部、排水/擁壁、防災/避難/法規、NPC/宝箱/案内図/FT/セーブ連携。','A東の追加搬入扉はv2の別案をそのまま保持し、今回の来客入口3か所と混ぜて完成扱いしません。搬入の台車運用や兼用EVの積載容量も未検証です。','今回の作業は設計資料の更新まで。ユーザーが修正版を確認・承認するまでGodotへの実装は禁止の状態で終了します。'],size=13,gap=18)
DOC.set_toc(TOC);out=R/'downloads/FIND_YOURSELF-Site-Correction-v3.pdf';DOC.save(out,garbage=3,deflate=True);DOC.close();write(O/'atlas-pages.json',PAGES);write(O/'pdf-source.json',dict(pdf=str(out.relative_to(R)),sha256=sha(out),source_sha256={str(p.relative_to(R)):sha(p)for p in[O/'geometry.json',O/'parking-geometry.json',O/'independent-verification.json',O/'vehicle-verification.json',O/'65-replayed-checks.json']}));print('PDF',fitz.open(out).page_count,'pages',out.stat().st_size,'bytes')
