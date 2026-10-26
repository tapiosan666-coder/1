"""Vector drawing set for B v4. Reads only immutable v3 and the new design data."""
from pathlib import Path
import sys,json,ast,math,csv,collections,hashlib,zipfile,subprocess
sys.path.append('/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
import fitz
from shapely.geometry import shape,Polygon,LineString,Point,box
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/b-purpose-review-v4';BASE=ROOT/'docs/b-detailed-review-v3';FONT=ROOT/'assets/fonts/NotoSansCJKjp-Regular.otf'
def dec(o):
 if isinstance(o,dict):return shape(o)if'type'in o and('coordinates'in o or'geometries'in o) else{k:dec(v)for k,v in o.items()}
 if isinstance(o,list):return[dec(v)for v in o]
 return o
D=dec(json.loads((OUT/'geometry.json').read_text()));OLD=dec(json.loads((BASE/'geometry.json').read_text()));FLOORS=D['floors'];PLAZAS=D['plazas'];CORES=D['cores'];ALL_ESC=D['escalators'];VOIDS=[p['void']for p in PLAZAS];CHECKS=json.loads((OUT/'checks.json').read_text());ROUTES=D['routes']
assert not[x for x in CHECKS if not x['pass_']], [x for x in CHECKS if not x['pass_']][:10]
# Reuse reviewed, pure drawing functions without importing or executing the v3 generator.
INK=(.12,.22,.26);MUTED=(.34,.42,.45);RED=(.72,.23,.16)
source=(ROOT/'tools/review_b_drawings.py').read_text();tree=ast.parse(source);keep={'polys','drawg','line','dot','text','paragraphs','viewmap'}
for node in tree.body:
 if isinstance(node,ast.FunctionDef)and node.name in keep:
  snippet=ast.get_source_segment(source,node)
  if node.name=='viewmap':snippet=snippet.replace("f'AT-{j+1}'","['P-W','P-T','P-L'][j]")
  exec(compile(snippet,'reviewed_vector_helpers','exec'),globals())
INK=(.12,.22,.26);MUTED=(.34,.42,.45);RED=(.72,.23,.16)
doc=fitz.open();TOC=[]
def world(p):return[p[0]-714,p[1]-30]
def newpage(title,subtitle='',w=1684,h=1000):
 p=doc.new_page(width=w,height=h);p.insert_font(fontname='jp',fontfile=str(FONT));text(p,40,42,title,22);text(p,40,68,subtitle,10,MUTED);text(p,40,h-20,f'FIND YOURSELF / B館 用途から見直す詳細設計 v4 / 2026-10-26 / 図面のみ・ゲーム未改修   •   {len(doc):02}',9,MUTED);TOC.append([1,title,len(doc)]);return p
old_viewmap=viewmap
def plan(p,f,extent,rect,detail=False,routelabel=False):
 xy,scale=old_viewmap(p,f,extent,rect,detail);clip=box(*extent)
 for store in f['stores']:
  if detail:
   doors=Point(store['entry']).buffer(store['door_width_m']/2+.1)
   if'secondary_entry'in store:doors=doors.union(Point(store['secondary_entry']).buffer(3.1))
   for gl in store.get('glazed_frontages',[]):
    gg=gl.intersection(clip).difference(doors)
    for seg in([gg]if gg.geom_type=='LineString'else getattr(gg,'geoms',[])):
     if seg.geom_type=='LineString'and not seg.is_empty:line(p,list(seg.coords),xy,(.18,.55,.68),1.)
  if'secondary_entry'in store and clip.covers(Point(store['secondary_entry'])):dot(p,store['secondary_entry'],xy,2.2)
 for zone in f.get('service_zones',[]):
  drawg(p,zone['polygon'].intersection(clip),xy,(.84,.83,.77),(.47,.45,.39),.6)
  if clip.covers(Point(zone['entry'])):dot(p,zone['entry'],xy,2.2,(.62,.34,.18))
  if clip.covers(zone['polygon'].representative_point()):q=xy(zone['polygon'].representative_point().coords[0]);text(p,q.x-15,q.y,zone['id'],7)
 for g in f.get('furniture',[]):
  colors={'bench':(.52,.34,.18),'planter':(.29,.49,.32),'object':(.43,.51,.55),'clock':(.72,.53,.22)}
  drawg(p,g['geom'].intersection(clip),xy,colors[g['kind']],INK,.4)
  if detail and clip.covers(g['geom'].centroid):q=xy(g['geom'].centroid.coords[0]);text(p,q.x+3,q.y-3,{'bench':'ベンチ','planter':'植栽','clock':'時計','object':'翼オブジェ'}[g['kind']],6)
 for sign in f.get('wayfinding',[]):
  if clip.covers(Point(sign['point'])):
   q=xy(sign['point']);p.draw_circle(q,3,color=(.2,.4,.65),width=.7);text(p,q.x+5,q.y-3,'案内（上部）',7,(.2,.4,.65))
 for w in f.get('waiting',[]):
  if clip.covers(Point(w['point'])):p.draw_circle(xy(w['point']),.35*scale,color=(.3,.35,.4),width=.5)
 for c in CORES:
  if f['floor']!=1:continue
  door=c.get('ground_discharge_door')
  if door and clip.covers(Point(door['p'])):dot(p,door['p'],xy,2,RED)
 if f['floor']==1:
  for e in D['egress']:
   drawg(p,e['poly'].intersection(clip),xy,(.94,.85,.78),RED,.5)
   mid=LineString(e['points']).interpolate(.5,normalized=True)
   if clip.covers(mid):q=xy(mid.coords[0]);text(p,q.x+3,q.y,e['id']+' / 3m',7,RED)
 if routelabel:
  for r in ROUTES:
   if f['floor']not in r['levels']:continue
   mid=LineString(r['points']).interpolate(.5,normalized=True)
   if clip.covers(mid):q=xy(mid.coords[0]);text(p,q.x-12,q.y,r['id'],7,(.18,.36,.55))
 for pp in PLAZAS:
  c=pp['void'].centroid
  if clip.covers(c):q=xy(c.coords[0]);text(p,q.x-22,q.y+23,pp['name'],8)
 return xy,scale
body=FLOORS[0]['shell'];bound=body.bounds;counts=[len(f['stores'])for f in FLOORS]
summary=newpage('B館 v4 / 商業施設の動線から見直した設計','v3追加修正の提出図。用途・接続・広場の景観・設備到達を一緒に確認する。',w=1190,h=842)
paragraphs(summary,[
 '今回もGodotシーン・マップ・NPC・スキャン・APのコード、既存ゲーム配布物を変更していない。',
 '旧walkポリゴンの継ぎ足しをやめ、用途と接続先を持つ通路・広場だけで共用部を組み直した。',
 '設備核の長い枝道を短縮。お手洗い・EV・階段は北/南の専門店街へ直接接続する。',
 '翼：細長い吹き抜けと核店の前庭。時：横断橋と待合前庭。光：曲面で開く端部広場。',
 '広場の中央を店で埋めず、通行の帯を先に空けてからベンチ・植栽・待ち合わせ点を配置した。',
 '南西の空白接続は短縮し、カフェ/雑貨の入口を持つ店舗街として再計画した。',
 f'計画区画：1F {counts[0]}、2F {counts[1]}、3F {counts[2]}。廃止したv3計画IDも変更台帳に記録。',
 f'図面検査 {len(CHECKS):,}件・不合格0。1m格子の経路と、実形状による線分検査を併用。',
 '立体図はこの設計データから作成した別モデル。ゲーム画面でも実歩行テストでもない。',
 '搬入は地上の核店裏口→共用通路（閉館後）→兼用EV→店内主路→バックルーム。',
 '専用裏回廊の全店接続、避難性能/防火、梁下、実際の人混みと負荷は未検証。',
 '確認したい内容：通路の役割、広場の違い、休憩位置、設備配置、搬入方式。承認後に施工する。'
],size=13,gap=45)
# Before/after sheets use the same view extent, no moving scale to exaggerate the revision.
for f,old in zip(FLOORS,OLD['floors']):
 p=newpage(f"{f['floor']}F / v3 → v4 比較",'左右同じ縮尺。細部は後続の拡大図。旧図の灰色は設備予約帯、新図は共用倉庫の入口も表示。')
 saved=(CORES,ALL_ESC,VOIDS);CORES=OLD['cores'];ALL_ESC=OLD['escalators'];VOIDS=[p['void']for p in OLD['plazas']]if'plazas'in OLD else[Polygon(v)for v in json.loads((BASE/'input/B_completed_plan_geometry.json').read_text())[0]['atrium_polygon']]
 old_viewmap(p,old,(-45,-95,610,195),(55,115,810,730),False)
 CORES,ALL_ESC,VOIDS=saved
 plan(p,f,(-45,-95,610,195),(870,115,1625,730),False,True)
 text(p,55,95,'修正前 v3',15);text(p,870,95,'修正後 v4',15)
 paragraphs(p,[
  'R01：旧西端の余分な折返しを削除。核店の入口に正面から接続する。',
  'R02：K1/K2/K3を専門店街の近くへ移設。設備用の必要な枝以外を残さない。',
  'R03：3広場の開口・上下動線を作り分ける。時の広場には同じXZの横断橋を2/3Fに設ける。',
  'R04：南西接続を短縮して4つの店頭を計画。広場の中を店舗で埋める修正ではない。',
  'R05：各階のベンチ/植栽/待ち合わせ位置を記録し、家具込みの共用経路を検査。'
 ],x=55,y=790,size=12,gap=28)
for f in FLOORS:
 p=newpage(f"B館 {f['floor']}F / 詳細平面・全体",f"床高+{f['height']:.3f}m / {len(f['stores'])}区画 / Local XZ m / 通路IDは用途一覧へ対応 / 主軸16m・枝道9m・設備前8m")
 plan(p,f,(-45,-95,610,195),(60,105,1620,845),False,True)
 paragraphs(p,['赤点＝店舗入口、茶点＝共用倉庫入口、緑＝植栽、茶＝ベンチ、灰＝非公開の躯体/設備帯。',
 'BC/ABの本体外部分は館間の歩行路/連絡橋。店舗がないからといって屋内の空廊下として扱わない。',
 '1FのEX-K1～3は階段から外部への幅3mの放流路。法定の避難適合を認定する図ではない。'],x=60,y=895,size=11,gap=23)
 for k,(a,b)in enumerate([(-40,170),(160,355),(345,535)],1):
  p=newpage(f"B館 {f['floor']}F / 店舗・共用部拡大 {k}",'実壁厚0.25m・通常入口2.4m・核店6m / 店舗主路、棚配置帯、専用バックルーム、共用倉庫入口を図示。')
  plan(p,f,(a,0,b,195),(60,105,1620,890),True,True)
  text(p,60,937,'灰色帯は公開の空き広場ではない。ベンチ等の配置は家具台帳、店ID・座標・面積は店舗台帳と一致する。',11)
# Each court has a structural plan and a separate 3D illustration sheet.
for j,pp in enumerate(PLAZAS):
 p=newpage(pp['name']+' / 1F・2F・3F 詳細配置',pp['landscape'])
 e=pp['court'].buffer(5).bounds
 for f,rect0 in zip(FLOORS,[(50,115,545,680),(595,115,1090,680),(1140,115,1635,680)]):
  plan(p,f,e,rect0,True);text(p,rect0[0],95,f"{f['floor']}F +{f['height']:.3f}m",13)
 paragraphs(p,[
  '接続先：'+' / '.join(pp['gateways'])+'（3Fから他館へは2Fへ降りる）',
  '機能：'+pp['role']+'。中央の空きは休憩と見通しのために残す。',
  '上階手すり高1.2m。時の横断橋は幅4m、2/3Fで同じ位置。床厚0.32mを断面に使用。',
  '休憩島を通行帯から外す。植栽は高さ1.4m以下、各階の広場出口に下端3.4mの吊り下げ誘導案内を計画。',
  '主要エスカレーターは吹き抜け側。2台の間は機器帯として塞ぎ、細い抜け道として使わせない。'
 ],x=55,y=745,size=12,gap=31)
 p=newpage(pp['name']+' / 立体イメージと接近時の見え方','設計図から作った別モデル。ゲーム内スクリーンショットではありません。仕上げ・商品・構造部材は簡略表示。前後の店舗街を含む局所モデル。端部は切断し、透明材の反射は省略。')
 for view,rect0,caption in[('axon',(45,120,825,655),'屋根を外した鳥瞰：開口・店舗・回廊の構成'),('eye',(865,120,1645,655),'床上1.65mの接近視点：広場への視界の開き')]:
  imagepath=OUT/'views'/f"{pp['id']}-{view}.png"
  if imagepath.exists():p.insert_image(fitz.Rect(rect0),filename=str(imagepath),keep_proportion=True)
  else:text(p,rect0[0]+20,300,'立体レンダー未生成（この状態で提出しない）',16,RED)
  text(p,rect0[0],690,caption,12)
 observations=[['長い吹き抜けの先に上階ギャラリーを重ね、西核店から広場へ出る変化を明瞭にした。','北と南に昇降機を分け、中央の見通しとベンチの溜まりを空ける。','残る確認：実ゲームの店頭照明とガラス反射で入口が埋もれないか。'],['北の店舗街/連絡口から複数方向へ分配する。横断橋で遠回りを減らす。','橋が上空の一部を隠すため、左右の縦抜けで階数を読ませる計画。南西は待合前庭。','残る確認：橋下面と梁・時計の視線干渉、昇降機の乗降待ちの密度。'],['直線の専門店街の終端を曲面で受け、東核店とA館側への選択が見える。','休憩島を曲面の外周へ寄せ、中央の対角動線を空ける。モビールは床に柱を増やさない。','残る確認：3D実装後の曲面手すりと柱割り、案内板の見える距離。']][j]
 paragraphs(p,observations,x=55,y=760,size=13,gap=44)
# Direction and headroom are distinguished from a tested moving escalator.
p=newpage('吹き抜け・昇降機 / 配置寸法と断面','2台1組の床開口は幅6.4m。機器間1.6mも歩行域から外す。通常銃/ソナー等のロジックには触れない。')
for row,(lo,hi)in enumerate([(1,2),(2,3)]):
 rise={1:5.525,2:5.35}[lo];x=120;y=440+row*320;sc=30
 coords=[(0,0),(3,0),(4.5,0),(16.3,rise),(17.8,rise),(20.8,rise)]
 p.draw_polyline([(x+a*sc,y-b*sc)for a,b in coords],color=INK,width=2)
 p.draw_polyline([(x+4.5*sc,y-1*sc),(x+16.3*sc,y-(rise+1)*sc)],color=(.34,.45,.48),width=1)
 text(p,830,y-130,f'{lo}F→{hi}F / 高差{rise:.3f}m / 傾斜{math.degrees(math.atan(rise/11.8)):.1f}°',16)
 text(p,830,y-90,'乗降床3m＋水平1.5m＋傾斜11.8m＋水平1.5m＋乗降床3m',12)
 text(p,830,y-55,'外幅2.4m / 段の有効幅1.0m / 2台間の機器帯1.6m',12)
 text(p,830,y-20,'転落防止手すり：回廊1.2m。機器側手すりは斜面に沿う。',12)
paragraphs(p,['ここでの検査：平面の床開口・乗降床・共用域の接続、上階開口と橋の位置合わせ。',
 '未検証：3D梁下の有効2.4m、斜面/乗降の物理判定、動く段、手すりコリジョン、NPCの回避。'],x=80,y=880,size=12,gap=28)
# Actual core-room plans include the corrected accessible WC and EV waiting bay.
for c in CORES:
 p=newpage(c['id']+' / お手洗い・EV・階段の詳細','設備核26×20m。EV前の1m隙間を廃止し、奥行3mの待合を確保。階段の背面放流口は1Fだけ。')
 b=c['outline'].bounds;scale=26;xy=lambda pt:fitz.Point(75+(pt[0]-b[0])*scale,120+(pt[1]-b[1])*scale)
 drawg(p,c['outline'],xy,(.94,.91,.87),INK,1.3)
 labels={'stair':'階段','lift':'EVシャフト','accessible_wc':'多目的WC','lift_lobby':'EVアクセス','women':'女性WC','men':'男性WC','front_lobby':'共用前室','lift_access':'通路2m','ev_front_lobby':'EV前待合3m'}
 for name,room in c['rooms'].items():
  drawg(p,room,xy,(.98,.97,.94),INK,.6);q=xy(room.centroid.coords[0]);text(p,q.x-22,q.y,labels[name],9)
 for g in c['fixtures']:drawg(p,g['geom'],xy,(.75,.84,.84),INK,.5)
 for l in c['vestibule_screens']:line(p,list(l.coords),xy,INK,1.)
 for d in c['doors']:
  a=[d['p'][i]-d['axis'][i]*d['w']/2 for i in[0,1]];bb=[d['p'][i]+d['axis'][i]*d['w']/2 for i in[0,1]];line(p,[a,bb],xy,(1,1,1),3);q=xy(d['p']);dot(p,d['p'],xy,2.5);text(p,q.x+4,q.y-4,d['id']+f" {d['w']}m",8,RED)
 d=c['ground_discharge_door'];out=[d['p'][0],d['p'][1]+(-1 if c['angle']==0 else 1)]
 for pt in[d['p'],out]:line(p,[[pt[0]-.75,pt[1]],[pt[0]+.75,pt[1]]],xy,(1,1,1),3);dot(p,pt,xy,2.5,(.7,.3,.15))
 q=xy(d['p']);text(p,q.x+6,q.y,'EX-'+c['id']+'（1Fのみ）',8,(.7,.3,.15))
 for fixture in c['fixtures']:
  rr=fixture['geom'];q=xy(rr.centroid.coords[0])
  if fixture['kind'].startswith('WC-'):p.draw_oval(fitz.Rect(q.x-5,q.y-8,q.x+5,q.y+8),color=INK,width=.6)
  elif fixture['kind']=='SINK':
   for zz in[-.7,.7]:q=xy((rr.centroid.x,rr.centroid.y+zz));p.draw_circle(q,.18*scale,color=INK,width=.5)
 for d in c['cubicle_doors']:
  a=[d['p'][0]-.5,d['p'][1]];bb=[d['p'][0]+.5,d['p'][1]];line(p,[a,bb],xy,(1,1,1),2.)
 room=c['rooms']['accessible_wc'];q=xy(room.centroid.coords[0]);p.draw_circle(q,.75*scale,color=(.2,.5,.6),dashes='[3 2]',width=.6)
 st=c['rooms']['stair'];a,b1,a1,b2=st.bounds
 for zz in[b1+3+k*.3 for k in range(16)]:
  line(p,[(a+.5,zz),(a+2.5,zz)],xy,INK,.5);line(p,[(a+3.5,zz),(a+5.5,zz)],xy,INK,.5)
 paragraphs(p,[
  f"Local中心 {c['centre']} / World中心 {world(c['centre'])}",
  '各階の同一XZに設備核を積層。B1/RFの接続は今回未設計。',
  'EVシャフト4×4m、開口1.4m、前待合6×3m。閉館後は0.8m幅の搬入カートも共用する案。',
  '多目的WC4×4m、開口1.2m（引戸案）、回転直径1.5mの余地。',
  '女性2個室、男性2個室＋小便器2。前室/側壁洗面/スクリーンを分ける。',
  '階段：32蹴上、16＋16折返し、踏面0.30m、有効2m、踊場1.8m。',
  '1F→2F 蹴上0.17266m、2F→3F 0.16719m。',
  '1Fは背面開口からEX-'+c['id']+'へ放流。上階はこの背面を出口として使わない。',
  '設備入口は共用前室から到達する平面検査を実施。',
  '未検証：EV駆動、扉の開閉、個室の3D衝突、階段の頭上、避難性能。'
 ],x=850,y=150,size=12,gap=46)
# All route names and junction names are printed; IDs alone are not an explanation of purpose.
nodes={'J-C':'中央分岐（主軸と北街）','J-NW':'北WC前分岐','J-NC':'北の館間連絡分岐（3Fは店舗街の曲がり）','J-SW':'南西街の曲がり','J-SC':'南西街東端','J-E':'東街分岐','J-SE':'南東街の曲がり','J-SEE':'南東街東端','SW-2中間口':'K2前へ入る口','SE-2中間口':'K3前へ入る口'}
p=newpage('通路・広場 / 接続点の定義','すべての通路を、店舗・広場・設備・他館・業務/放流のいずれかへ接続する。',w=1190,h=842)
paragraphs(p,[f'{k}：{v}'for k,v in nodes.items()]+['P-W＝翼、P-T＝時、P-L＝光。K1～3＝お手洗い・EV・階段の設備核。','AB/BC＝館間連絡。EX-K1～3＝1Fの階段放流。D-W/D-E＝核店裏の搬入口。'],size=13,gap=42)
rows=[]
for f in FLOORS:
 for r in ROUTES:
  if f['floor']in r['levels']:rows.append((f,r))
for start in range(0,len(rows),18):
 p=newpage(f'通路用途・接続一覧 {start//18+1}','入口数は設計上の店頭数。連絡橋や設備への枝は、店舗数ではなく具体的な接続機能を持つ。')
 for x,t in[(40,'階 / ID / 名称'),(470,'用途 / 接続先'),(1040,'幅 / 延長 / 店頭数'),(1300,'設計上の理由')]:text(p,x,110,t,11)
 for k,(f,r)in enumerate(rows[start:start+18]):
  y=150+k*42;text(p,40,y,f"{f['floor']}F {r['id']} {r['name']}",10);text(p,470,y,r['role'],9);text(p,470,y+14,' → '.join(r['links']),8);text(p,1040,y,f"{r['width']}m / {LineString(r['points']).length:.1f}m / {len(f['route_associations'][r['id']])}",10)
  reason=r['reason'];text(p,1300,y,reason[:29],8);text(p,1300,y+14,reason[29:58],8)
p=newpage('広場・回廊・横断橋 / 用途と接続一覧','各階の広場空間も通路台帳の対象に含める。これらは共用部を埋めるための小部屋ではない。')
for x,t in[(40,'階 / ID / 名称'),(570,'用途'),(1090,'接続先')]:text(p,x,110,t,11)
rows2=[]
for f in FLOORS:
 for pp in PLAZAS:rows2.append([f['floor'],pp['id'],pp['name']+('広場床'if f['floor']==1 else'回廊・休憩'),pp['role'],' / '.join((name+'（他館は2F経由）'if f['floor']==3 and('A館'in name or'C館'in name)else name)for name in pp['gateways'])])
 if f['floor']>1:rows2.append([f['floor'],'BR-T','時の横断橋（幅4m）','東西回廊間の短絡・上階店舗アクセス','時西回廊 / 時東回廊'])
for i,(floor,id,name,role,ends)in enumerate(rows2):
 y=160+i*60;text(p,40,y,f'{floor}F {id} {name}',11);text(p,570,y,role,10);text(p,1090,y,ends[:43],9)
text(p,40,900,'上階の吹き抜け内は歩行域ではない。橋と乗降床の外周で手すりを連続させ、入口を塞がない。',12)
p=newpage('業務・搬入・階段放流 / 役割を持つ通路','通常探索の通路と、営業時間外共用の搬入、1Fの外部放流を区別。全館専用の裏回廊を完成したとは扱わない。',w=1190,h=842)
paragraphs(p,[
 f"D-W（西核店裏）Local{D['delivery']['west_dock']}、D-E（東核店裏）Local{D['delivery']['east_dock']}。開口1.8m。",
 '核店の専用バックルーム→店内主路→主軸→K1/K2/K3の兼用EV→各階主軸→各店主路→バックルーム。',
 'カート幅0.8m、店内主路2.4m、EV開口1.4mを仮定。営業時間外に運ぶ運用案。',
 'EX-K1：階段背面Local(165.5,16)→(165.5,-1)、幅3m。',
 'EX-K2：階段背面Local(221.5,154)→(221.5,190)、幅3m。',
 'EX-K3：階段背面Local(396.5,169)→(396.5,190)、幅3m。',
 '上階の各店から3つの階段前まで、家具を避ける経路が存在することを検査した。',
 '各設備核のST/EV/WC入口は、機械可読の壁・洗面・スクリーンを引いて到達性を別検査。',
 '共用倉庫S-*は有効な共用側入口が取れる大区画だけに計画。小さな余りを無理に部屋にしない。',
 '共用倉庫以外の灰色帯は躯体/配管・設備帯として立入不可。公開の探索空間や宝箱候補にしない。',
 '未検証：トラック進入/荷捌き車両、貨物運転、消防避難性能、火戸/扉/梁の3D衝突、実人数の渋滞。',
 '今回の動線はゲームの空間設計。これらを実装・法令適合まで検証した報告ではない。'
],size=12,gap=44)
# Quantified changes and a design judgement, rather than passing a test alone.
p=newpage('設計上の評価 / プレイヤーの見え方','自動検査と設計者の判断を分ける。立体画像は現時点のゲーム品質を示すものではない。',w=1190,h=842)
paragraphs(p,[
 '翼：西核店から16mの街路を抜けると、長さ52mの吹き抜けが横長に開く。奥の店街が次の目的地になる。',
 '時：北口の案内地点から東西と南西を選ぶ。4m横断橋で上階の遠回りを減らし、待合を主流から退避。',
 '光：東の核店・A館・南東街を曲面で受ける。曲がりは分岐を増やすためでなく端部の分配空間として使う。',
 '広場の休憩島は目的のない埋め草ではない。歩行帯を避け、座る/待つ/案内を見る場所として具体的に計画。',
 '設備枝はK1 18m、K2 11m、K3 約14m。以前の長い孤立枝を引き継がない。',
 '南西接続は約35.6mに短縮して4店頭を設ける。元の空白通路を単に「回遊路」と呼び替えていない。',
 '視認性の注意：時の橋は上空の一部を隠す。光の曲面は照明/反射と案内板次第で入口が読みにくくなる。',
 '密度の注意：16mの主軸でも、エスカレーターの待ち列がはみ出せば詰まる。実人数の検証は別に必要。',
 '現段階の判断：接続先を持つ店舗街と、異なる構造の中継広場として読める設計に改善した。',
 '未確定：構造柱・梁・天井設備・材質仕上げ・店頭サイン。立体モデルの部材はその最終設計ではない。',
 '実装後は床上1.65mで全アプローチを歩き、看板、反射、手すり、混雑、猫/NPC経路を確認する。'
],size=12,gap=46)
p=newpage('検査結果と未検証事項','図面の経路確認を、ゲーム内実歩行と混同しない。',w=1190,h=842)
countscheck=collections.Counter(c['kind']for c in CHECKS)
paragraphs(p,[
 f"図面アサーション {len(CHECKS):,}件 / 不合格0。区画相互の重複が{countscheck['store_pair_no_overlap']:,}件を占める。",
 f"全{sum(counts)}店舗からK1/K2/K3へ：{countscheck['sampled_route_to_stair']}経路。1m格子で探索し、線分を実図形でも検査。",
 '共用部を半径0.45mで縮め、ベンチ/植栽/オブジェ/機器間帯を障害物として連結性を調べた。',
 '店舗入口は自店舗の境界にあること、共用成分から0.8m未満に接近できることを確認。',
 '店舗内は入口から0.8m以降の経路を半径0.45mで膨らませ、壁・棚との交差と区画外へのはみ出しを検査。',
 '設備入口は壁・洗面・スクリーン・個室壁を引いた別の平面領域で確認。ドアは開いた状態の計画。',
 '2F/3Fの開口・横断橋を同じXZにし、両方向の昇降機と全乗降床の接続を確認。',
 '座標はLocal→Worldの平行移動を維持。旧ゲームID38件を別名として継承し、映画館の空間も移設対象に残す。',
 'ゲーム内実歩行：0回。Godot動作テスト：今回未実施。新しいマップをゲームに入れていない。',
 '未検証：3D頭上、段/扉/EV/手すりの衝突、NPC・猫の回避、宝箱、ソナー階判定、ファストトラベル着地、負荷。',
 '未設計/未施工：B地下・屋上、全15フロアの仕上げ、店舗商品の最終内装、構造設備の実施工詳細。',
 '進行セーブは現行未実装。今回、新しいセーブ機能や5000人の実運用を完成したとは報告しない。'
],size=12,gap=44)
# Full dimensional ledger, not a count-only summary.
flat=[(f,s)for f in FLOORS for s in f['stores']]
for start in range(0,len(flat),27):
 p=newpage(f'店舗台帳 {start//27+1}','既存ゲームIDは別名として維持。新しい計画IDの廃止/追加は変更台帳で区別。最大奥行は不整形区画の参考寸法。')
 for x,t in[(40,'階 / 計画ID / 用途'),(620,'面積㎡ / 間口m / 最大奥行m'),(1030,'入口 Local X,Z / 幅m'),(1360,'旧ゲームID')]:text(p,x,110,t,11)
 for k,(f,s)in enumerate(flat[start:start+27]):
  y=142+k*28;text(p,40,y,f"{f['floor']}F {s['id']} "+(s.get('legacy_name')or s['category'])[:30],9);text(p,620,y,f"{s['polygon'].area:.1f} / {s['frontage_m']:.2f} / {s['depth_m']:.2f}",10);text(p,1030,y,f"{s['entry'][0]:.2f},{s['entry'][1]:.2f} / {s['door_width_m']}m",9);text(p,1360,y,s.get('legacy_id','計画新設'),9)
# Layout migration table includes all proposed v3 IDs, even if the space is retired.
MIG=[]
for old,f in zip(OLD['floors'],FLOORS):
 for s in old['stores']:
  t=next((t for t in f['stores']if t['id']==s['id']),None)
  if t is None and s.get('legacy_id'):t=next((t for t in f['stores']if t.get('legacy_id')==s['legacy_id']),None)
  MIG.append(dict(floor=f['floor'],v3_id=s['id'],v3_local=s['entry'],v3_world=world(s['entry']),game_id=s.get('legacy_id',''),v4_id=t['id']if t else'廃止',v4_local=t['entry']if t else[],v4_world=world(t['entry'])if t else[],reason='区画再配置/用途維持'if t else'必要な間口・売場が取れず計画廃止'))
for start in range(0,len(MIG),25):
 p=newpage(f'v3 → v4 座標・ID対応 {start//25+1}','World X=Local X−714、World Z=Local Z−30。床高0/5.525/10.875mを維持。旧ゲームIDはCSVに併記。')
 for x,t in[(40,'階 / v3 ID'),(350,'v3入口 Local X,Z'),(690,'v4 ID'),(990,'v4入口 Local X,Z'),(1340,'v4 World X,Z')]:text(p,x,110,t,11)
 for k,m in enumerate(MIG[start:start+25]):
  y=145+k*30;text(p,40,y,f"{m['floor']}F {m['v3_id']}",10);text(p,350,y,','.join(f'{v:.2f}'for v in m['v3_local']),10);text(p,690,y,m['v4_id'],10);text(p,990,y,','.join(f'{v:.2f}'for v in m['v4_local']),10);text(p,1340,y,','.join(f'{v:.2f}'for v in m['v4_world']),10)
with(OUT/'v3-v4-migration.csv').open('w',encoding='utf-8-sig',newline='')as fp:
 w=csv.writer(fp);w.writerow(['階','v3計画ID','v3入口Local','v3入口World','旧ゲームID','v4計画ID','v4入口Local','v4入口World','理由'])
 for m in MIG:w.writerow([m['floor'],m['v3_id'],m['v3_local'],m['v3_world'],m['game_id'],m['v4_id'],m['v4_local'],m['v4_world'],m['reason']])
doc.set_toc(TOC);doc.set_metadata(dict(title='FIND YOURSELF B館 v4 用途から見直す詳細設計',author='FIND YOURSELF design review',subject='Design only. No Godot modifications or runtime walking test.'))
pdf=ROOT/'downloads/FIND_YOURSELF-B-Purpose-Review-v4.pdf';doc.save(pdf,garbage=4,deflate=True);doc.close();print('PDF',len(TOC),'pages',pdf.stat().st_size)
