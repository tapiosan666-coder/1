"""Original ticket office and poster lounge for the upper-floor CERAVA cinema.
Both programs face local +Z. Units are metres. Imported by the anchor baker.
"""
from collections import defaultdict
from math import cos, sin, pi, hypot
from dining_rooms import Dining
from model import MATT, METAL, LAMP

INK = '#293631'
GREEN = '#385348'
BRASS = '#b59a6b'
LINEN = '#efe1c4'
CHERRY = '#794951'
VELVET = '#9d6268'
DARK = '#41383c'
OAK = '#967458'

# Original single-stroke capitals. Geometry keeps the flat-cut sign lettering
# sharp close to the booth without loading any typeface or extra material.
ALPHABET = {
    'A':('001406','1343'), 'B':('000646553443032330414000',),
    'C':('45560601004051',),'D':('00063655514000',),
    'E':('46060040','0333'), 'F':('000646','0333'),
    'G':('455606010040515323',),'H':('0006','5056','0353'),
    'I':('0646','2600','0040'), 'K':('0006','465300','2340'),
    'L':('060040',),'M':('0006254650',),'N':('00065056',),
    'O':('104051554616050110',),'P':('00063645544303',),
    'R':('00063645544303','2340'),'S':('45461605041442515010',),
    'T':('0656','2620'),'U':('060110405156',),
    'V':('06102056',),'W':('0601234156',),'X':('0650','0056'),
    'Y':('062356','2320'), '0':('104051554616050110','1145'),
    '1':('15262620','1040'), '2':('0516465554421040',),
    '3':('051646555443235342514010',), '4':('3643035350','3630'),
    '5':('4606033352514010',), '6':('354616050110405152432303',),
    '7':('065620',), '8':('10405152432314050616465554432314030110',),
    '9':('4151554616050414435450',), ':':('2425','2122')
}
# Use polylines with a local descent/ascent in a 5 × 6 glyph grid.
ALPHABET.update({'A':('002650','1343'), 'I':('0656','2620','0050'),
                 'K':('0006','4603','2340'), 'B':('0006364554430303','034352514000'),
                 'F':('000646','0333'), 'M':('0006234650',)})


