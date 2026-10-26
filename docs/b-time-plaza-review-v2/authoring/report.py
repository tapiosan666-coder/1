"""Japanese construction / retail audit and unchanged-camera actual viewport comparison book."""
from pathlib import Path
import sys,json,math,csv,hashlib,collections,shutil
sys.path.insert(0,'/workspace/1/tools');from site_v2_common import read,polys,encode
import fitz
from PIL import Image
import numpy as np
P=Path(__file__).resolve().parents[1];R=Path('/workspace/1');E=P/'evidence';S=P/'source';DOC=R/'docs/b-time-plaza-review-v2';DOC.mkdir(exist_ok=True)
m=read(S/'scene-manifest.json');audit=read(S/'audit/full-audit.json');qa=json.load(open(E/'walk-results.json'));ind=json.load(open(E/'independent-verification.json'));render=json.load(open(E/'after/render-results.json'));extra=json.load(open(S/'expanded-qa-inputs.json'))
font_path=str(P/'assets/NotoSansCJKjp-Regular.otf');font=fitz.Font(fontfile=font_path);book=fitz.open();page=None;W=842;H=595;teal=(.12,.33,.31);ink=(.13,.17,.17);muted=(.36,.41,.40)
def txt(x,y,t,size=11,color=ink):page.insert_text((x,y),str(t),fontname='JP',fontfile=font_path,fontsize=size,color=color)
def wrap(x,y,width,t,size=11,line=20,color=ink):
 for para in str(t).split('\n'):
  row=''
  for c in para:
   if row and font.text_length(row+c,fontsize=size)>width:txt(x,y,row,size,color);y+=line;row=c
   else:row+=c
  if row:txt(x,y,row,size,color)
  y+=line
 return y
def new(title,sub='',big=False):
 global page,W,H
 W,H=(1191,842)if big else(842,595);page=book.new_page(width=W,height=H);page.insert_font(fontname='JP',fontfile=font_path);page.draw_rect(fitz.Rect(0,0,W,8),color=None,fill=teal);txt(30,43,title,20,teal)
 if sub:txt(30,66,sub,9,muted)
 txt(30,H-18,'FIND YOURSELF / B館「時の広場」総合修正・検証 v2 / 2026-10-26 JST / 本体未統合',8,muted);txt(W-55,H-18,str(len(book)),8,muted)
def image(path,rect):page.insert_image(rect,filename=str(path),keep_proportion=True)
def svg(path,rect):
 d=fitz.open(stream=Path(path).read_bytes(),filetype='svg');v=fitz.open(stream=d.convert_to_pdf(),filetype='pdf');page.show_pdf_page(rect,v,0)
def line(y):page.draw_line((30,y),(W-30,y),color=(.82,.86,.84),width=.5)
def row(y,label,text,size=11):txt(35,y,label,size,muted);wrap(222,y,W-255,text,size,19);line(y+12)
new('B館「時の広場」総合修正・検証 v2','優先：接合不良の修正 → 区画規模・配置の検証 → 店舗表現 → 物理・実画面の確認')
image(E/'after/03-2F-crossing-bridge.png',fitz.Rect(30,87,534,371))
wrap(557,110,252,'元の床・広場・吹き抜け・店舗区画を維持し、生成不良と店舗造作を修正しました。\n図面の細かな境界や未割当床は、未承認の修正案・確認候補として残しています。\nFF15級の品質には未到達。建築全体の完成判定ではありません。',12,23)
row(411,'実際のGodot物理検査',f"{qa['passed']}/{qa['total']} 合格。不合格 {qa['failed']}。完全49区画すべてに店内サンプル経路。人間のWindows実機操作とは区別。")
row(460,'独立検査',f"{ind['pass']}合格、{ind['fail']}不合格。別に設計確認・未検証のステータスを残す。")
row(509,'保護した対象','元ゲーム、B館v4.1、敷地v3、v1検証プロジェクト。本体への統合なし。')
new('原因と修正 1：床・壁・天井の接合','大きな壁で隠す修正ではなく、生成する部材の範囲と重複を修正。')
items=[('壁上端の開き','v1は壁上部を床から4.49mまで生成。天井は4.65/4.825mで、16〜33.5cmの開きが生じた。','天井レベルから壁高さを算出。窓上部・入口上部までつながる部材を生成。'),('巾木の乱れ','壁を床から全高で生成したうえに、同一平面へ12cm高の巾木を重ねた。異なる材質が同じ位置で競合。','巾木0〜0.12m、壁0.12m〜天井と分割。窓上部も主壁と重複しない範囲に限定。'),('ガラス足元','ガラスは0.12mから、下枠は0.10mから生成。床との納まりが閉じていなかった。','下枠を床から生成。ガラスは枠から8mm後退した位置に納め、同一面の重複も避ける。'),('ガラスと壁の位置','旧glazed_frontagesには区画クリップ後の境界と一致しない直線が残る。','実際の店舗・共用部の接する境界からガラス線を取得。表示と衝突を同じ座標から生成。')]
y=100
for title,cause,fix in items:
 txt(34,y,title,13,teal);y=wrap(34,y+24,772,'原因：'+cause+'\n修正：'+fix,11,19)+15
