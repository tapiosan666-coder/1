"""Original fictional covers; Pillow is only needed to regenerate these assets."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
r=Path(__file__).resolve().parents[1]; f=r/'assets/fonts/NotoSansCJKjp-Regular.otf'
books=[('余白の街','#4b686c'),('遠い日曜日','#a87860'),('光のかたち','#737d61'),('季節を編む','#9a8969'),('静かな窓','#717488'),('歩く時間','#9b746f')]
for i,(title,c) in enumerate(books):
 im=Image.new('RGB',(256,360),'#eee8d8');d=ImageDraw.Draw(im)
 d.rectangle((0,0,255,22),fill=c);d.rectangle((0,235,255,359),fill=c)
 d.ellipse((72,91,184,203),fill=c);d.rectangle((32,167+i*4,224,208+i*4),fill='#c6bfa8')
 d.text((128,42),title,font=ImageFont.truetype(str(f),31),anchor='mt',fill='#303a3a')
 d.text((128,266),'紙とことば文庫',font=ImageFont.truetype(str(f),17),anchor='mt',fill='#f8f1e1')
 d.text((128,308),'FICTION / ESSAYS',font=ImageFont.truetype(str(f),13),anchor='mt',fill='#f8f1e1')
 im.save(r/f'assets/books/cover{i}.png')
