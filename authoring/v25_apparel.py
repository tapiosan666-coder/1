from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from v25_blender_common import *
from PIL import Image,ImageDraw,ImageFont
B=json.loads((P/'source/v25/model-bounds.json').read_text())if(P/'source/v25/model-bounds.json').exists()else{};C=json.loads((P/'source/v25/product-catalog.json').read_text())if(P/'source/v25/product-catalog.json').exists()else{};ivory=material('V25_limewash',(.73,.70,.62),.86);green=material('V25_spruce',(.065,.15,.12),.55);fabric=material('V25_upholstery',(.46,.43,.34),.93);clay=material('V25_clay_display',(.67,.60,.48),.68)
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';bold='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc';im=Image.new('RGB',(2048,512),'#213e32');d=ImageDraw.Draw(im);d.text((1024,190),'FERNELL WORKS',font=ImageFont.truetype(bold,150),fill='#efe4cc',anchor='mm');d.text((1024,380),'AUTUMN ATELIER  /  暮らしに馴染む一着',font=ImageFont.truetype(font,55),fill='#ceba91',anchor='mm');im.save(P/'assets/v25/art/fernell-wordmark.png');logo=material('V25_original_brand',(1,1,1),.7,texture='assets/v25/art/fernell-wordmark.png')
def emit(name,cat):
 bpy.context.view_layer.update();pts=[o.matrix_world@Vector(c)for o in bpy.context.scene.objects if o.type in['MESH','CURVE']for c in o.bound_box];lo=[min(q[i]for q in pts)for i in range(3)];hi=[max(q[i]for q in pts)for i in range(3)];B[name]={'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]]};C[name]={'category':cat,'source':'Original Blender dedicated retail joinery, profiles, shaped garments, brand artwork; inherited CC0 wood and Noto OFL'};finish(name)
def panel_text(x,y,z,w,h):mesh('Printed_brand',[(x-w/2,y,z-h/2),(x+w/2,y,z-h/2),(x+w/2,y,z+h/2),(x-w/2,y,z+h/2)],[(0,1,2,3)],logo,[(0,0),(1,0),(1,1),(0,1)])
# Rail with a supported cornice, backed wardrobe and the same1.70m working bar/footprint as v24.
for variant in['wardrobe','gallery_rail']:
 if variant=='wardrobe':
  box('Wardrobe_back',(0,.265,1.42),(1.83,.055,2.78),green,.015)
  for x in[-.885,.885]:box('Oak_stile',(x,0,1.42),(.055,.58,2.78),wood,.009)
  for z in[.045,2.21,2.77]:box('Shelf_and_cornice',(0,0,z),(1.83,.58,.045),wood,.009)
  for x in[-.64,0,.64]:box('Folded_knit_stock',(x,0,2.29),(.32,.28,.10),fabrics[1],.025)
 else:
  for x in[-.86,.86]:
   box('Cast_foot',(x,0,.025),(.12,.58,.05),metal,.018);tube('Looped_end',[(x,-.24,.05),(x,-.24,1.58),(x,0,1.70),(x,.24,1.58),(x,.24,.05)],.018,brass)
 tube('Working_rail',[(-.90,0,1.70),(.90,0,1.70)],.021,brass)
 if variant=='wardrobe':panel_text(0,-.296,2.50,1.48,.34)
 emit('fixture_v25_'+variant,'apparel_hanging_fixture')
# Tall bag gallery retains old shelf elevations and floor envelope.
box('Recessed_base',(0,.01,.055),(1.94,.61,.11),green,.025);box('Oak_back',(0,.28,1.37),(1.98,.06,2.70),wood,.01)
for z in[.4825,1.1325,1.7825,2.23]:
 box('Shelf',(0,-.02,z),(1.94,.59,.035),ivory,.01)
 for x in[-.83,.83]:tube('Brass_bracket',[(x,.25,z-.14),(x,-.20,z-.025)],.009,brass)
box('Brand_header',(0,.03,2.57),(1.96,.55,.30),green,.012);panel_text(0,-.251,2.57,1.65,.27);emit('fixture_v25_bag_gallery','apparel_accessories')
# Sculpted nested display with correct retained support heights.
for x,y,w,l,z in[(-.2,0,1.8,.75,.825),(.63,-.04,.80,.72,.525)]:
 for a in[-1,1]:
  for b in[-1,1]:tube('Tapered_leg',[(x+a*(w/2-.10),y+b*(l/2-.10),.035),(x+a*(w/2-.16),y+b*(l/2-.16),z-.05)],.024,wood)
 box('Rounded_solid_surface',(x,y,z-.02),(w,l,.04),stone,.018)
emit('fixture_v25_nested_atelier','apparel_display')
# Dedicated cashier: softened stone top, fluted front, existing1.0x.475 envelope.
box('Plinth',(0,0,.05),(1.93,.86,.10),green,.02);box('Cabinet',(0,.01,.46),(1.93,.86,.80),wood,.025)
for x in[-.86+i*.10 for i in range(18)]:box('Front_reed',(x,-.429,.46),(.027,.022,.72),brass,.004)
box('Stone_counter',(0,0,.9200),(1.98,.94,.055),stone,.015)
box('POS_base',(.48,.04,.976),(.29,.25,.055),metal,.012)
box('POS_stem',(.48,.10,1.08),(.045,.045,.20),brass,.007)
box('Touch_display',(.48,.09,1.21),(.31,.045,.23),metal,.016)
box('Receipt_printer',(.05,.07,1.015),(.21,.23,.13),ivory,.015)
emit('fixture_v25_atelier_checkout','checkout')
# Suspended acoustic rafts, recessed perimeter light and detailed slats; supports generated against actual ceiling.
led=material('V25_LED_diffuser',(.85,.77,.61),.4);node=led.node_tree.nodes.get('Principled BSDF');node.inputs['Emission Color'].default_value=(1,.83,.59,1);node.inputs['Emission Strength'].default_value=1.6
box('Acoustic_raft',(0,0,0),(3.3,2.5,.12),ivory,.035)
for side in[-1,1]:box('Recessed_LED',(0,side*1.19,-.065),(3.08,.027,.013),led,.004)
for x in[-1.4+i*.28 for i in range(11)]:box('Solid_oak_slat',(x,0,-.10),(.055,2.30,.09),wood,.006)
emit('finish_v25_raft','supported_ceiling_finish')
# Entry sign: suspended from verified roof, all material above head height.
box('Double_face_fascia',(0,0,0),(5.2,.15,.85),green,.04);panel_text(0,-.079,0,4.9,.76)
for x in[-2.55,2.55]:tube('Champagne_frame',[(x,-.09,-.38),(x,-.09,.38)],.012,brass)
emit('finish_v25_fernell_fascia','brand_fascia')
(P/'source/v25/model-bounds.json').write_text(json.dumps(B,indent=2));(P/'source/v25/product-catalog.json').write_text(json.dumps(C,indent=2));print('V25_APPAREL_ASSETS',len(B))
