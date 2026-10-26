"""Vector 15-floor atlas, whole-site plans, detailed arrivals and area audit. Game is read-only."""
from site_v2_common import *
import fitz,collections
O=R/'docs/site-completion-v2';S=read(O/'geometry.json');A=read(R/'docs/a-detailed-design-v1/geometry.json');B=read(R/'docs/b-v4-overlap-correction/geometry.json');C=read(R/'docs/c-detailed-design-v1/geometry.json');BN=read(R/'docs/b-completion-v2/geometry.json');P=read(R/'docs/parking-blocks-v2/geometry.json');CS=read(R/'docs/c-area-audit-v2/area-polygons.json');VER=read(R/'docs/c-area-audit-v2/verification.json');BS=read(R/'docs/b-completion-v2/summary.json');SS=read(O/'summary.json');IV=read(O/'independent-verification.json');BCP=read(O/'B-v4.1-local-cleanup-UNAPPLIED.json');BCHECK=read(O/'B-v4.1-local-cleanup-proposal-checks.json')
FONT=R/'assets/fonts/NotoSansCJKjp-Regular.otf';JP=fitz.Font(fontfile=str(FONT));DOC=fitz.open();TOC=[];PAGES=[]
INK=(.14,.21,.25);GREY=(.43,.47,.49);RED=(.78,.22,.18);GREEN=(.27,.58,.36);BLUE=(.15,.45,.7);ORANGE=(.9,.58,.22)
F={w:{f['level']:f for f in d['floors']}for w,d in [('A',A),('C',C),('B',BN)]}
for f in B['floors']:
 q=floor_B_world(f,CORES if 'CORES'in globals()else[core_world(c)for c in B['cores']]);q['escalators']=[translate_geoms(e,-714,-30)for e in B['escalators']if f['floor']in e['levels']];F['B'][q['level']]=q

def text(p,x,y,s,size=11,col=INK):
 s=str(s);p.insert_text((x,y),s,fontname='helv'if s.isascii()else'jp',fontsize=size,color=col)
def page(title,sub='',w=1684,h=1100,section=1):
 p=DOC.new_page(width=w,height=h);p.insert_font(fontname='jp',fontfile=str(FONT));text(p,42,43,title,23);text(p,42,70,sub,11,GREY);p.draw_line((42,85),(w-42,85),color=(.25,.5,.45));text(p,42,h-20,f'FIND YOURSELF | 全体設計 v2 / 図面上の設計確認・Godot未改修・実歩行未検証 / 2026-10-26 | {len(DOC)}',9,GREY);TOC.append([section,title,len(DOC)]);return p

def paras(p,ss,x=45,y=125,width=None,size=15,gap=20):
 width=width or p.rect.width-x-45
 for s in ss:
  cur=''
  for ch in str(s):
   if ch=='\n'or JP.text_length(cur+ch,fontsize=size)>width:text(p,x,y,cur,size);y+=size*1.6;cur=''if ch=='\n'else ch
   else:cur+=ch
  if cur:text(p,x,y,cur,size);y+=size*1.6
  y+=gap
 return y

def xy_map(ext,rr):
 a,b,c,d=ext;r=fitz.Rect(rr);scale=min(r.width/(c-a),r.height/(d-b));ox=r.x0+(r.width-(c-a)*scale)/2;oy=r.y0+(r.height-(d-b)*scale)/2;return lambda q:fitz.Point(ox+(q[0]-a)*scale,oy+(q[1]-b)*scale),scale

def geom(p,g,xy,fill=None,col=INK,width=.4):
 if g is None or g.is_empty:return
 if g.geom_type in['LineString','LinearRing']:
  if len(g.coords)>1:p.draw_polyline([xy(q)for q in g.coords],color=col,width=width)
  return
 if g.geom_type=='Point':p.draw_circle(xy(g.coords[0]),1.8,color=col,fill=fill);return
 if g.geom_type!='Polygon':
  for q in getattr(g,'geoms',[]):geom(p,q,xy,fill,col,width)
  return
 sh=p.new_shape();sh.draw_polyline([xy(q)for q in g.exterior.coords]);
 for ring in g.interiors:sh.draw_polyline([xy(q)for q in ring.coords])
 sh.finish(color=col,fill=fill,width=width,even_odd=True);sh.commit()

def label(p,pt,s,xy,size=7,col=INK):
 q=xy(pt);text(p,q.x+2,q.y-2,s,size,col)
def arrow(p,coords,xy,col=BLUE,width=1):
 geom(p,LineString(coords),xy,None,col,width)
 if len(coords)<2:return
 a,b=coords[-2:];dx=b[0]-a[0];dz=b[1]-a[1];ll=math.hypot(dx,dz)
 if ll==0:return
 u=(dx/ll,dz/ll);n=(-u[1],u[0]);L=min(3,ll/3);geom(p,LineString([(b[0]-u[0]*L+n[0]*L/2,b[1]-u[1]*L+n[1]*L/2),b,(b[0]-u[0]*L-n[0]*L/2,b[1]-u[1]*L-n[1]*L/2)]),xy,None,col,width)

def scale(p,xy,s,rr,metres=50):
 x=rr[0]+8;y=rr[3]-10;length=s*metres;p.draw_line((x,y),(x+length,y),color=INK,width=2);text(p,x,y-6,f'{metres} m / XZ世界座標・北は紙面上方向',9)
def grid(p,xy,ext,rr):
 a,b,c,d=ext;step=50 if c-a>250 else 25 if c-a>120 else 10
 for x in range(math.ceil(a/step)*step,int(c)+1,step):q=xy((x,d));text(p,q.x-7,rr[3]+14,f'{x}',7,GREY)
 for z in range(math.ceil(b/step)*step,int(d)+1,step):q=xy((a,z));text(p,rr[0]-36,q.y,f'{z}',7,GREY)

