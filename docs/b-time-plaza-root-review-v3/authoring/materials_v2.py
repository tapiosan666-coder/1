"""Original metric PBR maps and fictional editorial artwork. No external photographs."""
import numpy as np,math
from PIL import Image,ImageDraw,ImageFont

def build_assets(A):
 rng=np.random.default_rng(20261026);N=1024;z,x=np.mgrid[:N,:N];font=lambda n:ImageFont.truetype(str(A/'NotoSansCJKjp-Regular.otf'),n)
 def field(freq):
  a=np.fft.rfft2(rng.normal(size=(N,N)));fx=np.fft.rfftfreq(N)[None,:]*N;fy=np.fft.fftfreq(N)[:,None]*N;a*=np.exp(-(fx*fx+fy*fy)/(freq*freq*2));v=np.fft.irfft2(a,s=(N,N));return v/max(v.std(),1e-8)
 soft=field(5);grain=field(180);fibers=field(38)
 def save(name,color,height,rough,normalgain=1):
  Image.fromarray((np.clip(color,0,1)*255).astype('uint8')).save(A/(name+'_albedo.png'))
  dx=(np.roll(height,-1,1)-np.roll(height,1,1))*normalgain;dy=(np.roll(height,-1,0)-np.roll(height,1,0))*normalgain
  nn=np.stack([-dx,-dy,np.ones_like(dx)],2);nn/=np.linalg.norm(nn,axis=2,keepdims=True)
  Image.fromarray(((nn*.5+.5)*255).astype('uint8')).save(A/(name+'_normal.png'))
  Image.fromarray((np.clip(rough,0,1)*255).astype('uint8')).save(A/(name+'_roughness.png'))
 def color(base,delta):return np.array(base)[None,None,:]+delta[:,:,None]
 # Soft mineral variation. Actual roughness maps, not roughness multiplied twice.
 save('stone',color((.67,.65,.60),soft*.008+grain*.0018),grain*.001,.34+soft*.018,1)
 save('plaster',color((.84,.825,.785),grain*.0013),grain*.0004,np.full((N,N),.84),1)
 # Ring modulation and long fibers at metric scale; no synthetic high-contrast sine stripes.
 wood=np.sin((x+soft*2)*.23+fibers*.28)*.012+np.sin(x*.94+soft*.8)*.004+grain*.001
 save('wood',color((.52,.40,.27),wood),wood*.035,.47+grain*.015,1)
 save('walnut',color((.28,.19,.125),wood*.7),wood*.03,.42+grain*.02)
 save('dark_stone',color((.27,.29,.285),soft*.004+grain*.001),grain*.0007,.32+soft*.025)
 save('brushed',color((.64,.65,.64),rng.normal(size=(1,N))*.008+grain*.0008),grain*.0004,.28+np.sin(x*1.1)*.014)
 weave=np.sin(x*math.pi/2)*np.sin(z*math.pi/2)*.007
 save('fabric',color((.72,.71,.68),weave+grain*.002),weave*.12,.88+grain*.01)
 save('leather',color((.39,.28,.20),grain*.005+soft*.004),grain*.004,.55+grain*.03)
 # 32 original full book covers, editable SVG-like numeric graphics and typography.
 im=Image.new('RGB',(2048,1536),'white');dr=ImageDraw.Draw(im)
 names=['暮らしの輪郭','余白のある家','時間の庭','旅のスケッチ','小さな建築','珈琲の時間','LIGHT / SPACE','THE QUIET CITY','光と素材','歩く風景','本のある部屋','植物と日々','WINDOWS','FIELD NOTES','SLOW DESIGN','EVERYDAY LIFE']
 palettes=[((33,62,64),(235,225,195)),((211,187,143),(46,54,50)),((143,69,49),(245,233,207)),((224,224,209),(55,67,61)),((41,52,77),(232,224,199)),((102,124,110),(241,235,215))]
 for i in range(32):
  X=(i%8)*256;Y=(i//8)*384;bg,fg=palettes[i%len(palettes)];dr.rectangle((X,Y,X+255,Y+383),fill=bg)
  dr.rectangle((X+19,Y+18,X+237,Y+366),outline=fg,width=2)
  dr.ellipse((X+50,Y+90,X+208,Y+248),outline=fg,width=3)
  dr.rectangle((X+88,Y+115,X+170,Y+263),outline=fg,width=2)
  name=names[i%len(names)];dr.text((X+128,Y+45),name,font=font(23 if len(name)<9 else 15),fill=fg,anchor='mm')
  dr.text((X+128,Y+305),'FIND YOURSELF PRESS',font=font(13),fill=fg,anchor='mm');dr.text((X+128,Y+338),f'COLLECTION / {i+1:02}',font=font(12),fill=fg,anchor='mm')
 im.save(A/'book_covers.png')
 im=Image.new('RGB',(1536,768),(30,48,43));dr=ImageDraw.Draw(im);cream=(234,224,195)
 dr.text((80,64),'mellow / COFFEE & BAKERY',font=font(57),fill=cream)
 for j,(a,b)in enumerate([('本日のコーヒー','480'),('カフェラテ','560'),('バタークロワッサン','320'),('季節の焼き菓子','380')]):
  yy=210+j*110;dr.text((85,yy),a,font=font(42),fill=cream);dr.text((1380,yy),b,font=font(43),fill=cream,anchor='ra');dr.line((85,yy+65,1410,yy+65),fill=(94,116,104),width=2)
 im.save(A/'cafe_menu.png')
 im=Image.new('RGB',(512,512),(14,32,44));dr=ImageDraw.Draw(im)
 for i in range(9):dr.ellipse((60+i*19,60+i*19,452-i*19,452-i*19),outline=(40,137,143),width=2)
 dr.text((256,192),'FIND THE',font=font(42),fill=(232,227,204),anchor='mm');dr.text((256,252),'SIGNAL',font=font(56),fill=(245,189,87),anchor='mm');dr.text((256,390),'PRESS START',font=font(23),fill=(232,227,204),anchor='mm');im.save(A/'arcade_screen.png')
