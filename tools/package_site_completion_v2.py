"""Review-only release: all 15 mall layers, all external parking decks, ledgers and raw verification."""
from site_v2_common import *
import fitz,zipfile,collections
O=R/'docs/site-completion-v2';S=read(O/'summary.json');IV=read(O/'independent-verification.json');PV=read(O/'pdf-verification.json');BV=read(R/'docs/b-completion-v2/summary.json');CV=read(R/'docs/c-area-audit-v2/verification.json');PP=read(R/'docs/parking-blocks-v2/verification.json')
assert not PV['failed']and not BV['failed']and not CV['failed']and not PP['failed']and not S['failed']
assert len(IV['failed'])==65 and all(q['id'].startswith(('B1','B2','B3','B-'))for q in IV['failed'])
assert not[q for q in read(O/'B-v4.1-local-cleanup-proposal-checks.json')if not q['pass_']]
A=read(R/'docs/a-detailed-design-v1/geometry.json');B=read(R/'docs/b-v4-overlap-correction/geometry.json');C=read(R/'docs/c-detailed-design-v1/geometry.json');BN=read(R/'docs/b-completion-v2/geometry.json');F={w:{f['level']:f for f in d['floors']}for w,d in[('A',A),('C',C),('B',BN)]}
for f in B['floors']:q=floor_B_world(f,[core_world(c)for c in B['cores']]);F['B'][q['level']]=q
csvwrite(O/'all-15-floor-unit-ledger.csv',['館','階','ID','用途','区画㎡','入口X','入口Y','入口Z','入口幅m','バックルーム㎡','変更状態'],[[w,LABEL[l],st['id'],st['category'],st['polygon'].area,st['entry'][0],HEIGHT[l],st['entry'][1],st['door_width_m'],st['backroom'].area,'新規B地下/屋上案'if w=='B'and l in[-1,3]else'基準原本不変更']for w,ff in F.items()for l,f in sorted(ff.items())for st in f['stores']])
csvwrite(O/'all-fixed-B-issues.csv',['種別','ID','原本不合格値','原本変更','局所案適用'],[[q['kind'],q['id'],q['value'],False,False]for q in IV['failed']])
csvwrite(R/'docs/b-completion-v2/service-program-ledger.csv',['階','ID','用途','投影㎡','保守歩道㎡','機器作業ベイ㎡','一般客公開','入口X','入口Z'],[[f['label'],q['id'],q['name'],q['polygon'].area,q.get('service_walk',Polygon()).area,q.get('work_bays',Polygon()).area,False,*(q.get('entry')or[None,None])]for f in BN['floors']for q in f['program']])
md=f'''# FIND YOURSELF｜3館・駐車場・15層 設計補完 v2

2026-10-26、ユーザー承認待ち。**設計資料のみ。ゲーム未改修・未実装。**

## 収録物

- 全15層（A/B/C×B1・1F・2F・3F・RF）の詳細平面図と拡大図、全体配置、設備核、来客玄関、昇降塔、地下/屋上車路、面積表。
- 外部駐車17面（7段立体×2＋平面×3）の詳細図35ページを巻末に統合。
- 図面上の駐車区画実数 **6,699台**。外部6,369＋A既存22＋B B1 193＋B RF115。
- 全470店舗/施設区画の台帳、駐車場6,699IDの台帳、経路・接続・寸法台帳、設計JSON/GeoJSON、検査全行と原本SHA。
- A/C原本およびB館v4.1の1〜3F原本を同梱し、固定図と追加案を比較可能。

## 駐車場

|施設|形態|図面区画実数|
|---|---|---:|
|P-A-E|7段立体（最上段屋上を含む）|2,541|
|P-B-S|7段立体（最上段屋上を含む）|2,205|
|P-C-N|屋外平面|465|
|P-B-W|屋外平面|485|
|P-A-S|屋外平面|673|
|P-A-OLD22|既存地上22枠を保持、外部エプロン/後方歩道補完|22|
|P-B-B1|B地下|193|
|P-B-RF|B屋上|115|
|合計||6,699|

各枠の寸法、用途、座標、形状を台帳に保存。屋上段やEV/職員枠を重複加算しません。台数は描いた枠の実数で、全枠の実車切返し・交通容量の保証ではありません。

外部立体の床高：0 / 2.750 / 5.525 / 8.200 / 10.875 / 13.625 / 16.400m。P3/P5/P7がモール2F/3F/RF高と一致します。主にA東P3とB南P7の受口を接続し、未接続上階口は仮柵を維持。接続橋を施工する時点で対応する仮柵だけ撤去する条件です。

歩行者ポート3mは8m区間で4m歩道へ広げ、車路を無理に拡幅していません。搬入幹線の地上横断を避け、独立した階段/EV塔と橋（Y5.525、桁厚仮定0.32、桁下5.205m）で接続。

来客車系と搬入車系は幾何的に分離。搬入先はB西/東、A東新ヤード、C地下既存ヤード。C地下へは直線下降150m＋地下水平20m＋西折15m、幅8m・最大約3.82%の新露天下降路で接続します。地下ヤードは30×49m、Y-5.35m。地上公開床へ加算しません。

## B館B1/RF

B1は食品/受取2区画、193駐車枠、共同倉庫・設備保守ベイ。RFはカフェ1区画、115駐車枠、既存3吹き抜け投影を守った屋上前庭・PV/空調保守ベイ。
新エスカレーターは、B1↔1Fで既存12バンク、3F↔RFで既存23バンクの平面投影を再使用。既存1〜3Fを拡張せず上下に積層。新地下車路はB南立体G0から70m・幅7m・最大約8.23%。屋上は幅7m車路橋と4m歩道橋を2.5m離隔で分離。

地下/屋上の保守ルートは一般客の主路と区別。指定横断部を除き、駐車マスや開口を通らないように設計。大型共同倉庫/設備ベイは割付段階で、柱梁、機器型式、配管配線・ラック製作図は未設計です。

## C館1F面積

- 6棟躯体投影和集合：18,953.028976㎡。
- 公開床21,418.377759㎡＝6棟投影内6,574.336131㎡＋投影外14,844.041628㎡。
- 6棟投影内の非公開部分12,378.692845㎡。投影内公開床と合計して6棟躯体投影に一致。
- 構造床板33,046.830604㎡は屋外歩行床も含み、建物投影や室内面積の別名ではありません。
- 前廊4,071.114556㎡には投影外接続180.938425㎡と設備核との名目交差21.6㎡が含まれるため単純加算禁止。
- 排他的16区分で5階を監査。屋内施設/裏室/設備核/庇下前廊/屋外通路/広場歩行床/上階デッキ/非公開植栽/開口等を区別。
- 監査専用1e-12m正規化、最大面積差1.74e-10㎡未満。原本は無変更、元精度値も別保存。

## 検査と原本の不合格（隠さない）

|対象|結果|意味|
|---|---|---|
|外部駐車|source44,815＋独立43,445、失敗0|17面と個別マス/歩道/車路/支持/端段防護/PDF|
|B新B1/RF|{BV['checks']}件、失敗0|ポリゴン・接続・保守ルート。実車検証ではない|
|敷地統合|{S['checks']}件、失敗0|道路分離・ポート全幅・高さ・原本SHA等|
|C面積|1,611件、失敗0|排他的面積と元データ照合|
|15層独立検査|{IV['checks']}件中{IV['passed']}合格、**65不合格を保持**|すべて固定B1〜3Fの微小不整合|
|固定B局所修正案|9集約項目、失敗0|**原本未適用**。原本の65不合格を上書きしない|
|駐車面→モール関係グラフ|28項目、失敗0|扉等の承認条件付き宣言グラフ。実ナビ/衝突検査ではない|

前回v4.1で解消した共用床/閉鎖帯の重複は3階とも0㎡を維持（baseline-retained-checks.json）。以下は別の分類です。

固定Bの不合格：店舗境界56ペア、共用床/店舗3階分（0.042652630 / 0.046392481 / 0.043148223㎡）、入口中心と公開床の距離が1cm超6件（最大約1.9cm）。全ID/値はall-fixed-B-issues.csv。

別案では境界の局所切欠きと入口前床の微小充填だけを提案。建物外形/通路網/店舗数/広場を維持。入口中心の数値調整は0.7mm未満。B-v4.1-local-cleanup-UNAPPLIED.jsonは**採用済み原本ではありません**。承認後には店内什器/壁を新境界へ再クリップして再検査する必要があります。

## 未適用の変更案・未検証事項

1. 新来客口3：B1F翼広場南、A2F東、A2F南。元店舗/設備核との重複0を確認。A東核店バックルームの2m搬入扉も別案。
2. A/B既存24コア階図のEV/階段床穴。室割り記号だけで構造床に穴がないため、原本を保存して必要な穴を別提案。Cの既存開口は維持。
3. 固定B微小境界修正3階分の別案。原本65不合格は現状値のまま。
4. バリアフリー全15層接続と兼用貨物EVはA/B床開口案の承認が前提。ESC経路の連結と混同しません。
5. 実歩行、ゲーム衝突、NPC経路/1000・5000人負荷、宝箱、案内図、FT、セーブ、EV/ESC/階段動作、全車両軌跡、交通需要、構造/法規/防災/排水/地盤は未検証。
6. C露天搬入スロープの擁壁・排水ポンプ、橋の柱梁・基礎、駐車/屋上の構造荷重は未設計。トラックは12m級単車、車高4.2mのゲーム用想定。
7. 白い空白は敷地外/周辺街区未設計。敷地境界は実施設/道路/歩道/付属設備の投影＋12mの排水植栽管理帯の和集合。外接矩形を面積として数えません。公道接続はゲーム用仮定で実地測量ではありません。

**Godotのゲーム本体、B館v4.1原本、A/C原本を変更せず、ここで承認待ちとして作業を終了します。**

## データ・再生成

`geometry.json`はWorld XZメートル。B原本のみlocal→world(-714,-30)で剛体変換。Yは共通の[-5.35,0,5.525,10.875,16.4]m。CSVはExcel用UTF-8 BOM。

再生成は既存リポジトリ内で次の順番です。Python3＋Shapely2/NumPy/PyMuPDF/Pillowと既存Notoフォントが必要。ゲーム実行は不要。

```
python tools/design_b_completion_v2.py
python tools/refine_b_completion_v2.py
python tools/complete_b_service_v2.py
python tools/design_site_completion_v2.py
python tools/check_site_completion_v2.py
python tools/propose_b_baseline_cleanup_v2.py
python tools/site_reachability_v2.py
python tools/draw_site_completion_v2.py
python tools/verify_site_pdf_v2.py
python tools/package_site_completion_v2.py
```

外部駐車/C面積は`design_parking_v2.py`・`draw_parking_v2.py`・`audit_c_area_v2.py`。先行生成の固定SHAを各検査/図面に収録。再生成結果は浮動小数演算/ライブラリ版で最小桁が変わる場合があるため、提出済みSHAがレビューの基準です。

参考：ユーザー提供の公式AEON_LAKETOWN_OFFICIAL_FLOOR_GUIDE_202610.pdf（SHA256 2a50e320b180fe1fffc391d175deaa013f6bb50ee53b60fb7135530b8bfb7eac）、前回A/C v1とBv4.1。元公式PDF/写真は本ZIPへ再配布せず、今回数値を公式実測と扱いません。フォントの著作権・OFLはthird_party/noto-cjk-COPYRIGHT.txt。
'''
(O/'README.md').write_text(md)
(R/'docs/c-area-audit-v2/README.md').write_text('# C館面積監査 v2\n\n原本C館v1を変更しない監査。area-polygons.json/GeoJSONは排他的16用途、exclusive-area-ledger.csvは全5階の面積。raw-source-vs-audit-precision.jsonは元精度値と監査正規化の差を保持。verification.jsonの1,611項目が全合格でも、実歩行・建築法規の検証ではありません。詳しい集計範囲は全体設計READMEと統合PDFを参照。\n')
(R/'docs/b-completion-v2/README.md').write_text('# B館B1/RF補完 v2\n\n今回新しいB地下・屋上だけを設計。旧B館v4.1の1〜3Fは未変更。geometry.jsonには新B1/RF、積層ESC、地下車路、保守動線を収録。core-opening-proposals.jsonはA/B既存階の床穴の未適用提案。固定Bの微小不整合と局所案はdocs/site-completion-v2/へ分離。実歩行・実車・構造未検証。詳細は統合READMEを参照。\n')
(R/'docs/parking-blocks-v2/README.md').write_text('# 外部駐車詳細 v2\n\n6,369個のポリゴンを持つ駐車区画、2棟×7段と3平面の全17面。geometry.jsonと個別台帳は同じID。capacity.jsonは同一マスの用途別集計。verification.jsonはsource44,815/独立43,445の検査記録。敷地道路/館への接続/B地下・屋上追加はsite-completion-v2を参照。外部上階の未接続受口には仮柵を残し、橋を施工した受口だけ仮柵撤去。実車/需要/構造/法規未検証。\n')
# Reuse only an already verified PDF with byte-identical component sources.
if '--reuse-pdf'in sys.argv:
 full=R/'downloads/FIND_YOURSELF-Site-Complete-v2.pdf';vr=read(O/'complete-pdf-verification.json');assert sha(full)==vr['sha256']
 for part in vr['parts']:assert sha(R/part['path'])==part['sha256']
 d=fitz.open(full)
