"""Extend root report with latest user steering; publish only new v3 documentation."""
from pathlib import Path
import runpy,json,csv,hashlib,shutil,collections
import fitz
P=Path(__file__).resolve().parents[1];R=Path('/workspace/1');S=P/'source';E=P/'evidence';O=R/'downloads/FIND_YOURSELF-B-Root-Review-v3.pdf';D=R/'docs/b-time-plaza-root-review-v3'
g=runpy.run_path(str(P/'authoring/report_v3.py'));g['doc'].close();doc=fitz.open(O);g['new'].__globals__['doc']=doc;base_page_count=len(doc);new=g['new'];txt=g['txt'];wrap=g['wrap'];image=g['image'];svg=g['svg'];font=g['font']
v=json.load(open(S/'vertical-review/vertical-review.json'));area=json.load(open(S/'backroom-review/area-review.json'));glass=json.load(open(E/'stock-glass-results.json'));light=json.load(open(E/'lighting-comparison.json'));phys=json.load(open(E/'escalator-transfer-walk.json'));roles=json.load(open(S/'stock-role-corrections.json')) if(S/'stock-role-corrections.json').exists()else{}
new('総合改善指示への追加検討 / 結果一覧','2026-10-27 JST。以下は最新の昇降設備・バックヤード・3階照明の追加資料です。')
wrap(32,108,775,'実施：検証範囲の80店舗で在庫とガラスの境界を照合し、問題の5店舗を修正。入口のない在庫片4か所は売場・陳列ニッチへ戻し、既存売場面積は維持。3階の直射・床反射を調整。\n設計案のみ：EV2昇降路の候補、時の広場のエスカレーター積層配置。原図・Godotの設備位置は変更していません。\n未完：全館の未割当床約2.2万㎡、在庫作業条件に届かない56店舗の再計画、全館の自然さと人間による実操作。',12,27)
wrap(32,365,775,'この追加資料で全館改修を完成扱いにしていません。通常の本番生成は停止中です。独立比較シーンは未承認案の確認用としてのみ起動できます。',13,27,(.63,.24,.17))
new('エレベーター：図面と利用可能設備を分離','原図3昇降路×5階＝15停止階。現在の独立3D検証では稼働するEVは0台です。',True)
y=116
for q in v['existing']:
 b=q['source_shaft']['coordinates'][0];xs=[p[0]for p in b];zs=[p[1]for p in b];txt(35,y,q['id']+f'  世界中心 X={(min(xs)+max(xs))/2:.1f}, Z={(min(zs)+max(zs))/2:.1f}',14);y+=34
 txt(35,y,'5階の開口位置一致：'+str(all(f['opening_xz_consistent']for f in q['stops']))+' / 昇降機室4×4m',12);y+=45
wrap(35,393,1120,'検証範囲にはK2の一部のみが入り、設備核は閉鎖された形状です。かご・制御・呼出し・乗降機能は未実装。元ゲーム全体のEV実装有無を断定した結果ではありません。\n図面上のEVまでの距離と、現在のGodotで利用できるEVへの距離を混同しません。後者は設備がないため算出不可です。',13,27)
for f in ['1F','2F','3F']:
 new('EV現状・改善案 / B館 '+f,'茶：原図のK1〜K3。青：新設候補K4/K5。候補は原図・3Dへ未反映。',True)
 svg(S/f'vertical-review/{f}-vertical.svg',fitz.Rect(30,93,1161,655));wrap(35,704,1110,'館全体の歩行可能領域と接続点から比較。K4は時の広場直近ではなく中央西側です。主要広場・店舗・車路の無断変更はありません。',12,25)
new('EV増設候補：5階整合と未解決項目','K4/K5は売場を減らさない位置を探索した候補。需要計算に基づく最適配置ではありません。',True)
y=110
for q in v['proposed']:
 txt(35,y,q['id']+f" / X={q['center'][0]:.3f}, Z={q['center'][1]:.3f}",14);y+=30
 y=wrap(35,y,1120,'昇降路4×4m、ロビー3.6×2.4m、接続通路2.4m。かご2×2.4m・扉1.4mはゲーム用の目標寸法。\n全5階で売場・駐車マス・車路との面積重複なし。在庫との重複もなし。\nただしB1・RFでは各24.64㎡の既存用途区画の再配分が必要。既存用途名と代替位置の詳細設計は未了。ロビーの実際の到達・横断安全・ピット・頂部・構造・防火・メーカー仕様も未検証。',12,25)+28
