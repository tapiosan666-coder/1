from pathlib import Path
import sys,ast,math,csv,json,io,collections
sys.path.insert(0,str(Path(__file__).resolve().parent));from site_v2_common import *
import fitz
from PIL import Image
P=Path(__file__).resolve().parents[1];S=P/'source';E=P/'evidence';D=read(S/'design-v6.json');B=read(S/'baseline-v5.json');A=read(S/'annex-v6.json');C=read(S/'corner-revisions.json');Q=read(E/'geometric-results-v6.json');SCENE=read(S/'scene-manifest.json');doc=fitz.open();fontfile=P/'assets/NotoSansCJKjp-Regular.otf';font=fitz.Font(fontfile=str(fontfile));ink=(.13,.19,.19);green=(.18,.43,.34);rect_fn=rect
# Reuse only tested vector/text utilities, never execute the old report's workflow.
src=ast.parse((P/'authoring/drawing_primitives.py').read_text());names={'text','page','paragraphs','table','plan'}
for n in src.body:
 if isinstance(n,ast.FunctionDef)and n.name in names:exec(ast.unparse(n).replace('街区再構成 v5','局所整合検証 v6'))
ledger=list(csv.DictReader(open(S/'all-198-store-ledger-v6.csv',encoding='utf-8-sig')));ll={q['id']:q for q in ledger}
paragraphs('B館 v6｜17店舗と上下階・連絡部の局所修正',[
 ('維持したもの','v5の198区画（旧188ID＋追加10）、広場の開放感、吹き抜け、基本の通路網と昇降設備位置を維持しました。修正は独立検証プロジェクトのみです。ゲーム本体、B館v4.1、敷地全体v3、過去の検証プロジェクトは変更・統合していません。'),
 ('17候補の再評価','旧検査は角の小さい側だけを測っていたため、実際の凸先端11件と、細い凹状の折返し5件・数値的な針状境界1件を同じ候補にしていました。向き付きの内角と実際の境界を調べ、11件は局所面取り、6件は元データの折返し除去で修正しました。隣接区画の所有境界も合わせ、用途不明な通路や新しい倉庫で隠していません。'),
 ('屋上と地下','屋上の不要な設備予約床を整理し、屋上駐車115台・車路・歩行通路を保持。屋上支持は位置・干渉を確認した検討案で、耐荷重・基礎・防水設計の成立を実証したものではありません。B1は1Fより広い地下躯体を維持し、外側部分は地下屋根・外構地盤との取り合いとして示しました。'),
 ('承認待ちと残課題','RF-SUPPORT-16（約4.10㎡、最大張出し約1.25m）は支持方式の確定が必要です。全支持部の構造計算、設備容量、全車両経路・立体駐車場スロープ、人間による実操作は未検証です。数値検査の合格を建築品質や運用上の完成認定にはしません。')])
# True before/after area ledger for every named candidate.
rr=[]
for e in C['events']:
 q=ll[e['id']];method={'architectural_chamfer':'局所面取り','numeric_notch':'凹状折返し除去','numeric_needle':'針状境界除去'}[e['method']];rr.append([e['id'],f"{e['old_angle_deg']:.3f}",method,f"{e['area_m2']:.6f}",f"{float(q['delta_net_vs_v5_m2']):+.3f}",f"{float(q['entry_shift_m']):.3f}",f"{float(q['door_width_m']):.2f}",e.get('neighbour')or e['ownership']])