def floor_plan(p,w,f,rr,ext=None,fullids=True):
 ext=ext or f['floor_plate'].union(f['public']).buffer(5).bounds;clip=box(*ext);xy,s=xy_map(ext,rr)
 def draw(g,fill=None,col=INK,width=.35):geom(p,g.intersection(clip),xy,fill,col,width)
 draw(f['floor_plate'],(.94,.94,.91),GREY,.6)
 for q in f.get('program',[]):
  if not isinstance(q,dict)or'polygon'not in q:continue
  draw(q['polygon'],(.86,.87,.82),(.55,.58,.52),.2)
  if q.get('service_walk')is not None:draw(q['service_walk'],(.92,.91,.78),(.67,.65,.49),.15)
  for k,bay in enumerate(polys(q.get('work_bays',Polygon()))):
   if bay.area>80 and clip.covers(bay.representative_point()):label(p,bay.representative_point().coords[0],('物流/設備'if f['level']==-1 else'PV/空調')+f'-{k+1}',xy,5,GREY)
 for q in f.get('landscape',[]):
  if isinstance(q,dict):draw(q.get('geom',Polygon()),(.65,.79,.55),GREEN,.3)
 for q in f.get('gardens',[]):draw(q['polygon'],(.65,.79,.55),GREEN,.3)
 if f.get('parking'):
  pk=f['parking'];draw(pk['vehicle_aisles'],(.76,.79,.81),(.4,.46,.5),.3)
 draw(f['public'],(.84,.93,.89),GREEN,.3)
 if f.get('staff_walk')is not None:draw(f['staff_walk'].difference(f['public']),(.94,.9,.75),(.6,.5,.27),.2)
 if f.get('parking'):
  pk=f['parking'];draw(pk['crossings'],(.95,.85,.62),ORANGE,.4)
  for st in pk['stalls']:
   draw(st['polygon'],(.55,.77,.9)if st['category']=='accessible'else(.8,.87,.92),BLUE,.3)
   if clip.covers(st['polygon'].centroid):label(p,st['polygon'].centroid.coords[0],st['id'].split('-')[-1],xy,4.3)
 for st in f['stores']:
  poly=st['polygon'];draw(poly,(.9,.85,.75),(.45,.37,.29),.45)
  if st.get('backroom')is not None:draw(st['backroom'],(.71,.69,.65),(.4,.4,.38),.3)
  if st.get('shelf_zones')is not None:draw(st['shelf_zones'],(.87,.8,.67),(.63,.51,.37),.2)
  if st.get('aisles')is not None:draw(st['aisles'],(.97,.95,.88),(.7,.65,.53),.15)
  if st.get('wall_solids')is not None:draw(st['wall_solids'],(.26,.27,.25),(.26,.27,.25),.2)
  for key in ['main_route','secondary_main_route']:
   if len(st.get(key,[]))>1:draw(LineString(st[key]),None,BLUE,.65)
  for key in['entry','secondary_entry']:
   if key not in st or not clip.covers(Point(st[key])):continue
   u=st.get('secondary_u',st['u'])if key=='secondary_entry'else st['u'];ww=st.get('secondary_door_width_m',st['door_width_m'])if key=='secondary_entry'else st['door_width_m'];geom(p,LineString([(st[key][0]-u[0]*ww/2,st[key][1]-u[1]*ww/2),(st[key][0]+u[0]*ww/2,st[key][1]+u[1]*ww/2)]),xy,None,GREEN,2)
  if clip.covers(poly.representative_point()):
   pt=poly.representative_point().coords[0];label(p,pt,st['id'],xy,6 if s>2 else 5)
   if s>2.6:label(p,(pt[0],pt[1]+3),st['category'],xy,5.5)
 for core in f['cores']:
  draw(core['outline'],(.87,.82,.85),(.44,.31,.4),.7)
  for name,g in core['rooms'].items():
   if hasattr(g,'geom_type'):draw(g,(.91,.89,.92),(.4,.35,.45),.4)
  for k in['room_wall_solids','ground_room_wall_solids'][:1]:
   if k in core:draw(core[k],(.28,.26,.3),(.28,.26,.3),.2)
  for g in core.get('cubicle_wall_solids',[]):draw(g,(.28,.26,.3),(.28,.26,.3),.2)
  for q in core.get('cubicles',[]):draw(q['polygon'],None,INK,.35)
  for q in core.get('fixtures',[]):
   if isinstance(q,dict):draw(q.get('geom',Polygon()),(.75,.86,.91),BLUE,.3)
  for q in core.get('doors',[]):
   if 'p'in q:draw(Point(q['p']),(.15,.6,.4),GREEN,.5)
  if clip.covers(Point(core['entry'])):label(p,core['entry'],core['id'],xy,7)
 for e in f.get('escalators',[]):
  draw(e['shaft'],(.87,.79,.68),(.5,.3,.14),.7)
  for land in e['landings']:draw(land,(.82,.91,.78),GREEN,.3)
  # shaft long axis indicates direction; lower/upper meaning is documented in section, not guessed from centroid.
  if clip.covers(e['shaft'].centroid):label(p,e['shaft'].centroid.coords[0],e['id'],xy,5)
 draw(f.get('void',Polygon()),(.98,.98,1),BLUE,.9);draw(f.get('shafts',Polygon()),(.96,.79,.75),RED,.6)
 for item in f.get('furniture',[]):
  if isinstance(item,dict)and'geom'in item:draw(item['geom'],(.55,.58,.46),GREEN,.3)
 for prop in S['arrival_proposals']:
  if prop['wing']==w and prop['level']==f['level']:draw(prop['polygon'],None,RED,1.6);label(p,prop['entry'],prop['id']+' (未適用)',xy,7,RED)
 for prop in BN['existing_core_opening_proposals']:
  if prop['wing']==w and prop['level']==f['level']and prop['requires_approval']:draw(prop['opening'],None,RED,.9)
 grid(p,xy,ext,rr);scale(p,xy,s,rr,50 if ext[2]-ext[0]>200 else 10);return xy,s

