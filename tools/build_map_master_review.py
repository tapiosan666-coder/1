#!/usr/bin/env python3
"""Publish B structure review: actual game captures, authored plans and QA evidence."""
from pathlib import Path
import json,io,re,zipfile,hashlib
import build_review as r
ROOT=Path(__file__).resolve().parents[1]
STEM='FIND_YOURSELF-v0.24-Map-Review'
OUT=ROOT/'downloads'
r.PAGES=[];r.REV='v0.24';r.VERSION='0.24.0'
verification=json.loads((ROOT/'docs/map-master-verification.json').read_text())
assert all(item['exit']==0 for item in verification['suites']), 'Resolve or explicitly report failing verification before publishing this completion review'
manifest=json.loads((ROOT/'docs/map-master-captures.json').read_text())
r.CAPTURES={c['id']:{'image':Path(c['path']).name,'caption':c['caption']} for c in manifest['captures']}
f=r.figure;p=r.para;t=r.table;page=r.page;two=r.twocol;aside=r.callout;bullets=r.bullet
maps={i:ROOT/f'docs/images/mall24-b-{i}f.png' for i in (1,2,3)}
site=ROOT/'docs/images/mall24-site.png'
page('B館の先行改修 / 2026年10月26日','FIND YOURSELF',f('b-light-1f','B館1階・光の広場。実際のゲームで上階と昇降口を見上げた画面。','hero')+'<div class="cover-bottom"><div class="version">v0.24<span>マップ構造の改修・比較資料</span></div>'+p('B館1〜3階の骨格を優先。<br>全館・全店・15フロアの完成報告ではありません。')+'</div>','v0.23との比較 / 3館の完成構想 / B館1〜3階の実装・検証', 'cover')
page('施工前の比較と判断','「広くする」だけでは、巨大モールには見えない。',t(['現行v0.23の問題','今回の対応','次工程に残ること'],[['B本体は東西約306m。主軸＋南側副回廊が中心','東側接続を維持し西へ拡張。北側にも連続回廊','回廊沿いの店舗・設備・目的地の密度'],['細い連続開口が店前の床で削られ、広い吹き抜けに見えにくい','楕円・円・角丸長方形の3つの大開口へ。2/3Fで一致','各広場固有の仕上げ・什器・催事デザイン'],['壁や広い床に対し、人の尺度となる入口・滞留施設が少ない','既存39売場の入口・内装・人員を新配置へ移設','入口幅/店の奥行きの多様化、店舗の分割・統合'],['全10/15階層。Aは三角回遊でなく、C上階も部分実装','今回はB館1〜3階を優先。A・Cの売場を保護','不足5階層、A三辺回遊、C独立棟群、エレベーター']])+aside('今回の設計値は実在施設の寸法ではありません','添付の500×160m、通路12/8/7mなどは参考値です。実装はB本体約508×145m、主軸16m、南北回廊14m、分岐10mから試験しています。扉・棚・人物を一律拡大する処理ではありません。'),'添付詳細設計書とSVGは構想・指針として保存。既存のGodotゲーム、NPC管理、スキャン・APを維持。')
page('同じゲームの実画面比較','B館1階：分断された開口から、独立した大広場へ。',two('<figure><img src="'+r.image_uri(ROOT/'docs/screenshots/review23-b-1f.png')+'"><figcaption>実画面 / v0.23。時の広場付近。撮影位置は右図と異なります。</figcaption></figure>',f('b-time-1f','実画面 / v0.24。時の広場。円形開口と屋根の採光部。'))+p('建物が移設・拡張されているため、同一座標を比較していません。人物は1000人・同じシード912で、動きを停止。建築・照明・材質は通常のゲームと同じです。')+aside('これは骨格の改修です','長い回廊沿いには未施工の店舗・サービス区画が多く残ります。完成した内装の密度や実写品質に到達したという報告ではありません。'))
page('全体配置 / 実装済みの範囲','3館の位置関係と連絡。',r.mapfig(site,'現在の床データから作図。1階の床＋2階橋。実画面ではありません。')+p('A館＝東、B館＝西、C館＝図の上側。A/Bの1F歩道・2F橋を維持。B/Cの2F橋はX=-442を維持し、新しい北回廊へ取り付ける。Cの店舗・中庭は維持。'),cls='site')
for level,shot in [(1,'b-main'),(2,'b-north-2f'),(3,'b-south-3f')]:
 page('B館 / 全通路と既存売場の上面図',f'{level}階：全体の配置',r.mapfig(maps[level],f'{level}Fの全床・全13売場・3広場・上下対。図面はPDF/HTMLで拡大可能。')+p('本体約508×145m。主軸16m、南北回廊14m、分岐10m。B館の地下・屋上・通常階段・エレベーターは未施工。'),'床・案内図・衝突は同じポリゴン定義を使用。実在施設の測量図ではありません。','site')
 page('B館 / 通常のプレイヤー視点',f'{level}階：移動と既存の売場',two(f(shot),t(['項目','今回の状態'],[['既存売場','13 / 各階用途は従来通り'],['階高',f'{[0,5.525,10.875][level-1]:g}m（床面）'],['回遊路','主軸16m / 南北14m / 分岐10m'],['昇降','3広場に上下対。1↔2Fと2↔3F'],['B館内トイレ・階段・EV','この段階では未施工']])+aside('長い回廊の仕上げは未完成','既存店舗を移設した骨格先行版です。空区画や壁を新しい営業店舗として数えていません。')),'1000人・標準画質。撮影中だけ人物の動作とHUDを停止/非表示。建築・材質の差し替えなし。')