table('17候補｜修正方法・面積・実入口',['ID','旧内角°','修正','影響面積㎡','実効売場差㎡','入口移動m','入口幅m','隣接先・用途'],rr,[95,80,140,120,120,100,90,265],20,notes='360°近い値は凸の鋭角ではなく凹状の折返し。売場差は同一壁厚基準でv5と比較。既存188区画の旧v4実効売場予算と、全198区画の作業矩形を保持。')
# Full-floor before/after, vector geometry.
for f,b in zip(D['floors'],B['floors']):
 p=page('B館 '+f['label']+'｜局所修正前後の詳細平面図','上：凍結v5／下：v6。店舗・入口・売場・裏方・共用・吹き抜けを区別。連絡先のプレビュー床はB館所有床と別計上。',2384,1684);bounds=b['floor_plate'].union(f['floor_plate']).bounds
 text(p,40,120,2200,25,'v5',15);plan(p,b,(40,150,2340,800),bounds,True,False);text(p,40,830,2200,25,'v6 独立変更案',15);plan(p,f,(40,865,2340,1515),bounds,False,False)
 text(p,40,1540,2300,60,'広場・吹き抜け・既存エスカレーター位置を維持。細部は次の17地点の拡大図と全198区画CSVを参照。A/C館内部は未施工で、接続先の実公開床の一部のみを検証用に表示しています。',12)
# Concrete local plans of all17; no abstract circles substituted for the actual walls.
for e in C['events']:
 lev=next(i for i,f in enumerate(D['floors'])if any(s['id']==e['id']for s in f['stores']));f=D['floors'][lev];b=B['floors'][lev];x,z=e['position_world_xz'];bounds=(x-7,z-7,x+7,z+7);p=page(e['id']+'｜境界と店舗内部の局所詳細','左：v5、右：v6。実際の区画・売場・裏方・入口・作業矩形・検査経路を表示。角だけを別の図形で塗りつぶす処理ではありません。')
 plan(p,b,(40,145,575,655),bounds,True,True);plan(p,f,(615,145,1150,655),bounds,False,True);q=ll[e['id']]
 text(p,40,685,1110,90,f"World X/Z = {x:.4f}, {z:.4f}m / 旧内角 {e['old_angle_deg']:.4f}° / 修正 {e['method']} / 面積 {e['area_m2']:.6f}㎡\n入口移動 {float(q['entry_shift_m']):.3f}m、幅 {float(q['door_width_m']):.2f}m。実効売場 {float(q['sales_net_v5_m2']):.3f} → {float(q['sales_net_v6_m2']):.3f}㎡。作業矩形と旧v4売場予算を保持。",11)
# Auxiliary plan primitives, actual coordinates and footprints.
def auxplan(p,bounds,r,roof,after=True,sweeps=False):
 x0,z0,x1,z1=bounds;rr=fitz.Rect(r);sc=min((rr.width-35)/(x1-x0),(rr.height-45)/(z1-z0));ox=rr.x0+(rr.width-(x1-x0)*sc)/2;oz=rr.y0+25
 def pt(q):return fitz.Point(ox+(q[0]-x0)*sc,oz+(q[1]-z0)*sc)
 clip=box(*bounds)
 def shape(g,col=None,line=(.4,.44,.43),width=.4):
  sh=p.new_shape()
  for po in polys(g.intersection(clip)):
   if po.area<1e-7:continue
   for ring in[po.exterior,*po.interiors]:sh.draw_polyline([pt(q)for q in ring.coords])
  sh.finish(color=line,fill=col,width=width,even_odd=True,closePath=True);sh.commit()
 if roof:
  rf=A['roof'];orig=next(f for f in read(S/'master-site-v3.json')['floors']if f['wing']=='B'and f['label']=='RF');plate=rf['floor_plate']if after else orig['floor_plate'];shape(plate,(.88,.88,.83));shape(rf['parking']['vehicle_aisles']if after else orig['parking']['vehicle_aisles'],(.62,.65,.64));shape(rf['public'],(.96,.92,.77))
  for st in rf['parking']['stalls']:shape(st['polygon'],(1,1,1))
  for zone in rf['gardens']:shape(zone['polygon'],(.80,.89,.78))
  if after:
   for bed in rf.get('plant_beds',[]):shape(bed['polygon'],(.32,.53,.32))
   shape(rf['removed_slab'],None,(.8,.38,.32))
   for q in A['support_reservations']:
    shape(q['polygon'],None,(.78,.41,.19))
    for c in q['column_centres']:shape(box(c[0]-.225,c[1]-.225,c[0]+.225,c[1]+.225),(.72,.31,.13))
    if q['id']in A['unplaced_support_reservations']:
     c=q['polygon'].representative_point();pp=pt((c.x,c.y));p.draw_circle(pp,9,color=(.8,.15,.1),width=1);text(p,pp.x+12,pp.y-5,140,40,q['id']+' 支持方式未決',8)
  if sweeps:
   for data,col in[(read(S/'vehicle-sweep-v6.json')['results'][0],(.55,.78,.91)),(read(S/'opposite-lane-sweep-v6.json'),(.91,.76,.50))]:shape(data['swept'],col,None)
 else:
  b=A['basement'];shape(b['floor_plate'],(.9,.9,.86));shape(b['public'],(.97,.94,.82));shape(b['above_basement_grade_cover'],(.84,.74,.61))
  for s in b['stores']:shape(s['polygon'],(.72,.85,.75))
  for c in b['cores']:shape(c['outline'],(.65,.74,.82))
  shape(D['floors'][0]['shell'],None,(.17,.35,.25),.7)
 p.draw_rect(rr,color=(.6,.65,.63),width=.4);text(p,rr.x0+8,rr.y0+3,rr.width-16,22,f'World X[{x0:.2f},{x1:.2f}] / Z[{z0:.2f},{z1:.2f}] m　縮尺1:{2834.64567/sc:.0f}',8)
 return pt,shape
