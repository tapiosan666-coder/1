"""A-wing detailed vector review set; no game imports/writes."""
from pathlib import Path
import sys,json,math,ast,collections,csv
sys.path.append('/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
import fitz
from shapely.geometry import shape,Polygon,Point,LineString,box
from shapely.ops import unary_union
R=Path(__file__).resolve().parents[1];O=R/'docs/a-detailed-design-v1';FONT=R/'assets/fonts/NotoSansCJKjp-Regular.otf';INK=(.12,.22,.26);MUTED=(.34,.42,.45);RED=(.72,.23,.16)
def dec(x):
 if isinstance(x,dict):return shape(x)if'type'in x and('coordinates'in x or'geometries'in x)else{k:dec(v)for k,v in x.items()}
 if isinstance(x,list):return[dec(v)for v in x]
 return x
D=dec(json.loads((O/'geometry.json').read_text()));FLOORS=D['floors'];CORES=D['cores'];PLAZAS=D['plazas'];ALL_ESC=D['escalators'];VOIDS=[p['void']for p in PLAZAS];ROUTES=D['routes'];CHECKS=json.loads((O/'checks.json').read_text());doc=fitz.open();toc=[]
assert not[c for c in CHECKS if not c['pass_']],[c for c in CHECKS if not c['pass_']][:6]
for filename,names in[(R/'tools/review_b_drawings.py',{'polys','drawg','line','dot','text','viewmap'})]:
 source=filename.read_text()
 for n in ast.parse(source).body:
  if isinstance(n,ast.FunctionDef)and n.name in names:
   s=ast.get_source_segment(source,n)
   if n.name=='viewmap':s=s.replace("f'AT-{j+1}'","['A-PW','A-PE','A-PS'][j]")
   exec(compile(s,'pure_vector_helpers','exec'),globals())

def page(title,sub='',w=1684,h=1000):
 p=doc.new_page(width=w,height=h);p.insert_font(fontname='jp',fontfile=str(FONT));text(p,40,42,title,22);text(p,40,68,sub,10,MUTED);p.draw_line((40,82),(w-40,82),color=(.2,.45,.4));text(p,40,h-20,f'FIND YOURSELF / A館 詳細設計 v1 / 2026-10-26 / 図面のみ・ゲーム未改修   •   {len(doc):02}',9,MUTED);toc.append([1,title,len(doc)]);return p

def paras(p,items,x=45,y=110,size=14,gap=15,width=None):
 width=width or p.rect.width-x-45;font=fitz.Font(fontfile=str(FONT))
 for s in items:
  cur=''
  for ch in s:
   if ch=='\n'or font.text_length(cur+ch,fontsize=size)>width:
    text(p,x,y,cur,size);y+=size*1.6;cur=''if ch=='\n'else ch
   else:cur+=ch
  if cur:text(p,x,y,cur,size);y+=size*1.6
  y+=gap
 return y

def plan(p,f,extent,rect,detail=False):
 ff=dict(f);ff['floor']=f['level']+1;ff['connectors']=[]
 xy,sc=viewmap(p,ff,extent,rect,detail)
 for st in f['stores']:
  if'secondary_entry'in st and box(*extent).covers(Point(st['secondary_entry'])):
   ep=st['secondary_entry'];u=st['secondary_u'];line(p,[(ep[0]-u[0]*2,ep[1]-u[1]*2),(ep[0]+u[0]*2,ep[1]+u[1]*2)],xy,(1,1,1),2);dot(p,ep,xy,2.5)
  if detail:
   for gl in st.get('glazed_frontages',[]):
    gg=gl.intersection(box(*extent))
    for seg in([gg]if gg.geom_type=='LineString'else getattr(gg,'geoms',[])):
     if seg.geom_type=='LineString'and not seg.is_empty and len(seg.coords)>1:line(p,list(seg.coords),xy,(.2,.55,.65),.6)
 for pl in PLAZAS:
  q=pl['void'].centroid
  if box(*extent).covers(q):v=xy((q.x,q.y));text(p,v.x-25,v.y+28,pl['name'],9)
 for r in ROUTES:
  if f['level']not in r['levels']:continue
  q=LineString(r['points']).interpolate(.5,normalized=True)
  if box(*extent).covers(q):v=xy((q.x,q.y));text(p,v.x+4,v.y+4,r['id'],7,(.2,.4,.5))
 for g in f['furniture']:
  drawg(p,g['geom'].intersection(box(*extent)),xy,(.35,.55,.35)if g['kind']=='planter'else(.55,.35,.18),INK,.4)
 if detail:
  for prog in f['program']:
   if prog.get('public'):continue
   clipped=prog['polygon'].intersection(box(*extent));drawg(p,clipped,xy,None,(.62,.50,.32),.5)
   if not clipped.is_empty and clipped.area>100:
    q=clipped.representative_point();v=xy((q.x,q.y));text(p,v.x-15,v.y,prog['id'],6)
   for item in prog.get('fixtures',[]):drawg(p,item['geom'].intersection(box(*extent)),xy,(.65,.64,.59),INK,.3)
   if'entry'in prog and box(*extent).covers(Point(prog['entry'])):dot(p,prog['entry'],xy,2,(.62,.32,.18))
 if f['level']==3:drawg(p,f['roof_edge_parapet'].intersection(box(*extent)),xy,INK,INK,.3)
 if f['level']==0:
  for site in D['outdoor_site']:
   drawg(p,site['polygon'].intersection(box(*extent)),xy,(.88,.9,.9),INK,.5);drawg(p,site['protected_pedestrian'].intersection(box(*extent)),xy,(.85,.93,.84),INK,.3)
   for stall in site['parking_stalls']:drawg(p,stall['geom'].intersection(box(*extent)),xy,None,(.4,.5,.6),.3)
 return xy,sc

p=page('A館｜三角回遊型モール 詳細設計 v1','B館v4.1を固定基準とした承認候補。Godotシーン・NPC・スキャン・AP・セーブは変更していません。',w=1191,h=842)
paras(p,[
'計画の骨格は、風のゲート（西）・空のテラス（東）・光のコート（南）をつなぐ3方向の専門店街です。中央は北街から南の光コートに抜ける12mの商業街とし、両側に実入口を持つ大型店を設けました。',
'公式kaze資料の3広場、アンカーと専門店街の連続、上階の飲食・娯楽を参考にしています。三角形の配置、全寸法、地下・屋上はゲーム独自の設計値です。実在施設の計測・完全再現ではありません。',
'B1：大型食品店・生活専門店・搬入/共用保管。1F：食品/生活/服飾と西駐車場到着。2F：大型ファッションと服飾/雑貨。3F：映画/娯楽・飲食。RF：屋上庭園、カフェ、ガーデンショップ。',
'B館の1F口World(-174,-5.5)、2F口(-110,-5.5)を保持します。A側だけで受け口と共用床を設計し、他階への橋は増設していません。B1/RFからB館へはA内部で1F/2Fへ移動します。',
f"店舗区画はB1 {len(FLOORS[0]['stores'])}／1F {len(FLOORS[1]['stores'])}／2F {len(FLOORS[2]['stores'])}／3F {len(FLOORS[3]['stores'])}／RF {len(FLOORS[4]['stores'])}。旧商業ID51個＋補助サイン/読書施設2参照を移行表に保持します。",
'図面上の到達性と重なりを検査しています。Godotの実歩行、エスカレーター駆動、扉衝突、群衆・描画負荷や実施設計の適合は未検証です。'],size=14,gap=22)
p=page('設計値・用途・接続条件','World X/Z[m]。階高はB館に合わせ、実在施設の寸法と区別したゲーム用設計値です。',w=1191,h=842)
paras(p,[
'床高 B1 −5.350m／1F 0.000m／2F 5.525m／3F 10.875m／RF 16.400m。構造床厚の計画0.32m。天井/梁下有効高2.4mは実装後に確認する目標です。',
'北街16m、東街15m、西街15m、中央商業街12m、設備前8m、西駐車場歩道3m、B館連絡5m。大型店主入口6m・中央核店副入口4m、通常店2.4m、スタッフ扉1.5m。幅は通路原型で、広場/機器/家具による実有効幅は形状と到達検査で扱います。',
'広場の中央は店舗で埋めず、複数の通路の交点として視界を開きます。西は横長、東は斜めの面、南は広がる飲食前庭と、形と接続先を変えています。各広場に休憩島を配置し、出入口と乗降床を空けました。',
'閉鎖帯は共用床の余白を無差別に部屋にしたものではなく、外壁際・店舗背面の空調/防災・商品保管・清掃保守を割り当てました。大区画には機器/保管ラックと主路の計画を描きます。薄い外壁/配管帯は非室で、扉ではなく点検パネルとして扱います。機器型式・配管・防火区画は未設計です。',
'搬入は地上搬入口→兼用貨客EV→閉館後共用通路→店内主路→各専用裏室。専用の裏通路を全店へ張り巡らせた完成案ではありません。24時間営業や同時搬入は運用再検討が必要です。',
'西の地上駐車場は22台のゲーム用区画。旧a.parking訪問キーは保護歩道のゲート(-153,-16)に移行候補として保持します。駐車場は建物床と区別し、車両路と歩行者ゲートを分けます。'],size=14,gap=19)
for f in FLOORS:
 p=page(f"A館 {f['label']}｜全体詳細平面",f"床高{f['height']:+.3f}m / {len(f['stores'])}店舗区画 / 入口・3広場・機器開口・トイレ/EV・階段を図示")
 xy,sc=plan(p,f,(-180,-65,220,245),(50,105,1634,850),False)
 paras(p,['薄青＝店舗、茶＝裏室、濃緑＝エスカレーター、淡黄＝1F広場床/上階開口、灰＝非公開機械・保管/構造帯。赤点＝店舗入口。',
 '建物は三角回遊を基本に、アンカー・街路・設備の位置から外形を決定。中央街は大型店へのアクセスと回遊短絡を兼ねます。',
 '図は承認用設計で、実ゲームのスクリーンショットではありません。法定避難/防火・構造安全性の認証図ではありません。'],x=55,y=895,size=11,gap=8)
 for k,(a,b)in enumerate([(-175,-20),(-35,115),(100,220)],1):
  p=page(f"A館 {f['label']}｜店舗・共用部拡大 {k}",'店舗入口・店内主路・陳列帯・専用裏室、共用設備、閉鎖帯内の保守/保管機器を具体化。')
  plan(p,f,(a,-60,b,240),(50,105,1634,890),True)
  text(p,55,948,'細い灰色帯は通行域ではありません。店舗主路の計画幅2.4m、裏室扉は主路を避けた壁切欠きで接続。',11)
for pl in PLAZAS:
 p=page(pl['name']+'｜3層吹き抜け・昇降機配置',pl['landscape']+' B1/RFは全体図と断面を参照。')
 extent=pl['court'].buffer(5).bounds
 for f,rr in zip(FLOORS[1:4],[(50,120,545,700),(595,120,1090,700),(1140,120,1635,700)]):
  text(p,rr[0],105,f['label']+f" +{f['height']:.3f}m",14);plan(p,f,extent,rr,True)
 paras(p,['上階の吹き抜け開口は2F/3Fで一致。RFは同じ位置を非歩行の天窓として保持。1Fは開口ではなく広場床です。',
 '各広場2つのバンク位置を階間で交互に使い、同じ階の上り/下り・上階/下階機器が重ならないようにしました。踏面/機器部は共用歩行床から分離。',
 '店舗街→広場→複数の店舗街という見通し、手すりの切欠き、機器下面、群衆で案内が隠れないことはゲーム実装後に確認します。'],x=55,y=780,size=12,gap=17)
# Dimensioned common vertical circulation section and actual bank ledger.
p=page('昇降設備｜階高・踏面・乗降床の断面','各広場に上下対バンクを2位置へ分ける。平面のシャフト幅2.4m/台・機器ラン11.8m・水平コム各1.5m・乗降床各3m。')
for i,(lo,hi)in enumerate([(-1,0),(0,1),(1,2),(2,3)]):
 x=90+(i%2)*810;base=410+(i//2)*410;sc=30;rise=D['heights'][str(hi)]-D['heights'][str(lo)]
 pts=[(0,0),(3,0),(4.5,0),(16.3,rise),(17.8,rise),(20.8,rise)]
 p.draw_polyline([(x+a*sc,base-b*sc)for a,b in pts],color=INK,width=2);text(p,x,base+35,f'{lo} → {hi} / 高差{rise:.3f}m / 傾斜{math.degrees(math.atan(rise/11.8)):.1f}°',14)
 text(p,x,base+65,'実機の構造・駆動・梁下は未検証。ゲーム用の寸法設計。',11)
p=page('階段・EV｜全5階の連続接続','3設備核×B1/1F/2F/3F/RF。各階の共用前室、EV扉、階段扉は同じWorld XZへ揃える。',w=1191,h=842)
paras(p,['階段は2m幅の2折返し、32蹴上げ、踏面0.30m、踊り場1.8m。B1→1F 5.350m／1F→2F 5.525m／2F→3F 5.350m／3F→RF 5.525m。最大蹴上は0.172656mです。',
'EVシャフト4×4m・扉1.4m。各階に同じ前室とロビーを用意。専用のサービスEVを別に増やす計画ではなく、閉館後搬入と兼用する運用です。',
'12件のcore vertical_linksで5層を結びます。階段とEVの入口、下階/上階の高さ、踊り場・扉幅をgeometry.jsonに記録。B1/RFから直接B館へは接続せず、A内部で1F/2Fへ移動します。',
'RFは外周1.2m高パラペットと天窓周囲の手すりを計画し、外周0.12m帯を歩行域から除外しています。転落防止コリジョン・出入口の扉/避難設備の実装は未検証です。'],size=15,gap=25)
for core in CORES:
 p=page(core['id']+'｜トイレ・EV・階段 詳細','World座標の26×20m設備核を、主街に向けて回転配置。各階同一。扉/洗面/個室/前室とEVロビーを表示。')
 bb=core['outline'].bounds;scale=min(650/(bb[2]-bb[0]),650/(bb[3]-bb[1]));xy=lambda q:fitz.Point(90+(q[0]-bb[0])*scale,130+(q[1]-bb[1])*scale)
 drawg(p,core['outline'],xy,(.97,.94,.9),INK,1.)
 labels={'stair':'階段','lift':'EV','accessible_wc':'多目的WC','lift_lobby':'EVロビー','ev_front_lobby':'EV前室','women':'女性用WC','men':'男性用WC','front_lobby':'共用前室','lift_access':'EVアクセス'}
 for key,room in core['rooms'].items():
  drawg(p,room,xy,(.97,.97,.94),(.5,.4,.35),.5);q=xy((room.centroid.x,room.centroid.y));text(p,q.x-22,q.y,labels.get(key,key),8)
 drawg(p,core['room_wall_solids'],xy,(.2,.28,.3),INK,.3)
 for wall in core['cubicle_wall_solids']:drawg(p,wall,xy,(.3,.35,.35),INK,.3)
 for item in core['fixtures']:drawg(p,item['geom'],xy,(.66,.81,.83),INK,.4)
 for screen in core['vestibule_screens']:line(p,list(screen.coords),xy,INK,1.)
 for d in core['doors']:
  dot(p,d['p'],xy,2.5);q=xy(d['p']);text(p,q.x+4,q.y-4,d['id']+f" {d['w']}m",8,RED)
 paras(p,[f"設備中心World({core['centre'][0]}, {core['centre'][1]}) / 入口({core['entry'][0]}, {core['entry'][1]})。",'共用入口4m。男女トイレ入口各1.5m、階段1.5m、EV1.4m、多目的WC1.2m。','男女別の前室・目隠し、個室・洗面を分離。多目的WCは4×4m、回転直径1.5mの計画。','設備間の通過は壁/器具を差し引き、半径0.45mの2D到達域で検査。','階段・EVの上下階連続、トイレ入口へのアクセスは図面検査。Fキー扉やEV駆動は未実装。','配管/防火区画、衛生器具の法定数、梁下、バリアフリー認証を満たす実施設計ではありません。'],x=850,y=150,size=14,gap=30,width=740)
# Connections and site parking are separate from the unchanged B wing.
p=page('A/B固定受け口・西到着側 詳細','B館v4.1の図面データは変更しない。A側共用床と固定済みB床端が実面積で接続する。')
for f,rr in[(FLOORS[1],(55,130,790,700)),(FLOORS[2],(880,130,1615,700))]:
 text(p,rr[0],110,f['label'],15);plan(p,f,(-178,-60,-45,65),rr,True)
paras(p,['1F：B口World(-174,-5.5)・幅5m→西到着ロビー→風のゲート。地上駐車場からの保護歩道もここへ接続。',
'2F：B口World(-110,-5.5)・幅5m→風のゲート。橋の下階と上階の高さはB基準0/5.525mに合わせる。',
'受け口が店舗壁を貫かないよう共用床を先に確保してから店舗を配置。店舗内部を通り抜けない。B側端点や経路の付け替え案は不要と判断。'],x=55,y=780,size=13,gap=20)
p=page('閉鎖帯・バックヤードの用途一覧','公開床の空白と非公開の機械/商品保管・構造帯を区別。機器割付の最終承認/消防適合は未検証。',w=1191,h=842)
y=115
for f in FLOORS:
 text(p,45,y,f"{f['label']}：閉鎖帯合計 {f['residual'].area:.1f}㎡ / 建物平面 {f['shell'].area:.1f}㎡",15);y+=28
 for prog in sorted([q for q in f['program']if not q.get('public')],key=lambda q:q['polygon'].area,reverse=True)[:3]:text(p,60,y,f"{prog['id']} {prog['name']} {prog['polygon'].area:.1f}㎡ / 計画機器・ラック{len(prog.get('fixtures',[]))}組",11);y+=23
 y+=17
paras(p,['共用設備への枝道は用途と終点がある必要な行き止まり。店内/スタッフ保管室の奥も必要な終点であり、探索用の無意味な袋小路として増設していません。','非公開の機器型式・保管容量・搬入運用と防火区画は未検証。大きな閉鎖帯を公開の謎の空き部屋としてプレイヤーへ開放する計画ではありません。'],y=y+4,size=12,gap=15)
p=page('図面検査と未検証項目','現在のgeometry.jsonの形状に対する設計段階の検査。Godot実歩行・衝突判定・NPCナビメッシュではない。',w=1191,h=842)
paras(p,[f"図面検査 {len(CHECKS):,}件、不合格0。共用域の連結、全店舗入口、店舗同士/公開床との交差、閉鎖帯/共用床、床板/開口、乗降床、設備前室・内部扉を確認。",'面積の数値許容は交差検査1×10⁻⁸㎡。店内の主路/壁界面はB基準に合わせ0.025㎡未満、入口の余裕は共用域を0.45m縮めた領域から0.8m以内。個別実数と基準はchecks.json。','検査に合格したことと、プレイヤーが実際に通れることは別です。上階回廊・機器下・扉敷居・段差・手すり・天窓・屋上端の衝突、ガラスの見え方は実装後に確認します。','未検証：NPC/猫経路、宝箱配置、スキル・ソナー、案内図、訪問済みファストトラベル、セーブ互換、1,000/5,000人時の描画負荷。既存ゲームのこれらのコードは変更しません。','設計上の注意：大規模中央核店2区画の用途と内部陳列は詳細商品の制作前に再レビューが必要。現在は主路・棚配置帯・専用裏室までの設計で、棚一段の商品配置や機器の実型式は未制作です。','公式参考の構造から採用した点と、ゲーム独自の三角配置/寸法/地下/RFは区別。B館との整合は統合資料でさらに確認し、承認前に実装を開始しません。'],size=14,gap=21)
# Every store's dimensions/coordinates are readable in the PDF, not solely machine JSON.
for f in FLOORS:
 for start in range(0,len(f['stores']),26):
  p=page(f"A館 {f['label']}｜店舗寸法・入口台帳 {start//26+1}",'店舗入口はWorld X/Y/Z[m]。旧区画重心やTransform原点と入口を同じ点として比較しない。');y=120
  text(p,45,100,'ID                  用途                        区画㎡     間口m      奥行m     入口幅m      World X      World Y      World Z     裏室㎡',11)
  for s in f['stores'][start:start+26]:
   text(p,45,y,s['id'],10);text(p,215,y,s['category'][:17],10)
   for x,v in[(470,s['polygon'].area),(585,s['frontage_m']),(700,s['depth_m']),(815,s['door_width_m']),(940,s['entry'][0]),(1065,f['height']),(1190,s['entry'][1]),(1315,s['backroom'].area)]:text(p,x,y,f'{v:.3f}',10)
   y+=29
  text(p,45,948,'旧IDは別名として継続。全商業ID51＋補助2行の役割/比較座標はlegacy-id-coordinate-map.csv。',11)
# Full purpose and dead-end ledger.
with(O/'route-register.csv').open('w',encoding='utf-8-sig',newline='')as fp:
 w=csv.writer(fp);w.writerow(['階','ID','名称','幅m','用途','接続先','必要な終点'])
 for f in FLOORS:
  for r in ROUTES:
   if f['level']in r['levels']:w.writerow([f['label'],r['id'],r['name'],r['width'],r['role'],'→'.join(r['links']),'設備・店舗・他館・駐車場への用途上必要な終点'if'K'in r['id']or'PARK'in r['id']else'回遊/相互接続'])
with(O/'service-program.csv').open('w',encoding='utf-8-sig',newline='')as fp:
 w=csv.writer(fp);w.writerow(['階','ID','用途','面積㎡','公開','入口WorldXZ','計画機器数','内部保守経路未検証'])
 for f in FLOORS:
  for q in f['program']:w.writerow([f['label'],q['id'],q['name'],q['polygon'].area,q.get('public',False),q.get('entry',q.get('access','-')),len(q.get('fixtures',[])),q.get('internal_service_access_unverified',False)])
(O/'README.md').write_text('''# A館 詳細設計 v1\n\n設計資料のみ。Godot本体とB館v4.1は変更していません。\n5層(B1/1F/2F/3F/RF)、三角回遊の3専門店街＋中央核店街、3広場、3設備核、24エスカレーター機器を計画。\n\n主図面は downloads/FIND_YOURSELF-A-Detailed-Design-v1.pdf。\ngeometry.json は World XZ metres、階高はB基準。店舗入口・裏室・棚帯・主路・共用床・床開口を収録。\nchecks.json は図面検査のみ。実歩行・ゲーム画像・法的建築認定の結果ではありません。\n旧ID対応は旧40区画＋地下食品7＋フードコート4、補助サイン/読書施設2参照。比較点の定義をCSVに明記。\n全実寸はゲーム用設計値。公式kazeの3広場/専門店街とアンカー/階別用途を参考にしたオリジナル構成。\nB1/RFは実在施設にないゲーム独自の計画。機械型式・商品小物・施工/防火基準・群衆負荷は未検証。\n''')
doc.set_toc(toc);doc.set_metadata({'title':'FIND YOURSELF A館 詳細設計 v1','subject':'Design proposal only, no Godot changes','author':'FIND YOURSELF design team'});path=R/'downloads/FIND_YOURSELF-A-Detailed-Design-v1.pdf';doc.save(path,garbage=4,deflate=True)
import hashlib
(O/'pdf-source.json').write_text(json.dumps(dict(geometry_sha256=hashlib.sha256((O/'geometry.json').read_bytes()).hexdigest(),checks_sha256=hashlib.sha256((O/'checks.json').read_bytes()).hexdigest(),pdf_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),pdf_pages=len(doc)),indent=2))
print('PDF',len(doc),path)