page('3つの吹き抜け / 形状と上下の見通し','光・時・翼で、大空間の輪郭を変える。','<div class="gallery">'+f('b-light-1f')+f('b-light-3f')+f('b-wing-1f')+f('b-wing-3f')+'</div>'+p('名目開口：光35×28mの楕円、時は直径30m、翼35×30mの角丸長方形。縁のエスカレーターと踊り場は開口内の一部を使います。2/3Fの開口は一致。屋根にも実際の採光開口とガラス・骨組みがあります。'))
page('上下移動と周回路への接続','乗った先で、回廊・店へ出られるか。',two(f('b-time-3f')+f('bc-junction'),t(['接続','今回の実装'],[['B館のエスカレーター','3広場 × 2階間 × 上下2本＝12本'],['A館の既存8本','今回の回帰検証に含める'],['NPC・猫','上り/下りを分けた経路。既存の探索・射程を維持'],['B1/RF','B館は未施工。地図上も未実装'],['通常階段・EV','B館は未施工。次のサービス核工程で追加']])+aside('実歩行の検査','昇降機の端点だけでなく、上階到着後に広場周回路・店舗まで移動する検査を行っています。ジャンプやワープで障害を飛び越える検査ではありません。')))
page('既存売場とゲーム機能','入口・陳列・個別のNPCを維持。',two(f('b-store')+f('map-2f'),bullets(['B館は既存の13売場×3階＝39。全館101売場を維持。','階ごとの家電・家具・映画、服飾・書籍・ホビー等の用途を維持。','店舗位置、陳列、衝突、店員、看板に同じ配置変換を使用。','1000人/300人、初期スキャナー、AP、猫、宝箱10個、訪問済み移動20地点は維持。','本物はラン開始時に固定。銃/猫/特殊は位置通知、初期スキャナーが最終確認。'])+aside('次に必要な店舗設計','間口6/10/18/30mなどの複数モジュール、奥の売場・バックヤード、角地と二層店舗、トイレ・休憩・フードコートの動線を作る。75/75/65店という目標の達成はまだです。')))
qa=verification['suites'];passed=[q for q in qa if q['exit']==0];failed=[q for q in qa if q['exit']!=0]
page('動作確認 / 実施したことと測っていないこと','経路だけでなく、実際の床と移動を確認。',t(['検査','結果・範囲'],[['テストスイート',f'{len(passed)}/{len(qa)}組成功、失敗{len(failed)}組。詳細JSONを同梱'],['個別検査',f"{sum(q.get('checks') or 0 for q in qa):,}項目。失敗{sum(q.get('failures') or 0 for q in qa)}項目"],['ナビゲーション',f"{verification['world']['nav_points']:,}点、全点接続。孤立0"],['床・水平接続',verification['floor_audit']],['通常移動',verification['movement_summary']],['NPC・猫・宝箱・案内',verification['systems_summary']],['実描画','Godot 4.6.3 / Compatibility / Linux・Mesa llvmpipe / 標準画質']])+aside('未測定','Windows実機での操作、RTX 4060 LaptopのFPS、5000人時の性能、混雑時の動線、3時間の実プレイ時間は未測定です。スクリーンショット用の停止状態を性能測定として扱いません。'))
page('完成構想 / 今後の順序','残る5階層と、商業施設としての密度。',t(['階','A：三角回遊（改修予定）','B：長大な3広場','C：屋外棟群（拡張予定）'],[['B1','食品・惣菜・搬入を分離','駐車・食品・倉庫・設備','地下駐車・倉庫'],['1F','大型店と三つの角広場','服飾・スポーツ・催事・総合案内','中庭とアウトレット'],['2F','服飾・美容・近道','書籍・生活・カフェ・到着ロビー','テラス・雑貨・連絡橋'],['3F','キッズ・ホビー・飲食','映画・体験・ファミリー','屋内売場＋屋外デッキ'],['RF','庭園と設備','屋上テラス・イベント・設備','散策庭園・展望・設備']])+bullets(['次：B館の店舗配置とトイレ/通常階段/エレベーター等のサービス核。','続いてA館の三辺回遊・角広場、C館の独立棟群と上下街路。','B地下/屋上・C地下/3階/屋上を追加して15階層へ。','42探索区画の人数別閉鎖は新機能として別検証。現在の探索範囲を黙って狭めない。','最後にLOD・シーン分割・5000人の性能を実測し、密度と距離を調整。']),'表は将来計画です。今回の配布物は10/15階層。Aの三角回遊、Bの多数店舗、全施設の完成とは区別してください。')
html=r.html_document().replace('v0.23','v0.24').replace('全30ページ',f'全{len(r.PAGES)}ページ').replace('href="#p7">全体マップ','href="#p4">全体マップ').replace('href="#p9">各フロア','href="#p5">各フロア').replace('href="#p25">完成版の構想',f'href="#p{len(r.PAGES)}">完成版の構想')
OUT.mkdir(exist_ok=True);(OUT/(STEM+'.html')).write_text(html)
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
 tab=browser.new_page(viewport={'width':1280,'height':900});tab.set_content(html,wait_until='load');tab.evaluate('document.fonts.ready')
 over=tab.evaluate("Array.from(document.querySelectorAll('.page')).filter(p=>Math.max(...Array.from(p.querySelector('.body').children).map(c=>c.getBoundingClientRect().bottom))>p.querySelector('.footer').getBoundingClientRect().top-8).map(p=>p.id)")
 broken=tab.evaluate("Array.from(document.images).filter(i=>i.id!=='full'&&(!i.complete||!i.naturalWidth)).map(i=>i.alt)")
 assert not over,over
 assert not broken,broken
 tab.pdf(path=str(OUT/(STEM+'.pdf')),print_background=True,prefer_css_page_size=True)
 tab.emulate_media(media='print');tab.locator('#p5').screenshot(path='/tmp/fy024-report-floor.png');browser.close()
