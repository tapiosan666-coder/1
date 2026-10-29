from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];im=Image.new('RGBA',(3072,256),(0,0,0,0));d=ImageDraw.Draw(im);c='#e9f0ec';font='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
for i,kind in enumerate(['WC','EV','ES','ST','INFO','FOOD','DINING','CINEMA','ARCADE','PARK','A','B','C','EXIT']):
 x=i*192+24
 if kind=='WC':
  for dx in[40,108]:d.ellipse((x+dx-12,28,x+dx+12,52),fill=c);d.line((x+dx,63,x+dx,145),fill=c,width=16);d.line((x+dx,88,x+dx-23,118),fill=c,width=10);d.line((x+dx,88,x+dx+23,118),fill=c,width=10);d.line((x+dx,144,x+dx-16,198),fill=c,width=10);d.line((x+dx,144,x+dx+16,198),fill=c,width=10)
 elif kind=='EV':d.rounded_rectangle((x+18,58,x+135,205),radius=9,outline=c,width=9);d.ellipse((x+61,84,x+86,109),fill=c);d.line((x+73,116,x+73,179),fill=c,width=17);d.line((x+28,35,x+52,12,x+76,35),fill=c,width=8);d.line((x+96,12,x+120,35,x+144,12),fill=c,width=8)
 elif kind in['ES','ST']:
  pts=[(x+14,200),(x+52,200),(x+52,162),(x+90,162),(x+90,124),(x+128,124),(x+128,86),(x+158,86)]if kind=='ST'else[(x+12,195),(x+50,195),(x+133,91),(x+164,91)]
  d.line(pts,fill=c,width=12);d.ellipse((x+81,45,x+107,71),fill=c);d.line((x+94,81,x+94,135),fill=c,width=16)
 elif kind=='INFO':d.ellipse((x+8,25,x+163,214),outline=c,width=10);d.ellipse((x+71,58,x+98,85),fill=c);d.rectangle((x+73,101,x+95,174),fill=c)
 elif kind=='FOOD':d.rounded_rectangle((x+28,76,x+148,200),radius=6,outline=c,width=9);d.arc((x+55,28,x+120,115),180,360,fill=c,width=9);d.ellipse((x+69,115,x+109,168),outline=c,width=8)
 elif kind=='DINING':
  for off in[34,55,76]:d.line((x+off,30,x+off,100),fill=c,width=8)
  d.line((x+34,100,x+76,100),fill=c,width=10);d.line((x+55,100,x+55,210),fill=c,width=10);d.line((x+128,30,x+128,210),fill=c,width=10);d.rectangle((x+112,30,x+127,125),fill=c)
 elif kind=='CINEMA':d.rounded_rectangle((x+10,42,x+164,192),radius=8,outline=c,width=10);d.rectangle((x+30,74,x+144,162),outline=c,width=6)
 elif kind=='ARCADE':d.rounded_rectangle((x+12,85,x+162,172),radius=25,outline=c,width=10);d.line((x+42,107,x+42,147),fill=c,width=8);d.line((x+24,127,x+62,127),fill=c,width=8);d.ellipse((x+115,106,x+131,122),fill=c);d.ellipse((x+135,134,x+151,150),fill=c)
 else:d.text((x+85,122),('P' if kind=='PARK' else kind) if kind!='EXIT'else'→',font=ImageFont.truetype(font,145),fill=c,anchor='mm')
im.save(P/'assets/v21/art/wayfinding-icons.png',optimize=True)
