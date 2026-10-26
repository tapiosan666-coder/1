"""Root cause first. A failed full-building design is never presented as completed architecture."""
from pathlib import Path
import sys,json,csv,hashlib,collections,math,shutil
sys.path.insert(0,'/workspace/1/tools');from site_v2_common import read,polys,encode
import fitz
from PIL import Image
from io import BytesIO
from functools import lru_cache
P=Path(__file__).resolve().parents[1];R=Path('/workspace/1');E=P/'evidence';S=P/'source';A=S/'root-gap-review';G=S/'program-review-v3';DOC=R/'docs/b-time-plaza-root-review-v3';DOC.mkdir(exist_ok=True)
m=read(S/'scene-manifest.json');root=read(A/'full-B-root-audit.json');proposal=read(A/'refined-enclosure-proposals.json');contracts=read(E/'root-contract-results.json');walk=read(E/'walk-results.json');ind=read(E/'independent-verification.json');render=read(E/'after/render-results.json');equipment=read(G/'large-store-equipment.json');large=read(G/'large-store-studies.json');bookdata=read(G/'bookshop-comparison.json');mergers=read(G/'merger-review.json');expanded=read(S/'expanded-qa-inputs.json')
fontpath=str(P/'assets/NotoSansCJKjp-Regular.otf');font=fitz.Font(fontfile=fontpath);doc=fitz.open();page=None;W=842;H=595;green=(.13,.32,.28);dark=(.15,.18,.17);grey=(.39,.43,.40);red=(.63,.24,.17)
def txt(x,y,t,size=11,color=dark):page.insert_text((x,y),str(t),fontname='JP',fontfile=fontpath,fontsize=size,color=color)
def wrap(x,y,width,text,size=11,line=20,color=dark):
 for para in str(text).split('\n'):
  row=''
  for c in para:
   if row and font.text_length(row+c,fontsize=size)>width:txt(x,y,row,size,color);y+=line;row=c
   else:row+=c
  if row:txt(x,y,row,size,color)
  y+=line
 return y
def new(title,subtitle='',big=False):
 global page,W,H
 W,H=(1191,842)if big else(842,595);page=doc.new_page(width=W,height=H);page.insert_font(fontname='JP',fontfile=fontpath);page.draw_rect(fitz.Rect(0,0,W,7),fill=green,color=None);txt(30,42,title,19,green)
 if subtitle:wrap(30,65,W-60,subtitle,9,14,grey)
 txt(30,H-17,'FIND YOURSELF / B館 全体原因調査・修正案 v3 / 2026-10-27 JST / 原本・ゲーム本体未変更',8,grey)
@lru_cache(maxsize=160)
def image_bytes(path):
 # Strip malformed PNG ICC metadata for PDF embedding only. No resize, recolour or pixel edits.
 im=Image.open(path);raw=im.tobytes();b=BytesIO();im.save(b,format='PNG',icc_profile=None);data=b.getvalue();assert Image.open(BytesIO(data)).tobytes()==raw
 return data
def image(path,rect):page.insert_image(rect,stream=image_bytes(str(path)),keep_proportion=True)
def svg(path,rect):
 source=fitz.open(stream=Path(path).read_bytes(),filetype='svg');vector=fitz.open(stream=source.convert_to_pdf(),filetype='pdf');page.show_pdf_page(rect,vector,0)
