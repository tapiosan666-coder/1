"""Illustrated link identification printed on a two-sided suspended plate."""
import json
from pathlib import Path
from PIL import Image, ImageFont, ImageDraw
root=Path(__file__).resolve().parents[2]
rows=json.load(open(root/'source/v32/map-data.json'))
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
bold='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
def label(d,xy,txt,size,fill,strong=False):
 d.text(xy,txt,fill=fill,font=ImageFont.truetype(bold if strong else font,size,index=0))
for pair in ('AB','BC'):
 for floor in ('1F','2F'):
  im=Image.new('RGB',(1152,224),'#243b40')
  d=ImageDraw.Draw(im)
  c={'A':'#e7bc75','B':'#a5ca9f','C':'#85bcc1'}
  label(d,(44,11),f'{pair[0]}館・{pair[1]}館  連絡通路',70,'#fcf5df',True)
  label(d,(46,128),f'{floor}   /   {pair[0]}–{pair[1]}  CONNECTING GALLERY',32,'#ddd9c6')
  d.line((41,199,785,199),fill='#948b72',width=3)
  # Real outlines for the corresponding level. Drawing changes with the actual source floor.
  for row in rows:
   if row.get('wing') not in c or row['label']!=floor:continue
   col=c[row['wing']] if row['wing'] in pair else '#50646a'
   for poly in row['floor']:
    if not poly:continue
    for i,ring in enumerate(poly):
     d.polygon([(int(818+(x+750)*.325),int(5+(z+374)*.325)) for x,z in ring],fill=col if i==0 else '#243b40')
  im.resize((864,168),Image.Resampling.LANCZOS).save(root/f'assets/v36/commons/link-{pair}-{floor}.webp',quality=94)
