from pathlib import Path
import json,hashlib,html,csv,shutil,zipfile
from PIL import Image
P=Path(__file__).resolve().parents[1];R=Path('/workspace/v17-review');V=Path('/workspace/FIND_YOURSELF-Site-v16');pairs=[]
def read(p):return json.loads(Path(p).read_text())
notes={
'V16-A-visitor':'既存広場の開放感を維持。実在する不透明壁の広告・造作、店舗正面、樹木を更新。広場全体の天井・柱・什器の専用モデル化は未完成。',
'V17-A-long-street':'実際の店舗境界に沿うファサード・架空ブランド・商品広告を更新。店舗入口と保護動線は維持。まだ長い無地面と反復する造作が残る。',
'V16-B-aichi':'既存の愛知県フェアを維持し、各屋台の図案入り告知と周辺壁面広告、店舗正面、樹木表示を更新。催事全体の再制作ではない。',
'V16-B-fair-close':'9既存ブースの告知表現を更新。F11で今回の掲示も連動。食器・屋台形状・ステージの全面再制作は行っていない。',
'V17-B2-gallery':'2F専門店街の造作、各店のロゴと商品広告、店頭照明。床開口・乗降設備・店舗境界は変更なし。',
'V17-B3-gallery':'3Fも実在する入口と区画に沿って正面を更新。全館の天井造作を完成したという評価ではない。',
'V16-C-kids':'既存遊具と保護者スペースを維持。周辺店舗の正面と樹木表示を更新。遊具本体の新規追加はなし。',
'V16-C-dog':'既存二重ゲートと設備を保持。周辺景観の仕上げを更新。ドッグランの運営・犬の挙動は今回の対象外。',
'V16-C-melon':'既存メロンパン車両の手前へ注文・受取カウンターと図案入りメニューを配置。営業動作や商品購入機能は未実装。',
'V16-C-courtyard':'屋外の店舗正面と壁面広告を更新。通常版の上階デッキは維持。空の見え方を変えるF4は別案のまま。',
'AB1-003-interior':'既存食品売場に専用ベーカリーケースと調理機器を追加。保護した店内主路を維持。全面的な食品部門再編ではない。',
'BB1-MARKET-interior':'青果・既存食品棚を保持し、専用のパン・惣菜ケースを追加。冷蔵・加工食品すべての商品モデルの個別制作は未完成。',
'ARF-002-terrace':'休憩・飲食エリアに什器を追加し、カフェ席の浮いた背もたれを実接合モデルへ変更。屋上全域の景観完成ではない。',
'B-RF-garden':'既存の庭と支持確認済み施設を維持。休憩・展示什器を更新。RF-SUPPORT-16等の支持未確認箇所は未承認。',
'v15-B1-030-beauty_tester_bar':'化粧品専用のテスター台・鏡・展示什器を追加。店舗の奥行きと主通路を維持。',
'v15-B1-N03-electronics_media_demo':'実機、キーボード、支持ヒンジ、盗難防止コードを含む家電デモ台を追加。',
'shop-apparel-C1F-CW-1':'服飾専用ラック、ハンガー、衣服形状と縫い目を持つ展示を追加。既存試着・レジ動線を維持。',
'shop-book-A1F-007':'ジャンル壁棚の背表紙と面陳列を追加。店舗面積や入口を変更せず、既存中央通路を保護。',
'shop-cafe-C1F-CSW-3':'専用のエスプレッソ機器・バックバー・パンケースで既存カフェの用途を補強。厨房の全設備完成ではない。',
'ES-west-site':'F6未承認別案。機械配置は維持し、乗り継ぎ案内の図案を改善。8.4m経路と短縮候補を別資料で比較。',
'ES-west-upper':'F6未承認別案。7.53m候補は中央と中間部±35cmの自動歩行を通過。6.4m直線候補は手すり側の余裕が不足し不採用。'}
def location(id):
 if id.startswith('ES-west'):return 'B館2F'if id.endswith('upper')else'B館1F'
 if id.startswith('V17-B2'):return 'B館2F'
 if id.startswith('V17-B3'):return 'B館3F'
 if id.startswith('AB1'):return 'A館B1'
 if id.startswith('BB1'):return 'B館B1'
 if id.startswith('ARF'):return 'A館RF'
 if id.startswith('B-RF'):return 'B館RF'
 if 'C-'in id or 'C1F'in id:return 'C館1F'
 if id.startswith('V16-B')or id.startswith('v15-B1'):return 'B館1F'
 return 'A館1F'
