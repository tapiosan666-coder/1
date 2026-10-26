"""Package the design review only; fail rather than advertise incomplete checks as passed."""
from pathlib import Path
import sys,json,csv,collections,hashlib,zipfile,subprocess
sys.path.append('/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
import fitz,shapely
from shapely.geometry import shape
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/b-detailed-review-v3';D=ROOT/'downloads';data=json.loads((OUT/'geometry.json').read_text());checks=json.loads((OUT/'checks.json').read_text());failed=[x for x in checks if not x['pass_']]
assert not failed,failed
baseline=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
protected=['scripts','scenes','assets','project.godot','export_presets.cfg']
assert not subprocess.check_output(['git','diff','--name-only','HEAD','--',*protected],cwd=ROOT,text=True).strip()
tracked=subprocess.check_output(['git','ls-files','--',*protected],cwd=ROOT,text=True).splitlines()
filehashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in tracked if (ROOT/p).is_file()}
(OUT/'game-file-hashes.json').write_text(json.dumps(filehashes,indent=2))
summary=collections.Counter(x['kind']for x in checks)
with (OUT/'check-summary.csv').open('w',encoding='utf-8-sig',newline='')as fp:
 w=csv.writer(fp);w.writerow(['検査種別','件数','不合格']);w.writerows((k,n,0)for k,n in sorted(summary.items()))
# Comprehensive entity coordinate list, including polygons for doors and equipment.
with (OUT/'entity-coordinates.csv').open('w',encoding='utf-8-sig',newline='')as fp:
 w=csv.writer(fp);w.writerow(['階','分類','ID','localX','localZ','worldX','worldY','worldZ','寸法・補足'])
 for f in data['floors']:
  level=f['floor'];height=f['height']
  for s in f['stores']:
   x,z=s['entry'];w.writerow([level,'店舗入口',s['id'],x,z,x-714,height,z-30,f"開口{s['door_width_m']}m; 旧ID={s.get('legacy_id','新設')}"])
  for c in data['cores']:
   for d in c['doors']:
    x,z=d['p'];w.writerow([level,'設備扉',c['id']+'/'+d['id'],x,z,x-714,height,z-30,f"開口{d['w']}m"])
  for e in data['escalators']:
   if level not in e['levels']:continue
   x,z=e['c'];w.writerow([level,'エスカレーター中心',e['id'],x,z,x-714,height,z-30,'12/23の各接続先はgeometry.jsonに明記'])
# Rewrite final tenant ledger AFTER legacy identity coordination, not from the preliminary selection.
with (OUT/'tenant-ledger.csv').open('w',encoding='utf-8-sig',newline='')as fp:
 w=csv.writer(fp);w.writerow(['新ID','旧ID別名','階','種別','基本業種','維持する店舗名','旧内装業種','区画m2','間口m','最大奥行m','入口幅m','入口localX','入口localZ','入口worldX','入口worldY','入口worldZ','バックルームm2','搬入方式','主路座標JSON'])
 for f in data['floors']:
  for s in f['stores']:
   x,z=s['entry'];w.writerow([s['id'],s.get('legacy_id',''),f['floor'],s['kind'],s['category'],s.get('legacy_name',''),s.get('legacy_kind',''),round(shape(s['polygon']).area,2),round(s['frontage_m'],2),round(s['depth_m'],2),s['door_width_m'],x,z,x-714,f['height'],z-30,round(shape(s['backroom']).area,2),s['service_mode'],json.dumps(s['main_route'])])
# Dimension/area accounting explicitly exposes reserved service space.
areas=[]
for f in data['floors']:
 p=shape(f['shell']);areas.append(dict(floor=f['floor'],height=f['height'],body_bounds_local=list(p.bounds),body_bounds_world=[p.bounds[0]-714,p.bounds[1]-30,p.bounds[2]-714,p.bounds[3]-30],body_width=p.bounds[2]-p.bounds[0],body_depth=p.bounds[3]-p.bounds[1],body_area_m2=p.area,tenants=len(f['stores']),regular=sum(s['kind']=='tenant'for s in f['stores']),anchors=sum(s['kind']=='anchor'for s in f['stores']),tenant_area_m2=sum(shape(s['polygon']).area for s in f['stores']),public_area_in_body_m2=shape(f['public']).intersection(p).area,service_reserved_m2=shape(f['residual']).area,service_reserved_percent=shape(f['residual']).area/p.area*100))
