from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from v23_blender_common import *
from PIL import Image,ImageDraw,ImageFont
B=json.loads((P/'source/v23/model-bounds.json').read_text());C=json.loads((P/'source/v23/product-catalog.json').read_text());art=P/'assets/v23/art';font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';bold='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc';a=['旅の余白','暮らしの設計','季節の料理','夜明けの物語','子どもの図鑑','写真と光','街の音楽','小さな庭'];b=['道の向こうへ','道具と暮らす','旬の食卓','星の記憶','いきものと空','光を写す','リズムの記憶','四季の手入れ'];col=['#3c6b73','#ab714c','#72814c','#725369','#c59b4d','#3c4d6c','#8a5146','#436953'];im=Image.new('RGB',(2048,512),'#f2eddf');d=ImageDraw.Draw(im)
for k,title in enumerate(b):
 x=k*256;d.rectangle((x+3,3,x+252,509),fill='#eee7d6');d.rectangle((x+3,3,x+252,77),fill=col[k]);d.text((x+25,22),'VOLUME / %02d'%k,font=ImageFont.truetype(bold,19),fill='#f4ecd8');
 for j in range(5):d.arc((x+26+j*7,125+j*11,x+230-j*9,330+j*13),20+j*16,290,fill=col[k],width=6)
 d.text((x+128,394),title,font=ImageFont.truetype(bold,23),fill=col[k],anchor='mm');d.text((x+128,466),'ORIGINAL / READING ROOM',font=ImageFont.truetype(font,12),fill=col[k],anchor='mm')
im.save(art/'book-companion-original.png',optimize=True);sp=Image.new('RGB',(512,512));d=ImageDraw.Draw(sp)
for k,title in enumerate(a+b):
 x=k*32;d.rectangle((x,0,x+31,511),fill=col[k%8]);d.rectangle((x,12,x+31,52),fill='#eee5d0');d.text((x+16,31),'FY',font=ImageFont.truetype(bold,16),fill=col[k%8],anchor='mm')
 for j,ch in enumerate(title):d.text((x+16,102+j*35),ch,font=ImageFont.truetype(bold,25),fill='#f4e8d4',anchor='mm')
 d.text((x+16,458),'%02d'%k,font=ImageFont.truetype(font,18),fill='#e6d3ab',anchor='mm')
sp.save(art/'book-spines-original.png',optimize=True);primary=material('V23_original_editorial',(1,1,1),.63,texture='assets/v23/art/retail-editorial-atlas.png');companion=material('V23_original_companions',(1,1,1),.63,texture='assets/v23/art/book-companion-original.png');spine=material('V23_printed_genre_spines',(1,1,1),.67,texture='assets/v23/art/book-spines-original.png')
for variant in[0,1]:
 for k in range(8):
  w=[.105,.145,.19,.22,.15,.13,.18,.16][k]*(1.07 if variant else 1);h=[.17,.215,.265,.29,.20,.19,.24,.23][k]*(.96 if variant else 1);t=[.020,.031,.015,.023,.038,.018,.027,.022][k]*(1.12 if variant else 1);box('Paper_block',(0,0,h/2),(w-.004,t-.004,h-.008),paper,.0007)
  for y in[-t/2,t/2]:box('Cover_board',(0,y,h/2),(w,.0015,h),white,.0005)
  u=k/8;v=0 if variant else.75;uv=[(u,v),(u+.125,v),(u+.125,v+ (1 if variant else .25)),(u,v+(1 if variant else .25))];mesh('Editorial_cover',[(-w/2,-t/2-.001,0),(w/2,-t/2-.001,0),(w/2,-t/2-.001,h),(-w/2,-t/2-.001,h)],[(0,1,2,3)],companion if variant else primary,uv)
  ix=k+variant*8;u=ix/16;mesh('Printed_spine',[(-w/2-.001,-t/2,0),(-w/2-.001,t/2,0),(-w/2-.001,t/2,h),(-w/2-.001,-t/2,h)],[(0,3,2,1)],spine,[(u,0),(u+.0625,0),(u+.0625,1),(u,1)])
  name='sku_v23_book_'+str(k)+('_B'if variant else'');bpy.context.view_layer.update();pts=[o.matrix_world@Vector(c)for o in bpy.context.scene.objects if o.type=='MESH'for c in o.bound_box];lo=[min(q[i]for q in pts)for i in range(3)];hi=[max(q[i]for q in pts)for i in range(3)];B[name]={'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]]};C[name]={'category':'book','genre':['旅・紀行','デザイン・住まい','料理・暮らし','小説・文芸','こども・図鑑','写真・アート','音楽・カルチャー','ガーデニング'][k],'title':(b if variant else a)[k],'source':'Original v23 geometry, cover illustration and printed Japanese spine'};finish(name)
(P/'source/v23/model-bounds.json').write_text(json.dumps(B,indent=2));(P/'source/v23/product-catalog.json').write_text(json.dumps(C,ensure_ascii=False,indent=2))
