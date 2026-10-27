"""Vector architectural review PDF. Viewport pixels embedded unchanged; PDF is not an image generator."""
from pathlib import Path
import sys,math,csv,json,io
sys.path.insert(0,str(Path(__file__).resolve().parent));from site_v2_common import *
import fitz
from PIL import Image
P=Path(__file__).resolve().parents[1];S=P/'source';E=P/'evidence';OUT=P/'deliverables';OUT.mkdir(exist_ok=True);D=read(S/'design-v5.json');B=read(S/'baseline-v4.json');Q=read(E/'geometric-results.json');fontfile=P/'assets/NotoSansCJKjp-Regular.otf';font=fitz.Font(fontfile=str(fontfile));SCENE=read(S/'scene-manifest.json');doc=fitz.open();counter=0
ink=(.13,.19,.19);green=(.18,.43,.34)
def page(title,sub='',w=1190,h=842):
 p=doc.new_page(width=w,height=h);p.insert_font(fontname='JP',fontfile=str(fontfile));p.draw_rect(p.rect,fill=(.99,.99,.97),color=None);text(p,35,25,w-70,45,title,22);text(p,35,72,w-70,42,sub,10);text(p,35,h-30,w-70,20,f'FIND YOURSELF | B館 街区再構成 v5 | 2026-10-27 | 独立検証・未統合 | {len(doc)}',8);return p
def text(p,x,y,w,h,s,size=11,color=ink):
 r=p.insert_textbox(fitz.Rect(x,y,x+w,y+h),str(s),fontname='JP',fontsize=size,color=color,lineheight=1.35)
 while r<0 and size>5.5:
  size-=.25;r=p.insert_textbox(fitz.Rect(x,y,x+w,y+h),str(s),fontname='JP',fontsize=size,color=color,lineheight=1.30)
 if r<0:print('TEXT_OVERFLOW',str(s)[:90],size,r)
 return r
def paragraphs(title,ps):
 p=page(title,'設計・生成ルールと未検証事項を区別して記載');y=135
 for heading,body in ps:
  text(p,40,y,1110,35,heading,16,green);y+=38;h=max(52,math.ceil(len(body)/77)*18);text(p,40,y,1110,h,body,12);y+=h+22
 return p
def table(title,headers,rows,widths=None,rowsper=26,notes=''):
 w=1190;cols=len(headers);widths=widths or[(w-80)/cols]*cols
 for start in range(0,len(rows),rowsper):
  p=page(title+f'  {start+1}–{min(len(rows),start+rowsper)} / {len(rows)}',notes);y=128;x=40
  for head,cw in zip(headers,widths):p.draw_rect(fitz.Rect(x,y,x+cw,y+35),fill=(.15,.28,.25),color=None);text(p,x+5,y+5,cw-10,30,head,9,(1,1,1));x+=cw
  y+=35
  for ri,row in enumerate(rows[start:start+rowsper]):
   x=40;hh=min(32,(690-y)/max(1,len(rows[start:start+rowsper])-ri))
   for val,cw in zip(row,widths):p.draw_rect(fitz.Rect(x,y,x+cw,y+hh),fill=(.94,.96,.94)if ri%2==0 else(1,1,1),color=(.77,.81,.79),width=.25);text(p,x+4,y+3,cw-8,hh-3,val,8);x+=cw
   y+=hh