wrap(35,663,1120,'各階の同じ位置に昇降路を通せる平面候補であり、設備工事が成立するという承認済みの設計ではありません。',12,25,(.63,.24,.17))
new('昇降路・乗降ロビー / 5階断面案','寸法はゲーム設計値。上下位置を合わせる案で、構造・実機仕様の承認図ではありません。',True)
svg(S/'vertical-review/lift-five-level-section-proposal.svg',fitz.Rect(30,99,1161,745))
new('エレベーター歩行距離：比較方法と評価','原図の客用通路上の図面計算。機器の実動作・人間の歩行ではありません。')
wrap(32,107,775,'0.75m格子に入口・ロビーの明示ノードを追加し、半径0.30mのカプセルと線分の床内包を確認。失敗する地点を近傍へ移して合格にする処理はしていません。\n31地点：広場・大型/核店舗・駐車場来客入口・地下/屋上用途。各地点は等重みで、来客需要や待ち行列の推計ではありません。B1/RFの新設機への接続は未確定のため有利な距離に算入していません。',11,24)
y=308
for f in ['1F','2F','3F']:
 rr=[q for q in v['distance_rows']if q['floor']==f and q['old_plan_distance_m']is not None and q['add_central_and_east_plan_m']is not None];mean=lambda key:sum(q[key]for q in rr)/len(rr)
 txt(35,y,f+f" / 平均 {mean('old_plan_distance_m'):.1f}m → K4のみ{mean('add_central_only_plan_m'):.1f}m → K4＋K5 {mean('add_central_and_east_plan_m'):.1f}m",12);y+=38
wrap(32,448,775,'残課題：翼の広場は候補2機を加えても約162〜165mで、十分便利になったとは評価しません。売場を減らさず既存街区に収まる条件と利便性の両立を、次の設計で比較する必要があります。',11,23,(.63,.24,.17))
for start in range(0,len(v['distance_rows']),12):
 new(f'EV距離台帳 {start+1}〜{min(start+12,len(v["distance_rows"]))} / 31地点','単位m。原図3機→中央西側K4のみ→K4/K5。原図設備も現Godotでは使用不可。',True)
 for x,t in[(35,'階 / 地点'),(440,'既存3機'),(590,'＋K4'),(730,'＋K4/K5'),(880,'候補機')]:txt(x,112,t,12)
 y=150
 for q in v['distance_rows'][start:start+12]:
  txt(35,y,q['floor']+' / '+q['anchor'],11)
  for x,k in[(440,'old_plan_distance_m'),(590,'add_central_only_plan_m'),(730,'add_central_and_east_plan_m')]:txt(x,y,'未到達'if q[k]is None else f'{q[k]:.2f}',12)
  txt(880,y,q.get('proposed_lift')or'—',11);y+=43
new('EV案内表示の設計案 / 未実装','利用できない設備を、現在の検証シーンで利用可能として案内しません。')
wrap(32,106,775,'広場の分岐：EVピクト・機器ID・方向・図面距離を掲出。\n専門店街：曲がり角ごとに方向を継続。スタッフ専用扉とは表示を分ける。\n駐車場入口：段差を避ける来客動線と、利用可能な停止階を表示。\nEVロビー：館・階・機器ID、上下階用途、車椅子/ベビーカー動線を表示。\nMマップ案：既存計画機と増設候補を別表示し、未施工の機器は利用可能表示にしない。\n承認後の実装：各表示点から実際にロビーまでたどり、途中の欠落表示やスタッフ動線への誤誘導を確認。',12,27)
wrap(32,438,775,'今回のGodotにはEV操作・EV案内UIは追加していません。上記は配置案を承認後に施工するための表示計画です。',11,24,(.63,.24,.17))
new('エスカレーター：現状の設備と乗り継ぎ','全B館1〜3Fの原図は上り下り12バンク。現在の3D範囲は時の広場の4バンク。')
wrap(32,108,775,f"現状：1→2階が西側、2→3階が東側に離れています。図面経路50.89m。\n同じ既存配置を使った独立シーンの自動CharacterBody3Dで約{phys['actual_travel_m']:.2f}mを歩き、到達を確認しました。図面との小差は連続した経路追従で角を丸めることによります。人間の操作ではありません。\n推奨案：1→2階の位置を維持し、その直上に同じ進行軸で2→3階の上り下りを積層。2階の乗り継ぎは図面上20.06m。反対軸で重ねると乗降部が干渉するため採用しません。\n4列の横並び案は一部回廊を約2.6/4.2mへ狭めるため非推奨としました。",12,26)
wrap(32,450,775,'移設後のGodot歩行は未検証。移設・開口変更は承認待ちのため実施していません。',12,24,(.63,.24,.17))
for n,t in [('TIME-transfer-proposal-detail.svg','時の広場 / 2階乗り継ぎの新旧平面'),('TIME-stacked-section-proposal.svg','時の広場 / エスカレーター積層断面案')]:
 new(t,'比較図。バンク・乗降スペース・床開口を同時に検討。Godot位置は現状維持。',True);svg(S/'vertical-review'/n,fitz.Rect(30,95,1161,745))
