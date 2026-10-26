"""Three-wing coordination and design-model review book. Reads design data only."""
from pathlib import Path
import json,sys,math,collections
sys.path.append('/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
import fitz
from shapely.geometry import shape,Point,LineString,Polygon,box
from shapely.ops import unary_union
from shapely import affinity
R=Path(__file__).resolve().parents[1];O=R/'docs/ac-detailed-design-v1';FONT=R/'assets/fonts/NotoSansCJKjp-Regular.otf';INK=(.12,.22,.25);MUTED=(.35,.43,.46);RED=(.7,.2,.14);BLUE=(.27,.48,.61);GREEN=(.22,.47,.32);BROWN=(.59,.43,.24);H={-1:-5.35,0:0,1:5.525,2:10.875,3:16.4};L={-1:'B1',0:'1F',1:'2F',2:'3F',3:'RF'}
def dec(v):
 if isinstance(v,dict):return shape(v)if'type'in v and('coordinates'in v or'geometries'in v)else{k:dec(x)for k,x in v.items()}
 if isinstance(v,list):return[dec(x)for x in v]
 return v
D={w:dec(json.loads((R/f'docs/{w.lower()}-detailed-design-v1/geometry.json').read_text()))for w in['A','C']};D['B']=dec(json.loads((R/'docs/b-v4-overlap-correction/geometry.json').read_text()));V=json.loads((O/'integration-verification.json').read_text());assert not V['failed'];cams=json.loads((O/'view-camera-checks.json').read_text());seams=json.loads((O/'connection-register.json').read_text());hubs=json.loads((O/'travel-hub-migration-proposal.json').read_text());doc=fitz.open();toc=[]
def text(p,x,y,t,size=12,color=INK):p.insert_text((x,y),str(t),fontname='jp'if not str(t).isascii()else'helv',fontsize=size,color=color)
def page(title,sub='',w=1684,h=1000):
 p=doc.new_page(width=w,height=h);p.insert_font(fontname='jp',fontfile=str(FONT));text(p,40,43,title,23);text(p,40,69,sub,10,MUTED);p.draw_line((40,82),(w-40,82),color=GREEN);text(p,40,h-22,f'FIND YOURSELF / A・C館詳細設計v1・3館整合 / 設計のみ・Godot未改修 / 2026-10-26  •  {len(doc):02}',9,MUTED);toc.append([1,title,len(doc)]);return p
font=fitz.Font(fontfile=str(FONT))
def para(p,items,x=45,y=115,size=14,gap=16,width=None):
 width=width or p.rect.width-x-45
 for item in items:
  current=''
  for ch in item:
   if ch=='\n'or font.text_length(current+ch,fontsize=size)>width:
    text(p,x,y,current,size);y+=size*1.6;current=''if ch=='\n'else ch
   else:current+=ch
  if current:text(p,x,y,current,size);y+=size*1.6
  y+=gap
 return y

def geom(p,g,xy,fill=None,color=INK,width=.5):
 if g.is_empty:return
 if g.geom_type=='Polygon':
  s=p.new_shape();s.draw_polyline([xy(q)for q in g.exterior.coords])
  for ring in g.interiors:s.draw_polyline([xy(q)for q in ring.coords])
  s.finish(color=color,fill=fill,width=width,closePath=True,even_odd=True);s.commit()
 elif g.geom_type in['LineString','LinearRing']:p.draw_polyline([xy(q)for q in g.coords],color=color,width=width)
 else:
  for child in g.geoms:geom(p,child,xy,fill,color,width)

def trans(ext,rect):
 r=fitz.Rect(rect);x0,z0,x1,z1=ext;s=min(r.width/(x1-x0),r.height/(z1-z0));ox=r.x0+(r.width-s*(x1-x0))/2;oz=r.y0+(r.height-s*(z1-z0))/2
 return lambda q:fitz.Point(ox+(q[0]-x0)*s,oz+(q[1]-z0)*s),s

def floor(wing,level):
 if wing=='B':
  sf=next((f for f in D['B']['floors']if f['floor']-1==level),None)
  if sf is None:return None
  f={**sf,'level':level}
  for k in['shell','public','walkable','floor_plate','void','shafts']:f[k]=affinity.translate(sf[k],-714,-30)
  f['stores']=[{**s,'polygon':affinity.translate(s['polygon'],-714,-30),'entry':[s['entry'][0]-714,s['entry'][1]-30]}for s in sf['stores']];return f
 return next(f for f in D[wing]['floors']if f['level']==level)

def site(p,level,rect,extent=(-790,-410,245,260),old=False):
 xy,s=trans(extent,rect)
 if old:
  data=json.loads((R/'docs/map-master-floor-plans.json').read_text())
  for f in data:
   if f['level']!=level:continue
   col={'A':(.71,.84,.90),'B':(.88,.81,.68),'C':(.72,.85,.71)}[f['building']]
   for poly in f.get('base',[]):geom(p,Polygon(poly),xy,col,MUTED,.3)
   for pack in f.get('structure',[]):geom(p,Polygon(pack['outer'],pack.get('holes',[])),xy,col,MUTED,.3)
  return xy,s
 for wing,color,mark in[('B',(.88,.81,.68),BROWN),('A',(.70,.83,.90),BLUE),('C',(.73,.85,.71),GREEN)]:
  f=floor(wing,level)
  if f is None:
   b=floor('B',0)['shell'];geom(p,b,xy,(.96,.96,.94),(.6,.6,.6),.5);q=xy(b.centroid.coords[0]);text(p,q.x-65,q.y,'B館：当階は基準未設計',12,MUTED);continue
  geom(p,f['floor_plate'],xy,color,mark,.6);geom(p,f['public'],xy,(.98,.98,.96),mark,.4)
  for st in f['stores']:geom(p,st['polygon'],xy,color,mark,.4)
  for g in D[wing].get('plazas',[])if wing!='B'else D['B']['plazas']:
   gg=g.get('court',g.get('polygon'));c=gg.centroid
   if wing=='B':c=affinity.translate(c,-714,-30)
   text(p,*xy(c.coords[0]),g['name'],7,mark)
  q=xy(f['shell'].representative_point().coords[0]);text(p,q.x,q.y,wing+'館',18,mark)
 for c in seams:
  if c['level']!=level:continue
  q=xy(c['world_xz']);p.draw_circle(q,4,color=RED,fill=(1,1,1),width=1);text(p,q.x+6,q.y-4,c['id'],10,RED)
 a=xy((-730,220));b=xy((-630,220));p.draw_line(a,b,color=INK,width=2);text(p,a.x,a.y+18,'100m / World XZ',10)
 return xy,s

def image(p,id,rect,caption):p.insert_image(fitz.Rect(rect),filename=str(O/'views'/f'{id}.png'));text(p,rect[0],rect[3]+20,caption,11)

p=page('A館・C館 詳細設計v1｜3館の配置と接続','B館v4.1を固定した設計提案。建物・NPC・スキャン・AP・セーブを変更していません。',w=1191,h=842)
counts={w:[len(f['stores'])for f in D[w]['floors']]for w in['A','C']}
para(p,[
'A館は三方向の専門店街と3角の広場をつなぐ回遊型、C館は6独立棟・屋外通路・庭・周縁デッキで構成しました。両館ともB1／1F／2F／3F／RFの5階を図面化しています。',
f"計画区画数：A館 {counts['A']}＝計{sum(counts['A'])}区画。C館 {counts['C']}＝計{sum(counts['C'])}区画（商業54＋施設24）。施設区画や屋上施設をすべて商業店舗として数えていません。階順はB1→RFです。",
'B館v4.1の1F/2Fにある4つの接続をそのまま使用します。接続位置・幅・床高は固定し、受け口の床・ファサードの切欠きはA/C側で設計しました。B館のデータは変更していません。',
'重要な範囲区分：A5階＋C5階＋B館基準の1～3F＝13の詳細床面を確認。B館B1/RFの2面は基準データにないため未設計として表示します。全15面の実装完了を報告する資料ではありません。',
'この冊子は3館全体図・接続拡大・立体参考・統合検査を先にまとめ、後半にA館とC館の全階詳細図・設備・断面・台帳を収録しています。寸法は実測値ではなくゲーム用設計値です。',
'Godot本体への実装、実歩行、NPCの群衆、描画性能は未検証。完成図の確認と最終承認はユーザーが行います。承認前に実装を開始しません。'],size=14,gap=20)
p=page('公式資料の読み取りと、ゲーム独自の設計値','ユーザー提供公式フロアガイドを画像として目視。測量図・構造図ではありません。',w=1191,h=842)
para(p,[
'kazeの1～3頁：斜めの三方向の街路、角で広がる広場、広場へ向く大型店、上階の館間分配、階別の飲食・服飾・娯楽を確認。A館では三角の回遊と中央商業短絡路へ置き換え、楕円リング案を使いません。',
'OUTLETの7～8頁：1st/2nd/3rd Ave.とSouth St.、複数棟の店先、空の広場、屋外階段と上階デッキ、他館ブリッジを確認。C館では独立棟6つと3庭に整理し、庭の中央を上階床で塞がない設計としました。',
'地下・屋上、C館3F、各店舗の数・間口・奥行き、階高、設備容量、柱・梁の概略はゲーム用の提案値です。実施設の測定寸法や施工仕様と扱いません。施設名・実在ブランド・ロゴを複製していません。',
'提供された2つのPDFは同一の8ページデータでした。参照原本のSHA-256：2a50e320b180fe1fffc391d175deaa013f6bb50ee53b60fb7135530b8bfb7eac。原本は本ZIPに再配布せず、目視記録を同梱しています。',
'B館はWorld X=Local X−714、World Z=Local Z−30を読取時だけ適用。A/Cの新データは初めからWorld XZ m。新データを旧MallCurveに再度通す二重変形は行わない設計です。'],size=14,gap=23)
p=page('既存ゲーム配置と今回の3館案｜1F同縮尺比較','左は既存の静的エクスポート、右はA/C新設計＋固定Bv4.1。実ゲームの改修前後スクリーンショットではありません。')
site(p,0,(45,115,820,840),old=True);site(p,0,(865,115,1640,840));text(p,45,105,'既存ゲームの平面データ',14);text(p,865,105,'設計案：A三角回遊・B既定・C分棟',14)
para(p,['旧Aは湾曲した主通路と北の追加回廊、旧Cは地上8店＋2F3店。新案は各館の骨格と全階を再計画しますが、現在ゲームのファイルには反映していません。',
'旧商業ID：A40店＋地下7売場＋地上飲食4売場を継承、補助サイン/読書施設2参照も記録。C11店を用途が合う新店舗へ対応付け。旧点が重心/原点/看板である場合は、新入口と同じ種類の測点として比較しません。'],x=45,y=890,size=12,gap=12)
for level in[-1,0,1,2,3]:
 p=page(f'3館全体｜{L[level]} +{H[level]:.3f}m','青：A館　茶：B館v4.1　緑：C館　白：共用床　赤：固定接続。図の上はZ−で、実施設の真北ではありません。')
 site(p,level,(50,105,1634,855));para(p,[
 'A/Bは1F・2F、B/Cも1F・2Fで接続。地下・3F・RFの館間移動は各館の階段/EVから1Fまたは2Fへ移動して行う計画です。',
 'B館のB1/RFは基準の対象外として灰色表示し、床板・店舗・外部橋を今回勝手に追加しません。'if level in[-1,3]else '既存B側の橋・歩道は形状不変。受け側の公開床と、店舗/設備帯/外壁との干渉を別々に検査しています。'],x=55,y=900,size=12,gap=10)
# Gateways: draw the unchanged B bridge and the receiving floor at identical World coordinates.
for offset in[0,2]:
 p=page('固定受け口の拡大｜'+('A/B接続'if offset==0 else'B/C接続'),'B側の床を動かさず、A/C側の到着前庭・連続床・ファサードの切欠きを設計。寸法はm。')
 for i,c in enumerate(seams[offset:offset+2]):
  end=c['world_xz'];extent=(end[0]-24,end[1]-24,end[0]+24,end[1]+24);rect=(55+i*815,130,805+i*815,760);xy,s=trans(extent,rect);clip=box(*extent);wing=c['wing'];f=floor(wing,c['level']);b=floor('B',c['level'])
  geom(p,b['floor_plate'].intersection(clip),xy,(.88,.80,.66),BROWN,.7);geom(p,f['floor_plate'].intersection(clip),xy,(.70,.84,.91)if wing=='A'else(.73,.86,.72),GREEN,.7)
  geom(p,f['public'].intersection(clip),xy,(.98,.99,.98),GREEN,.6);geom(p,b['public'].intersection(clip),xy,(.95,.91,.81),BROWN,.5)
  for st in f['stores']:geom(p,st['polygon'].intersection(clip),xy,(.65,.78,.83),INK,.8)
  axis=[0,1]if wing=='A'else[1,0];line=LineString([(end[0]-axis[0]*c['width_m']/2,end[1]-axis[1]*c['width_m']/2),(end[0]+axis[0]*c['width_m']/2,end[1]+axis[1]*c['width_m']/2)]);geom(p,line,xy,color=RED,width=2)
  q=xy(end);text(p,q.x+6,q.y-8,c['id'],15,RED);text(p,rect[0],105,f"{c['id']} / {c['floor']} / 幅{c['width_m']}m",16)
  text(p,rect[0],800,f"World ({end[0]}, {end[1]}) / 床高{c['height']:.3f}m",13);text(p,rect[0],830,f"幅方向の床支持不足 A/C {c['missing_width_new_m']:.6f}m・B {c['missing_width_B_m']:.6f}m",12)
 para(p,['A館2Fでは、橋の端だけでなくA外壁を通る固定B橋の全区間を確認し、閉鎖帯と重なった6㎡をA側の到着床へ切欠きました。B側や店舗区画は変更していません。',
 'C側は到着口の前に建物の裏壁を置かず、公開床から棟前デッキ/屋外街路へ接続。手すり・支持柱・梁下の実装干渉は今後の実歩行と3D検証に残します。'],x=55,y=885,size=12,gap=10)
p=page('階高と縦移動｜13設計面のネットワーク','全館のB1/1F/2F/3F/RF高さを揃える。B館の対象外2面は未設計として区別。')
columns={'A':310,'B':840,'C':1370};ys={3:180,2:315,1:450,0:585,-1:720}
for wing in['A','B','C']:
 x=columns[wing];text(p,x-60,115,wing+'館',22)
 for level in[3,2,1,0,-1]:
  y=ys[level];planned=not(wing=='B'and level in[-1,3]);p.draw_rect(fitz.Rect(x-140,y-27,x+140,y+28),color=INK if planned else MUTED,fill=(.80,.88,.91)if wing=='A'else(.87,.82,.71)if wing=='B'and planned else(.80,.89,.77)if wing=='C'else(.96,.96,.94),width=1)
  text(p,x-100,y+6,f'{L[level]}  {H[level]:.3f}m'+('  未設計'if not planned else''),14)
 for lo in[-1,0,1,2]:
  if wing=='B'and lo in[-1,2]:continue
  p.draw_line((x,ys[lo]-27),(x,ys[lo+1]+28),color=INK,width=2)
for level in[0,1]:
 for left,right in[('A','B'),('B','C')]:p.draw_line((columns[left]+140,ys[level]),(columns[right]-140,ys[level]),color=RED,width=2)
para(p,['Aは3設備核、Cは6設備核の階段/EVを全5階で対応。Bはv4.1の3設備核を1～3Fだけ使用して接続グラフを検査しました。',
 '縦線は図面上の接続関係。実際のEV駆動や階段の段差、階段・梁・手すりのコリジョンをゲーム内で確認した線ではありません。',
 f"階高：B1→1F 5.350m / 1F→2F 5.525m / 2F→3F 5.350m / 3F→RF 5.525m。定義済み{V['defined_floor_surfaces']}面の接続が成立。"],x=55,y=820,size=13,gap=12)
# Court models show scale/connectivity, not finished materials or a running game.
notes={
'A-PW':['西到着口と北/西専門店街を受ける風のゲート。曲面の開口と西核店の顔を組み合わせる。','B橋受け口と店舗入口を混同せず、来館方向から次の街路が読めるかを実装後に確認。'],
'A-PE':['北/東の街路と東側大型店をつなぐ角の広場。西/南の広場とは開口形状・店舗接続が異なる。','外装・柱割り・商品・照明は簡略。広さを装飾で埋めず、店先と見通しを主役とする。'],
'A-PS':['中央商業短絡路、南東/西の街、飲食エリアを結ぶ光のコート。','4つの旧飲食売場と共有席を近接させる。最終照明・案内・NPC着席時の視認性は未検証。'],
'C-GATE':['B館からの到着側を受け、店舗棟の表側へ分配する南の迎賓庭。','上階の大きな広場床を積み重ねず、棟前の通路と周縁デッキだけでつなぐ。'],
'C-CENTRAL':['独立棟の間の木陰の中庭。庭の中心が上空まで抜け、地上と上階の見通しが連続する。','数値検査に加え立体で初稿の覆いを検出し、上階円盤/放射床を削除した。開放性は実装後の光・柱・人混みで再評価する。'],
'C-NORTH-GARDEN':['北側の庭と上階デッキから、向かいの棟・階段・次の店先を確認する。','実在OUTLETの2階建を完全再現したものではなく、C館3F/RFはゲーム用の独立した追加層。']}
for wing in['A','C']:
 for pl in D[wing]['plazas'][:3]:
  p=page(wing+'館｜'+pl['name']+'・立体参考','新設計JSONから生成した別モデル。実ゲーム画像ではありません。透明ガラス・天井設備・構造・商品は簡略表現。')
  image(p,pl['id']+'-axon',(45,115,825,635),'鳥瞰：同じ設計座標の床・開口・店頭・階層');image(p,pl['id']+'-eye',(865,115,1645,635),'人の目高：床上1.65mの静止設計視点')
  c=next(c for c in cams if c['plaza']==pl['id']);para(p,notes[pl['id']]+[f"視点：{L[c.get('level',0)]} / World X={c['actual_world_xz'][0]:.3f}, Z={c['actual_world_xz'][1]:.3f}, Y={c.get('eye_world_y',1.65):.3f}。図面の歩行余白内へ配置。",'画像の外周は局所モデルの切断範囲。白い背景や切断面を実際の壁・出口と解釈しないでください。静止視点が安全な床上にあることと、経路全長を実際に歩けたことは別です。'],x=55,y=710,size=13,gap=17)
p=page('設計上の評価と、採用前に修正した箇所','自動検査だけで商業施設としての自然さを合格にしていません。',w=1191,h=842)
para(p,[
'A館：三角回遊の中心に大きな用途不明の閉鎖面が残らないよう、中央大型店の入口と12mの商業短絡路を設計。外形を店舗/通路の用途へ寄せ、閉鎖帯は機械・保守・保管と、部屋ではない配管帯を区別しました。',
'A館：旧a_marketを小さな雑貨区画へ機械的に対応付ける問題を修正。食品スーパー/書店読書/地下食品街/飲食カウンターは用途が残る新区画へ対応。B2橋の6㎡の干渉はA側のファサードを切り欠き解消しました。',
'C館：上階に地上庭の円盤と短絡路をそのまま積層した初稿は、1Fが大きな屋根下になっていたため不採用。約6mの周縁デッキと棟前廊へ限定し、3庭の中心の抜けを各上階で揃えました。',
'維持する空間：広い庭・広場、屋上の緑地、待ち合わせの溜まりは、空いているという理由で店舗を詰めません。目的のある接続と、通行を避けた休憩場所の両方を残します。',
'残る体験上の課題：実際の歩行距離、長い店頭/閉鎖面の単調さ、地上と上階の視認、橋と柱の日陰・天候、NPCがいる際の混雑。これらは図面の交差検査や静止画像だけでは確定できません。'],size=14,gap=22)
p=page('図面検査｜各館の検査と3館の独立照合','検査件数は対象と方法を分けて記載。過去のゲーム実歩行を今回の結果として数えません。',w=1191,h=842)
para(p,[
 f"3館の独立照合：{V['total_checks']:,}項目、不合格{len(V['failed'])}。同じWorld座標で4ゲートの全幅支持・連続、他館の店舗/閉鎖帯/設備核干渉、共通階高、定義済み13床面の接続グラフ、保護ファイル{V['protected_file_count']}件を確認しました。",
'新A/Cの局所検査を別実装で補足：45cmの余裕を取った共用域の連結、全商業/施設入口の接続、店舗/施設相互と公開床との交差、内部主路が区画と棚配置を避けることを確認。面積の数値許容は1×10⁻⁸㎡です。',
'C庭の上空予約を各上階の床板と照合し、庭の中心を塞いでいないことを確認。吹き抜け/機械開口を共用床・構造床から分離しました。階段/EV/エスカレーターの段板・乗降口等の寸法は各館詳細図と検査表を参照してください。',
'旧IDはA商業51・補助参照2、C商業11。実装前の対応表として保持し、旧基準点が入口ではない場合の種類も記録。ファストトラベルの旧訪問キー20件は変更せず、A/C15件に新しい着地候補を提案し、B側5件は今回移動しません。',
'各館のgenerator検査/独立再検査は別ファイルに収録し、同じ対象の重複した件数を一つの総数に足し合わせて水増ししません。最新入力SHAとPDF/画像の対応も提出パッケージの検証記録へ保存します。'],size=14,gap=22)
# Travel proposal: explicit static reference types and no editing of save state.
for start in[0,10]:
 p=page(f'旧訪問キーの移行候補 {start//10+1}','実装案の参考台帳。既存訪問フラグ・ゲーム内座標は今回変更していません。')
 y=125
 for h in hubs[start:start+10]:
  text(p,45,y,h['id'],13);text(p,275,y,h['legacy_visited_key'],12);text(p,550,y,h['old_floor_id'],12)
  if h.get('new_world_xyz'):
   q=h['new_world_xyz'];text(p,680,y,f"→ {h.get('new_display_name','')}  ({q[0]:.2f}, {q[1]:.3f}, {q[2]:.2f})",12)
  else:text(p,680,y,'B側：今回変更しない／実装時照合',12,MUTED)
  text(p,275,y+28,'旧点はソース定義のMall.HUBSをMallCurve.worldで換算した静的参照。実歩行実測ではない。',10,MUTED);y+=75
 text(p,45,925,'新点は共用歩行域内の足元候補（床上0.1m）。実装後に床・壁・NPC・落下防止と既存セーブ互換を確認します。',12)
p=page('未検証事項・承認後の実装範囲','今回は図面を提出して終了。Godotへの反映は最終承認後です。',w=1191,h=842)
para(p,[
'未検証：Godotの実歩行、壁/床/扉/手すりのコリジョン、昇降機の乗降と駆動、階段・梁下、ガラス入口、サインの可読性、天候、夜間照明、NPC密度、描画フレーム時間、セーブ互換。図面検査の合格から実機性能や完成品質を推定しません。',
'実装時の連動対象：店舗/固定NPC/猫/宝箱候補/案内図/訪問済み地点を新座標へ一緒に移行。新しい当たり判定だけを入れて旧案内図や旧NPC経路を残す改修は避けます。',
'B館のB1/RFは今回未設計です。A/C10階分の完成と、全15階分の設計/実装完了を混同しません。B基準の接続を変更する必要は今回ありませんでした。',
'店舗/設備の用途や寸法はゲーム用設計値。柱梁の荷重設計、給排水/空調/防災の詳細、避難容量・法的認定は実施設計を行った成果ではありません。ゲーム内に必要な空間と動線を示しています。',
'以下にA館・C館の詳細図面本編を続けます。承認したい配置や寸法と、未検証の実歩行条件を分けて確認してください。ゲーム本体は変更せず、ここで作業を終了します。'],size=14,gap=24)

doc.set_toc(toc);doc.set_metadata({'title':'FIND YOURSELF A/C詳細設計v1・3館整合','author':'FIND YOURSELF design team','subject':'Design-only; B v4.1 fixed; Godot unchanged'});master=Path('/tmp/FIND_YOURSELF-AC-Coordination-v1.pdf');doc.save(master,garbage=4,deflate=True)
# One combined, bookmarked book for the user. Full standalone wing PDFs remain available in the ZIP.
combined=fitz.open();fulltoc=[]
for name,path in[('3館整合・立体参考',master),('A館詳細平面・設備・断面・台帳',R/'downloads/FIND_YOURSELF-A-Detailed-Design-v1.pdf'),('C館詳細平面・設備・断面・台帳',R/'downloads/FIND_YOURSELF-C-Detailed-Design-v1.pdf')]:
 part=fitz.open(path);offset=len(combined);combined.insert_pdf(part);fulltoc.append([1,name,offset+1])
 for row in part.get_toc():fulltoc.append([2,row[1],row[2]+offset])
combined.set_toc(fulltoc);combined.set_metadata({'title':'FIND YOURSELF A館・C館 詳細設計v1 全資料','author':'FIND YOURSELF design team','subject':'A5 floors, C5 floors, B v4.1 coordination; no game changes'});out=R/'downloads/FIND_YOURSELF-AC-Detailed-Design-v1.pdf';combined.save(out,garbage=4,deflate=True);print('MASTER_PAGES',len(doc),'COMBINED_PAGES',len(combined),'PDF_BYTES',out.stat().st_size)
