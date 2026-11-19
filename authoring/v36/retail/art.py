"""Original illustrated department / edition cards, drawn into a shared mipmapped sheet.

Run with Pillow. The font outlines in the raster use the local DejaVu family.
"""
import math, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[3]
CATEGORIES={
 'apparel':('Form & Fold','SPRING SILHOUETTES','garment'), 'shoes':('Sole Works','WALKING COLLECTION','shoe'),
 'beauty':('Pigment Lab','COLOUR & CARE','bottle'), 'book':('The Reading Room','EDITIONS & PRINT','book'),
 'food':('Market Table','FRESH FROM THE GROWER','pear'), 'cafe':('Daily Roast','COFFEE & PATISSERIE','cup'),
 'restaurant':('Table Service','THE SEASONAL MENU','plate'), 'home':('Objects & Form','CERAMICS AND GLASS','vase'),
 'electronics':('Listening Studio','SOUND / IMAGE','speaker'), 'sports':('Field Notes','OUTDOOR COLLECTION','mountain'),
 'service':('Service Desk','CUSTOMER SERVICES','paper'), 'arcade':('Arcade Club','PLAY SELECTION','controller'),
 'toy':('Play Workshop','LOOK • BUILD • PLAY','easel'), 'music':('Listening Room','RECORDS & INSTRUMENTS','record'),
 'pharmacy':('Care Studio','DAILY WELLNESS','bottle'), 'furniture':('Living Study','MATERIALS & TEXTURES','chair'),
 'garden':('Garden Journal','SEASONAL SPECIMENS','leaf'), 'accessories':('Fine Objects','SMALL EDITIONS','jewel'),
 'cinema':('Picture House','SCREENING PROGRAMME','film'), 'stationery':('Paper Atelier','PAPER AND INK','book'),
 'gallery':('Gallery Study','WORKS ON PAPER','abstract'), 'optics':('Frame Studio','EYEWEAR COLLECTION','glasses'),
 'mobile':('Pocket Studio','DEVICES & AUDIO','speaker')}
PALETTES=[('#243c39','#efdcad','#c5734f','#9db2a9'),('#463443','#f6dfb5','#bcbdef','#d18173'),
          ('#2f4054','#e7e3d4','#dfa65d','#a4bdc3'),('#773e34','#f8edce','#aeb994','#d8a270'),
          ('#3c4b39','#f2e6d0','#df9a67','#9abaae')]
S=256
def font(name,size):
 return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVu'+name+'.ttf',size)