def plan(p,f,rect,bounds=None,before=False,detail=False):
 x0,z0,x1,z1=bounds or f['old_floor_plate'].union(f['floor_plate']).bounds if not before else(bounds or f['floor_plate'].bounds)
 box0=fitz.Rect(rect);pad=20;sc=min((box0.width-2*pad)/(x1-x0),(box0.height-2*pad)/(z1-z0));ox=box0.x0+(box0.width-(x1-x0)*sc)/2;oz=box0.y0+(box0.height-(z1-z0)*sc)/2;clip=box(x0,z0,x1,z1)
 def pt(q):return fitz.Point(ox+(q[0]-x0)*sc,oz+(q[1]-z0)*sc)
 def geom(g,fill=None,color=None,width=.5):
  g=unary_union(polys(g.intersection(clip)))
  sh=p.new_shape()
  for a in polys(g):
   if a.area<.000001:continue
   for ring in[a.exterior,*a.interiors]:sh.draw_polyline([pt(q)for q in ring.coords])
  sh.finish(color=color,fill=fill,width=width,even_odd=True,closePath=True);sh.commit()
 geom(f['floor_plate'],(.94,.93,.88),(.4,.42,.4),.4);geom(f['public'],(.98,.965,.90),None)
 if before:
  assigned=unary_union([f['public'],f['void'],f['shafts'],f.get('egress',Polygon()),*[q['outline']for q in f['cores']],*[s['polygon']for s in f['stores']],*[q['polygon']for q in f['service_zones']]])
  geom(f['floor_plate'].difference(assigned),(.94,.65,.60),(.72,.32,.26),.4)
 else:
  geom(f['old_floor_plate'].difference(f['floor_plate']),None,(.72,.44,.40),.5)
 for c in f['cores']:geom(c['outline'],(.78,.82,.84),(.31,.36,.39),.6)
 for room in f['service_zones']:geom(room['polygon'],(.80,.79,.73),(.36,.36,.33),.7)
 for s in f['stores']:
  if not s['polygon'].intersects(clip):continue
  geom(s['sales'],(.79,.88,.82),(.25,.39,.33),.65);geom(s['backroom'],(.89,.81,.65),(.43,.36,.25),.6)
  if not before:
   geom(s['work_rectangle'],None,(.18,.42,.68),.65)
   if detail:
    for fp in SCENE.get('fixture_footprints',{}).get(s['id'],[]):geom(fp,(.71,.66,.56),None)
    pts=s.get('main_route',[])
    for aa,bb in zip(pts,pts[1:]):
     if clip.covers(LineString([aa,bb])):p.draw_line(pt(aa),pt(bb),color=(.20,.43,.65),width=.5)
  for key,uk,wk in[('entry','u','door_width_m'),('back_door','back_door_u','back_door_width_m')]:
   if key not in s:continue
   e=s[key];u=s.get(uk,s['u']);ww=s.get(wk,2.4 if key=='entry'else 1.5);a=[e[0]-u[0]*ww/2,e[1]-u[1]*ww/2];b=[e[0]+u[0]*ww/2,e[1]+u[1]*ww/2]
   if clip.covers(Point(e)):p.draw_line(pt(a),pt(b),color=(1,1,1),width=2.5);p.draw_line(pt(a),pt(b),color=(.12,.42,.31)if key=='entry'else(.39,.25,.12),width=.6)
  center=s['sales'].intersection(clip).representative_point()
  if center.is_empty:continue
  pp=pt((center.x,center.y));size=7 if detail else 5.5;label=s['id']+(' 新'if'-N'in s['id']else'')
  bw=s['sales'].intersection(clip).bounds;label_w=min(98,max(38,(bw[2]-bw[0])*sc*.8))
  if detail and s['polygon'].area>220:label+='\n売 %.0f / 裏 %.0f㎡'%(s['sales'].area,s['backroom'].area)
  text(p,pp.x-label_w/2,pp.y-6,label_w,35,label,size)
 geom(f['void'],(.82,.91,.96),(.22,.42,.54),.7)
 for e in f['escalators']:
  g=rect_fn(e['c'],e['u'],e['run_m'],2.4);geom(g,(.57,.65,.65),(.22,.3,.3),.6);c=pt(e['c']);text(p,c.x-30,c.y-5,60,24,e['direction'],5.5)
 for obj in f.get('furniture',[]):geom(obj['geom'],(.45,.59,.43),None)
 # Source-defined core doors and true floor openings are drawn distinctly.
 if not before:geom(f['floor_openings_v5'].difference(f['void']),(.83,.91,.96),(.19,.39,.58),.6)
 for conn in f.get('connectors',[]):
  pts=[(a[0]-714,a[1]-30)for a in conn['route']]
  for aa,bb in zip(pts,pts[1:]):
   if clip.covers(LineString([aa,bb])):p.draw_line(pt(aa),pt(bb),color=(.19,.40,.59),width=1)
  if clip.covers(Point(pts[-1])):
   cc=pt(pts[-1]);text(p,cc.x-45,cc.y-15,90,35,conn['id']+' / 他館側未施工',6)
 p.draw_rect(box0,color=(.64,.69,.67),width=.4);text(p,box0.x0+8,box0.y0+5,box0.width-16,20,f'World X[{x0:.2f}, {x1:.2f}] / Z[{z0:.2f}, {z1:.2f}]m　|　縮尺 1:{2834.64567/sc:.0f}（表示倍率100%時）',8)
 # Nominal width/depth and actual scale bar.
 text(p,ox,oz+(z1-z0)*sc+2,max(160,(x1-x0)*sc),17,f'幅 {x1-x0:.2f}m × 奥行 {z1-z0:.2f}m　N = −Z',8)
 scale=10 if detail else 50;a=fitz.Point(box0.x0+12,box0.y1-20);p.draw_line(a,a+fitz.Point(scale*sc,0),color=ink,width=2);text(p,a.x,a.y-16,120,18,f'{scale} m',8)
 return sc
