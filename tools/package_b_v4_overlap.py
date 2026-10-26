"""Validate PDF, protect game sources, and deliver the design-only v4.1 package."""
from pathlib import Path
import json,hashlib,csv,zipfile,subprocess,shutil,collections
import fitz
R=Path(__file__).resolve().parents[1];O=R/'docs/b-v4-overlap-correction';B=R/'docs/b-purpose-review-v4';F=R/'docs/b-v4-final-confirmation';P=R/'downloads/FIND_YOURSELF-B-v4.1-Overlap-Correction.pdf';Z=P.with_suffix('.zip');BASE='38a6391c4383fc7a91f3dc4b8fa570208d8996f9'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=json.loads((B/'geometry.json').read_text());b=json.loads((O/'geometry.json').read_text());revision=json.loads((O/'revision.json').read_text());v=json.loads((O/'verification.json').read_text());assert not v['failed'] and v['v4_checks_freshly_rerun']==7810
assert sha(B/'geometry.json')==revision['source_geometry_sha256'];assert sha(O/'geometry.json')==revision['corrected_geometry_sha256']==v['corrected_geometry_sha256']
# Apply exactly the delivered six-operation patch. No generator at runtime is needed to fix the floor.
import copy
patched=copy.deepcopy(a);patch=json.loads((O/'geometry.patch.json').read_text());assert len(patch)==6
for op in patch:
 assert op['op']=='replace';keys=op['path'].strip('/').split('/');assert len(keys)==3 and keys[0]=='floors'and keys[2]in['residual','floor_plate'];patched['floors'][int(keys[1])][keys[2]]=op['value']
assert patched==b
protected=json.loads((B/'game-file-hashes.json').read_text());assert all(sha(R/path)==h for path,h in protected.items())
# Earlier source materials, game resources and old tools all remain unchanged.
changed=subprocess.check_output(['git','diff','--name-only',BASE,'--','scripts','scenes','assets','project.godot','export_presets.cfg','docs/b-purpose-review-v4','docs/b-v4-final-confirmation','tools/design_b_v4.py','tools/draw_b_v4.py','tools/review_b_drawings.py'],cwd=R,text=True).splitlines();assert not changed,changed
# Unchanged reference tables are explicitly named rather than silently recalculated with changed store IDs.
for n in['tenant-ledger.csv','equipment-register.csv','space-register.csv','store-internal-routes.csv']:
 shutil.copyfile(B/n,O/('unchanged-v4-'+n))
shutil.copyfile(F/'local-finish-schedule.csv',O/'unchanged-v4-final-finish-schedule.csv')
# Protect every previously tracked game file, including ones not in the prior 238-file manifest.
tracked=subprocess.check_output(['git','ls-files','scripts','scenes','assets','project.godot','export_presets.cfg'],cwd=R,text=True).splitlines();expected={p:hashlib.sha256(subprocess.check_output(['git','show',f'{BASE}:{p}'],cwd=R)).hexdigest()for p in tracked};assert all(sha(R/p)==h for p,h in expected.items())
(O/'protected-game-hashes.json').write_text(json.dumps(expected,ensure_ascii=False,indent=2))
d=fitz.open(P);textall='';pageproof=[];preview=Path('/tmp/b-v4-overlap-pdf-preview');preview.mkdir(exist_ok=True)
for i,p in enumerate(d):
 p.get_pixmap(matrix=fitz.Matrix(.32,.32)).save(preview/f'{i+1:02}.png');textall+=p.get_text();bad=[]
 for block in p.get_text('dict')['blocks']:
  if block['type']!=0:continue
  for line in block['lines']:
   for sp in line['spans']:
    rect=fitz.Rect(sp['bbox'])
    if rect.x0<0 or rect.y0<0 or rect.x1>p.rect.width or rect.y1>p.rect.height:bad.append(sp['text'])
 assert not bad,(i+1,bad)
 pageproof.append({'page':i+1,'title':d.get_toc()[i][1],'rendered':True,'text_within_sheet':True})
assert len(d.get_toc())==len(d)
for f in b['floors']:
 for s in f['stores']:assert s['id']in textall,s['id']
