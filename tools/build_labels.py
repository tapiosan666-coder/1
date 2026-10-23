"""Original fictional package labels. Optional development tool; Pillow required."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
root=Path(__file__).resolve().parents[1]
font=root/'assets/fonts/NotoSansCJKjp-Regular.otf'
for index,(name,caption,color) in enumerate([('緑茶','GREEN TEA','#315447'),('珈琲','ROASTED COFFEE','#775443'),('小麦粉','FLOUR / 500g','#b09a62'),('牛乳','MILK / 1000ml','#4e788f')]):
 image=Image.new('RGB',(192,160),'#eeeade');d=ImageDraw.Draw(image)
 d.rectangle((0,0,191,22),fill=color);d.rectangle((0,142,191,159),fill=color)
 d.text((96,35),name,font=ImageFont.truetype(str(font),35),fill=color,anchor='mt')
 d.text((96,89),caption,font=ImageFont.truetype(str(font),12),fill='#454d48',anchor='mt')
 d.line((20,113,171,113),fill=color,width=2)
 for x in range(24,168,4):d.rectangle((x,123,x+1+(x%3),135),fill='#3c423d')
 image.save(root/f'assets/products/label{index}.png')