p=page('RF｜床・駐車115台・車歩道・支持検討位置','v5ではRFの3Dは未施工でした。左は敷地全体v3の設計原本、右は独立v6の整合案。原本は変更していません。',2384,1684);bounds=A['roof']['floor_plate'].union(next(f for f in read(S/'master-site-v3.json')['floors']if f['wing']=='B'and f['label']=='RF')['floor_plate']).bounds
auxplan(p,bounds,(40,140,2340,800),True,False);auxplan(p,bounds,(40,850,2340,1510),True,True);text(p,40,1535,2300,80,f"屋上床 {A['old_roof_slab_m2']:.2f} → {A['new_roof_slab_m2']:.2f}㎡（{A['removed_roof_slab_m2']:.2f}㎡整理）。駐車115台、車路、歩道、屋上庭園ゾーンの面積は保持。橙は支持位置案。屋根外郭からの張出しは{A['remaining_roof_overhang_m2']:.2f}㎡。容量・構造・基礎は未検証。",12)
p=page('B1｜地下躯体と1F外郭・外構地盤との取り合い','地下を機械的に1Fへ縮めず、元の地下用途と床を保持。茶色は1F店舗外郭の外に出る地下屋根・外構の取り合い範囲。',1684,1190);auxplan(p,A['basement']['floor_plate'].bounds,(40,140,1640,970),False);text(p,40,1000,1580,100,f"地下床 {A['basement']['floor_plate'].area:.2f}㎡。地下屋根・外構の取り合い {A['basement']['above_basement_grade_cover'].area:.2f}㎡。防水、土被り、排水、基礎荷重、リフトピットの設計は未検証。Godotでは躯体と2店舗入口を確認する範囲で、地下の全設備・在庫内装は未施工。",13)
# Actual section at unresolved patch, not a diagram of invented levels.
p=page('実座標断面｜RF-SUPPORT-16付近 X = −397.00m','元データの床断面を表示。赤は支持方式未決の張出し位置。15層の原本へは未反映。');x=-397;z0,z1=-35,135;sc=5.5;ox=60;oy=650
for f in[A['basement'],*D['floors'],A['roof']]:
 y=f['height'];cut=LineString([(x,z0),(x,z1)]).intersection(f['floor_plate'])
 for ln in lines(cut):
  a,b=ln.coords[0],ln.coords[-1];p.draw_rect(fitz.Rect(ox+(a[1]-z0)*sc,oy-y*15,ox+(b[1]-z0)*sc,oy-y*15+5.7),fill=(.32,.39,.37),color=None)
 text(p,1000,oy-y*15-8,150,28,f"{f['label']} {y:.3f}m",10)
