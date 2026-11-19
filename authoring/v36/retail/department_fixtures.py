"""Fabrication details for different trades, in metres. Front/customer side is +Z.

Major solid elements are exported alongside the model so an open rail does not
inherit the blocking back of a bookcase. Shelf stock remains part of the mesh.
"""
import math

WOOD = '#a78160'
ASH = '#caa980'
BRASS = '#ab9263'
ALLOY = '#aeb9b8'
CHALK = '#eee6d7'
GRAPHITE = '#3a434a'
FEET = '#555c59'


class Workshop:
    def __init__(self, case):
        self.c = case
        self.gallery = case.role == 'gallery'
        self.dark, self.light, self.accent, self.sage = case.pal

    def part(self, x, y, z, width, height, depth, surface, material=0):
        self.c.box(x, y, z, width, height, depth, surface, material)
        self.c.solids.append([x, y, z, width, height, depth])

    def endcard(self, x, base, w=.37, h=.27, z=-.22):
        self.part(x, base+h/2, z, w+.015, h+.015, .024, BRASS, 1)
        self.c.card(x, base+h/2, z+.013, w, h)

    def table(self, x, top, width, depth, finish, z=0):
        self.part(x, top-.028, z, width, .056, depth, finish)
        for xx in [-1,1]:
            for zz in [-1,1]:
                self.part(x+xx*(width/2-.09), (top-.056)/2, z+zz*(depth/2-.065),
                          .035, top-.056, .035, FEET, 1)

    def pillar(self,x,y,z,w,h,d,finish=WOOD):
        self.part(x, y+h/2, z, w, h, d, finish)

    def apparel(self):
        # Retail garment rail with a raised asymmetric crook; the outer
        # apparel hangs in the clear. A low folding table terminates the run.
        v=self.c.v
        xl, xr=-1.18,.29
        rh=(1.80 if self.gallery else 1.56)+.065*v
        for x in (xl,xr):
            self.part(x,.035,-.055,.155,.07,.49,GRAPHITE)
            self.part(x,rh/2,-.12,.042,rh,.042,BRASS,1)
        self.part((xl+xr)/2,rh,-.12,xr-xl,.035,.035,BRASS,1)
        for i,x in enumerate([-.975,-.50,-.02]):
            kind=(i+v)%3
            y=rh-.088
            if kind==0:
                # Long coat with lapels and pockets.
                points=[(-.08,0),(-.18,-.055),(-.215,-.48),(-.143,-.50),(-.124,-.33),
                        (-.165,-.78),(.162,-.78),(.125,-.33),(.143,-.50),(.21,-.48),(.18,-.055),(.072,0)]
                col=self.dark
            elif kind==1:
                points=[(-.07,-.01),(-.15,-.035),(-.213,-.15),(-.16,-.195),(-.125,-.16),
                        (-.127,-.45),(.142,-.45),(.125,-.16),(.175,-.195),(.22,-.155),(.155,-.04),(.07,-.01),(0,-.075)]
                col=self.accent
            else:
                points=[(-.068,0),(-.14,-.045),(-.162,-.16),(-.112,-.29),
                        (-.196,-.59),(-.132,-.615),(-.06,-.602),(.04,-.62),(.18,-.60),(.122,-.30),
                        (.158,-.16),(.144,-.05),(.075,0),(0,-.055)]
                col=self.sage
            self.c.silhouette([(x+dx,y+dy) for dx,dy in points],(-.10,.064),col)
            self.c.tube((x-.12,y-.034,-.115),(x,y+.026,-.115),.007,ASH,0)
            self.c.tube((x,y+.026,-.115),(x+.12,y-.034,-.115),.007,ASH,0)
            self.c.tube((x,y+.026,-.115),(x,rh,-.118),.005,ALLOY)
            if kind==0:
                self.c.tube((x-.07,y-.013,-.065),(x+.016,y-.19,-.065),.006,self.light,0)
                self.c.tube((x+.07,y-.013,-.065),(x+.016,y-.19,-.065),.006,self.light,0)
                self.c.box(x+.016,y-.44,-.064,.008,.47,.005,self.light)
                for side in [-1,1]:
                    self.c.box(x+.088*side,y-.48,-.065,.06,.021,.007,self.light)
            if kind==2:
                self.c.box(x,y-.277,-.065,.227,.020,.008,self.light)
        self.table(.79,.56+v*.045,.84,.54,ASH)
        for i in range(5):
            self.c.box(.80,.584+v*.045+i*.055,.046,.49-i*.015,.053,.29,
                       [self.dark,self.light,self.sage][(i+v)//2%3])
            self.c.box(.79,.583+v*.045+i*.055,.192,.33,.009,.008,CHALK)
        self.pillar(.93,.57+v*.045,-.16,.027,.39,.027,BRASS)
        self.endcard(.93,.91+v*.045,w=.33,h=.25,z=-.16)

    def book(self):
        # Paperback steps and tall library spine carry different stock; the
        # positive space / negative space was designed from its side elevation.
        v=self.c.v
        tall=1.88 if self.gallery else 1.26
        for x in [-1.19,-.44]:
            self.pillar(x,0,-.24,.052,tall,.09)
            self.c.tube((x,.035,.25),(x,tall,-.21),.021,BRASS)
        levels=[.33,.76,1.18,1.61] if self.gallery else [.28,.64,1.01]
        for j,y in enumerate(levels):
            self.part(-.81,y-.024,-.07,.81,.048,.45,ASH)
            self.c.box(-.81,y+.014,.148,.81,.028,.014,BRASS,1)
            for i in range(2):
                self.c.object(-1.005+.36*i,y,-.048,.86,i+j+v)
        self.table(.48,.45,1.39,.62,WOOD)
        for i,(z,y) in enumerate([(.17,.46),(-.023,.64),(-.20,.81)]):
            if i:self.part(.48,(y+.45)/2,z,1.33,y-.45,.18,ASH)
            for j,x in enumerate([.02,.46,.93]):
                self.c.object(x,y,z,.78,(i+j+v)%3)
        self.pillar(.99,.81,-.23,.035,.26,.035,BRASS)
        self.endcard(.99,1.05,w=.35,h=.22)

    def garden(self):
        # Nursery bench and a small pitched propagation house. The tall ends
        # are open mullions, not a closed box, with staggered potting benches.
        roof=1.98 if self.gallery else 1.47
        eave=roof-.28
        for x in [-1.20,-.20]:
            for z in [-.26,.21]:
                self.part(x,eave/2,z,.042,eave,.042,'#75887a',1)
                self.c.tube((x,eave,z),(x,roof,-.025),.022,'#75887a')
        self.part(-.70,roof,-.025,1.04,.035,.035,'#75887a',1)
        for z in [-.26,.21]:self.c.tube((-1.2,eave,z),(-.2,eave,z),.015,ALLOY)
        for j,y in enumerate([.53,1.07] if self.gallery else [.42,.82]):
            self.part(-.70,y-.02,-.01,1.08,.04,.56,ASH)
            for i in range(3):self.c.object(-1.08+i*.38,y,-.02,1.18,i+j)
        for j,(x,y,w) in enumerate([(.11,.73,.46),(.65,.50,.58),(1.06,.27,.29)]):
            self.pillar(x,0,0,w-.10,y-.04,.38,'#b8b39a')
            self.part(x,y-.02,0,w,.04,.49,WOOD)
            self.c.object(x,y,0,1.08+j*.08,j+self.c.v)
        self.pillar(.66,.50,-.18,.026,.46,.026,'#638773')
        self.endcard(.66,.96,w=.31,h=.23,z=-.18)

    def beauty(self):
        # Product testing vanity: illuminate a rounded mirror over a
        # compact drawer pedestal. Lower sample trays are visibly separate.
        v=self.c.v
        h=.87 if self.gallery else .75
        self.pillar(-.43,0,-.045,.78,h-.064,.55,'#c5aea2')
        self.part(-.43,h-.035,0,1.55,.07,.69,CHALK)
        for y in [.25,.46,.67]:
            self.c.box(-.43,y,.233,.74,.008,.008,BRASS,1)
        self.pillar(-.56,h,-.21,.13,.52,.06,BRASS)
        rx=.39 if self.gallery else .32
        ry=.51 if self.gallery else .35
        cy=h+.17+ry;cx=-.56
        for i in range(36):
            a=i*math.tau/36;b=(i+1)*math.tau/36
            pa=(cx+rx*math.cos(a),cy+ry*math.sin(a),-.167)
            pb=(cx+rx*math.cos(b),cy+ry*math.sin(b),-.167)
            self.c.face([(cx,cy,-.168),pa,pb],'#c1d4d7',1)
            self.c.tube(pa,pb,.019,CHALK,3)
        self.c.solids.append([cx,cy,-.17,.72*rx*2,ry*1.7,.027])
        self.table(.75,h-.25,.83,.52,'#c6a296')
        for j,(x,y) in enumerate([(-.91,h),(-.26,h),(.15,h),(.54,h-.25),(.9,h-.25)]):
            self.c.box(x,y+.012,.09,.27,.024,.25,BRASS,1)
            self.c.object(x,y+.024,.075,1.04,j+v)
        self.pillar(.91,h-.25,-.18,.03,.36,.03,BRASS)
        self.endcard(.91,h+.11,w=.35,h=.22,z=-.18)

    def electronics(self):
        # Wall-free listening/demo bar split into an AV plinth and a touch
        # bench. Screens have visible feet, dark bezels and printed UI.
        v=self.c.v
        left=-.70
        self.pillar(left,0,-.075,.75,.44,.46,GRAPHITE)
        self.part(left,.47,-.045,1.07,.06,.62,ALLOY,1)
        size=1 if self.gallery else .75
        self.pillar(left,.50,-.12,.059,.35,.055,ALLOY)
        self.part(left,.87+.22*size,-.14,.91*size,.49*size,.047,GRAPHITE)
        self.c.card(left,.87+.22*size,-.114,.87*size,.45*size,v)
        self.table(.55,.84,1.22,.58,'#d8d9ce')
        for i,x in enumerate([.20,.60,.97]):
            self.c.object(x,.84,.028,.92,i+v)
            self.c.box(x,.855,.221,.16,.018,.055,CHALK)
        self.c.box(.54,.81,.294,.95,.014,.006,'#d2e7ec',3)

    def market(self):
        # Independent produce crates face the buyer in stepped departments.
        # Legs and lips are painted individually, with no rear casework.
        v=self.c.v
        for i,(x,h,w) in enumerate([(-.88,.47,.73),(-.08,.70,.79),(.79,.53,.80)]):
            self.table(x,h,w,.61,WOOD)
            for z in [-.242,.242]:
                self.part(x,h+.052,z,w-.04,.105,.023,ASH)
            for side in [-1,1]:
                self.part(x+side*(w/2-.029),h+.054,0,.026,.108,.47,ASH)
            for j in range(2):self.c.object(x+(j-.5)*.34,h+.009,-.003,1.07,i+v)
        self.pillar(-.85,.47,-.20,.027,.55,.027,FEET)
        self.endcard(-.85,1.02,.37,.28,-.20)

    def hospitality(self):
        # Ceramic counter with a stepped bread service and side menu/easel.
        v=self.c.v
        self.pillar(-.46,0,-.06,1.29,.79,.52,'#b7b9ac')
        for i in range(11):
            self.c.box(-1.042+i*.116,.42,.204,.032,.67,.018,WOOD)
        self.part(-.46,.82,-.025,1.47,.06,.61,'#e6ddc7')
        for j,x in enumerate([-.93,-.55,-.14,.08]):
            self.c.object(x,.85,.012,1.14,(j+v)%3)
        if self.c.cat=='cafe':
            self.pillar(.71,0,-.055,.45,.61,.42,GRAPHITE)
            self.part(.71,.637,0,.84,.054,.52,WOOD)
            for n in range(2):
                z=(-.13,.11)[n]
                self.c.object(.70,.664+n*.013,z,.94,n+1)
        else:
            self.table(.76,.73,.78,.56,ASH)
            self.c.object(.73,.73,0,1.65,0)
        hip=.85 if self.gallery else .66
        self.pillar(-.85,.85,-.18,.035,hip-.32,.035,BRASS)
        self.endcard(-.85,.85+hip-.32,.48,.38,-.18)

    def shoes(self):
        # A flight of independent shoe display islands with outboard sole
        # samples; the tall end deliberately stops at the signed blade.
        v=self.c.v
        for i,(x,y,w) in enumerate([(-.91,.79,.57),(-.26,.57,.63),(.42,.37,.65),(1.0,.20,.43)]):
            self.pillar(x,0,-.06,w*.59,y-.042,.35,GRAPHITE if i%2 else ASH)
            self.part(x,y-.021,-.015,w,.042,.53,CHALK)
            self.c.object(x,y,.019,.95 if i<3 else .75,i+v)
        self.pillar(-.91,.79,-.19,.03,.35,.03,BRASS)
        self.endcard(-.91,1.14,.35,.31,-.19)

    def home(self):
        # Room-setting islands: timber sample table, a freestanding floor
        # lamp and a small stone pedestal. Customers see through the display.
        self.table(-.53,.69,1.36,.61,ASH)
        for j,x in enumerate([-.94,-.54,-.12]):
            self.c.object(x,.69,0,1.2,j+self.c.v)
        self.pillar(.53,0,.025,.44,.36,.46,'#bcb7a6')
        self.c.object(.53,.36,0,1.1,0)
        self.c.profile(.94,0,-.11,[(0,.15),(.042,.15)],BRASS,mat=1)
        h=1.63 if self.gallery else 1.30
        self.pillar(.94,.04,-.11,.036,h-.04,.036,BRASS)
        self.c.profile(.94,h,-.11,[(0,.27),(.36,.11)],'#d6c7aa',(.96,.83))
        self.c.profile(.94,h-.005,-.11,[(0,.258),(.008,.26)],CHALK,(.96,.83),mat=3)
        self.c.solids.append([.94,h+.14,-.11,.34,.28,.32])

    def service(self):
        # Accessible side counter beside a physical standing information
        # lectern; a separate vertical pinboard carries the illustrated card.
        self.pillar(-.43,0,-.02,.59,.99,.46,'#82999a')
        self.part(-.43,1.015,.005,.88,.05,.57,ASH)
        self.table(.59,.72,.95,.58,ASH)
        for j,x in enumerate([.34,.75]):self.c.object(x,.72,-.02,.82,j)
        self.pillar(-1.01,0,-.21,.09,1.13,.12,BRASS)
        self.endcard(-1.01,1.13,.41,.53,-.21)


    def sports(self):
        # Technical packs hang from a climbing display sail, beside a true-size
        # trekking pole stand and footwear-testing step.
        self.part(-.73,.065,-.045,.76,.13,.58,GRAPHITE)
        self.part(-.73,1.00,-.19,.55,1.75,.06,'#b9c4bc')
        for j,(x,y) in enumerate([(-.77,.48),(-.66,1.04)]):
            self.c.profile(x,y,-.07,[(0,.09),(.08,.156),(.31,.15),(.43,.082)],
                           [self.sage,self.dark][j],(1.12,.69))
            self.c.box(x,y+.17,.027,.205,.138,.045,self.accent)
            for side in [-1,1]:
                self.c.box(x+side*.091,y+.261,.029,.016,.223,.013,CHALK)
        self.table(.07,.30,.57,.50,WOOD)
        self.c.object(.07,.30,.018,1.03,self.c.v)
        self.part(.82,.06,-.01,.55,.12,.45,WOOD)
        for j,x in enumerate([.60,.79,.99]):
            h=.99+.10*j
            self.c.tube((x,.12,.055),(x+.055,h,-.07),.012,ALLOY)
            self.c.tube((x+.055,h,-.07),(x+.067,h+.16,-.09),.022,GRAPHITE)
        self.pillar(.77,.12,-.17,.027,.69,.027,BRASS)
        self.endcard(.77,.81,.38,.24,-.17)

    def furniture(self):
        # One life-size occasional chair, tall lamp and a finish library at
        # hand height; a product chair is never put on a display table.
        x=-.73; seat=.45
        self.part(x,seat,0,.64,.11,.54,self.sage)
        self.part(x,.706,-.20,.64,.43,.10,self.sage)
        for dx in [-.23,.23]:
            for dz in [-.17,.17]:self.pillar(x+dx,0,dz,.05,seat-.05,.05,WOOD)
        self.table(.27,.48,.74,.52,ASH)
        for j in range(5):
            self.c.box(.27,.495+j*.018,.005,.37-j*.009,.018,.225,
                       [self.light,self.accent,self.sage][j%3])
        self.c.profile(1.00,0,-.09,[(0,.15),(.032,.15)],BRASS,mat=1)
        self.pillar(1,.032,-.09,.036,1.33,.036,BRASS)
        self.c.profile(1,1.36,-.09,[(0,.235),(.34,.107)],'#dbcab0',(1,.87))
        self.c.profile(1,1.355,-.09,[(0,.226),(.008,.226)],CHALK,(1,.87),mat=3)

    def mobile(self):
        # Plug-in island, accessory peg board and a vertical tariff screen.
        self.pillar(-.79,0,-.08,.45,1.12,.37,GRAPHITE)
        self.part(-.79,1.38,-.12,.31,.52,.037,GRAPHITE)
        self.c.card(-.79,1.38,-.099,.265,.455)
        self.table(.33,.82,1.39,.59,CHALK)
        for j,x in enumerate([-.19,.24,.66]):
            self.c.box(x,.837,.105,.225,.034,.212,GRAPHITE)
            self.c.box(x,.968,.092,.147,.245,.023,GRAPHITE)
            self.c.card(x,.968,.104,.130,.218,(self.c.v+j)%3)
            self.c.box(x,.849,.234,.21,.012,.043,'#d5daca')
        self.part(.945,1.163,-.185,.405,.686,.036,'#c9d1d1')
        for i in range(4):
            xx=.86+(i%2)*.174; yy=1.015+(i//2)*.235
            self.c.box(xx,yy,-.156,.123,.191,.029,self.sage if i%2 else self.light)
            self.c.card(xx,yy,-.140,.111,.148,(self.c.v+i)%3)

    def optics(self):
        # Narrow stepped frame trays and an upright, full-face fitting mirror.
        self.pillar(-.82,0,-.075,.47,.40,.44,WOOD)
        self.pillar(-.82,.40,-.17,.064,.48,.064,BRASS)
        self.part(-.82,1.17,-.16,.46,.75,.041,BRASS,1)
        self.c.box(-.82,1.17,-.138,.42,.71,.009,'#c2d4d5',1)
        self.table(.39,.69,1.46,.56,ASH)
        for j,z in enumerate([.16,-.035,-.21]):
            h=.69+j*.10
            self.part(.39,(h+.699)/2,z,1.37,max(.018,h-.69),.14,'#c5bb99')
            for i,x in enumerate([-.10,.24,.58,.92]):
                self.c.object(x,h+.009,z,1.09,i+j)

    def stationery(self):
        # Writing desk with horizontal blotter, sample pens and a compact
        # greeting-card carousel above a low run of vertical paper drawers.
        self.table(-.55,.76,1.29,.57,ASH)
        self.c.box(-.55,.768,.038,.70,.016,.32,'#729187')
        for i in range(5):
            self.c.tube((-.81+i*.11,.787,-.035),(-.78+i*.11,.787,.107),.007,
                        [self.dark,self.accent,BRASS][i%3],0)
        self.c.object(-.90,.76,-.09,.69,self.c.v)
        self.pillar(.73,0,-.04,.65,.66,.49,'#d6c5a5')
        for j in range(4):
            self.c.box(.73,.10+j*.16,.208,.59,.008,.007,BRASS,1)
        self.part(.73,.68,-.017,.73,.04,.55,WOOD)
        self.pillar(.73,.70,-.11,.063,.72,.063,BRASS)
        for j in range(2):
            for i in range(2):
                x=.55+.35*i; y=.83+.32*j
                self.part(x,y,-.06,.28,.25,.035,'#bcac93')
                self.c.card(x,y,-.041,.264,.235,(i+j+self.c.v)%3)


    def arcade(self):
        # Single-player control deck beside a low two-player tabletop.
        tall=1.74 if self.gallery else 1.41
        self.pillar(-.65,0,-.06,.60,.78,.42,GRAPHITE)
        self.part(-.65,.81,.02,.81,.06,.61,self.accent)
        self.pillar(-.65,.84,-.18,.64,tall-.84,.15,self.dark)
        self.c.card(-.65,(tall+.88)/2,-.103,.56,tall-.94)
        self.part(-.65,tall+.03,-.14,.76,.065,.32,GRAPHITE)
        self.c.profile(-.86,.84,.10,[(0,.021),(.09,.021),(.11,.05),(.16,.04)],self.accent)
        for x in [-.56,-.48,-.40]:
            self.c.profile(x,.84,.10,[(0,.025),(.012,.028)],CHALK)
        self.table(.62,.72,1.04,.60,self.light)
        self.c.object(.37,.72,-.02,.85,0)
        self.c.object(.85,.72,-.02,.85,1)

    def pharmacy(self):
        # An illuminated consultation totem with a slotted range of wellness
        # products, plus an accessible dispensing counter.
        self.pillar(-.83,0,-.18,.57,1.56 if self.gallery else 1.23,.20,'#c4d5cd')
        self.endcard(-.83,1.01 if self.gallery else .68,.52,.49,-.055)
        self.table(.35,.85,1.47,.58,CHALK)
        for j,z in enumerate([.12,-.16]):
            if j:self.part(.35,.91,z,1.43,.12,.20,'#a4bdb4')
            for i in range(4):
                self.c.object(-.15+.32*i,.85+.12*j,z,.96,i+j+self.c.v)

    def toy(self):
        # Small children's construction table and an actual standing play
        # easel with an A-frame support.
        self.table(-.57,.54,1.10,.55,'#e1bd72')
        for i in range(3):self.c.object(-.93+i*.36,.54,.045,.90,i)
        for x in [.28,.99]:
            self.c.tube((x,0,.23),(x,1.31,-.04),.027,WOOD,0)
            self.c.tube((x,0,-.28),(x,1.31,-.04),.027,WOOD,0)
        self.part(.64,.91,-.02,.79,.68,.045,'#77918c')
        self.c.card(.64,.91,.004,.70,.58)
        self.part(.64,.58,.02,.87,.048,.24,WOOD)

    def music(self):
        # Instrument stands and vinyl listening console with two record bins.
        self.table(.54,.85,1.24,.61,WOOD)
        for j in range(6):
            self.c.box(.28,.96,-.12+j*.035,.46,.31,.013,
                       [self.dark,self.accent,self.sage][j%3])
        self.c.card(.28,.96,.064,.42,.27)
        self.c.profile(.84,.85,.025,[(0,.205),(.032,.205)],GRAPHITE,(1,.94))
        self.c.profile(.84,.884,.025,[(0,.07),(.005,.068)],self.accent)
        for j,x in enumerate([-.96,-.48]):
            self.c.profile(x,0,0,[(0,.145),(.025,.145)],FEET,(1,.85))
            self.c.tube((x,0,-.07),(x,.60,-.07),.021,FEET)
            self.c.object(x,.11,-.018,1.70 if j==0 else 1.30,j)

    def jewellery(self):
        # Individual velvet display drums of different heights, on fluted
        # brass stems; a narrow sign sits above only the tallest drum.
        for i,(x,h,r) in enumerate([(-.88,.83,.30),(-.16,.65,.28),(.58,.81,.33)]):
            self.c.profile(x,0,-.01,[(0,r*.62),(.035,r*.62),(.06,.054),
                (h-.06,.054),(h-.04,r),(h,r)],BRASS,(1,.86),18,1)
            self.c.profile(x,h,-.01,[(0,r),(.043,r)],self.dark,(1,.86),20)
            self.c.solids.append([x,h/2,-.01,.108,h,.108])
            self.c.solids.append([x,h-.02,-.01,1.65*r,.12,1.3*r])
            self.c.object(x,h+.043,.015,1.29,i+self.c.v)
        self.pillar(-.88,.83,-.20,.021,.31,.021,BRASS)
        self.endcard(-.88,1.14,.22,.18,-.20)

    def print_gallery(self):
        # Gallery works stand on two easels; cinema presents a double-sided
        # programme lightbox and a small physical ticket lectern.
        if self.c.cat=='cinema':
            self.pillar(-.66,0,-.09,.41,.216,.35,GRAPHITE)
            self.part(-.66,1.02,-.09,.96,1.64,.17,GRAPHITE)
            self.c.card(-.66,1.03,-.004,.846,1.48)
            self.c.box(-.66,1.81,.002,.88,.018,.008,CHALK,3)
            self.pillar(.65,0,-.05,.33,.91,.42,self.dark)
            self.part(.65,.94,0,.68,.06,.55,ASH)
            self.c.object(.66,.97,0,.90,self.c.v)
            return
        for i,(x,w,low,h) in enumerate([(-.64,.92,.56,1.21),(.60,.72,.39,.88)]):
            for xx in [x-w*.42,x+w*.42]:
                self.c.tube((xx,0,.11),(xx,low+h,-.18),.024,WOOD,0)
            self.c.tube((x,0,-.31),(x,low+h,-.18),.024,WOOD,0)
            self.part(x,low+h/2,-.07,w,h,.052,self.dark)
            self.c.card(x,low+h/2,-.043,w-.065,h-.065,(self.c.v+i)%3)
            self.part(x,low-.014,-.02,w+.05,.038,.18,WOOD)


DEPARTMENTS = {
    'apparel':'apparel','book':'book','stationery':'stationery','garden':'garden',
    'beauty':'beauty','optics':'optics','electronics':'electronics','mobile':'mobile',
    'food':'market','restaurant':'hospitality','cafe':'hospitality','shoes':'shoes',
    'sports':'sports','home':'home','furniture':'furniture','service':'service',
    'arcade':'arcade','toy':'toy','pharmacy':'pharmacy','music':'music','accessories':'jewellery',
    'gallery':'print_gallery','cinema':'print_gallery',
}

def build(case):
    method = DEPARTMENTS.get(case.cat)
    if method is None:
        return False
    method = getattr(Workshop(case), method)
    method()
    return True
