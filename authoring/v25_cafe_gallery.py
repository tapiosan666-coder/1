from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];A=P/'assets/v25/art';F='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
for k in range(3):
 im=Image.new('RGB',(512,768),['#e6ddc9','#244336','#ccb994'][k]);d=ImageDraw.Draw(im);ink=['#244336','#efe5cf','#294538'][k]
 def text(t,y,size=25):d.text((256,y),t,font=ImageFont.truetype(F,size),fill=ink,anchor='mm')
 text('ALVENE / COFFEE & BAKES',57,24);d.line((36,95,476,95),fill=ink,width=2)
 if k==0:
  text('BREWED SLOWLY',161,33);d.ellipse((138,267,354,479),outline=ink,width=9);d.ellipse((160,290,333,459),fill='#79543b');d.arc((309,303,411,415),270,90,fill=ink,width=13);d.arc((111,427,387,511),0,180,fill=ink,width=7);text('香りから、ひと休み。',608,29)
 elif k==1:
  text('SEASONAL MENU',160,32)
  for t,y in[('HAND DRIP COFFEE',252),('CAFE LATTE',337),('TEA / HERBAL',422),('BAKED THIS MORNING',507)]:text(t,y,23)
  text('本日の焼き菓子はカウンターへ',628,23)
 else:
  text('BAKED THIS MORNING',160,27);hero=Image.open(P/'assets/v24/art/product-portrait-food.png').convert('RGBA');hero.thumbnail((450,370));im.paste(hero,((512-hero.width)//2,220),hero);text('ひと口の、しあわせ。',625,28)
 text('ORIGINAL / FIND YOURSELF',726,16);im.save(A/f'cafe-gallery-{k}.png')
