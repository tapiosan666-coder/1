"""Build Orienne's original back-wall book cases in metres; glTF + embedded print atlas."""
from pathlib import Path
from array import array
from io import BytesIO
import json
import math
import random
import struct
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "assets/v36/models"
DEPARTMENTS = [
    ("atelier", "美術・建築", "ART & ARCHITECTURE", ["白い家", "建築の線", "緑の窓", "陶のかたち"], "#285451", "#E8B185"),
    ("field", "旅・地理", "FIELD GUIDES", ["島を歩く", "港の手帖", "山の地図", "北紀行"], "#27485B", "#CDA767"),
    ("press", "文学・随筆", "FICTION & ESSAYS", ["声の庭", "野の灯り", "朝の駅", "舟と月"], "#734438", "#E1C5A0"),
    ("junior", "児童書", "LITTLE READERS", ["くもの町", "うみの子", "きいろい実", "つきとねこ"], "#526447", "#EBB44F"),
]
SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"
SANS = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

def text(d, xy, value, size, color, serif=False, anchor=None):
    d.text(xy, value, font=ImageFont.truetype(SERIF if serif else SANS, size, index=0), fill=color, anchor=anchor)

def print_atlas(index):
    _, title, subtitle, titles, ink, accent = DEPARTMENTS[index]
    image = Image.new("RGB", (1024, 1024), "#eee3cc")
    d = ImageDraw.Draw(image)
    d.rectangle((0,0,1023,190),fill=ink)
    d.line((55,39,167,39),fill=accent,width=4)
    text(d,(53,58),title,62,"#FFF1D9",True)
    text(d,(990,149),subtitle,23,accent,anchor="rs")
    paper = ["#E8D6AD", "#9DACA2", "#DFA781", "#D3AB73","#ECE3C9","#9EAEBB","#BD8577","#A6B692"]
    for i in range(8):
        x,y=(i%4)*256, 200+(i//4)*326
        bg=paper[(i+index)%8]
        d.rectangle((x,y,x+255,y+325),fill=bg)
        other=ink if i%2==0 else "#313C42"
        if index==0:  # architectural axonometrics
            for k in range(5):
                xx=x+19+k*30; yy=y+146-k*9
                d.polygon([(xx,yy),(xx+39,yy-25),(xx+81,yy-13),(xx+43,yy+12)],fill=other)
                d.polygon([(xx,yy+2),(xx+42,yy+15),(xx+42,yy+72),(xx,yy+58)],fill=accent)
                d.line((xx+42, yy+13, xx+80, yy-11, xx+80, yy+47, xx+42, yy+72),fill=other,width=3)
        elif index==1:  # illustrated contour maps
            for k in range(13):
                points=[(x+127+math.cos(a*.13)*(21+k*6+8*math.sin(a*.39+i)),y+127+math.sin(a*.13)*(31+k*4+7*math.cos(a*.26))) for a in range(50)]
                d.line(points+[points[0]],fill=other,width=2)
            d.line((x+53,y+191,x+96,y+141,x+143,y+145,x+190,y+77),fill="#A34938",width=5)
        elif index==2:
            d.ellipse((x+36+i*2,y+42,x+152+i*2,y+158),fill=accent)
            for k in range(9):
                d.arc((x+25,y+87+k*8,x+216,y+202+k*6),180,350,fill=other,width=3)
        else:
            d.ellipse((x+65,y+92,x+183,y+195),fill=other)
            for side in (0,1):
                xx=x+65+side*80
                d.polygon([(xx,y+124),(xx+9,y+76),(xx+36,y+106)],fill=other)
            d.ellipse((x+101,y+131,x+108,y+138),fill=accent)
            d.ellipse((x+140,y+131,x+147,y+138),fill=accent)
            d.line((x+120,y+151,x+126,y+156,x+132,y+150),fill=accent,width=3)
        text(d,(x+16,y+8),"ORIENNE  /  EDITIONS",11,other)
        text(d,(x+15,y+230),titles[i%4],36,other,True)
        text(d,(x+16,y+294),subtitle,12,other)
    # Materials share this atlas. The oak sample carries vertical grain.
    colors=["#644332","#BD9B70","#27363A",ink,"#DFCCAB","#B58B56",accent,"#A76952","#718681","#ADA282","#ECD7B4","#847C70"]
    for i,c in enumerate(colors):d.rectangle((i*80,860,i*80+79,999),fill=c)
    rng=random.Random(7549)
    for k in range(90):
        x=rng.randrange(0,80);d.line((x,862,x+rng.randrange(-1,2),997),fill=rng.choice(["#694936","#70503D","#604132"]))
    buf=BytesIO();image.save(buf,"PNG",optimize=True)
    return buf.getvalue()

class Cabinet:
    def __init__(self,idx,variant):
        self.pos=array("f");self.uv=array("f");self.norm=array("f");self.ind=array("H")
        self.idx=idx;self.variant=variant;self.stock=0;self.rng=random.Random(1401+idx*172+variant*91)

    def quad(self,p,rect):
        a,b,c,_=p
        u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
        n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
        length=math.sqrt(sum(t*t for t in n));start=len(self.pos)//3
        x0,y0,x1,y1=rect
        for vertex,uv in zip(p,[(x0,y1),(x1,y1),(x1,y0),(x0,y0)]):
            self.pos.extend(vertex);self.norm.extend(t/length for t in n);self.uv.extend(t/1024 for t in uv)
        self.ind.extend(start+i for i in (0,1,2,0,2,3))

    def block(self,x,y,z,w,h,d,mat,front=None):
        r=(mat*80+3,865,mat*80+77,992)
        l,b,k=x-w/2,y,z-d/2
        R,T,F=l+w,b+h,k+d
        self.quad([(l,b,F),(R,b,F),(R,T,F),(l,T,F)],front or r)
        self.quad([(R,b,k),(l,b,k),(l,T,k),(R,T,k)],r)
        self.quad([(R,b,F),(R,b,k),(R,T,k),(R,T,F)],r)
        self.quad([(l,b,k),(l,b,F),(l,T,F),(l,T,k)],r)
        self.quad([(l,T,F),(R,T,F),(R,T,k),(l,T,k)],r)
        self.quad([(l,b,k),(R,b,k),(R,b,F),(l,b,F)],r)

    def cover(self,x,y,z,w,h,edition):
        i=edition%8;u=(i%4)*256;v=200+(i//4)*326
        self.block(x,y,z,w,h,.036,4,front=(u+2,v+2,u+253,v+323))
        self.stock+=1

    def spines(self,x,y,end,z):
        while x < end-.055:
            w=self.rng.uniform(.032,.058);h=self.rng.uniform(.19,.32)
            mat=self.rng.choice([3,6,7,8,9,10,11])
            self.block(x+w/2,y,z,w,h,.195,mat)
            self.block(x+w/2,y+h*.77,z+.099,w*.78,.009,.005,4)
            x+=w+.005;self.stock+=1

    def build(self):
        i=self.idx;v=self.variant
        top=[2.88,2.65,2.96,2.26][i]
        self.block(0,.023,-.02,1.89,.115,.76,2)
        self.block(0,.138,-.03,1.94,.46,.79,0)
        self.block(0,.598,-.02,1.95,.058,.81,1)
        self.block(0,.65,-.35,1.88,top-.65,.055,3)
        for x in (-.953,.953):self.block(x,.63,-.12,.044,top-.63,.56,0)
        self.block(0,top-.04,-.10,1.95,.058,.60,0)
        self.block(0,top-.345,-.06,1.85,.275,.055,3,(4,3,1020,187))
        self.block(0,top-.067,.18,1.79,.014,.037,10)
        levels=([.70,1.12,1.54,1.96] if i in (0,2) else [.69,1.17,1.68] if i==1 else [.69,1.08,1.49])
        for j,y in enumerate(levels):
            depth=.44 if i in (0,1,3) else .35
            z=-.12+(.06 if j==0 else 0)
            self.block(0,y,z,1.84,.047,depth,1)
            face_count=([3,4,0,2] if i==0 else [3,2,4] if i==1 else [0,2,0,2] if i==2 else [4,3,4])[j]
            left=-.87;right=.87
            if face_count:
                split=(i==2 or (i==0 and j==3))
                if split:
                    self.spines(-.86,y+.047,-.06,z+.01);left=.025
                for a in range(face_count):
                    cell=(right-left)/face_count
                    cx=left+cell*(a+.5)
                    self.cover(cx,y+.047,z+.087,min(.32,cell*.79),min(.386,(top-.38)-(y+.06)),v+a+j*2)
                self.block((left+right)*.5,y+.046,z+.145,right-left,.037,.017,5)
            else:self.spines(-.88,y+.047,.88,z+.02)
        for x in (-.44,.44):self.block(x,.36,.372,.12,.014,.022,5)
        return self

    def bench(self):
        # Two-sided island with low plinth and recessed feet; preserve the original aisle envelope.
        i=self.idx
        h=[.76,.79,.84,.55][i]
        self.block(0,.003,0,1.53,.073,.58,2)
        for x in (-.60,.60):
            self.block(x,.076,0,.11,h-.076,.50,0)
        self.block(0,.22,0,1.46,.065,.31,3)
        self.block(0,h-.068,0,1.73,.068,.72,1)
        if i in (0,2):
            for a in range(3):
                x=(a-1)*.525
                for j in range(2+a%2):
                    y=h+j*.034
                    self.block(x,y,-.028,.38,.033,.285,4)
                    edition=(a+j+self.variant)%8;u=(edition%4)*256;v=200+(edition//4)*326
                    self.quad([(x-.19,y+.034,.116),(x+.19,y+.034,.116),(x+.19,y+.034,-.171),(x-.19,y+.034,-.171)],(u+2,v+2,u+253,v+323))
                    self.stock+=1
        else:
            # Three tiered display troughs. Books lean against a solid, low backstop.
            for a in range(3):
                x=(a-1)*.52
                for j in range(2):
                    y=h+j*.09;z=.13-j*.29
                    if j: self.block(x,h,z,.492,.09,.23,1)
                    self.block(x,y,z-.065,.49,.15,.029,3)
                    self.cover(x-.095,y,z,.228,.32+j*.05,(a+j+self.variant)%8)
                    self.cover(x+.117,y,z+.052,.19,.264,(a+j+self.variant+3)%8)
                    self.block(x,y,z+.094,.49,.044,.025,5)
        return self

    def save(self,path,atlas):
        streams=[self.pos.tobytes(),self.norm.tobytes(),self.uv.tobytes(),self.ind.tobytes(),atlas]
        views=[];blob=bytearray()
        for s in streams:
            blob.extend(bytes((-len(blob))%4));views.append({"buffer":0,"byteOffset":len(blob),"byteLength":len(s)});blob.extend(s)
        bounds=[[fn(self.pos[i::3]) for i in range(3)] for fn in (min,max)]
        attrs=[]
        for j,(values,num,ty) in enumerate([(self.pos,3,"VEC3"),(self.norm,3,"VEC3"),(self.uv,2,"VEC2"),(self.ind,1,"SCALAR")]):
            attrs.append({"bufferView":j,"componentType":5123 if j==3 else 5126,"count":len(values)//num,"type":ty})
        attrs[0].update(min=bounds[0],max=bounds[1])
        data={"asset":{"version":"2.0","generator":"FIND YOURSELF v36 Orienne studio"},"scene":0,"scenes":[{"nodes":[0]}],"nodes":[{"mesh":0}],"meshes":[{"primitives":[{"attributes":{"POSITION":0,"NORMAL":1,"TEXCOORD_0":2},"indices":3,"material":0}]}],"materials":[{"name":"Orienne print and joinery","pbrMetallicRoughness":{"baseColorTexture":{"index":0},"metallicFactor":0,"roughnessFactor":.62}}],"images":[{"bufferView":4,"mimeType":"image/png"}],"textures":[{"source":0}],"buffers":[{"byteLength":len(blob)}],"bufferViews":views,"accessors":attrs}
        meta=json.dumps(data,separators=(",",":")).encode();meta+=b" "*((-len(meta))%4);blob.extend(bytes((-len(blob))%4))
        path.write_bytes(struct.pack("<4sII",b"glTF",2,28+len(meta)+len(blob))+struct.pack("<I4s",len(meta),b"JSON")+meta+struct.pack("<I4s",len(blob),b"BIN\0")+blob)

def main():
    DEST.mkdir(parents=True,exist_ok=True)
    by_fixture={};stock={}
    # The main sales spine splits this back wall at bays 12/13. Keep its opening.
    for i,slots in enumerate([[5,6,7],[8,9],[10,11,12],[13,14]]):
        atlas=print_atlas(i)
        for v,slot in enumerate(slots):
            key=f"orienne_{DEPARTMENTS[i][0]}_{v}"
            cabinet=Cabinet(i,v).build()
            cabinet.save(DEST/(key+".glb"),atlas)
            by_fixture[f"A1F-051-V31-{slot:03d}"]=key
            stock[key]=cabinet.stock
    for i,slots in enumerate([[40,51],[39,43],[48,46],[60,63]]):
        key=f"orienne_{DEPARTMENTS[i][0]}_island"
        cabinet=Cabinet(i,0).bench()
        cabinet.save(DEST/(key+".glb"),print_atlas(i))
        for slot in slots:by_fixture[f"A1F-051-V31-{slot:03d}"]=key
        stock[key]=cabinet.stock
    out=ROOT/"source/v36/orienne.json";out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({"by_fixture":by_fixture,"stock":stock},indent=2)+"\n")

if __name__=="__main__":main()
