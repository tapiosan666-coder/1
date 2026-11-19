"""Create a compact, shared library of original retail window and wall cases.
Each entry has separate finish, metal, printed artwork and light diffuser surfaces.
A build-time Godot script converts the binary triangles to compressed ArrayMeshes.
"""
from pathlib import Path
from collections import defaultdict
import json, math, struct, sys
from art import CATEGORIES, PALETTES
MATT, METAL, PRINT, LAMP, VENEER = range(5)
TAU=math.tau
def color(hexcode):
    return bytes.fromhex(hexcode.lstrip('#')+'ff')
cream='#eee4ce';coal='#393b3d';steel='#9ba59d';oak='#967458';gold='#ae9162';paper='#ebe2cd'
class Case:
    def __init__(self,category,role,v):
        self.cat=category;self.v=v;self.role=role;self.data=defaultdict(bytearray)
        self.solids=[]
        self.print_id=list(CATEGORIES).index(category)*3+v
        self.pal=PALETTES[(list(CATEGORIES).index(category)+v)%len(PALETTES)]
        self.make()
    def face(self,pts,col,mat=MATT,uv=None):
        a,b,c=pts[:3]
        if mat==MATT and col.lower() in ('#976e51','#a78160','#796451','#967458'):
            mat=VENEER
        u=[b[i]-a[i] for i in range(3)]; v=[c[i]-a[i] for i in range(3)]
        n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
        length=math.sqrt(sum(t*t for t in n))
        if length<1e-8:return
        n=[t/length for t in n]
        if mat==VENEER:
            if abs(n[1])>.6:uv=[(p[0]/1.28,p[2]/.72) for p in pts]
            elif abs(n[0])>.6:uv=[(p[1]/1.28,p[2]/.72) for p in pts]
            else:uv=[(p[0]/1.28,p[1]/.72) for p in pts]
        for i in range(1,len(pts)-1):
            for j in (0,i+1,i):
                self.data[mat].extend(struct.pack('<3f3f4s2f',*pts[j],*n,color(col),*(uv[j] if uv else (0,0))))
    def box(self,x,y,z,w,h,d,col,mat=MATT):
        a=x-w/2;b=x+w/2;c=y-h/2;e=y+h/2;f=z-d/2;g=z+d/2
        p=[(a,c,f),(b,c,f),(b,e,f),(a,e,f),(a,c,g),(b,c,g),(b,e,g),(a,e,g)]
        for face in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)]:
            self.face([p[i] for i in face],col,mat)
    def profile(self,x,y,z,rings,col,stretch=(1,1),sides=16,mat=MATT):
        pts=[[(x+math.sin(i*TAU/sides)*r*stretch[0],y+h,z+math.cos(i*TAU/sides)*r*stretch[1]) for i in range(sides)] for h,r in rings]
        for r,s in zip(pts,pts[1:]):
            for i in range(sides):
                j=(i+1)%sides
                self.face((r[i],r[j],s[j],s[i]),col,mat)
        self.face(list(reversed(pts[0])),col,mat);self.face(pts[-1],col,mat)
    def silhouette(self,points,depth,col):
        # An XY outline whose winding is CCW as seen from the customer's side.
        z,d=depth
        area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points,points[1:]+points[:1]))
        if area<0:points=list(reversed(points))
        front=[(x,y,z+d/2) for x,y in points];back=[(x,y,z-d/2) for x,y in points]
        # All silhouettes are authored star-shaped, including the sleeve seam.
        # Use a fan centred inside to keep the face clear of notches on outline.
        cx=sum(p[0] for p in points)/len(points);cy=sum(p[1] for p in points)/len(points)
        for i in range(len(points)):
            j=(i+1)%len(points)
            self.face([(cx,cy,z+d/2),front[i],front[j]],col)
            self.face([(cx,cy,z-d/2),back[j],back[i]],col)
            self.face([front[j],front[i],back[i],back[j]],col)
    def card(self,x,y,z,w,h,edition=None):
        i=self.print_id if edition is None else 3*list(CATEGORIES).index(self.cat)+edition%3
        u,v=i%8/8,i//8/9; left=u+.0008;right=u+1/8-.0008;top=v+.0008;bottom=v+1/9-.0008
        self.face([(x-w/2,y-h/2,z),(x+w/2,y-h/2,z),(x+w/2,y+h/2,z),(x-w/2,y+h/2,z)],
                  '#ffffff',PRINT,[(left,bottom),(right,bottom),(right,top),(left,top)])
    def tube(self,a,b,r,col,mat=METAL):
        v=[b[i]-a[i] for i in range(3)]; l=math.sqrt(sum(x*x for x in v))
        if l<.0001:return
        v=[x/l for x in v]; h=math.hypot(v[0],v[2]);u=(v[2]/h,0,-v[0]/h) if h>.0001 else (1,0,0)
        w=(v[1]*u[2]-v[2]*u[1],v[2]*u[0]-v[0]*u[2],v[0]*u[1]-v[1]*u[0])
        for i in range(8):
            t=i*TAU/8;k=(i+1)*TAU/8
            d=[r*(math.cos(t)*u[j]+math.sin(t)*w[j]) for j in range(3)]
            e=[r*(math.cos(k)*u[j]+math.sin(k)*w[j]) for j in range(3)]
            self.face([tuple(p[j]+s[j] for j in range(3)) for p,s in ((a,d),(a,e),(b,e),(b,d))],col,mat)
    def object(self,x,y,z,s,k):
        cat=self.cat
        dark,light,accent,sage=self.pal
        c=[dark,accent,sage][k%3]
        def bx(dx,dy,dz,w,h,d,co,m=MATT):self.box(x+dx*s,y+dy*s,z+dz*s,w*s,h*s,d*s,co,m)
        def lat(dx,dz,hp,co,stretch=(1,1),mat=MATT): self.profile(x+dx*s,y,z+dz*s,[(h*s,r*s) for h,r in hp],co,stretch,12,mat)
        if cat=='apparel':
            length=(.42,.51,.59)[k%3]
            pts=[(-.08,length),(-.16,length-.025),(-.25,length-.16),(-.18,length-.20),(-.125,length-.13),(-.15,.01),(.145,.018),(.125,length-.13),(.18,length-.19),(.24,length-.15),(.15,length-.025),(.067,length),(.045,length-.035),(-.035,length-.045)]
            self.silhouette([(x+i*s,y+j*s) for i,j in pts],(z,.052*s),c)
            self.tube((x-.12*s,y+length*s,z),(x,y+(length+.035)*s,z),.008*s,gold)
            self.tube((x,y+(length+.035)*s,z),(x+.12*s,y+length*s,z),.008*s,gold)
            self.tube((x,y+(length+.035)*s,z),(x,y+.68*s,z),.009*s,steel)
            bx(0,.10,0,.14,.012,.056,light)
        elif cat in ('shoes','sports'):
            lat(0,0,[(0,.16),(.025,.18),(.053,.165)],cream,(1.35,.55))
            self.silhouette([(x+i*s,y+j*s) for i,j in [(-.19,.051),(-.18,.09),(-.07,.12),(.025,.19),(.095,.14),(.17,.153),(.184,.052)]],(z,.13*s),c)
            for i in range(4):bx(-.062+i*.027,.133+i*.009,.066,.032,.009,.008,cream)
        elif cat in ('beauty','pharmacy','mobile','electronics'):
            if cat in ('mobile','electronics'):
                if k%3==1:
                    bx(0,.14,0,.24,.28,.09,coal);self.profile(x,y+.14*s,z+.045*s,[(0,.075*s),(.012*s,.07*s)],steel)
                else:
                    w,h=(.35,.21) if cat=='electronics' else (.126,.218)
                    bx(0,.016,0,.16,.032,.15,steel,METAL);bx(0,.083,0,.035,.14,.035,steel,METAL);bx(0,.135+h/2,0,w,h,.022,coal)
                    self.card(x,y+(.135+h/2)*s,z+.013*s,.92*w*s,.90*h*s,k)
            elif k%3==0:
                lat(0,0,[(0,.058),(.08,.062),(.088,.055),(.15,.055),(.175,.045)],c)
                bx(0,.093,.061,.075,.04,.005,cream)
            elif k%3==1:
                bx(0,.089,0,.11,.177,.075,c);bx(0,.202,0,.075,.049,.065,gold,METAL);bx(0,.082,.039,.082,.076,.004,paper)
            else:
                lat(0,0,[(0,.029),(.085,.029),(.09,.021),(.145,.019)],gold,mat=METAL)
                lat(.08,0,[(0,.037),(.095,.036)],c)
        elif cat in ('book','stationery','gallery','cinema','service','arcade'):
            w,h=(.224,.30) if k%3==0 else (.176,.26) if k%3==1 else (.25,.235)
            if cat=='arcade': w,h=.29,.35; bx(0,.065,0,.34,.13,.20,c);bx(0,.21,-.05,.31,.356,.08,dark);self.card(x,y+.245*s,z,.26*s,.22*s,k);return
            for j in range(2+(k%3)): bx(0,.018+j*.026,0,w,.024,.19,paper if j%2 else c)
            base=.052+.026*(k%3)
            bx(0,base+h/2,-.015,w,h,.03,c);self.card(x,y+(base+h/2)*s,z+.001*s,w*.955*s,h*.95*s,k)
        elif cat in ('home','garden','furniture','restaurant','cafe','food'):
            if cat=='garden':
                lat(0,0,[(0,.055),(.10,.09),(.12,.091)],c)
                for i in range(5):
                    a=i*TAU/5; tip=(x+math.sin(a)*.11*s,y+(.20+.04*(i%2))*s,z+math.cos(a)*.11*s)
                    self.tube((x,y+.12*s,z),tip,.013*s,sage,MATT)
                    self.profile(tip[0],tip[1]-.025*s,tip[2],[(0,.002*s),(.05*s,.035*s),(.082*s,.001*s)],['#677e5c','#506d55','#839665'][i%3],(.8,.62),9)
            elif cat=='food':
                for i in range(6):
                    dx=(i%3-1)*.082;dz=(i//3-.5)*.105
                    lat(dx,dz,[(0,.011),(.026,.043),(.065,.044),(.086,.019),(.093,.006)],['#d48742','#a45d4b','#9fac69'][k%3],(.98,1.04))
            elif cat=='cafe':
                if k%3==0:
                    lat(0,0,[(0,.055),(.008,.067),(.015,.105),(.022,.11)],cream)
                    lat(0,0,[(.023,.036),(.078,.062),(.105,.067),(.105,.058),(.077,.05)],c)
                    self.tube((x+.05*s,y+.09*s,z),(x+.093*s,y+.068*s,z),.009*s,c,MATT)
                    self.tube((x+.093*s,y+.068*s,z),(x+.048*s,y+.04*s,z),.009*s,c,MATT)
                else:
                    lat(0,0,[(0,.09),(.008,.12),(.014,.125)],paper)
                    for i in range(5):lat((i-2)*.028,0,[(.014,.016),(.045,.046-abs(i-2)*.006),(.076-abs(i-2)*.007,.01)],'#c58b4d',(1,1.25))
            elif cat=='furniture':
                bx(0,.18,0,.30,.042,.25,c);bx(0,.30,-.10,.29,.23,.035,c)
                for i in (-1,1):
                    for j in (-1,1):bx(i*.109,.079,j*.089,.026,.158,.026,oak)
            elif cat=='restaurant' or k%3==1:
                lat(0,0,[(0,.056),(.012,.072),(.041,.143),(.049,.146),(.05,.132),(.021,.065)],c)
            else:
                lat(0,0,[(0,.051),(.016,.07),(.11,.104),(.164,.066),(.19,.041),(.225,.045),(.226,.034),(.205,.035)],c,(1,1 if k%3 else .92))
        elif cat in ('toy','music','optics','accessories'):
            if cat=='music':
                for rad,center in ((.093,0),(.057,.035)):
                    self.profile(x+center*s,y,z,[(0,.05*s),(.08*s,rad*s),(.13*s,.046*s)],c,(1,.48))
                bx(.023,.27,0,.041,.29,.022,oak);bx(.023,.425,0,.069,.05,.026,c)
            elif cat=='toy':
                for i in range(3):
                    lat((i-1)*.098,0,[(0,.054),(.047,.055),(.058,.041)],(accent,sage,dark)[i],(1.05,1),MATT)
                    bx((i-1)*.098,.081,0,.08,.047,.06,light)
            elif cat=='optics':
                for sign in (-1,1):
                    for j in range(12):
                        a=j*TAU/12;b=(j+1)*TAU/12
                        self.tube((x+(sign*.061+.051*math.cos(a))*s,y+(.06+.029*math.sin(a))*s,z),(x+(sign*.061+.051*math.cos(b))*s,y+(.06+.029*math.sin(b))*s,z),.004*s,gold)
                bx(0,.061,0,.027,.008,.009,gold,METAL)
            else:
                lat(0,0,[(0,.09),(.025,.091),(.031,.084)],dark,(1,.7))
                for i in range(3):lat((i-1)*.041,0,[(.031,.012),(.047,.019),(.066,.003)],gold,mat=METAL)
    def make(self):
        from department_fixtures import build
        if self.role=='dining':
            dark,light,accent,_=self.pal
            self.dining_booth(dark,light,accent)
        elif not build(self):
            raise KeyError(f"No authored display for {self.cat}")

    def dining_booth(self,dark,light,accent):
        # Paired upholstered seats and a porcelain table on a real pedestal.
        self.box(0,.073,-.205,2.44,.146,.52,oak)
        self.box(0,.29,-.207,2.48,.285,.48,dark)
        self.box(0,.443,-.20,2.51,.095,.48,accent)
        self.box(0,.69,-.403,2.48,.54,.17,accent)
        for i in range(10):
            self.box(-1.10+i*.245,.69,-.313,.009,.50,.006,dark)
        for x in [-.61,.61]:
            self.profile(x,0,.227,[(0,.19),(.025,.20),(.045,.065),(.705,.048)],steel,(1,.85),12,METAL)
            self.profile(x,.705,.227,[(0,.32),(.042,.32)],light,(1.42,.71),20)
            self.profile(x,.748,.226,[(0,.055),(.015,.116),(.018,.12)],paper,(1,.75),18)
            self.profile(x+.19,.748,.222,[(0,.031),(.060,.046),(.066,.043)],dark,(1,.86),12)
        self.box(0,.685,-.45,2.55,1.31,.067,oak)
        self.card(.00,1.105,-.409,.35,.35)
    def save(self,path):
        with open(path,'wb') as f:
            for k in range(5):
                b=self.data[k];f.write(struct.pack('<I',len(b)//36));f.write(b)
def main():
    tmp=Path(sys.argv[1]);tmp.mkdir(parents=True,exist_ok=True)
    solids={}
    for cat in CATEGORIES:
        for role in (('arrival','gallery','dining') if cat=='restaurant' else ('arrival','gallery')):
            for v in range(3):
                case=Case(cat,role,v)
                key=f'{cat}-{role}-{v}'
                case.save(tmp/f'{key}.bin')
                if case.solids:solids[key]=[[round(n,5) for n in row] for row in case.solids]
    target=Path(__file__).resolve().parents[3]/'source/v36/studio-solids.json'
    target.write_text(json.dumps(solids,separators=(',',':'))+'\n')
if __name__=='__main__':main()
