from pathlib import Path
import sys,math,json,collections
P=Path(__file__).resolve().parents[2];R=P/'evidence/v22-review';sys.path.insert(0,str(P/'authoring'));from site_v2_common import *
from shapely.validation import make_valid
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor,Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'));font='HeiseiKakuGo-W5';O=P/'evidence/v22-review/drawings';O.mkdir(exist_ok=True);F=read(P/'source/v11/floors-updated.json');maps=read(P/'source/v22/map-data-integrated.json');plan=read(P/'source/v22/retail-plan.json');commons=read(P/'source/v22/commons.json');W=lambda g:affinity.translate(g,429,-46);md={(d['wing'],d['level']):d for d in maps};PAGE=(1684,1191);C=canvas.Canvas(str(O/'v22-Floorplans-and-Sections.pdf'),pagesize=PAGE);C.setTitle('FIND YOURSELF v22 / 15-layer plans and sections / Independent validation')
def text(x,y,msg,size=12):C.setFont(font,size);C.setFillColor(HexColor('#263e42'));C.drawString(x,y,str(msg))
def allpolys(g):
 if g.is_empty:return[]
 if g.geom_type=='Polygon':return[g]
 return[p for child in getattr(g,'geoms',[])for p in allpolys(child)]
def geometry(g,fill,stroke='#475b5e',line=.35):
 if not g.is_valid:g=make_valid(g)
 C.setLineWidth(line);C.setStrokeColor(HexColor(stroke));C.setFillColor(HexColor(fill))
 for poly in allpolys(g):
  path=C.beginPath()
  for ring in [poly.exterior]+list(poly.interiors):
   pts=list(ring.coords);x,y=xy(pts[0]);path.moveTo(x,y)
   for q in pts[1:]:x,y=xy(q);path.lineTo(x,y)
   path.close()
  C.drawPath(path,fill=1,stroke=1,fillMode=0)
def frommap(a):return unary_union([Polygon(r[0],r[1:])for r in a])
colours={'book':'#d2dce6','home':'#e1d5bf','beauty':'#e8cfda','apparel':'#d9d0e6','food':'#d9dfbc','electronics':'#c9d8d7','cafe':'#edcfb4','restaurant':'#edcfb4','service':'#d8d8d8','cinema':'#b9bdd8','arcade':'#d8c1db','garden':'#c5ddc4','stationery':'#d1dce7'}
for f in F:
 wing=f['wing'];lev=f['level'];floor=f['label'];m=md[(wing,lev)];plate=W(frommap(m['floor']));xmin,zmin,xmax,zmax=plate.bounds;scale=min(1490/(xmax-xmin),940/(zmax-zmin));ox=85-xmin*scale;oy=135+zmax*scale
 def xy(p):return(ox+p[0]*scale,oy-p[1]*scale)
 text(60,1145,f'FIND YOURSELF v22 / {wing}館 {floor} / 詳細配置・検証図',24);text(60,1114,f'ゲーム用寸法 / 床レベル Y={f["height"]:.3f}m / 建築申請図・構造安全証明ではありません',13)
 geometry(plate,'#f0eeea',line=.7);geometry(W(frommap(m['public'])),'#fff7df','#d5cbb5',.20)
 for s in f['stores']:
  record=next(r for r in plan['stores']if r['id']==s['id']);geometry(W(s['polygon']),colours.get(record['category'],'#d2dfdc'));geometry(W(s['backroom']),'#b6b8b5','#717772',.2)
  q=W(s['sales']).representative_point();x,y=xy((q.x,q.y));C.setFont('Helvetica',max(4.0,min(8.0,scale*1.6)));C.setFillColor(HexColor('#22343c'));C.drawCentredString(x,y,s['id']);e=record['entry_world'];x,y=xy(e);C.setFillColor(HexColor('#087895'));C.circle(x,y,max(1.3,scale*.35),stroke=0,fill=1)
 for r in plan['fixtures']:
  if r['wing']==wing and r['floor']==floor:geometry(r['footprint'],'#74888c','#556b6d',.12)
 for r in commons['instances']:
  if r['wing']==wing and int(r['level'])==lev and r.get('host')is None:geometry(r['footprint'],'#7fa27a','#4c7657',.25)
 for r in commons['pads']:
  if r.get('wing',wing)!=wing:continue
  # Ground C accents only; pad schema is global without floor on the legacy data.
  if wing=='C'and lev==0 and r['zone'].startswith('C-'):geometry(r['geometry'],'#d3e3c8','#86a67b',.15)
 for item in m.get('items',[]):
  if item.get('kind')in ['トイレ','エレベーター','階段']:
   q=item['point'];x,y=xy((q[0]+429,q[1]-46));C.setFont('Helvetica',7);C.setFillColor(HexColor('#9e4036'));C.drawString(x,y,{'トイレ':'WC','エレベーター':'EV','階段':'ST'}[item['kind']])
 if wing in ['A','B']:
  src=read(P/('source/v22/A-continuous-ES.json'if wing=='A'else'source/v15/ES-site-proposal.json'))
  for e in src['escalators']:
   if lev not in e['levels']:continue
   g=rect((e['c'][0],e['c'][2]),e['u'],e['run_m']+3.0,1.9);geometry(g,'#c4d9df','#277188',.5);start=e['test_start'];end=e['test_end'];x0,y0=xy((start[0],start[2]));x1,y1=xy((end[0],end[2]));C.setStrokeColor(HexColor('#17607a'));C.line(x0,y0,x1,y1);text(x0,y0,e['direction'],6)
  for tr in read(P/'source/v22/continuous-transfer-candidates.json'):
   if tr['wing']!=wing or tr['middle_lateral_offset_m']!=0 or abs(tr['points'][0][1]-f['height'])>.01:continue
   C.setStrokeColor(HexColor('#d2782b'));C.setLineWidth(1.3)
   for a,b in zip(tr['points'],tr['points'][1:]):C.line(*xy((a[0],a[2])),*xy((b[0],b[2])))
 # Dimension strings are measured from the drawn final floor plate, in game metres.
 C.setStrokeColor(HexColor('#6a7778'));C.setLineWidth(.4);a=xy((xmin,zmax));b=xy((xmax,zmax));C.line(a[0],110,b[0],110);text((a[0]+b[0])/2-50,90,f'X方向 {xmax-xmin:.2f} m',10);text(60,60,'青丸：実効入口 / 灰：バックヤード / 青灰：什器外接輪郭 / 緑：共用設備 / 橙線：約7.53m連続ES乗継候補',11);text(60,40,'図面の整合性・カプセル検査・自動歩行・人間による実操作は別評価。支持力・基礎・防水・排水・避難容量は未検証。',11);C.showPage()
