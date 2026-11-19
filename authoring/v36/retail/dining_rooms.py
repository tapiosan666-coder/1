"""Original furnishing sets for the two stacked, plan-identical C-SE dining rooms."""
from pathlib import Path
from collections import defaultdict
import json,math,sys
from model import Case,MATT,METAL,LAMP,VENEER,cream,coal,steel,oak,gold,paper,TAU
from art import CATEGORIES,PALETTES
ROOT=Path(__file__).resolve().parents[3]
class Dining(Case):
    def __init__(self,name):
        self.data=defaultdict(bytearray);self.name=name;self.offset=(0,0,0);self.angle=0
        self.cat='restaurant' if name in ['family_table','family_booth','host_station'] else 'cafe'
        self.v=2 if self.cat=='restaurant' else 0;self.print_id=list(CATEGORIES).index(self.cat)*3+self.v
        self.pal=PALETTES[self.v];self.solids=[];self.lights=[]
        if name=='family_table':
            self.inlay(3.28,5.86,'#dcc1a1','#7d6656',False)
        elif name=='family_booth':
            self.inlay(2.27,2.86,'#d9b99b','#9d725e',False)
        elif name=='reading_nook':
            self.inlay(4.41,3.69,'#738376','#d9c8aa',True)
        elif name=='tasting_bar':
            self.inlay(2.62,4.58,'#cebe9e','#8c745e',False)
        getattr(self,name)()
    def space(self,p):
        x,y,z=p;c=math.cos(self.angle);s=math.sin(self.angle)
        return (self.offset[0]+c*x+s*z,self.offset[1]+y,self.offset[2]-s*x+c*z)
    def face(self,points,col,mat=MATT,uv=None):
        super().face([self.space(p) for p in points],col,mat,uv)
    def collision(self,x,y,z,w,h,d):
        self.solids.append({'p':self.space((x,y,z)),'size':[w,h,d],'yaw':self.angle})
    def place(self,x,z,a=0):
        self.offset=(x,0,z);self.angle=a
    def fixed_box(self,x,y,z,w,h,d,c,mat=MATT):
        self.box(x,y,z,w,h,d,c,mat);self.collision(x,y,z,w,h,d)
    def inlay(self,w,d,tint,trim,loom):
        # Finish-only tiles/rug. The existing structural slab takes all loads.
        self.box(0,.015,0,w,.030,d,tint)
        self.box(0,.0308,-d*.5+.072,w-.12,.0014,.028,trim)
        self.box(0,.0308,d*.5-.072,w-.12,.0014,.028,trim)
        for sign in (-1,1):
            self.box(sign*(w*.5-.078),.0308,0,.026,.0014,d-.13,trim)
        if loom:
            for j in range(13):
                x=-w*.42+j*w*.07
                for sign in (-1,1):
                    a=(x-.070,.032,sign*d*.42);b=(x,.032,sign*(d*.42-.083));c=(x+.070,.032,sign*d*.42)
                    self.tube(a,b,.009,trim,MATT);self.tube(b,c,.009,trim,MATT)
        else:
            for j in range(1,max(2,round(d/.95))):
                z=-.5*d+j*d/max(2,round(d/.95));self.box(0,.0304,z,w-.20,.001,.006,trim)
    def spindle_chair(self,x,z,a=0):
        self.place(x,z,a)
        for px in [-.211,.211]:
            for pz in [-.19,.19]:self.tube((px*1.09,.045,pz*1.09),(px*.81,.462,pz*.86),.022,oak,MATT)
        self.profile(0,.432,0,[(0,.213),(.044,.261),(.061,.25)],'#b57f65',(1.1,.97),18)
        # Continuous curved back with individual wood spindles.
        prev=None
        for i in range(13):
            a=math.radians(31+118*i/12)
            q=(.29*math.cos(a),.749+.044*math.sin(a),-.26*math.sin(a))
            if prev:self.tube(prev,q,.033,oak,MATT)
            if i in (0,3,6,9,12): self.tube((q[0]*.93,.48,q[2]*.86),q,.019,oak,MATT)
            prev=q
        self.collision(0,.398,0,.53,.797,.465)
        self.place(0,0)
    def setting(self,x,z,angle=0,glass=True):
        self.place(x,z,angle)
        self.box(0,.765,0,.38,.006,.263,'#b5a287')
        self.profile(0,.768,0,[(0,.067),(.012,.077),(.025,.118),(.032,.123),(.033,.115),(.018,.081)],'#eddfbf',(1,1),20)
        for xx in [-.151,.149]:self.box(xx,.781,.006,.008,.010,.182,steel,METAL)
        if glass:self.profile(.148,.768,-.10,[(0,.029),(.015,.034),(.104,.038),(.104,.032),(.083,.032)],'#b6b7a4',sides=14)
        self.place(0,0)
    def shade(self,x,y,z,r,c):
        self.profile(x,y,z,[(0,r),(.028,r),(.08,r*.85),(.18,r*.29),(.21,r*.19)],c,sides=28)
        self.profile(x,y-.005,z,[(0,r*.91),(.01,r*.91)],'#f9d39c',sides=28,mat=LAMP)
        self.lights.append({"p":[x,y-.085,z],"color":"#ffe5c6","energy":.52,"range":3.2})
    def family_table(self):
        # Six seats and an appliance-free short end with knee space.
        self.box(0,.739,0,1.27,.05,4.28,oak)
        for z in [-1.4,1.4]:
            self.fixed_box(0,.36,z,.67,.714,.17,'#5a4b44')
            self.fixed_box(0,.08,z,.91,.16,.40,oak)
        self.collision(0,.741,0,1.27,.055,4.28)
        self.box(0,.767,0,.291,.006,4.19,'#687b64')
        for z in [-1.50,-.52,.52,1.50]:
            # Alternate toned table settings along the runner.
            for sign in [-1,1]:
                self.spindle_chair(sign*.97,z,sign*-math.pi/2)
                self.setting(sign*.39,z,sign*-math.pi/2,glass=abs(z)<1)
        for z in [-1.04,1.04]:
            self.profile(0,.766,z,[(0,.078),(.09,.092),(.19,.039),(.22,.033)],'#a8754d',sides=20)
            for i in range(4):
                a=i*TAU/4
                self.tube((0,.98,z),(.1*math.cos(a),1.16+.03*i,z+.09*math.sin(a)),.011,'#748569',MATT)
        # Floor-anchored service gantry. Long view remains open between the posts.
        for z in [-2.37,2.37]:
            self.fixed_box(0,1.23,z,.075,2.46,.075,'#464744',METAL)
            self.box(0,.017,z,.19,.034,.18,steel,METAL)
        self.box(0,2.457,0,.088,.097,4.83,'#464744',METAL)
        for z in [-1.36,0,1.36]:
            self.tube((0,2.42,z),(0,2.11,z),.013,coal)
            self.shade(0,1.91,z,.265,'#824f41')
    def booth_segment(self,x,z,a=0):
        self.place(x,z,a)
        self.fixed_box(0,.17,0,1.56,.34,.49,oak)
        self.box(0,.413,.025,1.61,.152,.54,'#b77a5d')
        self.fixed_box(0,.72,-.226,1.64,.635,.15,'#935d4b')
        for j in range(9):self.box(-.70+j*.176,.73,-.145,.012,.49,.008,'#b17c60')
        self.place(0,0)
    def family_booth(self):
        # Opposed benches stand across a rounded square table.
        self.booth_segment(0,-.84,0);self.booth_segment(0,.84,math.pi)
        self.profile(0,.712,0,[(0,.625),(.045,.64)],cream,(1.21,.76),28)
        self.fixed_box(0,.351,0,.24,.702,.24,steel,METAL);self.collision(0,.735,0,1.43,.052,.84)
        for x in [-.38,.38]:
            for z in [-.26,.26]:self.setting(x,z,0 if z<0 else math.pi)
        self.profile(0,.758,0,[(0,.059),(.12,.075),(.18,.045)],'#668b78')
        self.place(-.90,-.05)
        self.fixed_box(0,.62,0,.065,1.24,2.26,oak)
        for z in [-.94,-.68,-.42,-.16,.10,.36,.62,.88]:
            self.box(0,1.43,z,.052,.42,.057,'#88765b')
        self.box(0,1.657,0,.07,.048,2.26,oak);self.place(0,0)
    def host_station(self):
        self.fixed_box(0,.39,0,1.62,.78,.67,'#675344')
        self.box(0,.813,0,1.70,.063,.73,cream)
        for i in range(16):self.box(-.75+i*.099,.45,.344,.020,.59,.024,oak)
        self.box(.38,1.065,-.09,.58,.44,.042,'#464744')
        self.card(.38,1.065,-.067,.54,.39)
        self.profile(-.45,.85,.04,[(0,.116),(.235,.14),(.25,.115)],'#a79778')
        for i in range(4):
            x=-.45+.09*math.sin(i*1.57)
            self.tube((-.45,1.1,.04),(x,1.40+.035*i,.04+.11*math.cos(i*1.57)),.016,'#6c8267',MATT)
    def reading_nook(self):
        # A curved, low library banquette and two occasional tables; open ends
        # permit entering from the central aisle. Each segment has its own collider.
        for i in range(7):
            a=math.radians(-65+i*21.7); x,z=1.57*math.sin(a),-1.57*math.cos(a)
            self.place(x,z,-a)
            self.fixed_box(0,.22,0,.601,.44,.625,'#69776a')
            self.box(0,.459,.035,.609,.116,.62,'#99a18b')
            self.fixed_box(0,.722,-.263,.61,.496,.14,'#718276')
            self.place(0,0)
        for x,z,r in [(-.58,-.12,.38),(.45,.12,.326)]:
            self.profile(x,.038,z,[(0,.13),(.03,.17),(.075,.063),(.41,.055)],'#805f49',mat=METAL)
            self.profile(x,.449,z,[(0,r),(.032,r*1.019)],'#cec0a6',sides=26)
            self.collision(x,.252,z,r*1.68,.50,r*1.68)
            self.object(x,.487,z,.92,0)
        self.fixed_box(-1.70,.37,.31,.48,.74,.44,oak)
        self.box(-1.70,.832,.28,.43,.34,.07,coal);self.card(-1.70,.837,.32,.39,.29)
        self.profile(1.61,0,.04,[(0,.219),(.039,.219),(.068,.059),(1.37,.023)],gold,mat=METAL)
        self.shade(1.61,1.31,.04,.265,'#c5a67d')
        self.collision(1.61,.68,.04,.11,1.36,.11)
    def tasting_bar(self):
        # Oak tasting rail, tiled counter, stack of cups and counter-mounted drippers.
        self.fixed_box(0,.456,0,.92,.912,3.26,'#52665b')
        self.box(0,.944,0,1.08,.069,3.43,'#d4c7b4')
        for j in range(17):self.box(.468,.50,-1.54+.19*j,.017,.74,.021,oak)
        for z in [-1.18,-.39,.40,1.19]:
            self.profile(.93,.019,z,[(0,.219),(.028,.219),(.05,.048),(.572,.036)],gold,mat=METAL)
            self.profile(.93,.591,z,[(0,.182),(.041,.222),(.078,.224)],'#94775e',sides=24)
            self.collision(.93,.34,z,.425,.68,.425)
            self.object(.26,.983,z,.87,0)
        for z in [-.97,-.312,.327]:
            self.box(-.16,1.015,z,.23,.072,.26,oak)
            self.tube((-.24,1.05,z+.05),(-.24,1.35,z+.05),.010,gold)
            self.tube((-.24,1.35,z+.05),(-.12,1.35,z+.05),.010,gold)
            self.profile(-.12,1.245,z+.05,[(0,.019),(.12,.084),(.123,.073),(.036,.018)],cream)
            self.profile(-.12,1.05,z+.05,[(0,.054),(.112,.057),(.139,.043)],'#b3ac94')
        self.place(0,0)
        self.box(-.18,1.27,1.02,.44,.56,.043,oak);self.card(-.18,1.27,1.047,.40,.517)
    def pastry_cart(self):
        self.fixed_box(0,.453,0,1.62,.866,.687,oak)
        self.box(0,.912,0,1.70,.051,.73,cream)
        for i in range(5):
            x=-.63+i*.307
            self.object(x,.939,.02,1.03,1+i%2)
        for x in [-.795,.795]:
            for z in [-.32,.32]:
                self.tube((x,.94,z),(x,1.294,z),.014,gold)
        self.box(0,1.31,0,1.70,.036,.72,oak)
        self.box(0,1.29,.302,1.5,.011,.021,cream,LAMP)
        for i in range(11):self.box(-.73+i*.14,.49,.35,.032,.61,.023,oak)

