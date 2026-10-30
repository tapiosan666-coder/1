from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from v23_blender_common import *
from PIL import Image,ImageDraw,ImageFont
B=json.loads((P/'source/v23/model-bounds.json').read_text());C=json.loads((P/'source/v23/product-catalog.json').read_text());art=P/'assets/v23/art';f='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';bold='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc';im=Image.new('RGB',(1536,768),'#f0e9db');d=ImageDraw.Draw(im);d.rounded_rectangle((28,28,1508,740),30,outline='#274a41',width=5);d.text((75,72),'ALVENE EDIT / COFFEE & BAKES',font=ImageFont.truetype(bold,62),fill='#274a41');d.text((78,160),'焙煎コーヒーと、焼きたての時間。',font=ImageFont.truetype(f,30),fill='#8b6047')
for i,(name,price)in enumerate([('ハンドドリップ','480'),('カフェラテ','560'),('季節のタルト','620'),('ベーカリーセット','880')]):
 y=265+i*90;d.text((88,y),name,font=ImageFont.truetype(f,38),fill='#274a41');d.text((770,y),'¥ '+price,font=ImageFont.truetype(bold,40),fill='#274a41',anchor='ra')
d.ellipse((920,235,1370,660),fill='#d7c5aa');d.ellipse((950,265,1335,625),fill='#fff9ed');d.ellipse((995,305,1295,585),fill='#795640');d.arc((1290,360,1430,520),260,100,fill='#fff9ed',width=36)
for j in range(4):d.arc((1060-j*15,355-j*8,1235+j*10,535+j*8),15,340,fill='#f2dfbd',width=10)
im.save(art/'cafe-menu-original.png',optimize=True);menu=material('V23_original_cafe_menu',(1,1,1),.72,texture='assets/v23/art/cafe-menu-original.png')
def done(name,role):
 bpy.context.view_layer.update();q=[o.matrix_world@Vector(c)for o in bpy.context.scene.objects if o.type in['MESH','CURVE']for c in o.bound_box];lo=[min(p[i]for p in q)for i in range(3)];hi=[max(p[i]for p in q)for i in range(3)];B[name]={'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]]};C[name]={'category':'dining','role':role,'source':'Original Blender v23 and original illustrated menu'};finish(name)
box('Cafe_service_cabinet',(0,0,.44),(2.2,1.0,.88),wood,.025);box('Order_worktop',(0,0,.93),(2.26,1.04,.05),stone,.012)
for x in[-1.08,-.05]:
 for y in[-.48,.40]:box('Pastry_case_frame',(x,y,1.23),(.025,.025,.55),brass,.004)
for z in[1.04,1.26]:box('Empty_pastry_shelf',(-.56,-.025,z),(1.04,.86,.035),white,.007)
box('Pastry_case_top',(-.56,-.025,1.515),(1.10,.92,.035),glass,.007);box('Pastry_front_glass',(-.56,-.49,1.25),(1.08,.012,.48),glass,.002)
for x in[-1.10,-.015]:box('Case_side_glass',(x,-.025,1.25),(.012,.90,.48),glass,.002)
mesh('Mounted_menu_front',[(-.92,-.507,.25),(.92,-.507,.25),(.92,-.507,.79),(-.92,-.507,.79)],[(0,1,2,3)],menu,[(0,0),(1,0),(1,1),(0,1)]);box('POS_terminal',(.65,-.40,1.17),(.32,.10,.27),metal,.015);done('fixture_v23_order_counter','Order/POS, enclosed empty pastry display, mounted menu; merchandise stays independent')
box('Preparation_cabinet',(0,0,.45),(2.1,.9,.9),steel,.018);box('Prep_worktop',(0,0,.94),(2.18,1.0,.06),steel,.012)
for x in[-.65,0,.65]:lathe('Hob',[(0,0),(.17,0),(.17,.02),(0,.02)],metal,(x,0,.98),24)
box('Washable_splashback',(0,.43,1.44),(2.12,.05,1.0),white,.008)
for x in[-1.,1.]:box('Hood_support_post',(x,.38,1.48),(.055,.055,1.08),steel,.008)
box('Supported_extraction_hood',(0,.12,2.0),(2.2,.9,.30),steel,.025);done('fixture_v23_supported_kitchen','Prep/cooking and physically connected hood; full building ventilation design remains pending')
(P/'source/v23/model-bounds.json').write_text(json.dumps(B,indent=2));(P/'source/v23/product-catalog.json').write_text(json.dumps(C,ensure_ascii=False,indent=2))