new('エスカレーター案：開口・乗降・手すりの条件','主要吹き抜けと通路を維持。既存開口の単純コピーによる床欠落を防止。')
wrap(32,106,775,'勾配走行部11.8m、機械の投影14.8m、幅2.4m。乗降踊り場3×3.6m。\n床開口は到着側の上階の勾配部分だけに設け、出発側の床と櫛板1.5m、踊り場は切り抜かない。移設前の東側開口を床へ戻し、他の設備開口と主要吹き抜けは維持。\n提案平面では踊り場の床支持欠損、売場干渉、主要吹き抜けへの侵入は面積計算上なし。\n階高5.35/5.525mに対して、上下バンクの名目下端間隔は5.35−0.85＝4.50m。ただし構造材・手すり・頭上余裕の実機詳細は未検証。\n手すりの進行方向、櫛板と床の段差、上下階の案内、部材接合は承認後の3D移設で再検証します。',12,26)
new('バックヤード：全191区画の面積と作業評価','台帳：source/backroom-review/all-191-store-area-ledger.csv。1〜3階188区画＋地下2＋屋上1。')
wrap(32,107,775,'総面積・売場・在庫・在庫率・入口につながる在庫面積・最大内接幅・用途別作業モジュール・共用倉庫候補を記録。元面積と独立案の面積を分けています。\n全既存売場を維持し、一部は入口のない在庫片を陳列へ戻して売場が増えています。勝手な売場縮小・店舗統合はありません。\n56店舗は暫定の作業矩形や作業面積条件に届きません。通路や在庫率だけで運用できると判断せず、各店舗を見直し候補として残します。',12,26)
wrap(32,337,775,'面積条件は実在モールの法規・標準値ではありません。公開フロアガイドから在庫量や裏方の必要面積は分からず、実測した業界比率としては扱っていません。\n共用倉庫は既存S-*-W、S-*-Lのみを候補とし、清掃・管理室を転用しません。営業時間外の搬入・EV使用も未検証。現在の3Dでは共用倉庫は閉鎖代理形状、EVは稼働0台のため、実際に運用可能とは報告しません。',11,24)
new('用途別の作業条件と売場を減らさない代替案','以下は明示したゲーム用計画仮定。業界平均・法規・営業可能性の合格基準ではありません。',True)
wrap(35,110,1120,'飲食・食品：作業矩形3.6×2.1m、作業面積12㎡以上を一次条件。厨房・食材・洗浄・荷受けは別途。\n衣料・靴：3.6×2.1m、10㎡以上。在庫ラック・検品・着荷・スタッフ作業を検討。\n書籍：3.2×1.9m、9㎡以上。台車・荷解き・返品・在庫は在庫需要から追加検討。\n雑貨など：3.2×2.1m、9㎡以上。1.2m作業通路を想定。',13,30)
wrap(35,337,1120,'不足時の案：①既存共用倉庫への外部在庫、②納品頻度と台車/荷受け方式の見直し、③隣接する用途未確定床との街区再計画。\nどれも容量・人員・搬入距離・営業時間・防火/衛生を検証してから選択。売場面積を減らす案は適用していません。\n大型/核店は矩形が入るだけで合格にしません。映画館の映写・音響、食品の冷蔵/下処理、厨房の排気/排水などは別の設備計画が必要です。',13,29)
new('店舗規模：面積・用途分布の再評価','小型<150㎡、中型150〜500㎡、大型500〜1500㎡、核店1500㎡以上は今回の集計分類。',True)
y=111
for band in ['小型','中型','大型','核店舗']:
 rr=[q for q in area['stores']if q['area_band']==band];vals=[q['revision_plot_m2']for q in rr];sales=[q['revision_sales_m2']for q in rr];fails=sum(not q['working_space_screen_pass']for q in rr)
 txt(35,y,band+f' {len(rr)}区画 / 総面積{min(vals):.1f}〜{max(vals):.1f}㎡ / 売場{min(sales):.1f}〜{max(sales):.1f}㎡ / 在庫作業要検討{fails}',12);y+=55
