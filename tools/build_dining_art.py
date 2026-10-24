#!/usr/bin/env python3
"""Original fictional Japanese menus, authored at the actual sign's aspect ratio."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
root=Path(__file__).resolve().parents[1];font=root/'assets/fonts/NotoSansCJKjp-Regular.otf'
image=Image.new('RGB',(4096,184),'#e8e1cf');draw=ImageDraw.Draw(image)
menus=[('麦とだし','うどん・そば',['かけうどん　480円','天ぷらうどん　680円','冷やしそば　580円'],'#476558'),('食堂 まいにち','定食・ごはん',['鶏のから揚げ定食　880円','焼き魚定食　920円','季節の小鉢　180円'],'#886448'),('スパイスの庭','カレーとサラダ',['チキンカレー　780円','野菜カレー　820円','サラダセット　200円'],'#9a7d38'),('こもれび珈琲','珈琲・お茶・軽食',['ブレンド珈琲　420円','アイスティー　380円','焼きたてパン　280円'],'#655347')]
for i,(name,caption,items,color) in enumerate(menus):
 x=i*1024;draw.rectangle((x+5,5,x+1018,178),fill='#f0ece0');draw.rectangle((x+5,5,x+338,178),fill=color)
 draw.text((x+172,45),name,font=ImageFont.truetype(str(font),34),fill='#fff7df',anchor='mt');draw.text((x+172,99),caption,font=ImageFont.truetype(str(font),20),fill='#fff7df',anchor='mt')
 for j,item in enumerate(items):draw.text((x+365,20+j*43),item,font=ImageFont.truetype(str(font),25),fill='#354540')
 draw.text((x+990,154),'税込 / お会計は各店舗へ',font=ImageFont.truetype(str(font),14),fill=color,anchor='rt')
 # Small drawn dish icons, never a photograph or copied tenant mark.
 cx=x+891
 if i==3:
  draw.ellipse((cx-55,115,cx+60,138),fill='#c7b99d');draw.rounded_rectangle((cx-43,44,cx+37,121),radius=15,fill='#ddd3bc');draw.ellipse((cx-40,36,cx+37,68),fill='#40352c');draw.arc((cx+19,60,cx+63,101),-90,90,fill='#ddd3bc',width=9)
 elif i==2:
  draw.ellipse((cx-79,40,cx+79,130),fill='#d7cab1');draw.ellipse((cx-61,53,cx+10,113),fill='#f8eed1');draw.ellipse((cx-10,49,cx+62,118),fill='#a46b2d')
  for dx,dy in [(17,65),(40,85),(6,98)]:draw.ellipse((cx+dx-5,dy-4,cx+dx+5,dy+4),fill='#7c9c52')
 elif i==1:
  draw.rounded_rectangle((cx-80,36,cx+80,133),radius=12,fill='#cbbfa4')
  for dx,dy in [(-47,58),(-20,80),(5,62),(-45,95)]:draw.ellipse((cx+dx-15,dy-12,cx+dx+15,dy+12),fill='#ae7b3d')
  draw.ellipse((cx+17,75,cx+67,122),fill='#f4eacb')
 else:
  draw.ellipse((cx-72,35,cx+72,135),fill='#d3c3a3');draw.ellipse((cx-62,42,cx+62,103),fill='#7b6743')
  for j in range(5):draw.arc((cx-40+j*5,47,cx+37+j*3,91),0,170,fill='#ede3bd',width=3)
out=root/'assets/dining';out.mkdir(parents=True,exist_ok=True);image.save(out/'menus.png');print('menus.png',image.size,(out/'menus.png').stat().st_size)