def line(y):page.draw_line((30,y),(W-30,y),color=(.82,.86,.82),width=.4)
def row(y,label,t):txt(35,y,label,11,grey);wrap(225,y,W-255,t,11,19);line(y+17)
new('B館全体の隙間：原因調査と修正案 v3','調査・再発防止ルール・独立比較シーン。全館改修の完成報告ではありません。')
wrap(32,105,775,'結論：個々の壁の接合だけの問題ではなく、店舗配置後の未割当床、区画の逐次差演算、内部各領域の入口検査、3D生成契約の不足が重なっています。',15,28)
wrap(32,204,775,f"全B館5層から{len(root['issues'])}件の問題・確認候補を抽出。現在も各階に未帰属面積が残るため、完成版生成を停止しています。\n局所案6か所のうち3か所だけを独立した3D修正案へ反映。全館の隙間を解消したとは報告しません。",13,27,red)
row(350,'自動物理検査',f"{walk['passed']}/{walk['total']}。通行・接合・共有境界サンプル等。建築品質の合格ではない。")
row(408,'規約・独立検査',f"規約{contracts['passed']}件、独立{ind['pass']}件合格。通常出力が止まることも検査。原図の設計完成を意味しない。")
row(466,'人間の実操作','Windows/RTX4060上の人間による操作は未検証。図面・自動操作・画面評価を分離。')
new('読み方と提出物','PDF、CSV・設計JSON、独立Godotプロジェクトを使い分けます。')
wrap(32,107,775,'前半：根本原因、全5層の面積・問題位置、再発防止ルール、局所案の棄却理由。\n中盤：原図と修正案、Godotの通常視点比較、補助のGodot切断表示、内装の実画面。\n後半：大型12区画＋核店6区画、中央統合2案、未検証事項、全516件の座標一覧。\nissue-register.csv は原因と対応方針まで含む全件台帳。PDF末尾のU/G/C/B/S/D/Mは種別の略号です。\n同じ場所が複数の種別で挙がるため、問題台帳の面積を足し合わせないでください。未割当床の面積は各階の重複のない差分です。',12,25)
wrap(32,360,775,'現在の通常3D範囲は163×140m、1〜3階。B1・RFと範囲外の大型店は図面調査のみ。\n橙＝未割当、青＝区画再生成案、緑＝既存の用途付き領域。未割当の全てを不要と断定せず、維持の根拠がない部分を分けています。',11,23)
new('根本原因 1：用途より先に作られた外郭','根拠：tools/design_b_v4.py のBODY・residual・floor_plate生成。')
wrap(32,108,775,'店舗・通路・設備核を包む外郭BODYを、膨張・収縮・簡略化で生成し、その差分をresidualとして残していました。\n外郭全体には床が作られる一方、余った領域の多くには、部屋名・入口・接続先・設備仕様がありません。ここを「必要な従業員通路」「機械室」と一括で説明することはできません。\n地下・屋上はprogram・駐車場・庭・保守通路に具体的な指定があります。これらは未割当として誤抽出せず保護しています。',12,25)
wrap(32,343,775,'再設計方針：店舗・通路・裏方機能・設備の必要面積と接続を先に定め、外郭をそれに整合させる。余りの用途が説明できなければ、外郭縮減・店舗奥行き・共用設備を街区ごとに比較する。\n今回の小規模案だけでは、各階数千㎡の余剰床は解決しません。',12,25,red)
new('根本原因 2：区画の差演算と内部入口の不足','根拠：design_b_v4.py の区画クリップ・バックヤード分割、design_site_correction_v3.py の設備入口切欠き。')
wrap(32,107,775,'通路・吹き抜け・設備核・他店を店舗から順に差し引くため、短辺・鋭角・細い片・離れた片が残ります。この輪郭をそのまま壁のバッファへ使うと、意味のない壁の凹凸も立体化されます。\n店舗全体が入口へつながっていても、売場や在庫の一部だけが分離し、専用入口を持たない場合があります。今回、在庫7片・売場1片、店舗の離れた片1件を抽出しました。\n曲線・柱型・入口セットバックは意図的な場合があるため、331点の短辺/鋭角候補をすべて削除対象としたわけではありません。',12,25)
wrap(32,372,775,'再発防止：隣接区画を一つの共有境界として編集し、両側を同時に検査する。各内部領域にも専用開口か明示された内部接続を要求する。片側だけのsimplifyや、余った片への機械的な用途名付けを禁止する。',12,25)
new('根本原因 3：3D生成と検査の契約不足','根拠：独立v2 authoring/build.py の床・named service zones・店舗壁生成。')
wrap(32,108,775,'v2では外郭全体の床を作り、名前のある共用倉庫・設備核・店舗壁を生成していましたが、用途未確定領域の全体を実際の建築構成へ仕上げていませんでした。\n大きな壁で残余を埋めることを避けても、その先の用途・区画設計がなければ、用途不明の床・空間は残ります。これはメッシュ接合の微修正だけでは直りません。\n前回の床支持と指定経路の検査では、床全体の用途帰属と内部各部分の専用入口を検査できていませんでした。\nnav_freeは共用通路のマスクです。売場もoff-navになり得るため、off-navを立入禁止や設備の必要性の証拠にはしていません。',12,25)
new('B館全5層：未割当床の面積','駐車場・庭・命名済み保守通路・programを差し引いた全B館の値。時の広場切出しの値とは範囲が異なります。',True)
for t,x in [('階',35),('原設計 未割当㎡',140),('6局所案後の残り㎡',400),('確認候補件数',700),('3D対象',930)]:txt(x,112,t,12,green)
y=158
for s in root['summaries']:
 txt(35,y,s['floor'],14);txt(140,y,f"{s['unallocated_before_m2']:,.2f}",14);txt(400,y,f"{s['unallocated_after_proposed_small_annex_m2']:,.2f}",14);txt(750,y,str(s['issues']),14);txt(930,y,'一部切出しのみ'if s['level']in[0,1,2]else'図面のみ',12);y+=58