rect_fn=rect
# ---- report narrative ----
summary=Q['summary'];total=sum(q['old_unassigned_m2']for q in summary)
paragraphs('B館 v5｜用途未確定床の再構成',[
 ('今回の範囲',f'B館1〜3Fの未帰属床 {total:,.3f}㎡・{Q["unowned_before_components"]}成分を全件追跡しました。独立した新規検証プロジェクトだけを変更し、ゲーム本体・B館v4.1・敷地全体v3・過去の検証プロジェクトは変更していません。これは建築変更案と3D検証であり、最終承認・施工完了・商業運営上の完成を意味しません。'),
 ('主な原因', '外郭の膨張と階別の店舗奥行きの不一致、区画を個別に切った差分、用途と規模が曖昧な大型管理室、連絡通路の床を上階にも繰り返した処理が重なっていました。ブーリアン演算で生じた面積がほぼゼロの折返し境界も、長い壁として押し出されていました。'),
 ('対応', '21の共通街区を基準に隣接区画が同じ壁を共有する方式へ再構成。従来188区画のIDと比較可能な売場実効面積を保持し、新規10区画を加え198区画としました。用途が成立しない外周床は外部化・外郭縮小。大きな管理室は120㎡／階の具体的な運営室へ再編しています。'),
 ('完成扱いにしない項目', '主要広場・吹き抜け・昇降設備位置・館間接続は維持。ただし屋上・地下との構造的な荷重経路、実在店の在庫容量、避難・防火・設備設計、人間による実操作は未検証です。今回の全館モデルは建築・動線用の再生成モデルで、従来v4の一部店舗の詳細商品表現を置き換える完成内装ではありません。FF15級の画質に達したとは評価していません。')])
rows=[]
for q in summary:rows.append([q['floor'],f"{q['old_unassigned_m2']:,.3f}",f"{q['new_unassigned_m2']:.6f}",f"{q['old_floor_m2']:,.2f}",f"{q['new_floor_m2']:,.2f}",str(q['old_shop_count'])+' → '+str(q['new_shop_count']),f"{q['old_shop_m2']:,.2f} → {q['new_shop_m2']:,.2f}"])
table('変更前後の面積集計',['階','旧未帰属㎡','新未帰属㎡','旧床㎡','新床㎡','店舗数','区画面積㎡'],rows,[55,140,140,140,140,100,295],notes='床面積は実際のスラブ。吹き抜け・昇降路・受け側エスカレーター開口は床から除外。極小値は数値許容内。')
paragraphs('生成処理の根本修正と再発防止',[
 ('外郭と床の用途を別々に確定', '各階のスラブを「店舗／運営・在庫／共用・避難／設備核／機器・手すり支持／実際の構造納まり」に排他的に分割します。残り床を自動で倉庫や通路と呼ぶ処理は禁止。内側の既存採光中庭は外部空間として整理し、客用の謎の通路にはしません。'),
 ('境界の品質', '共用通路を固定し、その両側の連続した街区を店舗へ配分。細片の最近傍への無条件割当は行わず、共有境界・入口・売場予算・作業矩形を一緒に検査します。0.1マイクロメートルの座標正規化と、幅6mm未満の演算上の針状残片の除去を設計データに反映。除去面積は台帳に明記し、実際の壁の接合範囲としてのみ扱います。'),
 ('壁・ガラス・扉', '外周一律ガラスを廃止し、共用通路に面した売場のみをショーウィンドウとします。バックヤードは不透明な間仕切りと従業員扉。隣接店の壁は区画内側の半厚で接合し、重複する全面押出しを避けます。入口の幅を先に切り欠き、その範囲にマリオンを生成しません。'),
 ('什器と歩行経路', '売場の経路と作業室への出入りを先に確保し、その後に什器を配置。作業室に実物の棚を置いた最初の物理検査では経路を塞ぐ事例が多数検出されました。棚を検査から除外せず、実際の経路へ干渉する棚位置を変える生成ルールに修正しています。')])