else:
 # Combine both vector books with font stream deduplication.
 paths=[R/'downloads/FIND_YOURSELF-Site-15-Floors-v2-Review.pdf',R/'downloads/FIND_YOURSELF-Parking-Blocks-v2.pdf'];doc=fitz.open();toc=[];parts=[]
 for path in paths:
  src=fitz.open(path);offset=len(doc);doc.insert_pdf(src);toc.extend([[row[0],row[1],row[2]+offset]for row in src.get_toc()]);parts.append(dict(path=str(path.relative_to(R)),sha256=sha(path),start_page=offset+1,end_page=len(doc)));src.close()
 doc.set_toc(toc)
 # Reuse only byte-identical embedded font streams. Keep each font's own cmap/descriptor.
 # This avoids quadratic comparison of thousands of unrelated vector streams in garbage=4.
 fontstreams={};reused=0
 for xref in range(1,doc.xref_length()):
  for key in ['FontFile','FontFile2','FontFile3']:
   typ,val=doc.xref_get_key(xref,key)
   if typ!='xref':continue
   ref=int(val.split()[0]);digest=hashlib.sha256(doc.xref_stream(ref)).hexdigest()
   if digest in fontstreams and fontstreams[digest]!=ref:doc.xref_set_key(xref,key,f'{fontstreams[digest]} 0 R');reused+=1
   else:fontstreams[digest]=ref
 full=R/'downloads/FIND_YOURSELF-Site-Complete-v2.pdf';doc.save(full,garbage=3,deflate=True);doc.close();d=fitz.open(full);bad=[]
 source_docs=[fitz.open(p)for p in paths]
 for i,p in enumerate(d):
  pix=p.get_pixmap(matrix=fitz.Matrix(.12,.12));part=next((k,v)for k,v in enumerate(parts)if v['start_page']<=i+1<=v['end_page']);k,v=part;original=source_docs[k][i+1-v['start_page']].get_pixmap(matrix=fitz.Matrix(.12,.12))
  if not pix.samples or hashlib.sha256(pix.samples).digest()!=hashlib.sha256(original.samples).digest():bad.append(i+1)
 for src in source_docs:src.close()
 assert not bad and len(d)==sum(p['end_page']-p['start_page']+1 for p in parts)
 write(O/'complete-pdf-verification.json',dict(parts=parts,pages=len(d),sha256=sha(full),bytes=full.stat().st_size,all_pages_rendered=True,every_page_pixels_match_original=True,reused_identical_font_streams=reused,failed=bad))
