from pathlib import Path
import sys,json,importlib.util,math
sys.path.insert(0,'tools')
import build_mall_structure as m
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];source=json.loads((ROOT/'assets/layout/mall_structure.json').read_text());d=m.compile_plan(source);b=source['B']
font=lambda size:ImageFont.truetype(str(ROOT/'assets/fonts/NotoSansCJKjp-Regular.otf'),size)
for level in range(3):
 im=Image.new('RGB',(2700,1120),'#14272d');dr=ImageDraw.Draw(im);scale=4.25;origin=(-708,-85)
 def xy(p):return (round(50+(p[0]-origin[0])*scale),round(95+(p[1]-origin[1])*scale))
 def poly(g,fill,outline=None):
  if g.is_empty:return
  for a in m.polys(g):
   dr.polygon([xy(p) for p in a.exterior.coords],fill=fill,outline=outline)
   for r in a.interiors:dr.polygon([xy(p) for p in r.coords],fill='#14272d')
 for packet in d['B']['floors'][level]['polygons']:poly(m.Polygon(packet['outer'],packet['holes']),'#b4d7b9','#e8efe9')
 for i,st in enumerate(b['stores']+b['rear_stores']):
  g=m.store_shape(st);poly(g,'#abcbdc','#467e99');dr.text(xy(g.centroid.coords[0]),f'{i+1:02d}',font=font(24),anchor='mm',fill='#14272d')
 poly(m.rect(b['anchor']),'#abcbdc','#467e99');dr.text(xy((-669,0)),'13',font=font(27),anchor='mm',fill='#14272d')
 public_floor=m.unary_union([m.Polygon(p['outer'],p['holes']) for p in d['B']['floors'][level]['polygons']])
 for p in b['plazas']:
  opening=m.court(p,True) if level==0 else m.court(p,True).difference(public_floor)
  poly(opening,'#fbe3a6' if level==0 else '#d1b373')
  dr.text(xy((p['at'][0],p['at'][1]-3)),p['name'],font=font(23),fill='#14272d',anchor='mm')
 for bank in b['escalator_banks']:
  cx,cz=bank['at'];side=bank['side']
  for lane in (0,1):
   x=cx+side*[13.5,16.5][lane];a=xy((x,cz-6));c=xy((x,cz+6));dr.line([a,c],fill='#e45d35' if lane==0 else '#4b738d',width=7)
 for path in [b['main'],b['loop'],b['north_loop']]:
  points=list(m.curve(path).coords) if path!=b['main'] else path
  dr.line([xy(v) for v in points],fill='#6e9974',width=2)
 dr.text((40,20),f'B館 {level+1}F  基本構造改修 / 床・店舗の共通データによる上面図（実画面ではありません）',font=font(30),fill='white')
 for label,at in [('A館 接続',(-165,-24)),('C館 / 1F屋根付き歩道',(-370,-70)),('C館 / 2Fガーデンブリッジ',(-442,-70))]:
  dr.text(xy(at),label,font=font(19),fill='#e5eeee',anchor='mm',stroke_width=1,stroke_fill='#14272d')
 dr.text((50,850),'緑：公開床・回遊路  青：既存の入店可能売場  金：吹き抜け（1Fは広場床）  朱/紺：上り/下り',font=font(22),fill='#d3e2d9')
 dr.text((50,888),'図の上がZ− / 下がZ＋。実在施設の方位・測量図ではありません。B館の地下・屋上、階段・エレベーターは未施工。',font=font(22),fill='#d3e2d9')
 a=xy((-690,118));c=xy((-590,118));dr.line([a,c],fill='white',width=3);dr.text((a[0],a[1]+8),'100m',font=font(22),fill='white')
 dr.text((50,1000),f'本体約508×145m（連絡通路を除く） / 主軸16m・南北回廊14m・分岐10m / 13売場 / 床高 { [0,5.525,10.875][level]}m',font=font(25),fill='white')
 im.save(ROOT/f'docs/images/mall24-b-{level+1}f.png')
print(json.dumps({k:{'bounds':[f['bounds'] for f in v['floors']],'area':[f['area'] for f in v['floors']]} for k,v in d.items()},ensure_ascii=False))

# Site drawing uses exported curved A/C geometry and current B definitions.
floors=json.loads((ROOT/'docs/map-master-floor-plans.json').read_text())
im=Image.new('RGB',(2600,1450),'#f4f6f3');dr=ImageDraw.Draw(im);k=2.9
def q(p):return (80+(p[0]+710)*k,160+(p[1]+215)*k)
for f,color in [(next(f for f in floors if f['building']==building and f['level']==0),color) for building,color in [('A','#c8dccc'),('B','#bdcddc'),('C','#e2d1b3')]]:
 for poly in f['base']:dr.polygon([q(v) for v in poly],fill=color,outline='#708684',width=2)
 for packet in f['structure']:
  dr.polygon([q(v) for v in packet['outer']],fill=color,outline='#708684',width=2)
  for h in packet['holes']:dr.polygon([q(v) for v in h],fill='#f4f6f3')
for label,points in [('A/B 2階連絡橋',[[-194,-5.5],[-110,-5.5]]),('B/C 2階連絡橋',[[-442,-47],[-442,-92],[-432,-117]])]:
 pts=[q(v) for v in points];dr.line(pts,fill='#a7672e',width=8,joint='curve');x,y=pts[len(pts)//2];dr.text((x+10,y-28),label,font=font(24),fill='#824e23',stroke_width=3,stroke_fill='#f4f6f3')
for label,at in [('A館',[-5,-4]),('B館',[-530,39]),('C館',[-380,-170]),('西駐車場',[-152,18])]:dr.text(q(at),label,font=font(48 if len(label)==2 else 25),anchor='mm',fill='#183a42',stroke_width=3,stroke_fill='#f4f6f3')
for label,at in [('A/B入口',[-190,-5.5]),('C館ゲート',[-370,-80])]:
 x,y=q(at);dr.ellipse((x-6,y-6,x+6,y+6),fill='#b96832');dr.text((x+10,y+6),label,font=font(23),fill='#183a42',stroke_width=3,stroke_fill='#f4f6f3')
for x in range(-700,101,100):
 at=q((x,110));dr.line((at[0],at[1],at[0],at[1]+14),fill='#617d76',width=2);dr.text((at[0],at[1]+22),f'X={x}',anchor='ma',font=font(23),fill='#183a42')
dr.text((60,30),'3館の位置関係 / 今回施工後の実際の座標',font=font(42),fill='#183a42')
dr.text((60,92),'1階の公開床＋2階の橋。B館本体を西へ拡張。A館の三角回遊、C館の追加階層は未施工。',font=font(28),fill='#526b6b')
dr.text((60,1300),'上＝Z−方向（実在の北とは異なります）。各館5層の構想に対し、現在はA5層・B3層・C2層＝10/15フロア。',font=font(28),fill='#183a42')
dr.text((60,1360),'床・店舗の共通定義から作図。実画面／実在施設の測量図ではありません。',font=font(26),fill='#526b6b')
im.save(ROOT/'docs/images/mall24-site.png')