FONT=font('Serif',23);SMALL=font('SansCondensed-Bold',11);NUMBER=font('Serif-Italic',37)
def illustration(d,m,ink,c2,c3):
 def line(points,w=3,fill=ink):d.line(points,fill,width=w,joint='curve')
 def poly(points,fill):d.polygon(points,fill)
 def ellipse(coords,fill,outline=None,w=1):d.ellipse(coords,fill,outline,width=w)
 if m in ('vase','pear','bottle','cup','leaf'):
  ellipse((49,151,203,165),c3)
  if m=='leaf':
   for i in range(6):
    x=55+i*26; top=64+(i%3)*12
    poly([(128,154),(x,top+20),(x-12,top),(x+9,top+3),(x+21,top+23)],ink if i%2 else c2)
  elif m=='cup':
   d.arc((146,88,200,138),240,115,ink,8);d.pieslice((59,57,166,153),0,180,ink);ellipse((58,88,167,105),c2,ink,3)
   for x in (95,119,142):d.arc((x,62,x+10,88),80,265,ink,2)
  elif m=='bottle':
   for x,h in ((75,91),(121,71),(161,102)):
    d.rounded_rectangle((x-15,h+12,x+14,152),6,fill=ink);d.rectangle((x-8,h,x+7,h+16),c2)
    d.rectangle((x-12,h+31,x+11,h+45),c3)
  elif m=='pear':
   for x,y,r in ((93,121,30),(152,128,24)):
    ellipse((x-r,y-r//2,x+r,y+r),ink);poly([(x-r+3,y),(x-13,y-29),(x-4,y-38),(x+6,y-37),(x+r-2,y)],ink);line([(x,y-35),(x+6,y-49)],4);ellipse((x+5,y-48,x+28,y-39),c2)
  else:
   poly([(82,150),(77,133),(84,113),(97,98),(91,78),(120,78),(115,101),(131,120),(133,137),(124,150)],ink)
   ellipse((144,99,179,151),c2);d.rectangle((152,90,171,116),c2)
 elif m in ('book','paper','film','easel','abstract'):
  poly([(70,84),(122,71),(126,139),(75,151)],c2);poly([(128,72),(184,84),(178,151),(124,139)],ink)
  if m=='film':
   for j in range(4):d.rectangle((76,89+j*14,84,95+j*14),ink)
  elif m=='abstract':
   ellipse((88,91,149,141),c3);poly([(112,145),(150,92),(173,141)],ink)
  else:
   for j in range(4):line([(78,99+j*9),(112,91+j*9)],2,ink);line([(137,88+j*10),(171,96+j*10)],2,c3)
 elif m in ('record','speaker','controller','glasses','jewel','plate'):
  if m=='glasses':
   d.arc((48,89,119,137),0,360,ink,6);d.arc((133,89,204,137),0,360,ink,6);line([(118,101),(134,101)],5)
  elif m=='controller':
   d.rounded_rectangle((66,90,188,145),18,fill=ink);line([(83,114),(111,114)],6,c2);line([(97,100),(97,129)],6,c2)
   for x,y in ((150,109),(164,121)):ellipse((x,y,x+7,y+7),c3)
  elif m=='jewel':
   line([(67,78),(126,151),(187,78)],4);poly([(110,128),(126,116),(143,128),(126,151)],c2)
  else:
   ellipse((83,69,172,158),ink);ellipse((98,84,157,143),c2);ellipse((114,100,140,127),ink);ellipse((123,110,130,117),c3)
   if m=='speaker':d.rectangle((77,65,177,160),outline=ink,width=3)
 elif m in ('garment','shoe','mountain','chair'):
  if m=='garment':
   poly([(102,77),(86,80),(64,100),(79,113),(91,101),(88,151),(157,151),(153,101),(168,113),(184,99),(160,80),(144,77),(139,87),(110,87)],ink);line([(110,87),(124,107),(139,87)],3,c2)
  elif m=='shoe':
   poly([(54,135),(77,129),(108,103),(146,113),(165,108),(183,127),(200,135),(192,146),(59,146)],ink)
   line([(73,139),(187,139)],3,c2)
   for i in range(4):line([(105+i*8,111+i),(114+i*8,119+i)],2,c3)
  elif m=='chair':
   d.rounded_rectangle((84,77,166,116),8,fill=ink);poly([(74,121),(161,114),(181,130),(82,138)],c2);line([(85,135),(81,153)],4);line([(171,129),(173,151)],4)
  else:
   poly([(48,149),(102,71),(136,149)],c2);poly([(80,149),(146,82),(203,149)],ink);line([(134,96),(145,83),(158,98)],3,c3)
def main():
 keys=list(CATEGORIES)
 atlas=Image.new('RGB',(8*S,9*S))
 for i,key in enumerate(keys):
  title,sub,motif=CATEGORIES[key]
  for v in range(3):
   n=i*3+v
   bg,cream,ochre,sage=PALETTES[(i+v)%len(PALETTES)]
   back,ink=(cream,bg) if v!=1 else (bg,cream)
   card=Image.new('RGB',(S,S),back);d=ImageDraw.Draw(card)
   d.rectangle((11,10,244,245),outline=ochre,width=2)
   d.text((20,19),'S T U D I O    S E L E C T I O N',font=SMALL,fill=ink)
   d.line((19,39,236,39),ink,1);d.text((201,44),f'{v+1:02}',font=NUMBER,fill=sage)
   illustration(d,motif,ink,ochre,sage)
   d.text((128,177),title,font=FONT,fill=ink,anchor='mt',stroke_width=0)
   d.line((44,208,212,208),ochre,2);d.text((128,217),sub,font=SMALL,fill=ink,anchor='mt')
   atlas.paste(card,((n%8)*S,(n//8)*S))
 (ROOT/'assets/v36/studios').mkdir(parents=True,exist_ok=True)
 atlas.save(ROOT/'assets/v36/studios/edition-cards.webp',quality=92,method=5)
if __name__=='__main__':main()