for y in[-5.35,0,5.525,10.875,16.4]:p.draw_line((55,oy-y*15),(990,oy-y*15),color=(.78,.8,.78),dashes='[2 3]',width=.3)
p.draw_line((ox+(52-z0)*sc,oy-16.4*15-10),(ox+(52-z0)*sc,oy-10.875*15),color=(.8,.15,.1),width=1.5);text(p,40,150,1100,75,'RF-SUPPORT-16：面積約4.10㎡、最大張出し約1.25m。客用通路を塞がない外部支持候補が不足し、上部フレームからの梁・持出し方式の検討が必要です。現在のモデルで安全に支持できると認定していません。',12)
text(p,40,705,1100,80,'階高・床開口の整合と、梁・柱・基礎の耐荷重は別の検証です。B1床には下向き階段開口が不要なため、階段の上向き投影・踊り場を上階と比較しています。RFの追加96㎡のトップライトは、下階に新たな吹き抜け穴を作るものではありません。',11)
vr=read(E/'interface-results.json')['vertical_checks'];table('昇降設備｜5層×3コアの図面照合',['階','コア','床高m','EV位置差㎡','階段投影差㎡','開口条件','CAD照合'],[[q['floor'],q['core'],f"{q['height_m']:.3f}",f"{q['lift_opening_offset_m2']:.6f}",f"{q['stair_flight_projection_offset_m2']:.6f}",'B1は底床・下向開口なし'if q['floor']=='B1'else'上階床開口',str(q['CAD_alignment_pass'])]for q in vr],[80,80,130,150,180,350,100],20,notes='位置・投影・開口の照合。B1/RFへの実装済み階段・エレベーターが使えることを意味しません。')
# Connection details / dimensions and real before-missing area.
table('A/B・B/C接続｜同じ高さと有効幅で接続',['ID','階高m','幅m','高さ差m','旧図面の接続隙間㎡','実装・検証範囲'],[[c['id'],f"{c['height']:.3f}",str(c['width_m']),f"{c['height_error_m']:.3f}",f"{c['floor_before_missing_m2']:.6f}",'B側通路→連絡橋→相手館の実公開床プレビュー']for c in A['connections']],[100,140,100,150,220,400],20,notes='A/B曲がり角にあった約0.00372㎡の局所差分を解消。橋端の仮表示は検証範囲を示すもの。相手館内装・全館経路は今回未施工。元のA/C館設計は変更していません。')
# Vehicle path with honest scope.
p=page('RF車両動線｜選択した曲がり角の車体掃引','黒：車路、青：往路、黄：対向車線。平面上の車体軌跡検査で、Godot車両物理・実車走行・人間の運転ではありません。',1684,1190);auxplan(p,(-585,50,-530,172),(40,140,800,1040),True,True,True);auxplan(p,(-556,55,-532,83),(850,140,1640,740),True,True,True)
v=read(S/'vehicle-sweep-v6.json')['results'][0];op=read(S/'opposite-lane-sweep-v6.json');text(p,850,780,760,290,f"車体4.8×1.85m、軸距2.7mはゲーム用仮定。往路半径6.0m／対向車線9.5m、0.10mごとに姿勢を計算。旧車路外への車体はみ出し{v['old_road_departure_m2']:.3f}㎡に対し、駐車マス・保護歩道を削らない{read(S/'vehicle-sweep-v6.json')['new_road_flare'].area:.3f}㎡の局所車路余裕を確保。\n\n対向車線の道路逸脱 {op['road_departure_m2']:.6f}㎡、掃引形状同士の最短離隔約{op['opposing_sweeps_separation_m']:.3f}m。速度・交通制御・路面勾配・他の曲がり角・駐車入出庫・立体Pスロープは未検証。全車両動線の合格とはしません。",12)
# Support reservations table, including unresolved1 explicitly.
rr=[]
for q in A['support_reservations']:rr.append([q['id'],f"{q['area_m2']:.3f}",f"{q['maximum_overhang_depth_m']:.3f}",str(len(q['column_centres'])),'支持方式未決'if q['id']in A['unplaced_support_reservations']else q.get('alternative','支持位置候補のみ'),'未検証','未検証'])
table('屋上支持｜位置案と未決事項',['ID','張出し㎡','最大奥行m','柱候補数','位置案の状態','耐荷重','基礎'],rr,[160,130,130,110,300,140,140],22,notes='柱0.45m角・梁0.55×0.75m等は可視化用の仮定。全て構造計算未実施。橙色は施工済み構造ではなく独立検証モデルの検討位置です。')
# Actual engine images only.
shots=read(S/'cameras.json');photo_count=0
for c in shots:
 after=E/('context'if c['scope']=='context'else'after')/(c['id']+'.png');before=E/'before'/(c['id']+'.png')
 if not after.exists():continue
 p=page('Godot実画面｜'+c['label'],'同一視点比較の前画像は凍結したv5メッシュ・旧床シェーダー。新設RF/B1文脈モデルと自動歩行到達点は変更後のみ。',1190,1684)
 def photo(f,r):
  global photo_count
  im=Image.open(f).convert('RGB');raw=im.tobytes();buf=io.BytesIO();im.save(buf,format='PNG',icc_profile=None);assert Image.open(io.BytesIO(buf.getvalue())).convert('RGB').tobytes()==raw;p.insert_image(fitz.Rect(r),stream=buf.getvalue());photo_count+=1
 if before.exists()and not c.get('after_only'):
  text(p,40,125,1100,28,'v5参照データ（検証ハーネスで表示）',14);photo(before,(40,160,1150,785));text(p,40,815,1100,28,'v6独立検証',14);photo(after,(40,850,1150,1475))
 else:text(p,40,125,1100,28,'変更後のみ',14);photo(after,(40,170,1150,795))
 text(p,40,1510,1100,105,'カメラLocal XYZ '+str(c['eye_local'])+' → '+str(c['look_local'])+'。World XZ原点 −429,46m。実Viewportの画素を変更せず収録。\n'+('自動物理歩行で記録された実際の到達位置。人間の操作ではありません。'if c.get('grounded_checkpoint')else'代表視点の画面確認であり、人間による全館実操作検証ではありません。'),10)