new('原因と修正 2：バックヤード・見た目の均一化','計画済みの区画を復元。新しい用途不明の小部屋は追加しない。')
wrap(32,104,775,'v4.1では外周壁とバックヤード間仕切りを合成していたが、敷地v3の店舗境界更新で外周壁だけを再構築していた。\n参照：tools/design_b_v4.py の wall.union(partition)、tools/design_site_correction_v3.py の境界壁再構築。\n今回、既存sales/backroomの境界とback_doorを使って間仕切りを復元。開口位置・1.6m幅を維持して56扉を構築。経路の掃引による不定形な開口を1.6mの矩形開口に修正し、扉上部の壁を天井まで接続。扉葉は1.594m（左右各3mmの逃げ）。B1-022・B2-022は開いた葉の干渉を避ける壁沿い引戸。',11,22)
wrap(32,275,775,'均一に見えた原因は、面積だけではない。v1は専門店の入口幅が一律2.4m、看板幅が8m上限、看板の縦横比が元画像と不一致、ほぼ同じガラス仕様・棚を使用していた。\n看板の縦横比を維持し、窓主体・壁面＋窓・商品窓の違い、床・壁・造作・商品を用途ごとに変更。入口そのものを広げる変更や全面開放型への改修は未適用。\n数値検査後のViewport確認で什器の入口側偏在も検出。元区画内で奥行き方向へ分散し、広場や公共通路を什器で埋めない。',11,22)
wrap(32,478,775,'壁の0.5mm以内の数値的整理は製作誤差の除去。元区画の意味のある柱型・セットバックは削除していない。図面由来の大きな折れは変更案として扱う。',10,18)
new('店舗規模と用途の分布','区分は分析用のゲーム設計値。実在施設の正式な面積区分ではない。')
headers=[('階',35),('小型 <150㎡',110),('中型 150〜500㎡',263),('大型 500〜1500㎡',440),('核店 1500㎡以上',635)]
for t,x in headers:txt(x,110,t,11,teal)
y=151
for f in audit['floors']:
 b=f['bands_full_B'];txt(35,y,f['floor'],12)
 for x,k in[(150,'小型(<150㎡)'),(315,'中型(150〜500㎡)'),(507,'大型(500〜1500㎡)'),(710,'核店舗(1500㎡以上)')]:txt(x,y,str(b.get(k,0)),13)
 y+=44
wrap(32,315,775,'B館1〜3階の台帳は計188区画。小型44、中型126、大型12、核店6。\nただし大型12区画（約528〜594㎡）と核店6区画（約3,312〜3,728㎡）は今回の切出し外。中央検証範囲には小・中型店が偏る。\n49完区画は3階合計（1F15、2F19、3F15）。80交差区画の31は切出し端を含み、完成店舗数に含めない。',12,23)
# Metric comparison by band, explicit frontage parameter meaning.
ledger=list(csv.DictReader(open(S/'audit/all-B-store-ledger.csv',encoding='utf-8-sig')))
new('店舗用途の分布','全B館1〜3Fと、検証範囲に完全に含まれる49区画を区別。',True)
txt(35,104,'用途',11,teal);txt(345,104,'1F',11,teal);txt(430,104,'2F',11,teal);txt(515,104,'3F',11,teal);txt(600,104,'全体',11,teal);txt(695,104,'検証完区画',11,teal)
y=132
for category in sorted(set(r['category']for r in ledger)):
 rr=[r for r in ledger if r['category']==category];txt(35,y,category,10)
 for x,fl in[(345,'1F'),(430,'2F'),(515,'3F')]:txt(x,y,str(sum(r['floor']==fl for r in rr)),10)
 txt(600,y,str(len(rr)),10);txt(715,y,str(sum(str(r['fully_in_crop']).lower()=='true'for r in rr)),10);y+=22