def site_plan(p,rr,ext=None,mode='all'):
 ext=ext or S['site_boundary'].buffer(5).bounds;clip=box(*ext);xy,s=xy_map(ext,rr)
 def draw(g,fill=None,col=INK,width=.4):geom(p,g.intersection(clip),xy,fill,col,width)
 draw(S['landscape_buffer'],(.88,.93,.83),(.68,.78,.57),.2)
 for w,ff in F.items():
  f=ff[0];draw(f['floor_plate'],(.87,.85,.8),INK,.55);draw(f['public'],(.82,.92,.87),GREEN,.3)
  if mode=='detail':
   for st in f['stores']:draw(st['polygon'],(.89,.84,.73),(.5,.42,.33),.25)
  label(p,f['shell'].representative_point().coords[0],w+'館',xy,16)
 for fac in P['facilities']:
  f=fac['floors'][0];draw(f['shell'],(.83,.87,.9),(.35,.45,.52),.6)
  if mode=='detail':
   draw(f['vehicle_aisles'],(.68,.73,.77),GREY,.2);draw(f['protected_pedestrian'],(.68,.85,.68),GREEN,.2)
   for st in f['stalls']:draw(st['polygon'],(.83,.9,.94),BLUE,.15)
  if clip.covers(f['shell'].centroid):label(p,f['shell'].centroid.coords[0],fac['id'],xy,10)
 draw(S['old_A22']['shell'],(.83,.87,.9),BLUE,.5)
 for r in S['roads']:draw(r['polygon'],(.78,.8,.83)if r['role']=='customer'else(.9,.72,.62),(.4,.44,.5)if r['role']=='customer'else RED,.6)
 for t in S['turn_reservations']:draw(t['polygon'],(.78,.8,.83)if t['role']=='customer'else(.9,.72,.62),GREY,.2)
 for y in S['loading_yards']:draw(y['polygon'],(.9,.72,.62),RED,.6);label(p,y['polygon'].centroid.coords[0],y['id']+(' B1 -5.35m'if y['id']=='Y-C'else''),xy,7,RED)
 for w in S['walks']:draw(w['polygon'],(.47,.75,.57),GREEN,.5)
 for b in S['bridges']:draw(b['polygon'],(.45,.7,.91),BLUE,1)
 draw(S['roof_car_bridge']['polygon'],(.58,.62,.79),(.26,.28,.5),.8)
 draw(BN['car_ramps'][0]['polygon'],None,(.36,.24,.62),1)
 for t in S['pedestrian_towers']:draw(t['outline'],(.68,.75,.84),BLUE,.5)
 for g in S['gates']:
  if clip.covers(Point(g['point'])):label(p,g['point'],g['id'],xy,9,RED if g['role']=='delivery'else BLUE)
 for prop in S['arrival_proposals']:draw(prop['polygon'],None,RED,1.4)
 grid(p,xy,ext,rr);scale(p,xy,s,rr,100 if ext[2]-ext[0]>700 else 50);return xy,s

p=page('FIND YOURSELF｜3館・駐車場・15層 詳細設計補完 v2','ユーザー確認用。A/C内部案とB館v4.1の1〜3Fを保存し、敷地計画・B1/RF・面積監査を追加。',1191,842)
paras(p,[f'図形として数えた駐車マスは合計 {S["total_stalls"]:,}台。外部6,369台＋既存A西22台＋B館B1 193台＋B館RF115台です。立体駐車場の屋上段を二重加算していません。','本資料には全15層の上面図と拡大図、3館全体配置、来客/搬入/歩行の区分、駐車場台帳、B館地下/屋上、C館面積の排他的集計を収録します。','承認が必要な局所案：A2Fの新到着口2か所、B1Fの翼広場南新到着口1か所、およびA/Bの既存階段・EV床開口。元のゲーム/原図データへは一切適用していません。','独立再検査では、固定したB館v4.1の1〜3Fに65件の微小不整合（店舗間56件・店舗/共用3件・入口座標6件）が残っています。原図を変更せず、局所修正案と案の再検査を別紙にしました。','今回の検査は設計ポリゴン上の重なり/接続/寸法です。実歩行、実車、NPCの経路、衝突、構造荷重、排水、法規、交通容量は未検証です。ゲーム完成や安全審査済みの図面として扱わないでください。','実在施設を参考にしたゲーム用オリジナル計画です。寸法・駐車台数・敷地境界はゲーム用設計値で、イオンレイクタウンの実測値ではありません。'],size=14,gap=20)
p=page('図面の読み方・固定範囲・承認条件','緑=公開歩行／薄茶=店舗／濃灰=バックルーム／青=駐車・歩道橋／赤=開口・未適用局所案',1191,842)
paras(p,['15層＝A/B/CそれぞれB1・1F・2F・3F・RF。外部立体の中間駐車段は15層に混ぜず、別冊の17駐車面で扱います。','基準階高：B1 -5.350m、1F 0m、2F +5.525m、3F +10.875m、RF +16.400m。B1↔1Fと3F↔RFの追加エスカレーターは既存3対の平面位置を上下に積層し、既存B1〜3Fの開口拡張を要求しません。','新到着口3か所は既存店舗/設備核との重なり0㎡を検査し、原通路に接続する局所案を赤で示します。原図は未変更なので、これらの駐車場→店舗街の最終接続は承認を条件とします。','既存A/Bの設備核は、室割りの記号上は階段・EVがあっても構造床に穴が含まれていません。今回の床開口追加案を別JSON/CSVで提示します。C館のEV内法・階段開口は既存の設計を維持します。','図面の拡大率は閲覧環境に依存するため、印刷縮尺を断定せず、世界座標のグリッドとメートル尺度を示します。全店舗のID・入口・バックルーム・内部主路は原データに沿って描画。'],size=14,gap=20)
p=page('敷地全体配置｜建物・駐車場・道路・歩道橋','灰=来客車／茶=搬入専用／緑=地上歩行／青=立体横断。白地は周辺街区未設計、外接矩形を敷地面積に算入しません。')
site_plan(p,(85,110,1570,990));text(p,90,1040,f'計画投影和集合 {SS["site_managed_projection_m2"]:,.1f}㎡ / 排水・植栽管理帯 {SS["drainage_green_buffer_m2"]:,.1f}㎡ / 合計 {SS["site_boundary_area_m2"]:,.1f}㎡',12)
for name,ext in [('A館周辺・東立体・南平面',(-220,-130,520,550)),('B館周辺・西平面・南立体',(-1140,-100,-140,330)),('C館周辺・北平面',(-820,-650,-170,-75))]:
 p=page('敷地拡大｜'+name,'車路は駐車入口/搬入口にだけ接続。各経路のIDと座標列はroad-path-register.csv。');site_plan(p,(85,115,1590,1000),ext,'detail')
