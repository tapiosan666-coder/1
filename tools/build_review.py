#!/usr/bin/env python3
"""Build an offline Japanese review pack from captured v0.23 data. No game edits."""
from pathlib import Path
import json, math, base64, io, csv, re, hashlib, zipfile, shutil, argparse
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'downloads'; MAPS=ROOT/'docs/images'; SHOTS=ROOT/'docs/screenshots'
def integer_fields(value):
 if isinstance(value,float) and value.is_integer():return int(value)
 if isinstance(value,list):return [integer_fields(x) for x in value]
 if isinstance(value,dict):return {k:integer_fields(v) for k,v in value.items()}
 return value
SNAP=integer_fields(json.loads((ROOT/'docs/review-v023-snapshot.json').read_text()))
VERSION=SNAP['version']; REV=SNAP['source_commit']; STEM='FIND_YOURSELF-v0.23-Review'
FONT=ROOT/'assets/fonts/NotoSansCJKjp-Regular.otf'
CATS={'fashion':'服飾','clothes':'服飾','kids':'服飾','shoes':'服飾','travel':'生活','home':'生活','daily':'生活','kitchen':'生活','grocery':'飲食','deli':'飲食','food':'飲食','cafe':'飲食','beauty':'生活','optical':'生活','jewelry':'服飾','digital':'家電','music':'文化','books':'文化','stationery':'文化','sport':'趣味','outdoor':'趣味','arcade':'娯楽','hobby':'趣味','toys':'娯楽','cinema':'娯楽'}
COLORS={'服飾':'#a2c6bd','生活':'#b8cbd9','飲食':'#e5c59a','家電':'#a6bdd0','文化':'#c4b8d4','趣味':'#d6c995','娯楽':'#d6adb0'}
FLOOR_NAMES={-1:'地下1階',0:'1階',1:'2階',2:'3階',3:'屋上'}
FLOOR_SHORT={-1:'B1',0:'1F',1:'2F',2:'3F',3:'RF'}
UNITS=sorted(SNAP['outlets'],key=lambda u:(u['building'],u['level'],u['id']))
NUMBER={u['id']:i+1 for i,u in enumerate(UNITS)}
for u in UNITS:u['number']=NUMBER[u['id']]
FLOORS={f['id']:f for f in SNAP['floors']}
CAPTURES={c['id']:c for c in SNAP['captures']}
PAGES=[]
def font(n):return ImageFont.truetype(str(FONT),n)
def cat(u):return CATS.get(u['kind'],'生活')
def all_points(f):
 return [p for r in f['base'] for p in r]+[p for r in f['structure'] for p in r['outer']]