class Cinema(Dining):
    def __init__(self, name):
        self.data = defaultdict(bytearray)
        self.solids, self.lights, self.posters = [], [], []
        self.name = name
        self.place(0, 0)
        getattr(self, name)()
        self.architectural_bay(name == "cinema_lounge")

    def rounded(self, x, z, y0, y1, width, depth, radius, color, material=MATT):
        """Extruded radiused plan with a closed top and bottom."""
        hx, hz = width / 2, depth / 2
        r = min(hx, hz, radius)
        pts = []
        for cx, cz, start in ((hx-r,hz-r,0),(-hx+r,hz-r,90),
                              (-hx+r,-hz+r,180),(hx-r,-hz+r,270)):
            for step in range(7):
                a = (start + 15*step)*pi/180
                pts.append((x + cx+r*cos(a), z + cz+r*sin(a)))
        top = [(a,y1,b) for a,b in pts]
        bottom = [(a,y0,b) for a,b in pts]
        self.face(top[::-1],color,material)
        self.face(bottom,color,material)
        for i in range(len(pts)):
            j=(i+1)%len(pts)
            self.face([top[i],top[j],bottom[j],bottom[i]],color,material)

    def legend(self, label, x, y, z, height, color=LINEN, material=MATT):
        """Centered readable geometric lettering, all signs face +Z."""
        scale=height/6
        step=scale*7.55
        start=x-(len(label)-1)*step/2-2.5*scale
        for idx,char in enumerate(label):
            if char==' ':
                continue
            for path in ALPHABET[char]:
                xy=[(start+idx*step+scale*int(path[i]),
                     y+(int(path[i+1])-3)*scale) for i in range(0,len(path),2)]
                for (x1,y1),(x2,y2) in zip(xy,xy[1:]):
                    dx,dy=x2-x1,y2-y1
                    extent=hypot(dx,dy)
                    if extent<1e-7:
                        continue
                    w=scale*.355
                    ex,ey=w*dx/extent,w*dy/extent
                    nx,ny=-ey,ex
                    self.face([(x1-ex-nx,y1-ey-ny,z),(x2+ex-nx,y2+ey-ny,z),
                               (x2+ex+nx,y2+ey+ny,z),(x1-ex+nx,y1-ey+ny,z)],color,material)

    def curtain(self, x, z, width, height):
        """A single continuous pleated acoustic panel behind the lightboxes."""
        n=max(12,round(width/.08))
        for i in range(n):
            x0=x+width*(i/n-.5)
            x1=x+width*((i+1)/n-.5)
            z0=z+.035*(i%2)
            z1=z+.035*((i+1)%2)
            self.face([(x0,.14,z0),(x1,.14,z1),(x1,height,z1),(x0,height,z0)],
                      '#60464a' if i%2 else '#704e53')

    def deck(self,w,d):
        self.rounded(0,0,.0005,.010,w,d,.24,'#6e6662')
        self.rounded(0,0,.010,.012,w-.075,d-.075,.21,'#ad9270')
        self.rounded(0,0,.012,.014,w-.105,d-.105,.20,'#665b59')

    def architectural_bay(self, lounge):
        # An independent shell whose posts and supporting edge beams visibly
        # run to the existing slab. All public entrance approaches stay open.
        front = 1.35 if lounge else .91
        for side in (-1, 1):
            x = side*3.15
            self.fixed_box(x,.12,front-.09,.19,.22,.20,DARK,METAL)
            self.fixed_box(x,1.43,front-.09,.11,2.46,.14,BRASS,METAL)
            self.box(x,2.595,front-.09,.225,.062,.22,OAK)
            self.fixed_box(x,1.35,-1.62,.155,2.67,.23,OAK)
            self.box(x,2.59,(front-1.80)*.5,.16,.145,front+1.82,OAK)
            # Acoustic side returns deliberately stop behind the customer.
            z0 = -.70 if lounge else -.49
            self.fixed_box(side*3.11,1.325,(-1.66+z0)*.5,.125,2.62,z0+1.67,GREEN)
            for i in range(12):
                z = -1.61+(z0+1.57)*i/11
                self.box(side*3.045,1.36,z,.073,2.48,.041,OAK if i%4 else '#aa845f')
            self.box(side*3.11,1.36,z0+.031,.147,2.53,.077,BRASS,METAL)

        # Softly vaulted acoustic plaster underside, built from a continuous
        # elliptical cross-section. Timber ribs follow the same section.
        width = 3.245
        rear = -1.885
        def underside(x):
            return 2.63+.153*(1-(x/width)**2)
        def pt(x,z,h=0):
            return (x,underside(x)+h,z)
        count = 24
        for i in range(count):
            x0=-width+i*2*width/count
            x1=-width+(i+1)*2*width/count
            self.face([pt(x0,rear),pt(x1,rear),pt(x1,front),pt(x0,front)],
                      '#c9b197' if lounge else '#d4be9c')
            self.face([pt(x0,front),pt(x1,front),pt(x1,front,.087),pt(x0,front,.087)],OAK)
            self.face([pt(x1,rear,.087),pt(x1,front,.087),pt(x0,front,.087),pt(x0,rear,.087)][::-1],
                      '#695b51')
            self.face([pt(x0,rear,.087),pt(x1,rear,.087),pt(x1,rear),pt(x0,rear)],DARK)
            self.face([pt(x0,front+.002,.049),pt(x1,front+.002,.049),
                       pt(x1,front+.002,.063),pt(x0,front+.002,.063)],BRASS,METAL)
            for z in [rear+.31, -.91, -.18, front-.54]:
                # The outboard edge of each slat casts a visible relief line.
                rib = .034 if lounge else .047
                self.face([pt(x0,z,-.015),pt(x1,z,-.015),
                           pt(x1,z+rib,-.015),pt(x0,z+rib,-.015)],OAK)
                self.face([pt(x0,z+rib,-.015),pt(x1,z+rib,-.015),
                           pt(x1,z+rib),pt(x0,z+rib)],'#9d7957')
            if 2<=i<count-2:
                zz=front-.20
                self.face([pt(x0,zz,-.010),pt(x1,zz,-.010),pt(x1,zz+.027,-.010),pt(x0,zz+.027,-.010)],
                          '#ffe1ad',LAMP)
        for sign in (-1,1):
            xx=sign*width
            self.face([pt(xx,rear),pt(xx,front),pt(xx,front,.087),pt(xx,rear,.087)],OAK)
        # The purpose of the bay is readable from the approach even before the
        # visitor reaches a ticket terminal or individual poster caption.
        self.rounded(0,front-.027,2.50,2.735,3.11,.17,.074, GREEN if lounge else '#594046')
        self.box(0,2.506,front+.060,2.90,.014,.009,BRASS,METAL)
        self.legend('CINEMA' if lounge else 'CERAVA',0,2.624,front+.061,.136,LINEN)
        for x in (-2.21,2.21):
            self.box(x,2.677,front-.30,.29,.025,.21,'#f2d5b1',LAMP)
        if not lounge:
            # A proper framed key-art portrait accompanies the programme slate
            # at the box office. It is visible over the accessible lower desk.
            self.box(-2.422,1.48,-1.493,1.185,1.622,.126,BRASS,METAL)
            self.box(-2.422,1.48,-1.410,1.105,1.536,.055,INK)
            self.posters.append({'p':[-2.422,1.48,-1.377], 'width':1.045,
                                 'height':1.3933,'yaw':0.,'tile':0})
            self.box(2.412,1.345,-1.491,.84,1.83,.16,INK)
            for i in range(10):
                self.box(2.055+i*.078,1.35,-1.396,.055,1.75,.096,OAK)
            self.box(2.412,1.947,-1.331,.75,.042,.043,BRASS,METAL)

    def terminal(self,x,z,y):
        self.rounded(x,z,y,y+.023,.38,.32,.065,INK,METAL)
        self.tube((x,y+.022,z-.02),(x,y+.225,z+.035),.034,BRASS)
        # Tilt both the bezel and the customer display. Centimetre-scale slots
        # and button groups make the counters read as transaction stations.
        self.box(x,y+.265,z,.40,.254,.052,INK)
        self.face([(x-.177,y+.159,z+.028),(x+.177,y+.159,z+.028),
                   (x+.177,y+.369,z+.076),(x-.177,y+.369,z+.076)],'#426a67')
        for i in range(2):
            self.box(x-.061,y+.229+.053*i,z+.078,.152,.012,.005,LINEN)
        self.box(x+.121,y+.242,z+.078,.055,.065,.006,'#c6b187')
        self.rounded(x+.34,z+.076,y,y+.052,.18,.23,.037,DARK)
        self.box(x+.34,y+.053,z+.071,.107,.005,.074,'#71968c')

    def cinema_box_office(self):
        self.deck(6.65,4.02)
        # The sign and its canopy are carried by two dark side pylons behind
        # the counter. The staff aisle remains open at both ends, without gates.
        for x in (-2.86,2.86):
            self.fixed_box(x,1.29,-1.57,.28,2.56,.36,INK)
            self.box(x,1.30,-1.375,.19,2.54,.036,BRASS,METAL)
        self.fixed_box(0,1.13,-1.70,5.69,2.23,.16,GREEN)
        self.curtain(0,-1.615,5.50,2.23)
        self.rounded(0,-1.46,2.35,2.70,6.29,.77,.12,INK)
        self.rounded(0,-1.46,2.690,2.725,6.34,.79,.12,BRASS,METAL)
        self.box(0,2.362,-1.064,5.98,.024,.029,'#f6dcaa',LAMP)
        self.legend('TICKETS',0,2.535,-1.070,.20,LINEN)
        for side in (-1,1):
            for j in range(5):
                self.box(side*(1.50+.262*j),2.530,-1.070,.109,.055,.015,BRASS,METAL)
        self.box(0,1.722,-1.547,3.84,.823,.12,INK)
        self.box(0,1.730,-1.481,3.76,.72,.012,'#253d39')
        self.legend('PROGRAMME',-.74,1.90,-1.469,.111,BRASS)
        self.legend('SCREEN',1.066,1.90,-1.469,.111,BRASS)
        for i,(desc,num) in enumerate([('FEATURE','01'),('SHORTS','02'),('ARCHIVE','03')]):
            yy=1.70-i*.125
            self.legend(desc,-.72,yy,-1.469,.069)
            self.legend(num,1.075,yy,-1.469,.072)
        self.box(0,1.817,-1.468,3.50,.007,.009,BRASS)
        self.rounded(.58,.30,.018,.153,4.28,.79,.17,DARK)
        self.rounded(.58,.30,.151,.939,4.42,.86,.19,GREEN)
        self.collision(.58,.479,.30,4.34,.92,.80)
        for i in range(31):
            self.box(-1.43+i*.135,.566,.728,.023,.602,.033,'#65786c')
        self.rounded(.58,.30,.936,.966,4.54,.99,.21,BRASS,METAL)
        self.rounded(.58,.30,.966,1.018,4.57,1.025,.21,'#c1ac8f')
        self.collision(.58,.976,.30,4.48,.078,.97)
        for i,xx in enumerate((-.57,1.56)):
            self.terminal(xx,.25,1.018)
            self.box(xx,.784,.752,.331,.119,.035,INK)
            self.legend('0'+str(i+1),xx,.784,.774,.071,LINEN)
        # Lower access counter: the opening beneath the surface provides knee space.
        self.fixed_box(-2.72,.39,.29,.115,.76,.71,GREEN)
        self.rounded(-2.10,.30,.751,.79,1.38,.85,.108,'#c1ac8f')
        self.collision(-2.10,.772,.30,1.36,.045,.83)
        self.box(-2.14,.808,.21,.29,.025,.22,INK)
        for x in (-1.53,1.53):
            self.box(x,2.347,-1.42,.56,.024,.14,'#f4deb5',LAMP)
            self.lights.append({'p':[x,2.33,-1.29],'color':'#ffe5bd','energy':.55,'range':3.25})

    def lounge_seat(self,x,z,a):
        self.place(x,z,a)
        self.rounded(0,0,.065,.27,.71,.64,.106,DARK)
        self.rounded(0,.034,.27,.404,.748,.717,.095,CHERRY)
        self.rounded(0,.045,.404,.463,.748,.717,.105,VELVET)
        # Curved upholstery shell; the back slopes away from a sitter.
        sections=[(.04,-.246,.365),(.042,-.302,.51),(.049,-.359,.84),
                  (.05,-.337,.93),(.044,-.305,.951),(.033,-.27,.924)]
        for (th0,zz0,h0),(th1,zz1,h1) in zip(sections,sections[1:]):
            l0,r0=(-.335,h0,zz0),(.335,h0,zz0)
            l1,r1=(-.335,h1,zz1),(.335,h1,zz1)
            self.face([l0,r0,r1,l1],VELVET)
            self.face([(-.335,h1,zz1-th1),(.335,h1,zz1-th1),(.335,h0,zz0-th0),(-.335,h0,zz0-th0)],CHERRY)
            for s in (-1,1):
                xx=.335*s
                self.face([(xx,h0,zz0),(xx,h1,zz1),(xx,h1,zz1-th1),(xx,h0,zz0-th0)],CHERRY)
        for side in (-1,1):
            self.rounded(side*.343,-.04,.394,.62,.080,.58,.036,CHERRY)
            self.rounded(side*.343,-.035,.62,.639,.084,.57,.035,'#765d49')
        self.collision(0,.479,-.009,.751,.932,.757)
        self.place(0,0)

    def cinema_lounge(self):
        self.deck(6.62,4.08)
        self.fixed_box(0,1.29,-1.67,5.87,2.54,.18,GREEN)
        self.curtain(0,-1.575,5.63,2.33)
        self.rounded(0,-1.532,2.284,2.664,6.08,.56,.106,INK)
        self.box(0,2.29,-1.247,5.82,.018,.015,BRASS,METAL)
        self.legend('NOW SHOWING',0,2.471,-1.248,.157,LINEN)
        for i,x in enumerate((-1.73,0,1.73)):
            # Glazing is represented by a slim reflective edge; a full cover
            # would reflect across the commissioned poster at oblique angles.
            self.rounded(x,-1.518,.498,2.118,1.18,.20,.070,BRASS,METAL)
            self.box(x,1.309,-1.405,1.085,1.469,.064,INK)
            self.posters.append({'p':[x,1.313,-1.368],'width':1.009,'height':1.3453,'yaw':0.,'tile':i})
            self.box(x,2.163,-1.488,.91,.049,.283,INK)
            self.box(x,2.136,-1.432,.75,.013,.116,'#f3d7b0',LAMP)
            self.box(x,.359,-1.535,.641,.132,.063,INK)
            self.legend('0'+str(i+1),x,.36,-1.496,.072,BRASS)
        for x, a in ((-2.69,pi*.57),(2.69,-pi*.57)):
            for zz in (.12,.91):
                self.lounge_seat(x,zz,a)
        # Opposite side-by-side seats leave a wide centre approach to the three prints.
        for x in (-2.53,2.53):
            self.profile(x,.017,1.596,[(0,.17),(.034,.17),(.067,.061),(.438,.042)],BRASS,mat=METAL)
            self.profile(x,.455,1.596,[(0,.252),(.023,.265),(.033,.259)],'#b89f85',sides=22)
            self.collision(x,.254,1.596,.51,.495,.51)
            self.box(x,.495,1.596,.21,.013,.135,INK)
        for x in (-1.61,1.61):
            self.lights.append({'p':[x,2.145,-1.261],'color':'#ffe5c2','energy':.43,'range':2.32})

def make_module(name):
    if name not in ('cinema_box_office','cinema_lounge'):
        raise ValueError(name)
    return Cinema(name)