p=page('駐車台数・用途別台帳｜全8施設','一般/ゆとり/身障者用/EV/職員は同じマスの用途区分です。別枠容量として重複加算しません。',1191,842)
y=125;text(p,45,y,'施設              駐車面数    一般      ゆとり     身障者     EV      職員      合計',13);y+=40
for q in S['parking_capacity']:
 co=q['categories'];general=co.get('general',0)+co.get('standard',0);values=[len(q['levels']),general,co.get('comfort',0),co.get('accessible',0),co.get('EV',0),co.get('staff',0),q['count']];text(p,45,y,q['facility'],13)
 for x,v in zip([255,370,480,600,725,830,965],values):text(p,x,y,v,13)
 y+=43
text(p,45,y+20,f'合計 {S["total_stalls"]:,}台 / 1マス1ID / 既存A西22台を含む',17)
paras(p,['外部の各駐車面・全マス番号・斜路・保護歩道・コアは別冊35ページに収録。B館地下/屋上と既存A西22台は本資料の図面および全体台帳に収録。','容量の妥当性は巨大モールを想定したゲーム設計です。来客数・自動車分担率・ピーク回転率を使った需要予測や実際の交通処理能力は未検証です。'],y=y+65,size=13)
p=page('15層の寸法・用途・区画数一覧','外接寸法はshell投影のX/Z範囲。公開床と躯体投影を加算しません。RFの庭・公開床・空調保守は別用途。',1191,842)
y=120;text(p,45,y,'館/階    高さm      外接X×Z寸法m          shell㎡          公開床㎡       店舗/施設区画',12);y+=28;metricrows=[]
for w in ['A','B','C']:
 for lev in [-1,0,1,2,3]:
  f=F[w][lev];a,b,c,d=f['shell'].bounds;row=[w+' '+LABEL[lev],HEIGHT[lev],c-a,d-b,f['shell'].area,f['public'].area,len(f['stores'])];metricrows.append(row)
  for x,v in zip([45,180,300,560,755,970],[row[0],f'{row[1]:+.3f}',f'{row[2]:.1f} x {row[3]:.1f}',f'{row[4]:,.1f}',f'{row[5]:,.1f}',row[6]]):text(p,x,y,v,11)
  y+=32
paras(p,['B館B1：地下食品/受取2区画＋193台＋共同倉庫/受変電/ポンプ・空調保守。RF：カフェ1区画＋115台＋3光庭前庭＋PV/空調保守。保守ベイは商業店舗数に含めません。','この一覧のA/C区画には地下や屋上の施設区画も含みます。純粋な専門店数と同義ではありません。C1Fのshellは独立6棟の投影であり、屋外床を除きます。'],y=y+18,size=12,gap=12)
csvwrite(O/'15-floor-dimensions.csv',['館階','高さm','外接X寸法m','外接Z寸法m','shell㎡','public㎡','店舗施設区画数'],metricrows)
# Full 15-floor atlas, not only conceptual diagrams.
for w in ['A','B','C']:
 for lev in [-1,0,1,2,3]:
  f=F[w][lev];status='既存内部形状を維持'if w!='B'or lev in[0,1,2]else'今回新設計';p=page(f'{w}館 {LABEL[lev]}｜詳細平面図 全体',f'{status} / Y={HEIGHT[lev]:+.3f}m / 区画数 {len(f["stores"])} / 入口緑線・主路青線・バックルーム灰。赤の局所案は未適用。')
  floor_plan(p,w,f,(85,115,1595,995));PAGES.append(dict(wing=w,level=lev,overview_page=len(DOC),source='fixed baseline'if status.startswith('既存')else'new design'))
  ext=f['floor_plate'].union(f['public']).bounds;a,b,c,d=ext;segments=3 if w=='B'else 2
  for j in range(segments):
   lo=a+(c-a)*j/segments-4;hi=a+(c-a)*(j+1)/segments+4;e=(lo,b-4,hi,d+4)
   p=page(f'{w}館 {LABEL[lev]}｜詳細拡大 {j+1}/{segments}',f'入口幅・売場主路・バックルーム・設備室を原ポリゴンで表示 / 範囲X {lo:.1f}〜{hi:.1f}m');floor_plan(p,w,f,(85,115,1595,995),e)
# Connections and bridge/tower details.
for prop in S['arrival_proposals']:
 p=page('新来客玄関の局所案｜'+prop['id'],'未適用。館内の原通路・店舗区画・広場を変更せず、外周閉鎖帯の局所だけを開口する案。')
 ep=prop['entry'];ext=(ep[0]-24,ep[1]-24,ep[0]+30,ep[1]+30);xy,_=floor_plan(p,prop['wing'],F[prop['wing']][prop['level']],(85,115,1050,950),ext)
 geom(p,prop['wall_cut'],xy,(.95,.7,.65),RED,1.2)
 paras(p,[f'玄関幅 {prop["width_m"]:.1f}m / Y {prop["height"]:.3f}m',f'既存店舗・設備核との重なり {prop["existing_store_overlap_m2"]:.9f}㎡',f'外壁/閉鎖帯の局所開口 {prop["wall_cut"].area:.3f}㎡',f'新玄関床支持 {prop["new_floor"].area:.3f}㎡','到着橋/地上歩道はこの案の承認が前提。自動実装補正で解決した扱いにしない。','B館v4.1 1〜3Fの原本、A館v1原本、ゲーム本体はいずれも未変更。'],x=1110,y=150,width=500,size=14,gap=23)