phys=read(E/'after/physical-results.json');paragraphs('検査結果の区別と残課題',[
 ('図面の独立再検査',f"{Q['passed']}件合格／{Q['failed']}件不合格。17候補の向き付き内角、198区画の入口・裏方作業矩形・予算、吹き抜け・共用床・屋上駐車115台と車歩道・館間接続を確認。短い辺があるだけで不合格にせず、面取り・壁厚の納まりと、狭い未用途空間を区別しました。"),
 ('Godot自動歩行',f"{phys['passed']}件合格／{phys['failed']}件不合格。半径0.3m・高さ1.8mの実CharacterBody3Dを衝突判定付きで移動。店舗198、既存共用・運営経路、連絡橋往復、RF3コア前と歩道橋、B1の2入口、12基のエスカレーター上下を区別。B1/RF階段・EVの上下移動は未施工です。"),
 ('人間の実操作・画質', '未実施です。保存した実画面と自動歩行到達点の見え方を確認していますが、手動で全館を歩いた試験ではありません。内装・商品・看板の個別仕上げ、自然な店舗照明、FF15級の建築表現には未到達です。今回の比較では入口の輪郭と床の遠景モアレ、連絡橋の窓・屋根を改善しています。描画FPSは今回再計測していません。'),
 ('承認前の保留', 'RF-SUPPORT-16の支持方式、全支持部の耐荷重・基礎、地下防水・土被り・設備容量、立体Pの全スロープ・全駐車経路・交通制御、A/C館内部の実歩行は未検証です。これらを合格扱いせず、ゲーム本体への統合も行っていません。')])
(P/'deliverables').mkdir(exist_ok=True);doc.set_metadata({'title':'FIND YOURSELF B館 v6 局所整合検証','author':'FIND YOURSELF project','subject':'17 retail boundaries, B1/RF and bridges; standalone only; structural capacity unverified'});doc.save(P/'deliverables/FIND_YOURSELF_B_WING_LOCAL_REVIEW_v6.pdf',garbage=4,deflate=True);print('PDF',len(doc),'pages',photo_count,'actual viewport images')
