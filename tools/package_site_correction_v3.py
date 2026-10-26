"""Review-only v3 ZIP. Preserve and separately identify original v2 inputs."""
from site_v2_common import *
import zipfile,collections
O=R/'docs/site-correction-v3';D=read(O/'geometry.json');P=read(O/'parking-geometry.json');A=read(O/'independent-verification.json');V=read(O/'vehicle-verification.json');PV=read(O/'pdf-verification.json');pdf=R/'downloads/FIND_YOURSELF-Site-Correction-v3.pdf'
assert not A['failed']and not V['failures']and not PV['failed'];assert A['source_geometry_sha256']==sha(O/'geometry.json');assert PV['sha256']==sha(pdf);assert A['old_65_remaining']==0
for path,h in read(O/'protected-inputs.json').items():assert sha(R/path)==h,path
F=D['floors'];slots=[dict(st,facility=fac['id'],level=f['level'],height=f['height'])for fac in P['facilities']for f in fac['floors']for st in f['stalls']]+[st for f in F if f.get('parking')for st in f['parking']['stalls']]+D['site']['old_A22']['stalls'];assert len(slots)==6699 and len({s['id']for s in slots})==6699
use={'general':'一般','standard':'一般','comfort':'ゆとり','accessible':'身障者用','EV':'EV充電','staff':'職員'}
csvwrite(O/'parking-ledger.csv',['ID','施設','駐車段','高さm','用途','幅m','長さm','X','Z','ポリゴンGeoJSON'],[[s['id'],s['facility'],s['level'],s['height'],use[s['category']],s['width_m'],s['length_m'],s['polygon'].centroid.x,s['polygon'].centroid.y,json.dumps(mapping(s['polygon']))]for s in slots]);counts=collections.Counter((s['facility'],s['level'],use[s['category']])for s in slots);csvwrite(O/'parking-capacity-by-use.csv',['施設','駐車段','用途','区画数'],[[*k,n]for k,n in sorted(counts.items())])
csvwrite(O/'all-15-floor-unit-ledger.csv',['館','階','ID','用途','区画㎡','入口X','入口Y','入口Z','扉幅m','バックルーム㎡','床版'],[[f['wing'],LABEL[f['level']],s['id'],s['category'],s['polygon'].area,s['entry'][0],f['height'],s['entry'][1],s['door_width_m'],s['backroom'].area,'v3']for f in F for s in f['stores']])
replay=read(O/'65-replayed-checks.json');csvwrite(O/'65-issue-before-after.csv',['種別','ID','旧値','新値','結果','旧原本変更'],[[q['kind'],q['id'],q['old_value'],q['new_value'],'PASS'if q['pass_']else'FAIL',False]for q in replay])
csvwrite(O/'core-opening-landing-ledger.csv',['ID','館','階','Y','EV開口㎡','階段開口㎡','前方乗降㎡','中間踊場投影㎡','中間踊場Y','EV前乗降㎡','設計反映','Godot実装'],[[v['id'],v['wing'],LABEL[v['level']],v['height'],v['lift_opening'].area,v['stair_opening'].area,v['front_landing'].area,v['mid_landing'].area,v['mid_landing_elevation_m'],v['lift_landing'].area,True,False]for v in D['vertical_devices']])
changes=collections.Counter(q['kind']for q in D['changes']);rows='\n'.join('|'+d['id']+'|'+str(d['clear_width_m'])+'|'+str(round(d['frame_opening_width_m'],2))+'|'+str(round(d['overall_frame_width_m'],2))+'|'for d in D['doors'])
md=f'''# FIND YOURSELF｜敷地全体設計 修正版 v3

**設計資料のみ。Godot未実装・最終承認待ち。** 2026-10-26。

## 結果

- 全3館15層、店舗/施設470区画、駐車6,699区画の基本配置を維持。
- B館の旧65件は同じ検査IDで再照合し、**残存0件**。
- 全15層独立検査 **{A['checks']:,}件・不合格0件**。0.30m半径の歩行者で、壁/枠/開扉パネル/什器/床穴を引いた連続床を検査。
- 来客入口3か所を新設計へ反映。A/Bの30コア階図（EV穴30、上階の階段穴24）と、24層間の中間踊場を図面へ統合。
- 車両は10到着路線の平面掃引と34寸法項目を確認。**NOT_TESTED 6,737件を合格に含めない**。
- ゲーム/既存図面/既存データの保護対象{A['protected_originals']}ファイルのSHA一致。旧原本を上書きせず、v3データだけを新設。

## 原本と修正版

`geometry.json`は**修正版の15層＋敷地**、`parking-geometry.json`は**修正版の外部17駐車面**です。v2ファイルへの上書きではありません。
B旧65の修正をv3の店舗/壁/共用床/入口/店内主路に反映し、図面だけを塗り直した扱いにしていません。

比較は65-replayed-checks.json/65-issue-before-after.csv、変更形状はchange-register.jsonとgeometry.jsonのchangesへ保存。B館v4.1の原本をZIPにも別パスで同梱します。

## 修正内容

1. B旧65：店舗境界56ペア、共用床/店舗3階分、入口中心が公開床から1cm超離れた6件を解消。店舗の壁/主路/棚/バックルームも新しい区画へ整合。
2. 扉前の局所調整：実際の壁を引くと、A/Bの設備核入口に隣接店舗がかかる箇所がありました。必要な閾部だけを区画から退避。A {changes['A_core_threshold_local_store_recess']}区画階、B {changes['B_core_threshold_local_store_recess']}区画階。店舗数/館形/広場は維持。
3. C設備前：既存ベンチ/植栽{changes['C_equipment_approach_furniture_shift']}点を近傍へ移設し、扉前を空けました。公用床・庭・デッキ形状は増やしていません。Cの床/面積原本はそのまま保護。
4. 駐車後方：個別アクセス線の0.8m前後の余裕帯を、幅1mの短い歩行エプロンとして歩行床へ明示。マス・車路とは重ならず、既存床に支持され、全枠後方から共用歩道へ接続。
5. 接続した上階の受口だけ、仮柵を修正版で開放。未接続上階口や駐車棟端段の斜路防護は保持。

## 来客扉3か所

|ID|有効幅m|躯体孔m|枠外寸m|
|---|---:|---:|---:|
{rows}

4枚テレスコピック自動引戸。開いたパネルは両側収納部、閉じたパネルは中央に置く別状態で定義。躯体孔と枠の左右各2cmの取付部は充填、枠と玄関側壁の間も閉鎖パネルを入れ、隙間を残しません。玄関床/段差0/枠/扉/両側1.5m待機床を統合。検査は**開扉状態**で、開閉制御はGodot未実装。

## 階段・EV

- A/B全30コア階図でEV内法14.44㎡を構造床から切欠き、上階24か所に階段用床穴を反映。B1階段下の基礎床は保持。
- 有効幅2m、16段×2、踏面0.30m、片側水平長4.5m。中間踊場は各階の中間高さに別スラブで置き、各階の平床と混同しません。
- 中間踊場投影は両フライトに重なって接続。前方乗降床とEV前1.8×1.5m床は、その階の構造床で支持。
- EVの穴をキャビンで構造的に埋めていません。キャビン/敷居は停止時の可動設備として別形状、前方隙間設計0.02m。実機、インターロック、ピット/昇降路頂部、制御/構造は未検証。

## 到達性の検査範囲

店の公開側アンカーは入口から公開側へ0.5m。壁・什器・穴を引き、半径0.30mで縮めた連続床の実座標に入ることを確認。到達しない点を近傍へ自動投影して合格にはしていません。
駐車後方→共用歩道→階段/EV前、実際の受口→敷地歩道/橋→新玄関→商業階、各階→他館を図面上で照合。graphは歩行可能床と乗降設備の設計関係であり、**Godot実歩行/ナビメッシュの検証ではありません**。

## 車両の結果と限界

|状態|件数|意味|
|---|---:|---|
|PASS_2D_SAMPLED|10|指定到着方向の平面車体掃引が舗装内|
|PASS_DIMENSION|34|出入口法線、幅、スロープ数値勾配、系統分離|
|FAIL|0|実行した上記検査の残存不合格|
|NOT_TESTED|6,737|下記の未実行軌跡。**合格扱いしない**|

乗用車4.8×1.9m/軸距2.8m/後端1m/後車軸半径6m、単車トラック12×2.5m/軸距6m/後端3m/後車軸半径12mというゲーム用モデル。メーカー実測ではありません。
直線0.25m、円弧0.5度の姿勢から車体全体を掃引し、姿勢間を凸包でつなぎ0.02mの余裕を追加。車輪中心の円だけを合格証拠にしていません。

局所修正：A南の最後12mを入口法線へ正対。B東は搬入縦車路上に停止して不自然な西向き切返しを廃止。B西は停止を0.3m手前にして車体前端余裕を確保。C地下の停止点は既存ヤードの車路中心に合わせています。館形/駐車枠は不変更。

**未検証の内訳：**6,699区画それぞれの前後進/切返し、10到着路線の出庫/ヤード反転、24外部斜路の3D姿勢/腹擦り/桁下、B/Cの新斜路の3D、B地下/屋上2エリアの内部最小半径経路。合計6,737行を個別に記録。
既存の駐車棟の円形旋回テンプレートを、全車路/全駐車枠の運動学的合格へ拡大解釈していません。対向車、車線ごとの走行、同時通行、交通需要、敷地外道路、実車も未検証。

**6,699は設計区画数です。全区画の入出庫が成立した運用可能台数は未確定（vehicle_verified_capacity=null）。**

## 残課題

- 上記NOT_TESTEDの車両軌跡と交通運用。
- Godot実歩行、階段/EV/扉の動作、衝突、NPC1000/5000人、宝箱、案内図、FT、セーブ連携。
- 橋/屋上/床/階段/EVの構造・柱梁・荷重・基礎、EV仕様/ピット/頂部、排水/擁壁/地盤、法規/避難/防災。
- A東の追加搬入扉はv2の別案を保持し、今回の来客扉3か所と混ぜて完了扱いしていません。搬入台車の運用・兼用EVの実積載も未検証。

**設計資料までで停止。ユーザー承認までGodotへの実装は行いません。**

## データ/再生成

World XZメートル、Y=-5.35/0/5.525/10.875/16.4。B旧原本だけlocal→world(-714,-30)。CSVはUTF-8 BOM。
再生成は既存リポジトリ上で、`protected-inputs.json`の固定入力と既存Notoフォントを使います。ZIPはすべてのv2入力やゲームを重複収録する完全ソース配布ではありません。旧入力は前回v2資料および同リポジトリのcommit 9a24bd6b084311582ab5ac3a3e73613224f6186fへ固定。

```
python tools/design_site_correction_v3.py
python tools/check_vehicle_correction_v3.py
python tools/check_site_correction_v3.py
python tools/draw_site_correction_v3.py
python tools/verify_site_correction_v3.py
python tools/package_site_correction_v3.py
```

Python3/Shapely2/NumPy/PyMuPDF/Pillow。旧描画ツールは純関数のみAST抽出し、旧ツールのトップレベルは実行しません。
図面フォントはNoto CJK、著作権/OFLは同梱third_party/noto-cjk-COPYRIGHT.txt。公式フロアガイド/写真は再配布していません。
'''
(O/'README.md').write_text(md)
# Accurate small previews: drawings, not gameplay captures.
import fitz
pdoc=fitz.open(pdf)
for name,i in [('site',2),('A-2F',next(q['page']-1 for q in read(O/'atlas-pages.json')if q['wing']=='A'and q['level']==1)),('B-2F',next(q['page']-1 for q in read(O/'atlas-pages.json')if q['wing']=='B'and q['level']==1))]:pdoc[i].get_pixmap(matrix=fitz.Matrix(.8,.8)).save(O/(name+'-drawing-preview.png'))
files=[pdf]+[p for p in O.iterdir()if p.is_file()and p.name not in['release-manifest.json','zip-verification.json']]+list((R/'tools').glob('*correction_v3.py'))+[R/'tools/site_v2_common.py',R/'tools/draw_site_completion_v2.py',R/'docs/b-v4-overlap-correction/geometry.json',R/'docs/site-completion-v2/independent-verification.json',R/'third_party/noto-cjk-COPYRIGHT.txt'];files=list(dict.fromkeys(files));manifest=[dict(path=str(p.relative_to(R)),sha256=sha(p),bytes=p.stat().st_size)for p in files]
write(O/'release-manifest.json',dict(files=manifest,game_included=False,originals_modified=False));archive=R/'downloads/FIND_YOURSELF-Site-Correction-v3.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9)as z:
 for p in files+[O/'release-manifest.json']:z.write(p,p.relative_to(R))
with zipfile.ZipFile(archive)as z:
 assert z.testzip()is None
 for q in manifest:assert hashlib.sha256(z.read(q['path'])).hexdigest()==q['sha256']
assert archive.stat().st_size<32*1024**2 and pdf.stat().st_size<32*1024**2
write(O/'zip-verification.json',dict(sha256=sha(archive),bytes=archive.stat().st_size,files=len(files)+1,CRC='all pass',member_hashes='all pass',game_modified=False,old65_remaining=0,vehicle_NOT_TESTED=V['status_counts']['NOT_TESTED']))
print(json.dumps(dict(pdf_pages=PV['pages'],pdf_MiB=round(pdf.stat().st_size/1024**2,2),zip_MiB=round(archive.stat().st_size/1024**2,2),zip_files=len(files)+1),ensure_ascii=False))