wrap(35,375,1120,'1〜3階には大型12・核店舗6区画が存在しますが、時の広場切出しには含まれません。検証範囲の49完全区画だけを見ると大型店舗の規模差を感じられない点は残ります。\n小型の衣料・書籍・飲食は商品点数と営業形態の裏付けが必要。形状や面積があるだけでは妥当と判定しません。B館全体の用途と面積・在庫の対応は全件台帳で追跡できます。\n間口・奥行きの比較、用途別の配置図、18大型区画の内部計画は本資料前半とprogram-review-v3に収録。中央統合2案は未適用です。',12,26)
for start in range(0,len(area['stores']),18):
 new(f'全店舗の面積台帳 {start+1}〜{min(start+18,len(area["stores"]))} / 191','単位㎡。独立案の総区画/売場/在庫、在庫率、作業モジュール検査。詳細はCSV。',True)
 for x,t in[(35,'ID / 用途'),(410,'総区画'),(545,'売場'),(675,'在庫'),(790,'在庫%'),(905,'作業検査'),(1030,'3D範囲')]:txt(x,108,t,11)
 y=143
 for q in area['stores'][start:start+18]:
  txt(35,y,q['id']+' / '+q['category'],9)
  for x,k in[(410,'revision_plot_m2'),(545,'revision_sales_m2'),(675,'revision_stock_m2'),(790,'revision_stock_percent')]:txt(x,y,f'{q[k]:.2f}',10)
  txt(905,y,'条件内※'if q['working_space_screen_pass']else'要検討',10);txt(1030,y,q['validation_scope'],9);y+=32
 wrap(35,748,1120,'※作業矩形の幾何判定であり、在庫・営業・法規の合格ではありません。元面積と差分はCSVに保存。',10,20)

category_items=list(area['summary']['by_category'].items())
for start in range(0,len(category_items),14):
 new(f'業種別の在庫割合 / {start+1}〜{min(start+14,len(category_items))}','修正案の在庫率。比率の高低だけで営業妥当性を判定しません。',True)
 for x,t in [(35,'用途'),(430,'店舗数'),(580,'在庫率の範囲%'),(900,'作業条件要検討')]:txt(x,110,t,12)
 y=150
 for cat,q in category_items[start:start+14]:
  txt(35,y,cat,12);txt(450,y,str(q['stores']),12);txt(580,y,f"{q['stock_ratio_min_percent']:.2f}〜{q['stock_ratio_max_percent']:.2f}",12);txt(940,y,str(q['working_geometry_screen_fail']),12);y+=38

new('在庫のガラス張り：原因と全80店舗の是正','全店舗外周を同じ窓処理へ流すと、共用床に接する在庫の面もガラスになっていました。')
wrap(32,108,775,'修正ルール：窓は売場が接する前面だけ。在庫・非居室の境界を除外し、不透明壁の開口切欠きも同じ売場境界へ限定。端部の枠を補い、在庫外壁と間仕切りは天井まで不透明にします。\n実ガラスメッシュの投影三角形と在庫ポリゴンを照合し、80店舗中5店舗に元のガラス干渉を検出。修正後の残存は0店舗。用途の異なる壁・開口を区別した修正で、ガラス色の変更だけではありません。',12,26)
y=330
for id in glass['affected_baseline_ids']:txt(35,y,id,13);y+=30
wrap(295,333,490,'注意：従業員扉は通常閉。Fで開ける検証操作では内部が見えます。意図したオープンキッチン例外は今回設定していません。\nB2-070の約13mの在庫面は不透明化により閉じた壁として残ります。客用景観の改善は入口/用途計画の課題で、プライバシー是正だけで自然な前面が完成したとは判断しません。',10,23)
for id,name in [('B1-040','28-privacy-B1-040'),('B2-070','29-privacy-B2-070')]:
 new(id+' / 在庫境界のGodot実画面','左v2、右独立v3。姿勢・FOV・解像度・MSAA固定。光源と材料は明示した変更。',True);image(E/'before-v2'/(name+'.png'),fitz.Rect(30,112,579,421));image(E/'after'/(name+'.png'),fitz.Rect(612,112,1161,421));wrap(35,480,1120,'ガラスと在庫の対応を修正。従業員扉・不透明外壁・売場との間仕切りを区別。閉鎖壁が長い箇所の景観は別の残課題です。',12,25)