# Small standalone, accurate previews; these are drawings, not in-game screenshots.
for title,i in [('whole-site',2),('B-basement',23),('C-area-map',74)]:
 p=d[i];p.get_pixmap(matrix=fitz.Matrix(.8,.8),alpha=False).save(O/(title+'-drawing-preview.png'))
# Japanese capacity ledger: normalize general/standard as the same use without duplicating slots.
with (O/'parking-ledger.csv').open(encoding='utf-8-sig')as fp:slotrows=list(csv.DictReader(fp))
usejp={'general':'一般','standard':'一般','comfort':'ゆとり','accessible':'身障者用','EV':'EV充電','staff':'職員'};cap=collections.Counter((row['facility'],row['level'],usejp[row['category']])for row in slotrows);assert sum(cap.values())==6699
csvwrite(O/'parking-capacity-by-use.csv',['施設','駐車段level','用途','区画実数'],[[*key,count]for key,count in sorted(cap.items())])
# Sources, original baseline ledgers and notices; no game/official reference PDFs are redistributed.
files=[full]+list(O.glob('*'))
for sub in ['b-completion-v2','c-area-audit-v2','parking-blocks-v2']:files+=list((R/'docs'/sub).glob('*'))
for sub in ['a-detailed-design-v1','c-detailed-design-v1','b-v4-overlap-correction']:
 files+=[p for p in(R/'docs'/sub).glob('*')if p.suffix in['.json','.csv','.md']]
