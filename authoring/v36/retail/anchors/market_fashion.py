"""Original floor-based food departments and fashion display programs."""
from collections import defaultdict
from math import sin,cos,pi,atan2
from dining_rooms import Dining
from model import MATT,METAL,LAMP
from art import CATEGORIES,PALETTES

oak='#a78160';brass='#ac9570';milk='#eee5ce';steel='#aab4ae';cloth='#f0e3c9';forest='#3c6054'
class Department(Dining):
    def __init__(self,name):
        self.name=name;self.data=defaultdict(bytearray);self.offset=(0,0,0);self.angle=0
        self.cat='food' if name.startswith('market') else 'apparel'
        self.v=0;self.print_id=list(CATEGORIES).index(self.cat)*3
        self.pal=PALETTES[3 if self.cat=='food' else 1];self.solids=[];self.lights=[];self.posters=[]
        getattr(self,name)()
        if self.cat=="food":self.market_pavilion(name=="market_produce")
        else:self.fashion_salon(name=="fashion_lookbook")
    def ad(self,x,y,z,w,tile):
        h=w*4./3.
        self.fixed_box(x,y,z-.043,w+.072,h+.072,.076,oak)
        self.posters.append(dict(p=[x,y,z],width=w,height=h,yaw=0.,tile=tile))
    def legs(self,x,y,z,w,d):
        for a in [-1,1]:
            for b in [-1,1]:
                self.fixed_box(x+a*(w*.5-.09),y*.5,z+b*(d*.5-.09),.065,y,.065,'#555955',METAL)
    def kiosk_sign(self,x,z,tile,w=.65,bottom=1.50):
        for d in [-1,1]:
            self.fixed_box(x+d*(w*.42),bottom/2,z-.04,.048,bottom,.048,brass,METAL)
        self.ad(x,bottom+w*2/3,z,w,tile)
    def fruit(self,x,y,z,kind,s):
        if kind==0:  # apple with recessed crown
            self.profile(x,y,z,[(0,.032*s),(.035*s,.076*s),(.098*s,.089*s),(.142*s,.068*s),(.151*s,.027*s)],'#bd624e',(.96,1.05),12)
            self.tube((x,y+.147*s,z),(x+.012*s,y+.184*s,z),.004*s,'#786551',MATT)
        elif kind==1:  # aubergine and folded calyx
            self.profile(x,y,z,[(0,.027*s),(.03*s,.062*s),(.080*s,.071*s),(.18*s,.042*s),(.202*s,.023*s)],'#595366',(1.02,.87),12)
            self.profile(x,y+.182*s,z,[(0,.045*s),(.031*s,.021*s),(.063*s,.009*s)],'#62745a',sides=10)
        elif kind==2:  # deeply ridged squash
            self.profile(x,y,z,[(0,.035*s),(.028*s,.088*s),(.088*s,.112*s),(.147*s,.069*s),(.158*s,.032*s)],'#cb8a42',(1.18,1.),14)
            self.profile(x,y+.153*s,z,[(0,.018*s),(.045*s,.009*s)],'#747d54',sides=7)
        else:  # cabbage: overlapping leaves
            self.profile(x,y,z,[(0,.035*s),(.04*s,.088*s),(.116*s,.098*s),(.161*s,.065*s),(.168*s,.031*s)],'#93a463',(1.05,.95),13)
            for k in range(3):
                a=k*2*pi/3;self.profile(x+.062*s*sin(a),y+.015*s,z+.05*s*cos(a),[(0,.018*s),(.048*s,.048*s),(.108*s,.042*s),(.134*s,.017*s)],'#779866',(.83,1),8)
    def crate(self,x,y,z,w,d,kind):
        self.box(x,y+.018,z,w,.036,d,oak)
        for k in [-1,1]:
            self.box(x+k*(w*.5-.016),y+.080,z,.032,.125,d,oak)
            self.box(x,y+.069,z+k*(d*.5-.017),w,.100,.034,'#ba956f')
        for j in range(2):
            n=4 if w>.95 else 3
            for i in range(n):
                xx=x+(i-(n-1)*.5)*(w-.22)/(n-.35)+.014*((i+j+kind)%3)
                zz=z+(j-.5)*d*.37+.017*(i%2)
                self.fruit(xx,y+.036,zz,kind,.85+.12*((i+j+kind)%3))
        # Folded paper stock card clipped to front face.
        self.box(x+.20*w,y+.079,z+d*.5+.002,.124,.058,.006,milk)
        self.box(x+.20*w,y+.078,z+d*.5+.006,.082,.006,.002,'#506456')
    def market_produce(self):
        self.inlay(6.54,4.05,'#d4c5a4','#877c59',False)
        # Produce table steps down toward the main aisle; the canopy outline
        # and commissioned seasonal campaign make the department legible at distance.
        for x in [-2.72,-.20]:
            self.fixed_box(x,1.17,-.86,.085,2.34,.085,forest)
            self.box(x,.024,-.86,.26,.048,.23,steel,METAL)
        self.fixed_box(-1.46,2.40,-.75,2.75,.14,.42,forest)
        for i in range(15):
            xx=-2.81+i*.19
            self.box(xx,2.40,-.42,.11,.054,.50,oak)
        self.box(-1.45,2.344,-.595,2.54,.022,.037,'#fbecd0',LAMP)
        for row,yy in enumerate([.48,.74,.99]):
            zz=.91-row*.65
            self.fixed_box(-1.36,yy/2,zz,2.63,yy,.61,'#b09b79')
            self.crate(-2.03,yy,zz,1.25,.60,(3-row)%4)
            self.crate(-.71,yy,zz,1.20,.60,row)
        self.kiosk_sign(2.23,-.98,0,.83,1.22)
        self.fixed_box(1.68,.34,.25,1.47,.68,.79,forest)
        self.fixed_box(1.68,.716,.25,1.56,.072,.86,oak)
        self.crate(1.68,.752,.24,1.32,.70,0)
        self.profile(2.90,0,.32,[(0,.24),(.06,.26),(.40,.31),(.51,.32)],'#bb9674',sides=20)
        for i in range(5):
            a=i*2*pi/5;self.fruit(2.90+.15*sin(a),.452,.32+.15*cos(a),3,1.0)
        self.collision(2.90,.25,.32,.51,.50,.51)
        self.lights.append(dict(p=[-1.43,2.27,-.57],color='#ffe5bc',energy=.45,range=4.0))
    def deli_tray(self,x,y,z,kind):
        self.box(x,y+.026,z,.64,.052,.38,steel,METAL)
        for a in [-1,1]:
            self.box(x+a*.303,y+.063,z,.032,.068,.38,steel,METAL)
            self.box(x,y+.063,z+a*.17,.64,.066,.025,steel,METAL)
        if kind==1:
            for j in range(5):self.profile(x-.23+j*.105,y+.053,z,[(0,.057),(.034,.070),(.062,.043),(.070,.018)],'#c29460',(.63,1.55),12)
        elif kind==2:
            for j in range(5):self.profile(x-.23+j*.105,y+.053,z,[(0,.054),(.032,.069),(.046,.057)],'#bf8a77',(.66,1.64),12)
        else:
            for j in range(9):
                self.profile(x-.23+(j%5)*.104,y+.054,z+(-.059 if j//5 else .052),[(0,.035),(.036,.050),(.049,.029)],'#7c9258',sides=10)
    def market_deli(self):
        self.inlay(6.52,4.03,'#b8bdab','#737f72',False)
        self.fixed_box(-.40,.415,.44,4.20,.83,1.02,forest)
        for j in range(20):
            self.box(-2.39+j*.210,.446,.969,.052,.685,.028,'#81917a')
        self.fixed_box(-.40,.875,.44,4.30,.09,1.09,'#d6d4c3')
        for i in range(5):
            self.deli_tray(-2.08+i*.82,.921,.51,(i+2)%3)
            self.box(-2.09+i*.82,.935,.887,.176,.026,.071,milk)
        # Glass canopy is represented by its stainless rim and shallow acrylic
        # lid sections in the shader-independent shared kit; the line stays open.
        for x in [-2.48,1.67]:self.fixed_box(x,1.144,.04,.051,.45,.051,steel,METAL)
        self.fixed_box(-.40,1.39,.19,4.24,.079,.44,steel,METAL)
        self.box(-.40,1.351,.348,4.05,.010,.023,'#fff0d9',LAMP)
        self.kiosk_sign(2.48,-.72,1,.75,1.22)
        self.fixed_box(-.77,.39,-1.58,2.49,.78,.60,'#ada795')
        self.fixed_box(-.77,.818,-1.58,2.59,.076,.66,steel,METAL)
        for i in range(3):
            self.box(-1.52+i*.69,.992,-1.59,.40,.34,.13,milk)
            self.box(-1.52+i*.69,.993,-1.519,.26,.17,.008,'#7f8a83')
        self.lights.append(dict(p=[-.4,1.32,.37],color='#f8eddb',energy=.42,range=2.9))
    def torso(self,x,base,z,kind,color):
        # Shop dress form: shaped waist/bust/shoulder on a real stand. Neck
        # collar and hanger socket distinguish it visibly from a character.
        self.profile(x,base,z,[(0,.22),(.035,.22),(.055,.036),(.79,.024)],brass,(1,.8),18,METAL)
        if kind==0:
            rings=[(.75,.24),(.83,.225),(1.04,.16),(1.21,.20),(1.33,.229),(1.43,.17),(1.50,.087)]
        else:
            rings=[(.56,.31),(.72,.26),(1.02,.151),(1.20,.19),(1.34,.21),(1.42,.17),(1.48,.067)]
        self.profile(x,base,z,rings,color,(1,.69),24)
        for a in [-1,1]:
            self.tube((x+a*.18,base+1.34,z),(x+a*.276,base+1.09,z+.018),.076,color,MATT)
        self.profile(x,base+1.42,z,[(0,.10),(.12,.070),(.14,.068)],'#dfc9a3',(1,.88),16)
        if kind:
            self.profile(x,base+1.006,z,[(0,.159),(.046,.169)],brass,(1,.71),18)
        else:
            self.box(x,base+1.19,z+.124,.018,.28,.014,milk)
        self.collision(x,base+.74,z,.48,1.48,.33)
    def rail(self,x,z,n=5):
        for xx in [x-1.06,x+1.06]:
            self.fixed_box(xx,.034,z,.19,.068,.65,brass,METAL)
            self.fixed_box(xx,.856,z,.047,1.70,.047,brass,METAL)
        self.fixed_box(x,1.716,z,2.16,.040,.040,brass,METAL)
        for i in range(n):
            xx=x+(-.86+1.72*i/(n-1)); k=i%3; c=['#9a655b','#a7afa0','#aea0a7','#566771','#d0bd98'][i%5]
            points=[(-.07,0),(-.155,-.038),(-.205,-.20),(-.151,-.225),(-.111,-.163),(-.14,-.58-.08*k),(.14,-.58-.08*k),(.116,-.167),(.167,-.225),(.218,-.19),(.148,-.04),(.073,0),(0,-.064)]
            self.silhouette([(xx+dx,1.62+dy) for dx,dy in points],(z,.049),c)
            self.tube((xx-.115,1.595,z),(xx,1.653,z),.009,oak,MATT)
            self.tube((xx,1.653,z),(xx+.115,1.595,z),.009,oak,MATT)
            self.tube((xx,1.653,z),(xx,1.72,z),.006,steel)
            if k==1:self.box(xx,1.374,z+.026,.014,.34,.005,'#ddc7b4')
    def fashion_lookbook(self):
        self.inlay(6.50,4.02,'#a6a89c','#e1d9c8',False)
        # Three-dimensional window installation, viewed in the round instead
        # of a frontal stock wall. A tall printed textile screens the back.
        self.fixed_box(-1.35,.102,.15,2.77,.204,1.74,oak)
        self.fixed_box(-1.87,.24,-.06,1.0,.12,.88,'#dad5c8')
        self.torso(-1.86,.30,-.06,1,'#657783')
        self.torso(-.80,.204,.49,0,'#a47970')
        for x in [-2.51,-.41]:self.fixed_box(x,1.22,-1.44,.061,2.44,.061,brass,METAL)
        self.fixed_box(-1.46,2.456,-1.44,2.18,.064,.065,brass,METAL)
        self.fixed_box(-1.46,1.448,-1.44,1.81,1.99,.052,'#c6baab')
        self.ad(-1.46,1.48,-1.40,1.30,0)
        self.rail(1.67,-.46)
        self.lights.append(dict(p=[-1.15,2.37,-.64],color='#ffebd5',energy=.49,range=3.))
    def fashion_atelier(self):
        self.inlay(6.52,4.04,'#bfc3ba','#8a938a',False)
        # Fabric/sample consultation table and standing length mirror. Only the
        # seamstress work surface carries folded fabric; garment rail is separate.
        self.legs(-1.41,.79,.14,2.52,1.00)
        self.fixed_box(-1.41,.824,.14,2.65,.068,1.07,oak)
        for j in range(5):
            self.box(-2.30+j*.41,.872,.20,.35,.025,.42,['#6d8282','#ad8d77','#9e6972','#bdb09d','#697079'][j])
            self.box(-2.31+j*.41,.890,.37,.17,.006,.076,milk)
        for j in range(3):
            x=-2.28+j*.45
            self.box(x,.884,-.16,.34,.053,.18,cloth)
            self.box(x,.929,-.16,.31,.04,.17,'#9da9a7')
        self.rail(1.55,.05,4)
        self.kiosk_sign(-2.47,-1.37,1,.67,1.08)
        self.pillar_mirror(.12,-1.52)
        self.lights.append(dict(p=[.0,2.26,-.72],color='#ffe6d3',energy=.44,range=3.05))
    def pillar_mirror(self,x,z):
        self.fixed_box(x,.046,z,.91,.092,.47,'#858b80')
        self.fixed_box(x,1.04,z,.67,1.94,.064,brass,METAL)
        self.box(x,1.045,z+.035,.603,1.84,.012,'#c6d6d6',METAL)

    def market_pavilion(self,produce):
        # Each department is a free-standing market hall stall. Two splayed
        # timber returns and a public-facing fascia make the sales edge legible.
        for sign in [-1,1]:
            self.fixed_box(sign*3.14,1.335,-1.79,.17,2.67,.17,oak)
            self.fixed_box(sign*3.14,.075,-1.72,.36,.15,.54,'#576254',METAL)
            self.fixed_box(sign*3.14,1.33,-.39,.108,2.66,.108,forest)
            self.fixed_box(sign*3.14,.045,-.39,.22,.09,.23,steel,METAL)
            self.fixed_box(sign*3.14,2.669,-1.05,.17,.13,1.62,oak)
        self.fixed_box(0,2.682,-1.75,6.38,.135,.20,oak)
        self.fixed_box(0,2.69,-.35,6.43,.22,.18,forest)
        self.box(0,2.59,-.241,6.31,.022,.024,brass,METAL)
        self.box(0,2.575,-.38,6.17,.018,.046,'#fff0db',LAMP)
        if produce:
            # Woven canvas awning over the produce department; the shallow
            # scalloped edges are visible from the shop entrance at eye level.
            for i in range(19):
                x=-3.03+i*.337;col='#d5ad76' if i%2 else '#7f986f'
                xa,xb=x-.167,x+.167
                self.face([(xa,2.71,-1.68),(xa,2.49,-.08),(xb,2.49,-.08),(xb,2.71,-1.68)],col)
                self.face([(xb,2.702,-1.68),(xb,2.482,-.08),(xa,2.482,-.08),(xa,2.702,-1.68)],'#e5d4b5')
                self.silhouette([(xa,2.51),(xb,2.51),(xb,2.404),(x+.097,2.345),(x-.097,2.345),(xa,2.404)],(-.076,.019),col)
            self.fixed_box(-1.31,1.36,-1.842,3.46,2.57,.091,'#526d59')
            for i in range(18):
                self.box(-2.90+i*.182,1.34,-1.78,.065,2.4,.036,'#829170' if i%3 else oak)
            self.fixed_box(1.93,.37,-1.84,2.18,.74,.13,forest)
            for x in [1.06,2.83]:self.fixed_box(x,1.37,-1.84,.090,2.57,.10,oak)
            for y in [.98,1.39,2.17]:self.box(1.94,y,-1.82,1.82,.041,.09,oak)
        else:
            # Tiled deli backbar with wall returns, peg rails and pitched timber
            # acoustic baffles. Framing and steel pass are distinct from produce.
            self.fixed_box(0,1.30,-1.90,6.21,2.60,.125,'#b4c0aa')
            for y in [.47,.84,1.21,1.58,1.95,2.32]:
                self.box(0,y,-1.832,6.15,.013,.013,'#83978a')
            for i in range(17):
                x=-3.0+i*.37
                self.box(x,1.32,-1.827,.012,2.46,.014,'#83978a')
            for i in range(12):
                self.box(-2.89+i*.52,2.62,-1.06,.061,.12,1.23,oak)
            self.box(0,2.534,-.62,5.95,.019,.023,'#fae9cc',LAMP)
            for x,h in [(-2.05,1.94),(-.37,1.94)]:
                self.fixed_box(x,h,-1.67,1.34,.054,.25,steel,METAL)
                for j in range(6):
                    self.profile(x-.51+j*.195,h+.026,-1.68,[(0,.056),(.132,.063),(.145,.047)],'#c8b994' if j%2 else '#a17058',sides=12)
    def fashion_salon(self,lookbook):
        # The apparel threshold is a tailored, recessed fabric wall and
        # independent joinery portal; front suspension hardware joins the uprights.
        wrap='#657b78' if lookbook else '#967670'
        fibre='#d9d4bd' if lookbook else '#c8b5a3'
        self.fixed_box(0,1.34,-1.915,6.24,2.68,.13,wrap)
        self.box(0,.16,-1.829,6.19,.27,.055,'#716a5d')
        for i in range(8):
            xx=-2.76+i*.79
            self.box(xx,1.36,-1.825,.750,2.23,.047,fibre)
            self.box(xx-.336,1.36,-1.793,.013,2.18,.012,'#b9aa95')
        for sign in [-1,1]:
            x=3.15*sign
            self.fixed_box(x,1.34,-1.18,.165,2.68,1.41,wrap)
            self.box(x+sign*.092,1.36,-1.16,.018,2.38,1.21,brass,METAL)
            self.fixed_box(x,1.32,-.38,.17,2.64,.25,oak)
            self.box(x,1.35,-.242,.035,2.41,.017,'#ead6aa',LAMP)
        if lookbook:
            # Shallow elliptical eyebrow rises over the mannequins and draws
            # the eye from the main aisle to the shop's two editorial bays.
            coords=[]
            for i in range(25):
                x=-3.20+i*6.4/24
                a=(i/24)*pi
                coords.append((x,2.53+.245*sin(a),-.37+.34*sin(a)))
            for a,b in zip(coords[:-1],coords[1:]):
                self.face([a,b,(b[0],b[1]-.113,b[2]),(a[0],a[1]-.113,a[2])],wrap)
                self.face([(a[0],a[1],-1.82),a,b,(b[0],b[1],-1.82)],fibre)
                self.face([(b[0],b[1]-.118,-1.82),(b[0],b[1]-.118,b[2]),(a[0],a[1]-.118,a[2]),(a[0],a[1]-.118,-1.82)],'#b5aa94')
                self.tube((a[0],a[1]-.123,a[2]),(b[0],b[1]-.123,b[2]),.014,brass,METAL)
        else:
            # Full-height drapery backdrop for fabric consultation, plus a narrow
            # slatted ceiling band. Cloth silhouette reads from across the floor.
            for i in range(22):
                x=-1.39+i*.2
                self.profile(x,.19,-1.70,[(0,.10),(1.05,.102),(2.30,.103)],'#b5a292' if i%2 else '#a29287',(1.04,.49),12)
            self.fixed_box(0,2.69,-.66,6.43,.154,1.06,wrap)
            for i in range(32):
                self.box(-3.06+i*.2,2.595,-.66,.04,.05,.94,'#c4b49a')
            self.box(0,2.595,-.125,6.11,.024,.033,'#ffead4',LAMP)
