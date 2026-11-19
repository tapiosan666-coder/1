"""Two purpose-built travel displays, shared by the nine travel-coded brands.

Run with the existing department catalogue built. The baggage edition reuses
the shared paints and metals; all suitcase bodies, bags, wheel assemblies,
handles, lining and presentation furniture are original.
"""
from pathlib import Path
from collections import defaultdict
import json,math,sys
from model import Case,MATT,METAL
from department_fixtures import Workshop, WOOD,BRASS,CHALK,ALLOY,GRAPHITE,ASH

ROOT=Path(__file__).resolve().parents[3]
def outline(x,y,w,h,r):
    pts=[]
    for dx,dy,start in [(w/2-r,-h/2+r,-90),(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180)]:
        for s in range(5):
            a=math.radians(start+90*s/4)
            pts.append((x+dx+r*math.cos(a),y+dy+r*math.sin(a)))
    return pts

class Travel(Case):
    def __init__(self,role):
        self.role=role;self.data=defaultdict(bytearray);self.solids=[]
        self.cat='shoes';self.v=0;self.pal=('#585b6a','#e2b59e','#636e74','#b1b1a2')
        work=Workshop(self)
        if role=='arrival':
            # Luggage inspection desk with an open case showing strapped lining;
            # a cabin roller can be pulled out to its left.
            work.table(.51,.73,1.37,.61,ASH)
            self.hard(-.83,.022,-.02,.56,.67,.29,'#637783',True)
            self.open_lid(.47,.732,-.015)
            self.duffel(1.00,.735,.035,.30,.21,.22,'#bd8767')
        else:
            # Full-size and cabin pieces stand on different test-plinth heights.
            # The travel bag is actually a bag, with piping, straps and handles.
            for x,top,w in [(-.77,.12,.79),(-.01,.33,.58),(.78,.54,.76)]:
                work.pillar(x,0,-.012,w-.07,top-.026,.42,'#b3afa2')
                work.part(x,top-.013,-.01,w,.026,.53,WOOD)
            self.hard(-.77,.12,-.02,.57,.70,.29,'#718594',True)
            self.hard(-.013,.33,-.02,.44,.53,.25,'#b59b71',False)
            self.duffel(.78,.54,-.01,.59,.34,.32,'#776d65')
    def shell(self,x,y,z,w,h,d,r,col):
        # Chamfered shoulder and corner radii form a rounded shell at every angle.
        denom=min(w,h)
        rv=min(r,denom*.23)
        centre=outline(x,y,w,h,rv)
        inset=min(.019,denom*.05)
        front=outline(x,y,w-inset*2,h-inset*2,max(.008,rv-inset))
        rings=[[(px,py,z+s) for px,py in outline_] for s,outline_ in [(-d*.5,front),(-d*.5+inset,centre),(d*.5-inset,centre),(d*.5,front)]]
        for i,r1 in enumerate(rings[:-1]):
            r2=rings[i+1]
            for j in range(len(r1)):
                k=(j+1)%len(r1);self.face([r1[j],r1[k],r2[k],r2[j]],col)
        self.face(rings[-1],col);self.face(list(reversed(rings[0])),col)
    def hard(self,x,base,z,w,h,d,col,extended):
        # Four spinner wheels and axle yokes. Both telescopic bars are visible.
        dark='#3d4246'
        for a in [-1,1]:
            for b in [-1,1]:
                xx=x+a*w*.35; zz=z+b*d*.31
                self.profile(xx,base,zz,[(0,.017),(.014,.031),(.044,.031),(.057,.018)],dark,(.71,.98),12)
                self.box(xx,base+.060,zz,.021,.034,.024,ALLOY,METAL)
        bottom=base+.070
        self.shell(x,bottom+h/2,z,w,h,d,.067,col)
        self.solids.append([x,bottom+h/2,z,w*.88,h,d*.90])
        for j in range(6):
            xx=x+w*(j-2.5)*.123
            self.shell(xx,bottom+h*.50,z+d*.5,w*.031,h*.70,.014,.007,'#aaaeb0' if j%2 else col)
        for sign in [-1,1]:
            self.box(x+sign*w*.49,bottom+.52*h,z+.022,.012,h*.83,.011,GRAPHITE)
        eh=(.43 if extended else .11)
        for s in [-1,1]:
            self.box(x+s*w*.192,bottom+h+eh*.5,z-d*.23,.017,eh,.019,ALLOY,METAL)
        self.shell(x,bottom+h+eh,z-d*.23,w*.47,.046,.042,.014,dark)
        self.box(x+w*.22,bottom+h*.72,z+d*.5+.013,w*.15,.071,.014,'#d7b683')
        self.box(x+w*.22,bottom+h*.73,z+d*.5+.021,w*.105,.012,.003,GRAPHITE)
    def duffel(self,x,base,z,w,h,d,col):
        self.shell(x,base+h*.48,z,w,h*.91,d,.10,col)
        self.solids.append([x,base+h*.48,z,w*.86,h*.85,d*.86])
        self.shell(x,base+h*.40,z+d*.5,w*.58,h*.38,.026,.023,'#998772')
        self.box(x,base+h*.52,z+d*.5+.015,w*.50,.010,.008,BRASS,METAL)
        for s in [-1,1]:
            self.box(x+s*w*.24,base+h*.49,z+d*.5+.003,.018,h*.72,.009,'#534a44')
        for zz in [z-d*.32,z+d*.32]:
            start=None
            for j in range(17):
                a=math.pi*j/16;p=(x+.24*w*math.cos(a),base+h*.87+h*.51*math.sin(a),zz)
                if start:self.tube(start,p,.009,'#594a41',MATT)
                start=p
    def open_lid(self,x,top,z):
        self.shell(x,top+.044,z,.70,.088,.41,.035,'#789284')
        self.box(x,top+.091,z,.63,.019,.36,'#cbbbad')
        for a in [-1,1]:self.tube((x-.29,top+.103,z+a*.14),(x+.29,top+.103,z-a*.14),.009,GRAPHITE,MATT)
        self.shell(x,top+.303,z-.185,.69,.46,.056,.045,'#789284')
        self.shell(x,top+.31,z-.155,.63,.391,.010,.043,'#c7b8a8')
        self.box(x,top+.364,z-.148,.53,.011,.008,GRAPHITE)
        self.solids.append([x,top+.31,z-.18,.65,.45,.056])
def main():
    raw=Path(sys.argv[1]);raw.mkdir(exist_ok=True,parents=True)
    dst=ROOT/'source/v36/studio-solids.json'
    solids=json.loads(dst.read_bytes())
    for role in ['arrival','gallery']:
        key='luggage-'+role
        case=Travel(role);case.save(raw/(key+'.bin'))
        solids[key]=[[round(t,5) for t in p] for p in case.solids]
    dst.write_text(json.dumps(solids,separators=(',',':'))+'\n')
if __name__=='__main__':main()