from pypdf import PdfReader,PdfWriter
reader=PdfReader(OUT/(STEM+'.pdf'));writer=PdfWriter();writer.clone_document_from_reader(reader)
for i,pg in enumerate(r.PAGES):writer.add_outline_item(pg['title'],i)
writer.add_metadata({'/Title':'FIND YOURSELF v0.24 — モール構造の改修・比較','/Subject':'現状比較、B館1〜3階の構造実装、実画面と検証結果'})
buffer=io.BytesIO();writer.write(buffer);(OUT/(STEM+'.pdf')).write_bytes(buffer.getvalue())
assert len(PdfReader(OUT/(STEM+'.pdf'),strict=True).pages)==len(r.PAGES)
with zipfile.ZipFile(OUT/(STEM+'.zip'),'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for suffix in ('pdf','html'):z.write(OUT/(STEM+'.'+suffix),'B館改修資料.'+suffix)
 z.writestr('お読みください.txt','PDFで比較と結果を確認できます。HTMLは画像クリックで拡大できます。画像・図面・設計書・検証JSONも同梱。ゲーム本体は別のSource.zipです。\n')
 for c in manifest['captures']:z.write(ROOT/c['path'].replace('res://',''),'screenshots/'+Path(c['path']).name)
 for path in list(maps.values())+[site]:z.write(path,'images/'+path.name)
 z.write(ROOT/'docs/screenshots/review23-b-1f.png','screenshots/review23-b-1f.png')
 z.write(ROOT/'docs/images/mall23-b-2f.png','images/mall23-b-2f.png')
 for path in (ROOT/'docs/reference/map-master-v1').glob('*'):z.write(path,'reference/map-master-v1/'+path.name)
 for name in ['MAP_MASTER_PLAN.md','MAP_MASTER_IMPLEMENTATION.md','map-master-verification.json','map-master-movement.json','map-master-captures.json','map-master-floor-plans.json','map-master-dimensions.json']:z.write(ROOT/'docs'/name,name)
 z.write(ROOT/'third_party/noto-cjk-COPYRIGHT.txt','licenses/noto-cjk-COPYRIGHT.txt')
with zipfile.ZipFile(OUT/(STEM+'.zip')) as z:assert z.testzip() is None
sums=[]
for suffix in ('pdf','html','zip'):
 path=OUT/(STEM+'.'+suffix);sums.append(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n');print(path.name,path.stat().st_size,flush=True)
(OUT/(STEM+'-SHA256SUMS.txt')).write_text(''.join(sums))
print('MAP_REVIEW_COMPLETE',len(r.PAGES),'pages',flush=True)
