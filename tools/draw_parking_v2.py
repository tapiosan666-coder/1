"""Vector detail set for five external parking facilities, all 17 parking decks."""
from pathlib import Path
import sys,json,math,hashlib,collections,csv
sys.path.append('/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
import fitz
from shapely.geometry import shape,box,Polygon,LineString,Point
from shapely.ops import unary_union
R=Path(__file__).resolve().parents[1];O=R/'docs/parking-blocks-v2';FONT=R/'assets/fonts/NotoSansCJKjp-Regular.otf';INK=(.12,.22,.26);MUTED=(.35,.43,.46);RED=(.75,.22,.15)
def dec(v):
 if isinstance(v,dict):return shape(v)if'type'in v and('coordinates'in v or'geometries'in v)else{k:dec(x)for k,x in v.items()}
 if isinstance(v,list):return[dec(x)for x in v]
 return v
D=dec(json.loads((O/'geometry.json').read_text()));FAC=D['facilities'];CHECK=json.loads((O/'checks.json').read_text());assert not[q for q in CHECK if not q['pass_']], [q for q in CHECK if not q['pass_']][:5]
CAP=json.loads((O/'capacity.json').read_text());TOTAL=sum(v['count']for v in CAP);COL={'general':(.75,.84,.9),'comfort':(.91,.85,.66),'accessible':(.3,.67,.9),'EV':(.43,.72,.49),'staff':(.65,.64,.62)};CATJP={'general':'一般','comfort':'ゆとり','accessible':'身障者用','EV':'充電EV','staff':'職員'}
doc=fitz.open();toc=[];DECKPAGES=[]
def text(p,x,y,s,size=12,col=INK):p.insert_text((x,y),str(s),fontname=('helv'if str(s).isascii()else'jp'),fontsize=size,color=col)
def page(title,sub='',w=1684,h=1000):
 p=doc.new_page(width=w,height=h);p.insert_font(fontname='jp',fontfile=str(FONT));text(p,40,42,title,23);text(p,40,67,sub,10,MUTED);p.draw_line((40,82),(w-40,82),color=(.22,.48,.42));text(p,40,h-20,f'FIND YOURSELF / 外部駐車ブロック v2 / 図面のみ・ゲーム未改修 / 2026-10-26   •   {len(doc):02}',9,MUTED);toc.append([1,title,len(doc)]);return p
def paras(p,items,x=45,y=115,size=14,gap=18,width=None):
 width=width or p.rect.width-x-45;font=fitz.Font(fontfile=str(FONT))
 for s in items:
  cur=''
  for ch in s:
   if ch=='\n'or font.text_length(cur+ch,fontsize=size)>width:text(p,x,y,cur,size);y+=size*1.6;cur=''if ch=='\n'else ch
   else:cur+=ch
  if cur:text(p,x,y,cur,size);y+=size*1.6
  y+=gap
 return y

def polygons(g):return[]if g.is_empty else[g]if g.geom_type=='Polygon'else[p for p in getattr(g,'geoms',[])if p.geom_type=='Polygon']
def geom(p,g,xy,fill=None,col=INK,width=.4):
 for poly in polygons(g):
  sh=p.new_shape();sh.draw_polyline([xy(q)for q in poly.exterior.coords])
  for ring in poly.interiors:sh.draw_polyline([xy(q)for q in ring.coords])
  sh.finish(color=col,fill=fill,width=width,even_odd=True);sh.commit()
def line(p,coords,xy,col=INK,width=.5,dashes=None):
 if len(coords)>1:p.draw_polyline([xy(q)for q in coords],color=col,width=width,dashes=dashes)
def arrow(p,a,b,xy,col=INK,width=.8):
 line(p,[a,b],xy,col,width);dx,dz=b[0]-a[0],b[1]-a[1];ll=math.hypot(dx,dz)
 if not ll:return
 u=(dx/ll,dz/ll);n=(-u[1],u[0]);line(p,[(b[0]-u[0]*1.5+n[0]*.7,b[1]-u[1]*1.5+n[1]*.7),b,(b[0]-u[0]*1.5-n[0]*.7,b[1]-u[1]*1.5-n[1]*.7)],xy,col,width)
def xymap(extent,rect):
 x,z,xx,zz=extent;r=fitz.Rect(rect);s=min(r.width/(xx-x),r.height/(zz-z));ox=r.x0+(r.width-s*(xx-x))/2;oz=r.y0+(r.height-s*(zz-z))/2;return lambda q:fitz.Point(ox+(q[0]-x)*s,oz+(q[1]-z)*s),s

def plan(p,fac,f,rect,extent=None,ids=True,turns=False):
 extent=extent or f['shell'].buffer(3).bounds;xy,s=xymap(extent,rect);clip=box(*extent)
 geom(p,f['shell'].intersection(clip),xy,(.93,.93,.9),INK,.8);geom(p,f['vehicle_aisles'].intersection(clip),xy,(.77,.79,.81),(.5,.53,.55),.3);geom(p,f['protected_pedestrian'].intersection(clip),xy,(.65,.86,.67),(.2,.5,.3),.4)
 for q in polygons(f['crossings'].intersection(clip)):
  geom(p,q,xy,(.95,.95,.92),(.28,.42,.32),.3);a,b,c,d=q.bounds
  for t in np_range(b,d,.8)if d-b>=c-a else np_range(a,c,.8):
   stripe=box(a,t,c,min(t+.35,d))if d-b>=c-a else box(t,b,min(t+.35,c),d);geom(p,stripe.intersection(q),xy,(.35,.48,.4),(.35,.48,.4),.05)
 for st in f['stalls']:
  if not st['polygon'].intersects(clip):continue
  geom(p,st['polygon'].intersection(clip),xy,COL[st['category']],(.2,.35,.4),.25)
  if not st['side_access_aisle'].is_empty:geom(p,st['side_access_aisle'].intersection(clip),xy,(.6,.82,.88),(.2,.5,.6),.3)
  if ids and clip.covers(st['polygon'].centroid):
   q=xy(st['polygon'].centroid.coords[0]);text(p,q.x-4,q.y+1.5,st['id'].split('-')[-1],3.8)
  a=st['vehicle_entry'];b=[a[0],a[1]+st['parking_direction'][1]*.8];arrow(p,a,b,xy,(.3,.42,.45),.25)
 geom(p,f['columns'].intersection(clip),xy,(.2,.23,.25),INK,.1)
 for c in f['cores']:
  geom(p,c['outline'].intersection(clip),xy,(.88,.77,.73),(.5,.3,.25),.6);geom(p,c['public_lobby'].intersection(clip),xy,(.65,.86,.67),(.2,.5,.3),.3);geom(p,c['stair'].intersection(clip),xy,(.64,.66,.66),INK,.4);geom(p,c['elevator'].intersection(clip),xy,(.56,.76,.83),INK,.4)
  if clip.covers(Point(c['entry'])):q=xy(c['entry']);text(p,q.x+2,q.y-3,c['id'].split('-')[-1],5)
 for lane in fac['ramp_lanes']:
  geom(p,lane['shaft'].intersection(clip),xy,(.52,.60,.69),(.2,.33,.5),.5)
  cx=lane['lower_port'][0];a=lane['lower_port'];b=lane['upper_port'];a=[cx,a[1]+8];b=[cx,b[1]-8]
  if lane['direction']=='DOWN':a,b=b,a
  if clip.intersects(lane['shaft']):arrow(p,a,b,xy,(.1,.22,.45),1.1);q=xy(lane['shaft'].centroid.coords[0]);text(p,q.x+2,q.y,lane['direction']+' 4m',5)
 geom(p,f['ramp_terminal_barriers'].intersection(clip),xy,(.62,.22,.18),(.62,.22,.18),.5)
 geom(p,f['edge_guard'].intersection(clip),xy,(.15,.24,.28),INK,.3)
 if not f['temporary_guard_until_bridge_built'].is_empty:geom(p,f['temporary_guard_until_bridge_built'].intersection(clip),xy,(.25,.44,.7),(.25,.44,.7),.4)
 for port in fac['portals']:
  if port['level']!=f['level']or not clip.buffer(.1).covers(Point(port['point'])):continue
  x,z=port['point'];n=port['normal'];u=(-n[1],n[0]);w=port['width_m'];a=[x-u[0]*w/2,z-u[1]*w/2];b=[x+u[0]*w/2,z+u[1]*w/2];line(p,[a,b],xy,RED,2.0);q=xy((x,z));label=('車'if port['type'].startswith('vehicle')else'歩')+f'{w}m';text(p,q.x+4,q.y-4,label,6,RED)
 if turns:
  for q in fac['turn_templates']:geom(p,q['swept'].intersection(clip),xy,None,(.75,.33,.24),.5)
 # Numeric coordinate grid and fixed metric scale.
 for x in range(math.ceil(extent[0]/25)*25,math.floor(extent[2]/25)*25+1,25):q=xy((x,extent[3]));text(p,q.x-7,rect[3]+14,str(x),7,MUTED)
 for z in range(math.ceil(extent[1]/25)*25,math.floor(extent[3]/25)*25+1,25):q=xy((extent[0],z));text(p,rect[0]-34,q.y,str(z),7,MUTED)
 return xy,s

def np_range(a,b,step):
 out=[];v=a
 while v<b:out.append(v);v+=step
 return out

p=page('全館外部駐車ブロック｜詳細設計 v2','2棟の7段立体＋3か所の平面駐車場。既存A/C内部・B館v4.1・Godotゲーム本体は変更していません。',w=1191,h=842)
paras(p,[f"実際に描画・ID化した外部駐車マスは{TOTAL:,}台です。A館既存22台、B館地下/屋上等のroot統合追加分を含めて水増ししていません。",'A東/B南は各7段、P1 0m／P2 2.750m／P3 5.525m／P4 8.200m／P5 10.875m／P6 13.625m／P7屋上16.400m。P3/P5/P7はモールの2F/3F/RFの高さに一致します。','主車路は双方向6m。上下斜路は別々の4m一方向、緩和3m＋直線22m＋緩和3m。P1の高端/P7の低端は防護壁で閉鎖し、架空の次階へ進ませません。最急勾配11.1%、水平平場は下端10.5m/上端9.5mを確保します。','標準2.5×5m、ゆとり2.7×5.2m、身障者3.5×5m＋側方1.2m。後方2m保護歩道、列末の保護歩道、指定横断歩道で階段/EV/地上出口へ接続。','身障者/EV/職員は一般駐車と区分して数えます。大型配送トラックやバスの荷捌きは本設計へ混ぜず、root側の別系統で扱います。','指定敷地ブロック全部を舗装せず、実際のコンパクトな施設範囲を設計。外部の全体車路・モール接続・地下へのスロープはroot統合資料と照合してください。','構造荷重・地盤・排水・法定駐車/避難基準や実車走行、ゲーム車両/歩行AIの検証結果ではありません。ゲーム用設計値として承認を求める資料です。'],size=14,gap=20)
p=page('全台数・用途内訳','各階の台数は図面上の個別ID付きマスを集計。EVや職員を別カウントして総数に二重計上しません。',w=1191,h=842)
y=120;text(p,45,y,'施設                      階層         一般     ゆとり    身障者     EV       職員      合計',12);y+=34
for fac in FAC:
 count=collections.Counter(s['category']for f in fac['floors']for s in f['stalls']);text(p,45,y,fac['id']+' '+fac['name'],12);text(p,340,y,len(fac['floors']),12)
 for x,k in[(460,'general'),(560,'comfort'),(670,'accessible'),(780,'EV'),(880,'staff')]:text(p,x,y,count[k],12)
 text(p,990,y,sum(count.values()),13);y+=47
text(p,45,y+20,f'外部合計 {TOTAL:,}台 / 立体屋上P7も個別マスを配置 / 既存A22台・B追加区画は別集計',15)
paras(p,['駐車マスはstall-ledger.csvとgeometry.jsonに facility/level/id/category/width/length/車路前面点/後方歩道接続点/実ポリゴンを収録。全IDは施設-段-4桁番号です。','図面内は4桁番号を表示し、各ページの接頭辞と組み合わせて一意に照合できます。集計上の台数と実図形の数が一致することを検査します。','EV充電の受電容量・充電器実型式、身障者指定数の法的充足、歩行実測・運用費・収益は未検証です。用途を物理マスと別の架空容量として加算していません。'],y=y+75,size=13,gap=20)
# Every deck, including intermediate and roof decks, gets a full plan.
for fac in FAC:
 for f in fac['floors']:
  mall=('モール1F'if f['level']==0 else'モール2F高'if f['level']==2 else'モール3F高'if f['level']==4 else'モールRF高'if f['level']==6 else'中間駐車段（モール直結なし）')if fac['kind']=='garage'else'地上平面'
  p=page(f"{fac['name']}｜{f['label']} +{f['height']:.3f}m / {len(f['stalls'])}台",f"{mall} / ID接頭辞 {fac['id']}-L{f['level']:02}- / 青=一般・黄=ゆとり・水色=身障者・緑=EV・灰=職員")
  plan(p,fac,f,(55,110,1625,850),ids=True);text(p,55,880,f"ID prefix: {fac['id']}-L{f['level']:02}-  /  4-digit bay labels + prefix = full stall ID",9);DECKPAGES.append(dict(facility=fac['id'],level=f['level'],page=len(doc),prefix=f"{fac['id']}-L{f['level']:02}-",count=len(f['stalls'])))
  count=collections.Counter(s['category']for s in f['stalls']);paras(p,['台数：'+' / '.join(CATJP[k]+str(count[k])for k in COL)+'。赤は地上/橋受け口、緑は保護歩道、縞は指定横断歩道。','外周防護/転落防止1.2m。P1高端/P7低端の斜路口は赤茶の防護壁で閉鎖。上階の未接続口は仮設柵を維持し、橋が実際につながるまで開放しない。'if fac['kind']=='garage'else'平面場に不要な階段/EVを置かず、保護歩道で地上出口へ。身障者側方通路と主保護歩道はフラットに接続。','4.8×2.0m車両のR6m旋回図形を車路・斜路平場内で検査。個々の駐車の切返しや実車制御を実測した結果ではありません。'],x=55,y=895,size=11,gap=7)
 # Large close-up of the first parking module, dimensions and wheelchair/EV access.
 f=fac['floors'][0];bb=f['main'].bounds;extent=(bb[0]+8,bb[1],min(bb[2],bb[0]+90),min(bb[3],bb[1]+57));p=page(fac['name']+'｜駐車モジュール拡大','標準/ゆとり/身障者側方通路・後方保護歩道・柱・車路・横断歩道とEV/階段前室を拡大。')
 plan(p,fac,f,(60,110,1620,810),extent,True,False)
 paras(p,['車路6m、後方保護歩道2m。背面サービス帯に0.4m角柱を配置し、駐車ポリゴン・歩道・各マスの後方アクセス線へ食い込まないことを検査。','身障者マス3.5m＋側方1.2m、ゆとりマス2.7m×5.2m。幾何上の位置を具体化した設計値で、構造/バリアフリー適合の認証ではない。'],x=55,y=865,size=13,gap=18)
# Dimensioned parking unit, using simple coordinates rather than an unlabeled schematic.
p=page('共通寸法｜保護歩道を挟む両面モジュール','車路・駐車・保護歩道を意図的に分離。寸法単位m。',w=1191,h=842)
xy,s=xymap((0,0,18,25),(55,115,620,705));geom(p,box(0,0,18,6),xy,(.78,.8,.82));geom(p,box(0,6,18,11.8),xy,(.92,.91,.87));geom(p,box(0,11.8,18,13.8),xy,(.65,.86,.67));geom(p,box(0,13.8,18,19.6),xy,(.92,.91,.87));geom(p,box(0,19.6,18,25),xy,(.78,.8,.82))
for a,b,label in[(0,6,'車路6.0'),(6,11.8,'駐車+構造帯5.8'),(11.8,13.8,'保護歩道2.0'),(13.8,19.6,'駐車+構造帯5.8')]:q=xy((.4,(a+b)/2));text(p,q.x,q.y,label,10)
paras(p,['標準マス2.5×5.0m、ゆとり2.7×5.2m。モジュールの駐車側奥行5.8mには、車後方のアクセス/構造柱帯を含む。','柱は0.4m角、奥行方向のサービス帯に置き、マスと主歩道に干渉させない。柱割りと部材/床スパンは概念的な支持配置で構造計算ではない。','側方通路1.2mは身障者マスとは別ポリゴン。歩道2.0mへ連続し、段差は設けない。指定横断部は歩道優先の停止線/低速運用を計画。','各マスの後方接続は図面の線分/距離で検査。駐車中車両の扉や車椅子の実動作、運転者の切返しを再現した検査ではない。'],x=675,y=150,size=14,gap=25,width=470)
for fac in FAC[:2]:
 f=fac['floors'][2];bb=f['main'].bounds;x,z,w=bb[0],bb[1],bb[2]-bb[0]
 p=page(fac['name']+'｜斜路・平場・旋回の拡大','UP/DOWN各4m一方向。低速車路と斜路の合流は停止/譲り標示を設計。大型配送車は通さない。')
 plan(p,fac,f,(55,110,1000,850),(x+w-15,z+1,x+w+33,z+63),ids=False,turns=True)
 paras(p,['下端平場10.5m、上端9.5m。斜路の水平ラン28m（緩和3m＋直線22m＋緩和3m）、段の高差は2.675～2.775m。','実際の断面は縦曲線をサンプリングし、平場で勾配0、直線区間で10.7～11.1%。架空の段差ワープで上下接続していない。','赤線は4.8×2.0m設計車のR6m車体包絡のサンプル。マス列端の旋回と斜路平場の右左折が通る図形内に収まることを検査。','斜路両側は4m内法を侵さない位置に1.1m防護壁。平場・車路と共用歩道を交差させず、歩行者を斜路へ誘導しない。','UP到着側の上端から、次段のUP低端へは同じ階の車路を回って移動する。階を飛ばす接続ではなく、上下別レーンの連続系統。'],x=1060,y=155,size=13,gap=22,width=560)
 p=page(fac['name']+'｜全6階間の斜路断面','断面は横方向と鉛直方向を別倍率で示す。実寸・勾配は数値を参照。段差のない縦接続を確認する設計図。')
 for row,lo in enumerate(range(6)):
  ramp=next(r for r in fac['ramps']if min(r['from_level'],r['to_level'])==lo and r['direction']=='UP');ox=90+(row%2)*810;oz=300+(row//2)*290;sx=17;sy=45;profile=ramp['profile_xyz'];base=min(q[1]for q in profile);pts=[(ox+(q[2]-profile[0][2])*sx,oz-(q[1]-base)*sy)for q in profile];p.draw_polyline(pts,color=INK,width=1.5);text(p,ox,oz+30,f'P{lo+1}→P{lo+2}  +{ramp["rise_m"]:.3f}m / {ramp["max_grade_percent"]:.1f}%',12);text(p,ox,oz+55,'下端10.5m平場 / 緩和3+直線22+緩和3m / 上端9.5m平場',9)
# Core type and 7-deck section.
p=page('立体駐車場｜4階段核・2EV核・前室の詳細','前側2核はEV併設、後側2核は階段。平面駐車場に不要な昇降核は設けない。')
fac=FAC[0];f=fac['floors'][0]
for ci,(core,rr)in enumerate([(f['cores'][0],(60,120,780,650)),(f['cores'][2],(880,120,1600,650))]):
 xy,s=xymap(core['outline'].buffer(.8).bounds,rr);geom(p,core['outline'],xy,(.92,.87,.81));geom(p,core['stair'],xy,(.65,.68,.68));geom(p,core['elevator'],xy,(.53,.75,.82));geom(p,core['public_lobby'],xy,(.62,.86,.65));sx,sz,ex,ez=core['stair'].bounds
 for k in range(8):line(p,[(sx+.25,sz+1.6+k*.3),(sx+2.25,sz+1.6+k*.3)],xy,INK,.6);line(p,[(sx+2.7,sz+1.6+k*.3),(sx+4.7,sz+1.6+k*.3)],xy,INK,.6)
 for pt,name in[(core['stair_entry'],'階段扉1.5m'),(core['elevator_entry'],'EV扉1.4m')]:
  if pt:q=xy(pt);p.draw_circle(q,3,color=RED,fill=RED);text(p,q.x+5,q.y-5,name,11)
 text(p,rr[0],690,'前側：階段＋EV＋前室'if ci==0 else'後側：階段＋前室',15)
paras(p,['階段は2.0m内法×2フライト、各段16蹴上げ（8＋8）、踏面0.30m、踊場1.5m以上。最大蹴上0.17344m。各核で全7段を接続。','EVシャフト3×3m、扉1.4m、前室は保護歩道へ接続。車路の中へ直接降りず、階段を横切るロビー短絡も作らない。','EV実機・地震/火災/避難性能、階段の梁下、扉・敷居の実コリジョンは未検証。'],x=55,y=755,size=13,gap=21)
p=page('各段の高さ・制限高・車歩の系統','段の高さはモールに合わせ、奇数の中間段に無理なモール連絡橋を追加しない。',w=1191,h=842)
paras(p,['高さ：0.000／2.750／5.525／8.200／10.875／13.625／16.400m。屋上も車マスを実際に配置し、未接続の外周開口は防護柵で閉じる。','構造床厚0.30m・設備帯0.15mを仮定した最小クリアランスは2.225m。車両制限高は2.0mとして入口・分岐に表示する設計。実際の梁/設備/構造計算で減少する場合は高さ/段構成の再検討が必要。','これは無梁床構成を仮定したゲーム用計画値。荷重・柱スパン・耐震・防火を検証済みとせず、構造/設備の詳細が確定する前に実建物やゲーム物理の完成扱いにしない。','車は専用UP/DOWNで全7段へ、歩行者は保護歩道→前室→階段/EV→地上出口へ接続。共用の車線上を歩行者通路として丸ごと兼用せず、指定横断部だけを例外にする。','モール橋はP3/P5/P7高の歩行受け口。B南P1には新B館地下へのスロープ受け口、P7にはB RF車橋受け口を別に設ける。橋/外部斜路の本体はrootの統合資料へ。'],size=14,gap=24)
p=page('B南｜G0地下連絡口・RF車橋と歩行橋の分離','北東の受け口はG0/RFだけ。他の中間段へ外部車口を開けない。')
fac=FAC[1]
for f,rr in[(fac['floors'][0],(55,130,790,730)),(fac['floors'][6],(880,130,1615,730))]:text(p,rr[0],108,f['label']+f" +{f['height']:.3f}m",15);plan(p,fac,f,rr,(-578,167,-520,214),ids=True)
paras(p,['車口 World(-540,170)・幅7m北向き。RF歩行口(-548,170)・幅4m北向きは、車口と平面で離隔し保護歩道へ接続。','主体の東角からはみ出す部分に明示的な受入平場を追加し、幅全体を床で支持。車/歩のアプローチが重ならないことを検査。','G0の車口はrootの新B1スロープへ、RFはB新屋上車橋へ。G0主車口(-677,170)と地上歩行口(-630,170)は維持。外側の道路/橋/スロープはroot担当。'],x=55,y=790,size=13,gap=18)
# Full portal register and per-deck table, rather than only typical-floor counts.
p=page('接続受け口一覧｜root敷地ネットワークとの境界','World X/Z m、向きは施設から外へ。モール内部やB館v4.1の既存座標は変更しない。',w=1684,h=1000);y=117
for fac in FAC:
 for port in fac['portals']:
  text(p,45,y,port['id'],10);text(p,400,y,port['type'],10);text(p,800,y,f"L{port['level']} +{port['height']:.3f}m",10);text(p,1040,y,str(port['point']),10);text(p,1265,y,f"{port['width_m']}m / {port['normal']}",10);y+=30
p=page('全段台数表｜描画マスと一致する実数','全17面。用途内訳CSV/JSONとマス台帳を同梱。',w=1191,h=842);y=115
text(p,45,y,'施設 / 段       高さm      一般     ゆとり    身障者     EV       職員     合計',11);y+=28
for row in CAP:
 text(p,45,y,f"{row['facility']} L{row['level']}",11);text(p,260,y,f"{row['height']:.3f}",11)
 for x,k in[(400,'general'),(510,'comfort'),(620,'accessible'),(730,'EV'),(840,'staff')]:text(p,x,y,row['categories'].get(k,0),11)
 text(p,960,y,row['count'],12);y+=31
p=page('図面検査と未検証事項','図面上の静的幾何と接続を確認。実車試験・ゲーム内走行/実歩行ではない。',w=1191,h=842)
paras(p,[f"生成時の図面検査{len(CHECK):,}件、不合格0。全{TOTAL:,}台の車路前面接続・後方歩道接続、柱/開口/車路との非交差、重複マス、保護歩道と車路の横断例外、各段車路/歩道の連結、階段/EV入口、斜路平場、RF/G0受入の全幅支持を確認。",'旋回検査は4.8×2.0mの設計車体をR6mの軌跡でサンプルした2D図形。列末端と斜路平場を対象とし、隣接車両がいる各駐車の切返し、車両軸距/操舵/勾配変化の実動作、背の高い配送車を検証済みとはしない。','歩行接続は保護路・前室・階段/EVポータルの幾何連結。駐車中車両のドア開閉、車椅子の操作や交通誘導を含む実測ではない。出口までの移動距離・運用容量・混雑は今後の評価対象。','未検証：構造荷重・柱スパン/接合・地盤/排水、法定設備・消防/避難、受電/充電容量、ガードの実物衝突、梁下/設備、外部道路の信号/見通しと実車走行。','ゲーム本体、NPC、スキャン、セーブ、既存館は変更していない。root全体図との接続確認後に図面を提出し、承認前に実装を始めない。'],size=14,gap=23)
doc.set_toc(toc);doc.set_metadata({'title':'FIND YOURSELF 外部駐車ブロック詳細設計 v2','author':'FIND YOURSELF design review','subject':'Design only; no mall/game modifications'});P=R/'downloads/FIND_YOURSELF-Parking-Blocks-v2.pdf';doc.save(P,garbage=4,deflate=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();(O/'pdf-deck-pages.json').write_text(json.dumps(DECKPAGES,indent=2));(O/'pdf-source.json').write_text(json.dumps(dict(geometry_sha256=sha(O/'geometry.json'),checks_sha256=sha(O/'checks.json'),capacity_sha256=sha(O/'capacity.json'),pdf_sha256=sha(P),pages=len(doc)),indent=2));print('PDF',len(doc),P)