(OUT/'dimensions.json').write_text(json.dumps(areas,ensure_ascii=False,indent=2))
pdf=D/'FIND_YOURSELF-B-Detailed-Review-v3.pdf';doc=fitz.open(pdf)
assert len(doc)==34 and len(doc.get_toc())==34
texts=[]
for i,page in enumerate(doc):
 page.get_pixmap(matrix=fitz.Matrix(.25,.25));texts.append(page.get_text())
for n,i in [(1,1),(2,5),(3,9)]:
 doc[i].get_pixmap(matrix=fitz.Matrix(1,1)).save(OUT/f'B-{n}F-preview.png')
for f in data['floors']:
 for s in f['stores']:assert s['id']in '\n'.join(texts),s['id']
assert '未実施'in '\n'.join(texts)
assert not fitz.TOOLS.mupdf_warnings(),fitz.TOOLS.mupdf_warnings()
previewpages=[0,2,13,16,19,20]
for i in previewpages:doc[i].get_pixmap(matrix=fitz.Matrix(.75,.75)).save(f'/tmp/b-final-review-{i}.png')
doc.close()
status=dict(design_only=True,not_implemented=True,source_commit=baseline,game_tracked_files_unchanged=True,game_tracked_hash_count=len(filehashes),geometric_assertions=len(checks),geometric_failures=0,gameplay_movement_tests=0,pdf_pages=34,pdf_all_pages_rendered=True,pdf_all_tenant_ids_present=True,python=sys.version.split()[0],shapely=shapely.__version__,pymupdf=fitz.VersionBind,shop_counts=[len(f['stores'])for f in data['floors']],known_limits=['No new Godot walking test','No 3D headroom or collision test','No NPC/chest/sonar/travel integration test','Service delivery through shared public aisles outside opening hours','Structural, fire and legal accessibility compliance not evaluated','Reserved service areas not fitted out','B1/RF not designed in this issue'])
(OUT/'verification.json').write_text(json.dumps(status,ensure_ascii=False,indent=2))
report=f'''# B館1F～3F 詳細図面レビュー改訂3

2026-10-26。**ゲーム本体はv0.24のまま。これは図面の改訂であり、ゲーム改修完了の報告ではありません。**

## 提出物
- `FIND_YOURSELF-B-Detailed-Review-v3.pdf`：34ページ、ベクトル図と日本語テキスト。拡大可能。
- 各階全体図＋3分割拡大図：売場境界、入口開口、店内主路、棚を置く帯、バックルーム、外形、共用域。
- 吹き抜け3か所の全階対照図と上下エスカレーター断面、設備核3か所の詳細、階段断面・EV上下階対応。
- A/C既存床と新B館の配置、連絡通路、旧→新対応表、全店台帳。
- CSV/JSONは図面と同じ数値。`input/`は受領データの保存用で、改訂版と混同しないこと。

## 独立検査で見つかった問題と修正
1. B1-068の旧入口は自店舗から2.13m外。区画の残る正面辺を選び直し、入口幅2.4mを図示した。
2. 上階のpublic_walkwayは吹き抜け3409㎡をそのまま包含。図の黄色部分と歩行データが一致していなかった。新データは開口を歩行域から除外。
3. public_walkwayが設備核内部にも侵入。新データでは設備室/共用域/出入口を区別した。
4. 3広場から得た旧アフィン変換は主倍率約1.096/0.229。強いせん断・非一様縮尺となるので不採用。全体を平行移動し、寸法を保つ。
5. 添付は核店舗をPDFに描いているがtenant_lotsに含めない。通常198＋大型6＝計画204区画として分けて台帳化。
6. 38個の既存カタログIDと3F映画館を別扱い。映画館には既存カタログIDがないため捏造せずコード上の空間として対応した。
7. 店内奥へのルートと小さな接続を検査。奥の細い突出を除き、内側0.6mの可視グラフで経路を作成。半径0.45mの通路検査も行った。
8. 男性用トイレのスクリーンと洗面台の位置が狭窄を作ったため、洗面台を反対側へ移し、共用部分の連結性を再確認した。

## 現状v0.24との比較・参考資料との関係
現行B本体508×144.5m、主軸16m、南北回廊14m、各階13の売場機能。現行カタログ上は1F13/2F13/3F12で、映画館が別生成のため機能数とID数が一致しない。
新案は楕円状の外周回廊を廃止。屈曲主軸16m、枝道9m、設備アクセス8m、局所回遊と小/中/大型の区画を用いる。全館を回る同心リングや均等格子は採用していない。

公式ガイドPDF（受領済み8ページ）のmori 1F/2F/3F（PDF4/5/6ページ）を高解像度で再度目視した。1Fの家電核と食品核、長い専門店街、2Fの大型区画と小店列の混在、3Fの娯楽/飲食のまとまりを参考にしている。原寸の寸法/柱割りを測った図ではなく、外壁形状やテナント名を写した計画でもない。
公式PDF SHA256：`2a50e320b180fe1fffc391d175deaa013f6bb50ee53b60fb7135530b8bfb7eac`。別の参考URL430/pdf.pdfは未確認で、本レビューの根拠にはしない。旧FIND_YOURSELF_MAP_LAYOUT.svgは参照していない。

## 寸法と区画数（ゲーム用m）
'''
for a in areas:
 report+=f"- {a['floor']}F：床高+{a['height']:.3f}、本体外接 {a['body_width']:.1f}×{a['body_depth']:.1f}、通常{a['regular']}＋大型{a['anchors']}。区画面積合計{a['tenant_area_m2']:.0f}㎡。設備/外壁サービス予約{a['service_reserved_m2']:.0f}㎡（本体の{a['service_reserved_percent']:.1f}%）。\n"