wrap(32,750,1120,'用途別の店舗数。範囲端で切れた区画を完全な店舗として数えていない。',10,18)
new('面積・間口・奥行きの比較','frontage/depthは既存台帳のパラメータ。建物外形の最大幅や実施設の実測値ではない。')
for t,x in[('区分',35),('面積範囲㎡',222),('間口パラメータm',410),('奥行きパラメータm',620)]:txt(x,108,t,10,teal)
y=151
for prefix in['小型','中型','大型','核店舗']:
 rr=[r for r in ledger if r['band'].startswith(prefix)];a=[float(r['area_m2'])for r in rr];b=[float(r['frontage_parameter_m'])for r in rr];c=[float(r['depth_parameter_m'])for r in rr]
 txt(35,y,prefix,12);txt(222,y,f'{min(a):.1f}〜{max(a):.1f}',12);txt(410,y,f'{min(b):.1f}〜{max(b):.1f}',12);txt(620,y,f'{min(c):.1f}〜{max(c):.1f}',12);y+=48
wrap(32,375,775,'核店は面積と6m入口で一般専門店（2.4m入口）と差がある一方、共用部に接する間口パラメータは約14〜14.8m。大きな売場が通路から広く見える保証にはならない。\n現時点の標準層高は5.35〜5.525m。核店専用の天井高さ・上映室断面・食品ホールの厨房構成は確定していない。',11,22)
for f in audit['floors']:
 new('B館全体図 / '+f['floor'],'橙：核店舗。赤枠：163×140m検証範囲。全体図は原設計データのベクトル表示。',True)
 svg(S/f'audit/B-{f["floor"]}-full-map.svg',fitz.Rect(30,90,1161,680))
 wrap(35,721,1120,'東西の核店の位置と共用通路への接続は維持。大型12区画・核店6区画は3D検証範囲外であり、この図を実装・実歩行済みの証拠とはしない。',12,21)
new('東西の核店舗6区画：配置と完成度','無断で移設・拡張していない。位置・面積は図面確認、内部機能は別評価。',True)
for t,x in[('ID / 用途',35),('区画㎡',405),('売場㎡',520),('倉庫㎡',635),('入口m',755),('入口世界X/Z',850)]:txt(x,111,t,12,teal)
y=151
for a in audit['anchors']:
 txt(35,y,a['id']+' / '+a['use'],12);txt(405,y,f"{a['area_m2']:.1f}",12);txt(520,y,f"{a['sales_m2']:.1f}",12);txt(635,y,f"{a['backroom_m2']:.1f}",12);txt(755,y,'6.0',12);txt(850,y,f"{a['entry_world_xz'][0]:.1f} / {a['entry_world_xz'][1]:.1f}",12);y+=47
wrap(35,490,1120,'西核店はM-W（西核店前専門店街）、東核店はA-E（東核店接続）側からアクセスする。\n大型売場の面積と倉庫・主経路は定義されているが、シネマの上映室・段床、フードホールの厨房・設備等は詳細化されていない。一般店と同じ標準断面・単純な主経路をそのまま完成形とするのは不十分。\n今回のスライスでは核店の天井高・売場内回遊・設備を実歩行検証していない。',12,24)
new('店舗密度・通路景観の評価','店舗数だけで適否を決めず、入口の連続性と視界、切出し条件を考慮する。')
y=107
for f in audit['floors']:
 txt(35,y,f['floor'],12,teal);wrap(105,y,700,f"交差{f['slice_intersections']}区画 / 完全{f['slice_full_tenants']}区画 / 実床{f['actual_slab_area_m2']:.0f}㎡ / 共用部{f['public_m2']:.0f}㎡",11,20);y+=42
