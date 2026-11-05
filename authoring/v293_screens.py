"""Original fictional device demonstration interfaces. No external photos or software screenshots."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];O=P/'assets/v293/art';O.mkdir(exist_ok=True)
def font(n):return ImageFont.truetype(str(P/'assets/NotoSansCJKjp-Regular.otf'),n)
for kind,size in [('desktop',(1200,760)),('tablet',(768,1024)),('mobile',(512,1024)),('tv',(1280,720))]:
 w,h=size;im=Image.new('RGB',size,'#102d3b');d=ImageDraw.Draw(im)
 for y in range(h):d.line((0,y,w,y),fill=(16+int(y/h*22),45+int(y/h*28),59+int(y/h*24)))
 if kind=='tv':
  d.ellipse((850,70,1020,240),fill='#eed3a1');d.polygon([(0,570),(400,170),(770,570)],fill='#315f70');d.polygon([(380,610),(810,245),(1280,615)],fill='#497b81');d.rectangle((0,605,w,h),fill='#183f50');d.text((55,35),'SUVEL  /  DISPLAY DEMO',font=font(32),fill='#f3ede0');d.text((55,645),'色彩とディテールを、その目で。',font=font(25),fill='#e9e5d6')
 elif kind=='mobile':
  d.text((35,80),'12:30',font=font(100),fill='white');d.text((40,208),'SUVEL  /  TODAY',font=font(22),fill='#a1c9cd')
  for i,label in enumerate(['天気','写真','地図','音楽','予定','メモ']):
   x=35+(i%3)*160;y=380+(i//3)*190;d.rounded_rectangle((x,y,x+115,y+115),22,fill=['#e1ac6a','#91b2b6','#e7dbbc'][i%3]);d.ellipse((x+31,y+31,x+84,y+84),outline='#244c5c',width=7);d.text((x+18,y+125),label,font=font(23),fill='white')
  d.rounded_rectangle((45,900,467,970),28,fill='#446671');d.line((185,996,325,996),fill='#f5ebd8',width=5)
 else:
  d.rounded_rectangle((35,38,w-35,h-38),20,fill='#f2f0e6');d.rectangle((35,38,w-35,112),fill='#244d59');d.text((63,55),'SUVEL  WORKSPACE',font=font(27 if kind=='desktop'else 22),fill='white')
  for i in range(3):d.ellipse((w-150+i*31,67,w-136+i*31,81),fill='#c6d1c5')
  d.text((65,147),'今日のアイデアを、形に。',font=font(40 if kind=='desktop'else 31),fill='#203d48');d.text((66,211),'NOTES  /  DESIGN  /  MEDIA',font=font(21),fill='#657f80')
  count=3 if kind=='desktop'else 2;cw=(w-150)/count
  for i,label in enumerate(['暮らしの記録','新しいプロジェクト','おすすめの音楽'][:count]):
   x=65+i*cw;y=290;d.rounded_rectangle((x,y,x+cw-25,y+210),12,fill=['#d5ba90','#a8c4be','#9db1c3'][i]);d.ellipse((x+35,y+40,x+105,y+110),fill='#f5eee2');d.line((x+22,y+170,x+cw-50,y+170),fill='#41646d',width=5);d.text((x+8,y+230),label,font=font(22),fill='#294955')
  d.text((65,h-113),'あなたの毎日を、もっと自由に。',font=font(23),fill='#5c7375')
 im.save(O/(kind+'-demo.png'))