paragraphs('連絡通路・管理室・在庫室の設計判断',[
 ('B/C連絡の繰返し床', '元の接続計画は1F幅8m、2F幅5m、3F接続なしです。上階でも1Fの躯体形状を繰り返したため、2Fに細い床、3Fに使い道のない張出しが残っていました。接続座標・有効幅は保持し、不要な上階床は外部庇・屋根側へ整理。B2-062の幅1.5m・45.00㎡の孤立した裏側片も外部化し、隣店との共有壁を0.5m調整して既存売場予算を保っています。'),
 ('管理室', '旧T室3区画は合計約2,403㎡でした。新案は120㎡×3階＝360㎡。受付20／執務36／打合せ24／休憩16／清掃12／ロッカー12㎡の計画です。防災センターや本格救護施設の機能を満たすという主張はしません。'),
 ('共用在庫', 'W・L室は160㎡ずつ、計320㎡／階。2.2×3.0mの仮定ケージをWに8、Lに12配置し中央作業通路・荷受け前室を確保します。合計60枠ですが、48店舗分の実在庫が必ず入るという容量保証ではありません。先に各店舗内の作業スペースを成立させ、共用在庫は補助とします。'),
 ('維持した条件', '既存188店舗のIDを全件保持。売場は外周壁0.12m、間仕切り0.10mを差し引いた同一基準で比較します。全店舗に作業矩形を設計しましたが、これはゲーム用の寸法仮定で、実在施設の規格値・法規適合・業種別在庫運営の実測結果ではありません。')])
# overall detailed vector comparisons
for new,old in zip(D['floors'],B['floors']):
 p=page('B館 '+new['label']+'｜変更前後 詳細平面図','赤：旧未帰属床／緑：売場／黄土：バックヤード／灰：設備・運営／水色：吹き抜け・開口／白緑：実入口。図面はベクターで拡大可能。',2384,1684)
 bounds=old['floor_plate'].union(new['floor_plate']).bounds;text(p,40,120,2300,28,'変更前：v4設計抽出データ（赤い床は店舗でも共用でもない）',15);plan(p,old,(40,150,2340,800),bounds,True)
 text(p,40,830,2300,28,'変更後：v5独立変更案（元の図面・ゲーム本体には未反映）',15);plan(p,new,(40,865,2340,1515),bounds,False)
 text(p,40,1540,2300,80,'連絡橋は接続先側のプレビュー端まで。構造柱・梁・耐火区画・設備配管の設計は別途必要。店舗内は売場／作業室／実際の出入口を表示。青線の店内経路と作業矩形は街区詳細図で確認できます。',12)
# all shared blocks: three floors before/after on one sheet; exact coordinates and merchandise footprints
for bi,block in enumerate(D['blocks'],1):
 bounds=block.buffer(4).bounds;p=page(f'街区 {bi:02}｜3階層の区画・入口・作業室比較','左：旧区画と未帰属床　右：共有境界を再構成したv5。青：検査用の実経路／青枠：作業矩形。店舗の統合・既存ID削除はありません。',2384,1684)
 for lev,(f,b)in enumerate(zip(D['floors'],B['floors'])):
  yy=140+lev*480;text(p,40,yy-22,2200,25,f'{f["label"]}　旧 → 新',13);plan(p,b,(40,yy,1170,yy+440),bounds,True,True);plan(p,f,(1210,yy,2340,yy+440),bounds,False,True)