wrap(32,265,775,'公式moriフロアガイド4〜6ページを目視。専門店の連続、大きな区画の途中混在、核店・広場で通路方向と景観が変わる構成を確認。公式図の縮尺・実測面積が未確認のため、㎡あたり店舗数の実施設との定量比較は行っていない。\nroute-exposure.csvは入口の中心線への投影間隔を記録。25mを超える候補を抽出するが、これは無店舗壁の実測長ではない。広場・設備前・館間連絡を一律に問題扱いしない。\n今回、広場を店舗で埋めず、什器・店舗窓・案内・材質で用途を読み取りやすくする。区画の統合・入口幅の変更は未承認案に分ける。',11,22)
new('用途未確定床・細かな境界の確認候補','独自の用途分類による候補。すべてを用途不明・不良と断定していない。')
y=108
for f in audit['floors']:
 txt(35,y,f['floor'],13,teal);wrap(110,y,690,f"未割当候補 {f['unassigned_candidate_total_m2']:.1f}㎡ / 短い折れの候補 {len(f['short_corner_candidates'])}点",12,22);y+=47
wrap(32,290,775,'共用床・店舗・設備核・明示された設備帯を除いた残りを抽出した。外部床、搬入余地、設備余地を含む可能性があり、用途の確定と現地的な視界評価が必要。\n店舗境界の短い折れは入口・裏口付近を除いて抽出。全てを削除対象としたわけではない。構造的意味のある柱型や入口セットバックは保持。\nB2-026には1.67048㎡の離れた部分がある。今回の切出し外の原図問題として記録し、無断で消去していない。\nこれらを大壁で隠して建物完成とする修正は行っていない。',11,22)
for f in audit['floors']:
 new(f['floor']+' / 設計確認候補の位置','橙：独自分類の未割当候補。赤点：短い折れの候補。広場・元区画は維持。',True)
 svg(S/f'audit/{f["floor"]}-review-candidates.svg',fitz.Rect(35,90,820,738))
 wrap(855,122,300,'未割当候補は用途未確定であり、すべてを不良と断定しない。搬入・設備・外部床の可能性も原本で確認する。\n候補を大きな壁で隠すことや、公共通路へ無断で店舗を張り出す修正は行っていない。',12,25)
new('未適用の区画改善案','原本へ未反映。ユーザーの確認後に図面を詳細化する変更案。')
y=108
for q in audit['proposals_not_applied']:
 txt(35,y,q['id'],12,teal);y=wrap(35,y+25,770,'対象：'+' / '.join(q['stores'])+f"\n統合面積候補：約{q['combined_area_m2']:.1f}㎡\n"+q['intent']+'\n共有境界長1.5m超の連結区画を選択。入口の統合・売場構成・内壁・設備は未設計。',11,21)+23
wrap(32,480,775,'広場・吹き抜け・主要通路・既存核店6区画は動かさない案。1Fの中央大型化は境界の共有・入口・搬入を再検討してから。店舗数を増やすための分割は提案していない。',10,18)
for i,q in enumerate(audit['proposals_not_applied']):
 new(q['id']+' / 未適用の図面案','左：現状の区画。右：統合候補の外形。承認前に施工しない。',True)
 svg(S/f'audit/proposal-{i+1}-before.svg',fitz.Rect(35,105,565,540));svg(S/f'audit/proposal-{i+1}-proposal.svg',fitz.Rect(625,105,1155,540))
 wrap(35,590,1110,'対象 '+ ' / '.join(q['stores'])+f'、統合面積候補{q["combined_area_m2"]:.1f}㎡。公共通路・広場・吹き抜けを維持し、内部境界を再設計する候補。入口・レジ・倉庫・売場の詳細は未確定。',13,26)
new('幾何と物理：検査結果の読み方','数値合格を建築全体・美術品質の完成へ読み替えない。',True)
y=109
names={'capsule_move_and_slide_to_shop_or_public_waypoint':'既存の入口・共用経路','entrance_left_center_right_capsule':'入口の左・中央・右（半径0.30mカプセル）','actual_character_body_shop_interior':'店舗内部サンプル','declared_sales_to_backroom_route':'既存の売場→バックヤード経路','3D_construction_joint_ray':'ガラス足元・壁上端の接合レイ','interior_actual_ceiling_raycast':'店内天井の実位置レイ','physical_escalator_slope_walk':'4基の上下歩行','automatic_conveyor_without_movement_input':'4基の入力なし搬送','staff_door_actual_closed_collider':'閉じたバックヤード扉','guardrail_prevents_fall':'手すり転落防止','actual_3D_floor_or_void_raycast':'床・吹き抜け・横断橋','mechanical':'踏段閉ループ・向き・間隔等'}
for kind,label in names.items():
 cs=[q for q in qa['checks']if q.get('kind','mechanical')==kind];txt(35,y,label,12);txt(840,y,f"{sum(q['pass']for q in cs)}/{len(cs)}",13,teal);y+=36