def draw_map(f):
 W,H=1800,1160;im=Image.new('RGB',(W,H),'#f4f6f3');d=ImageDraw.Draw(im)
 pts=all_points(f);xs=[p[0] for p in pts];zs=[p[1] for p in pts];x0,x1,z0,z1=min(xs),max(xs),min(zs),max(zs)
 scale=min((W-180)/(x1-x0),(H-260)/(z1-z0));cx=(x0+x1)*.5;cz=(z0+z1)*.5
 def q(p):return (W*.5+(p[0]-cx)*scale, H*.5-10+(p[1]-cz)*scale)
 def poly(p,fill,outline='#788e8d',width=2):d.polygon([q(x) for x in p],fill=fill);d.line([q(x) for x in p]+[q(p[0])],fill=outline,width=width,joint='curve')
 # Draw on a separate floor layer so openings reveal the background, then preserve legacy floors.
 for p in f['base']:poly(p,'#fdfcf7')
 for p in f['structure']:
  poly(p['outer'],'#fdfcf7')
  for hole in p['holes']:poly(hole,'#dce8e8','#9cb5b3',2)
 if 'private' in f:poly(f['private'],'#cdd2cf','#adb8b3')
 for u in f['shops']:poly(u['polygon'],COLORS.get(cat(u),'#c9d3ca'),'#788e8d',2)
 # Stairs are projected from the actual 3D circulation routes, not invented rooms.
 seen_stairs=set()
 for route in SNAP.get('stair_routes',[]):
  if route['building']!=f['building'] or f['level'] not in [route['lower'],route['upper']] or route['name'] in seen_stairs:continue
  seen_stairs.add(route['name']);pts=[q((p[0],p[2])) for p in route['world_points']]
  d.line(pts,fill='#577b78',width=8,joint='curve')
  x,y=pts[len(pts)//2];d.text((x-10,y-12),'階段',font=font(18),fill='#183a42',stroke_width=3,stroke_fill='#f4f6f3')
 for u in f['shops']:
  p=u['polygon'];cxu=sum(a[0] for a in p)/len(p);czu=sum(a[1] for a in p)/len(p);x,y=q((cxu,czu));n=f'{NUMBER[u["id"]]:03d}'
  d.rounded_rectangle((x-28,y-18,x+28,y+18),radius=5,fill='#fffdf6',outline='#788e8d');d.text((x,y-1),n,font=font(26),fill='#183a42',anchor='mm')
 for e in f['escalators']:
  a=q(e['a']);b=q(e['b']);color='#b17e39' if e['up'] else '#367e7e';d.line([a,b],fill=color,width=6)
  end=b if e['up'] else a;other=a if e['up'] else b;vx=end[0]-other[0];vy=end[1]-other[1];length=math.hypot(vx,vy);vx/=length;vy/=length
  d.polygon([end,(end[0]-vx*13+vy*6,end[1]-vy*13-vx*6),(end[0]-vx*13-vy*6,end[1]-vy*13+vx*6)],fill=color)
 # Destination positions are real; compact labels on very dense courts are reserved for the game map.
 for h in f['hubs']:
  x,y=q(h['at']);d.ellipse((x-5,y-5,x+5,y+5),fill='#c37a4a',outline='white',width=2)
 for p in f['plazas']:
  x,y=q(p['at']);label=p['name'];box=d.textbbox((0,0),label,font=font(26));width=box[2]+22
  d.rounded_rectangle((x-width/2,y-18,x+width/2,y+20),radius=5,fill='#183a42');d.text((x,y),label,font=font(26),fill='white',anchor='mm')
 d.text((55,38),f'{f["building"]}館  {FLOOR_NAMES[f["level"]]}',font=font(40),fill='#183a42')
 d.text((W-55,47),'共通配置データから作図 / ゲーム画面ではありません',font=font(21),fill='#607775',anchor='ra')
 # Scale uses physical game-world coordinates, not real-site measurements.
 bar=20 if (x1-x0)<300 else 50;px=bar*scale;by=H-115;d.line((75,by,75+px,by),fill='#183a42',width=4)
 for x in [75,75+px]:d.line((x,by-7,x,by+7),fill='#183a42',width=3)
 d.text((75,by+13),f'{bar}m相当（ゲーム内座標）',font=font(20),fill='#183a42')
 d.text((W-55,H-112),'番号＝店舗一覧と対応　●＝移動地点　矢印＝昇降口',font=font(21),fill='#183a42',anchor='ra')
 d.text((W-55,H-43),'階段は3D経路の平面投影を模式表示',font=font(17),fill='#607775',anchor='ra')
 d.text((W-55,H-79),'青灰＝吹き抜け　灰＝非公開区画　上＝Z−方向（実在の北とは異なります）',font=font(18),fill='#607775',anchor='ra')
 path=MAPS/f'review23-{f["building"].lower()}-{FLOOR_SHORT[f["level"]].lower()}.png';im.save(path,optimize=True);return path

def draw_site():
 W,H=2000,1200;im=Image.new('RGB',(W,H),'#f4f6f3');d=ImageDraw.Draw(im)
 fs=[FLOORS[f'{b}/1F'] for b in ['A','B','C']];pts=[p for f in fs for p in all_points(f)];xs=[p[0] for p in pts];zs=[p[1] for p in pts];x0,x1,z0,z1=min(xs),max(xs),min(zs),max(zs);k=min((W-160)/(x1-x0),(H-250)/(z1-z0))
 def q(p):return (80+(p[0]-x0)*k,170+(p[1]-z0)*k)
 for f,color in zip(fs,['#c8dccc','#bdcddc','#e2d1b3']):
  for p in f['base']:d.polygon([q(v) for v in p],fill=color,outline='#6f8583',width=2)
  for p in f['structure']:
   d.polygon([q(v) for v in p['outer']],fill=color,outline='#6f8583',width=2)
   for h in p['holes']:d.polygon([q(v) for v in h],fill='#f4f6f3')
 # Links are schematic overlays on the actual exported world footprints.
 bridges=[('A/B 2階連絡通路',[[-194,-5.5],[-110,-6.4]]),('B/C 2階連絡橋',[[-442,-17],[-442,-92],[-432,-117]])]
 for label,line in bridges:
  pts=[q(v) for v in line];d.line(pts,fill='#c17e3e',width=10,joint='curve');x,y=pts[len(pts)//2];d.text((x+12,y-20),label,font=font(24),fill='#824e23',stroke_width=4,stroke_fill='#f4f6f3')
 for label,p in [('A館',[0,-5]),('B館',[-337,78]),('C館',[-381,-168]),('西駐車場',[-152,12])]:
  x,y=q(p);d.text((x,y),label,font=font(44 if len(label)==2 else 24),fill='#183a42',anchor='mm',stroke_width=3,stroke_fill='#f4f6f3')
 d.text((65,38),'3棟の位置関係と接続',font=font(43),fill='#183a42')
 d.text((65,95),'1階の床形状＋2階の連絡橋 / ゲーム内配置の整理図 / 実在施設の測量図ではありません',font=font(24),fill='#607775')
 d.text((65,H-65),'A館＝東側の曲線モール　B館＝西側の分岐・回遊モール　C館＝図の上側の屋外型エリア',font=font(25),fill='#183a42')
 path=MAPS/'review23-site.png';im.save(path,optimize=True);return path

IMG_CACHE={}
def image_uri(path):
 path=Path(path)
 if path not in IMG_CACHE:
  im=Image.open(path).convert('RGB');out=io.BytesIO()
  if path.parent==SHOTS:im.save(out,format='JPEG',quality=89,optimize=True);mime='image/jpeg'
  else:im.save(out,format='PNG',optimize=True);mime='image/png'
  IMG_CACHE[path]=f'data:{mime};base64,'+base64.b64encode(out.getvalue()).decode()
 return IMG_CACHE[path]
def esc(s):
 import html
 return html.escape(str(s))
def figure(id,caption=None,cls=''):
 c=CAPTURES[id];path=SHOTS/c['image'];return f'<figure class="{cls}"><img src="{image_uri(path)}" alt="{esc(c["caption"])}"/><figcaption><b class="real">実画面</b> {esc(caption or c["caption"])}</figcaption></figure>'
def mapfig(path,caption='共通配置データから作図。店舗番号は巻末と対応。'):
 return f'<figure class="map"><img src="{image_uri(path)}" alt="平面図"/><figcaption><b class="plan">配置図</b> {esc(caption)}</figcaption></figure>'
def para(s):return f'<p>{s}</p>'
def table(headers,rows,cls=''):
 return f'<table class="{cls}"><thead><tr>'+''.join(f'<th>{h}</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join(f'<td>{c}</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table>'
def callout(title,text):return f'<aside><strong>{title}</strong><p>{text}</p></aside>'
def page(kicker,title,body,sub='',cls=''):
 PAGES.append({'kicker':kicker,'title':title,'body':body,'sub':sub,'cls':cls})
def twocol(a,b,cls=''):return f'<div class="two {cls}"><div>{a}</div><div>{b}</div></div>'
def badge(t,c='done'):return f'<span class="tag {c}">{t}</span>'
def bullet(items):return '<ul>'+''.join('<li>'+x+'</li>' for x in items)+'</ul>'

def content(maps,site):
 page('現状を、起動せずに見る','FIND YOURSELF',figure('a-center','A館・中央吹き抜け。v0.23の通常描画。','hero')+'<div class="cover-bottom"><div><h2>ゲームの現状資料集</h2><p>構想・設計・マップ・実画面を、ひとつに。</p></div><div class="version">v0.23<span>日本語開発版 / 基準40ccc24</span></div></div>','写真付きレビュー / 現在の実装と完成版の目標を区別', 'cover')
 metrics='<div class="metrics">'+''.join(f'<div><b>{a}</b><span>{b}</span></div>' for a,b in [('1,000人','現在の既定人数'),('10 / 15','実装済みフロア / 目標'),('101','店舗・売場'),('20','訪問で解放する移動地点')])+'</div>'
 page('まず、この2ページ','現在は、こういうゲームです。',metrics+twocol('<h3>同じ顔の群衆から、本当の自分を探す。</h3>'+para('ショッピングモールをFPS視点で歩き、単体スキャナーで人物を解析します。偽物を消してAPを獲得し、銃・猫・ソナー・範囲スキャンで探索を効率化します。')+callout('本物の位置は開始時に固定','運がよければ1人目でクリア。途中で本物を移動したり、最低プレイ時間を強制したりしません。'),figure('b-2f'))+table(['現在できること','完成版へ残ること'],[['1,000人 / 比較用300人。滞在900人・歩行100人。','5,000人での実地最適化とプレイ時間調整。'],['A館5フロア、B館3フロア、C館2フロア。','B館地下・屋上、C館地下・3階・屋上。'],['単体解析、成長、猫、宝箱、移動、吹き出し。','写真からの顔生成、人物・内装の販売品質仕上げ。']]),'最初に全体像。その後、各館のマップとスクリーンショットへ。')
 flow='<div class="flow">'+''.join(f'<div><b>{a}</b><span>{b}</span></div>' for a,b in [('探索','店舗・広場・別フロアへ'),('単体解析','最初は約2秒 / 1人'),('成長','偽物1人につき10 AP'),('効率化','銃・猫・特殊・移動'),('最終確認','本物を初期スキャナーで')])+'</div>'
 page('ゲームの芯','見つける。近づく。自分で確かめる。',flow+twocol(figure('scanner'),figure('fall'))+callout('本物の発見と、クリアの確定は別','銃・猫・範囲・アイテムで本物を検出しても、その場ではクリアになりません。位置を通知し、初期スキャナーで解析してクリアします。他の人々もそのまま残ります。'),'v0.23の確定ルール。初期装備が銃だった初案は、後の指示で更新済み。')
 page('成長と装備','APで、探索の手触りが変わる。',twocol(figure('skills'),'<h3>4系統・15種類のスキル</h3>'+bullet(['装備：初期スキャナー高速化、銃、銃の強化。','猫：自動探索を配備し、解析時間を短縮。','探索・移動：ソナー、ダッシュ、二段ジャンプ、訪問済み移動。','特殊：連鎖スキャンと範囲スキャン。'])+table(['通常開始の主な値','v0.23'],[['初期スキャナー','6m / 単体 / 2秒'],['銃の価格','1,000人版 3,330 AP / 300人版 1,000 AP'],['銃の初期値','30m / 5発命中 / 30発弾倉 / 約1秒リロード'],['解析報酬','偽物1人につき10 AP']])+callout('撮影の設定','このスキル画面は説明用に20,000 APを付与した状態です。通常開始時のAPではありません。')),'購入はそのラン内で継続。具体的な段階・価格は巻末へ。')
 page('補助探索','猫とソナーは、探す手間を減らす。',twocol(figure('cat'),figure('gun-sonar'))+twocol('<h3>猫は自動で近づいて解析</h3>'+para('猫のみを配備。初期は1人20秒、強化で12秒・6秒へ。段差や別フロアには経路を使って移動します。本物を見つけても、最後はプレイヤーが確認します。'),'<h3>ソナーは、その瞬間の位置を記録</h3>'+para('壁・床・天井の向こうも対象。15→30→50→80→120m。表示は4秒で、移動する相手には追従しません。本物と偽物の表示は同じです。'))+para('<small>写真は説明用APで正規購入した猫・銃・ソナーです。猫の写真は通常の探索処理を90ステップ進めて撮影しています。</small>'),'猫の追加配備・範囲拡張は構想。現状は1匹の配備と解析速度の強化。')
 item_rows=[[esc(x['name']),esc(x['detail'])] for x in SNAP['items'].values()]
 page('探索の報酬','10個の宝箱と、8種類の使い切りアイテム。',twocol(figure('chest'),figure('inventory'))+table(['使い切りアイテム','現版の効果（調整用の値）'],item_rows,'dense')+para('<small>通常6・レア3・伝説1。到達可能な場所から抽選。攻撃系の「最大200人」は上限で、周辺人数や遮蔽に左右されます。バッグの写真は撮影用にこのランの10個を開封した結果です。</small>'),'スキルとは別の在庫。通常は近づいてGで開封し、Iでバッグ、Xで使用。')
 page('マップの全体像','3棟は、ひとつの探索空間。',mapfig(site,'1階の床と2階の連絡橋を重ねた整理図。現実のレイクタウンの地図ではありません。')+ '<div class="three">'+''.join(f'<div><h3>{a}</h3><p>{b}</p></div>' for a,b in [('A館','曲線の主通路と北側の回遊路。地下食品街・屋上庭園・西駐車場を持つ。'),('B館','斜めの主回廊・曲線の副回廊・光/時/翼の3広場。各階の店と大型売場。'),('C館','屋外型の街路・中庭。2階テラスとB館からの連絡橋。')])+'</div>','参考にするのは巨大商業施設の回遊性。実在施設の完全再現ではありません。','site')
 status=[]
 for level in [3,2,1,0,-1]:
  row=[FLOOR_NAMES[level]]
  for building in ['A','B','C']:
   f=FLOORS[f'{building}/{FLOOR_SHORT[level]}'];row.append(badge('実装済み')+f'　滞在 {f["fixed_people"]}人' if f['implemented'] else badge('構想・未実装','goal'))
  status.append(row)
 page('実装範囲','15フロアのうち、現在は10フロア。',table(['階層','A館','B館','C館'],status)+twocol(callout('人数の見方','上の人数は撮影時の1,000人設定における「滞在型900人」の初期配置です。別に歩行者100人がいます。固定された人も姿勢・役割の動作を持ちます。'),callout('範囲の見方','「実装済み」は探索できる床と接続があるという意味です。内装・人物・施設の密度や仕上げを完成品質と判定した表示ではありません。'))+para('西駐車場はA館1階側の付属エリアとして数え、15フロアへ重複加算しません。300人設定は比較用に残しています。')+para('<strong>この後の10ページ：</strong> 各フロアの平面図と、同じ場所の実画面。店舗番号は巻末の101店舗一覧と対応します。'),'完成版5,000人の初期配置案と、現在の人数配分を混同しないための一覧。')
 floor_info=[
 ('A','1F','a-center','中央吹き抜けと店舗の回遊','1階には中央入口、食品スーパー、フードコート、トイレ、読書・待合の役割を配置。中央と木もれびの吹き抜けに上下対の昇降口があります。','a-entry'),
 ('A','2F','a-2f','ファッション・コスメ・暮らし','専門店の内容を1階から変更。北側の回遊路と大型売場も探索でき、B館へは西側の2階連絡通路で移動します。',None),
 ('A','3F','a-3f','キッズ・文具・楽器・ホビー','店舗に入れる3階。二つの吹き抜けの昇降口、回廊、店舗前の床をつなぎます。楽器店の写真は現在の陳列密度です。',None),
 ('A','B1','a-basement','地下食品街','7つの食品カウンターと食品棚。A館西側の通常階段で接続します。B/C館の地下を実装したものではありません。',None),
 ('A','RF','a-roof','屋上庭園','植栽と休憩席のあるA館の屋上エリア。通常階段で到達できます。立体駐車場全体や車両の運転は未実装です。',None),
 ('B','1F','b-1f','3広場をつなぐ分岐・回遊','光・時・翼の広場と、背面の回遊路へ店舗を接続。奥の大型売場は家電。地上側の歩行接続からA/C館へ移動できます。',None),
 ('B','2F','b-2f','広い回廊から店舗へ','主回廊10m・背面通路14m、連絡路12m。昇降口の踊り場から店舗前へ抜ける床を確保。奥の大型売場は生活用品です。',None),
 ('B','3F','b-3f','上階の回遊と映画館','2階と同様に店前の床を保護して吹き抜けを生成。3階の大型施設は映画館です。写真には現在の回廊と映画館を載せています。','b-cinema'),
 ('C','1F','c-1f','屋外街路と3つの中庭','ゲート・ガーデン・テラスの各コートを曲線の街路で接続。アウトレットを意識した独立した店構えです。',None),
 ('C','2F','c-2f','ガーデンテラスと3店舗','書店・生活雑貨・カフェ。ゲートコートの通常階段と、B館2階からのガーデンブリッジで接続します。',None)
 ]
 for building,key,shot,title,description,extra in floor_info:
  f=FLOORS[f'{building}/{key}'];right=figure(shot)+f'<h3>{title}</h3>'+para(description)+table(['売場・施設','撮影時の滞在型NPC'],[[f'{len(f["shops"])}区画',f'{f["fixed_people"]}人']])
  right+=callout('見どころを確認する','図では形状・入口側のつながり、写真では高さ・見通し・店舗や人物の密度を確認できます。壁や内装の細部は、原寸PNGで拡大してください。')
  page('フロアごとの設計図と実画面',f'{building}館 / {FLOOR_NAMES[f["level"]]}',twocol(mapfig(maps[f['id']]),right,'floor'),f'現在の床・店舗定義から作図 / {len(f["shops"])}店舗・売場区画 / 写真はv0.23','floor-page')
 page('館と階を移る','連絡通路も、歩いてつながる。',twocol(figure('ab-bridge'),figure('bc-bridge'))+twocol('<h3>A館 ↔ B館</h3>'+para('2階のガラス張り連絡通路。1階にも駐車場側の歩行接続があります。A館西側の通常階段は地下・地上・屋上へ接続します。'),'<h3>B館 ↔ C館</h3>'+para('1階の歩行接続に加え、2階にはガーデンブリッジ。C館内には1階から2階へ上がる通常階段があります。'))+callout('ファストトラベルは訪問済みだけ','移動スキルを購入し、実際に近づいて記録した地点をMの案内図から選びます。未訪問の場所へはワープできません。現在は20地点。'),'エスカレーターはA館2か所・B館3か所の吹き抜けに分散。1↔2階・2↔3階の上下対、合計20本。')
 page('店構えと陳列','看板・商品・入口を、店の種類で変える。','<div class="gallery">'+figure('a-entry')+figure('a-2f')+figure('a-3f')+figure('b-cinema')+'</div>'+para('現在は101店舗・売場、ブランド看板106枚、58の架空ブランド。売場小物の配置は34,898組。商品数のカウントは配置データの組数で、固有の高精細モデル数とは異なります。現版の棚や物の量・簡略な造形も、そのまま写真で確認できます。'),'衣料・コスメ・楽器・映画館の代表例。全店舗の位置と名称は、巻末とCSVに収録。')
 page('商業施設の生活感','食べる、休む、身支度する。',twocol(figure('a-food'),figure('a-restroom'))+twocol('<h3>フードコート</h3>'+para('着席客、テーブル・椅子、食器、注文側のカウンター。現在の密度や造形は写真の状態です。NPCの飲食は役割別の演出です。'),'<h3>トイレ・試着室</h3>'+para('男女別区画、洗面、個室、多機能/ベビー室。個室・試着室など13枚の扉を近づいて注視しFで開閉。空の個室にNPCや宝箱を配置しない設計です。'))+para('現時点で、NPCが扉を開けて個室を利用する施設AIや、すべての店舗での接客会話は完成していません。'),'主要動線以外の機能と、現在できるインタラクション。')
 page('人物の現状','同じ顔、違う服、違う過ごし方。',twocol(figure('person-1'),figure('speech'))+table(['現在の表現','残る制作'],[['同じ基礎の顔。肌色・髪色・顔幅をタイトルで設定。','写真を使った顔生成、細かな顔パーツ編集。'],['近距離/遠距離モデルと、役割に応じた姿勢・小さな動き。','専用の高品質人物、衣服・髪・手指・表情の仕上げ。'],['店員・買物・読書・着席・会話・休憩・歩行など。','音声会話、分岐会話、さらに自然な施設利用。']])+para('人物の目標は若い成人のスタイライズ表現です。『ペルソナ5』程度の作り込みを将来の目安とし、現版がその完成度に到達したという扱いにはしていません。写真は別モデルへの置き換えを行っていません。'),'人物近接は、通常ゲーム内の同じ会話役の人物を固定カメラで記録。')
 page('起動から案内図まで','日本語UIで、選ぶ・探す・見直す。',twocol(figure('title'),figure('map'))+twocol(callout('通常開始とデバッグ開始','通常は初期スキャナーから成長します。タイトルの「デバッグ：スキャン系スキルを全解放」をONにすると、銃・銃の強化・連鎖・範囲・ソナー等を最大段階で試せます。'),callout('基本操作','WASD移動 / マウス視点 / Shiftダッシュ / Spaceジャンプ / 左クリック解析・射撃 / 右クリック照準 / Rリロード / 1・2装備 / Tabスキル / M案内図 / Iバッグ / F文脈操作 / G宝箱 / Xアイテム。')),'画面は現在のUI。案内図の色、未訪問表示、人数選択、デバッグの位置も確認できます。')
 diagram='<div class="architecture"><div><b>配置・店舗データ</b><span>外形 / 開口 / 店 / 什器</span></div><i>→</i><div><b>共通の地形変換</b><span>曲線化 / A館の奥行き拡張</span></div><i>→</i><div><b>同じ空間を使う仕組み</b><span>描画 / 衝突 / 経路 / 宝箱 / 案内図</span></div></div>'
 page('仕組みの設計図','見た目と判定を、同じデータへつなぐ。',diagram+twocol('<h3>人物は1人ずつ管理</h3>'+para('全員に個別のIDとスキャン状態を持たせます。本物はランの開始時に一度だけ抽選。描画の簡略化と、本人判定・消滅状態の管理を分けます。')+callout('役割と描画','滞在型900人と歩行100人。遠距離ではモデルを簡略化し、静的建築や商品はまとめて描画する構成です。'),'<h3>改修時に揃えるもの</h3>'+bullet(['床と壁・開口・ガードレールの物理形状。','猫・歩行者・アイテムが使う経路。','到達可能な宝箱候補とNPCの解析位置。','各階の案内図と、訪問済み移動地点。']))+table(['主要な管理','対応するソース'],[['本物・AP・スキル','IdentityRun / identity_run.gd'],['人物の役割・位置・描画','Crowd / crowd.gd'],['床形状・フロア・案内図','MallStructure / MallLayout / MallCurve'],['スキャン・猫・アイテム・UI','main.gd / CatSearch / RunLoot / FindHUD']]),'現在の実装構造を、読みやすく整理した図。3Dゲーム画面ではありません。')
 target_rows=[]
 for idx,level in enumerate([-1,0,1,2,3]):target_rows.append([FLOOR_NAMES[level]]+[f'{SNAP["target_distribution"][b][idx]:,}人' for b in ['A','B','C']])
 page('完成版の構想','5,000人・3棟15フロアへ。',twocol('<h3>維持する中心コンセプト</h3>'+bullet(['自分と同じ顔の5,000人から、本当の自分1人を見つける。','探索、FPSの操作感、まとめて解析する爽快感、成長を両立。','本物の固定・等確率。時間のために配置や確率を操作しない。','初期スキャナーで最終確認。猫・特殊攻撃は発見を助ける。']),'<h3>3時間は、目標の平均時間</h3>'+para('3時間を必ず遊ばせる仕様ではありません。現版1,000人の実測平均として扱える時間は、まだありません。以前の10万回の集約試算も、v0.23を10万回プレイした実測ではありません。'))+table(['完成版の仮配置','A館','B館','C館'],target_rows+[['計','1,500人','2,300人','1,200人']])+para('<small>上表は初期のバランス用仮設定。現在の滞在900人・歩行100人の配分とは別です。混雑、店内探索、成長速度、残り人数が少ない終盤の負担を検証して調整します。</small>'),'確定した方向と初期の仮設定。個々の未実装フロアの詳細間取りは、まだ決定済みとして描いていません。')
 verification=json.loads((ROOT/'docs/upper-access-verification.json').read_text())
 page('品質と次の課題','動作の確認と、美術の完成は分けて見る。','<div class="metrics">'+''.join(f'<div><b>{a}</b><span>{b}</span></div>' for a,b in [('1,238','v0.23の検証項目'),('29','検証スイート'),('47,275','公開床の検査点'),('294,575','水平接続の中点')])+'</div>'+twocol('<h3>確認できていること</h3>'+bullet(['全20本の昇降、乗降後の回廊・店舗への歩行。','猫の到達、NPCの管理、宝箱、訪問済み移動。','公開床と接続中点の欠落0件。','Linux実行ファイルで1,000人の起動。配布ZIPの再展開確認。']),'<h3>次の制作課題</h3>'+bullet(['未実装5フロアと、館ごとの機能・内装の拡充。','人物の造形・衣服・髪・表情、店内の細部と照明。','5,000人の描画・AI、終盤の探索負担。','Windows実機とRTX 4060 LaptopでのFPS測定。']))+callout('資料作成時点の位置づけ','Steam販売を最終目標にした日本語開発版です。施設の密度、仕上げ、自然な動作など、写真で見える未完成の部分も現状として残しています。'),'上の数値は機能・データの検証。美術品質やWindows実機のフレームレートを保証する数値ではありません。')
 skill_rows=[]
 for key,s in SNAP['skills'].items():
  price='3,330 / 1,000 AP' if key=='gun' else f'{s["cost"]} AP × 段階'
  skill_rows.append([s['branch'].split(' / ')[-1],s['name'],str(s['max']),price,s['detail']])
 page('付録 / 現在の成長設計','実装済みスキル一覧',table(['系統','スキル','最大段階','価格の基本','効果'],skill_rows,'skills-table')+para('銃の価格は左から1,000人設定 / 300人設定。それ以外の段階価格は「基本価格×購入する段階」。銃の強化は銃、猫パンチ強化は猫の購入が前提です。')+callout('構想に残る能力','スライディング、エアダッシュ、グラップリング、猫の複数配備、銃の拡散/連射強化、特殊スキルとしてのビーム・衝撃波・ブラックホール・広域一斉解析などは未実装です。ブラックホールは現在、宝箱の使い切りアイテムとして存在します。'),'一覧はv0.23のIdentityRun.SKILLSから作成。15種類。')
 for building_label,selected in [('A館',[u for u in UNITS if u['building']=='A']),('B館・C館',[u for u in UNITS if u['building']!='A'])]:
  split=(len(selected)+1)//2
  def outlet_rows(rows):return table(['番号','フロア','店舗・売場'],[[f'{u["number"]:03}',u['building']+'/'+FLOOR_SHORT[u['level']],esc(u['name'])] for u in rows],'outlets')
  page('付録 / 配置図の店舗番号',building_label+'の店舗・売場一覧',twocol(outlet_rows(selected[:split]),outlet_rows(selected[split:]))+para('番号はこの資料の配置図とCSVで共通です。NPCのIDや、ゲーム画面の解析対象番号とは別です。カウンター・大型売場も含めた区画数で、独立したブランド数とは異なります。'),f'{len(selected)}区画 / 名称・配置は現版データから抽出')
 page('出典と読み方','この資料の基準と、写真の条件。',twocol('<h3>基準</h3>'+para(f'<strong>FIND YOURSELF {VERSION}</strong><br>ゲーム基準コミット：<code>{REV}</code>')+bullet(['Godot 4.6.3 / GL Compatibility / 標準画質。','新規の実画面30点。建築や人物を撮影専用モデルに置き換えていません。','通常は人物の移動と動作を止め、固定カメラで撮影。','スキャン・猫・宝箱・UIは、キャプションの説明用設定で処理を進めています。'])+callout('画像の区別','「実画面」はゲームの描画。「配置図」は同じ床・店舗データから作図した図です。PNG原本と撮影条件はZIPに同梱します。'),'<h3>参照した設計・検証</h3>'+bullet(['docs/DESIGN.md / docs/ART_AND_LAYOUT.md','docs/UPPER_ACCESS.md / docs/WORLD_BAKING.md','docs/upper-access-verification.json','scripts/mall_layout.gd / mall_structure_data.gd','scripts/identity_run.gd / run_loot.gd','scripts/retail_density.gd / store_signs.gd'])+'<h3>一緒に渡すもの</h3>'+bullet(['このPDF：全体を順番に読む。','同内容のHTML：オフラインで閲覧・画像拡大。','10フロア＋全体配置のPNG図。','30枚のスクリーンショット原本。','101区画のCSV、抽出データ、撮影条件。']))+para('フォントはNoto Sans CJK JPを使用。資料内の日本語文字のみをサブセット埋め込みし、ライセンスを同梱します。ネット接続もゲームのインストールも、資料閲覧には不要です。'),'過去の仕様書は開発履歴を含むため、この資料では現在のソースとv0.23の検証結果を優先しています。')

CSS='''
@font-face{font-family:ReviewSans;src:url("FONT_DATA") format("woff");font-weight:100 900;font-display:block}
*{box-sizing:border-box}html{background:#dbe3df;scroll-behavior:smooth}body{margin:0;font-family:ReviewSans,"Yu Gothic",Meiryo,sans-serif;color:#183a42;font-size:10pt;line-height:1.65}h1,h2,h3,p{margin:0}h1{font-size:25pt;line-height:1.25;font-weight:700;letter-spacing:-.02em}h2{font-size:19pt}h3{font-size:13pt;margin:2mm 0}p{margin:2mm 0}ul{padding-left:5mm;margin:2mm 0}li{padding:1mm 0}small{font-size:8.1pt;color:#536b6c}code{font-size:8pt;word-break:break-all}.page{width:297mm;height:210mm;padding:12mm 14mm 13mm;margin:6mm auto;position:relative;background:#fffdf8;box-shadow:0 2px 20px #193b4230;break-after:page}.heading{height:26mm;border-bottom:1px solid #c9d6cf;margin-bottom:4mm}.kicker{font-size:8pt;color:#657e78;letter-spacing:.14em;margin-bottom:2mm}.sub{font-size:8.4pt;color:#607575;margin-top:2mm}.body{height:150mm}.footer{position:absolute;bottom:5mm;left:14mm;right:14mm;border-top:1px solid #c9d6cf;display:flex;justify-content:space-between;padding-top:2mm;font-size:7pt;color:#657e78}.two{display:grid;grid-template-columns:1fr 1fr;gap:6mm}.three{display:grid;grid-template-columns:1fr 1fr 1fr;gap:7mm}.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:3mm;margin-bottom:5mm}.metrics div{border-left:3px solid #b7894d;background:#ecf1eb;padding:3mm 4mm}.metrics b{display:block;font-size:23pt;line-height:1.2}.metrics span{font-size:8pt}.flow{display:grid;grid-template-columns:repeat(5,1fr);gap:2mm;margin:0 0 4mm}.flow div{background:#183a42;color:#fffdf8;padding:3mm}.flow b,.flow span{display:block}.flow b{font-size:12pt}.flow span{font-size:7.5pt;color:#d1ded6}figure{margin:0 0 2mm}figure img{display:block;width:100%;height:69mm;object-fit:contain;background:#e8eee9;cursor:zoom-in}figcaption{font-size:7.4pt;color:#526b6b;line-height:1.5;margin-top:1.2mm}.real,.plan{font-weight:normal;font-size:6.7pt;display:inline-block;padding:.1mm 1.5mm;color:white;background:#426f66;margin-right:1mm}.plan{background:#7f734c}.map img{height:133mm;background:#f4f6f3}.site .map img{height:116mm}.site .three p{font-size:8.5pt}.floor-page .floor{grid-template-columns:1.12fr .88fr;gap:5mm}.floor-page .floor>div:nth-child(2)>figure img{height:61mm}.floor-page .floor>div:nth-child(2)>figure.small-shot img{height:42mm}.floor-page .floor aside{font-size:8.5pt}.floor-page .floor p{font-size:9pt}.floor-page .floor table{margin:2mm 0}.floor-page .floor h3{font-size:12pt}.floor-page .floor .map img{height:137mm}.gallery{display:grid;grid-template-columns:1fr 1fr;gap:3mm 5mm}.gallery img{height:58mm}.gallery+p{font-size:9pt}table{border-collapse:collapse;width:100%;font-size:9pt;margin:3mm 0}th{background:#e5ece5;text-align:left;padding:2mm 2.4mm;color:#20474a;font-weight:600}td{padding:2mm 2.4mm;border-bottom:1px solid #d7dfd7;vertical-align:top}tr:nth-child(even) td{background:#f3f5ef}.dense{font-size:8pt;margin:1.5mm 0}.dense th,.dense td{padding:1.15mm 2mm;line-height:1.4}.dense th:first-child,.dense td:first-child{width:29%}.skills-table{font-size:8.1pt}.skills-table td,.skills-table th{padding:1.25mm 1.7mm;line-height:1.4}.skills-table td:nth-child(5){width:40%}aside{background:#eaf0e8;border-left:3px solid #ad8656;padding:2.5mm 3.5mm;margin:3mm 0;font-size:9pt}aside strong{font-size:10pt}aside p{margin:1mm 0}.tag{font-size:8pt;border-radius:2mm;padding:.5mm 2mm;white-space:nowrap;background:#d5e7d8;color:#285744}.tag.goal{background:#f0e3c6;color:#825b26}.architecture{display:flex;align-items:center;gap:3mm;margin:3mm 0 8mm}.architecture div{flex:1;background:#e9efe8;border-top:4px solid #7faaa0;padding:7mm 4mm}.architecture b,.architecture span{display:block}.architecture span{font-size:8pt;margin-top:3mm}.architecture i{font-size:20pt;font-style:normal;color:#aa844c}.outlets{font-size:8.1pt;margin-top:0}.outlets th,.outlets td{padding:.55mm 1.5mm;line-height:1.25;white-space:nowrap}.outlets td:nth-child(1){width:9mm;color:#7d683f}.outlets td:nth-child(2){width:14mm}.outlets td:nth-child(3){font-size:7.9pt}.cover .heading{height:32mm;border:0}.cover h1{font-size:43pt}.cover figure.hero img{height:110mm;object-fit:cover}.cover-bottom{display:flex;justify-content:space-between;align-items:center;margin-top:5mm}.cover .version{font-size:33pt;color:#9d7b47}.cover .version span{display:block;font-size:8pt;color:#657e78}.cover .sub{margin-top:2mm}.toolbar{position:sticky;top:0;background:#183a42ee;color:white;padding:12px 24px;z-index:2;display:flex;gap:24px;justify-content:center;align-items:center;font-size:13px}.toolbar a,.toolbar button{color:#fffdf8;background:transparent;border:1px solid #6f9890;border-radius:4px;padding:6px 12px;text-decoration:none;font:inherit;cursor:pointer}.toolbar span{color:#c4d7ce}dialog{max-width:96vw;max-height:96vh;padding:15px;border:0;background:#fffdf8}dialog::backdrop{background:#091f25e8}dialog img{max-width:90vw;max-height:83vh;object-fit:contain}dialog button{float:right;font:inherit;padding:6px 20px}dialog p{font-size:14px}
@page{size:A4 landscape;margin:0}@media print{html,body{background:white}.toolbar,dialog{display:none!important}.page{margin:0;box-shadow:none;page-break-after:always;break-inside:avoid}.page:last-of-type{page-break-after:auto}figure img{cursor:default}}
@media screen and (max-width:1130px){.page{margin:5mm 8px}.toolbar{justify-content:flex-start;flex-wrap:wrap}}
'''
def html_document():
 total=len(PAGES);parts=[]
 for n,p in enumerate(PAGES,1):
  parts.append(f'<section class="page {p["cls"]}" id="p{n}"><header class="heading"><div class="kicker">{p["kicker"]}</div><h1>{p["title"]}</h1><div class="sub">{p["sub"]}</div></header><div class="body">{p["body"]}</div><footer class="footer"><span>FIND YOURSELF / v0.23 現状資料 / 基準 {REV[:7]}</span><span>{n:02d} / {total:02d}</span></footer></section>')
 text=''.join(parts)
 from fontTools import subset
 from fontTools.ttLib import TTFont
 options=subset.Options();options.hinting=False;subsetter=subset.Subsetter(options=options);subsetter.populate(text=re.sub('<[^>]+>','',text)+'0123456789↑↓↔●→');tt=TTFont(str(FONT));subsetter.subset(tt);tt.flavor='woff';buf=io.BytesIO();tt.save(buf);font_data='data:font/woff;base64,'+base64.b64encode(buf.getvalue()).decode()
 style=CSS.replace('FONT_DATA',font_data)
 toolbar='<nav class="toolbar"><strong>FIND YOURSELF / v0.23</strong><a href="#p2">概要</a><a href="#p7">全体マップ</a><a href="#p9">各フロア</a><a href="#p25">完成版の構想</a><button onclick="window.print()">印刷・PDF保存</button><span>画像クリックで拡大 / 全30ページ</span></nav>'
 script='''<dialog id="viewer"><button onclick="viewer.close()">閉じる</button><p id="caption"></p><img id="full" alt="拡大画像"/></dialog><script>const viewer=document.querySelector('#viewer');document.querySelectorAll('figure img').forEach(img=>img.onclick=()=>{document.querySelector('#full').src=img.src;document.querySelector('#caption').textContent=img.alt;viewer.showModal()});viewer.onclick=e=>{if(e.target===viewer)viewer.close()}</script>'''
 return '<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FIND YOURSELF v0.23 — 現状資料集</title><style>'+style+'</style></head><body>'+toolbar+text+script+'</body></html>'

def build():
 OUT.mkdir(exist_ok=True);MAPS.mkdir(exist_ok=True)
 maps={f['id']:draw_map(f) for f in SNAP['floors'] if f['implemented']};site=draw_site();content(maps,site);assert len(PAGES)==30,len(PAGES)
 html=html_document();(OUT/(STEM+'.html')).write_text(html)
 with (OUT/(STEM+'-stores.csv')).open('w',encoding='utf-8-sig',newline='') as handle:
  writer=csv.writer(handle);writer.writerow(['図の番号','建物','フロア','店舗・売場名','カテゴリ','内部ID'])
  for u in UNITS:writer.writerow([f'{u["number"]:03}',u['building'],FLOOR_NAMES[u['level']],u['name'],cat(u),u['id']])
 print('HTML_READY',len(PAGES),'pages',len(html),'characters',flush=True)
 manifest={'version':VERSION,'game_source_commit':REV,'pages':len(PAGES),'screenshots':SNAP['captures'],'maps':[p.name for p in maps.values()]+[site.name],'outlets':len(UNITS),'font_license':'third_party/noto-cjk-COPYRIGHT.txt','notes':['Screens are actual game renders; preparation is disclosed per image.','Maps are diagrams exported from the same current geometry definitions.','The game and its downloadable build ZIPs are not modified by this documentation task.']}
 (ROOT/'docs/review-v023-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 if args.html_only:return
 from playwright.sync_api import sync_playwright
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
  page=browser.new_page(viewport={'width':1280,'height':900},device_scale_factor=1)
  page.set_content(html,wait_until='load');page.evaluate('document.fonts.ready');page.wait_for_timeout(500)
  failures=page.evaluate('''Array.from(document.querySelectorAll('.page')).map(p=>{let b=p.querySelector('.body'),f=p.querySelector('.footer');return {page:p.id,title:p.querySelector('h1').textContent,contentBottom:Math.max(...Array.from(b.children).map(e=>e.getBoundingClientRect().bottom)),footerTop:f.getBoundingClientRect().top}}).filter(x=>x.contentBottom>x.footerTop-8)''')
  broken=page.evaluate('Array.from(document.images).filter(i=>i.id!=="full"&&(!i.complete||i.naturalWidth===0)).map(i=>i.alt)')
  assert not failures,failures
  assert not broken,broken
  import inspect
  pdf_options={'path':str(OUT/(STEM+'.pdf')),'print_background':True,'prefer_css_page_size':True}
  if 'outline' in inspect.signature(page.pdf).parameters:pdf_options['outline']=True
  page.pdf(**pdf_options)
  page.emulate_media(media='print');page.locator('#p2').screenshot(path='/tmp/fy-review-layout-check.png')
  browser.close()
 from pypdf import PdfReader,PdfWriter
 source_pdf=PdfReader(OUT/(STEM+'.pdf'));writer=PdfWriter();writer.clone_document_from_reader(source_pdf)
 for i,p in enumerate(PAGES):writer.add_outline_item(f'{i+1:02d} / {p["title"]}',i)
 writer.add_metadata({'/Title':'FIND YOURSELF v0.23 — 現状資料集','/Subject':'構想・マップ・実画面で見る現在のゲーム'})
 buffer=io.BytesIO();writer.write(buffer);(OUT/(STEM+'.pdf')).write_bytes(buffer.getvalue())
 pdf=PdfReader(OUT/(STEM+'.pdf'),strict=True);assert len(pdf.pages)==30,len(pdf.pages)
 text='\n'.join(p.extract_text() for p in pdf.pages);assert all(word in text for word in ['現在は','5,000','B館','スキャナー','参考','0.23'])
 (ROOT/'docs/review-v023-validation.json').write_text(json.dumps({'pdf_pages':len(pdf.pages),'pdf_bookmarks':len(pdf.outline),'screenshots':len(CAPTURES),'maps':len(maps)+1,'outlets_csv_rows':len(UNITS),'broken_images':broken,'layout_overflows':failures,'strict_pdf_reader':True,'all_assets_embedded_in_html':True,'source_revision':REV},ensure_ascii=False,indent=2)+'\n')
 readme='''FIND YOURSELF v0.23 現状資料集\n\n1. PDFを開くと、ゲームを起動せずに全体と各館を確認できます。\n2. HTMLはブラウザーで開きます。ネット接続不要。画像クリックで拡大できます。\n3. screenshots/ はゲーム画面のPNG原本30枚、maps/ は配置図11枚です。\n4. stores.csv は101店舗・売場の一覧。番号は配置図と対応します。\n5. snapshot.json / capture-manifest.json に元データ・撮影設定があります。\n\n基準ゲーム：0.23.0 / 40ccc24b350373fbc40d14489ea1a46a5207737d\n現在1,000人（300人も選択）・10/15フロア。完成版の構想と現状はPDFで区別しています。\nこのZIPは閲覧資料です。ゲームのEXEやGodot本体のインストールは不要です。\n'''
 zip_path=OUT/(STEM+'.zip')
 with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  z.write(OUT/(STEM+'.pdf'),'FIND_YOURSELF_現状資料.pdf');z.write(OUT/(STEM+'.html'),'はじめに開く_現状資料.html');z.writestr('お読みください.txt',readme)
  z.write(OUT/(STEM+'-stores.csv'),'stores.csv')
  for c in SNAP['captures']:z.write(SHOTS/c['image'],'screenshots/'+c['image'])
  for p in list(maps.values())+[site]:z.write(p,'maps/'+p.name)
  z.write(ROOT/'docs/review-v023-snapshot.json','snapshot.json');z.write(ROOT/'docs/review-v023-manifest.json','capture-manifest.json');z.write(ROOT/'docs/review-v023-validation.json','validation.json');z.write(ROOT/'third_party/noto-cjk-COPYRIGHT.txt','licenses/noto-cjk-COPYRIGHT.txt')
 with zipfile.ZipFile(zip_path) as z:assert z.testzip() is None
 sums=[]
 for suffix in ['pdf','html','zip']:
  path=OUT/(STEM+'.'+suffix);assert path.stat().st_size<100*1024*1024;sums.append(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n');print(path.name,path.stat().st_size,flush=True)
 (OUT/(STEM+'-SHA256SUMS.txt')).write_text(''.join(sums))
 print('REVIEW_COMPLETE',flush=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--html-only',action='store_true');args=parser.parse_args();build()
