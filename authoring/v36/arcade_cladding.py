"""Make seamless public-gallery joinery prints. One texture span is one panel bay."""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw

assets=Path(__file__).resolve().parents[2]/'assets/v36/commons'
w,h=768,1024
y,x=np.mgrid[0:h,0:w]
u=x/w
level=3.80-3.60*y/(h-1)
rng=np.random.default_rng(81036)
for wing,cell,base,body,wood,metal in [
    ('A',2.35,(63,76,81),(155,164,157),(133,113,91),(174,148,113)),
    ('B',3.10,(67,78,67),(161,167,145),(151,128,94),(165,134,86))]:
    raster=np.zeros((h,w,3),dtype=float)
    grain=rng.normal(0,1.3,(h,w))
    bed=2.1*np.sin(2*math.pi*(2*u+.31*np.sin(y/136)))+2.5*np.cos(2*math.pi*(u+level*.14))
    upper=level>=2.64
    lower=level<.83
    phase=(u*(28 if wing=='A' else 27))%1
    flute=np.minimum(phase,1-phase)
    shadow=(np.clip((.21-flute)/.14,0,1)*31) + (4*np.cos(phase*2*math.pi))
    for c in range(3):
        raster[:,:,c]=np.where(lower,base[c]+.8*grain+bed,np.where(upper,wood[c]+grain*.55+bed*.65-shadow,body[c]+grain+bed))
    im=Image.fromarray(np.uint8(np.clip(raster,0,255)))
    draw=ImageDraw.Draw(im)
    def y_at(m): return round((3.80-m)/3.60*(h-1))
    for m in [.29,.81,2.62,3.59]:
        v=y_at(m)
        draw.rectangle((0,v-2,w,v+2),fill=metal)
        draw.line((0,v+3,w,v+3),fill=(60,60,54))
    draw.rectangle((0,y_at(2.61),2,y_at(.84)),fill=(103,109,98))
    draw.line((3,y_at(2.61),3,y_at(.84)),fill=(180,181,163))
    im.save(assets/('cladding-'+wing+'.webp'),quality=88,method=5)