files+=[R/'third_party/noto-cjk-COPYRIGHT.txt']
files+=[R/'tools'/name for name in['site_v2_common.py','design_b_completion_v2.py','refine_b_completion_v2.py','complete_b_service_v2.py','design_site_completion_v2.py','check_site_completion_v2.py','propose_b_baseline_cleanup_v2.py','site_reachability_v2.py','draw_site_completion_v2.py','verify_site_pdf_v2.py','package_site_completion_v2.py','design_parking_v2.py','draw_parking_v2.py','verify_parking_v2.py','audit_c_area_v2.py']]
# Read-only pure Grid extraction uses this existing generator. Include as dependency, never execute it during supplements.
files.append(R/'tools/design_b_v4.py')
files=[p for p in dict.fromkeys(files)if p.is_file()and p.name not in['release-manifest.json','zip-verification.json']]
manifest=[dict(path=str(p.relative_to(R)),sha256=sha(p),bytes=p.stat().st_size)for p in files];write(O/'release-manifest.json',dict(files=manifest,game_implemented=False,original_B_issues_retained=65))
archive=R/'downloads/FIND_YOURSELF-Site-Complete-v2.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9)as z:
 for p in files+[O/'release-manifest.json']:z.write(p,p.relative_to(R))
with zipfile.ZipFile(archive)as z:
 assert z.testzip()is None
 for item in manifest:assert hashlib.sha256(z.read(item['path'])).hexdigest()==item['sha256']
assert archive.stat().st_size<32*1024*1024,(archive.stat().st_size,'ZIP must stay below artifact limit')
assert full.stat().st_size<32*1024*1024
write(O/'zip-verification.json',dict(sha256=sha(archive),bytes=archive.stat().st_size,files=len(files)+1,CRC='all pass',sha256_of_every_member='all pass',game_included=False,official_reference_pdf_included=False,unresolved_original_B_failures=65))
print(json.dumps(dict(pdf=str(full.relative_to(R)),pages=len(d),pdf_MiB=round(full.stat().st_size/1024**2,2),zip=str(archive.relative_to(R)),zip_MiB=round(archive.stat().st_size/1024**2,2),files=len(files)+1),ensure_ascii=False))
