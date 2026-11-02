from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from v24_blender_common import *
from PIL import Image,ImageDraw,ImageFont
A=P/'assets/v24/art';im=Image.new('RGB',(768,320),'#25372e');d=ImageDraw.Draw(im);font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';d.text((30,24),'COFFEE & BAKES',font=ImageFont.truetype(font,46),fill='#eadbc2');d.line((30,89,738,89),fill='#b89b64',width=2)
for i,t in enumerate(['本日のコーヒー  ¥420','カフェラテ       ¥480','焼きたてのパン  ¥280']):d.text((34,117+i*54),t,font=ImageFont.truetype(font,32),fill='#eadbc2')
file=A/'coffee-menu.png';im.save(file);menu=material('Original_coffee_menu',(1,1,1),.75,texture='assets/v24/art/coffee-menu.png');green=material('Cafe_sage_enamel',(.10,.18,.13),.47);black=material('Coffee_machine_body',(.018,.022,.023),.31,.5)
# Identical maximum footprint to the replaced legacy kitchen; all functional elements inside it.
box('Recessed_plinth',(0,.06,.05),(2.12,.72,.10),metal,.012)
box('Front_cabinet',(0,.06,.49),(2.12,.72,.82),green,.018)
for x in[-.92,-.60,-.28,.04,.36,.68,.94]:box('Oak_flute',(x,-.311,.48),(.027,.015,.73),wood,.003)
box('Stone_bar',(0,.07,.94),(2.2,.80,.07),stone,.012)
for x in[-.55,.55]:
 box('Staff_storage_door',(x,.428,.49),(1.02,.025,.68),green,.009);tube('Storage_handle',[(x-.15,.45,.70),(x+.15,.45,.70)],.009,brass)
# Espresso machine with rounded housing, buttons, portafilters, steam wand and drip grid.
box('Machine_base',(.18,.13,1.01),(.72,.48,.065),steel,.018);box('Espresso_housing',(.18,.26,1.24),(.72,.26,.45),black,.045)
box('Cup_warmer',(.18,.26,1.47),(.75,.29,.035),steel,.009)
for x in[-.01,.37]:
 box('Brew_head',(x,.06,1.30),(.17,.13,.09),steel,.02);tube('Portafilter',[(x,.025,1.25),(x,-.15,1.25)],.018,black)
 for k in range(3):lathe('Control_button',[(.012,0),(.012,.008)],brass,(x-.04+k*.04,.11,1.40),16)
for x in[-.09,.08,.25,.42]:box('Drip_slot',(x,-.02,1.049),(.008,.28,.005),black,.001)
tube('Steam_wand',[(.51,.13,1.32),(.57,.04,1.24),(.55,-.02,1.12)],.009,steel)
# Pastry display: transparent front and curved end pane, two supported shelves.
for z in[1.01,1.23]:box('Pastry_tray',(-.69,.05,z),(.54,.49,.025),wood,.008)
box('Display_front_glass',(-.69,-.20,1.24),(.59,.012,.49),glass,.002)
for x in[-.985,-.395]:box('Display_side_glass',(x,.04,1.24),(.012,.48,.49),glass,.002)
box('Display_roof',(-.69,.04,1.495),(.61,.49,.025),brass,.006)
for z in[1.04,1.26]:
 for x in[-.83,-.60]:
  lathe('Baked_roll',[(0,0),(.065,0),(.075,.025),(.055,.06),(0,.075)],pastry,(x,.04,z),24)
# Menuboard is physically supported by two rear posts, not a floating screen.
for x in[-.96,.96]:tube('Menu_upright',[(x,.42,.97),(x,.42,2.12)],.014,metal)
box('Menu_frame',(0,.42,1.96),(2.12,.055,.39),green,.013)
mesh('Printed_menu',[(-1.02,.387,1.78),(1.02,.387,1.78),(1.02,.387,2.135),(-1.02,.387,2.135)],[(0,1,2,3)],menu,[(0,0),(1,0),(1,1),(0,1)])
name='fixture_v24_coffee_station';bpy.context.view_layer.update();pts=[o.matrix_world@Vector(c)for o in bpy.context.scene.objects if o.type in['MESH','CURVE']for c in o.bound_box];lo=[min(q[i]for q in pts)for i in range(3)];hi=[max(q[i]for q in pts)for i in range(3)];B=json.loads((P/'source/v24/model-bounds.json').read_text());B[name]={'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]]};C=json.loads((P/'source/v24/product-catalog.json').read_text());C[name]={'category':'cafe_service_station','source':'Original Blender dedicated cabinet, espresso machine, glass pastry case and Japanese menu, same legacy kitchen envelope'};finish(name);(P/'source/v24/model-bounds.json').write_text(json.dumps(B,indent=2));(P/'source/v24/product-catalog.json').write_text(json.dumps(C,ensure_ascii=False,indent=2))