for before,after,variant in [('before','after','通常版'),('before-C-option','after-C-option','C館F4・未承認'),('before-ES-option','after-ES-option','B館F6・未承認')]:
 a=read(R/after/'captures.json');b=read(R/before/'captures.json');by={s['id']:s for s in b['shots']}
 assert a['runtime']['main_script_sha256']==hashlib.sha256((P/'main.gd').read_bytes()).hexdigest(),after
 assert b['runtime']['main_script_sha256']==hashlib.sha256((V/'main.gd').read_bytes()).hexdigest(),before
 for s in a['shots']:
  t=by[s['id']];assert s['eye']==t['eye']and s['look']==t['look']and s['fov']==t['fov'];assert s['resolution']==t['resolution']==[1920,1080]
  assert max(abs(x-y)for x,y in zip(s['actual_camera_global'],t['actual_camera_global']))<.002
  assert max(abs(x-y)for x,y in zip(s['actual_look_direction'],t['actual_look_direction']))<.0001
  row={'id':s['id'],'title':s.get('title',s['id']),'variant':variant,'floor':location(s['id']),'before':before+'/'+s['id']+'.png','after':after+'/'+s['id']+'.png','eye':s['eye'],'look':s['look'],'resolution':s['resolution'],'native_Godot_Viewport':True,'actual_camera_match':True,'change':notes.get(s['id'],'店舗正面と景観仕上げを更新。'),'capture_fps_observation':s.get('reference_fps_1s_window'),'draw_calls':s.get('draw_calls'),'renderer':a['runtime']['adapter'],'Windows_GPU':False}
  if variant.startswith('C館'):row['change']='F4の未承認構造を維持した比較。店舗正面・樹木・広告の仕上げを更新。新たなデッキ削除や支持構造の承認はしていない。'
  for k in ['before','after']:
   p=R/row[k];assert Image.open(p).size==(1920,1080);row[k+'_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
  pairs.append(row)
assert len(pairs)==23,len(pairs)
(R/'screenshot-index.json').write_text(json.dumps(pairs,ensure_ascii=False,indent=2))
summary=read(R/'検査結果.json');design=read(P/'source/v17/scene-design.json');pres=read(R/'source/preservation.json');assert pres['all_unchanged']
body=['''<!doctype html><html lang="ja"><meta charset="utf-8"><title>FIND YOURSELF v17 — 実画面比較</title><style>body{background:#111b1c;color:#e8e6dc;font:16px/1.8 system-ui,sans-serif;margin:24px auto;padding:0 24px;max-width:1500px}h1,h2{color:#d6bd85}a{color:#d7c89e}p{max-width:1100px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:12px}.pair img{width:100%;height:auto}section{padding:22px 0;border-top:1px solid #405255}small{color:#b6c6c4}table{border-collapse:collapse}td,th{border:1px solid #5a6663;padding:6px 12px;text-align:left}.compare{position:relative;aspect-ratio:16/9;max-width:1500px;overflow:hidden}.compare img{width:100%;position:absolute;top:0;left:0}.new{clip-path:inset(0 0 0 50%)}input[type=range]{width:100%}button{background:#dbcfae;color:#152a26;padding:7px 14px;border:0;border-radius:4px}details{margin:14px 0}@media(max-width:800px){.pair{grid-template-columns:1fr}}</style><h1>FIND YOURSELF v17</h1><p>v16を基準とした独立した景観・店舗品質の検証版です。Godot 4.6.3 / Forward+ の1920×1080実Viewportを、同一位置・向き・FOVで23組比較します。画像をクリックすると原寸PNGを開けます。ゲーム本体へは統合していません。</p><p><strong>全館完成・FF16級の達成とはしていません。</strong>店舗正面の更新と代表業種の展示強化が中心です。広い無地面、周辺景観の密度、各店舗の個別売場計画は依然改善が必要です。人間による実操作とWindows GPUのFPSは未検証です。</p><p><a href="変更内容と未完成.md">変更点・未完成事項</a> / <a href="検査結果.json">検査結果</a> / <a href="source/全15層の改善範囲.csv">15層の更新範囲</a> / <a href="plans/v17-15-floor-improvement-map.pdf">15層の更新位置図</a> / <a href="proposals/F6-candidate-evaluation.json">F6経路比較</a> / <a href="proposals/C-roof-water-garden-design.pdf">C屋上の設計検討</a></p><p>新しいモデル・広告・店頭照明を実際の区画と既存壁に合わせています。既存壁の粗い照合を通過した58候補は、198本ずつの物理レイで再点検し、4候補を除外しました。さらにB館2F・3Fの客用通路側6面を追加しました。ベイク間接光の四角い境界が実画面に出たため、その照明方式は既定表示に採用していません。</p>''']
for i,r in enumerate(pairs):
 body+=['<section><h2>'+html.escape(r['title'])+'</h2><small>'+html.escape(r['variant']+' / '+r['floor'])+' / eye '+str(r['eye'])+' / 1920×1080</small><p>'+html.escape(r['change'])+'</p>',f'<div class="compare"><img src="{r["before"]}" loading="lazy" alt="v16"><img class="new" id="cmp{i}" src="{r["after"]}" loading="lazy" alt="v17"></div><input aria-label="v16とv17の境界" type="range" min="0" max="100" value="50" oninput="document.getElementById(\'cmp{i}\').style.clipPath=\'inset(0 0 0 \'+this.value+\'%)\'"><small>左：v16 / 右：v17　スライダーで切替</small>',f'<details><summary>並べて比較・原寸画像</summary><div class="pair"><a href="{r["before"]}"><img src="{r["before"]}" loading="lazy" alt="v16"></a><a href="{r["after"]}"><img src="{r["after"]}" loading="lazy" alt="v17"></a></div></details></section>']
body+=['<h2>検証と性能</h2><table><tr><th>区分</th><th>結果</th><th>方法</th></tr>']
for t in summary['tests']:body.append('<tr><td>'+html.escape(t['name'])+'</td><td>'+str(t['passed'])+' / '+str(t['passed']+t['failed'])+'</td><td>'+html.escape(t['method'])+'</td></tr>')
body+=['</table><p>描画はLinuxのソフトウェアVulkan（llvmpipe）です。各画像のFPSは撮影時の短い観測値で、安定したベンチマークでもWindows GPUの性能でもありません。144FPS達成は確認していません。新規造作に伴う描画負荷の継続測定とLOD調整は残課題です。</p><p>F4・F6・水上庭園・RF-SUPPORT-16は未承認。水盤は未実装で、構造耐力・防水・排水・避難は未検証です。外周道路と駅連絡通路は変更していません。</p></html>']
(R/'index.html').write_text('\n'.join(body))
(R/'変更内容と未完成.md').write_text('''# v17の変更と到達範囲\n\nGodot 4.6.3の実Viewportをv16と同一視点で比較しています。全館完成・AAA品質の達成ではありません。\n\n今回実装したもの\n\n- 既存458店舗・909辺の実境界に沿う正面造作、480ブランドの独自図案・ロゴ台帳、商品CGを含む広告。屋上の開放型22店舗に浮いた正面壁は作っていません。\n- 不透明壁の60区間に仕上げ・広告。粗い検査の58候補から、細い開口を見落とす4候補を除外。上階の客用通路側6面を追加。198レイによる照合は厳密な位相証明や建築品質保証とは区別します。\n- 書店・化粧品・衣料・雑貨・家電・食品/カフェの専用什器、代表店舗と休憩エリアの80配置。16点は実什器の上に載せた小物で、床置き什器とは区別しています。全店舗の内装更新ではありません。\n- 愛知県フェアの9既存屋台へ図案入り告知、F11連動。既存ステージ・食品工芸モデル・主通路は維持。\n- C館キッチンカーの注文/受取設備とメニュー。屋上カフェ等のカフェ椅子を実接合モデルへ修正。樹木の葉と枝の接続・樹冠を改善。\n- 自然光・店頭照明を調整。ベイクした間接光は四角い明暗差が現れたため不採用。既定表示にそのキャッシュを使わず、無効なキャッシュは配布していません。\n\n維持したもの\n\n- 15層、480店舗ID、建築パック19点、通路・床開口・館間接続、プレイヤー、ESの滑らかな搬送、EV・階段・扉。\n- M、F4、F6、F9、F11。標準1920×1080、144FPS上限、VSync初期ON。\n- 元ゲームのNPC・スキャン・AP・セーブは変更・統合なし。\n\n未承認・提案\n\n- F4 C館は別案のまま。v17は仕上げを更新し、通常版のデッキを無断で削除していません。\n- F6機械配置は維持。既存8.4m、角を緩める7.53m、最短6.4mを比較。最短は中心の通行に成功しても片側35cmで手すり接触が発生し不採用。7.53mは中心・中間部の左右35cmを通過しましたが、人の見通しや混雑は未検証。次の確認候補であり承認済みではありません。\n- C屋上水上庭園：実屋上の公開床と支持床を照合。指定した余裕を持つ12×16mの軸平行候補を確定できず、設置位置は未決定。これは全向きで不可能という証明ではありません。240㎡水盤のローカル詳細と、深さ40/80/120mmの水荷重を別案で提示。80mmなら水だけで19.2t。躯体・排水等は未検証で、通常版・F4とも未実装。\n- RF-SUPPORT-16、支持未確認の屋上植栽は未承認維持。\n\nまだ不十分なもの\n\n- 通路・広場に残る広い無地面、単調な天井、店舗ごとの素材/ディテール、広告の館全体での構成。\n- 全480店舗の入口から奥までの個別売場計画。今回の専用什器が全店に置換されたわけではありません。\n- C館通常版の過剰デッキ、屋外植栽と建物支持表現の全面仕上げ。構造別案の承認と設計見直しが必要です。\n- 地下食品売場の全商品・部門別売場、屋上全域の景観、B館の他広場の新規水景・季節展示。既存施設を維持し、追加していない設備は完成扱いにしません。\n- キッチンカーの実営業、催事運営、子ども・犬の挙動は未実装。\n- 人間の実操作、Windows GPU性能、144FPS、構造安全・車両軌跡は未検証。\n\n制作環境と素材\n\n- Blender 4.3.2の専用モデル、オリジナルCG商品写真と図案、既存の商用利用条件が明記されたテクスチャを使用。新たな外部写真を確認済みとはしていません。\n- 商品写真風のCGは広告の素材であり、Godot証拠画像とは別です。参考写真・他ゲームの固有資産・実在ブランドのロゴは転用していません。\n- 使用条件・継承素材の出典はlicensesフォルダ。ブランド名の商標調査は未実施。\n\n確認方法\n\nReviewを展開してindex.htmlを開くと、23組の実画面を拡大・スライダー比較できます。sourceのCSVは館・階・座標・実装範囲、plansは15層の更新位置、testsは自動検査、proposalsは未承認案です。検査の成功件数を景観品質の完成判定としていません。\n''')
# Preserve current licence evidence, experimental decisions, wall host audit and exact photography provenance.
shutil.copytree(P/'licenses',R/'licenses',dirs_exist_ok=True);shutil.copy2(P/'source/v17/lighting-decision.json',R/'source/lighting-decision.json')
perf={'environment':'Linux llvmpipe software Vulkan, Godot Forward+ 1920x1080','Windows_GPU':False,'144FPS_confirmed':False,'steady_state_benchmark':False,'observations':[{k:r[k]for k in['id','variant','capture_fps_observation','draw_calls','renderer']}for r in pairs]};(R/'描画性能の観測.json').write_text(json.dumps(perf,ensure_ascii=False,indent=2))
print('V17_REVIEW',len(pairs),'native matched pairs, regression failures',summary['reported_regression_failures'])