wrap(35,520,1120,'B1/RFの残りは0.5㎡以下の微小片の集約です。地下や屋上の3万㎡規模の既存programを未割当と呼んでいません。\n1〜3階の残余は規模が大きく、全館としての用途再配分・外郭の再検討が必要です。6案の採用だけで解消するとは評価しません。',13,27,red)
for label in ['B1','1F','2F','3F','RF']:
 new('全体所有区分 / B館 '+label,'橙：未割当床。青：今回の区画再生成案。緑：既存の用途指定（客用・裏方・設備・駐車等）。原図は変更していません。',True)
 svg(A/f'B-{label}-refined.svg',fitz.Rect(30,95,1161,690));wrap(35,735,1120,'この図は図面上の用途帰属の検査です。Godot全館の描画・歩行を完了した図ではありません。青い案以外にも残る橙部分を次の街区設計で解決する必要があります。',12,24)
new('再発させない設計・生成ルール','原文：source/root-gap-review/GENERATION_RULES.md。通常出力の停止をコードで実装。')
wrap(32,108,775,'1. 用途と必要幅を持つ通路、広場、設備、店舗を先に設計し、余りを廊下にしない。\n2. 店舗・売場・在庫・設備室ごとに、入口と接続を持たせる。\n3. 隣接区画は共有境界で扱い、窓・扉・柱・曲線を意味付きで保持する。\n4. 非居室の納まり幅を、売場・倉庫・通路の有効面積へ算入しない。\n5. 用途不明の床が残れば、完成版の生成を停止する。\n6. 表示・衝突・案内・移動データは同じ確定した境界から生成する。\n7. 形状検査・自動歩行・実画面の評価・人間の実操作は、それぞれ別に合否を残す。',12,28)
wrap(32,370,775,'実行結果：通常のbuild.pyはPRODUCTION_EXPORT_BLOCKEDで停止。--review-draftを明示した場合だけ未完の比較シーンを生成します。\n現在は全5層に未帰属が残るため、通常出力が止まることが正しい結果です。ゲート検査の合格を、建築設計の合格へ読み替えないでください。',12,25,red)
new('局所修正案の絞り込み：11案から6案へ','余剰床を近隣店へ足すだけでも、壁面を悪化させることがあるため棄却基準を追加。')
wrap(32,107,775,'初期11案のうち、壁長や有効な曲がり角を増やす案、既存区画を削る案、局所範囲を超える案など5案を棄却しました。\n残る6案は、既存区画と余剰領域の外郭を直線化し、公共空間・隣店・設備・保守経路を同時に制約したものです。単純な近傍割当や、全館のconvex hull化ではありません。\n2mm簡略化は有効頂点数の評価だけに用いています。実際の保護境界を片側から簡略化していません。',12,25)
y=345
for q in proposal['rejected_candidates']:
 txt(35,y,q['store'],11,green);wrap(155,y,650,' / '.join(q['reasons']),10,19);y+=39
for c in proposal['changes']:
 new(c['store']+' / 区画再生成案','左：原設計。右：未承認案。橙：旧未割当、青灰：在庫、茶灰：非居室、緑：既存公共空間。',True)
 svg(A/(c['store']+'-before.svg'),fitz.Rect(30,95,580,590));svg(A/(c['store']+'-after.svg'),fitz.Rect(610,95,1161,590))
 wrap(35,641,1120,f"区画増分 {c['added_plot_m2']:.3f}㎡ / 有効在庫増分 {c['added_usable_stock_m2']:.3f}㎡ / 有効頂点 {c['old_effective_vertices']}→{c['new_effective_vertices']} / 壁長変化 {c['perimeter_delta_m']:+.3f}m。\n既存の入口・在庫扉を維持。広場・吹き抜け・公共通路・他店を侵していません。"+('\n現在の3D切出し内で比較。'if c['in_current_3D']else'\n3D範囲外。図面検査のみで、実装・実歩行済みとはしない。'),12,24)
