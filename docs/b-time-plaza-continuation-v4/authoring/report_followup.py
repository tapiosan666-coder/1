"""Single combined progress report: frozen v3 results + concrete v4 continuation + explicit remaining work."""
from pathlib import Path
import sys,json,csv,hashlib,shutil,statistics,datetime,collections
from io import BytesIO
from functools import lru_cache
sys.path.insert(0,'/workspace/1/tools');from site_v2_common import *
import fitz
from PIL import Image
P=Path(__file__).resolve().parents[1];V3=Path('/workspace/FIND_YOURSELF-B-Time-Plaza-v3');S=P/'source';O=S/'followup';E=P/'evidence';DOC=R/'docs/b-time-plaza-continuation-v4';DOC.mkdir(exist_ok=True);OUT=R/'downloads/FIND_YOURSELF-B-Continuation-v4.pdf'
summary=read(O/'summary.json');studies=read(O/'backroom-layout-proposals.json');requests=read(O/'request-register.json');coord=list(csv.DictReader(open(O/'coordinate-corrections.csv',encoding='utf-8-sig')));routes=list(csv.DictReader(open(O/'corrected-warehouse-routes.csv',encoding='utf-8-sig')));data=read(O/'coordinate-role-source.json');manifest=read(S/'scene-manifest.json');walk=read(E/'walk-results.json');roomtest=read(E/'service-room-walk.json');ind=read(E/'followup-independent-checks.json');perf=read(E/'profile-results.json');glass=read(E/'stock-glass-results.json');ledger=list(csv.DictReader(open(O/'all-191-current-area-ledger.csv',encoding='utf-8-sig')));byid={s['id']:s for f in read(S/'design-extract.json')['floors']for s in f['stores']};root=read(S/'root-gap-review/full-B-root-audit.json');vp=read(S/'vertical-review/vertical-review.json')
doc=fitz.open();W,H=1191,842;fontfile=str(P/'assets/NotoSansCJKjp-Regular.otf');font=fitz.Font(fontfile=fontfile);page=None;green=(.13,.32,.28);dark=(.15,.18,.17);grey=(.40,.44,.41);red=(.64,.23,.17);toc=[]
def text(x,y,s,size=13,col=dark):page.insert_text((x,y),str(s),fontname='JP',fontfile=fontfile,fontsize=size,color=col)
def wrap(x,y,width,s,size=13,lead=27,col=dark):
 for para in str(s).split('\n'):
  line=''
  for c in para:
   if line and font.text_length(line+c,fontsize=size)>width:text(x,y,line,size,col);y+=lead;line=c
   else:line+=c
  if line:text(x,y,line,size,col)
  y+=lead
 return y
def new(title,subtitle='',bookmark=False):
 global page
 page=doc.new_page(width=W,height=H);page.draw_rect(fitz.Rect(0,0,W,7),fill=green,color=None);text(32,43,title,22,green);wrap(32,70,W-64,subtitle,10,17,grey);text(32,H-19,'FIND YOURSELF / B館 継続検証v4 / 2026-10-27 JST / 原図・ゲーム本体へ未統合',9,grey);text(W-63,H-19,str(len(doc)),9,grey)
 if bookmark:toc.append([1,title,len(doc)])
@lru_cache(maxsize=100)
def png(p):
 im=Image.open(p);buf=BytesIO();im.save(buf,format='PNG',icc_profile=None);out=buf.getvalue();assert Image.open(BytesIO(out)).tobytes()==im.tobytes();return out
def image(p,rect):page.insert_image(rect,stream=png(str(p)),keep_proportion=True)
def svg(p,rect):
 raw=fitz.open(stream=Path(p).read_bytes(),filetype='svg');vec=fitz.open(stream=raw.convert_to_pdf(),filetype='pdf');page.show_pdf_page(rect,vec,0)
