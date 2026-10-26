"""Validate final A/C books, current model pixels, protected bytes and downloadable package."""
from pathlib import Path
import sys,json,gzip,hashlib,collections,zipfile,subprocess,csv,unicodedata
import fitz
R=Path(__file__).resolve().parents[1];O=R/'docs/ac-detailed-design-v1';PDF=R/'downloads/FIND_YOURSELF-AC-Detailed-Design-v1.pdf';ZIP=PDF.with_suffix('.zip');BASE='9dd0b1a712340118586c266f1c8c172bf64edea1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
V=json.loads((O/'integration-verification.json').read_text());assert not V['failed']
for wing in['A','C']:
 p=R/f'docs/{wing.lower()}-detailed-design-v1/geometry.json';assert sha(p)==V['source_geometry_sha256'][wing]
A=json.loads((R/'docs/a-detailed-design-v1/pdf-source.json').read_text());C=json.loads((R/'docs/c-detailed-design-v1/delivery-verification.json').read_text())
for wing,proof in[('A',A),('C',C)]:
 root=R/f'docs/{wing.lower()}-detailed-design-v1';p=R/f'downloads/FIND_YOURSELF-{wing}-Detailed-Design-v1.pdf';assert sha(root/'geometry.json')==proof['geometry_sha256'];assert sha(p)==proof['pdf_sha256']
# Protected resources include all 238 tracked game resources and every B v4/v4.1 material.
protected=json.loads((O/'protected-baseline-hashes.json').read_text());mismatches=[path for path,h in protected.items()if sha(R/path)!=h];assert not mismatches,mismatches
changed=subprocess.check_output(['git','diff','--name-only',BASE,'--','scripts','scenes','assets','project.godot','export_presets.cfg','docs/b-purpose-review-v4','docs/b-v4-final-confirmation','docs/b-v4-overlap-correction'],cwd=R,text=True).splitlines();assert not changed,changed
model=json.loads(gzip.decompress((O/'view-model.json.gz').read_bytes()));imagefiles=[]
for m in model['models']:
 assert m['source_sha256']==V['source_geometry_sha256'][m['wing']]
 manifest=json.loads((O/'views'/f"{m['id']}-manifest.json").read_text());assert manifest['model_sha256']==hashlib.sha256(json.dumps(m,sort_keys=True).encode()).hexdigest();assert manifest['render_script_sha256']==sha(R/'tools/render_ac_detail_v1_views.py');assert manifest['source_geometry_sha256']==m['source_sha256']
 for c in m['cameras']:imagefiles.append(O/'views'/f"{m['id']}-{c['id']}.png")
