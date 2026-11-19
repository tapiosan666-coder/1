"""Original ceramic/terrazzo drawings. All distances are in a 1024-unit art frame."""
from pathlib import Path
import math,random
import numpy as np
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'assets/v36/commons'
OUT.mkdir(parents=True,exist_ok=True)
PALETTES={
'A':('#ddd8cc','#293f4b','#a48050','#94a6a4','#e6dfc8'),
'B':('#d4c9aa','#345044','#a16842','#839477','#ede1bc'),
'C':('#ddd1b5','#465d61','#ad654a','#79a09c','#e6d7b8')
}
def leaf(draw,root,tip,width,fill,stroke):
    sx,sy=root; dx,dy=tip[0]-sx,tip[1]-sy; length=math.hypot(dx,dy)
    nx,ny=-dy/length,dx/length
    sides=[]
    for sign in (1,-1):
        half=[]
        for i in range(23):
            t=i/22
            bow=math.sin(t*math.pi)*width*sign
            half.append((sx+t*dx+nx*bow,sy+t*dy+ny*bow))
        sides.append(half)
    draw.polygon(sides[0]+sides[1][::-1],fill)
    draw.line([root,tip],fill=stroke,width=4)
def band(draw,box,start,end,fill,width):
    draw.arc(box,start,end,fill,width)
def design(wing,district):
    base,ink,metal,teal,ivory=PALETTES[wing]
    im=Image.new('RGB',(1024,1024),base); d=ImageDraw.Draw(im)
    if wing=='A':
        # Cut-stone fans: alternating vault sections with a smaller nested fan.
        c=(512,570) if district==1 else ((480,520) if district==2 else (512,700))
        off={1:-12,2:24,3:-38}[district]
        for i in range(14):
            a=off+6+i*12
            box=[c[0]-325,c[1]-325,c[0]+325,c[1]+325]
            d.pieslice(box,a+177,a+186,fill=teal if i%3 else ink)
            band(d,box,a+178,a+187,metal,9)
        for i in range(4):
            r=240-i*48
            band(d,[c[0]-r,c[1]-r,c[0]+r,c[1]+r],off+173,off+350,ivory if i%2 else metal,8)
        for i in range(4):
            cx=286+i*144; y=705-abs(1.5-i)*26
            d.polygon([(cx-25,y),(cx,y-21),(cx+25,y),(cx,y+21)],ink)
        d.line([(230,767),(794,767)],fill=metal,width=7)
    elif wing=='B' and district==2:
        # An astronomical dial in the district that houses the real plaza clock.
        d.ellipse((235,235,789,789),outline=ink,width=34)
        for k in range(60):
            a=k*math.tau/60; major=k%5==0
            r1=226 if major else 249; r2=266
            d.line([(512+math.sin(a)*r1,512-math.cos(a)*r1),(512+math.sin(a)*r2,512-math.cos(a)*r2)],fill=metal if major else ivory,width=8 if major else 3)
        for r in [206,160]: d.ellipse((512-r,512-r,512+r,512+r),outline=teal,width=4)
        d.polygon([(512,291),(537,520),(512,562),(488,520)],ink)
        d.polygon([(512,733),(488,512),(512,470),(537,512)],metal)
        d.ellipse((500,500,524,524),fill=ivory)
    elif wing=='B':
        # A fern frond or a sun through leaves. Alternating leaflet lengths are hand profiled.
        if district==3:
            d.ellipse((335,252,683,600),fill=metal)
            for k in range(15):
                a=(k*17+145)*math.pi/180
                d.line([(508+math.cos(a)*200,426+math.sin(a)*200),(508+math.cos(a)*258,426+math.sin(a)*258)],fill=teal,width=5)
        root=(360,799); tip=(624,237)
        d.line([root,tip],fill=ink,width=9)
        for i in range(8):
            t=i/10+.13; p=(root[0]+(tip[0]-root[0])*t,root[1]+(tip[1]-root[1])*t)
            spread=130*math.sin(math.pi*(t+.05)); up=110*(1-t)+35
            leaf(d,p,(p[0]-spread,p[1]-up),14*(1-t)+4,teal if i%2 else ink,metal)
            leaf(d,p,(p[0]+spread*1.18,p[1]-up*.46),15*(1-t)+5,ink if i%2 else teal,ivory)
    elif district==1:
        for i in range(5):
            root=(330+i*62,785);tip=(327+i*73,345-abs(i-2)*22)
            leaf(d,root,tip,12+i%2*3,teal if i%2 else ink,metal)
            d.ellipse((tip[0]-12,tip[1]-61,tip[0]+13,tip[1]+8),fill=metal)
        for i in range(4):
            band(d,(200,677+i*19,824,766+i*19),4,176,ink,5)
    elif district==2:
        for i in range(7):
            y=306+i*68
            pts=[(x,y+37*math.sin((x-250)/106+i*.45)) for x in range(240,790,4)]
            d.line(pts,fill=[ink,teal,metal][i%3],width=18 if i%3==0 else 9)
        d.ellipse((637,234,713,310),fill=metal)
    else:
        for r,th,k in [(275,24,ink),(215,10,metal),(165,15,teal)]:
            for j in range(5):band(d,(512-r,512-r,512+r,512+r),j*72+5,j*72+53,k,th)
        for j in range(5):
            a=math.tau*j/5-.3; ca=math.cos(a);sa=math.sin(a)
            pts=[(512+ca*x-sa*y,512+sa*x+ca*y) for x,y in [(0,12),(185,-36),(139,20),(22,47)]]
            d.polygon(pts,fill=ink if j%2 else metal)
    # Visible mineral aggregate with irregular ceramic joints, baked only once.
    rng=np.random.default_rng((ord(wing)*13+district)*37)
    ar=np.asarray(im).astype(np.float32)
    field=rng.normal(1,.018,(1024,1024,1))
    pieces=rng.uniform(.94,1.055,(32,32))
    yy,xx=np.indices((1024,1024))
    rows=yy//32;xx=(xx+16*(rows%2))%1024;cols=xx//32
    joint=(xx%32==0)|(yy%32==0)
    field*=pieces[rows,cols][...,None]
    ar=np.uint8(np.clip(ar*field*(1.-joint[...,None]*.105),0,255))
    out=Image.fromarray(ar).resize((640,640),Image.Resampling.LANCZOS)
    out.save(OUT/f'inlay-{wing}{district}.webp',quality=91,method=6)
for wing in PALETTES:
    for d in range(1,4):design(wing,d)
