"""Print original panoramic artwork and the three nearest shops from v17's actual brand directory.
Run after the physically surveyed wall footprints are present in the public courts catalog."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,math,random
from functools import lru_cache
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
DIR=ROOT/'assets/v36/commons'
CJK='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
SERIF='/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc'
LATIN='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
@lru_cache(maxsize=32)
def font(size,face=CJK):return ImageFont.truetype(face,size,index=0)
def draw_text(draw,x,y,message,size,color,typeface=CJK):
 draw.text((x,y),message,font=font(size,typeface),fill=color,anchor='lt')
def arch(d,x,base,w,h,col,inner,thick):
 d.rectangle((x-w,base-h*.49,x+w,base),fill=col)
 d.pieslice((x-w,base-h*.98,x+w,base),180,360,fill=col)
 d.rectangle((x-w+thick,base-h*.49,x+w-thick,base+1),fill=inner)
 d.pieslice((x-w+thick,base-h*.98+thick,x+w-thick,base-thick),180,360,fill=inner)
def frond(d,x,y,l,angle,leaf,tint):
 v=np.array((math.cos(angle),math.sin(angle))); ort=np.array((-v[1],v[0])); base=np.array((x,y))
 d.line([tuple(base),tuple(base+v*l)],fill=tint,width=2)
 for j in range(1,14):
  t=j/16
  for sign in [-1,1]:
   st=base+v*l*(t+(.016 if sign==1 else 0))
   end=st+v*l*.14+ort*l*sign*.18*math.sin(t*math.pi)
   dx=end-st;norm=np.array((-dx[1],dx[0]));norm=norm/max(1,np.linalg.norm(norm))
   leafw=l*.019*(1-t*.65)
   mask=[tuple(st+dx*u+norm*leafw*math.sin(u*math.pi)*s) for s in (1,-1) for u in (np.linspace(0,1,11) if s==1 else np.linspace(1,0,11))]
   d.polygon(mask,fill=leaf)
PALETTE={
'A':('#182c3a','#eee5d1','#c3a77e','#586e74','#a98d71'),
'B':('#213e36','#f0e9d6','#d6a16a','#779381','#9aab80'),
'C':('#284348','#f1e4c9','#c57c58','#73a1a0','#b3ba9c')}
TITLES={'A':['西の回廊','東の回廊','南の回廊'],'B':['翼の広場','時の広場','光の広場'],'C':['西の散歩道','中庭の散歩道','東の散歩道']}
FLOORS={'B1':'地下の街路','1F':'広場階','2F':'回廊階','3F':'上層階','RF':'屋上階'}
def print_panel(row,brands):
 wing=row['wing'];floor=row['floor'];district=row['district'];zone=row['zone']; title=TITLES[wing][district-1]
 if wing=='B' and floor in ('B1','RF'):title='地下のプロムナード' if floor=='B1' else '屋上の散策路'
 if wing=='C' and floor=='B1':title='アウトレット地下街'
 if floor=='RF' and wing!='B':title='屋上の散策路'
 ink,paper,accent,green,muted=PALETTE[wing]
 im=Image.new('RGB',(1400,420),paper);art=Image.new('RGB',(660,420),green);a=ImageDraw.Draw(art)
 tier=list(FLOORS).index(floor)
 seed=ord(wing)*100+tier*10+district;rng=random.Random(seed)
 if wing=='A':
  a.rectangle((0,0,660,420),fill='#bcc7be')
  a.ellipse((370+12*tier,33,509+12*tier,167),fill='#e8c99c')
  for depth in range(3):
   horizon=235+depth*67
   heights=[rng.randint(30,91) for _ in range(23)]
   for k,h in enumerate(heights):a.rectangle((k*33-12,horizon-h,k*33+22,horizon),fill=('#95a7a5','#788e93','#5c747b')[depth])
  for k in range(5):
   x=-88+k*175+tier*17;y=430
   arch(a,x,y,89,270-district*8,ink,green,18)
  for i in range(24):
   a.line((365,260,i*55-280,425),fill=accent,width=1)
 elif wing=='B':
  a.rectangle((0,0,660,420),fill='#d8dcc2')
  a.ellipse((100+35*tier,-42,383+35*tier,241),fill='#e9c298')
  for m in range(7):
   xy=[(x,250+m*20-24*math.sin(x/98+m*.46)+10*math.cos(x/58+tier)) for x in range(-3,672,7)]
   a.line(xy,fill=('#adbba1','#a8b89c','#829a87','#bcc3a6','#91a894','#789987','#627e70')[m],width=5)
  for i in range(7):
   frond(a,rng.randrange(-30,680),468,rng.randint(155,385),rng.uniform(-2.44,-.8),[ink,green,muted][i%3],green)
 else:
  a.rectangle((0,0,660,420),fill='#c5d6c8')
  a.ellipse((95+45*tier,33,228+45*tier,166),fill='#f0d9ad')
  for k,(h,c) in enumerate([(175,'#b7c4a9'),(226,'#91b3a8'),(273,'#719795'),(331,'#507776')]):
   coords=[(x,h-48*math.sin(x/(143+k*3)+tier*.17+k*.46)+18*math.cos(x/67-k)) for x in range(-7,676,6)]
   a.polygon(coords+[(670,420),(-8,420)],fill=c)
  for i in range(6):
   x=70+97*i+district*9;y=249+int(25*math.sin(i*.9))
   a.polygon([(x-21,y+6),(x+4,y-13),(x+26,y+4),(x+21,y+4),(x+20,y+23),(x-15,y+25),(x-15,y+6)],fill=paper if i%3 else accent)
  for k in range(4):
   a.line([(420+k*19,310),(363+k*20,342),(249+k*22,370),(162+k*28,420)],fill='#cbbba0',width=2)
 # Paper texture and distinct composition at the destination; text is sharply typeset last.
 ar=np.asarray(art).astype(np.int16)
 ar=np.uint8(np.clip(ar+np.random.default_rng(seed).normal(0,1.8,(420,660,1)),0,255))
 im.paste(Image.fromarray(ar),(0,0));d=ImageDraw.Draw(im)
 d.rectangle((659,0,671,419),fill=accent)
 draw_text(d,709,34,f'{wing} 館    /    {floor}      {FLOORS[floor]}',24,green)
 draw_text(d,704,93,title,55,ink,SERIF)
 d.line((709,186,1352,186),fill=accent,width=3)
 draw_text(d,709,211,'この階の近隣店舗',21,ink)
 x,y,z=row['p']
 local=[b for b in brands if b['wing']==wing and b['floor']==floor]
 local.sort(key=lambda b:math.hypot(x-b['sign_position'][0],z-b['sign_position'][2]))
 for i,b in enumerate(local[:3]):
  draw_text(d,710,254+i*43,b['name'],25,ink,LATIN)
  draw_text(d,1178,254+i*43,b['category'][:9],18,green)
 im.resize((1120,336),Image.Resampling.LANCZOS).save(DIR/f'wall-{zone}.webp',quality=89,method=4)
def main():
 brands=json.load(open(ROOT/'source/v17/brands.json'))
 for row in json.load(open(ROOT/'source/v36/public-courts.json')):
  if row.get('wall'):print_panel(row,brands)
if __name__=='__main__':main()