wrap(35,590,1120,f"合計 {qa['passed']}/{qa['total']}。60Hz、半径0.30m、全高1.80m。途中の座標投影・ワープなし。\n独立検査 {ind['pass']}合格 / {ind['fail']}不合格。元ゲーム・原図・v1保護、区画不変、床形状、モデル/静的衝突、実行版ハッシュを確認。\n図面上の孤立候補・未割当・区画変更案は、合格件数に含めず別ステータスで記録。",12,23)
new('検査範囲・残課題','自動操作と、人間による実操作、Viewportを見た設計評価を区別する。')
wrap(32,108,775,f"初回拡張検査は753/854。範囲外へ出る目標と、開いた扉の葉による通行干渉を検出した。範囲外は対象外へ分類し、扉の吊り元・引戸、実際の開いた葉を考慮する経路へ修正した。初回結果を保存している。\n今回の対象外の既存バックヤード経路は{len(extra['excluded_out_of_scope_declared_routes'])}件。合格として数えていない。\n保守的2D自由空間には{len(extra['review_required'])}件の確認候補が残る。すべてを移動不能と断定せず、指定された実物理サンプルと区別。全売場の全位置を人間が歩き切った検査ではない。",11,22)
wrap(32,335,775,'未検証：人間によるWindows操作、混雑、全配置での視認性、車椅子、RTX4060のFPS、核店内部、範囲外の区画・他館・他階。\n機械的近似：エスカレーターの表示踏段は移動するが、接触は安定した連続勾配面。各踏段との厳密な剛体接触ではない。床仕上げ6mm・柱の薄い化粧材等、小物非衝突の扱いも本体統合前に見直す。\nB館全体を完成・全問題解消とする判定は保留。',11,22)
# Actual identical camera pairs. PNG contents are embedded directly without retouch.
captions={
'01-1F-time-plaza':'吹き抜け・床・天井の基本構造を維持。床の強い日射ハイライトと反射の調整は残る。','02-1F-west-escalators':'手すりの戻り形状・踏段・くし板。','03-2F-crossing-bridge':'回廊・反射・床端・対岸店舗。','04-2F-storefront':'入口・商品窓・店舗奥の区別。','05-3F-void-and-roof':'吹き抜け・ガラス・上階の見通し。','06-1F-north-shopping-street':'店舗の連続・窓と壁・看板の比率。','07-1F-cafe-interior':'客席とバックヤードを区別。壁面造作・厨房設備・照明の詳細は未完成。','08-1F-bookshop-interior':'棚の奥行き分散と本の形状を改善。壁面陳列・売場案内・照明の密度は不足。','09-store-wall-ceiling-joint':'壁上端の接合確認。眼高1.65m、FOV55。','10-glass-floor-shoe':'ガラス足元の納まり。高さ0.45mの技術検査視点。','11-shop-boundary':'店舗境界の見え方。図面由来の折れは未平滑化。'}
base_poses=json.load(open(S/'camera-lock.json'));inspect=json.load(open(S/'inspection-cameras.json'));poses={p['id']:p for p in base_poses+inspect}
for name,caption in captions.items():
 new(name+' / 同一カメラ比較','左：v1 / 右：v2。実際のGodot Viewportから保存したPNG。生成画像・レタッチではない。',True)
 txt(35,105,'BEFORE / v1',15,muted);txt(612,105,'AFTER / v2',15,teal)
 image(E/'before'/(name+'.png'),fitz.Rect(30,122,579,431));image(E/'after'/(name+'.png'),fitz.Rect(612,122,1161,431))
 wrap(35,476,1110,caption,14,25)
 pose=poses[name];wrap(35,535,1110,'カメラ位置 '+str(pose['p'])+' / 注視点 '+str(pose['look'])+f" / FOV {pose.get('fov_deg',75)}° / 1280×720。",11,21)
 wrap(35,610,1110,'接合不良と用途に合う造作を評価する比較。図面に起因する細かな折れや、範囲端の閉鎖面は別の確認事項として残る。素材・照明・完成内装はFF15級に未到達。',12,22)