p=page('歩道橋の昇降塔｜階段・EV・地上/橋上接続','共通寸法を5基へ適用。2m幅の折返し階段・34段・EV1m扉。地上から橋面5.525m、橋桁下5.205m。')
t=S['pedestrian_towers'][0];ext=t['outline'].buffer(1).bounds;xy,sc=xy_map(ext,(100,130,750,950));geom(p,t['outline'],xy,(.92,.92,.89),INK,.8)
for k,color in [('stair',(.8,.8,.79)),('landing',(.68,.85,.7)),('lift',(.68,.81,.9)),('stair_opening',(.95,.8,.72)),('lift_opening',(.95,.8,.72))]:geom(p,t[k],xy,color,INK,.7)
geom(p,t['lift_door'],xy,None,GREEN,2)
for flight in t['stair_flights']:
 a,b,c,d=flight.bounds
 for z in range(1,16):zz=b+z*.3;geom(p,LineString([(a,zz),(c,zz)]),xy,None,GREY,.4)
paras(p,['昇降塔の設置位置（X,Z）']+[q['id']+f' = {q["point"]}'for q in S['pedestrian_towers']]+['各塔は地上歩道と橋上歩道の同一点へ接続。階段/EV機器・構造柱/地盤は未実装。桁・基礎の構造計算は未検証。'],x=850,y=140,width=730,size=15,gap=20)
# B parking/ramp/atria and vertical sections.
p=page('B館地下車路・屋上連絡橋｜平面と縦断','地下スロープはP-B-S地上からB B1へ。屋上は別の水平橋でP7と接続。既存B1〜3Fを車路で貫通しません。')
xy,s=site_plan(p,(85,125,800,800),(-700,80,-500,310),'detail');paras(p,['地下：幅7m、延長70m、5m緩和×2＋60m本勾配。最大約8.23%。車高2.1m制限、設計内空2.4m。','歩行者出口3mの駐車場では、敷地側を8mかけて4mへ広げる。駐車場受け口や端部柵を4mに広げた扱いにはしません。','屋上：車路幅7m、歩道幅4m、両者の離隔2.5m。Y16.4mで別支持。B側とP-B-S側の口を全幅で支持する設計。','地下車路口は(-540,170)→(-540,100)、屋上車路は(-540,170)→(-540,110)、屋上歩道はX=-548に分離。','地上搬入車路を横断する橋はY5.525m、桁厚0.32mの設計仮定で桁下5.205m。トラック4.2m＋余裕0.5mを上回る。構造成立の実証ではない。'],x=875,y=140,width=720,size=15,gap=28)
# True metric vertical section for basement ramp.
rr=(130,830,1490,1000);xy,s=xy_map((0,-1,70,7),rr);profile=BN['car_ramps'][0]['profile'];geom(p,LineString([(q['station_m'],-q['world_y'])for q in profile]),xy,None,BLUE,2)
for q in profile:label(p,(q['station_m'],-q['world_y']),f'{q["station_m"]:.0f}m / Y{q["world_y"]:.3f}',xy,10)
for group,cores in [('A',A['cores']),('B',[core_world(c)for c in B['cores']]),('C',C['cores'])]:
 for j in range(0,len(cores),3):
  p=page(f'{group}館 設備核｜トイレ・階段・EV 詳細 {j//3+1}','既存室割りを維持。赤枠はA/B既存構造床に必要な穴の別提案。Cは原設計の穴を維持。')
  for i,c in enumerate(cores[j:j+3]):
   ext=c['outline'].buffer(1).bounds;rr=(80+i*520,140,560+i*520,850);xy,s=xy_map(ext,rr);geom(p,c['outline'],xy,(.9,.86,.9),INK,.8)
   for name,g in c['rooms'].items():
    if hasattr(g,'geom_type'):geom(p,g,xy,(.95,.94,.95),INK,.6);label(p,g.representative_point().coords[0],name,xy,7)
   for key in ['room_wall_solids']:
    if key in c:geom(p,c[key],xy,(.25,.23,.26),INK,.2)
   for g in c.get('cubicle_wall_solids',[]):geom(p,g,xy,(.25,.23,.26),INK,.2)
   for q in c.get('cubicles',[]):geom(p,q['polygon'],xy,None,INK,.4)
   for q in c.get('fixtures',[]):
    if'geom'in q:geom(p,q['geom'],xy,(.7,.85,.91),BLUE,.4)
   for q in c.get('doors',[]):
    if'p'in q:label(p,q['p'],q.get('id','扉'),xy,6,GREEN)
   if group in['A','B']:
    prop=next(q for q in BN['existing_core_opening_proposals']if q['wing']==group and q['core']==c['id']and q['level']==0);geom(p,prop['opening'],xy,None,RED,1.2)
   label(p,c['entry'],c['id']+' / entry',xy,9,BLUE)
  paras(p,['A/B別案：EV内法は室境界から0.1m壁厚を残して切欠き。階段は2本の2m有効幅、踊り場は保持。既存階の床穴を未施工のまま上下移動可能と報告しません。','B1階段底部は基礎床を保持。B1↔1F、3F↔RFの追加ESCは既存の吹き抜け周辺3対に積層。機器仕様・衝突・実歩行・法定避難は実装後に検証。'],y=930,size=13,gap=10)