for wing in ['A','B']:
 src=read(P/('source/v22/A-continuous-ES.json'if wing=='A'else'source/v15/ES-site-proposal.json'));centre=src['centre_world'][0];text(70,1120,f'{wing}館 連続エスカレーター / 投影断面',26);text(70,1080,'1F～RF / 機材の奥行き位置は平面図参照 / 移動処理は既存の連続斜面方式を維持',15)
 sx=50.;sy=44.;ox=840-centre*sx;oy=180
 for lev in [0,1,2,3]:
  y=HEIGHT[lev];C.setFillColor(HexColor('#d0d5d2'))
  for a,b in [(-12,-7.4),(7.4,12)]if lev>0 else[(-12,12)]:C.rect((centre+a)*sx+ox,oy+(y-.38)*sy,(b-a)*sx,.38*sy,fill=1,stroke=0)
  text(100,oy+y*sy,f'{LABEL[lev]} / +{y:.3f}m',15)
 for e in src['escalators']:
  a=e['test_start'];b=e['test_end'];C.setStrokeColor(HexColor('#376b7b'));C.setLineWidth(11);C.line(ox+a[0]*sx,oy+a[1]*sy,ox+b[0]*sx,oy+b[1]*sy);C.setStrokeColor(HexColor('#799d9e'));C.setLineWidth(1.2);C.line(ox+a[0]*sx,oy+(a[1]+1.0)*sy,ox+b[0]*sx,oy+(b[1]+1.0)*sy)
 for dx in [-10.5,10.5]:C.setFillColor(HexColor('#bbc5c2'));C.rect(ox+(centre+dx-.27)*sx,oy,.54*sx,21.2*sy,fill=1,stroke=0)
 text(70,115,'新設地下延伸なし。既存B1の車路・駐車区画は変更していません。',14);text(70,88,'構造計算・基礎・荷重・避難の承認ではありません。RF-SUPPORT-16は未承認を維持。',14);C.showPage()
C.save();print('PDF_DRAWINGS',len(F)+2,'pages')