new('B2-022：分離在庫の扱い','店舗区画の連結だけでなく、専用扉につながる内部領域を評価する例。')
c=next(q for q in proposal['changes']if q['store']=='B2-022')
wrap(32,108,775,f"旧バックヤードは3つの部分に分かれていました。修正案では、専用扉へ接続する在庫床を1つにまとめ、狭い残りを非居室として区別しています。\n旧在庫 {c['old_backroom'].area:.3f}㎡ → 接続する新在庫 {c['new_backroom'].area:.3f}㎡。元の売場と入口位置は維持。\n面積が増えただけで有効な在庫室とは判断せず、扉へ接続しない部分を在庫面積から除きました。\nなお、納まり・壁厚・運用上の必要量・全位置の人間による操作は未確認です。規約による候補選別と、自然な建築であることの確認は別です。",12,25)
new('検査結果：何が合格し、何が未完成か','合格件数はシーンの限られた実装検査を表します。全B館の建築品質は未承認です。',True)
counts=collections.Counter(q.get('kind','mechanical')for q in walk['checks']);names={'sampled_shared_store_boundary_raycast':'共有店舗境界の実コライダ・レイ（1.5m間隔、低部と壁上端）','3D_construction_joint_ray':'ガラス足元・壁上端・扉上部の接合レイ','actual_character_body_shop_interior':'店舗内部の自動カプセル歩行','entrance_left_center_right_capsule':'入口の左・中央・右の実通過','declared_sales_to_backroom_route':'既存売場→バックヤード経路','capsule_move_and_slide_to_shop_or_public_waypoint':'共用・既存入口の経路','interior_actual_ceiling_raycast':'店内天井位置','physical_escalator_slope_walk':'エスカレーター上下歩行','automatic_conveyor_without_movement_input':'入力なし搬送','guardrail_prevents_fall':'手すり','actual_3D_floor_or_void_raycast':'床/吹き抜け','staff_door_actual_closed_collider':'閉じた在庫扉','mechanical':'踏段の閉ループ等'}
y=112
for k,label in names.items():txt(35,y,label,11);txt(990,y,str(counts.get(k,0)),12,green);y+=32
wrap(35,573,1120,f"自動物理 {walk['passed']}/{walk['total']}、規約 {contracts['passed']}/{contracts['passed']+contracts['failed']}、独立検査 {ind['pass']}合格/{ind['fail']}不合格。\n区画の意図・壁の自然さ・密度の完成は、この件数では判定できません。広い未割当床は残り、通常の完成版生成は停止しています。\n保守的2D自由空間に{len(expanded['review_required'])}件の確認候補。Windows上の人間による実操作は未検証。",12,25)
new('Godot実画面の評価と限界','通常視点と補助の検査表示を分離。画像の差を誇張しません。')
wrap(32,108,775,'通常視点19〜21では、主な変更部が店舗奥にあり、通路から十分に見えません。この画像だけで「不自然な隙間が解消し、自然なモールになった」とは判断できません。\n22・23は既存在庫内の眼高1.65mからの比較で、扉は自動で開けた検査状態です。奥の壁・視認性・部屋の納まりはなお見直しが必要です。\n補助の24〜26は、同じGodotメッシュを高さ1.25mで切断した正投影・診断色の検査表示です。通常プレイのグラフィック品質を示すものではありません。\n全B館の街区再設計と、人間による実際の探索確認を残しています。今回の6案は施工承認用完成図ではありません。',12,25)
# Normal viewport comparisons. Protected basic poses include v1; new focused poses match v2 and v3.
poses={q['id']:q for q in json.load(open(S/'final-cameras.json'))}
for name in ['19-gap-B1-066','20-gap-B2-022','21-gap-B3-028','22-stock-connection-B2-022','23-stock-connection-B3-028']:
 new(name+' / 通常Godot実画面','左：保護したv2。右：未承認のv3比較案。画像の加工・生成AIは不使用。',True)
 image(E/'before-v2'/(name+'.png'),fitz.Rect(30,110,579,419));image(E/'after'/(name+'.png'),fitz.Rect(612,110,1161,419));p=poses[name]
 wrap(35,470,1120,'カメラ '+str(p['p'])+' → '+str(p['look'])+f" / FOV {p['fov_deg']}°。"+('在庫扉は自動で開けた状態。人間による操作ではありません。'if p.get('open_staff')else'公共側の眼高1.65m。'),12,24)
 wrap(35,586,1120,'この通常視点では修正部全体を見渡せません。通路景観・奥壁・納まりの改善は保留項目を残しており、全館の品質合格の証拠にはしていません。図面と補助の切断表示を併読してください。',12,24,red)