def rule(y):page.draw_line((32,y),(W-32,y),color=(.8,.84,.8),width=.5)
new('途中の依頼を引き継いだ統合報告 / 独立検証v4','前回の成果・今回の追加・訂正・未施工・未検証をまとめています。建築図面B館v4.1の改訂ではありません。',True)
wrap(35,126,1120,'今回進めたこと：共用倉庫等の入口座標の不整合を発見・補正し、既存の裏方室3か所を独立Godotで通れる室へ復元。バックヤード56区画の検討を続け、過去の依頼46項目を一覧化しました。',17,34)
wrap(35,275,1120,'訂正：前回の「最寄り共用倉庫」は、入口に旧座標が残っていたため選定を再計算しました。新しい191店舗台帳を使用してください。56区画は固定軸・0.30m刻みの検査でした。配置刻みを0.25mへ細かくし、向きも変えると8区画が収まりました。内訳は回転4、刻みの改善4です。',15,31,red)
wrap(35,441,1120,'未完：全館の用途未確定床約2.2万㎡、48区画の在庫作業条件、全店の内装、18大型/核店の3D、15層の統合、人物品質・実機性能。EV増設・エスカレーター移設・店舗統合は未承認案のままです。',15,31)
wrap(35,618,1120,f"自動物理 {walk['passed']}/{walk['total']}、裏方室 {roomtest['passed']}/{roomtest['total']}、独立照合 {ind['passed']}件合格。これを建築の自然さ・搬入運用・人間の実操作の合格に置き換えていません。",14,29)
new('前回と今回の差分','この資料の「完了」は明示した検査・局所実装の範囲だけです。全館の完成を意味しません。',True)
rows=[('共通原因','未割当床・ブーリアン輪郭・内部入口不足','維持。新たに点座標だけ変換漏れという原因を確認'),('用途未確定床','全B館約2.2万㎡が残る','面積は未解消。室名があるだけで運用妥当とはしない'),('裏方室','閉鎖代理ブロック・実際の扉なし','3室を壁/扉/内部経路へ復元。1室は切出し外入口のため保留'),('倉庫選定','旧入口座標で最寄りを選定','9室補正、188店舗の入口間経路を再計算'),('在庫作業56区画','固定軸の矩形に収まらない','向き・配置刻みの見直しで8区画が収まり、48区画を検討継続'),('拡張案','未確定','24案検討。22案は境界悪化で棄却、2案だけ未承認候補'),('EV/エスカレーター','増設2案/乗継短縮案','未施工。承認前に設備を移していない'),('ゲーム本体','0.24.0を保護','一切変更せず。独立検証だけを追加')]
y=119
for a,b,c in rows:
 text(35,y,a,12,green);wrap(235,y,385,b,11,21);wrap(658,y,490,c,11,21);rule(y+58);y+=77
new('維持した前回成果：根本原因と生成規則','全館516件は問題・確認候補であり、確定した不良516件という意味ではありません。',True)
wrap(35,117,1120,'1. 店舗・共用部を包む外郭を先に作り、その余り床へ具体的な用途・入口・設備を割り当てていなかった。\n2. 区画の差演算で残る短辺・鋭角・細い片を、そのまま壁へ変換していた。\n3. 店舗全体の入口だけを検査し、分離した売場/在庫の各片の入口を見落としていた。\n4. 未割当が残っていても、床と一部の閉鎖帯だけで3Dが成立してしまう生成契約だった。',14,31)
wrap(35,323,1120,'前回の6局所案のうち3か所だけが独立3Dに含まれています。今回の裏方室復元は既存用途の輪郭と扉を実装するもので、この6案のほかに店舗境界・主要通路・吹き抜けを変更していません。\n未割当床が残る限り、本番出力は停止。比較用の --review-draft だけを明示して生成します。v1以来の出発床補完142.08㎡は独立モデル内の案として維持し、原図には未反映です。nav_freeは共用床のマスクであり、全off-navが不要・立入禁止という意味ではありません。',14,30)
y=560
for q in root['summaries']:text(40,y,q['floor']+f" / 現行局所案後の未割当 {q['unallocated_after_proposed_small_annex_m2']:,.2f}㎡ / 今回解消面積0㎡",13);y+=34
for group in [('B1','1F','2F'),('3F','RF')]:
 new('全B館の用途帰属 / '+ '・'.join(group),'橙：用途未確定床。青：前回の区画候補。今回も全体の用途未確定は残る。原図は保護。')
 for i,label in enumerate(group):
  yy=105+i*205;text(36,yy+20,label,13,green);svg(S/f'root-gap-review/B-{label}-refined.svg',fitz.Rect(90,yy,1155,yy+190))