report+='''
外接寸法は通路の有効幅や建物の実床面積とは異なる。専用の連絡橋は本体の外に延びる。設備・サービス予約帯は公開探索空間ではなく、NPC・宝箱の配置候補から除外する。予約部分の機器・倉庫の細分内装は未設計。

## 設備・搬入方式
男女別WC＋4×4mの多目的WC、前室、側壁洗面、女性2個室、男性2個室＋小便器2。共用前室と扉開口、内部スクリーンを描いた。個室扉は1.0mを計画。多目的WCの回転余地は直径1.5mを検査。便器や手すりの完成3Dモデルは含まない。
階段は32蹴上げ、16＋16折返し、踏面0.30m、有効幅2.0m、踊場1.8m。EVシャフト4×4mと開口1.4m、アクセス2m。上下階で設備核のXZを合わせる。
エスカレーターは傾斜走行11.8m、水平部各1.5m、乗降床各3m、外幅2.4m、段の有効幅1m。床高から断面角を算出する。主開口と乗降床の計画は上下階で一致。手すり高1.2m、開口を跨いで塞がないことを施工指示とする。

**搬入は全店専用の裏回廊ではない。** 各店に専用バックルームと店内主路からのアクセスを計画。売場主路と共用廊下を営業時間外に共用する。バックルーム専用扉の位置はgeometry.json、主路はJSON/CSVに記録。搬入NPCを営業中の人混みへ常時流す仕様ではない。

## 座標とID
World X=Local X−714 / World Z=Local Z−30。縮尺1、回転0。高さは現行0/5.525/10.875mを維持する案。
A/B1F端(−174,−5.5)、A/B2F端(−110,−5.5)、B/C1F端(−370,−80)、B/C2F端(−432,−117)を維持。3Fには橋を追加していない。
旧→新店舗は業種を優先して一意に割当。旧IDを新IDの別名にして既存の用途/表示名を維持する。旧座標は区画重心、新座標は入口と明記し、同じ意味の点として扱わない。旧大判の棚配置を小さい新区画に縮尺変形して押し込まず、内装を再配置する。
将来改修時の移行：ID別名表→訪問先座標→店舗別NPCスロット/店内経路→宝箱候補→案内図/移動先。移行は未実行。

## 検査の意味と未検証事項
'''
report+=f"幾何アサーション{len(checks):,}件、失敗0。うち区画相互の非重複は{summary['shop_pair_no_overlap']:,}件であり、実歩行テスト件数ではない。全204店舗の入口への平面上の接近、店内経路、壁開口と棚の分離を検査。\n"
report+='''
共用歩行域を0.45m内側へ縮小した連結成分と入口の距離を使用。店舗入口はその成分から0.72m以内、乗降床中心と館間端点は成分上にあることを確認する。店内の入口から0.8m以降は経路を半径0.45mで膨張し区画内に収まることを確認した。扉開閉による障害物、天井、ガラス、階段/斜面/EV駆動を含む物理検査ではない。
**新案のゲーム内実歩行0回。Godotを使った動作確認は今回未実施。** 旧v0.24の1450検査を新案の試験結果として流用しない。

未検証：梁下/頭上余裕、吹き抜け沿いの柱と見通し、壁・床の3D接合、全個室のプレイヤー衝突、EV稼働、ファストトラベル着地、NPC/猫の経路、宝箱、スキャン/ソナーの階判定、負荷/5000人、滞在時間。実建築の避難/消防/法定バリアフリー適合も保証しない。
今回の図面範囲はB1～3階であり、B地下/屋上の詳細図、全15フロアの完成を意味しない。構造設計・配管・設備予約帯の内装細分も未施工/未確定。

## 承認後の施工手順（今回は実行しない）
1. 既存世界・訪問済みID・実行中の状態を保つ設計データ/ID別名層を用意。進行セーブは現行未実装で、今回実装したとは扱わない。当選抽選やスキルは変更しない。
2. B1Fの床/外壁と連絡路を実装。A/C側の手すり・ガラスの切欠きと段差を実歩行で検査。
3. 共通開口、上階床、上下別エスカレーター/階段/EV。到着後共用通路へ進めることをテスト。
4. 各店の内装を新入口/主路に再配置し、NPC・猫・宝箱と案内図・移動先を更新。
5. 1000人で回避/負荷と全店の入口到達を検査。初期スキャナーでのクリア、特殊/猫では位置通知のみを回帰試験。
6. 実測スクリーンショット・検査ログを提出してから次フロアへ進む。

**この資料を提出して承認待ちで終了する。ゲーム本体の施工は行っていない。**
'''
(OUT/'README.md').write_text(report)
# Copy the exact reviewed scripts so the ZIP is reproducible in the same dependency environment.
(OUT/'review_b_drawings.py').write_bytes((ROOT/'tools/review_b_drawings.py').read_bytes())
(OUT/'package_b_drawing_review.py').write_bytes(Path(__file__).read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(OUT/'SHA256SUMS.txt').write_text('\n'.join(f'{sha(p)}  {p.relative_to(OUT)}'for p in sorted(OUT.rglob('*'))if p.is_file()and p.name!='SHA256SUMS.txt')+'\n'+sha(pdf)+'  '+pdf.name+'\n')
zipout=D/'FIND_YOURSELF-B-Detailed-Review-v3.zip'
with zipfile.ZipFile(zipout,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9)as z:
 z.write(pdf,pdf.name)
 for p in sorted(OUT.rglob('*')):
  if p.is_file():z.write(p,'review/'+str(p.relative_to(OUT)))
with zipfile.ZipFile(zipout)as z:assert z.testzip()is None
print(json.dumps(dict(pdf=dict(bytes=pdf.stat().st_size,sha256=sha(pdf)),zip=dict(bytes=zipout.stat().st_size,sha256=sha(zipout)),checks=len(checks),pdf_pages=34,game_files_unchanged=len(filehashes)),indent=2))