# Service interiors: the diagram dimensions match the actual exported geometry, not arbitrary room labels.
for suffix in ['W','L','T']:
 r=next(z for z in SCENE['service_rooms']if z['id']=='S-1-'+suffix);w=r['planned_width_m'];dep=r['planned_depth_m'];p=page('運営・在庫室 '+suffix+'｜1〜3F共通詳細','各階で同じ平面。入口位置・World座標は最終JSON/CSV。内部の通路・作業域・開口を実モデルと照合。')
 scale=min(640/dep,650/w);ox=80;oy=760
 def pp(x,z):return fitz.Point(ox+(x+w/2)*scale,oy-z*scale)
 def rr(x0,z0,x1,z1,col):
  a=pp(x0,z1);b=pp(x1,z0);p.draw_rect(fitz.Rect(a,b),color=(.3,.34,.31),fill=col,width=.7)
 rr(-w/2,0,w/2,dep,(.89,.89,.84))
 if suffix=='T':
  for x0,z0,x1,z1,label in[(-5,0,5,2,'受付 20㎡'),(-5,2,1,8,'執務 36㎡'),(-5,8,1,12,'打合せ 24㎡'),(1,2,5,6,'休憩 16㎡'),(1,6,5,9,'清掃 12㎡'),(1,9,5,12,'ロッカー 12㎡')]:
   rr(x0,z0,x1,z1,(.88,.90,.85));q=pp((x0+x1)/2,(z0+z1)/2);text(p,q.x-65,q.y-12,130,35,label,11)
  for x,z,u in[(0,2,'u'),(-2,8,'u'),(3,6,'u'),(3,9,'u'),(1,4,'n'),(1,7.5,'n'),(1,10.5,'n')]:
   a=pp(x-.6,z)if u=='u'else pp(x,z-.6);b=pp(x+.6,z)if u=='u'else pp(x,z+.6);p.draw_line(a,b,color=(1,1,1),width=5)
  text(p,760,150,375,380,'120㎡ = 10.00 × 12.00m\n外部入口は施錠可能な従業員扉。内部開口は1.20m。\n\n受付・作業・打合せ・休憩・清掃・ロッカーを区分。設備容量、防火区画、法定避難、家具の業務適合は別途。防災センター・救護施設を実装したとは扱いません。',13)
 else:
  count=r['cage_count']//2
  for side in[-1,1]:
   for j in range(count):
    cx=side*(w/2-1.5);zz=2.8+(j+.5)*2.2;rr(cx-1.5,zz-1.1,cx+1.5,zz+1.1,(.78,.83,.74));q=pp(cx,zz);text(p,q.x-40,q.y-11,80,35,f'{"L"if side<0 else"R"}-{j+1}\n2.2×3.0m',8)
  q=pp(0,dep/2);text(p,q.x-60,q.y-25,120,60,f'中央作業通路\n幅 {w-6:.2f}m',11);q=pp(0,1.3);text(p,q.x-70,q.y-18,140,40,'荷受け前室 2.8m',10)
  text(p,760,150,375,400,f'160㎡ = {w:.2f} × {dep:.3f}m\nケージ {r["cage_count"]}枠 / 階\n3階分の共用在庫ケージ合計60枠\n\n通路と荷受けテーブルを分離し、出入口から奥まで実際に歩行検査。仮定ケージの数を数えた結果であり、48店舗分の在庫容量を実証したものではありません。棚・防火・冷蔵・食品衛生等は業種別の追加検討が必要。',13)
 a=pp(-1,0);b=pp(1,0);p.draw_line(a,b,color=(1,1,1),width=5);text(p,80,780,650,25,f'間口 {w:.2f}m × 奥行 {dep:.3f}m / 原点は客用通路側の入口、上向きが室内N',10)

# role tables current recomputation
area_rows=[]
for f in D['floors']:
 for q in f['floor_roles']:area_rows.append([f['label'],q['role'],f"{q['polygon'].area:,.6f}",q['purpose']])
table('用途別面積表',['階','用途','㎡','定義'],area_rows,[60,190,160,700],18,notes='用途は排他的に集計。店舗区画には売場と店舗内作業室を含む。実壁厚分を含む区画面積と実効売場面積は別の値。')
# component inventory
actions_ja={'店舗区画':'店舗','外郭縮小・開口・外部化':'外部化・開口','機器・手すり支持':'機器支持','運営・共用在庫':'運営・在庫','壁・構造納まり':'壁接合','共用・避難':'共用','設備核':'設備'}
inv=read(S/'unowned-full-inventory.json');rr=[]
for q in inv:
 act=' / '.join(actions_ja.get(a['role'],a['role'])+f" {a['area_m2']:.2f}"for a in q['new_actions']);rr.append([q['id'],q['floor'],f"{q['world_x_m']:.2f}, {q['world_z_m']:.2f}",f"{q['old_area_m2']:.6f}",q['cause'],act or'数値残差のみ'])