p=page('15層の接続断面｜床高さ・吹き抜け・追加ESC','各館は同じ床高。連絡橋は1F/2F既存接続を維持。B館地下/屋上は同じ核・既存ESC位置に接続。')
for j,w in enumerate(['A','B','C']):
 x=110+j*510;text(p,x,125,w+'館',20)
 for lev in [-1,0,1,2,3]:
  yy=900-(HEIGHT[lev]+5.35)*28;p.draw_line((x,yy),(x+380,yy),color=INK,width=2);text(p,x+390,yy+3,f'{LABEL[lev]} {HEIGHT[lev]:.3f}m',10)
  if lev<3:p.draw_line((x+55,yy),(x+145,900-(HEIGHT[lev+1]+5.35)*28),color=BLUE,width=2)
 text(p,x,995,'同一コア・階高維持 / 斜線は接続関係',10)
paras(p,['これは接続関係の断面で、全建物の外形を直線断面として誤表示するものではありません。B新ESCは旧12/23バンクの投影を再使用し、開口と乗降床を一致。','A/BのEV・階段に関する赤い別案を承認するまで、全15層のバリアフリー連続性は「条件付き」です。ESC経由の図面上の経路と区別しています。'],y=145,size=12,gap=10)
# C ground floor exclusive accounting and maps.
p=page('C館1F 面積の集計範囲｜投影・公開床・屋外を区別','同じ位置の複数名目（前廊/公開床/設備核）を足し合わせず、排他的区分で集計。',1191,842)
paras(p,['6つの独立棟の躯体投影和集合：18,953.028976㎡。屋外通路や庭園・棟間デッキはこの「6棟投影」に含めません。','1F公開床：21,418.377759㎡。うち6棟投影内6,574.336131㎡、投影外の屋外公開床14,844.041628㎡。公開床は室内だけの面積ではありません。','1F構造床板：33,046.830604㎡。店舗・設備核に加えて屋外歩行床などを含みます。6棟投影や延床面積の別名として使いません。','6棟投影内の非公開部分：12,378.692845㎡。公開6,574.336131㎡と足して投影18,953.028976㎡になります。','名目前廊4,071.114556㎡をそのまま屋内公開床に加算しません。投影外の前廊接続180.938425㎡と設備核との名目交差21.6㎡があり、前廊/設備核/屋外通路の排他的台帳へ配分済み。',f'面積監査：{VER["checks"]:,}件、失敗{len(VER["failed"])}件。監査専用1e-12mグリッド正規化の最大面積差1.74e-10㎡未満。原図は無変更。raw-source-vs-audit-precision.jsonに元精度値を保持。','C館の共用publicとwalkableの差には固定什器の占有が含まれます。通路を含む名目面積を、障害物を除いた有効歩行面積と混同しません。'],size=14,gap=17)
# Separate area atlas using audit polygons (schema loaded conservatively below).
area_rows=list(__import__('csv').DictReader((R/'docs/c-area-audit-v2/exclusive-area-ledger.csv').open(encoding='utf-8-sig')))
for lev in ['1F','B1','2F','3F','RF']:
 rows=[q for q in area_rows if q['階']==lev];p=page('C館 '+lev+'｜排他的面積台帳','区分ポリゴンはexclusive-area-zones.geojson、原図との名目重複はnominal-overlaps.json。0㎡区分も定義を残しています。',1191,842)
 y=120;text(p,45,y,'区分    用途                                   面積㎡            うち元public㎡',13);y+=31
 for q in rows:
  text(p,45,y,q['区分ID'],11);text(p,110,y,q['排他的用途区分'],11);text(p,620,y,f'{float(q["区分面積㎡"]):,.6f}',11);text(p,875,y,f'{float(q["うち元public㎡"]):,.6f}',11);y+=32
 text(p,45,y+20,f'排他的監査範囲合計 {sum(float(q["区分面積㎡"])for q in rows):,.6f}㎡',13)
p=page('C館1F｜排他的用途ポリゴン図','公開床が6棟躯体投影を越える理由を可視化。前廊/屋外/庭園/設備核を排他的に区分。')
cf=CS['floors'][1];xy,sc=xy_map(cf['audit_domain'].buffer(4).bounds,(90,120,1130,990))
for z in cf['zones']:
 color=tuple(CS['catalog'][z['code']]['color']);geom(p,z['geom'],xy,color,INK,.3)
geom(p,CS['six_pavilion_projection'].boundary,xy,None,RED,1)
y=140
for z in cf['zones']:
 if z['area_m2']<EPS:continue
 text(p,1190,y,z['code']+' '+z['name'],12);text(p,1210,y+20,f'{z["area_m2"]:,.6f} ㎡',11);y+=56
text(p,1190,y+15,'赤線＝6棟躯体投影',12,RED)
p=page('B館追加ESC｜上下階開口・乗降・積層断面','既存12/23バンクを下/上へ積層。平面投影・乗降口・3m平場を保持し、既存1〜3Fの開口を拡張しません。')
e=BN['escalators'][0];xy,sc=xy_map(e['shaft'].union(unary_union(e['landings'])).buffer(2).bounds,(100,120,800,500));geom(p,e['shaft'],xy,(.95,.8,.7),RED,1)
for l in e['landings']:geom(p,l,xy,(.7,.85,.7),GREEN,.6)
c=e['c'];u=e['u'];arrow(p,[(c[0]-u[0]*5,c[1]-u[1]*5),(c[0]+u[0]*5,c[1]+u[1]*5)],xy,BLUE,2)
paras(p,['斜路本体の投影11.8m＋くし板平場1.5m×2、幅2.4m。乗降床は3m×3.6m。隣接上下行の中央機器帯は歩行床に含めません。','B1→1F：高低差5.350m。3F→RF：高低差5.525m。同じ投影でも勾配角は約24.4/25.1度。','上下の投影が重なる機器は、階高5.35m以上から機器厚0.4mを引いて4.95m以上を確保する設計仮定。機器ベンダーの実仕様・頭上判定は未確認。'],x=875,y=140,width=710,size=15,gap=25)
xy,sc=xy_map((-4,-18,23,7),(150,560,1490,1010))
for lev in [-1,0,1,2,3]:
 y=-HEIGHT[lev];geom(p,LineString([(-3,y),(0,y)]),xy,None,INK,2);geom(p,LineString([(11.8,y),(20,y)]),xy,None,INK,2);label(p,(-3,y),LABEL[lev]+' '+str(HEIGHT[lev])+'m',xy,10)
 if lev<3:
  col=RED if lev in[-1,2]else BLUE;geom(p,LineString([(0,y),(11.8,-HEIGHT[lev+1])]),xy,None,col,2)
