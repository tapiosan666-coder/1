from pathlib import Path
import math,json,csv,hashlib,io,base64,zipfile
from PIL import Image,ImageDraw,ImageFont
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/rebuild-v2';OUT.mkdir(exist_ok=True)
spine=[(12,85),(98,65),(184,95),(279,77),(354,109),(488,62)]
voids=[Polygon([(69,57),(83,43),(107,47),(119,64),(103,79),(80,75)]),Polygon([(261,67),(280,57),(301,66),(310,86),(291,99),(276,89)]),Polygon([(408,75),(425,60),(448,63),(458,76),(440,91),(420,89)])]
cores=[(139,28),(243,135),(379,33)]
fontpath=ROOT/'assets/fonts/NotoSansCJKjp-Regular.otf';font=lambda n:ImageFont.truetype(str(fontpath),n)
allfloors=[]
for floor,target in [(1,68),(2,70),(3,60)]:
 lanes=LineString(spine).buffer(8,join_style=2)
 courts=unary_union([v.buffer(9,join_style=2) for v in voids]);public=lanes.union(courts)
 branches=[[(98,65),(136,112),(220,125),(279,77)],[(354,109),(375,139),(452,122),(470,68)],[(184,95),(192,35),(277,28),(302,87)]]
 for branch in branches:public=public.union(LineString(branch).buffer(4.5,join_style=2))
 rooms=[]
 for i,(x,y) in enumerate(cores):
  rooms.append({'id':f'K{i+1}','polygon':[(x-13,y-10),(x+13,y-10),(x+13,y+10),(x-13,y+10)],'stairs':[x-10,y-7,7,14],'elevator':[x-1,y-7,5,5],'wc':[x+5,y-7,7,14]})
  public=public.union(LineString([(x,y),spine[[1,2,4][i]]]).buffer(4,join_style=2))
 candidates=[]
 segments=list(zip(spine,spine[1:]))+[pair for branch in branches for pair in zip(branch,branch[1:])]
 for seg,(a,b) in enumerate(segments):
  dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy);u=(dx/length,dy/length);n=(-u[1],u[0])
  for side in [-1,1]:
   t=3.;j=0
   while t<length-8:
    w=[7.5,10,13,8.5,16,11][(j+seg+floor+side)%6];w=min(w,length-t-1)
    if w<6:break
    depth=[14,18,23,16][(j+floor+seg)%4]
    def q(s,d):return (a[0]+u[0]*s+n[0]*d*side,a[1]+u[1]*s+n[1]*d*side)
    front=8 if seg<5 else 4.5
    coords=[q(t,front),q(t+w,front),q(t+w,front+depth),q(t,front+depth)];poly=Polygon(coords);door=q(t+w*.5,front)
    if not any(poly.intersection(v.buffer(2)).area>.1 for v in voids) and not any(poly.intersection(Polygon(k['polygon'])).area>.1 for k in rooms) and poly.intersection(public.buffer(-.15)).area<.2 and not any(poly.intersection(c['poly']).area>.1 for c in candidates):
     candidates.append({'poly':poly,'polygon':coords,'entry':door,'frontage':w,'depth':depth,'segment':seg,'side':side})
    t+=w+.3;j+=1
 # Spread selection over all parts of the spine rather than filling one end first.
 selected=[];groups=[[c for c in candidates if c['segment']==i] for i in range(len(segments))]
 while len(selected)<target and any(groups):
  for group in groups:
   if group and len(selected)<target:selected.append(group.pop(0))
 kinds=['衣料','生活雑貨','靴・鞄','食品・カフェ','書籍・文具','美容・ケア'] if floor<3 else ['キッズ','ホビー','飲食','体験・ゲーム','楽器','生活雑貨']
 stores=[]
 for i,c in enumerate(selected):
  stores.append({k:v for k,v in dict(c,id=f'B{floor}-{i+1:03}',kind=kinds[i%len(kinds)],accessible=True,route=f'P{c["segment"]+1}→入口→店内主路',floor=floor).items() if k!='poly'})
 # Distinct anchors, not included in ordinary tenant count.
 anchors=[{'id':f'B{floor}-A1','name':['大型生活店','書店・生活複合店','映画館'][floor-1],'polygon':[(-35,55),(8,55),(8,110),(-35,110)],'entry':[8,85]},{'id':f'B{floor}-A2','name':['食品核店','大型衣料店','フードホール'][floor-1],'polygon':[(480,31),(530,31),(530,100),(490,100),(480,78)],'entry':[488,62]}]
 public=public.union(LineString([(-10,85),(12,85)]).buffer(8)).union(LineString([(488,62),(500,62)]).buffer(8))
 floorrec={'floor':floor,'stores':stores,'anchors':anchors,'cores':rooms,'voids':[list(v.exterior.coords) for v in voids],'public':[{'outer':list(p.exterior.coords),'holes':[list(h.coords) for h in p.interiors]} for p in ([public] if public.geom_type=='Polygon' else public.geoms)],'centreline':spine,'branches':branches,'planned_only':True,'entry_checks':sum(public.distance(Point(s['entry']))<.001 for s in stores)}
 allfloors.append(floorrec)
 im=Image.new('RGB',(3000,1350),'#faf8f0');d=ImageDraw.Draw(im);scale=4.8
 def xy(p):return (210+p[0]*scale,200+p[1]*scale)
 def drawpoly(coords,fill,outline='#415a60',width=2):d.polygon([xy(p) for p in coords],fill=fill);d.line([xy(p) for p in coords]+[xy(coords[0])],fill=outline,width=width)
 for packet in floorrec['public']:
  drawpoly(packet['outer'],'#dce8dc')
  for hole in packet['holes']:drawpoly(hole,'#faf8f0')
 for anchor in anchors:drawpoly(anchor['polygon'],'#adbbc9');d.text(xy(Polygon(anchor['polygon']).centroid.coords[0]),anchor['name'],anchor='mm',font=font(26),fill='#243e48')
 for s in stores:
  drawpoly(s['polygon'],['#bcd8e0','#e6cba6','#d5c6db'][floor-1]);c=Polygon(s['polygon']).centroid;d.text(xy((c.x,c.y)),s['id'],anchor='mm',font=font(14),fill='#183a42');x,y=xy(s['entry']);d.ellipse((x-5,y-5,x+5,y+5),fill='#bf4e2f')
 for i,v in enumerate(voids):
  drawpoly(list(v.exterior.coords),'#eddfb4' if floor==1 else '#768d99',width=4);c=v.centroid;d.text(xy((c.x,c.y)),['翼 / 催事','時 / 分岐','光 / 連絡'][i],anchor='mm',font=font(22),fill='#203e46')
  cx,cy=c.x,c.y
  # Different orientations; paired flights for each floor connection.
  angle=[.3,1.57,-.6][i];u=(math.cos(angle),math.sin(angle));n=(-u[1],u[0])
  for lane in [-1,1]:
   a=(cx+u[0]*-7+n[0]*lane*2,cy+u[1]*-7+n[1]*lane*2);b=(cx+u[0]*7+n[0]*lane*2,cy+u[1]*7+n[1]*lane*2);d.line([xy(a),xy(b)],fill='#af5238' if lane==1 else '#42748c',width=9);d.text(xy(b if lane==1 else a),'↑' if lane==1 else '↓',font=font(24),fill='#243e48')
 for k in rooms:
  drawpoly(k['polygon'],'#e4bac1')
  for key,label in [('stairs','ST'),('elevator','EV'),('wc','WC')]:
   x,y,w,h=k[key];drawpoly([(x,y),(x+w,y),(x+w,y+h),(x,y+h)],'#eedddc');d.text(xy((x+w/2,y+h/2)),label,font=font(15),anchor='mm',fill='#263e48')
  x,y,w,h=k['wc']
  for j in range(3):
   drawpoly([(x+4,y+2+j*3),(x+7,y+2+j*3),(x+7,y+5+j*3),(x+4,y+5+j*3)],'#c4d3d8')
  d.text(xy((x-12,y-2)),k['id'],font=font(18),fill='#263e48')
 d.line([xy(p) for p in spine],fill='#4f8573',width=3)
 d.text((60,30),f'FIND YOURSELF / B館 {floor}F 建築平面・一次協議案',font=font(44),fill='#183a42')
 d.text((60,95),'未施工 / ゲーム用仮寸法。旧楕円リングを廃止し、屈曲する主軸と局所的な近道へ。',font=font(27),fill='#526c72')
 d.text((65,1070),f'図示：通常区画 {len(stores)} ＋ 核区画2。すべて計画上の区画数であり、完成店舗数ではありません。',font=font(28),fill='#183a42')
 d.text((65,1125),'主軸16m / 枝道9m / 設備連絡8m / 開口は2F・3Fで整合。赤点＝店舗入口。',font=font(27),fill='#183a42')
 d.text((65,1180),'局所座標を表示。既存館への接続・エスカレーター干渉・室内動線は設計審査待ち。実歩行テスト未実施。',font=font(26),fill='#8b4838')
 d.line((210,1260,690,1260),fill='#183a42',width=4);d.text((210,1280),'100m（ゲーム用仮設計）',font=font(22),fill='#183a42')
 im.save(OUT/f'B-{floor}F.png')
(OUT/'floor-design.json').write_text(json.dumps(allfloors,ensure_ascii=False,indent=2))
with (OUT/'tenant-schedule.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['店ID','階','業種','間口m','奥行m','入口X','入口Z','出入予定','NPC経路'])
 for floor in allfloors:
  for s in floor['stores']:w.writerow([s['id'],s['floor'],s['kind'],s['frontage'],s['depth'],*s['entry'],'可（未実装）',s['route']])
print([(f['floor'],len(f['stores']),f['entry_checks']) for f in allfloors])