new('新たな共通原因：ポリゴンと数値点の座標系が不一致','根拠：元リポジトリ tools/site_v2_common.py の translate_geoms と floor_B_world。原本は変更していません。',True)
wrap(35,118,1120,'ポリゴンは変換されても、通常の数値配列 [x,z] は自動変換されません。B館の店舗入口は個別に補正されていましたが、共用倉庫/管理室の entry と main_route は旧B館ローカル値のままでした。\nその結果、世界座標の室輪郭と入口が数百m離れ、最寄り倉庫の選定に使える点ではありませんでした。今回の独立データでは、固定原図の既知の変換 (-714,-30)m を入口と経路へ適用しています。',14,31)
wrap(35,330,1120,'再発防止：座標系の属性を付け、方向ベクトル・寸法と点を区別する。世界座標の点へ二重変換しない。変換後は自室境界・接続床と照合。不明な座標系は推測して通さず停止する。\n9室すべてで入口の境界誤差は0.01m未満、既存の室内経路は室/共用床の中に収まることを図面で確認しました。室輪郭・既存売場・主要通路は保持。',14,31)
wrap(35,590,1120,'影響訂正：旧v3台帳のnearest_existing_shared_warehouseは使わず、今回のall-191-current-area-ledger.csvを参照してください。元の面積・在庫率はこの座標漏れの影響を受けていません。',14,30,red)
new('9室の入口補正一覧','世界X/Z、単位m。Yは階高。部屋の輪郭とIDは同じで、数値点と内部経路だけを独立データで補正。')
for x,t in [(35,'階 / ID'),(255,'旧X / Z'),(520,'補正後 世界X / Z'),(845,'旧点と室の距離m')]:text(x,119,t,12,green)
y=165
for q in coord:
 if not q['new_distance_to_boundary_m']:continue
 text(35,y,q['floor']+' / '+q['id'],12);text(255,y,f"{float(q['old_x']):.3f} / {float(q['old_z']):.3f}",12);text(520,y,f"{float(q['new_x']):.3f} / {float(q['new_z']):.3f}",12);text(880,y,f"{float(q['old_distance_to_room_m']):.2f}",12);rule(y+19);y+=52
wrap(35,694,1120,'共用倉庫6室と管理・清掃室3室。管理・清掃室は店舗共用倉庫へ転用していません。原図への補正採用は未実施。',12,25)
new('座標メタデータで残る別の注意点','この資料は、原図の全メタデータが修正済みという報告ではありません。')
wrap(35,116,1120,'案内板：1F・2F・3Fに各3件、合計9レコードがあり、3階用の同じID・高さの案内板が他階にも重複しています。点も旧座標です。独立3Dは従来の独自案内表示を使用し、この不正なメタデータをそのまま読ませていません。\n館間経路：1F/2Fに計4本の経路数値が旧座標で残ります。世界座標への変換案を保存しましたが、敷地側の実際の橋・終点との照合前に採用しません。館間の橋を勝手に移していません。',14,31)
wrap(35,390,1120,'今後の設計データでは position_world_xz / direction_xz / level / height_m を明示し、同じ名前の数値配列で混在させない方針です。今回の補正コードは既知の共用室の点だけを対象とし、方向ベクトルや建物ポリゴンを再平行移動しません。',14,31)
new('共用倉庫への図面経路を再計算','188店舗の客用通路側入口→同階の共用倉庫の通路側入口。搬入作業の合格ではありません。',True)
wrap(35,117,1120,'半径0.30m、0.75m格子と明示した入口ノードを用い、線分が通行領域に収まることを確認。失敗点を近くへ動かして合格させていません。管理・清掃室を候補から除外し、正しい共用倉庫だけを対象にしています。',14,31)
y=285
for label in ['1F','2F','3F']:
 rr=[q for q in routes if q['floor']==label and q['public_entry_distance_m']];vals=sorted(float(q['public_entry_distance_m'])for q in rr);text(35,y,label+f' / {len(rr)}店舗 / 中央値 {statistics.median(vals):.1f}m / 最大 {max(vals):.1f}m',14);y+=58