for name in ['24-cutaway-B1-066','25-cutaway-B2-022','26-cutaway-B3-028']:
 new(name+' / Godot検査用切断表示','高さ1.25mで切断・診断色・正投影。実Godot Viewportですが、通常プレイ画面ではありません。',True)
 image(E/'cutaway-before'/(name+'.png'),fitz.Rect(30,110,579,419));image(E/'cutaway-after'/(name+'.png'),fitz.Rect(612,110,1161,419));wrap(35,480,1120,'左：v2モデル。右：区画の所有境界から再生成したv3モデル。外郭・在庫領域の位置を確認する補助資料です。陰影や素材の完成度の評価には使いません。衝突は通常シーンと同じメッシュから検査しています。',13,27)
new('並行して進めた内装：対象と未完成箇所','根本原因調査を優先。内装改善は代表3店舗の比較で、全店の完成ではありません。')
for j,q in enumerate(m['detailed_fitouts']):
 y=110+j*100;txt(35,y,q['id']+' / '+q['type'],13,green);wrap(35,y+26,770,f"売場 {q['sales_area_m2']:.1f}㎡ / 造作予約 {q['fixture_reserved_m2']:.1f}㎡ / 機能組数 {len(q['features'])}。"+' / '.join(next(s for s in m['shops']if s['id']==q['id'])['fitout_details']),10,19)
wrap(32,448,775,'残課題：壁面の仕上げ量、光の回り方、素材・小物の精度、厨房設備の実用性、ストックの運用、全店固有の意匠。FF15級には未到達です。',12,25,red)
new('書店：v1より空いて見えるか','同じカメラ08で比較。什器数と視覚的密度を同一視しません。',True)
for x,sub,label in[(30,'before-v1','v1'),(420,'before-v2','v2'),(810,'after','v3')]:txt(x,102,label,14,green);image(E/sub/'08-1F-bookshop-interior.png',fitz.Rect(x,118,x+360,321))
b=next(q for q in bookdata if q['id']=='B1-017');wrap(35,376,1120,f"同店の配置組数：v1 {b['v1_recovered_fixture_count']} → v2 {b['v2_fixture_count']} → v3 {b['v3_fixture_count']}。組数は減っていませんが、v2では壁面が未使用で、同一視点から通路と棚の側面が強く見え、空いて感じる部分がありました。\nv3は壁面書架・カテゴリ表示・棚下灯・新刊平台・レジ・読書席を組み合わせています。島書架を減らした分も壁面を使っています。\n見た目はなお壁・天井・サイン密度と仕上げの精度に課題があり、全書店の内装完成とは判定していません。",13,28)
new('切出し内の書店：数量と面積の比較','v1の配置条件を復元し、原台帳の組数と照合。面積は予約領域で、陳列能力・体感密度ではありません。',True)
for t,x in [('ID',35),('売場㎡',210),('v1 組/㎡',370),('v2 組/㎡',565),('v3 組/㎡',760),('全区画',990)]:txt(x,110,t,12,green)
y=158
for q in bookdata:
 txt(35,y,q['id'],12);txt(210,y,f"{q['sales_m2']:.1f}",12)
 for x,v in[(370,'v1'),(565,'v2'),(760,'v3')]:txt(x,y,f"{q[v+'_recovered_fixture_count']if v=='v1'else q[v+'_fixture_count']} / {q[v+'_fixture_reserved_m2']:.1f}",12)
 txt(990,y,'全体'if q['fully_inside_crop']else'範囲端',12);y+=47
