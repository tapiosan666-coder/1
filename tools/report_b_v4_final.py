"""Final review supplement; writes documentation only."""
from pathlib import Path
import json,sys,hashlib,csv,math
sys.path.append('/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
import fitz
from shapely.geometry import shape,Point,LineString
R=Path(__file__).resolve().parents[1];O=R/'docs/b-v4-final-confirmation';B=R/'docs/b-purpose-review-v4';a=json.loads((O/'frontage-audit.json').read_text());g=json.loads((B/'geometry.json').read_text());cams=json.loads((O/'camera-checks.json').read_text());doc=fitz.open();FONT=R/'assets/fonts/NotoSansCJKjp-Regular.otf';W,H=1191,842;INK=(.12,.19,.23);RED=(.72,.18,.12);GREEN=(.1,.4,.35)
def tx(p,x,y,s,size=12,col=INK):p.insert_font(fontname='jp',fontfile=str(FONT));p.insert_text((x,y),str(s),fontname='jp',fontsize=size,color=col)
def page(title,sub='図面・設計モデルによる確認資料｜Godot本体は未変更'):
 p=doc.new_page(width=W,height=H);tx(p,35,40,title,23);tx(p,35,65,sub,10);p.draw_line((35,77),(1156,77),color=GREEN);tx(p,35,821,'FIND YOURSELF / B館 v4 最終確認追補 / 2026-10-26',9);tx(p,1110,821,f'{len(doc):02}',10);return p
def paras(p,items,x=45,y=110,size=15,width=1070):
 for s in items:
  # Measured CJK-aware wrap; fitz textbox automatic wrapping, fixed line spacing.
  chars=max(18,int(width/size));lines=[]
  for part in s.split('\n'):
   while len(part)>chars:lines.append(part[:chars]);part=part[chars:]
   lines.append(part)
  for z in lines:tx(p,x,y,z,size);y+=size*1.7
  y+=13
 return y
def pic(p,name,rect,caption):
 f=O/'views'/f'{name}.png';p.insert_image(fitz.Rect(rect),filename=str(f));tx(p,rect[0],rect[3]+17,caption,11)
def geom(p,gg,trans,fill=None,color=(.45,.5,.52),width=.5):
 gg=shape(gg)if isinstance(gg,dict)else gg
 if gg.is_empty:return
 if gg.geom_type=='Polygon':
  sh=p.new_shape();sh.draw_polyline([trans(q)for q in gg.exterior.coords]);sh.finish(color=color,fill=fill,width=width,closePath=True);sh.commit()
  for ring in gg.interiors:
   sh=p.new_shape();sh.draw_polyline([trans(q)for q in ring.coords]);sh.finish(color=color,fill=(1,1,1),width=.3,closePath=True);sh.commit()
 elif gg.geom_type in ['LineString','LinearRing']:
  sh=p.new_shape();sh.draw_polyline([trans(q)for q in gg.coords]);sh.finish(color=color,width=width);sh.commit()
 else:
  for part in gg.geoms:geom(p,part,trans,fill,color,width)
def plan(p,f,rect=(45,120,1140,650)):
 shell=shape(f['shell']);lo,bo,hi,to=shell.union(shape(f['public'])).bounds;x0,y0,x1,y1=rect;scale=min((x1-x0)/(hi-lo),(y1-y0)/(to-bo));tr=lambda q:(x0+(q[0]-lo)*scale,y0+(q[1]-bo)*scale)
 geom(p,f['shell'],tr,fill=(.85,.85,.83));geom(p,f['public'],tr,fill=(.98,.98,.95))
 for s in f['stores']:
  geom(p,s['polygon'],tr,fill=(.81,.89,.9),color=(.25,.4,.44));x,y=tr(s['entry']);p.draw_circle((x,y),1.8,color=GREEN,fill=GREEN)
 for pl in g['plazas']:
  geom(p,pl['void'],tr,fill=(1,1,1),color=(.3,.5,.65));pt=shape(pl['void']).centroid;tx(p,*tr((pt.x,pt.y)),pl['name'],10)
 for w in a['walls']:
  if w['floor']==f['floor']:geom(p,w['line'],tr,color=(.9,.61,.15),width=1.1)
 for t in a['treatments']:
  if t['floor']==f['floor']:
   geom(p,t['line'],tr,color=RED,width=2);q=shape(t['line']).interpolate(.5,normalized=True);tx(p,*tr((q.x,q.y)),t['id'],7,RED)
 for r in g['routes']:
  if f['floor']in r['levels']:
   q=LineString(r['points']).interpolate(.5,normalized=True);tx(p,*tr((q.x,q.y)),r['id'],7)
 for c in cams:
  if c['floor']==f['floor']and c['phase']=='after':
   x,y=tr(c['actual']);p.draw_circle((x,y),2,color=(.4,.16,.65),fill=(.4,.16,.65));tx(p,x+2,y-3,c['plaza'][2:]+'-'+c['id'],6)
 tx(p,45,700,'青：店舗区画　緑点：店舗入口　橙：閉鎖帯の通路側面　赤：仕上げ追補面　紫：視点位置',12)
 tx(p,45,726,'平面・店舗区画・入口位置はv4を保持。赤は壁面仕上げの指定であり、新しい壁や空間ではありません。',12)
 tx(p,45,752,'座標：Local X/Z [m]。World X=Local X−714、World Z=Local Z−30。寸法・正確な座標は同梱CSV/元v4図面参照。',11)
p=page('B館 v4｜最終確認資料');paras(p,[
'結論：大規模な再設計は行わず、v4の平面構造を維持します。店舗数は1F 65・2F 66・3F 57、計188区画です。',
'必要な局所修正は、主要6系統の通路と時の広場南側に面する長い閉鎖壁の仕上げ・案内表示だけです。新しい通路、店舗入口、部屋、窓は追加しません。',
'58件の階別通路を確認。42件の専門店街のうち29件を数値上の重点確認候補として抽出しました。候補数は不合格数ではありません。',
'北西専門店街N-Wと東専門店街M-E2は入口の疎な区間が残ります。仕上げを足しても入口の少なさ自体は解消しません。Godot実装後に優先して実歩行評価します。',
'本資料の18視点は設計モデルの静止画です。ゲーム内の実歩行検証は実施していません。承認前にGodotのシーン・ロジック・アセットは変更しません。',
'資料の位置づけ：v4詳細平面図を置き換えない最終確認追補。構造は保持し、局所仕上げの指定と未検証項目を明確にします。'])
p=page('確認方法と、結果の読み方');paras(p,[
'通路中心線を0.5m間隔で調査。左右28mまでの最初の共用床境界を確認し、その背後0.65mが閉鎖設備帯かを分類しました。店舗や設備核の壁と、細い作図上の継ぎ目は閉鎖帯から分けています。',
'入口数は「中心線から半幅+1m以内で、入口までの直線が共用床上に収まる入口」の2D集計です。人の視線、文字の読みやすさ、ガラス反射、NPCによる遮蔽を測った数値ではありません。',
'抽出基準：広場内を除く入口なし区間25m以上、片側閉鎖帯20m以上、両側閉鎖帯12m以上。いずれも設計レビュー用の目安で、法令や建築基準ではありません。',
'通路脇の近接面は数値で検査し、吹き抜け越しの遠方壁・複数階の見通しは静的な立体モデルで別途評価しました。全方向・全地点の可視性を保証する検査ではありません。',
'v4参考立体図では閉鎖設備帯の壁面が省略されていました。今回の図では不透過壁と設備核の外枠を補い、仕上げなし／ありを同一形状で比較します。旧図との見え方の差を建物改修の成果とは扱いません。',
'表示の限界：透明ガラス、照明反射、商品、人物、設備内部は簡略化。局所モデルの外周は切断範囲です。白い外部やモデル端は実際の通路終端・屋外入口を示しません。'])
for f in g['floors']:
 p=page(f"{f['floor']}F｜閉鎖壁・局所仕上げ・視点位置");plan(p,f)
# Route audit, all 58 entries, 20 per sheet.
rows=a['routes']
for n in range(0,len(rows),20):
 p=page(f'通路別確認一覧 {n//20+1} / {math.ceil(len(rows)/20)}','入口数は2D直線接続の集計。長さはm。広場内は入口なし長から除外。');y=113
 tx(p,40,y,'階 / ID       入口数    入口なし最長    左閉鎖 / 右閉鎖      判断',12);y+=28
 for r in rows[n:n+20]:
  ids=[t['id']for t in a['treatments']if t['floor']==r['floor']and r['route']in t['routes']]
  decision='形状維持・仕上げ '+','.join(ids)if ids else '維持・実装後重点確認'if r['reasons']else '維持'
  tx(p,40,y,f"{r['floor']}F {r['route']}",11);tx(p,175,y,r['visible_doors'],11);tx(p,270,y,r['max_retail_door_gap_excluding_plaza_m'],11);tx(p,405,y,f"{r['longest_closed_left_m']} / {r['longest_closed_right_m']}",11);tx(p,560,y,decision,10);y+=29
 tx(p,40,765,'連絡通路・設備アクセスは用途上入口が少なくても維持。店舗街と同じ入口数の基準で不合格にはしません。',11)
p=page('入口の少ない区間｜残す理由と重点確認');paras(p,[
'N-W 北西専門店街：入口なし最長は1F 39m／2F 38.5m／3F 43m。両側に店舗が見える視点でも、曲がり先の広場や設備の目的地が把握しづらい可能性があります。入口増設はせず、既存WC・EV・店舗列への案内を補足します。',
'M-E2 東専門店街：1F 34.5m・入口1、2F 27m・入口2、3F 38.5m・入口1。光の広場が正面に開く進入方向は成立しますが、逆向きの歩行では単調さが残る可能性があります。平面を維持し、広場側／設備側の案内を区別します。',
'M-C2：2Fは入口なし34m、3Fは25.5m。時の広場への連続性と片側店頭が変化を担います。閉鎖面の仕上げのみ追補。N-Mは1F/3Fに約74mの片側閉鎖面がある一方、反対側に7／5入口があります。2Fは10入口があるため追加仕上げを強制しません。',
'SW-2：片側閉鎖帯は1F 51.5m／2F 59.5m／3F 80m。ただし各階6入口が接続し、設備アクセスK2-Aも共用します。対面店頭を主役として壁側は控えめな仕上げに留めます。',
'M-C1・M-E1・SW-1・SE-1は、対面店頭・分岐・広場・昇降機による変化があり、今回の平面変更は不要と判断。AB/BC連絡とK1-A/K2-A/K3-Aは目的のある移動空間であり、店舗を増やすために変更しません。',
'保留条件：実装後、N-WとM-E2を両方向に歩き、目的地の認識と歩行時間を確認します。無表情な印象が強い場合も、まず既存面の照明・実在目的地への案内を調整し、通路や店舗を即増設しません。'])
p=page('局所修正｜同一面内の仕上げ・案内');paras(p,[
'壁は閉鎖のまま保持。3mを基準に縦目地、6m以下で控えめな色調を切替。1面につき1～2枚の館内案内・施設管理展示を置き、等間隔に大量のオブジェを並べません。',
'案内面は下端0.9m／上端2.1mを基本とし、既存スタッフ扉と設備点検口を避けます。ピクトグラムと日本語の誘導先は、実装時に各階の実在経路・向きを照合してください。参考画像の英語仮ラベルは完成サインではありません。',
'通路への張出しは0m。新たな立体ベンチ、植栽、展示ケースを通路に追加しません。法定表示やスタッフ扉を隠しません。架空の入口や閉鎖帯を透かす窓は作りません。',
'参考モデルの面はちらつき防止に6～12mmだけずらして描画しています。これは施工寸法・当たり判定ではありません。Godot実装ではマテリアルやデカールを優先し、通行幅を減らさない仕様とします。'])
# Simple vector elevation comparison
for yy,title,after in [(505,'修正前：連続した閉鎖面',False),(650,'修正後：閉鎖を保持し、仕上げだけ分節',True)]:
 tx(p,45,yy-15,title,13);p.draw_rect(fitz.Rect(45,yy,1120,yy+95),color=INK,fill=(.8,.79,.75))
 if after:
  for x in range(45,1120,90):p.draw_line((x,yy),(x,yy+95),color=(.6,.63,.61),width=.7)
  for x in[220,830]:p.draw_rect(fitz.Rect(x,yy+25,x+90,yy+65),color=GREEN,fill=(.3,.45,.45));tx(p,x+5,yy+48,'館内案内',10,(1,1,1))
for start in range(0,len(a['treatments']),12):
 p=page(f'壁面仕上げ指示台帳 {start//12+1}','正確な始終点はlocal-finish-schedule.csv。P-T-SOUTHは広場南側の壁面識別子で、追加通路ではありません。');y=118
 for t in a['treatments'][start:start+12]:
  line=shape(t['line']);z=list(line.coords);tx(p,42,y,f"{t['id']}  {t['floor']}F  {' / '.join(t['routes'])}  {t['length_m']:.2f}m",12)
  tx(p,42,y+20,f"Local ({z[0][0]:.3f}, {z[0][1]:.3f}) → ({z[-1][0]:.3f}, {z[-1][1]:.3f}) / {t['wall_id']}",10);y+=51
notes={
'P-W':['翼の広場｜西核店の大きな店頭→長い開放空間→中央専門店街の連続性を保持。','北側店舗列・南西街にも接続。北側1→2F、南側2→3Fに昇降機を分けるため、上下階の移動先は一望だけで理解できるとは限りません。階別表示は実装後に確認。','進入部は上階床下の低い見え方から吹き抜けで開放されます。奥の長い閉鎖面は残るため、店頭の連続性と壁面仕上げの強弱を両方向から確認します。'],
'P-T':['時の広場｜北街→偏心した矩形開口→東街・南西街をつなぐ構成を保持。','2F/3Fの4m横断橋が見通しを横切り、光・翼より上下階の見通しが遮られます。これは構造上の違いとして残し、橋の下からも出口が読めるかを重点確認します。','追加発見：広場南側に不透過面が正面に見えます。近接通路の数値検査だけでは抽出されなかったため、各階の該当3面にも同じ平面仕上げ・館内案内を追補しました。開口や新通路は追加しません。'],
'P-L':['光の広場｜東専門店街から扇状に開く吹き抜けと東核店の接続を保持。','曲面回廊と対角の昇降機で翼・時とは違う見え方になります。南東街の退出側は閉鎖壁が近くに見え、進入時と同じ開放感にはならない点を残存課題とします。','A館への連絡は2F経由。3Fの見通しだけでA館へ直進できるような案内は出しません。ガラスの視認性と東核店の入口認識は実装後に確認します。']}
for pl in ['P-W','P-T','P-L']:
 p=page(notes[pl][0]);pic(p,pl+'-approach',(40,100,400,337),'A：店舗街から進入 / 1F');pic(p,pl+'-court',(415,100,775,337),'B：広場の入口 / 1F');pic(p,pl+'-exit',(790,100,1150,337),'C：接続する専門店街へ / 1F');paras(p,notes[pl][1:],y=400,size=14)
 cs=[c for c in cams if c['plaza']==pl and c['id']in['approach','court','exit']]
 paras(p,[f"{c['id']}：Local ({c['actual'][0]:.2f}, {c['actual'][1]:.2f}) / 視点高1.65m"for c in cs],y=650,size=11)
 p=page(notes[pl][0]+'｜上階');pic(p,pl+'-upper2',(40,105,587,463),'2F：回廊・横断橋・下階とのつながり');pic(p,pl+'-upper3',(605,105,1152,463),'3F：店頭・吹き抜け・次の経路');paras(p,[notes[pl][1],'評価範囲：歩行面から0.5m以上内側に置いた静止視点。画像間の経路をプレイヤーが歩いた結果ではありません。橋や梁の遮蔽、視点移動、カメラ揺れ、群衆の影響は未検証です。','図のガラス面は透明表現を省略しています。手すりの支柱は表示しますが、転落防止・衝突・頭上クリアランスの実装合格を意味しません。'],y=530,size=14)
for pl,before,after,title in [('P-W','nw-before','nw-after','北西専門店街N-W'),('P-L','approach-before','approach','東専門店街M-E2')]:
 p=page(title+'｜同一視点の局所仕上げ比較');pic(p,f'{pl}-{before}',(40,110,587,468),'仕上げ前：不透過壁を補完した共通モデル');pic(p,f'{pl}-{after}',(605,110,1152,468),'仕上げ追補後：平面・入口位置は同一');paras(p,['差分は壁面の控えめな色調・館内案内のみです。モデルの床面積、通路幅、入口数、吹き抜け位置は増減していません。','見た目の変化は限定的です。長い壁や入口の少なさを装飾だけで解決済みにはしません。実装後は反対方向・曲がり角の手前からも目的地を認識できるか評価します。'],y=540,size=15)
p=page('検査結果｜合格・指摘・未検証を区別');checks=a['checks'];failed=[c for c in checks if not c['pass_']];paras(p,[
'今回の図面検査：共用床の形状有効性3件、仕上げの通路張出し0mの指定が全件成立。18視点すべてが共用歩行域を0.5m内側へ縮めた範囲にあります。これは18地点の確認であり、経路全長の実歩行ではありません。',
'指摘として残す作図上の微小重複：1Fの共用床と閉鎖帯に0.038842㎡、2Fに0.033557㎡の交差があります。本監査の0.02㎡基準では2件不合格です。構造の全面再設計はせず、実装メッシュ生成時に共用歩行域を優先して閉鎖帯から差し引く局所処理を指定します。元v4データを無断で上書きして合格扱いにはしません。',
'3Fにも0.02㎡未満の交差があります（許容基準内であり、完全ゼロではありません）。全階の交差形状はresidual-overlap-findings.jsonに収録。微小重複は面積の小ささだけで無害とは断定できません。該当部の衝突・床の継ぎ目・段差は実装時のホールド項目です。閉鎖壁の参考モデルは設備側に切り取っていますが、ゲームの衝突確認は別途必要です。',
'従来v4の7,810件の図面検査結果は前回資料の記録として参照しています。今回すべてを再実施した結果ではありません。新監査の全件合格やGodot実装完了とは報告しません。',
'ゲーム保護確認：前回のgame-file-hashes.jsonを基準に238ファイルのバイト一致を照合。NPC・スキャン・AP・セーブ・Godotシーンの変更はありません。元v4資料も変更しません。'])
p=page('Godot実装後の実歩行確認｜今回未実施');paras(p,[
'① 空間認識：3広場への進入→広場内→専門店街への退出を1F/2F/3Fで両方向に歩く。N-W・M-E2の入口疎区間は特に、経路の見通し、誘導の向き、実歩行時間を記録する。',
'② 昇降機：全乗降口から共用通路まで移動し、手すり・床開口・踊り場・梁・上階床との干渉を確認。頭上有効高2.4mは設計目標として実寸検査し、ゲーム内の当たり判定と一致させる。',
'③ 安全な歩行：閉鎖帯との微小重複を共用床優先で解消した後、壁際、床継ぎ目、店舗入口、設備核4m入口、EV/トイレ前室で引っ掛かり・落下・隙間を確認する。',
'④ 案内と商業空間：文字の可読性、実在のWC/EV/他館への矢印、店頭の連続性、ガラス入口の認識を最終照明・マテリアルで確認。ベンチ・植栽・群衆が案内や入口を隠さないことを確認する。',
'⑤ 既存機能：NPC経路、猫の到達、宝箱配置、ソナー、案内図、訪問済みファストトラベル、セーブ互換を回帰確認。今回はどれもゲーム内で検証していません。',
'⑥ 性能：1,000人配置の通常移動と広場を見渡す瞬間のフレーム時間を測る。将来5,000人時の合格を推定で報告しない。仕上げ追加はマテリアル/デカールを基本とし描画負荷を測定する。'])
p=page('最終判断と承認待ちの範囲');paras(p,[
'維持：建物輪郭、通路網、3広場の形状、吹き抜けの上下位置、エスカレーター配置、188店舗の入口と区画、設備核、A/C館連絡位置。今回、これらの再設計は行いません。',
f"局所追補：6系統の通路脇と時の広場南側の閉鎖面、計{len(a['treatments'])}面に同一面内の仕上げ・案内を指定。微小重複2件は実装時に共用床優先で除去する処理条件を追補。新しい動線・入口は作りません。",
'未解決：N-W/M-E2の入口疎区間の体験、広場越しの長い閉鎖面の最終的な見栄え、横断橋下の圧迫感、照明・ガラス・群衆を含む可読性。静的モデルからの評価には限界があります。',
'設計上の評価：用途のある通路と異なる3広場は成立しており、主要骨格は維持する価値があります。一方で、実際に歩いて十分楽しいことまで確認済みとはしません。重点区間の実歩行結果を施工完了の条件にします。',
'この段階でゲーム本体は改修しません。v4平面図と本追補をご確認いただき、承認を受けてから実装へ進む状態で終了します。',
'同梱：本PDF、壁面位置図、通路別CSV、仕上げ座標CSV、18視点PNGとカメラ座標、機械可読監査、検証記録。既存v4の詳細店舗図・設備詳細は前回成果物を引き続き使用します。'])
doc.set_metadata({'title':'FIND YOURSELF B館 v4 最終確認追補','author':'FIND YOURSELF design review','subject':'Design review only; no Godot changes'});out=R/'downloads/FIND_YOURSELF-B-v4-Final-Confirmation.pdf';out.parent.mkdir(exist_ok=True);doc.save(out,garbage=4,deflate=True);print('PDF',len(doc),out)
# Structured final decisions
with(O/'final-decisions.csv').open('w',encoding='utf-8-sig',newline='')as fp:
 w=csv.writer(fp);w.writerow(['階','通路','名称','用途','局所仕上げID','判断','実歩行検証'])
 for r in rows:
  ids=[t['id']for t in a['treatments']if t['floor']==r['floor']and r['route']in t['routes']];w.writerow([r['floor'],r['route'],r['name'],r['role'],'/'.join(ids),'形状維持・仕上げ追補'if ids else '形状維持','未実施'])
(O/'README.md').write_text('''# B館 v4 最終確認追補\n\nゲーム本体を変更しない設計レビューです。前回v4の平面図に併せて確認してください。\n\n- PDF: downloads/FIND_YOURSELF-B-v4-Final-Confirmation.pdf\n- 全58階別通路: route-review.csv / final-decisions.csv\n- 局所仕上げの座標: local-finish-schedule.csv\n- 静止設計モデル18視点: views/*.png / camera-checks.json\n- 機械可読検査: frontage-audit.json\n\n「visible_doors」は2D直線接続入口数であり、現実の可視性測定ではありません。\n前後画像は同じ不透過壁補完モデルで仕上げだけ切り替えています。ゲーム画像ではありません。\n18視点は目高1.65m。全経路の移動検証・Godot実歩行は未実施です。\n旧v4の7810検査は前回記録で、今回の再試験結果ではありません。\n閉鎖帯/共用床の微小重複2件を残存指摘として報告しています。\n承認待ち。シーン・ゲームロジックを施工していません。\n''')