new('80店舗のガラス検査：読み方','全件の店舗IDはglass-80-store-results.csv。実メッシュの三角形投影を独立に照合。')
wrap(32,108,775,'検査範囲：切出しと交差する80店舗（完全に含まれる49区画と、一部だけ入る区画）。\n元設計の在庫境界・修正案の在庫境界・実際に出力されたガラスを区別します。生成時の境界線分監査に加え、実メッシュの投影面積でも在庫との干渉を追跡しています。\n入口のない在庫片はB1-022の2片、B1-038、B3-008の計4片を売場・陳列の役割へ戻しました。小さいというだけで設備室と呼んだり、在庫能力へ算入したりしていません。\n検査の合格は80店舗のプライバシー境界の結果です。全店舗内装・在庫運用・避難・全館の不自然な隙間を合格にする結果ではありません。',12,27)

for start in range(0,len(glass['stores']),22):
 new(f'全80店の在庫ガラス検査 {start+1}〜{min(start+22,len(glass["stores"]))}','実メッシュ投影の在庫干渉㎡と、生成時の在庫面ガラス長m。0は幾何許容差内。',True)
 for x,t in [(35,'店舗ID'),(250,'元 干渉㎡'),(460,'修正後㎡'),(665,'元 ガラス長m'),(880,'修正後m')]:txt(x,106,t,11)
 y=142
 for q in glass['stores'][start:start+22]:
  txt(35,y,q['id'],10)
  for x,k in [(250,'baseline_actual_stock_glass_overlap_m2'),(460,'revised_actual_stock_glass_overlap_m2'),(665,'baseline_stock_facing_glazing_m'),(880,'remaining_stock_facing_glazing_m')]:txt(x,y,f'{q[k]:.5f}',10)
  y+=28

new('3階のまぶしさ：光源・床材の調整','カメラ27：同じ位置・角度・FOV75°、1280×720、MSAA4x。露出0.90・FILMICは維持。')
wrap(32,107,775,'太陽光0.65→0.12、色を暖色から中立寄りへ。直射の影響を弱め、環境光0.78→0.70で日陰の明るさを維持。補助光0.08と露出0.90は固定。\n床：粗さの下限0.58、スペキュラ0.26、目地0.76。床全体の色を暗くして対処したわけではありません。\n原因：この簡易描画ではトップライトのガラスが実物と同じ日射減衰をしません。光源・環境光による近似であり、物理日照シミュレーションや拡散GIではありません。\n画面評価：白く飽和して消えていた床の目地・石目は見えるようになりました。ただしテクスチャの繰返し、長い無表情な壁、店舗の密度と照明の作り込みは残ります。',12,27)
new('3階 / 同一視点のGodot比較','左：保護v2。右：最終独立v3。明るさの数値と見た目を分けて確認。',True)
image(E/'before-v2/27-3F-daylight-corridor.png',fitz.Rect(30,112,579,421));image(E/'after/27-3F-daylight-corridor.png',fitz.Rect(612,112,1161,421));wrap(35,485,1120,'床・壁の白飛びを抑えました。照度・輝度計による測定や、人間のまぶしさの主観評価は未実施。FF15級の品質達成とは評価していません。',13,27)
new('階ごとの画面明度の比較','画像のsRGB値を比較。物理輝度nit・照度lux・快適性の合格基準ではありません。',True)
y=115
for q in light['comparisons']:
 txt(35,y,q['id'],13);y+=27
 for key,label in [('before','v2'),('after','v3')]:
  z=q[key];txt(45,y,label+f" / 平均Y {z['mean_srgb_luma']:.3f} / 中央値 {z['median_srgb_luma']:.3f} / 95%点 {z['p95_srgb_luma']:.3f} / 全RGB>.98 {z['near_white_percent']:.2f}%",12);y+=29
 y+=15