wrap(35,458,1120,'v3で個別改修した書店はB1-017です。他の書店を同じ品質で仕上げたとは報告していません。B1-059は切出し端であり、完成店舗として数えません。',12,25)
for name in ['07-1F-cafe-interior','08-1F-bookshop-interior','12-fashion-interior','16-bookshop-wall-collection','17-cafe-service-and-seating','18-fashion-wall-and-fitout','04-2F-storefront','06-1F-north-shopping-street']:
 new(name+' / 店舗と通路の実画面','左：v2。右：v3。位置・注視点・FOVを一致。通常の材質・照明で取得したGodot Viewport。',True)
 image(E/'before-v2'/(name+'.png'),fitz.Rect(30,108,579,417));image(E/'after'/(name+'.png'),fitz.Rect(612,108,1161,417))
 wrap(35,474,1120,'用途別の造作・レジ・壁面・客席・照明を評価する比較です。実機の人間による探索検証ではありません。3店舗以外の内装や1〜3階の全店を改修したとはしていません。',12,25)
 if name.startswith(('04-','06-')):wrap(35,590,1120,'店の外観は入口幅2.4mや看板上限など共通仕様が残り、通路からの均一感は未解決です。図面上の全体計画と、前面意匠の再設計を別途進める必要があります。',12,25,red)
new('間口・奥行き・用途未確定床の整理','見た目だけの色違いで均一感を解決しない。')
y=108
for q in m['shops']:
 if q['id']not in ['B1-017','B1-040','B1-043']:continue
 txt(35,y,q['id'],12,green);wrap(170,y,630,f"台帳間口 {q['frontage_m']:.2f}m / 台帳奥行 {q['depth_m']:.2f}m / 入口 {q['clear_width_m']:.1f}m。",12,23);y+=47
wrap(32,282,775,'同じ入口幅、ガラス主体の前面、看板幅の上限は均一感を残しています。書店の開放型前面、カフェの窓側席とサービス側、衣料のショーウィンドウと入口を用途に応じて設計する必要があります。入口拡幅は未適用です。\n時の広場切出しの用途候補はspace-program.csvに位置・面積・隣接機能・根拠を記録。納まり用、既存倉庫への編入、在庫への編入、外郭縮減の候補を区分しています。必要な設備量の裏付けなしに全てを設備室とはしていません。',12,25)
new('大型12区画・核店舗6区画：具体化した検討','全18区画は現在の3D範囲外。以下は寸法付き平面・設備ゾーニングで、施工図・実装完成ではありません。')
wrap(32,108,775,'家電：体験展示・映像/音響・大型家電・修理受取を区分。\n食品：青果・常温棚・冷ケース・下処理、レジ/搬入/冷蔵の分離を検討。\n大型書店：新刊・一般書・児童・専門書、低い島と壁面・読書席。\n大型衣料：入口の滞留、商品街区、試着・相談、レジ/受取。\nシネマ：12×18mの小型上映室4室、各80席案。既存内法4.825mから音響天井0.35m・最奥段床0.72mを除くと3.755m。大型スクリーンの高天井を保証していません。\nフードホール：厨房/受渡し、共用客席、家族席、返却・清掃を区分。\nカフェ/レストラン：作業設備・客席形式・配膳と客動線を用途別に変えています。',12,27)
wrap(32,457,775,'18案の什器が区画外へ出ない・重ならないことは平面で検査。全什器への到達、避難、遮音、構造、厨房排気・排水、設備負荷は未検証です。',11,23,red)
for study in large:
 eq=next(q for q in equipment if q['id']==study['id']);new(study['id']+' / '+study['category'],'寸法付き平面検討。既存区画と主経路を保持した案。原図へ未反映・Godot範囲外。',True)
 svg(G/(study['id']+'-functional.svg'),fitz.Rect(30,94,765,668))
 txt(790,109,f"区画 {study['area_m2']:.1f}㎡",14,green);txt(790,138,f"売場 {study['sales_m2']:.1f}㎡",12);txt(790,166,f"内法 {study['height_clear_m']:.3f}m",12);txt(790,193,f"入口 {study['door_width_m']:.1f}m",12);txt(790,220,'主経路予約 3.6m',12)
 y=261
 for z in study['zones']:
  y=wrap(790,y,365,z['id']+' / '+z['name']+f" / {z['polygon'].area:.1f}㎡",10,18)+6
 y+=8
 for k,v in eq['module_dimensions_m'].items():
  y=wrap(790,y,365,k+f' {v[0]:.2f}×{v[1]:.2f}m',9,16)
 wrap(35,710,1120,'図の什器は用途別の配置検討。主経路予約を除く領域に納め、幾何の外部流出・重複を検査しています。全配置の移動・営業運用可能性を保証するものではありません。',12,24)