wrap(35,494,1120,'B1の食品/受取2店舗とRFカフェは、同階の共用倉庫を定義していないため未検証。EVは独立シーンで稼働0台なので、垂直搬送ができるとはしていません。\n在庫室→店舗入口の店内搬送、営業時間、台車、在庫量、受入/返却/冷蔵/衛生、共用倉庫の割当余力は未検証。全188経路をGodotで実歩行した結果ではありません。',14,30,red)
for label in ['1F','2F','3F']:
 new(label+' / 共用倉庫と経路例','短距離・中央・長距離の3例。色付き室が共用倉庫、灰色が管理室、赤点が補正後の入口。')
 svg(O/(label+'-warehouse-route-plan.svg'),fitz.Rect(32,128,1159,656));wrap(35,712,1120,'原図の共用通路を維持した図面経路です。バックヤード専用の搬入路を新設した図ではありません。営業時間外の共用通路利用という既存方針の運用可否は別途検証。',12,25)
new('既存の共用室：名前と必要性を区別','既存用途は維持していますが、室名があるという理由だけで面積や運用の妥当性を合格にしていません。')
y=124
for f in data['floors']:
 if f['wing']!='B':continue
 for z in f.get('service_zones',[]):text(35,y,f['label']+' / '+z['id']+' / '+z['name']+f" / {z['polygon'].area:.1f}㎡",13);y+=43
wrap(35,577,1120,'管理・清掃室には1,000㎡級の区画もあります。必要な部門・作業内容・設備量がまだ裏付けられていないため、仮棚を置くだけで妥当な商業施設になったとは判断しません。\n現在は元の用途と区画を保護し、次の街区設計で管理機能・倉庫・設備・外郭縮減を比較する課題として残します。',14,30,red)
new('バックヤード56区画の継続検討','前回の「56」は固定軸の暫定作業矩形に収まらなかった件数で、56店舗が必ず使用不能という意味ではありません。',True)
wrap(35,122,1120,'同じ面積で収まる8区画：回転4、配置刻み改善4。境界や売場は変更しない。\n拡張を検討した24区画：必要面積・矩形が収まる案を作ったが、22案は角数/壁長を悪化させるため棄却。2案だけを未承認候補として保存。\nその他24区画：局所拡張案を成立させず、共用倉庫・納品方式・街区再設計の比較対象。\n今回の探索で未解消なのは48区画。配置不能の厳密な証明ではない。未承認の2案を施工済みとして46へ減らしていません。',15,33)
wrap(35,361,1120,'面積条件：飲食/食品3.6×2.1m＋12㎡、衣料/靴3.6×2.1m＋10㎡、書籍3.2×1.9m＋9㎡、その他3.2×2.1m＋9㎡を一次条件としています。これはゲーム用の計画仮定で、業界平均・法規・在庫容量の合格基準ではありません。',13,28)
wrap(35,539,1120,'既存の全売場面積を維持。店舗の統合・分割・拡張、在庫の新しい割当はGodotへ適用していません。図面上の作業矩形の確認と、実際の在庫室で人が働けることを区別しています。',14,30,red)
new('残した拡張候補2案 / 未承認','面積・入口の接続・角数と壁長の暫定ガードを通過。構造・防火・搬入・見た目は未承認。')
y=124
for q in studies:
 if q['status']!='ANNEX_CANDIDATE_NEEDS_APPROVAL':continue
 text(35,y,q['id']+f" / 拡張候補{q['annex_candidate_m2']:.2f}㎡ / 角数差{q['plot_vertices_delta']:+d} / 壁長差{q['plot_perimeter_delta_m']:+.2f}m",14,green);svg(O/(q['id']+'-stock-proposal.svg'),fitz.Rect(35,y+24,550,y+242));wrap(610,y+60,530,'既存入口・スタッフ扉・売場を維持する案。青が作業矩形、橙が拡張候補。在庫への1.2m以上の接続を確保する平面検討。未施工。',13,28);y+=290
