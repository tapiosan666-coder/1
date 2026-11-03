from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from v25_blender_common import *
from PIL import Image,ImageDraw,ImageFont
B=json.loads((P/'source/v25/model-bounds.json').read_text());C=json.loads((P/'source/v25/product-catalog.json').read_text());cream=material('V25_cream_metal',(.76,.74,.66),.45);cloth=material('V25_cafe_seat_fabric',(.32,.40,.32),.93);glow=material('V25_linear_diffuser',(.9,.85,.72),.4);shader=glow.node_tree.nodes.get('Principled BSDF');shader.inputs['Emission Color'].default_value=(1,.88,.66,1);shader.inputs['Emission Strength'].default_value=1.4

def emit(name,cat):
 bpy.context.view_layer.update();pts=[o.matrix_world@Vector(c)for o in bpy.context.scene.objects if o.type in['MESH','CURVE']for c in o.bound_box];lo=[min(q[i]for q in pts)for i in range(3)];hi=[max(q[i]for q in pts)for i in range(3)];B[name]={'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]]};C[name]={'category':cat,'source':'Original v25 dedicated interior finish and joinery'};finish(name)
box('Cushioned_dining_seat',(0,0,.45),(.47,.47,.11),cloth,.04)
for side in[-1,1]:tube('Curved_side_rail',[(side*.21,.20,.04),(side*.21,.20,.89)],.018,wood)
for j in range(3):tube('Curved_back_slat',[(-.21,.20,.61+j*.10),(0,.25,.63+j*.10),(.21,.20,.61+j*.10)],.018,wood)
for x in[-.19,.19]:tube('Front_leg',[(x,-.20,.03),(x,-.19,.40)],.018,wood)
emit('sku_v25_dining_chair','cafe_seating')
box('Long_book_luminaire',(0,0,0),(3.20,.58,.14),wood,.022)
for y in[-.22,.22]:box('Recessed_book_LED',(0,y,-.078),(3.0,.033,.015),glow,.003)
emit('finish_v25_book_linear','book_ceiling')
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc';brands=[('book','ORIENNE BOOKS',(.12,.19,.16),'BOOKS / MAGAZINES / READING'),('cafe','ALVENE EDIT',(.16,.23,.18),'COFFEE / BAKES / SLOW MOMENTS'),('beauty','VELORIA COLLECTIVE',(.65,.68,.59),'BOTANICAL BEAUTY'),('arcade','TERRUNE PLAY',(.04,.08,.14),'MUSIC / PRIZE / PHOTO')]
for kind,brand,col,subtitle in brands:
 im=Image.new('RGB',(2048,512),tuple(int(x*255)for x in col));d=ImageDraw.Draw(im);size=145
 while ImageFont.truetype(font,size).getlength(brand)>1940:size-=1
 d.text((1024,195),brand,font=ImageFont.truetype(font,size),fill='#f0e7d0',anchor='mm');d.text((1024,385),subtitle,font=ImageFont.truetype(font,53),fill='#e8d6b0',anchor='mm');f=P/f'assets/v25/art/{kind}-fascia.png';im.save(f);mat=material('V25_'+kind+'_graphic',(1,1,1),.62,texture='assets/v25/art/'+f.name);base=material('V25_'+kind+'_brand_enamel',col,.50)
 box('Brand_fascia',(0,0,0),(4.2,.14,.68),base,.04)
 mesh('Original_wordmark',[(-2,-.076,-.31),(2,-.076,-.31),(2,-.076,.31),(-2,-.076,.31)],[(0,1,2,3)],mat,[(0,0),(1,0),(1,1),(0,1)])
 for x in[-2.05,2.05]:tube('Detail_frame',[(x,-.085,-.28),(x,-.085,.28)],.012,brass)
 emit('finish_v25_'+kind+'_fascia','store_brand')
(P/'source/v25/model-bounds.json').write_text(json.dumps(B,indent=2));(P/'source/v25/product-catalog.json').write_text(json.dumps(C,indent=2))
