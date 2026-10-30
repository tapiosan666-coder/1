"""Original genre collections; different formats and printed covers/spines, no borrowed titles/art."""
from pathlib import Path
import sys,json,math
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from v24_blender_common import *
B=json.loads((P/'source/v24/model-bounds.json').read_text());C=json.loads((P/'source/v24/product-catalog.json').read_text());A=P/'assets/v24/art';font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';bold='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
genres=[('旅・紀行',['旅先の窓','まちを巡る','路地の記憶','地図のつづき']),('住まい・デザイン',['住まいの輪郭','暮らしの余白','光を編む部屋','道具とともに']),('料理・暮らし',['週末の食卓','ひと皿の季節','台所の手帖','おやつの日々']),('小説・文芸',['風待ちの午後','月と小さな駅','夜明けの喫茶店','雨色の手紙']),('こども・図鑑',['もりのいちにち','ふしぎなたび','はじめてのずかん','いろとかたち']),('写真・アート',['ひかりの断片','空間の記憶','色をあるく','静かな風景']),('音楽・カルチャー',['街の音を集めて','リズムの地図','小さな音楽室','音のある暮らし']),('園芸・自然',['小さな緑の手帖','庭に吹く風','植物と暮らす','葉のしるし'])]
cols=['#38615c','#946c47','#b36a51','#4e586e','#75915e','#687f8a','#75617a','#56745d']
for genre,(label,titles)in enumerate(genres):
 for variant,title in enumerate(titles):
  w=[.145,.185,.17,.132,.19,.21,.16,.17][genre];h=[.215,.25,.235,.195,.24,.27,.225,.235][genre];depth=.018+variant*.004;image=Image.new('RGB',(320,480),'#eee8d9');draw=ImageDraw.Draw(image);col=cols[genre];draw.rectangle((0,0,319,79),fill=col);draw.text((24,28),f'FY EDITIONS  /  {genre+1:02d}',font=ImageFont.truetype(bold,16),fill='#f6eddb')
  for k in range(6):
   if variant==0:draw.arc((40+k*8,120+k*9,280-k*6,325+k*4),15,290,fill=col,width=3)
   elif variant==1:draw.rectangle((40+k*28,110+k*13,130+k*23,300+k*11),outline=col,width=3)
   elif variant==2:draw.line((40,135+k*24,275,300-k*13),fill=col,width=4)
   else:draw.ellipse((40+k*13,110+k*21,275-k*11,280+k*12),outline=col,width=3)
  size=30
  while ImageFont.truetype(bold,size).getlength(title)>280:size-=1
  draw.text((160,365),title,font=ImageFont.truetype(bold,size),fill=col,anchor='mm');draw.text((160,426),label,font=ImageFont.truetype(font,18),fill=col,anchor='mm');file=A/f'book-{genre}-{variant}-cover.png';image.save(file,optimize=True)
  spine=Image.new('RGB',(64,480),col);dr=ImageDraw.Draw(spine);dr.text((32,30),f'{variant+1:02d}',font=ImageFont.truetype(bold,20),fill='#f6eddd',anchor='mm');y=90
  for char in title:dr.text((32,y),char,font=ImageFont.truetype(bold,25),fill='#f8efdf',anchor='mm');y+=29
  dr.line((12,442,52,442),fill='#d0bc8a',width=3);spine.save(A/f'book-{genre}-{variant}-spine.png',optimize=True)
  cover=material(f'V24_book_cover_{genre}_{variant}',(1,1,1),.62,texture=f'assets/v24/art/{file.name}');sp=material(f'V24_book_spine_{genre}_{variant}',(1,1,1),.65,texture=f'assets/v24/art/book-{genre}-{variant}-spine.png')
  box('Page_block',(0,0,h/2),(w-.006,depth-.004,h-.006),paper,.002)
  edge_colour=tuple(int(col[j:j+2],16)/255 for j in[1,3,5]);binding=material(f'Printed_binding_{genre}_{variant}',edge_colour,.72)
  for side in[-1,1]:box('Hard_cover',(0,side*depth/2,h/2),(w,.0028,h),binding,.0015)
  mesh('Printed_cover',[(-w/2,-depth/2-.0016,0),(w/2,-depth/2-.0016,0),(w/2,-depth/2-.0016,h),(-w/2,-depth/2-.0016,h)],[(0,1,2,3)],cover,[(0,0),(1,0),(1,1),(0,1)])
  mesh('Printed_spine',[(-w/2-.0004,depth/2,0),(-w/2-.0004,-depth/2,0),(-w/2-.0004,-depth/2,h),(-w/2-.0004,depth/2,h)],[(0,1,2,3)],sp,[(0,0),(1,0),(1,1),(0,1)])
  name=f'sku_v24_book_{genre}_{variant}';bpy.context.view_layer.update();points=[o.matrix_world@Vector(c)for o in bpy.context.scene.objects if o.type in['MESH','CURVE']for c in o.bound_box];lo=[min(q[i]for q in points)for i in range(3)];hi=[max(q[i]for q in points)for i in range(3)];B[name]={'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]]};C[name]={'category':'book','genre':label,'title':title,'source':'Original v24 printed covers and spines, multiple book formats; cover variants are not claimed independent shape designs'};finish(name)
(P/'source/v24/model-bounds.json').write_text(json.dumps(B,indent=2));(P/'source/v24/product-catalog.json').write_text(json.dumps(C,ensure_ascii=False,indent=2));print('V24_GENRE_BOOKS',32)
