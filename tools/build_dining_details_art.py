#!/usr/bin/env python3
"""Original Japanese counter signs/screens; no commercial artwork or photographs."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
root=Path(__file__).resolve().parents[1]
font=root/'assets/fonts/NotoSansCJKjp-Regular.otf'
img=Image.new('RGB',(2048,1024),'#e7e1d2');d=ImageDraw.Draw(img)
F=lambda size:ImageFont.truetype(str(font),size)
brands=[('麦とだし','うどん・そば','#466457'),('食堂 まいにち','定食・ごはん','#886448'),('スパイスの庭','カレーとサラダ','#927c37'),('こもれび珈琲','珈琲・軽食','#655347')]
for i,(name,caption,color) in enumerate(brands):
 y=i*256
 d.rectangle((0,y,511,y+255),fill=color)
 d.text((256,y+74),name,font=F(51),fill='#fff6df',anchor='mt')
 d.text((256,y+155),caption,font=F(28),fill='#efe2c4',anchor='mt')
 # Customer-facing till display, restrained information rather than UI jargon.
 d.rectangle((512,y,1023,y+255),fill='#203f3b')
 d.text((768,y+30),'お会計',font=F(31),fill='#d9e8dc',anchor='mt')
 d.text((980,y+103),['680','880','780','420'][i]+' 円',font=F(54),fill='#fff8df',anchor='rt')
 d.line((545,y+174,990,y+174),fill='#759286',width=2)
 d.text((768,y+195),'各種キャッシュレス決済',font=F(20),fill='#bcd1c2',anchor='mt')
 d.rectangle((1024,y,1535,y+255),fill='#e9e3d1')
 d.text((1280,y+50),'お渡し口',font=F(53),fill=color,anchor='mt')
 d.text((1280,y+145),'番号をお呼びします',font=F(27),fill='#4a544c',anchor='mt')
 d.rectangle((1536,y,2047,y+255),fill='#e9e3d1')
 d.text((1792,y+50),'お箸・調味料',font=F(45),fill=color,anchor='mt')
 d.text((1792,y+145),'ご自由にお取りください',font=F(24),fill='#4a544c',anchor='mt')
path=root/'assets/dining/counter_details.png';path.parent.mkdir(parents=True,exist_ok=True);img.save(path)
print(path.relative_to(root),img.size,path.stat().st_size)