table('全254成分｜旧未帰属床と割当結果',['旧領域ID','階','World X,Z m','旧面積㎡','原因','新用途・外部化㎡'],rr,[120,40,140,120,300,290],20,notes='ゼロに近い演算残差も省略せず記載。各成分のポリゴン・全桁面積・用途別内訳はJSON/CSV。')
ledger=list(csv.DictReader(open(S/'all-198-store-ledger.csv',encoding='utf-8-sig')));rr=[]
for q in ledger:rr.append([q['id'],q['category'],f"{float(q['old_plot_m2']):.1f} → {float(q['new_plot_m2']):.1f}",f"{float(q['old_net_sales_m2']):.2f} → {float(q['new_net_sales_m2']):.2f}",f"{float(q['old_backroom_m2']):.2f} → {float(q['new_backroom_m2']):.2f}",q['work_module_m'],('旧48対象'if q['old_48']=='True'else'新規'if q['new_unit']=='True'else'既存')])
table('全198店舗｜売場・バックヤード・作業寸法',['ID','業種','区画 旧→新㎡','実効売場 旧→新㎡','裏方 旧→新㎡','作業矩形m','区分'],rr,[110,180,170,210,190,160,90],24,notes='新規店舗の旧面積0は比較対象なし。内部区画・入口座標の全桁データはCSVに収録。')
# screenshots actual engine only
shots=read(S/'cameras.json')
for shot in shots:
 before=E/'before'/f'{shot["id"]}.png';after=E/'after'/f'{shot["id"]}.png'
 if not after.exists():continue
 p=page('Godot実画面｜'+shot['label'],'カメラ・照明・画角・解像度を一致。比較前はv4全館モデルが存在しなかったため、凍結したv4図面から再構成した実Godot画面。v4配布版そのものの全館写真ではありません。',1190,1684)
 def photo(path,r):
  im=Image.open(path).convert('RGB');raw=im.tobytes();buf=io.BytesIO();im.save(buf,format='PNG',icc_profile=None);assert Image.open(io.BytesIO(buf.getvalue())).convert('RGB').tobytes()==raw;p.insert_image(fitz.Rect(r),stream=buf.getvalue())
 if before.exists()and not shot.get('after_only'):
  text(p,40,125,1100,30,'変更前｜v4図面の再構成',15);photo(before,(40,160,1150,785));text(p,40,815,1100,30,'変更後｜v5独立検証',15);photo(after,(40,850,1150,1475))
 else:text(p,40,125,1100,30,'変更後のみ｜室内の作業通路・在庫配置',15);photo(after,(40,180,1150,805))
 text(p,40,1510,1100,90,'撮影メタデータ：'+str(shot['eye_local'])+' → '+str(shot['look_local'])+'（検証プロジェクトLocal XYZ m／World XZ原点 −429,46m）\n合成・画像生成・画面の塗り直しは行っていません。PDFにはピクセルを変えず埋込み。',10)
# test status
phys=read(E/'summary-results.json')if(E/'summary-results.json').exists()else{'passed':0,'failed':'未実行','checks':[]};render=read(E/'after/render-results.json')if(E/'after/render-results.json').exists()else{}
paragraphs('検査結果と、合格と呼んでいない項目',[
 ('図面上の独立再検査',f'最終ポリゴンから再計算：{Q["passed"]}合格／{Q["failed"]}不合格。未帰属床、役割重複、店舗同士、共用との重複、吹き抜け・床開口、売場予算、作業矩形、入口の接続、188旧ID保持を検査。作業室48区画も48／48で計画矩形が成立。'),
 ('実際のGodot物理検査',f'{phys["passed"]}合格／{phys["failed"]}不合格。高さ1.8m・半径0.3mのCharacterBody3Dをmove_and_slideで移動。実際の壁・ガラス・棚・開いた従業員扉に衝突します。図面上の経路計算とは別検査です。内訳は店舗・運営室・エスカレーター231件と、各階の西東横断435〜452mの3経路で、同一メッシュに対する2回の実行結果を集計しています。ヘッドレス固定60Hzで実行した値は描画FPSではありません。'),
 ('人間の実操作', '未検証です。自動操作で経路を通れたことを、人間が歩いて自然・快適と感じた実証にはしません。スクリーンショットの目視評価も、全地点を実操作で確認した検査とは別です。'),
 ('構造・運用上の保留', f'屋上115台の区画は今回の上階外郭内に収まりますが、旧RF床約{Q["roof_basement_impact"]["original_roof_floor_outside_proposed_support_envelope_m2"]:.1f}㎡が新上階外郭の外へ張り出します。柱・梁・屋根支持の設計が必要です。地下も外周の取り合いが変わります。敷地全体6699台の成立を今回再承認したものではありません。')])
