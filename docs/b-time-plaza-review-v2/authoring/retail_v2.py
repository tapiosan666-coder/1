"""Purpose-built original retail millwork. Source tenant boundaries / aisles stay frozen."""
import math,random,hashlib
import numpy as np
from shapely.geometry import Point,Polygon,LineString,box
from shapely.ops import unary_union

def fit_shop(ctx,s,lev,y,idx,poly,shelf):
 ex,surf,bar,rect,cyl,tri,quad,pos=[ctx[k]for k in['extrude','surf','bar','rect','cylinder','tri','quad','pos']]
 u=np.array(s['u']);n=np.array(s['n']);e=np.array(s['entry']);rng=random.Random(91000+idx)
 occupied=[];t={'カフェ':'食品・カフェ','レストラン':'飲食','生活・服飾':'衣料','書籍・雑貨':'書籍・文具'}.get(s['category'],s['category']);details=[]
 usable=s['sales'].intersection(ctx['CROP']).buffer(-.22).difference(s['aisles'].buffer(.36))
 def P(a,b):return tuple(e+u*a+n*b)
 def mark(fp):occupied.append(fp)
 def fit(fp):return usable.covers(fp)and all(fp.distance(q)>.42 for q in occupied)
 def tube(a,b,r,mat='metal',segments=10):
  a=np.array(a);b=np.array(b);v=b-a;v/=max(np.linalg.norm(v),1e-8);ref=np.array([0,1,0])if abs(v[1])<.8 else np.array([1,0,0]);v1=np.cross(v,ref);v1/=np.linalg.norm(v1);v2=np.cross(v,v1)
  for i in range(segments):
   aa=i*math.tau/segments;bb=(i+1)*math.tau/segments;nn=v1*math.cos((aa+bb)/2)+v2*math.sin((aa+bb)/2)
   q1=v1*math.cos(aa)*r+v2*math.sin(aa)*r;q2=v1*math.cos(bb)*r+v2*math.sin(bb)*r
   quad(mat,[pos(*(a+q1)),pos(*(b+q1)),pos(*(b+q2)),pos(*(a+q2))],nn.tolist())
 def lathe(c,profile,mat,segments=12):
  # profile is actual metric (radius,height), smooth radial normals, no source models.
  for (r0,h0),(r1,h1)in zip(profile,profile[1:]):
   dh=h1-h0;dr=r1-r0
   for i in range(segments):
    a=i*math.tau/segments;b=(i+1)*math.tau/segments;mid=(a+b)/2;nn=np.array([math.cos(mid)*dh,-dr,math.sin(mid)*dh]);nn/=max(np.linalg.norm(nn),1e-8)
    pts=[pos(c[0]+r0*math.cos(a),y+h0,c[1]+r0*math.sin(a)),pos(c[0]+r1*math.cos(a),y+h1,c[1]+r1*math.sin(a)),pos(c[0]+r1*math.cos(b),y+h1,c[1]+r1*math.sin(b)),pos(c[0]+r0*math.cos(b),y+h0,c[1]+r0*math.sin(b))]
    quad(mat,pts,nn.tolist(),[[i/segments,h0],[i/segments,h1],[(i+1)/segments,h1],[(i+1)/segments,h0]])
 def panel(c,w,h,yy,atlas,index=0,face=-1):
  cc=np.array(c);nn=n*face
  pts=[pos(*( [*(cc-u*w/2+nn*.012)][:1] ))]if False else None
  pts=[pos(cc[0]-u[0]*w/2+nn[0]*.012,y+yy,cc[1]-u[1]*w/2+nn[1]*.012),pos(cc[0]+u[0]*w/2+nn[0]*.012,y+yy,cc[1]+u[1]*w/2+nn[1]*.012),pos(cc[0]+u[0]*w/2+nn[0]*.012,y+yy+h,cc[1]+u[1]*w/2+nn[1]*.012),pos(cc[0]-u[0]*w/2+nn[0]*.012,y+yy+h,cc[1]-u[1]*w/2+nn[1]*.012)]
  col=index%8;row=(index//8)%4;uv=[[(col+.02)/8,(row+.98)/4],[(col+.98)/8,(row+.98)/4],[(col+.98)/8,(row+.02)/4],[(col+.02)/8,(row+.02)/4]]if atlas=='book_covers'else[[0,1],[1,1],[1,0],[0,0]]
  quad(atlas,pts,(nn[0],0,nn[1]),uv)
 def rounded(c,l,w,yy,h,mat,solid=True,r=.04):
  base=rect(c,u,max(.02,l-2*r),max(.02,w-2*r)).buffer(r,quad_segs=3)
  ex(base,y+yy,h,mat,solid)
 def bowl(c,yy,kind=0):
  r=.08+kind*.035
  lathe(c,[(.025,yy),(.035,yy+.015),(r*.8,yy+.04),(r,yy+.10),(r-.006,yy+.105),(.045,yy+.035)],'ceramic_'+str((idx+kind)%3))
 def book(c,yy,j,face):
  width=rng.uniform(.026,.060);height=rng.uniform(.21,.30);depth=.175;cc=np.array(c)
  ex(rect(c,u,width,depth),y+yy,height,'paper',False)
  for sy in[0,height]:surf(rect(c,u,width+.007,depth+.008),y+yy+sy,'book_'+str(j%6),up=sy>0)
  # Thin colored spine, two metallic title rules. Facing both aisles, no generic boxes cover it.
  sc=cc+n*face*(depth/2+.004)
  nn=n*face
  def spine(ya,yb,ww,mat):
   quad(mat,[pos(sc[0]-u[0]*ww/2,y+yy+ya,sc[1]-u[1]*ww/2),pos(sc[0]+u[0]*ww/2,y+yy+ya,sc[1]+u[1]*ww/2),pos(sc[0]+u[0]*ww/2,y+yy+yb,sc[1]+u[1]*ww/2),pos(sc[0]-u[0]*ww/2,y+yy+yb,sc[1]-u[1]*ww/2)],(nn[0],0,nn[1]))
  spine(0,height,width+.006,'book_'+str(j%6))
  for by in[.052,.083,height-.035]:
   if by>0:spine(by,by+.003,width*.70,'gold')
 def case(c,kind=0):
  # Slender solid joinery, correctly sized shelving, edge profiles and open stock.
  h=2.05 if kind==1 else 1.32
  rounded(c,1.75,.66,0,.09,'oak',True)
  ex(rect(c,u,1.70,.04),y+.09,h-.09,'oak',True)
  for side in[-1,1]:ex(rect(np.array(c)+u*side*.84,u,.035,.65),y+.09,h-.09,'oak',True)
  for yy in[.12,.49,.86,1.23]+([1.60,1.97]if kind==1 else[]):
   rounded(c,1.75,.66,yy,.028,'oak',False,.012)
   for side in[-1,1]:
    cc=np.array(c)+n*.24*side;cursor=-.74;j=0
    if t in['書籍・文具','楽器','ホビー']:
     while cursor<.75:
      b=cc+u*cursor;book(b,yy+.029,idx+j+int(yy*10),side);cursor+=rng.uniform(.037,.068);j+=1
     # face-out illustrated edition on selected shelves
     if int(yy*10)%2==0:panel(cc, .18,.25,yy+.03,'book_covers',(idx+int(yy*10))%32,side)
    elif t in['美容・ケア']:
     for j in range(4):
      cc0=cc+u*(j-1.5)*.34
      lathe(cc0,[(.025,yy+.03),(.034,yy+.04),(.034,yy+.19),(.018,yy+.22),(.018,yy+.25),(.0,yy+.25)],'bottle_'+str(j%3))
    elif t in['靴・鞄']:
     for j in range(2):
      shoe(cc+u*(j-.5)*.70,yy+.03,j)
    else:
     for j in range(2):bowl(cc+u*(j-.5)*.62,yy+.03,(idx+j)%3)
  details.append('両面の薄い背表紙・表紙・紙束'if t in['書籍・文具','ホビー','楽器']else'実物形状の商品を載せた開放棚')
 def shoe(c,yy,j):
  cc=np.array(c);vec=n;across=u
  for offset in[-.075,.075]:
   center=cc+across*offset
   # Toe/waist/heel sections, curved leather upper, layered rubber sole.
   sections=[(-.14,.035,.025),(-.11,.05,.055),(-.04,.048,.095),(.055,.036,.085),(.12,.04,.10),(.14,.032,.07)]
   for (s0,w0,h0),(s1,w1,h1)in zip(sections,sections[1:]):
    for a0,a1 in zip(np.linspace(0,math.pi,9),np.linspace(0,math.pi,9)[1:]):
     pts=[]
     for ss,ww,hh,aa in[(s0,w0,h0,a0),(s1,w1,h1,a0),(s1,w1,h1,a1),(s0,w0,h0,a1)]:
      q=center+vec*ss+across*math.cos(aa)*ww;pts.append(pos(q[0],y+yy+.025+math.sin(aa)*hh,q[1]))
     quad('leather_'+str(j%2),pts,(0,1,0))
   sole=rect(center,n,.28,.09).buffer(.008,quad_segs=3);ex(sole,y+yy,.026,'rubber_white',False)
   for k in range(4):
    q=center+vec*(.005+k*.018);bar(tuple(q-across*.028),tuple(q+across*.028),.005,y+yy+.108,.004,'fabric_cream')
 def garment(c,j):
  cc=np.array(c);mat=['fabric_cream','fabric_navy','fabric_sage','fabric_rust'][(idx+j)%4]
  outline=[(-.19,1.48),(-.10,1.59),(-.06,1.55),(.06,1.55),(.10,1.59),(.19,1.48),(.31,1.20),(.22,1.15),(.15,1.29),(.16,.77),(-.16,.77),(-.15,1.29),(-.22,1.15),(-.31,1.20)]
  from shapely import constrained_delaunay_triangles
  for tr in constrained_delaunay_triangles(Polygon(outline)).geoms:
   xy=list(tr.exterior.coords)[:3]
   for side in[-1,1]:
    pp=[]
    for a,b in xy:
     fold=math.sin(a*35+b*8)*.009;pp.append(pos(cc[0]+u[0]*a+n[0]*(side*.025+fold),y+b+.2,cc[1]+u[1]*a+n[1]*(side*.025+fold)))
    tri(mat,pp,(n[0]*side,0,n[1]*side),[[a,b]for a,b in xy])
  for a,b in zip(outline,outline[1:]+outline[:1]):
   quad(mat,[pos(cc[0]+u[0]*a[0]+n[0]*side*.025,y+a[1]+.2,cc[1]+u[1]*a[0]+n[1]*side*.025)for side in[-1,1]]+[pos(cc[0]+u[0]*b[0]+n[0]*side*.025,y+b[1]+.2,cc[1]+u[1]*b[0]+n[1]*side*.025)for side in[1,-1]],(0,1,0))
  # Curved wooden hanger and suspension hook.
  a=cc-u*.18;b=cc+u*.18
  tube((a[0],y+1.76,a[1]),(cc[0],y+1.86,cc[1]),.009,'oak');tube((cc[0],y+1.86,cc[1]),(b[0],y+1.76,b[1]),.009,'oak')
  tube((cc[0],y+1.85,cc[1]),(cc[0],y+1.98,cc[1]),.005)
 def rack(c):
  cc=np.array(c)
  for side in[-1,1]:
   p=cc+u*.82*side;tube((p[0],y+.05,p[1]),(p[0],y+2,p[1]),.022,'bronze')
   rounded(p,.10,.65,0,.05,'dark_stone',True,.02)
  a=cc-u*.82;b=cc+u*.82;tube((a[0],y+2,a[1]),(b[0],y+2,b[1]),.022,'bronze')
  for j in range(4):garment(cc+u*(j-1.5)*.38,j)
  details.append('折り目を持つ衣服・ハンガー・金属ラック')
 def chair(c,angle):
  # Curved timber shell back, upholstered seat, tapered tubular legs.
  pp=np.array(c);dv=np.array([math.cos(angle),math.sin(angle)]);ac=np.array([-dv[1],dv[0]])
  seat=rect(pp,ac,.40,.40).buffer(.035,quad_segs=3);ex(seat,y+.43,.055,'fabric_sage',True)
  for sx in[-1,1]:
   for sz in[-1,1]:
    top=pp+ac*sx*.14+dv*sz*.13;bot=pp+ac*sx*.18+dv*sz*.18;tube((top[0],y+.44,top[1]),(bot[0],y+.03,bot[1]),.015,'black')
  for aa,bb in zip(np.linspace(-1.0,1.0,12),np.linspace(-1.0,1.0,12)[1:]):
   a=pp+dv*.12+ac*math.sin(aa)*.25+dv*math.cos(aa)*.13;b=pp+dv*.12+ac*math.sin(bb)*.25+dv*math.cos(bb)*.13
   quad('oak',[pos(a[0],y+.52,a[1]),pos(b[0],y+.52,b[1]),pos(b[0],y+.83,b[1]),pos(a[0],y+.83,a[1])],(-dv[0],0,-dv[1]),solid=True)
 def cafe_counter(c,l=3.2):
  cc=np.array(c);rounded(c,l,.88,0,.88,'walnut',True,.06);rounded(c,l+.06,.94,.88,.055,'quartz',False,.035)
  # Recessed kick and vertical timber flutes, quartz top, glazed vitrine to one side.
  for off in np.arange(-l/2+.07,l/2,.11):
   q=cc+u*off-n*.45;ex(rect(q,u,.025,.024),y+.12,.70,'oak',False)
  vc=cc-u*(l*.25);casefp=rect(vc,u,l*.40,.66)
  ex(casefp,y+.936,.035,'metal',False);ex(casefp.boundary.buffer(.009),y+.97,.44,'glass',False);surf(casefp,y+1.41,'glass')
  for j in range(4):
   q=vc+u*(j-1.5)*.23;lathe(q,[(0,.976),(.095,.976),(.10,.993),(0,.993)],'ceramic_0')
   lathe(q,[(.03,.996),(.07,1.01),(.085,1.05),(.06,1.095),(.01,1.11)],'bread',16)
  # Espresso machine: curved boiler, polished group heads and drip tray, cup stack.
  mc=cc+u*l*.24;rounded(mc,.88,.50,.936,.42,'metal',False,.07);rounded(mc,.90,.56,.92,.028,'black',False,.035)
  for off in[-.22,.22]:
   q=mc+u*off-n*.31;tube((q[0],y+1.25,q[1]),(q[0],y+1.11,q[1]),.034,'metal')
   end=q-n*.14;tube((q[0],y+1.13,q[1]),(end[0],y+1.13,end[1]),.014,'black')
  for j in range(3):
   q=mc+u*(j-1)*.19;lathe(q,[(.025,1.36),(.03,1.37),(.045,1.43),(.044,1.445),(.035,1.44)],'ceramic_0')
  # Suspended menu has actual hanging rods and original typography.
  panel(cc+n*.22,l*.75,l*.375,2.30,'cafe_menu',0,-1)
  for side in[-1,1]:
   q=cc+u*side*l*.3+n*.22;tube((q[0],y+2.30+l*.375,q[1]),(q[0],y+4.30,q[1]),.008,'black')
  details.append('木製受付・クォーツ天板・曲面コーヒーマシン・食品ケース・メニュー')
 def kiosk(c):
  cc=np.array(c);rounded(c,.76,.75,0,.85,'black',True,.055)
  # Sloped console and upright video display, original screen content.
  panel(cc+n*.10,.62,.58,1.05,'arcade_screen',0,-1)
  rounded(cc-n*.17,.76,.40,.78,.08,'book_2',False,.03)
  q=cc-n*.27;cyl(q,y+.86,.025,.10,'metal',12);cyl(q,y+.96,.045,.025,'book_3',12)
  for j in range(3):cyl(tuple(cc+u*(j-1)*.11-n*.28),y+.86,.026,.012,'book_'+str(j),12)
  details.append('傾斜操作卓・映像画面・ジョイスティック付きゲーム筐体')
 def luggage(c,j):
  cc=np.array(c);rounded(cc,.38,.23,.04,.57,'leather_'+str(j%2),True,.06)
  for off in[-.13,.13]:
   p=cc+u*off;rounded(p,.07,.09,0,.05,'black',False,.025)
  for off in[-.09,.09]:
   q=cc+u*off;tube((q[0],y+.57,q[1]),(q[0],y+.85,q[1]),.008,'metal')
  a=cc-u*.09;b=cc+u*.09;tube((a[0],y+.85,a[1]),(b[0],y+.85,b[1]),.015,'black')
  for off in[-.08,0,.08]:
   q=cc+u*off-n*.125;bar(tuple(q-n*.006),tuple(q+n*.006),.02,y+.15,.37,'metal')
 def guitar(c,j):
  cc=np.array(c)
  outline=[(-.10,.32),(-.19,.39),(-.21,.50),(-.17,.61),(-.10,.68),(-.14,.78),(-.14,.88),(-.08,.95),(.08,.95),(.14,.88),(.14,.78),(.10,.68),(.17,.61),(.21,.50),(.19,.39),(.10,.32)]
  from shapely import constrained_delaunay_triangles
  pp=Polygon(outline).buffer(.015,quad_segs=4)
  for tr in constrained_delaunay_triangles(pp).geoms:
   aa=list(tr.exterior.coords)[:3]
   for side in[-1,1]:tri('oak'if side==-1 else'walnut',[pos(cc[0]+u[0]*a+n[0]*side*.045,y+b,cc[1]+u[1]*a+n[1]*side*.045)for a,b in aa],(n[0]*side,0,n[1]*side),[[a,b]for a,b in aa],solid=True)
  coords=list(pp.exterior.coords)
  for a,b in zip(coords,coords[1:]):quad('walnut',[pos(cc[0]+u[0]*q[0]+n[0]*side*.045,y+q[1],cc[1]+u[1]*q[0]+n[1]*side*.045)for q,side in[(a,-1),(b,-1),(b,1),(a,1)]],(0,1,0),solid=True)
  for yy,h,w in[(.88,.67,.055),(1.55,.15,.085)]:ex(rect(cc,u,w,.06),y+yy,h,'walnut',True)
  # Sound hole, strings, bridge, and fretted neck, all original geometry.
  hole=[]
  for a in np.linspace(0,math.tau,25):hole.append((math.cos(a)*.042,.69+math.sin(a)*.042))
  for a,b in zip(hole,hole[1:]):tri('black',[pos(cc[0]-n[0]*.047,y+.69,cc[1]-n[1]*.047),pos(cc[0]+u[0]*a[0]-n[0]*.047,y+a[1],cc[1]+u[1]*a[0]-n[1]*.047),pos(cc[0]+u[0]*b[0]-n[0]*.047,y+b[1],cc[1]+u[1]*b[0]-n[1]*.047)],(-n[0],0,-n[1]))
  for off in np.linspace(-.018,.018,6):
   q=cc+u*off-n*.049;tube((q[0],y+.44,q[1]),(q[0],y+1.63,q[1]),.0007,'metal',4)
  for yy in np.linspace(.95,1.52,16):
   q=cc-n*.049;a=q-u*.026;b=q+u*.026;tube((a[0],y+yy,a[1]),(b[0],y+yy,b[1]),.0012,'metal',4)
  for side in[-1,1]:
   q=cc+u*.15*side+n*.08;tube((q[0],y+.04,q[1]),(cc[0],y+.60,cc[1]),.012,'black')
  details.append('胴・ネック・サウンドホール・弦・フレットのあるギターとスタンド')
 # Candidates in a STORE-ALIGNED grid; aisle and entrance clearance have priority over density.
 coords=[];minx,minz,maxx,maxz=usable.bounds if not usable.is_empty else(0,0,0,0)
 # project shop extents onto its own frontage axes
 corners=[np.array(q)for q in[(minx,minz),(maxx,minz),(maxx,maxz),(minx,maxz)]]
 aa=[np.dot(q-e,u)for q in corners];bb=[np.dot(q-e,n)for q in corners]
 for b in np.arange(max(.9,min(bb)+.8),max(bb),3.10 if t in ['食品・カフェ','カフェ・焼菓子','飲食'] else 2.20):
  for a in np.arange(min(aa)+1,max(aa),3.10):
   c=P(a,b);fp=rect(c,u,1.85,.85)
   if usable.covers(fp):coords.append((a,b,c))
 # Fine secondary search prevents coarse-grid aliasing in oblique sales polygons.
 # It also covers sales pockets behind the declared frontage plane; actual polygon
 # containment and protected aisles, not an assumed positive depth, decide placement.
 for b in np.arange(min(bb)+.55,max(bb),1.10):
  for a in np.arange(min(aa)+.55,max(aa),1.10):
   c=P(a,b)
   if usable.covers(rect(c,u,1.90,.90)):coords.append((a,b,c))
 coords.sort(key=lambda q:(q[1],abs(q[0])))
 # Interleave depths instead of exhausting entrance-side rows first.
 if coords:
  depths=sorted(set(round(q[1],6)for q in coords));ordered=[];lo,hi=0,len(depths)-1
  while lo<=hi:
   ordered.append(depths[lo]);lo+=1
   if lo<=hi:ordered.append(depths[hi]);hi-=1
  rank={v:i for i,v in enumerate(ordered)};spread=sorted(coords,key=lambda q:(rank[round(q[1],6)],abs(q[0])))
 else:spread=[]
 target_count=max(6,min(15,int(usable.area/12)+1))if t in ['書籍・文具']else max(6,min(10,int(usable.area/18)+1))

 # Functional checkout at the front, distinct from merchandise display furniture.
 if t not in ['食品・カフェ','カフェ・焼菓子','飲食']:
  for a,b,c in coords:
   fp=rect(c,u,1.55,.85)
   if not fit(fp):continue
   rounded(c,1.45,.72,0,.91,'walnut',True,.045);rounded(c,1.52,.78,.91,.035,'quartz',False,.025)
   cc=np.array(c)+u*.25
   rounded(cc,.30,.22,.945,.025,'black',False,.02)
   tube((cc[0],y+.97,cc[1]),(cc[0],y+1.16,cc[1]),.025,'metal')
   ex(rect(cc,u,.35,.035),y+1.06,.22,'black',False)
   mark(fp);details.append('入口から見える受付・レジカウンターとPOS端末');break
 # Fitting booth is millwork inside the shop, not a new tenant plot or public corridor.
 if t in ['衣料','キッズ']:
  for a,b,c in reversed(coords):
   fp=rect(c,u,1.9,1.9)
   if not fit(fp):continue
   cc=np.array(c)
   for side in[-1,1]:
    q=cc+u*side*.92;ex(rect(q,u,.055,1.85),y,2.25,'wall_chalk',True)
   q=cc+n*.92;ex(rect(q,u,1.85,.055),y,2.25,'wall_chalk',True)
   # Half-retracted curtain leaves a clear 0.90m opening.
   for j in range(9):
    q=cc-u*(.80-j*.09)-n*.88+n*(.025 if j%2 else -.025)
    ex(rect(q,u,.095,.025),y+.08,2.0,'fabric_cream',True)
   mark(fp);details.append('既存売場内の試着ブース・半開きカーテン（入口約0.9m）');break
 # Counters chosen near entrance but outside the canonical central circulation line.
 if t in['食品・カフェ','カフェ・焼菓子','飲食']:
  counters=[]
  for a,b,c in coords:
   fp=rect(c,u,3.4,1.05)
   if fit(fp):counters.append((a,b,c,fp))
  if counters:
   a,b,c,fp=counters[0];cafe_counter(c);mark(fp)
  # Round cafe tables and curved chairs, fewer purposeful pieces instead of shop-wide shelving.
  for a,b,c in spread:
   fp=Point(c).buffer(1.0)
   if not fit(fp):continue
   cyl(c,y,.21,.035,'black',20,True);cyl(c,y+.035,.045,.66,'metal',16,True)
   lathe(c,[(.32,.695),(.36,.71),(.36,.745),(.34,.75)],'oak',24)
   surf(Point(c).buffer(.34,quad_segs=6),y+.75,'oak',solid=True)
   for side in[-1,1]:
    q=np.array(c)+n*side*.68;chair(q,math.atan2(n[1]*side,n[0]*side))
   q=np.array(c)+u*.13;lathe(q,[(.025,.75),(.028,.765),(.04,.83),(.042,.84),(.034,.835)],'ceramic_0',16)
   mark(fp)
   if len(occupied)>=target_count:break
  # compact counter in unusually narrow bakeries
  if not occupied:
   for a,b,c in coords:
    fp=rect(c,u,1.85,.85)
    if fit(fp):cafe_counter(c,1.7);mark(fp);break
 elif t in['衣料','キッズ']:
  for a,b,c in spread:
   fp=rect(c,u,1.90,.85)
   if fit(fp):rack(c);mark(fp)
   if len(occupied)>=target_count:break
  if occupied:details.append('入口側の低い造作台と衣料ショーウィンドウ')
 elif t in['体験・ゲーム']:
  for a,b,c in coords:
   fp=rect(c,u,.90,.90)
   if fit(fp):kiosk(c);mark(fp)
   if len(occupied)>=8:break
 elif t in['旅行・雑貨']:
  for a,b,c in spread:
   fp=rect(c,u,1.9,.8)
   if fit(fp):
    rounded(c,1.8,.75,0,.11,'quartz',True)
    for j in range(3):luggage(np.array(c)+u*(j-1)*.51,j)
    mark(fp);details.append('車輪・伸縮ハンドルのあるスーツケース展示台')
   if len(occupied)>=target_count:break
 else:
  for a,b,c in spread:
   fp=rect(c,u,1.90,.85)
   if fit(fp):
    if t=='楽器':
     for j in range(2):guitar(np.array(c)+u*(j-.5)*.78,j)
    else:case(c,1 if t in['書籍・文具'] and len(occupied)%3==0 else 0)
    mark(fp)
   if len(occupied)>=target_count:break
 # Entrance showcase: a small display plinth strictly outside preserved aisles.
 if occupied and t not in['食品・カフェ','カフェ・焼菓子','飲食']:
  details.append('専用什器・商品は保護した店内主通路の外に設置')
 return occupied,sorted(set(details))