assert '8,377'in textall and '7,810'in textall
warnings=fitz.TOOLS.mupdf_warnings();assert not warnings,warnings
# Contact sheet, every page, for visual review. Full-resolution samples are stored outside the repository.
contact=fitz.open();pp=contact.new_page(width=1200,height=((len(d)+3)//4)*220)
for i,p in enumerate(d):
 x=(i%4)*300;y=(i//4)*220;pp.insert_image(fitz.Rect(x,y,x+294,y+194),pixmap=p.get_pixmap(matrix=fitz.Matrix(.20,.20)));pp.insert_text((x+4,y+210),str(i+1),fontsize=12)
pp.get_pixmap().save('/tmp/b-v4-overlap-contact.png')
for i in[2,3,14,17,18,22]:
 if i<len(d):d[i].get_pixmap(matrix=fitz.Matrix(.85,.85)).save(preview/f'{i+1:02}-large.png')
# A readable delivery report independent of PDF layout.
comparison=json.loads((O/'comparison.json').read_text())
report='''# FIND YOURSELF B館 v4.1 — 重複修正・再検査\n\n**図面・設計データのみ。Godot本体は変更せず、最終承認待ちで作業終了。**\n\n## 読む順番\n1. `downloads/FIND_YOURSELF-B-v4.1-Overlap-Correction.pdf`：修正内容→各階の全体/店舗拡大→10mm角の前後比較→開口/乗降口→検査→店舗座標台帳。\n2. `comparison.csv/json`：修正前後の面積。\n3. `geometry.json`：修正済み設計データ。実装時の自動補正に任せない。\n4. `geometry.patch.json`：元v4からの6操作だけの差分。元資料は上書きしていない。\n5. `removed-components.csv/geojson`：局所削除の正確な座標。`added-components.csv/geojson`：構造床板の局所補完。Local X/Z、単位m。地理座標ではない。\n6. `checks.json` / `check-summary.csv` / `verification.json`：今回の再検査結果。\n7. `route-paths.json`：188店舗から3階段核への564件の2Dサンプル経路。ゲームの実歩行ログではない。\n8. `unchanged-v4-*.csv`：変更しなかった店舗・設備・用途・店内経路・壁面仕上げの台帳。\n\n## 修正範囲\n- 全階の閉鎖帯 residual：共用床、店舗区画、設備核、吹き抜け、機械開口との交差を設計座標で削除。\n- 全階の構造床板 floor_plate：機械開口に入る微小端部を削り、既存共用床の下にある同じ主要2箇所の欠けを補完（各階計0.001813088㎡）。\n- それ以外の全JSONフィールドは変更なし。建物、通路、入口、区画、3広場、吹き抜け、エスカレーター、設備、他館端点を保持。\n- 修正済みデータの識別子はrevision.jsonの `B-v4.1-overlap-correction`。geometry.json内部の旧version文字列は他のデータとともに保持。\n\n## 面積比較\n|階|共用床/閉鎖帯：前㎡|後㎡|床板/機械開口：前㎡|後㎡|公開床下の床板欠け：前㎡|後㎡|\n|---|---:|---:|---:|---:|---:|---:|\n'''
for m in comparison:report+=f"|{m['floor']}F|{m['residual_public_before_m2']:.9f}|{m['residual_public_after_m2']:.9f}|{m['floor_plate_shaft_before_m2']:.9f}|{m['floor_plate_shaft_after_m2']:.9f}|{m['public_without_plate_before_m2']:.9f}|{m['public_without_plate_after_m2']:.9f}|\n"
report+='''\n## 再検査と限界\n- 旧v4検査7,810項目を修正版JSONに対して今回再計算。図面の生成・店舗の自動廃止処理は実行していない。\n- 追加検査を含め8,377項目、合格8,377・不合格0。共用床と閉鎖帯は全階の計算値0㎡。閉鎖帯/開口の追加判定許容は1e-8㎡。\n- 補完の主要成分は各階同じ2箇所。CSV/GeoJSONには数値許容未満の浮動小数点成分も省かず記録。\n- 浮動小数点のため他の界面に1e-13～1e-18㎡程度の残差がある。新しい許容は施工上の重複・隙間の許可ではない。\n- 既存の店舗/共用床界面は従来基準0.06㎡を保持（最大約0.006318㎡）。店舗区画と入口を勝手に変えていない。店舗間交差0.02㎡、店内経路0.025㎡も従来通り。すべての意図的な図形交差が数学的に0という主張ではない。\n- 主188＋副3の店舗入口、設備・乗降口、全店舗から階段核への経路を確認。1m格子と正確な線分判定を使用し、共用歩行域に半径0.45mの余裕を取る。Godotで歩いた結果ではない。\n- 元v4、前回最終確認資料とゲームのファイルは維持。今回の新規ファイルはdocs/downloads/toolsの設計用だけ。\n\n## 今後に残す項目\nGodot実装後の実歩行、コリジョン、床継ぎ目、階段・エスカレーター動作、手すり、ガラス視認性、梁下、NPC/猫/宝箱経路、ソナー、案内図、ファストトラベル、セーブ、描画負荷は未検証。N-W/M-E2の単調さと3広場の視覚体験も実装後に確認する。\n今回の提出後は実装に進まない。最終承認はユーザーが行う。\n'''
(O/'README.md').write_text(report)
# Prove all source inputs and delivered corrected files correspond.
proof={'design_only':True,'game_modified':False,'source_commit':BASE,'source_geometry_sha256':sha(B/'geometry.json'),'corrected_geometry_sha256':sha(O/'geometry.json'),'pdf_sha256':sha(P),'pdf_pages':len(d),'all_pages_rendered':True,'all_store_ids_in_pdf':True,'pdf_has_raster_game_screenshots':False,'six_operation_patch_matches_corrected_geometry':True,'previous_materials_changed':changed,'protected_game_files_current_tracked':len(expected),'protected_game_files_previous_manifest':len(protected),'checks_freshly_rerun':v['total_assertions'],'failed_checks':len(v['failed']),'runtime_walking_tests':0,'page_checks':pageproof,'source_hashes':{p:sha(R/p)for p in['tools/design_b_v4.py','tools/review_b_drawings.py','tools/draw_b_v4.py','tools/correct_b_v4_overlap.py','tools/check_b_v4_overlap.py','tools/draw_b_v4_overlap.py','tools/package_b_v4_overlap.py']}}
(O/'delivery-verification.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2))
files=[p for p in O.rglob('*')if p.is_file()and p.name!='SHA256SUMS.txt']+[P]+[R/p for p in proof['source_hashes']]+[B/'geometry.json',B/'checks.json',B/'game-file-hashes.json']
(O/'SHA256SUMS.txt').write_text('\n'.join(f'{sha(p)}  {p.relative_to(R)}'for p in sorted(files))+'\n')
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=9)as z:
 for p in files+[O/'SHA256SUMS.txt']:z.write(p,p.relative_to(R))
with zipfile.ZipFile(Z)as z:assert z.testzip()is None
print(json.dumps({k:proof[k]for k in['pdf_pages','checks_freshly_rerun','failed_checks','protected_game_files_current_tracked','six_operation_patch_matches_corrected_geometry','runtime_walking_tests']},ensure_ascii=False));print('PDF bytes',P.stat().st_size,'ZIP bytes',Z.stat().st_size)