new('中央専門店街の統合2案：未適用','周辺の小・中型店を残して中央に滞在型店舗を加える案。原本の店舗数や入口を変更していません。',True)
y=113
for q in mergers:
 txt(35,y,q['id'],13,green);y=wrap(35,y+27,1110,' / '.join(q['stores'])+f" → {q['proposed_id_not_applied']} / {q['combined_area_m2']:.1f}㎡\n用途案："+q['recommended_use']+f" / 店舗数 {q['store_count_before']}→{q['store_count_after_if_approved']}（承認された場合のみ）\n主入口：{q['primary_entry_store']}、既存幅{q['entry_width_m']:.1f}m。副入口1か所と既存在庫扉を維持する案。\n周辺店："+' / '.join(q['adjacent_store_ids'])+'\n'+q['balance_assessment'],11,23)+28
wrap(35,695,1120,'入口の拡幅案は4.8/3.6/2.4mの平面開口収まりを別途計算。売場同士の接続辺がない組み合わせは在庫再編が必要。開口の構造と全体の内部到達性・避難は未検証。',12,25,red)
for i,q in enumerate(mergers):
 new(q['id']+' / 入口と内部接続の検討','形状の連結と、客が売場を回遊できることを区別。無断統合はしていません。',True)
 svg(S/f'audit/proposal-{i+1}-before.svg',fitz.Rect(30,96,560,430));svg(S/f'audit/proposal-{i+1}-proposal.svg',fitz.Rect(625,96,1155,430))
 y=483
 for opening in q['entry_width_studies']:txt(35,y,f"主入口幅案 {opening['proposed_width_m']:.1f}m / 公共＋統合区画内に開口予約が収まる：{opening['fits_2D_aperture_footprint']}",12);y+=28
 for c in q['internal_sales_connection_studies']:y=wrap(35,y,1120,c['a']+' / '+c['b']+f"：売場共有辺{c['sales_shared_boundary_m']:.2f}m。"+c['status'],10,19)
new('性能・使用素材・検証の限界','目標品質と測定済みの範囲を区別。FF15級には未到達。')
fps=render['performance'][0];wr=render['walking_performance'];wrap(32,109,775,f"Godot {render['godot_version']['string']} / {render['renderer']} / 1280×720 / MSAA4x / NPC0人。\n{render['adapter']}。CPUソフトウェア描画の参考値：静止{fps['fps_from_mean_frame_time']:.2f} FPS、移動{wr['fps_from_mean_frame_time']:.2f} FPS。各20フレームの短い測定で、実機GPUや5,000人の性能には換算しません。\n建築・造作・本・看板・ポスター・PBRマップはオリジナル。Noto Sans CJK JPはSIL OFL1.1、Godot4.6.3はMIT。外部ゲーム素材・写真・HDRI・実在店舗ロゴは使用していません。\nAOは頂点接触陰影で、拡散GIではありません。エスカレーター接触は連続勾配近似。Windows実機の人間操作・全館・全位置・構造/設備/法規/営業運用は未検証です。",11,24)
new('残課題と次の全体設計','局所案6か所を承認しても、全館の用途未確定領域は解消しません。')
wrap(32,108,775,'1. 街区ごとに、店舗の前面と奥行き、必要な搬入・保守・設備面積を先に再配分する。\n2. 広い残余は外郭縮減と店舗街区の再設計を比較し、意味のない道を設計段階でなくす。\n3. 全内部領域が適切な入口を持つことを確認し、離れた片や極細領域を用途面積へ算入しない。\n4. 共有境界・開口・床から3Dと衝突を一体生成し、実際に見える境界を歩いて評価する。\n5. 主要広場・吹き抜け・エスカレーター・館間接続はできる限り維持する。\n6. 図面・自動操作・実画面・人間の実操作をそれぞれ記録し、完成版生成の停止条件を全館で解消する。',12,28)
wrap(32,360,775,'提出物は原因調査・設計ルール・未承認の修正案・独立した比較用プロトタイプです。全館改修の完成報告ではありません。ゲーム本体への統合、原図上書き、中央店舗の統合は行っていません。',13,27,red)
# Complete readable coordinate register. Causes/policies are supplied in the full CSV, category legend here.
legend={'UNALLOCATED_ENVELOPE_REMAINDER':'U','BETWEEN_STORE_UNOWNED_GAP':'G','RAW_POLYGON_SHORT_OR_ACUTE_CORNER':'C','BACKROOM_COMPONENT_WITHOUT_OWN_ACCESS':'B','SALES_COMPONENT_WITHOUT_OWN_ACCESS':'S','DISCONNECTED_TENANT_COMPONENT':'D','SUB_0_5_M2_FRAGMENTS_AGGREGATE':'M','NARROW_PUBLIC_SPUR_CANDIDATE':'N'}
new('全件座標一覧：種別と対応方針','以下の一覧は確認候補を含む。確定した不良516件という意味ではありません。')
y=109
for kind,code in legend.items():
 n=sum(q['kind']==kind for q in root['issues']);txt(35,y,code+' / '+str(n)+'件',11,green);y=wrap(165,y,640,kind,10,18)+17