text(p,120,1040,'赤＝今回追加する地下/屋上接続、青＝既存層間。断面はUPバンクの投影、DOWNは隣の別レーン。',11)
p=page('C館地下搬入ヤード｜新しい屋外トラック下降路','既存C搬入ヤードはB1 -5.35m。敷地側の新スロープだけで接続し、既存C1Fの床や店舗を変更しません。')
cr=next(q for q in S['roads']if q['id']=='D-C');xy,sc=site_plan(p,(90,120,870,800),(-295,-450,-145,-210),'detail');geom(p,cr['retaining_walls'],xy,(.55,.5,.45),INK,.4)
paras(p,['搬入専用幹線(-190,-420,Y0)→直線下降150m→地下水平20m→ヤード入口(-205,-250,Y-5.35)。最後の15mは水平で西へ折れる。','幅8m、上下緩和10mずつ、最大勾配約3.82%。地下の曲がり角は半径15mの旋回予約。12m級単車トラックの動的軌跡は未検証。','地下ヤードは30×49m、既存面積1,470㎡。Cの旧truck_gate/地下床/台車用ゲートに高さを一致。ピットとスロープは露天で、地上駐車場として加算しない。','1Fの6棟投影18,953.028976㎡、公開床21,418.377759㎡のいずれにも、この地下ヤードを新しく足しません。','保護歩道橋はこの下降路ではなく、北側の地上搬入幹線を跨ぐ。地上歩行者を下降路へ誘導しない。擁壁・排水ポンプ・雨水貯留・構造は未設計。'],x=930,y=130,width=650,size=14,gap=24)
xy,sc=xy_map((0,-1,185,7),(130,870,1510,1010));geom(p,LineString([(q['station_m'],-q['world_y'])for q in cr['profile']]),xy,None,BLUE,2)
for q in cr['profile']:label(p,(q['station_m'],-q['world_y']),f'{q["station_m"]:.0f}m / Y{q["world_y"]:.3f}',xy,8)
p=page('A西既存22台｜車路・後方歩道の局所補完','既存22マスは位置/寸法/IDを保持。車路前の2m離隔を進入エプロンで、後方を保護歩道でつなぐ敷地側案。')
o=S['old_A22'];xy,sc=xy_map(o['shell'].buffer(4).bounds,(100,120,1000,980));geom(p,o['shell'],xy,(.92,.92,.9),INK,.8);geom(p,o['vehicle_aisles'],xy,(.73,.77,.8),GREY,.4);geom(p,o['protected_pedestrian'],xy,(.66,.85,.68),GREEN,.4);geom(p,o['crossings'],xy,(.94,.84,.57),ORANGE,.5)
for st in o['stalls']:geom(p,st['polygon'],xy,(.79,.87,.94),BLUE,.4);label(p,st['polygon'].centroid.coords[0],st['id'],xy,6)
paras(p,['元のマス22台は無変更。一般枠として計上。','入口車路は西側(-174,-39)から幅6mでエプロンへ。後方歩道は車路を横断する指定1か所へ集約。','歩行到着点(-153,-20)からA西既存公開部へ接続。身障者用/EV/ゆとり枠は大規模駐車場で別途確保。'],x=1080,y=170,width=500,size=15,gap=25)
p=page('A館搬入口｜東核店バックルームへ直接接続する局所案','貨物車路は客用車路と分離。既存バックルームの外壁に2m搬入扉を提案し、売場をトラックで通過させません。')
q=S['loading_door_proposals'][0];xy,sc=floor_plan(p,'A',F['A'][0],(90,120,1110,980),(185,-25,270,42));geom(p,q['polygon'],xy,(.94,.78,.65),RED,1)
for yard in S['loading_yards']:
 if yard['id']=='Y-A':geom(p,yard['polygon'],xy,(.94,.8,.68),RED,.5)