status_names={'EXISTING_ROOM_LAYOUT_FITS':'同じ面積・配置見直しで収まる（図面）','ANNEX_CANDIDATE_NEEDS_APPROVAL':'拡張候補・未承認','ANNEX_REJECTED_BOUNDARY_COMPLEXITY':'拡張は境界悪化で棄却','SHARED_WAREHOUSE_OR_BLOCK_REDESIGN_REQUIRED':'共用倉庫/街区再設計を比較','CONFLICT_REQUIRES_JOINT_BLOCK_DESIGN':'競合・共同設計が必要'}
for start in range(0,len(studies),4):
 new(f'56区画の具体的検討 {start+1}〜{min(start+4,len(studies))}','緑：現状在庫、灰白：現状売場、青：作業矩形、橙：候補/棄却した拡張。赤点：客用入口、青点：スタッフ扉。')
 for j,q in enumerate(studies[start:start+4]):
  x=35+(j%2)*575;y=115+(j//2)*327;s=byid[q['id']];text(x,y,q['id']+' / '+q['category'],13,green);svg(O/(q['id']+'-stock-proposal.svg'),fitz.Rect(x,y+20,x+315,y+230));wrap(x+325,y+45,230,status_names[q['status']],11,22);wrap(x+325,y+112,230,f"在庫{q['stock_m2']:.1f}㎡\n追加案{q['annex_candidate_m2']:.2f}㎡\n間口{s.get('frontage_m',0):.1f}m\n台帳奥行{s.get('depth_m',0):.1f}m",10,21);wrap(x,y+259,540,'売場縮小0㎡。作業矩形の条件だけで営業可能とは判定しない。',10,21)
new('独立3Dで進めた裏方室3か所','S-1-T：管理・清掃、S-2-L：共用倉庫、S-3-T：管理・清掃。用途・輪郭・既存扉位置を維持。',True)
wrap(35,121,1120,'前回：室全体を閉じた代理ブロックとして出力。扉・内部・搬入路は未施工。\n今回：元の室外周から不透明壁を作り、正しい入口へ1.5m扉・上部壁・表示を配置。室内には既存経路幅1.6mの予約帯を取り、その外へ仮棚を10台ずつ配置しました。配布前に棚板・支柱の衝突不足を発見し、生成側で修正。棚の3件は正しい金属衝突レイヤーへの物理レイ検査です。\nS-2-Tは室の一部だけが範囲に入り、元の入口が切出し外にあるため閉鎖代理形状を維持。勝手に別入口を作りません。',15,32)
wrap(35,378,1120,'裏方室の扉は通常閉で「関係者以外立入禁止」と用途を表示。Fで開くのは検証操作です。スタッフ認証やNPCの搬入AIを追加したわけではありません。\n室輪郭の複雑さ・大きさの妥当性、設備や机・倉庫の容量、照明・床材の仕上げはまだ改善が必要です。共用通路や広場の代わりに裏方室を使わせる構成にはしていません。',14,31)
new('実Godotの検査結果と範囲','図面検査・自動物理・実画面・人間の実操作を分離。')
wrap(35,118,1120,f"既存経路と接合：{walk['passed']}/{walk['total']}合格。\n裏方室の閉鎖扉・通過幅・室内経路・外周壁：{roomtest['passed']}/{roomtest['total']}合格。\n原本保護・三角形と静的衝突・座標変換・店舗境界等：{ind['passed']}件合格。\n在庫のガラス監査：80店、元の問題5店、現モデルの残存0。\n図面の倉庫経路：188店舗分。実際のGodotで188店舗から台車搬送した検査ではありません。",15,34)
wrap(35,435,1120,'人間による実操作、Windows/RTX4060実機、構造・防火・衛生・搬入運用・在庫容量は未検証です。接合や通行が合格しても、建築の自然さや美術品質の合格とはしません。',15,32,red)
for room in ['S-1-T','S-2-L','S-3-T']:
 for state in ['closed','open']:
  name=room+'-'+state;new(room+' / 扉'+('閉鎖'if state=='closed'else'開放')+'の実画面比較','左：保護したv3。右：独立v4。同じ位置・角度・FOV75°・1280×720・MSAA4x。')
  image(E/'before-v3'/(name+'.png'),fitz.Rect(32,132,579,440));image(E/'after'/(name+'.png'),fitz.Rect(612,132,1159,440));wrap(35,501,1120,'v3では代理ブロックに扉がありません。v4は元の室と入口を復元した比較です。壁を追加して用途不明の隙間を隠したものではありません。部屋の必要面積・設備・仕上げは別の残課題です。',14,29)
for room in ['S-1-T','S-2-L','S-3-T']:
 new(room+' / 室内のGodot実画面','今回初めて通れる状態になった室内。beforeには室内が存在しないため、同一視点の改善前比較として扱いません。')
 image(E/'after'/(room+'-interior.png'),fitz.Rect(65,113,1126,710));wrap(35,758,1120,'仮棚と通路の検証段階。天井・設備・床材・荷受け運用まで完成した倉庫/管理室ではありません。',11,23)
for name,title in [('08-1F-bookshop-interior','書店の前回改修を維持'),('17-cafe-service-and-seating','カフェの前回改修を維持')]:
 new(title,'左：v3、右：v4。今回、代表店舗の区画や什器を変更していません。全店の内装完成ではありません。')
 image(V3/'evidence/after'/(name+'.png'),fitz.Rect(32,132,579,440));image(E/'after'/(name+'.png'),fitz.Rect(612,132,1159,440));wrap(35,510,1120,'書店B1-017・カフェB1-040・衣料B1-043の代表店改修は保持。壁面陳列、レジ、設備、席等を追加した前回成果です。全店の外観・店種ごとの密度・商品造形・照明は引き続き未完成です。',14,30)
new('3階の白飛び低減を維持','左：調整前v2。右：今回v4。同じカメラ。v4ではv3の太陽・環境光・露出・床材設定を変更していません。')
image(V3/'evidence/before-v2/27-3F-daylight-corridor.png',fitz.Rect(32,132,579,440));image(E/'after/27-3F-daylight-corridor.png',fitz.Rect(612,132,1159,440));wrap(35,510,1120,'太陽0.65→0.12、環境光0.78→0.70、露出0.90/FILMIC、床粗さ下限0.58/スペキュラ0.26。床の目地や石目が白く消える状態を抑えています。照度や主観的まぶしさの測定は未実施です。',14,30)
new('昇降設備・大型店・店舗統合の保留を引き継ぐ','承認前に配置や区画を変えないという条件を維持。今回の「進めて」を設計案の一括承認とは扱っていません。',True)
wrap(35,119,1120,'EV：原図3昇降路/15停止階、現在の独立シーンで稼働0台。K4中央西・K5東の2案は未承認。翼からの距離約162〜165m、B1/RFの既存用途再配分・接続・構造/機械が未解決。\nエスカレーター：2→3階を下段直上へ積層する案は図面50.89→20.06m。現位置は維持し、移設後の実歩行は未検証。\n大型/核店：12＋6区画の用途別平面を維持。今の3D切出し外で、映画館・食品・家電・フードホールの3Dは未施工。\n中央専門店街：2つの統合案は未適用。店舗ID・入口・売場はそのまま。',14,32)
wrap(35,525,1120,'前回の詳細135ページには、これらの断面・位置・台帳・全516候補を収録。今回の統合報告は、それを置き換えて完成扱いにするのではなく、新しい訂正・検証結果を重ねたものです。',14,30)
for filename,title in [('TIME-transfer-proposal-detail.svg','引継ぎ / 時の広場の乗継改善案'),('lift-five-level-section-proposal.svg','引継ぎ / EV増設の5層断面案')]:
 new(title,'前回と同じ未承認案。Godotの昇降設備は移動・増設していません。');svg(S/'vertical-review'/filename,fitz.Rect(32,123,1159,748))
for start in range(0,len(requests),8):
 new(f'過去依頼の進捗台帳 {start+1}〜{min(start+8,len(requests))} / 46','旧本体の実装記録と、今回の独立シーンで検査したものを区別しています。',bookmark=start==0)
 y=119
 for q in requests[start:start+8]:
  text(35,y,q['id']+' / '+q['request'],13,green);text(620,y,q['status'],12);wrap(35,y+25,1115,q['detail'],11,22);rule(y+58);y+=82
new('性能・素材・今回残る品質課題','性能測定は自動歩行検査とは別実行。実際のプレイヤー目線の画像も完成品質とは評価していません。',True)
wrap(35,119,1120,f"Godot4.6.3 / GL Compatibility / 1280×720 / MSAA4x / NPC0。\n{perf['adapter']}。CPUソフトウェア描画の参考：静止{perf['performance'][0]['fps_from_mean_frame_time']:.3f}FPS、移動{perf['walking_performance']['fps_from_mean_frame_time']:.3f}FPS。各20フレームの短い測定。RTX4060や1000/5000NPCへ換算しません。\n建築・商品・看板・仮棚はオリジナル。Noto Sans CJK JPはSIL OFL1.1、GodotはMIT。外部のゲーム素材や写真は使っていません。\nAOは12レイの接触陰影であり、拡散GIではありません。エスカレーターの接触は連続勾配面で近似。",14,32)
wrap(35,455,1120,'残課題：全館の用途未確定床、48在庫区画、管理室の面積根拠、長い閉鎖壁、商品密度・材料反復・実物らしい建具、全店・18大型店・15層の実装。FF15級の表現やSteam販売品質には未到達です。',15,32,red)
new('次に進める順序と承認が必要な部分','「途中」を隠さず、同じ台帳を引き継ぐ方針です。')
wrap(35,118,1120,'1. 街区ごとに未割当床・管理/倉庫の必要量・店舗奥行き・外郭縮減を比較する。名前を付けるだけで余り床を解決扱いにしない。\n2. 在庫48区画は、回転案・候補2案・共用倉庫利用と店内搬送の条件を決める。売場を減らす必要があれば変更案として提示する。\n3. EV/エスカレーター案と大型店/統合案は、承認された案から独立モデルへ施工。承認前には原図・本体を変更しない。\n4. 美術は用途ごとの内装・入口・照明・商品を仕上げ、同じ視点と実歩行で自然さを評価する。\n5. 建築の承認後、旧本体のNPC・猫・宝箱・ファストトラベル・セーブと接続し、実機の性能・長時間・終盤探索を再検証する。',14,33)
wrap(35,566,1120,'今回も本体への統合は行っていません。図面・自動物理・実画面・人間の操作を別の結果として保持し、検査件数だけで完成扱いにしません。',15,32,red)
doc.set_toc(toc);doc.save(OUT,garbage=4,deflate=True)
f=fitz.open(OUT);bad=[]
for i,pg in enumerate(f):
 pg.get_pixmap(matrix=fitz.Matrix(.15,.15),alpha=False)
 for b in pg.get_text('dict')['blocks']:
  if b['type']!=0:continue
  for l in b['lines']:
   for sp in l['spans']:
    rr=fitz.Rect(sp['bbox'])
    if rr.x0<-.5 or rr.y0<-.5 or rr.x1>W+.5 or rr.y1>H+.5:bad.append({'page':i+1,'text':sp['text'],'bbox':sp['bbox']})
receipt={'pages':len(f),'all_pages_rendered':True,'text_outside_pages':bad,'warnings':fitz.TOOLS.mupdf_warnings(),'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'main_game_modified':False,'architecture_complete':False};(E/'pdf-verification.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2));print('PDF_V4',len(f),OUT.stat().st_size,'overflow',len(bad),flush=True);assert not bad,bad
for folder in ['authoring','runtime-source','evidence','after','before-v3']:(DOC/folder).mkdir(exist_ok=True)
shutil.copytree(O,DOC/'followup',dirs_exist_ok=True)
for p in(P/'authoring').glob('*'):
 if p.is_file():shutil.copy2(p,DOC/'authoring'/p.name)
for p in P.iterdir():
 if p.is_file()and(p.suffix in ['.gd','.gdshader','.tscn']or p.name=='project.godot'):shutil.copy2(p,DOC/'runtime-source'/p.name)
for p in E.glob('*.json'):shutil.copy2(p,DOC/'evidence'/p.name)
for name in ['after','before-v3']:
 for p in(E/name).glob('*'):
  if p.is_file():shutil.copy2(p,DOC/name/p.name)
shutil.copy2(P/'README.md',DOC/'README.md')