assert len(imagefiles)==12
# Every static camera is on a delivered walkable floor with >0.5m reserve; checks are not runtime traversal.
sys.path.append('/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
from shapely.geometry import shape,Point
cam_checks=json.loads((O/'view-camera-checks.json').read_text());assert len(cam_checks)==6
for c in cam_checks:
 g=json.loads((R/f"docs/{c['wing'].lower()}-detailed-design-v1/geometry.json").read_text());f=next(f for f in g['floors']if f['level']==c['level']);assert shape(f['walkable']).covers(Point(c['actual_world_xz']).buffer(.54));assert abs(c['eye_world_y']-f['height']-1.65)<1e-10
# Read all PDF pages and rendered design views from the actual final combined PDF.
d=fitz.open(PDF);preview=Path('/tmp/ac-detail-v1-final-pdf');preview.mkdir(exist_ok=True);textall='';pageproof=[];xrefs=set()
for i,p in enumerate(d):
 p.get_pixmap(matrix=fitz.Matrix(.22,.22)).save(preview/f'{i+1:03}.png');textall+=p.get_text();bad=[]
 for b in p.get_text('dict')['blocks']:
  if b['type']!=0:continue
  for line in b['lines']:
   for span in line['spans']:
    b=fitz.Rect(span['bbox'])
    if b.x0<-.01 or b.y0<-.01 or b.x1>p.rect.width+.01 or b.y1>p.rect.height+.01:bad.append(span['text'])
 assert not bad,(i+1,bad)
 xrefs|={rec[0]for rec in p.get_images()};pageproof.append({'page':i+1,'rendered':True,'text_in_sheet':True})
for w in['A','C']:
 g=json.loads((R/f'docs/{w.lower()}-detailed-design-v1/geometry.json').read_text())
 for f in g['floors']:
  for s in f['stores']:assert s['id']in textall,(w,s['id'])
for s in['AB-1','AB-2','BC-1','BC-2','B1','RF']:assert s in textall,s
normalized_text=unicodedata.normalize('NFKC',textall)
assert '未設計'in normalized_text and '実歩行'in normalized_text

def rgbhash(px):
 if px.colorspace.n!=3:px=fitz.Pixmap(fitz.csRGB,px)
 if px.alpha:px=fitz.Pixmap(px,0)
 return hashlib.sha256(px.samples).hexdigest()
embedded={rgbhash(fitz.Pixmap(d,x)):x for x in xrefs};pixels=[]
for f in imagefiles:
 px=fitz.Pixmap(f);assert(px.width,px.height)==(1500,1000);h=rgbhash(px);assert h in embedded,('Stale/missing model image',f.name);pixels.append({'file':str(f.relative_to(R)),'png_sha256':sha(f),'pixel_rgb_sha256':h,'pdf_xref':embedded[h]})
assert not fitz.TOOLS.mupdf_warnings(),fitz.TOOLS.mupdf_warnings()
# The full PDF is reviewed by a contact sheet; larger selected sheets are generated for manual inspection.
contact=fitz.open();nrows=(len(d)+5)//6;cp=contact.new_page(width=1440,height=nrows*165)
for i,p in enumerate(d):
 x=i%6*240;y=i//6*165;cp.insert_image(fitz.Rect(x,y,x+236,y+143),pixmap=p.get_pixmap(matrix=fitz.Matrix(.15,.15)));cp.insert_text((x+4,y+158),str(i+1),fontsize=10)
cp.get_pixmap().save('/tmp/ac-detail-v1-book-contact.png')
for i in[0,2,8,10,11,12,13,14,15,16,17,18,21,22,30,63,64,70,90]:
 if i<len(d):d[i].get_pixmap(matrix=fitz.Matrix(.75,.75)).save(preview/f'{i+1:03}-large.png')
# Dimensions/field counts and checks stay separate across authors to avoid adding duplicate assertions.
stats={};all_geometry={}
for w in['A','C']:
 g=json.loads((R/f'docs/{w.lower()}-detailed-design-v1/geometry.json').read_text());all_geometry[w]=g;stats[w]=[]
 for f in g['floors']:
  body=shape(f['shell']);stats[w].append({'level':f['level'],'label':f['label'],'height':f['height'],'planned_units':len(f['stores']),'public_area_m2':shape(f['public']).area,'structural_floor_area_m2':shape(f['floor_plate']).area,'shell_bounds_world_xz':list(body.bounds),'shell_area_m2':body.area,'secondary_portals':sum(bool(s.get('secondary_entry'))for s in f['stores'])})
(O/'dimensions-and-counts.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2))
AP=json.loads((R/'docs/a-detailed-design-v1/pdf-verification.json').read_text());CP=json.loads((R/'docs/c-detailed-design-v1/delivery-verification.json').read_text())
report=f'''# FIND YOURSELF A館・C館 詳細設計v1\n\n**図面・設計データの提出。Godot本体とB館v4.1は変更していません。最終承認待ちで終了します。**\n\n## 開く資料\n- `downloads/FIND_YOURSELF-AC-Detailed-Design-v1.pdf`：全{len(d)}ページ。3館整合/立体参考22頁、A館42頁、C館38頁。しおりから各館・各階へ移動できます。\n- `docs/a-detailed-design-v1/`：A館5階、3広場、3設備核、三角回遊と中央短絡街、店舗/機器/設備/断面、台帳、旧ID対応、検査。\n- `docs/c-detailed-design-v1/`：C館5階、6独立棟、3庭、屋外デッキと棟前通路、地下歩行/搬入、屋上庭園、店舗/設備/断面と検査。\n- `docs/ac-detailed-design-v1/`：3館の接続、World座標、縦接続、旧訪問キー提案、最終立体図と統合検査。\n- `docs/b-v4-overlap-correction/geometry.json`：無変更のB館v4.1入力（本ZIPには基準データとして収録、原本上書きなし）。\n\n## 寸法・階層・区画\n- 階高：B1 -5.350m / 1F 0 / 2F 5.525m / 3F 10.875m / RF 16.400m。すべてゲーム用の設計値。\n- A：31/52/52/51/15=201区画。主201＋中央核店副8=209入口。旧51商業IDと補助2参照を用途付きで保持。三方向の街16/15/15m、中央商業短絡12m。\n- C：18/18/18/18/6=78区画。商業54、地下/屋上施設24を区別。独立棟6、周縁連絡デッキ約6m、棟前廊約6.75m。旧C商業11IDを用途一致で保持。\n- 全階の外接寸法・床/共用面積はdimensions-and-counts.json。店舗/設備の寸法は各館台帳・PDFを参照。外接矩形をそのまま床面積として数えていません。\n- A/C10面と、基準B館1～3Fの3面＝13詳細床面を接続確認。B館B1/RFの2面は基準未設計であり、勝手に新規設計していません。全15面の完成ではありません。\n\n## B館との固定接続\n|接続|World X,Z|床高m|幅m|\n|---|---|---:|---:|\n|AB-1|(-174,-5.5)|0|5|\n|AB-2|(-110,-5.5)|5.525|5|\n|BC-1|(-370,-80)|0|8|\n|BC-2|(-432,-117)|5.525|5|\n\nB側のポリゴン・端点・幅・高さは無変更。A2Fで橋が閉鎖帯へ入る6㎡は、A側の到着公共床とファサード切欠きで解消。C2Fは庭の西縁からSW棟の前廊へ接続します。幅方向の支持・両館の床連続・店舗/閉鎖帯/設備核との干渉を別々に検査しています。B側の変更案は今回ありません。\n\n## 立体目視で直した内容\nC初稿の上階円盤/放射状床は庭を屋根のように覆ったため不採用。棟前/周縁デッキに限定し、3庭の中心の空中抜けを全上階で合わせました。Aは用途不明な大きな閉鎖帯を削減して、実入口を持つ中央大型店を計画。旧スーパー・書店/読書・food4と共有28席は機能を残す対応へ修正しました。\n\n## 検査結果の区分\n- A著者側：source {AP['source_checks']:,}＋独立 {AP['independent_checks']:,}、不合格0。\n- C著者側：source {CP['source_checks']:,}＋独立 {CP['independent_checks']:,}、不合格0。\n- 3館独立照合：{V['total_checks']:,}、不合格0。45cm余裕の共用域連結、商業/施設入口、内部主路、重複、開口、4固定ゲート、13床面ネットワークと保護ファイルを確認。面積数値許容1e-8㎡。\n- 各検査には対象の重複があるため、足し合わせて単一の検査総数にはしていません。\n- Godot実歩行0。過去v0.24の実歩行結果は今回の新設計の結果に流用しません。\n\n## 座標・ID・保存互換\n新A/CはWorld XZ m。Bは無変更のLocalからWorldへ(-714,-30)平行移動で読取比較。旧AはMallCurveの変形があるため、旧区画重心と新入口、旧論理原点とWorld換算点を区別しました。旧ID・旧用途・新用途・比較点の種類を各館CSVへ収録。訪問キー20件を保持した新A/C15候補の提案表もあり、B側5件の移動は今回対象外。フラグ・セーブ・ゲームコードは一切編集していません。\n\n## 画像の限界と未検証\n12枚は設計JSONから別モデルを作った画像で、実ゲーム画面ではありません。透明材・商品・照明・構造支持架構は簡略化。模型外周は切断範囲で、白い背景は実際の出口ではありません。立体モデルのカメラ位置は共用歩行域の0.54m余裕内、目高1.65mで独立確認。反射・実照明の採光測定や実歩行の代替ではありません。\n\n未検証：Godotの実歩行/コリジョン、梁下/支持柱/手すり、扉/EV/エスカレーター駆動、雨天/夜間照明、NPC密度、猫/宝箱/ソナー/案内図/ファストトラベル、セーブ互換、実機フレーム時間、施設の構造/設備/法規適合。図面で不合格0でもゲームや実施設の完成を意味しません。承認後に既存機能と一緒に段階実装する必要があります。\n\n## 再現\n同じリポジトリ入力とPython/Shapely/PyMuPDF/Blenderを用い、設計用toolsを実行。ZIPは完成図面/データ/検査を閲覧するためのものでゲーム一式や全依存ソフトは含みません。立体画像12枚は統合PDFに収録し、重複する個別PNGと中間描画メッシュはZIPから省いています（リポジトリには保存）。公式参考PDF原本は再配布せず、提供ファイルのSHAと目視参照ページを記録しています。\n'''
(O/'README.md').write_text(report)
proof={'design_only':True,'game_modified':False,'B_v4_1_modified':False,'source_baseline_commit':BASE,'source_geometry_sha256':V['source_geometry_sha256'],'combined_pdf_sha256':sha(PDF),'pdf_pages':len(d),'bookmarks':len(d.get_toc()),'all_pages_rendered':True,'all_A_C_unit_ids_present':True,'design_views_embedded':len(imagefiles),'standalone_render_PNGs_in_ZIP':False,'render_mesh_cache_in_ZIP':False,'image_pixels_match_current_models':True,'view_provenance':pixels,'protected_files':len(protected),'protected_mismatches':mismatches,'old_game_or_B_files_changed':changed,'integration_checks':V['total_checks'],'integration_failed':V['failed'],'A_source_checks':AP['source_checks'],'A_independent_checks':AP['independent_checks'],'C_source_checks':CP['source_checks'],'C_independent_checks':CP['independent_checks'],'runtime_walk_tests':0,'defined_network_floor_surfaces':13,'B_B1_RF_defined':False,'page_checks':pageproof,'tools_sha256':{str(p.relative_to(R)):sha(p)for p in list(R.glob('tools/*ac_detail_v1*.py'))+[R/'tools/extract_ac_legacy_v1.py']}}
(O/'delivery-verification.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2))
# Full current design data plus one combined PDF, avoiding duplicate embedded-font PDF copies.
dirs=[R/'docs/a-detailed-design-v1',R/'docs/c-detailed-design-v1',O];files=[]
for folder in dirs:
 for p in folder.rglob('*'):
  if not p.is_file()or p.name=='SHA256SUMS.txt'or'design-review-before'in p.parts:continue
  if p.name=='view-model.json.gz'or('views'in p.parts and p.suffix=='.png'):continue
  files.append(p)
files +=[PDF,R/'docs/b-v4-overlap-correction/geometry.json',R/'docs/b-v4-overlap-correction/revision.json',R/'docs/b-v4-overlap-correction/verification.json']
files +=[R/p for p in proof['tools_sha256']]
files +=list(R.glob('tools/*a_detail_v1*.py'))+list(R.glob('tools/*c_detail_v1*.py'))
# Historical source inputs are referenced by hash; do not duplicate game assets or uploaded official PDF.
files=list(dict.fromkeys(files));(O/'SHA256SUMS.txt').write_text('\n'.join(f'{sha(p)}  {p.relative_to(R)}'for p in sorted(files))+'\n')
with zipfile.ZipFile(ZIP,'w',zipfile.ZIP_DEFLATED,compresslevel=9)as z:
 for p in files+[O/'SHA256SUMS.txt']:z.write(p,p.relative_to(R))
with zipfile.ZipFile(ZIP)as z:assert z.testzip()is None
print(json.dumps({k:proof[k]for k in['pdf_pages','design_views_embedded','integration_checks','integration_failed','protected_files','runtime_walk_tests','defined_network_floor_surfaces']},ensure_ascii=False));print('PDF_BYTES',PDF.stat().st_size,'ZIP_BYTES',ZIP.stat().st_size,'ZIP_FILES',len(files)+1)