if render:
 rr=[]
 for r in render.get('performance',[]):rr.append([r['id'],str(r['sample_frames']),f"{r['mean_ms']:.1f}",f"{r['fps']:.2f}",f"{r['p95_ms']:.1f}",str(r['draw_calls'])])
 if rr:table('描画実測｜ソフトウェアGPU',['視点','フレーム数','平均ms','FPS換算','最大付近ms','Draw calls'],rr,[300,120,180,180,180,150],notes='llvmpipe／Godot4.6.3／GL Compatibility／1280×720／MSAA4×／NPC0。短時間サンプル。ユーザーのRTX4060性能とは無関係。')
failures=[q for q in phys['checks']if not q.get('pass',False)]
if failures:table('実物理で残った不合格',['ID','理由','停止位置','目標'],[[q['id'],q.get('reason',''),str(q.get('position','')),str(q.get('target',''))]for q in failures],[180,330,300,300],20,notes='不合格を隠さず収録。検証条件と再試験ログはevidenceフォルダー。')
paragraphs('残課題と、過去依頼の継続状況',[
 ('建築的な自然さ',f'面積上の未帰属は解消しましたが、鋭角・短辺の追加目視候補が{len(Q["acute_boundary_review"])}店舗あります。境界レビューCSVにIDを残しました。共有壁・公開面・裏方側の納まりをさらに詰める必要があり、自動検査の合格を完成認定とはしません。'),
 ('昇降設備', '既存12エスカレーターの位置と上下階を維持。過去に提出したエレベーター増設・エスカレーター乗継改善案は承認前のため未施工。検証モデルに操作可能なエレベーターや全避難階段はありません。昇降路へ誤侵入しない閉鎖表示のみ設置。'),
 ('内装・大型店', '本モデルの棚・衣料・カフェは建築動線検証用です。詳細な商品・個別ブランド表現、書店v1との視覚的な密度比較、核店舗のシネマ・食品・家電等の専用設備、中央店舗の統合は未完成・未施工。旧v4の詳細店舗内装は凍結して残しています。店舗を勝手に統合してはいません。'),
 ('次の判断', '全階床・天井は階単位の検証メッシュで、遮蔽カリング・LOD・ストリーミングは未最適化です。性能合格としていません。この変更案の平面・写真・残課題を確認してから、外郭縮小と店舗区画変更の採用可否を判断してください。ゲーム本体への統合は行っていません。採用前に屋上／地下／構造と、客用・荷受け・避難の実操作評価が必要です。')])
paragraphs('Godot実画面の目視評価｜完成判定とは分離',[
 ('改善を確認した点', '比較01〜03では旧閉鎖帯の壁面が店舗入口・売場へ変わり、長い無表情な管理室前面を整理できています。07〜09では時の広場の開放感と上下階の見通しを維持。10〜12では共用在庫室の中央通路が空いており、両側の在庫配置と分離されています。'),
 ('残る空間の課題', '13の西側店舗には鋭角な上部・壁面の取り合いが残ります。04・05の食品カフェは入口を通れますが奥の壁が近く、客席・厨房・壁面の構成を仕上げる必要があります。16は連絡部側の店舗街からの写真で、撤去した張出し床そのものは壁外にあり、この写真だけで撤去を実証したとは扱いません。平面図・スラブ差分を参照してください。'),
 ('画質と商品密度', '棚・商品は建築動線確認用の基本表現で、業種ごとの品揃えや密度は未完成です。床の反復模様とモアレ、店舗ごとの照明不足、3Fの強い陰影、建築ディテールの不足も見えます。FF15級の建築表現に到達したとは評価していません。'),
 ('検査の限界', '今回の目視は保存した代表29画面と詳細図面に対する評価で、人間が全館を操作して歩いた検証ではありません。234件の物理通行と1811件の幾何検査が合格しても、以上の建築・内装・見え方の課題を合格へ変更しません。')])

# Only save once: do not reuse stale image caches after garbage4.
doc.set_metadata({'title':'FIND YOURSELF B館 街区再構成検証 v5','author':'FIND YOURSELF project','subject':'Unassigned floor ownership, before/after vector plans and actual Godot evidence; standalone only'});doc.save(OUT/'FIND_YOURSELF_B_WING_RECONFIGURATION_v5.pdf',garbage=4,deflate=True);print('PDF',len(doc),OUT/'FIND_YOURSELF_B_WING_RECONFIGURATION_v5.pdf')