wrap(32,440,775,'U：用途帰属と外郭を設計。G：両側の共有境界を再設計。C：意図的な曲線/柱/開口と区別。B/S/D：各内部領域の入口と連結を確認。M：非居室・納まりの所有者を確定。\n全件の原因・対応方針はissue-register.csv。Mの個別微小片の座標はmicro-fragment-register.csv（内訳の別表）。座標は世界XZメートル、Yは階高です。',10,20)
issues=root['issues']
for start in range(0,len(issues),22):
 new(f'全件座標一覧 {start+1}〜{min(start+22,len(issues))} / {len(issues)}','同じ場所が複数種別で挙がることがあります。面積の単純合計は禁止。',True)
 for t,x in [('問題ID',35),('階',240),('店舗ID',300),('世界 X / Y / Z m',590),('種別',920),('領域㎡',1010)]:txt(x,104,t,11,green)
 y=138
 for q in issues[start:start+22]:
  txt(35,y,q['issue_id'],9);txt(240,y,q['floor'],10);wrap(300,y,260,q['store_ids']or'—',9,13);txt(590,y,f"{q['world_x_m']:.3f} / {q['world_y_m']:.3f} / {q['world_z_m']:.3f}",10);txt(932,y,legend.get(q['kind'],'?'),11);txt(1010,y,f"{q['area_m2']:.3f}",10);y+=29
OUT=R/'downloads/FIND_YOURSELF-B-Root-Review-v3.pdf';doc.save(OUT,garbage=4,deflate=True)
checked=fitz.open(OUT);bad=[]
for i,pg in enumerate(checked):
 pg.get_pixmap(matrix=fitz.Matrix(.15,.15),alpha=False)
 for b in pg.get_text('dict')['blocks']:
  if b['type']!=0:continue
  for l in b['lines']:
   for sp in l['spans']:
    r=fitz.Rect(sp['bbox'])
    if r.x0<-.5 or r.y0<-.5 or r.x1>pg.rect.width+.5 or r.y1>pg.rect.height+.5:bad.append({'page':i+1,'text':sp['text'],'bbox':sp['bbox']})
receipt={'pages':len(checked),'all_pages_rendered':True,'text_outside_pages':bad,'warnings':fitz.TOOLS.mupdf_warnings(),'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'root_issue_register_rows':len(root['issues']),'production_design_complete':False};(E/'pdf-verification.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2));print('PDF',len(checked),OUT.stat().st_size,receipt,flush=True)
# Human-readable sources, evidence, code review material. All writes are new v3 documentation only.
for folder in ['authoring','runtime-source','evidence']:(DOC/folder).mkdir(exist_ok=True)
for p in(P/'authoring').glob('*'):
 if p.is_file():shutil.copy2(p,DOC/'authoring'/p.name)
for p in P.iterdir():
 if p.is_file()and(p.suffix in['.gd','.gdshader','.tscn']or p.name=='project.godot'):shutil.copy2(p,DOC/'runtime-source'/p.name)
shutil.copy2(P/'README.md',DOC/'README.md')
for folder in [A,G]:shutil.copytree(folder,DOC/folder.name,dirs_exist_ok=True)
for f in E.glob('*.json'):shutil.copy2(f,DOC/'evidence'/f.name)
for name in ['camera-lock.json','final-cameras.json','cutaway-cameras.json','scene-manifest.json','expanded-qa-inputs.json']:shutil.copy2(S/name,DOC/name)
for folder in ['before-v1','before-v2','after','cutaway-before','cutaway-after']:
 (DOC/folder).mkdir(exist_ok=True)
 for p in(E/folder).iterdir():
  if p.is_file()and p.suffix in['.png','.json']:shutil.copy2(p,DOC/folder/p.name)