for name,label in[('12-fashion-interior','衣料：レジ・ラック・試着ブース'),('13-beauty-interior','美容：レジ・商品ボトル・専用棚'),('14-shoes-interior','靴：靴形状・レース・靴底・展示'),('15-music-interior','楽器：ギター・弦・フレット・スタンド')]:
 new(label,'v2追加の代表視点。前後比較には使用しない。実Godot Viewport。',True);image(E/'after'/(name+'.png'),fitz.Rect(30,96,1161,732));txt(35,778,'この区画の専用造作の例。全店の完成内装を示すものではない。',11,muted)
new('店舗内装の施工範囲と未完成箇所','数値上の通行合格と、店舗としての完成度を分ける。')
full=[q for q in m['shops']if q['full_polygon_in_scope']];low=[q for q in full if len(q['fixture_footprints'])<=2];empty=[q['id']for q in full if not q['fixture_footprints']]
wrap(32,105,775,f"完全区画49のうち什器あり{sum(bool(q['fixture_footprints'])for q in full)}区画。交差80区画のうち什器あり{sum(bool(q['fixture_footprints'])for q in m['shops'])}区画。\n完全区画の未施工区画：{', '.join(empty)if empty else'なし（配置組数上）'}。什器0〜2組は{len(low)}区画。\n初期配置では粗いグリッドが斜めの売場を取りこぼし、B1-014・B3-009・B3-014等が空になっていた。細かい二次探索と売場の実形状判定を追加し、区画と保護通路を変更せず配置候補を求め直した。",12,24)
wrap(32,330,775,'配置済みでも全店舗の内装完成ではない。壁面陳列・厨房設備・レジ周辺・照明・細部の個別設計は残る。用途別の商品形状を追加しただけで完成とは判定しない。\nfitout-coverage.csvに各区画の配置組数と状態を記録。原図を無断変更して配置可能面積を広げる処理は行わない。',11,23)
new('素材・照明と美術品質','形状数・合格件数の増加で完成扱いにしない。')
wrap(32,106,775,'数値生成の石・塗装・木・金属・布・革のPBRマップ、環境光、店舗局所照明、ボックス投影反射、静的頂点AOを使用。\nAOはBlenderのBVHで12方向をサンプリングした接触陰影であり、拡散GIや多重反射の実装ではない。実在施設の写真スキャン素材・HDRIは使用していない。\n今回の見た目評価：壁際・足元の部材干渉の除去、ガラスと枠の奥行き、間仕切りによる売場の区別、棚・客席の分散を実画面で確認。\n実画面01は強い日射ハイライト、07は壁面と客席の単調さ、08は棚の反復と案内・照明の不足が残る。\n残課題：図面側の不自然な境界、より精細な素材・小物、店舗固有の完成造作、拡散GI、露出・照明、生活感、LOD。FF15級の商業施設表現には未到達。',12,24)
new('エスカレーター：形状・動き・衝突','実装した見える動きと、機械シミュレーション上の近似を区別する。')
wrap(32,105,775,'踏段はメッシュインスタンスが閉ループを進み、乗降部で水平になり、覆いの内部で反転する。戻りを持つ丸い手すり形状、動くゴム表面、固定くし板の歯を構築。表面速度0.5m/s。\n各踏段の向き・間隔・閉ループ継目を数値で検査し、Godotの実画面から動画を取得。動画はシミュレーション時刻8Hzのサンプリング。8fpsを実際の描画FPSと読み替えない。\n歩行衝突は連続勾配・乗降面の近似。機械内部・各踏段と足の厳密な剛体接触は完成していない。',11,22)
image(E/'animation/animation-008.png',fitz.Rect(32,306,471,553));image(E/'animation/animation-016.png',fitz.Rect(483,306,811,491))
new('参考FPS・使用条件','共有クラウドのCPU描画。RTX4060の結果ではない。')
wrap(32,106,775,f"{render['adapter']} / Godot {render['godot_version']['string']} / {render['renderer']} / 1280×720 / MSAA4x。\nNPC0人。エディタ付属実行バイナリ。Release・RTX・長時間負荷は未測定。",11,22)
y=205
for a in render['performance']:txt(35,y,a['id'],10);txt(420,y,f"平均 {a['fps_from_mean_frame_time']:.2f} FPS",11);txt(625,y,f"95%点 {a['p95_ms']:.0f}ms",10);y+=42
r=render['walking_performance'];txt(35,y,'移動中',11);txt(420,y,f"平均 {r['fps_from_mean_frame_time']:.2f} FPS",11)
wrap(32,420,775,'ソフトウェア描画での参考値。実機のGPU性能や5,000人時の性能へ換算しない。画像比較を目的とした測定であり、60FPS達成の判定は保留。生フレーム時間はrender-results.jsonに記録。',11,22)
new('使用素材・ライセンス・確認方法','Godot検証プロジェクトはゲーム本体とは独立。承認前に統合しない。')
wrap(32,105,775,'建築メッシュ、造作、商品、看板、表紙、メニュー、時計、数値生成PBRマップ、シェーダーは本プロジェクトのオリジナル。新しい一般向け公開利用ライセンスは未設定。\nNoto Sans CJK JP：SIL OFL1.1。Godot4.6.3：MIT。ライセンス原文はlicenses/。制作専用のShapely、NumPy、Pillow、Blender、PyMuPDF、ffmpeg等の実行バイナリは同梱していない。\n公式参考資料：AEON_LAKETOWN_OFFICIAL_FLOOR_GUIDE_202610.pdf、mori4〜6ページを目視。原資料そのものは配布物へ転載していない。参照SHA256はfull-audit.jsonに記録。',11,22)
wrap(32,330,775,'ZIPを展開し、Godot4.6.3でproject.godotをインポートしてF5。WASD・マウス・Shift、Fで扉開閉。1/2/3は階移動の検証用。\nsource/audit/：B館全体図、全188区画台帳、用途・面積分析、未適用案。\nevidence/：実Viewportの前後画像、物理検査、独立検査、初回の失敗記録、アニメーション。\n図面原本・元ゲーム・v1の変更は行っていない。',11,22)
OUT=R/'downloads/FIND_YOURSELF-B-Time-Plaza-Review-v2.pdf';book.save(OUT,garbage=4,deflate=True)
check=fitz.open(OUT);bad=[]
for i,p in enumerate(check):
 p.get_pixmap(matrix=fitz.Matrix(.2,.2),alpha=False)
 for b in p.get_text('dict')['blocks']:
  if b['type']!=0:continue
  for l in b['lines']:
   for sp in l['spans']:
    q=fitz.Rect(sp['bbox'])
    if q.x0<-.5 or q.y0<-.5 or q.x1>p.rect.width+.5 or q.y1>p.rect.height+.5:bad.append({'page':i+1,'text':sp['text'],'bbox':sp['bbox']})