wrap(35,669,1120,'同一の構図・同一領域で比較。HUD周辺は除外。店舗内装の変更も一部の画素差へ影響するため、照明単独の実験値とは呼びません。',11,24)
new('追加項目：検査区分と残課題','図面・自動物理・実画面・人間操作の結果を混在させません。')
wrap(32,106,775,'図面：EV既存位置・候補2機の5階重複、31地点の距離、積層エスカレーターの床開口・乗降支持、191区画の面積。B1/RF接続・構造・車両交錯・運用は未検証。\n自動物理：既存配置での乗継約50.45m、全1273検査。新設EV・移設エスカレーターは未施工のため対象外。\n実画面：通常20視点と検査切断3視点、書店v1/v2/v3比較、在庫2地点、3階のまぶしさ。検査表示は通常品質画像と別扱い。\n人間の実操作：今回の制作環境でのプレイヤー操作、Windows/RTX4060での確認は未実施。\n残課題：全館の未割当床、在庫56店舗、翼のEV距離、B2-070の閉じた前面、材料の繰返し・商品密度・大型店の実装。',11,26)
wrap(32,449,775,'原図・ゲーム本体は保持。設備変更・店舗統合・全館の区画再設計は承認前に適用していません。',12,24,(.63,.24,.17))
# Keep the full issue register after the latest comprehensive review, with accurate page numbers.
split=next(i for i in range(base_page_count)if '全件座標一覧' in doc[i].get_text().splitlines()[0] and '種別' in doc[i].get_text().splitlines()[0])
doc.select(list(range(split))+list(range(base_page_count,len(doc)))+list(range(split,base_page_count)))
for i,pg in enumerate(doc):pg.insert_text((pg.rect.width-58,pg.rect.height-17),str(i+1),fontname='JP',fontfile=str(P/'assets/NotoSansCJKjp-Regular.otf'),fontsize=8,color=(.39,.43,.40))
pg=doc[1];pg.insert_text((32,506),f'昇降設備・在庫・ガラス・照明の追加検討：p.{split+1}〜110。全516件の座標一覧：p.111以降。',fontname='JP',fontfile=str(P/'assets/NotoSansCJKjp-Regular.otf'),fontsize=11,color=(.13,.32,.28))
toc=[]
for i,pg in enumerate(doc):
 title=pg.get_text().splitlines()[0]
 if any(t in title for t in ['根本原因','全5層','局所案','総合改善指示','エレベーター：','エレベーター歩','エスカレーター：','バックヤード：','店舗規模：','在庫のガラス張り：','3階のまぶしさ：','追加項目：','全件座標一覧：']):toc.append([1,title,i+1])
doc.set_toc(toc)
tmp=O.with_suffix('.tmp.pdf');doc.save(tmp,garbage=4,deflate=True);tmp.replace(O)
# Update complete document receipt and publish all new analysis sources.
f=fitz.open(O);bad=[]
for i,pg in enumerate(f):
 pg.get_pixmap(matrix=fitz.Matrix(.15,.15),alpha=False)
 for b in pg.get_text('dict')['blocks']:
  if b['type']!=0:continue
  for l in b['lines']:
   for sp in l['spans']:
    r=fitz.Rect(sp['bbox'])
    if r.x0<-.5 or r.y0<-.5 or r.x1>pg.rect.width+.5 or r.y1>pg.rect.height+.5:bad.append({'page':i+1,'text':sp['text'],'bbox':sp['bbox']})
r={'pages':len(f),'all_pages_rendered':True,'text_outside_pages':bad,'sha256':hashlib.sha256(O.read_bytes()).hexdigest(),'production_design_complete':False,'date_jst':'2026-10-27'};(E/'pdf-verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
for folder in ['vertical-review','backroom-review']:shutil.copytree(S/folder,D/folder,dirs_exist_ok=True)
for p in(P/'authoring').glob('*'):
 if p.is_file():shutil.copy2(p,D/'authoring'/p.name)
for p in E.glob('*.json'):shutil.copy2(p,D/'evidence'/p.name)
for n in ['stock-role-corrections.json','baseline-stock-privacy.json','asset-license-ledger.csv']:
 if(S/n).exists():shutil.copy2(S/n,D/n)
print('COMPREHENSIVE_PDF',len(f),O.stat().st_size,'overflow',len(bad),flush=True)
assert not bad,bad