paras(p,['未適用の新搬入扉：A1F-052バックルーム外壁、幅2m。原店舗区画や内部主路は維持。','荷捌きヤード38×55m、接続貨物車路8m。トラックはヤードで停止し、先は台車のみ。','荷物は閉館後の共用路と兼用EVで各店へ輸送する想定。来客通路を営業中に常時配送台車が縦走する計画ではありません。','A/B兼用EVは既存床開口案の承認が前提。動力・積載・EV実仕様/作業運用は未検証。'],x=1170,y=150,width=440,size=14,gap=25)
# Original source issues remain failures; proposals have their own separately labelled after-checks.
p=page('固定B館v4.1｜今回の独立再検査で残った65項目','B館1〜3Fは原本を保持。原本の失敗を、局所修正案の合格で上書きしていません。',1191,842)
paras(p,[f'全15層の独立検査 {IV["checks"]:,}件：原本合格{IV["passed"]:,}件／不合格{len(IV["failed"])}件。すべて固定B館1〜3Fに限定。新B地下/屋上、A/C原図には今回の検査条件で不合格なし。','内訳：店舗間微小重複56件、共用床と店舗の微小重複3件、入口中心と公開床の距離が1cmを超えるもの6件（最大約1.9cm）。全失敗のID/面積/距離はindependent-checks.json。','別案：共用床を優先して店舗境界の微小重複だけ切り欠き、入口前の短い床の切れを局所充填。既存店舗数・通路網・広場・建物外形は不変更。','別案の入口中心は元位置から0.7mm未満の数値調整に限定。原本へ一切適用せずB-v4.1-local-cleanup-UNAPPLIED.jsonへ保存。別案再検査9集約項目は全合格。','これは原本65項目を解消済みにした報告ではありません。既存Bの変更禁止を守ったまま、承認判断できる比較資料を提出するものです。','A/Bの設備核床穴24件と新来客口3件・A搬入扉1件も未適用の承認対象です。実歩行/ゲーム動作は全て未検証です。'],size=14,gap=20)
for prop in BCP:
 p=page('固定B館 '+LABEL[prop['floor']]+'｜微小境界修正の比較案','未適用。通常の見た目が変わらない範囲を拡大し、青/赤で数値境界の差分を示します。')
 # Pick largest original pair overlap as a readable metre-coordinate inset.
 original=prop['stores_before'];pairs=[]
 for i,st in enumerate(original):
  for other in original[i+1:]:
   over=st['polygon'].intersection(other['polygon'])
   if over.area>EPS:pairs.append((over.area,st,other,over))
 _,st,other,over=max(pairs,key=lambda z:z[0]);pt=over.centroid;ext=(pt.x-2,pt.y-2,pt.x+2,pt.y+2)
 for j,after in enumerate([False,True]):
  rr=(95+j*790,150,800+j*790,830);xy,sc=xy_map(ext,rr);clip=box(*ext);geom(p,(prop['public_proposed']if after else prop['public_before']).intersection(clip),xy,(.8,.92,.84),GREEN,.8)
  rows=prop['stores_proposed']if after else prop['stores_before']
  for row in rows:geom(p,row['polygon'].intersection(clip),xy,(.91,.84,.7),INK,.7)
  if not after:geom(p,over.intersection(clip),xy,(.95,.25,.15),RED,1.5)
  else:
   for row in prop['store_boundary_changes']:geom(p,row['removed'].intersection(clip),xy,(.4,.65,.95),BLUE,.8)
  text(p,rr[0],115,'局所案（未適用）'if after else'原本（保持）',17);grid(p,xy,ext,rr)
 paras(p,[f'例：{st["id"]} / {other["id"]} の原本重複 {over.area:.9f}㎡。赤い細線は数値重複で、面積を拡大誇張した店舗区画ではありません。',f'この階の原本共用/店舗重複 {prop["old_public_store_overlap_m2"]:.9f}㎡、局所案の入口前床充填 {prop["proposed_public_infill_m2"]:.9f}㎡、店舗境界除去合計 {prop["aggregate_unit_removed_m2"]:.9f}㎡。','店舗区画内の細部は、この局所案が承認された後に境界へ再クリップして再出図する対象です。B館v4.1原本とゲームは今回変更していません。'],y=930,size=12,gap=12)
# Check/limitations report is embedded to avoid presenting automated passes as real walking tests.
p=page('検査結果と承認条件｜設計検査と実動作を分離','図面上の合格は実装済み・実歩行済みを意味しません。設計データ、全検査行、原本SHAをZIPに収録。',1191,842)
paras(p,[f'外部駐車：6,369台、17面。source44,815件＋独立43,445件の検査は全合格（端段防護、全マスID、台数、支持床、車路/歩道、PDF記載）。',f'B館B1/RF：新規入力の検査 {BS["checks"]}件、失敗 {len(BS["failed"])}件。機械的な連結と床開口の検査であり、交通流や快適さの合格判定ではありません。',f'敷地統合：{SS["checks"]}件、失敗 {len(SS["failed"])}件。原本{SS["source_files_immutable"]}ファイルのSHA一致、歩行者の搬入車路地上交差0、駐車入口から敷地外ゲートへ到達。',f'C面積監査：{VER["checks"]}件全合格。独立棟・屋外・庭・デッキ・開口を排他的に計上。全15層の既存店舗入口経路と原図形状の無変更を統合再検査。',f'全15層独立再検査：{IV["checks"]}件中{len(IV["failed"])}件は固定B館に残存。局所案の9集約再検査は全合格。原本の不合格と区別。','残る承認条件：新玄関3か所・A搬入扉・A/B既存階の床開口・固定Bの微小境界局所案。自動補正やゲーム改変は行っていません。既存バリアフリー移動を完成扱いしません。','B地下/屋上の車路は幅・前面接続・連結を検査。6m最小回転は設計目標で、全枠の切返し/動的車体軌跡は未検証。台数は図面の区画実数であり実車保証値ではありません。','未検証：実歩行・衝突・NPC1000/5000人・宝箱/案内図/セーブ/FT・階段/EV/ESCの動作・駐車/荷捌き交通容量・構造/防災/避難/排水/建築法規。','屋上設備と地下共同倉庫は保守通路と作業ベイを図示した用途割付です。設備機器の製作図、配管・配線・ラック品番、柱梁/耐荷重、倉庫運営計画は設計していません。'],size=13,gap=18)
DOC.set_toc(TOC);out=R/'downloads/FIND_YOURSELF-Site-15-Floors-v2-Review.pdf';DOC.save(out,garbage=4,deflate=True);DOC.close();write(O/'atlas-pages.json',PAGES);write(O/'pdf-source.json',dict(pdf=str(out.relative_to(R)),source_sha256={str(p.relative_to(R)):sha(p)for p in[O/'geometry.json',R/'docs/b-completion-v2/geometry.json',R/'docs/parking-blocks-v2/geometry.json',R/'docs/a-detailed-design-v1/geometry.json',R/'docs/b-v4-overlap-correction/geometry.json',R/'docs/c-detailed-design-v1/geometry.json']},pdf_sha256=sha(out)))
print(json.dumps(dict(pdf=str(out),pages=fitz.open(out).page_count,bytes=out.stat().st_size),ensure_ascii=False))