def main():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
    # X/Z locations in authoritative C sales coordinates. Clear 2.4 m public
    # centreline, kitchen, checkout and both perimeter table rows.
    layouts={
        'C2F-CSE-3':[(41.6,-183.3,0,'family_table'),(30.3,-186.5,-.18,'family_booth'),
                     (30.4,-179.1,.22,'family_booth'),(41.6,-191.4,-.17,'host_station')],
        'C3F-CSE-3':[(30.7,-184.1,-.28,'reading_nook'),(41.8,-181.8,0,'tasting_bar'),(41.4,-190.8,-.19,'pastry_cart')]}
    rooms=[];model_info={}
    for sid,rows in layouts.items():
        wing='C'; floor='2F' if sid.startswith('C2') else '3F'; height=5.525 if floor=='2F' else 10.875
        r=dict(id=sid,floor=floor,wing=wing,placements=[])
        for i,(x,z,yaw,name) in enumerate(rows):
            m=Dining(name)
            if name not in model_info:
                m.save(out/('room-'+name+'.bin'))
                model_info[name]=dict(solids=m.solids,lights=m.lights)
            r['placements'].append(dict(role=name+'-'+str(i),program=name,p=[x,height+.002,z],yaw=yaw,width=4.))
        rooms.append(r)
    (ROOT/'source/v36/dining-programs.json').write_text(json.dumps({'rooms':rooms,'models':model_info},separators=(',',':'))+'\n')
if __name__=='__main__':main()
