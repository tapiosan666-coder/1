"""Detailed vector plans for C wing. Separate from the Godot project."""
from pathlib import Path
import json,sys,math,collections
sys.path.append('/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
import fitz
from shapely.geometry import shape,Polygon,Point,LineString,box
from shapely.ops import unary_union
R=Path(__file__).resolve().parents[1];O=R/'docs/c-detailed-design-v1';FONT=R/'assets/fonts/NotoSansCJKjp-Regular.otf';INK=(.12,.22,.26);RED=(.76,.2,.14);GREEN=(.16,.46,.35)
def dec(v):
 if isinstance(v,dict):return shape(v)if'type'in v and('coordinates'in v or'geometries'in v)else{k:dec(x)for k,x in v.items()}
 if isinstance(v,list):return[dec(x)for x in v]
 return v
D=dec(json.loads((O/'geometry.json').read_text()));V=json.loads((O/'verification.json').read_text());doc=fitz.open();TOC=[]
def text(p,x,y,t,size=11,col=INK):p.insert_text((x,y),str(t),fontname='jp'if not str(t).isascii()else'helv',fontsize=size,color=col)
def page(title,sub='',w=1684,h=1000):
 p=doc.new_page(width=w,height=h);p.insert_font(fontname='jp',fontfile=str(FONT));text(p,40,42,title,23);text(p,40,68,sub,10);p.draw_line((40,82),(w-40,82),color=GREEN);text(p,40,h-20,f'FIND YOURSELF / C館 詳細設計 v1 / 図面のみ・Godot未改修 / 2026-10-26   {len(doc):02}',9);TOC.append([1,title,len(doc)]);return p
font=fitz.Font(fontfile=str(FONT))
def paras(p,items,x=45,y=120,size=15,width=None,gap=17):
 width=width or p.rect.width-x-45
 for item in items:
  line=''
  for c in item:
   if c=='\n'or font.text_length(line+c,fontsize=size)>width:text(p,x,y,line,size);y+=size*1.6;line=''if c=='\n'else c
   else:line+=c
  if line:text(p,x,y,line,size);y+=size*1.6
  y+=gap
 return y
def polys(g):return[]if g.is_empty else[g]if g.geom_type=='Polygon'else[p for p in getattr(g,'geoms',[])if p.geom_type=='Polygon']
def draw(p,g,xy,fill=None,col=INK,w=.5):
 for q in polys(g):
  s=p.new_shape();s.draw_polyline([xy(a)for a in q.exterior.coords])
  for ring in q.interiors:s.draw_polyline([xy(a)for a in ring.coords])
  s.finish(color=col,fill=fill,width=w,closePath=True,even_odd=True);s.commit()
def line(p,g,xy,col=INK,w=.5):
 parts=[g]if g.geom_type=='LineString'else getattr(g,'geoms',[])
 for q in parts:
  if q.geom_type=='LineString'and len(q.coords)>1:p.draw_polyline([xy(a)for a in q.coords],color=col,width=w)
def transform(ext,rect):
 x0,z0,x1,z1=ext;r=fitz.Rect(rect);s=min(r.width/(x1-x0),r.height/(z1-z0));ox=r.x0+(r.width-(x1-x0)*s)/2;oz=r.y0+(r.height-(z1-z0)*s)/2;return lambda a:fitz.Point(ox+(a[0]-x0)*s,oz+(a[1]-z0)*s),s

def plan(p,f,extent,rect,detail=False,routes=False):
 xy,sc=transform(extent,rect);clip=box(*extent);draw(p,f['shell'].intersection(clip),xy,(.90,.89,.85),(.5,.5,.46),.7)
 # C outdoor upper decks remain strips and courts: background void is deliberately unfilled.
 if f['level']>0:draw(p,f['void'].intersection(clip),xy,(.97,.98,.97),(.76,.82,.76),.2)
 draw(p,f['public'].intersection(clip),xy,(.96,.96,.89),(.42,.5,.47),.5)
 for garden in f['landscape']:draw(p,garden['geom'].intersection(clip),xy,(.47,.65,.44),(.27,.45,.3),.6)
 if f['level']==-1:
  draw(p,f.get('loading_yard',Polygon()).intersection(clip),xy,(.72,.72,.70),(.35,.35,.33),.7);draw(p,f.get('staff_corridor',Polygon()).intersection(clip),xy,(.84,.75,.59),(.5,.36,.21),.5)
  if clip.covers(Point(-222,-248)):q=xy((-222,-248));text(p,q.x-16,q.y,'閉鎖搬入',8)
 for v in f['pavilions']:
  if not v['footprint'].intersects(clip):continue
  if clip.covers(v['footprint'].centroid):q=xy(v['footprint'].centroid.coords[0]);text(p,q.x,q.y-14,v['id'],10,GREEN)
 for s in f['stores']:
  if not s['polygon'].intersects(clip):continue
  draw(p,s['polygon'].intersection(clip),xy,(.75,.85,.9)if s['kind']=='retail'else(.81,.83,.87),INK,.6);draw(p,s['backroom'].intersection(clip),xy,(.9,.77,.58),(.6,.46,.26),.4)
  if detail:
   draw(p,s['shelf_zones'].intersection(clip),xy,(.62,.7,.68),(.32,.46,.39),.3);draw(p,s['wall_solids'].intersection(clip),xy,(.19,.28,.3),(.19,.28,.3),.1)
   line(p,LineString(s['main_route']).intersection(clip),xy,GREEN,1)
  ep=s['entry'];u=s['u'];a=[ep[0]-u[0]*1.5,ep[1]-u[1]*1.5];b=[ep[0]+u[0]*1.5,ep[1]+u[1]*1.5]
  if clip.covers(Point(ep)):
   p.draw_line(xy(a),xy(b),color=(1,1,1),width=2);p.draw_circle(xy(ep),2.1,color=RED,fill=RED)
  c=s['polygon'].representative_point()
  if clip.covers(c):q=xy(c.coords[0]);text(p,q.x-18,q.y,s['id'],7 if detail else 5);text(p,q.x-18,q.y+11,s['category'],7 if detail else 5)
 for c in f['cores']:
  draw(p,c['outline'].intersection(clip),xy,(.91,.8,.8),(.61,.3,.3),.6)
  if detail:
   for room in c['rooms'].values():draw(p,room.intersection(clip),xy,None,(.56,.35,.35),.35)
   draw(p,c['room_wall_solids'].intersection(clip),xy,(.3,.3,.3),(.3,.3,.3),.1)
   for fix in c['fixtures']:draw(p,fix['geom'].intersection(clip),xy,(.72,.82,.84),INK,.3)
  ep=c['entry']
  if clip.covers(Point(ep)):q=xy(ep);p.draw_circle(q,2,color=GREEN,fill=GREEN);text(p,q.x+3,q.y-2,c['id'],7)
 draw(p,f.get('guardrails',Polygon()).intersection(clip),xy,(.3,.55,.6),(.2,.44,.5),.4)
 draw(p,f['shafts'].intersection(clip),xy,(1,1,1),(.5,.21,.19),.8)
 for e in f['escalators']:
  for land in e['landings']:draw(p,land.intersection(clip),xy,(.74,.87,.77),GREEN,.6)
  c=Point(e['c']);u=e['u'];sign=1 if e['direction']=='UP'else-1
  if clip.covers(c):
   a=(c.x-u[0]*4*sign,c.y-u[1]*4*sign);b=(c.x+u[0]*4*sign,c.y+u[1]*4*sign);p.draw_line(xy(a),xy(b),color=GREEN,width=1);q=xy((c.x,c.y));text(p,q.x+2,q.y,e['id'],6)
 for g in f['furniture']:draw(p,g['geom'].intersection(clip),xy,(.4,.57,.35)if g['kind']=='planter'else(.55,.35,.18),INK,.5)
 if routes:
  for r in D['routes']:
   if f['level']not in r['levels']:continue
   mid=LineString(r['points']).interpolate(.5,normalized=True)
   if clip.covers(mid):q=xy(mid.coords[0]);text(p,q.x+3,q.y,r['id'],6,(.26,.38,.65))
 for plaza in D['plazas']:
  c=plaza['polygon'].centroid
  if clip.covers(c):q=xy(c.coords[0]);text(p,q.x-25,q.y,plaza['name'],9)
 for x in range(math.ceil(extent[0]/25)*25,math.floor(extent[2]/25)*25+1,25):q=xy((x,extent[3]));text(p,q.x-9,rect[3]+14,x,7)
 for z in range(math.ceil(extent[1]/25)*25,math.floor(extent[3]/25)*25+1,25):q=xy((extent[0],z));text(p,rect[0]-29,q.y,z,7)
 return xy,sc

p=page('C館｜独立棟と屋外街路の詳細設計','参照：公式OUTLET 1F/2Fガイド。実在寸法の測量・完全再現ではなく、ゲーム用のオリジナル計画です。',w=1191,h=842)
paras(p,[
'6つの独立棟を、向きの異なる店舗街・中央庭・南の迎賓庭・北のテラス庭で接続します。建物間の未使用面を一枚の公開床で埋めず、1Fの地上歩行路・植栽と、上階の細長い屋外デッキ・中庭の抜けを分けています。',
'参考資料の1st/2nd/3rd街路、合流する広場、分棟・2階デッキの構成を採用。配置・寸法・6棟の向きとB1/3F/RFは本ゲーム独自です。実在OUTLETが5層であるとは扱いません。',
'B1は棟下と地下共用ホール、搬入ヤードと時間分離の管理通路。1～3Fは各18商業区画。RFは各棟1施設の計6施設と、残りを屋上庭園・回遊床にします。合計78区画のうち商業店舗は54です。',
'各店に入口3m、奥行24.35m（RF小施設11.85m）、専用バックルーム、店内主路2.4m計画、棚配置帯を描きます。全階に6つのトイレ・階段・EV核を持たせ、屋外エスカレーターは1→2Fと2→3Fの2バンクです。',
'B館固定受け口は1F(-370,-80)、2F(-432,-117)、床高0／5.525mを保持。B1・3F・RFの直接B館橋は計画せず、C館内部で1F/2Fへ上下移動して館間移動します。',
f"図面検査{V['checks']:,}件、不合格{len(V['failed'])}件。実歩行・衝突・群衆・法的建築適合・構造/防水は未検証。Godot本体とB館v4.1は変更していません。"],size=14,gap=18)
# Five levels, no unfinished level hidden behind a program label.
for f in D['floors']:
 p=page('C館 '+f['label']+'｜全体詳細平面',f"床高{f['height']:+.3f}m / {len(f['stores'])}区画 / 屋外デッキ・地上歩行・棟内前廊・閉鎖搬入を区別")
 xy,sc=plan(p,f,(-640,-395,-195,-70),(55,110,1625,840),False,True)
 x=-625;z=-88;a=xy((x,z));b=xy((x+50,z));p.draw_line(a,b,color=INK,width=2);text(p,a.x,a.y+18,'50m',10)
 paras(p,['赤点：店舗入口 / 青灰：商業・施設区画 / 茶：バックルーム / 桃：共用設備核 / 白い抜け：床開口 / 緑：植栽・乗降床。',
 '上階の白い中庭は地上まで抜ける屋外空間で、歩ける床ではありません。1Fの地上庭園とは意味を分けています。'if f['level']>0 else'地下は屋内ホールと閉鎖搬入を分離。上部の地上庭園と同じ外形・植栽用途ではありません。'if f['level']==-1 else'地上の緑地は店頭通路と分け、歩行経路を通さない植栽床として示しています。'],y=900,size=12,gap=9)
 # Every store remains readable in enlarged facade sectors.
 for j,(ext,title)in enumerate([((-635,-385,-425,-175),'西・北西・南西'),((-435,-390,-235,-120),'北東・東・南東')],1):
  p=page(f"C館 {f['label']}｜店舗・設備拡大 {j} / {title}",'実際の店舗入口・専用バックルーム・棚配置帯・内部主路・共用設備を表示。用途不明の余白を公開床にしない。')
  plan(p,f,ext,(55,110,1625,890),True,True);text(p,55,948,'内部主路2.4m計画。通常店入口3m、バックルーム扉1.7m、設備共用入口4m。World X/Z m。',11)
# Individual courts, all levels distinguish open yard vs podium.
for plaza in D['plazas']:
 p=page(plaza['name']+'｜地上・デッキ・屋上の関係',plaza['role'])
 ext=plaza['polygon'].buffer(18).bounds
 for f,rect in zip([D['floors'][1],D['floors'][2],D['floors'][4]],[(50,120,545,720),(595,120,1090,720),(1140,120,1635,720)]):
  plan(p,f,ext,rect,True,True);text(p,rect[0],104,f['label']+' '+str(f['height'])+'m',14)
 paras(p,['広場は店頭・階段/EV・複数街路をつなぐ中継地点として配置。店舗入口や乗降口をベンチで塞がない位置だけを採用。',
 '1Fは庭と地上歩行を接続。上階は6mの周縁デッキと必要な連絡橋だけで接続し、庭の中心には同位置の空中抜けを全上階で確保します。屋外の雨風対策は実装段階に残します。',
 '立体イメージは3館統合確認資料に収録します。本PDFの平面は設計データそのものです。ゲーム画面・実歩行結果ではありません。'],x=55,y=795,size=13,gap=15)
# Specific equipment cores, not a generic picture unrelated to the floor plan.
for core in D['cores']:
 p=page(core['id']+'｜トイレ・階段・EV詳細','全5階で同一World XZ。前廊から男女トイレ/階段/EVへ入り、多目的WCは2mアクセス路の先。')
 bounds=core['outline'].buffer(1).bounds;xy,sc=transform(bounds,(55,125,825,890));draw(p,core['outline'],xy,(.97,.95,.92),INK,1)
 names={'front_lobby':'共用前室','stair':'階段室・保守領域','lift':'EV 4×4m','accessible_wc':'多目的WC 4×4m','lift_access':'アクセス幅2m','accessible_access':'多目的WC前','women':'女性WC','men':'男性WC'}
 for k,r in core['rooms'].items():
  draw(p,r,xy,None,(.5,.4,.37),.6);q=xy(r.centroid.coords[0]);text(p,q.x-25,q.y,names[k],9)
 draw(p,core['room_wall_solids'],xy,(.25,.3,.3),(.25,.3,.3),.1)
 for c in core['cubicles']:
  draw(p,c['polygon'],xy,None,INK,.6);q=xy(c['door']);p.draw_line((q.x-12,q.y),(q.x+12,q.y),color=(1,1,1),width=2)
 for fix in core['fixtures']:draw(p,fix['geom'],xy,(.7,.83,.87),INK,.5)
 for land in core['stair_landings']:draw(p,land,xy,(.85,.92,.85),GREEN,.5)
 # Stair treads shown in the same world transform, schematic flight plan in its reserved room.
 a=next(v['core_origin']for v in D['pavilions']if v['id']==core['pavilion']);u=core['u'];n=core['n'];tp=lambda x,z:(a[0]+u[0]*x+n[0]*z,a[1]+u[1]*x+n[1]*z)
 for z in[7+k*.30 for k in range(16)]:
  p.draw_line(xy(tp(.5,z)),xy(tp(2.5,z)),color=INK,width=.5);p.draw_line(xy(tp(3.5,z)),xy(tp(5.5,z)),color=INK,width=.5)
 for door in core['doors']:
  q=xy(door['p']);p.draw_circle(q,3,color=RED,fill=RED);text(p,q.x+5,q.y-4,door['id']+' '+str(door['w'])+'m',8)
 paras(p,[
  '設備核の外形24×24m。共用前室奥行4m、前廊の幅は約6.75m。',
  '階段：2方向折返し、各階32蹴上げ。片側有効2m、踏面0.30m。描画範囲に加え保守・防災設備の領域を予約。',
  'EV：シャフト4×4m、正面扉1.6m。前室から直接接続し、2mの内部アクセスから多目的WCへ。',
  '男女それぞれ前室から入る。背面に個室各2、側壁に洗面。男性WCには小便器2。多目的WCは4×4m。',
  '個室扉0.9m、男女入口1.6m、多目的WC扉1.2m。手すり、ベビー設備、詳細な給排水は未設計。',
  '店舗のバックヤードは専用室として各店内に確保。共用の搬入は閉店後の店頭/EVを使う運用計画で、架空の専用裏回廊を全店に接続したとは扱わない。',
  '法的な避難人数・距離、階段防火、頭上高さ、EVの駆動・扉コリジョンはGodot実装後と構造検討で確認する。'],x=875,y=150,width=740,size=14,gap=18)
# Vertical diagram is dimensioned across all storeys.
p=page('C館｜全5階の階高・階段・EVの断面','6つの設備核がB1からRFまで連続。B館への移動は1F/2Fでのみ行う。')
x=160;base=835;scale=28
for f in D['floors']:
 y=base-(f['height']+5.35)*scale;p.draw_line((80,y),(780,y),color=INK,width=1);text(p,85,y-10,f['label']+f" {f['height']:+.3f}m",14)
for lo,hi in zip(D['floors'][:-1],D['floors'][1:]):
 rise=hi['height']-lo['height'];y0=base-(lo['height']+5.35)*scale;y1=base-(hi['height']+5.35)*scale
 p.draw_polyline([(190,y0),(240,y0),(375,(y0+y1)/2),(455,(y0+y1)/2),(590,y1),(640,y1)],color=GREEN,width=2)
 text(p,810,(y0+y1)/2,f"{lo['label']}→{hi['label']}：高差{rise:.3f}m、32蹴上げ、1段{rise/32:.5f}m",15)
p.draw_rect(fitz.Rect(690,base-(16.4+5.35)*scale,755,base),color=(.4,.4,.5),width=1.5);text(p,690,base+30,'EV 4×4m / 同一軸',12)
paras(p,['階段は折返しを展開した断面です。15踏面×0.30mの2方向フライト、水平踊り場2.8mを計画します。',
 'RFの囲われた小施設は各棟1つで、それ以外は空の上部階店舗ではなく屋上庭園・回遊床。安全柵1.2m、局所の庇を設計方針とし、全体を屋根で覆いません。',
 '床厚0.32mはゲーム用仮設計値。構造スパン、梁せい、地下の土圧・防水、積雪・雨風・避難認定は未検証です。'],x=80,y=900,size=12,gap=7)
p=page('屋外エスカレーター｜開口・踊り場・断面','1F↔2Fは東の店頭街、2F↔3Fは北のテラス庭に面する。B1/RFへは階段とEVを使用。')
for idx,bank in enumerate([('CE12',[0,1]),('CN23',[1,2])]):
 id,levels=bank;es=[e for e in D['escalators']if e['id'].startswith(id)];foot=unary_union([e['shaft'].union(unary_union(e['landings']))for e in es]);ext=foot.buffer(4).bounds
 for f,rect in zip([next(f for f in D['floors']if f['level']==levels[0]),next(f for f in D['floors']if f['level']==levels[1])],[(55+idx*820,120,430+idx*820,590),(455+idx*820,120,830+idx*820,590)]):
  plan(p,f,ext,rect,True);text(p,rect[0],106,id+' '+f['label'],13)
 rise=next(f['height']for f in D['floors']if f['level']==levels[1])-next(f['height']for f in D['floors']if f['level']==levels[0]);x=90+idx*820;y=800;sc=27
 coords=[(0,0),(3,0),(4.5,0),(16.3,rise),(17.8,rise),(20.8,rise)];p.draw_polyline([(x+a*sc,y-b*sc)for a,b in coords],color=INK,width=1.7)
 text(p,x,y+40,f'高差{rise:.3f}m / 傾斜{math.degrees(math.atan(rise/11.8)):.1f}度',13)
text(p,55,925,'走行水平長11.8m、コーム各1.5m、機械開口長14.8m×2.4m、乗降床3×3.6m。仮設計でありメーカー仕様・実歩行は未検証。',12)
# Explicit B link plans at common world scale.
p=page('B/C接続｜固定受け口とC側の経路','B館v4.1は変更せず、C側の受け方だけを設計。赤い受け口は既存B終点、床高・幅を合わせる。')
for f,point,width,rr in[(D['floors'][1],[-370,-80],8,(50,120,810,760)),(D['floors'][2],[-432,-117],5,(870,120,1630,760))]:
 xy,sc=plan(p,f,(-470,-205,-280,-65),rr,True,True);q=xy(point);p.draw_circle(q,6,color=RED,width=1.5);text(p,q.x+9,q.y,'B固定受け口 '+str(width)+'m',12,RED);text(p,rr[0],105,f['label']+f" 高さ{f['height']:.3f}m",15)
paras(p,['1FはB終点(-370,-80)から南東棟の背面に突っ込まず、棟の東を回って正面の商業街路へ接続します。受け口付近は幅8mを保持。',
 '2FはB終点(-432,-117)から幅5mの短い直線受けを取り、南庭の西縁を回って南西棟の前廊へ。設備核の壁・店舗区画と重ならない経路です。',
 'B1・3F・RFには直接B連絡橋を追加していません。各階からCの階段/EVを通って1F/2Fで館間移動する設計です。B館側のB1/RF設計は今回の範囲外。'],x=55,y=810,size=13,gap=14)
p=page('用途・通路・行き止まりの評価','用途のある設備枝・店舗内の終端・固定B接続を、探索を複雑にするだけの袋小路と区別。',w=1191,h=842)
paras(p,[
'6棟の前廊は巡回する街路に接続。北の生活/スポーツ街、南の飲食街、中央庭園の東西プロムナードと南北の短絡に、それぞれ明確な店頭・広場・昇降設備の終点があります。',
'独立棟の間は地上の庭・屋外移動路、上階は幅を絞ったデッキ。広い植栽床や中庭の空中部分を、目的不明の公開床・宝箱候補として埋めていません。',
'トイレ・EV・階段の内部前室、専用バックルーム、乗降口のアクセス枝は用途上の終端です。BC-1-C/BC-2-Cの端はB館と接続するため、孤立した行き止まりとは扱いません。',
'上階の中央放射路と庭全体の円盤床を廃し、庭の中心を覆わない周縁デッキに限定しました。全ての名前付き通路の中心線が公開床に収まることと、端点が共用主成分へ接続することを検査。機械開口に向かって戻る誤った乗降口アクセスを検査中に発見し、北庭側へ向きを変えて修正済みです。',
'屋外ならではの長い視界と6棟の切り替わりは設計上成立します。一方、全階の同じ店頭配列の見え方、風雨、夜間、3階デッキの高所感とNPC密度は実装後に評価します。'],size=14,gap=20)
# Route ledger, all purposes and destinations visible in the PDF.
for start in range(0,len(D['routes']),20):
 p=page('通路台帳 '+str(start//20+1),'幅はゲーム用設計値。中心線・全座標・公開階はroute-register.csvに収録。',w=1684,h=1000);y=122
 for r in D['routes'][start:start+20]:
  text(p,45,y,r['id'],11);text(p,250,y,r['name'],11);text(p,650,y,str(r['width'])+'m',11);text(p,740,y,','.join(str(x)for x in r['levels']),11);text(p,920,y,r['role'],10);y+=36
p=page('検査結果と未検証事項','図面上の検査と、ゲーム内で実際に歩く検証を混同しません。',w=1191,h=842)
paras(p,[
 f"検査{V['checks']:,}件、合格{V['passed']:,}件、不合格{len(V['failed'])}件。図面の面積交差判定は1×10⁻⁸㎡を使用しています。",
'検査範囲：区画同士の重なり、区画と共用床、公開床/構造床と機械開口、閉鎖帯と公開床、棟同士の独立、主路・壁・棚の干渉、入口/設備/乗降口の到達性、名前付き通路の全中心線と終点、固定B受け口と幅。',
'到達性は共用床を壁・家具・機器から避け、0.35m内側に縮めた最大連結成分からの入口距離で判定。全78区画と6設備核は同じ主成分へ到達します。これは実際のFPSのカプセル形状や経路AIを用いた試験ではありません。',
'既存Cカタログの旧店舗ID11件を新しい同階区画へ全件対応。旧データには入口がないため、旧区画の重心と新店舗入口を比較しており、「旧入口からの移動距離」とは呼びません。',
'未検証：Godotでの実歩行/コリジョン/機器動作、NPC/猫/宝箱経路、群衆・描画負荷、避難/防火・構造・梁下・防水・地下車両の旋回、夜間サインと雨風対策。3館統合のB/A干渉検査は統合資料を参照。',
'本資料は商用ゲーム用の設計案です。実建築の実施設計や法的適合の証明ではありません。Godot本体は変更せず、ユーザー承認後の施工対象として提出します。'],size=13,gap=17)
# All tenant and facility doors, with dimensions and exact coordinates.
for f in D['floors']:
 p=page(f"{f['label']}｜店舗・施設台帳",f"18商業区画の階と施設階を区別。計{len(f['stores'])}区画 / 床高{f['height']:+.3f}m",w=1684,h=1000);y=125
 text(p,45,102,'ID                     種別 / 用途                         区画㎡       間口m       奥行m       入口幅m       WorldX          WorldZ          旧ID',11)
 for s in f['stores']:
  text(p,45,y,s['id'],11);text(p,255,y,s['kind']+' / '+s['category'],11);text(p,650,y,f"{s['polygon'].area:.1f}",11);text(p,780,y,f"{s['frontage_m']:.2f}",11);text(p,910,y,f"{s['depth_m']:.2f}",11);text(p,1030,y,s['door_width_m'],11);text(p,1150,y,f"{s['entry'][0]:.4f}",11);text(p,1320,y,f"{s['entry'][1]:.4f}",11);text(p,1490,y,s['legacy_id']or'-',11);y+=35
 text(p,45,910,'商業店舗54、B1/RFの施設24、合計78区画。各店の専用バックルーム・店内主路・棚配置はgeometry.jsonと拡大図に記録。',12)
p=page('既存C館からのID・座標対応','旧カタログの11区画を同階の新設計区画へ保持。新規IDは既存ゲームIDを上書きしません。',w=1684,h=1000)
y=130
for m in json.loads((O/'id-migration.json').read_text()):
 text(p,45,y,m['old_id'],12);text(p,220,y,f"旧重心({m['old_x']:.3f},{m['old_z']:.3f})",12);text(p,650,y,'→ '+m['new_id'],12);text(p,970,y,f"新入口({m['new_x']:.3f},{m['new_z']:.3f})",12);y+=45
paras(p,['比較基準を区別：旧資料のポリゴン重心であり、旧入口の測量値ではありません。階level=0は1F、level=1は2F。',
 '既存のC館1F8店・2F3店を保持し、用途の近い新しい店舗街へ配置。新規区画と施設には旧IDを捏造していません。',
 'NPC配置・セーブ・スキャン・スキル・ファストトラベル等のゲーム実装との接続は今後の施工工程。本設計でゲームIDを消したり書き換えたりしていません。'],x=45,y=700,size=14,gap=18)
doc.set_toc(TOC);doc.set_metadata({'title':'FIND YOURSELF C館 詳細設計 v1','author':'FIND YOURSELF design team','subject':'Design only; Godot and B wing unchanged'});P=R/'downloads/FIND_YOURSELF-C-Detailed-Design-v1.pdf';doc.save(P,garbage=4,deflate=True);print('PDF',len(doc),P)
