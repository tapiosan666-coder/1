"""Revised vector plans and local overlap comparisons. Documentation only."""
from pathlib import Path
import sys,json,math,ast,collections
sys.path.append('/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
import fitz
from shapely.geometry import shape,Polygon,Point,LineString,box
from shapely.ops import unary_union
R=Path(__file__).resolve().parents[1];O=R/'docs/b-v4-overlap-correction';B=R/'docs/b-purpose-review-v4';FONT=R/'assets/fonts/NotoSansCJKjp-Regular.otf';INK=(.12,.22,.26);MUTED=(.34,.42,.45);RED=(.72,.23,.16)
def dec(v):
 if isinstance(v,dict):return shape(v)if'type'in v and('coordinates'in v or'geometries'in v)else{k:dec(x)for k,x in v.items()}
 if isinstance(v,list):return[dec(x)for x in v]
 return v
D=dec(json.loads((O/'geometry.json').read_text()));OLD=dec(json.loads((B/'geometry.json').read_text()));FLOORS=D['floors'];CORES=D['cores'];ALL_ESC=D['escalators'];VOIDS=[p['void']for p in D['plazas']];PLAZAS=D['plazas'];ROUTES=D['routes'];metrics=json.loads((O/'comparison.json').read_text());verify=json.loads((O/'verification.json').read_text());changes=dec(json.loads((O/'changes.json').read_text()));doc=fitz.open();TOC=[]
# Load pure vector helpers only, then the pure v4 plan function. No generation scripts are imported.
for file,names in[(R/'tools/review_b_drawings.py',{'polys','drawg','line','dot','text','viewmap'}),(R/'tools/draw_b_v4.py',{'plan'})]:
 src=file.read_text()
 for n in ast.parse(src).body:
  if isinstance(n,ast.FunctionDef)and n.name in names:
   s=ast.get_source_segment(src,n)
   if n.name=='viewmap':s=s.replace("f'AT-{j+1}'","['P-W','P-T','P-L'][j]")
   exec(compile(s,'pure_vector_helper','exec'),globals())
old_viewmap=viewmap

def page(title,sub='',w=1684,h=1000):
 p=doc.new_page(width=w,height=h);p.insert_font(fontname='jp',fontfile=str(FONT));text(p,40,42,title,22);text(p,40,68,sub,10,MUTED);p.draw_line((40,82),(w-40,82),color=(.2,.48,.43));text(p,40,h-22,f'FIND YOURSELF / B館 v4.1 重複修正 / 図面のみ・ゲーム未改修 / 2026-10-26  •  {len(doc):02}',9,MUTED);TOC.append([1,title,len(doc)]);return p

def paragraphs(p,items,x=45,y=115,size=14,gap=16,width=None):
 width=width or p.rect.width-x-45;font=fitz.Font(fontfile=str(FONT))
 for item in items:
  current=''
  for ch in item:
   if ch=='\n' or font.text_length(current+ch,fontsize=size)>width:
    text(p,x,y,current,size);y+=size*1.6;current=''if ch=='\n'else ch
   else:current+=ch
  if current:text(p,x,y,current,size);y+=size*1.6
  y+=gap
 return y

def scale_bar(p,xy,at,length):
 x,z=at;a=xy((x,z));b=xy((x+length,z));p.draw_line(a,b,color=INK,width=2);p.draw_line((a.x,a.y-4),(a.x,a.y+4),color=INK);p.draw_line((b.x,b.y-4),(b.x,b.y+4),color=INK);text(p,a.x,a.y+17,f'{length}m',9)

p=page('B館 v4.1｜設計データの重複解消','v4の基本構造を保持した局所修正版。承認前のGodot本体の変更は行っていません。',w=1191,h=842)
paragraphs(p,[
'共用床と閉鎖帯の交差を3階すべてで解消しました。共用床を動かさず、閉鎖帯から競合部分を差し引いた修正済み座標データを提出します。実装時の自動補正に任せる方式ではありません。',
'変更は各階の residual（閉鎖帯）と floor_plate（構造床板）の2項目、合計6項目のみです。閉鎖帯は共用床・店舗区画・設備核・吹き抜け・機械開口を優先して局所的に削りました。床板は機械開口の縁の微小な侵入を削り、既存共用床の下の微小な欠けを補完しました。',
'建物外形、共用通路、3広場、店舗区画、入口、吹き抜け、エスカレーター、乗降口、設備核、案内・家具・他館接続を変更前後で照合し、座標データの一致を確認しています。店舗数は65／66／57、計188区画を保持します。',
f"既存v4の図面検査7,810件を修正版データに対して再実施しました。追加の局所修正・保存条件・独立検査を含む全{verify['total_assertions']:,}件で不合格0です。前回の合格記録をコピーした集計ではありません。",
'図面上の検査であり、Godotの実歩行・コリジョン・群衆・描画負荷は未検証です。これらは承認後の実装段階に残します。今回の作業は修正図面と再検査資料の提出で終了します。'],size=15,gap=20)
p=page('修正前後の面積と、変更したデータ','新しい通路・店舗入口・部屋・広場を追加していません。面積の単位は㎡。',w=1191,h=842)
y=125
for m in metrics:
 text(p,45,y,f"{m['floor']}F  共用床 / 閉鎖帯",17);y+=30
 text(p,45,y,f"修正前 {m['residual_public_before_m2']:.9f} → 修正後 {m['residual_public_after_m2']:.9f}",15);y+=29
 text(p,45,y,f"閉鎖帯の全削除面積 {m['residual_removed_m2']:.9f} / 床板の機械開口競合削除 {m['floor_plate_removed_m2']:.9f}",12);y+=46
paragraphs(p,[
'閉鎖帯の全削除面積には、共用床だけでなく、同じ境界計算で生じていた店舗・機械開口との微小交差も含みます。重なる面を二重に足し合わせず、削除形状の和集合面積で記録しています。',
'床板は吹き抜け形状を変えず、固定済みのエスカレーター床開口に侵入する端部だけを局所的に除去。床厚・階高・開口輪郭・機器位置は変更していません。',
'計算は配布元JSONの座標で直接差分を取り、新たな丸め・スナップ・全体バッファは使いません。床板の補完は全階同じ主要2成分、各階合計0.001813088㎡で、既存の共用床の範囲内に限ります。微小な島状・細長い図形が含まれるため、一般図では線幅より小さく見えます。後続の10mm角拡大図と座標台帳を併用してください。',
'新しいゼロ交差検査の数値許容は1×10⁻⁸㎡。共用床との交差は3階とも計算値0です。一部の別界面に10⁻¹³～10⁻¹⁸㎡程度の浮動小数点残差があります。施工上許す隙間や重複の寸法を示す値ではありません。'],y=y+10,size=12,gap=16)
# Revised floor plans and full storefront details, using the delivered corrected polygons.
for f in FLOORS:
 p=page(f"B館 {f['floor']}F｜修正済み全体平面",f"床高 +{f['height']:.3f}m / 店舗{len(f['stores'])}区画 / 主軸16m・枝道9m・設備前8m / 同梱geometry.jsonの座標")
 xy,sc=plan(p,f,(-45,-95,610,195),(50,105,1634,850),False,True)
 # Locator rings are explicitly not the scale of the removed area.
 for ch in changes:
  if ch['floor']!=f['floor']:continue
  parts=sorted(polys(ch['removed_geometry']),key=lambda q:q.area,reverse=True)[:3]
  for q in parts:
   pp=xy(q.representative_point().coords[0]);p.draw_circle(pp,5,color=RED,width=.8)
 scale_bar(p,xy,(-30,176),50)
 paragraphs(p,['赤い円は局所修正の主要位置を示す目印で、削除面積の大きさではありません。閉鎖帯を削り、共用床を保持。床板欠けは局所補完。',
 '図の茶＝バックルーム、青＝店舗、薄灰＝閉鎖帯、緑＝機器/乗降床、赤点＝店舗入口。正確な削除位置はremoved-components.csv / GeoJSON。',
 '店舗・広場・通路の全体形状、他館連絡端点、入口幅と位置はv4から変更していません。'],x=55,y=895,size=11,gap=8)
 for k,(lo,hi)in enumerate([(-40,170),(160,355),(345,535)],1):
  p=page(f"B館 {f['floor']}F｜修正済み店舗・共用部拡大 {k}",'店ID・入口・店内主路・棚配置帯・バックルームを表示。閉鎖帯/構造床だけを局所修正。')
  xy,sc=plan(p,f,(lo,0,hi,195),(50,105,1634,890),True,True);scale_bar(p,xy,(lo+5,188),10)
  text(p,55,948,'通常店入口2.4m、核店6m。これらの寸法と区画座標はv4から変更していません。精密な入口座標は同梱台帳。',11)
# Local true-scale comparisons: same 10mm x 10mm cutout before/after, no nonuniform stretch.
locators=[]
def micro(p,f,before,after,conflict,rect,centre,caption,show_before):
 rr=fitz.Rect(rect);cx,cz=centre;extent=(cx-.005,cz-.005,cx+.005,cz+.005);sc=min(rr.width,rr.height)/.01;clip=box(*extent);xy=lambda q:fitz.Point(rr.x0+(q[0]-extent[0])*sc,rr.y0+(q[1]-extent[1])*sc)
 drawg(p,clip,xy,(.99,.99,.98),(.6,.65,.65),.5)
 drawg(p,f['public'].intersection(clip),xy,(.80,.91,.94),(.4,.6,.65),.3)
 drawg(p,(before if show_before else after).intersection(clip),xy,(.8,.76,.64),(.3,.3,.25),.6)
 if show_before:drawg(p,before.intersection(conflict).intersection(clip),xy,(.96,.42,.32),RED,.3)
 for k in range(1,5):
  z=rr.y0+k*rr.height/5;x=rr.x0+k*rr.width/5;p.draw_line((rr.x0,z),(rr.x1,z),color=(.5,.58,.6),width=.15,dashes='[1 3]');p.draw_line((x,rr.y0),(x,rr.y1),color=(.5,.58,.6),width=.15,dashes='[1 3]')
 text(p,rr.x0,rr.y1+18,caption,10)
for f,bf in zip(FLOORS,OLD['floors']):
 p=page(f"{f['floor']}F｜共用床と閉鎖帯の局所比較",'各ペアは同じ位置の10mm×10mm、縦横同一倍率。点線間隔2mm。赤＝修正前の交差、青＝保持する共用床、茶＝閉鎖帯。')
 overlap=bf['residual'].intersection(bf['public']);parts=sorted(polys(overlap),key=lambda q:q.area,reverse=True)[:3]
 for i,q in enumerate(parts):
  c=q.representative_point();cx,cz=c.x,c.y;y=130+i*255;locators.append({'floor':f['floor'],'kind':'residual/public','case':i+1,'centre_local':[cx,cz],'extent_m':.01,'source_component_area_m2':q.area})
  micro(p,f,bf['residual'],f['residual'],bf['public'],(50,y,260,y+210),(cx,cz),'修正前：交差帯を赤で表示',True)
  micro(p,f,bf['residual'],f['residual'],bf['public'],(300,y,510,y+210),(cx,cz),'修正後：共用床側の交差を除去',False)
  text(p,570,y+30,f"例{i+1}  Local X={cx:.9f}, Z={cz:.9f}",13)
  text(p,570,y+62,f"World X={cx-714:.9f}, Z={cz-30:.9f}",12)
  text(p,570,y+94,f"元の連結交差成分 {q.area:.9f}㎡（画面内だけの面積ではありません）",12)
  text(p,570,y+126,'開口を増設せず、公開床の座標を固定したまま閉鎖側だけ削除。',12)
  text(p,570,y+158,'10mm角の拡大図は人間の視点画像ではありません。',11,MUTED)
 text(p,55,948,'全交差成分と削除形状は機械可読データに記録。ここでは各階の面積が大きい成分から3例を表示。',11)
p=page('床開口｜床板側の微小な侵入を削除','機械開口輪郭と機器位置は保持。各図10mm×10mm、縦横同一倍率・2mm点線。茶＝床板、赤＝機械開口に入った床板。')
for i,(f,bf)in enumerate(zip(FLOORS,OLD['floors'])):
 q=max(polys(bf['floor_plate'].intersection(bf['shafts'])),key=lambda x:x.area);pt=q.representative_point();y=130+i*255
 micro(p,f,bf['floor_plate'],f['floor_plate'],bf['shafts'],(50,y,260,y+210),(pt.x,pt.y),'修正前：床板が開口に侵入',True)
 micro(p,f,bf['floor_plate'],f['floor_plate'],bf['shafts'],(300,y,510,y+210),(pt.x,pt.y),'修正後：開口の輪郭まで床を除去',False)
 text(p,570,y+35,f"{f['floor']}F  Local ({pt.x:.9f}, {pt.y:.9f})",13);text(p,570,y+75,f"階全体の床板侵入：{metrics[i]['floor_plate_shaft_before_m2']:.9f} → {metrics[i]['floor_plate_shaft_after_m2']:.9f}㎡",13)
 text(p,570,y+115,'乗降床・エスカレーター開口・階高・機器寸法は同一。',12)
 locators.append({'floor':f['floor'],'kind':'floor_plate/shafts','centre_local':[pt.x,pt.y],'extent_m':.01})
text(p,55,948,'吹き抜けの床板交差は全階で修正前から0㎡。今回の床板修正は機械開口の縁に限定しています。',11)
# Slab support gaps: same two local positions on all three floors.
p=page('構造床板の微小欠け｜既存共用床の下だけ補完','共用通路の座標・幅は保持。各階に同じ主要2成分があり、合計0.001813088㎡を局所補完しました。図は1F、2/3Fも同位置。')
f=FLOORS[0];bf=OLD['floors'][0];gaps=sorted(polys(bf['public'].difference(bf['floor_plate'])),key=lambda q:q.area,reverse=True)
for i,q in enumerate(gaps):
 pt=q.representative_point();y=145+i*330
 micro(p,f,bf['floor_plate'],f['floor_plate'],Polygon(),(50,y,310,y+260),(pt.x,pt.y),'修正前：青い帯に構造床板が不足',True)
 micro(p,f,bf['floor_plate'],f['floor_plate'],Polygon(),(350,y,610,y+260),(pt.x,pt.y),'修正後：共用床の下まで床板を補完',False)
 text(p,675,y+40,f'成分{i+1} / 各図10mm角・点線2mm',14)
 text(p,675,y+80,f'Local ({pt.x:.9f}, {pt.y:.9f})',13)
 text(p,675,y+120,f'成分全体の面積 {q.area:.9f}㎡',13)
 text(p,675,y+160,'機械開口や通路の位置は動かしていません。',12)
 locators.append({'floor':'1/2/3','kind':'slab-support-gap','centre_local':[pt.x,pt.y],'extent_m':.01})
paragraphs(p,['補完形状・局所座標はadded-components.geojson / CSVに記録。数値許容未満の浮動小数点成分も省かず収録。一般図で目立つ新しい床や部屋を追加する変更ではありません。'],x=55,y=900,size=12,gap=10)

# Coordinated opening and landing sheets with the actual corrected slab shown at each court.
for pl in PLAZAS:
 p=page(pl['name']+'｜開口・回廊・乗降口の再確認','2F/3Fの吹き抜け位置、機械開口、床板、手すり、踊り場の相互関係。形状・位置はv4と一致。')
 extent=pl['court'].buffer(5).bounds
 for f,rr in zip(FLOORS,[(50,120,545,700),(595,120,1090,700),(1140,120,1635,700)]):
  xy,sc=plan(p,f,extent,rr,True,False);text(p,rr[0],105,f"{f['floor']}F +{f['height']:.3f}m",14)
 paragraphs(p,[
  '開口輪郭と上階の整合：2F/3Fの吹き抜け形状は一致。時の広場の4m横断橋は両階で同位置。1Fの広場床を上階開口として誤削除していません。',
  '床板は開口を確実に避け、共用通路を欠損させていないことを追加検査。全乗降口から共用歩行域までの図面上の到達も再検査しました。',
  '図は床/開口の投影図です。実装後の梁下、手すりの端部、機器の移動、コリジョン、プレイヤーの実歩行は未検証です。'],x=55,y=780,size=13,gap=15)
# Fresh pass/fail results, never inferred from unchanged files alone.
p=page('再検査結果｜今回実施した項目と判定','checks.jsonに全行、check-summary.csvに種別別集計、route-paths.jsonに2Dサンプル経路を収録。',w=1191,h=842)
paragraphs(p,[
 f"全検査 {verify['total_assertions']:,}件 / 合格 {verify['passed']:,}件 / 不合格 {len(verify['failed'])}件。うちv4の既存7,810項目を修正版JSONから再計算しました。再生成時の図面/店舗削除処理は実行していません。",
'重なり：閉鎖帯と共用床・店舗・設備核・吹き抜け・機械開口の交差を追加検査。新しい数値許容1×10⁻⁸㎡で全件合格。閉鎖帯・床板の有効形状、競合外を削っていないこと、共用床の範囲外に床板を増やしていないことも検査しました。',
'吹き抜け・床開口：上階開口一致、共用歩行域が開口を避けること、床板が吹き抜け/機械開口を侵さないこと、床板が公開床を覆うことを確認しました。',
'入口到達：188店舗の主入口と核店の副入口3か所を再検査。全188店舗からK1/K2/K3への564経路を、半径0.45mの余裕を取った共用域・1m格子で計算し、構成線分が同域内に収まることを確認しました。実際のプレイヤー移動を再現した検証ではありません。',
'設備・昇降：共用設備入口、トイレ/EV/階段の内部扉、全乗降口、広場接続、館間接続端点を検査。店舗の店内主路、壁/陳列との干渉、店舗同士の交差も従来基準で再検査しました。',
f"保護対象：ゲーム関連{verify['protected_game_files']}ファイルのハッシュ一致。承認済みv4資料も上書きせず、修正版geometry.jsonと差分パッチを別フォルダへ保存しています。"],size=13,gap=19)
p=page('検査基準と、今回変更しなかった既存の界面','「不合格0」は明記した検査基準についての結果です。すべての意図的な図形の交差が数学的に0という意味ではありません。',w=1191,h=842)
paragraphs(p,[
'今回の追加検査は閉鎖帯・開口の交差を1×10⁻⁸㎡未満で判定。従来の0.02㎡や0.06㎡で問題箇所を隠す方式にしていません。共用床/閉鎖帯は3階とも実計算値0㎡です。',
'既存の店舗区画/共用床界面は、v4の独立検査と同じ0.06㎡未満の基準を維持。各階の最大値は1F 0.005201㎡／2F 0.006318㎡／3F 0.006103㎡で、今回は区画座標を変更していません。店舗間交差の0.02㎡、店内主路の0.025㎡も以前と同じ基準です。これらを今回解消した交差と混同しないでください。',
'店舗の壁厚が売場や共用部の境界にかかること、床板が店舗や共用床の下を覆うこと、家具が共用床に設置されることは、用途の違う図形の意図的な関係です。「全ポリゴンを相互に非交差」にする処理はしていません。',
'今回の範囲：設計上の床・閉鎖帯・開口を修正し、公開経路の到達性と区画の保護を確認すること。店舗界面の既存許容差は実装時の境界生成で改めて検証しますが、本修正の閉鎖帯/床開口について自動補正が必要な状態で渡すことはありません。',
'数値許容・検査対象・生の実測値はJSON/CSVに記載。既存基準を緩めたり、不合格の行を集計から除いたりしていません。'],size=14,gap=22)
# Exact invariance ledger and local geometry size.
p=page('変更範囲の照合｜6ポリゴン項目のみ','geometry.patch.jsonを元v4に適用すると、提出geometry.jsonと同じデータになります。',w=1191,h=842)
paragraphs(p,[
'変更：floors/0/residual、floors/0/floor_plate、floors/1/residual、floors/1/floor_plate、floors/2/residual、floors/2/floor_plate。閉鎖帯は競合部分の局所削除、床板は開口への侵入削除と共用床の下の欠け補完です。',
'保持：建物外形・階高、共用床・歩行域・到達域、各階の店舗ポリゴン・主/副入口・幅・店内経路・棚・裏室、3広場と開口、経路網・接続点・幅、設備核、機器・乗降床・手すり、家具・案内・搬入・他館端点。JSONの他の全フィールドを一致検査しました。',
'修正は別の承認候補データに保存しました。元v4のgeometry.json、前回の最終確認PDF、既存のGodotリソースは変更しません。将来の実装は本修正版JSONを入力にする必要があります。',
'元geometry.jsonの内部version文字列は、6項目以外を変更していないことが分かるよう保持しています。修正版の正式な識別はrevision.jsonの B-v4.1-overlap-correction とデータSHA-256で行ってください。',
'前回の24壁面の仕上げ・案内指示は継続。今回、新しい装飾・通路・店舗は追加していません。旧3D画像を修正版の新しい実装結果として使い回していません。微小な境界差は、今回の正確な平面拡大図で提出します。'],size=14,gap=20)
p=page('今後の実装後に確認する項目｜今回未実施','今回の作業は図面・データ修正と再検査の提出まで。Godot本体の変更は許可されていません。',w=1191,h=842)
paragraphs(p,[
'実歩行：店舗入口191か所、全乗降口、トイレ前室、EV前、階段、横断橋、他館接続をプレイヤーが通れること。壁際の引っ掛かり、床継ぎ目、段差、落下、梁下・手すり・ガラスの視認性を確認する。',
'空間の見え方：翼・時・光への進入と退出を各階・両方向から確認。N-W/M-E2の入口が少ない区間、時の橋下面と閉鎖壁の見え方は前回の重点事項を維持する。図面の交差解消だけで楽しさや見やすさまで合格とはしない。',
'既存機能：NPC/猫の経路、宝箱の到達、ソナー、案内図、訪問済みファストトラベル、AP・スキャン・セーブの互換を確認。人数と視界に応じたフレーム時間も測定する。今回はこれらを実行していない。',
'最終承認はユーザーが行います。本修正の提出後は一旦終了し、承認前にゲーム本体へ反映しません。'],size=15,gap=24)
# All-check category table appended, making the fresh scope reviewable without parsing JSON.
summary=collections.defaultdict(lambda:[0,0])
for q in json.loads((O/'checks.json').read_text()):summary[q['kind']][0]+=1;summary[q['kind']][1]+=not q['pass_']
items=sorted(summary.items())
for start in range(0,len(items),26):
 p=page(f'再検査の種別一覧 {start//26+1}','検査種別 / 件数 / 不合格数。数値基準と個別実測値はchecks.json参照。',w=1191,h=842);y=116
 for k,(n,fail)in items[start:start+26]:text(p,45,y,k,11);text(p,820,y,n,11);text(p,980,y,fail,11);y+=25
# Updated tenant and door coordinates in a human-readable PDF appendix, plus unchanged CSV copies.
for f in FLOORS:
 for start in range(0,len(f['stores']),27):
  p=page(f"{f['floor']}F｜店舗入口座標・区画台帳 {start//27+1}",'旧ID・座標・間口・区画を保持。Local X/Z m、World X=Local X−714、Z=Local Z−30。',w=1684,h=1000);y=122
  text(p,45,100,'店舗ID                旧ゲームID          用途                          区画㎡      間口m      入口幅m      Local X          Local Z',11)
  for s in f['stores'][start:start+27]:
   text(p,45,y,s['id'],10);text(p,225,y,s.get('legacy_id','-'),10);text(p,420,y,(s.get('legacy_name')or s['category'])[:18],10);text(p,760,y,f"{s['polygon'].area:.2f}",10);text(p,880,y,f"{s['frontage_m']:.3f}",10);text(p,1000,y,s['door_width_m'],10);text(p,1130,y,f"{s['entry'][0]:.6f}",10);text(p,1310,y,f"{s['entry'][1]:.6f}",10);y+=29
  text(p,45,948,'全191入口（主188＋副3）の到達判定はchecks.json。区画の詳細は店舗拡大図、CSV台帳とgeometry.json。',11)
(O/'comparison-view-locations.json').write_text(json.dumps(locators,ensure_ascii=False,indent=2));doc.set_toc(TOC);doc.set_metadata({'title':'FIND YOURSELF B館 v4.1 重複修正・再検査','author':'FIND YOURSELF design review','subject':'Design-data correction only; Godot unchanged'});out=R/'downloads/FIND_YOURSELF-B-v4.1-Overlap-Correction.pdf';doc.save(out,garbage=4,deflate=True);print('PDF',len(doc),out)