receipt={'pages':len(check),'all_pages_rendered':True,'text_outside_pages':bad,'warnings':fitz.TOOLS.mupdf_warnings(),'actual_comparison_pairs':11,'additional_after_views':4,'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest()}
(E/'pdf-verification.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2));print('PDF',len(check),OUT.stat().st_size,receipt)
# Asset license inventory: generated original maps and unmodified OFL font.
assets=[]
for p in sorted((P/'assets').iterdir()):
 if not p.is_file()or p.suffix=='.import':continue
 assets.append({'file':str(p.relative_to(P)),'license':'SIL OFL1.1'if p.suffix=='.otf'else'Original project work; no separate public reuse license assigned','sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
with open(S/'asset-license-ledger.csv','w',newline='',encoding='utf-8-sig')as o:w=csv.DictWriter(o,list(assets[0]));w.writeheader();w.writerows(assets)
for name in['README.md']:shutil.copy2(P/name,DOC/name)
for name in['independent-verification.json','walk-results.json','pdf-verification.json','ao-bake.json']:
 shutil.copy2(E/name,DOC/name)
for name in['fitout-coverage.csv','scene-manifest.json','asset-license-ledger.csv','door-hinge-selection.json','camera-lock.json','inspection-cameras.json']:
 shutil.copy2(S/name,DOC/name)
shutil.copytree(S/'audit',DOC/'audit',dirs_exist_ok=True)
for sub in['before','after']:
 (DOC/sub).mkdir(exist_ok=True)
 for p in(E/sub).glob('*.png'):shutil.copy2(p,DOC/sub/p.name)
shutil.copy2(E/'after/render-results.json',DOC/'render-results.json')
if(E/'animation/escalator-motion.mp4').exists():shutil.copy2(E/'animation/escalator-motion.mp4',DOC/'escalator-motion.mp4')
