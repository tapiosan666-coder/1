"""Three individually developed fitouts, constrained to existing sales polygons and aisles."""
import math
import numpy as np
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
TARGETS={'B1-017':'bookshop','B1-040':'cafe','B1-043':'fashion'}
def detailed(ctx,s,lev,y,idx,h):
 ex,surf,bar,rect,cyl,quad,pos=[ctx[k]for k in ['extrude','surf','bar','rect','cylinder','quad','pos']]
 u=np.array(s['u']);n=np.array(s['n']);e=np.array(s['entry']);typ=TARGETS[s['id']]
 occupied=[];features=[];details=[];ceiling=[5.525,10.875,16.4][lev]-y-.7
 sales=s['sales'].intersection(ctx['CROP']);aisle=s['aisles'].buffer(.36)
 free=sales.buffer(-.22).difference(aisle);wallfree=sales.buffer(-.008).difference(aisle)
 def fits(fp,wall=False,clear=.90):return (wallfree if wall else free).covers(fp)and all(fp.distance(q)>clear for q in occupied)
 def mark(fp,kind):occupied.append(fp);features.append({'kind':kind,'footprint':fp})
 def panel(c,tangent,normal,w,hh,yy,slot):
  c=np.array(c);a=np.array(tangent);nn=np.array(normal);C=lambda xx,zz:pos(c[0]+a[0]*xx,y+zz,c[1]+a[1]*xx)
  col=slot%4;row=slot//4;uv=[[(col+.002)/4,(row+.998)/4],[(col+.998)/4,(row+.998)/4],[(col+.998)/4,(row+.002)/4],[(col+.002)/4,(row+.002)/4]]
  quad('editorial_v3',[C(-w/2,yy),C(w/2,yy),C(w/2,yy+hh),C(-w/2,yy+hh)],(nn[0],0,nn[1]),uv)
 def led(c,axis,length,height):
  c=np.array(c);a=np.array(axis);bar(tuple(c-a*length/2),tuple(c+a*length/2),.045,y+height,.025,'light')
 def spot(c,height=3.35,energy=.65):
  ctx['lights'].append({'p':pos(c[0],y+height,c[1]),'level':lev,'type':'shop','energy':energy,'room_index':idx,'store':s['id'],'fitout_v3':True})
 def tabletop(c,w,d,yy,material='oak'):
  ex(rect(c,u,w,d),y+yy,.045,material,True)
  for a in[-1,1]:
   for b in[-1,1]:
    q=np.array(c)+u*a*(w/2-.12)+n*b*(d/2-.12);ex(rect(q,u,.055,.055),y,.0+yy,'metal',True)
 def books_wall(c,a,nn,width=2.35):
  c=np.array(c);a=np.array(a);nn=np.array(nn)
  ex(rect(c,a,width,.48),y,.13,'walnut',True)
  for side in[-1,1]:ex(rect(c+a*side*(width/2-.025),a,.045,.44),y+.13,2.34,'oak',True)
  ex(rect(c-nn*.215,a,width,.035),y+.13,2.34,'oak',True)
  for shelf_no,hh in enumerate([.18,.56,.94,1.32,1.70,2.08]):
   ex(rect(c,a,width,.44),y+hh,.028,'oak',False)
   for j in range(int(width/.075)-2):
    p=c+a*(-width/2+.12+j*.075)+nn*.035;bw=.045+(j%3)*.006;bh=.21+(j%5)*.018
    ex(rect(p,a,bw,.205),y+hh+.028,bh,'book_'+str((j+shelf_no+idx)%6),False)
    # Cover and spine titles are two small foil rules on the outward face.
    for h0 in [.08,.13]:
     pp=p+nn*.105;bar(tuple(pp-a*bw*.30),tuple(pp+a*bw*.30),.003,y+hh+h0,.003,'gold')
  label=c+nn*.26;panel(label,a,nn,width-.12,.24,2.20,idx%4)
  led(c+nn*.25,a,width-.12,2.46)
 def fold_wall(c,a,nn,width=2.35):
  c=np.array(c);a=np.array(a);nn=np.array(nn);ex(rect(c,a,width,.48),y,.12,'walnut',True)
  ex(rect(c-nn*.215,a,width,.035),y+.12,2.30,'wall_taupe',True)
  for hh in[.33,.88,1.43,1.98]:
   ex(rect(c,a,width,.44),y+hh,.03,'oak',False)
   for j in range(4):
    for k in range(3):
     p=c+a*((j-1.5)*.50);ex(rect(p,a,.39,.29),y+hh+.032+k*.038,.035,['fabric_cream','fabric_navy','fabric_sage','fabric_rust'][(j+k)%4],False)
  panel(c+nn*.25,a,nn,width-.12,.27,2.08,8+idx%3);led(c+nn*.25,a,width-.12,2.43)
 # Concrete rear/side wall faces, including the already declared stock partition.
 front=unary_union(ctx['fronts'].get(s['id'],[])).buffer(.15)
 stockcut=Point(s['back_door']).buffer(1.2)
 partition=s['backroom'].boundary.intersection(s['sales'].buffer(.002))
 boundary=s['polygon'].boundary.union(partition).intersection(s['sales'].buffer(.002)).difference(front).difference(stockcut)
 modules=[]
 for line in ctx['lines'](boundary):
  coords=list(line.coords)
  for p0,p1 in zip(coords,coords[1:]):
   le=math.dist(p0,p1)
   if le<2.6:continue
   axis=np.array(p1)-p0;axis/=le;normal=np.array([-axis[1],axis[0]])
   for sign in[1,-1]:
    nn=normal*sign
    for distance in np.arange(1.35,le-1.25,2.75):
     wall=np.array(p0)+axis*distance;c=wall+nn*.295;fp=rect(c,axis,2.35,.56)
     if fits(fp,True,.45):modules.append((c,axis,nn,fp))
 # Dense search, separated by actual circulation clearance rather than a maximum count of copies.
 points=[];x0,z0,x1,z1=free.bounds
 for xx in np.arange(x0+.4,x1,.75):
  for zz in np.arange(z0+.4,z1,.75):
   p=np.array([xx,zz]);points.append((float(np.linalg.norm(p-e)),p))
 points.sort(key=lambda q:q[0])
 def place(w,d,kind,draw,order=None,clear=.9):
  seq=points if order is None else order
  for _,p in seq:
   fp=rect(p,u,w,d)
   if fits(fp,False,clear):draw(p);mark(fp,kind);return p
  return None
 def checkout(p,width=2.45):
  ex(rect(p,u,width,.78),y,.92,'walnut',True);ex(rect(p,u,width+.07,.85),y+.92,.035,'quartz',False)
  for j in range(int(width/.12)):
   q=p+u*(j-(int(width/.12)-1)/2)*.12-n*.40;ex(rect(q,u,.06,.018),y+.07,.79,'oak',False)
  p0=p+u*min(.65,width*.25);ex(rect(p0,u,.32,.035),y+1.10,.24,'black',False);cyl(p0,y+.955,.035,.19,'metal',12)
  # bag rack, work tray, receipt printer; all inside the reserved counter.
  ex(rect(p-u*min(.65,width*.25),u,.32,.25),y+.955,.17,'black',False)
  panel(p-n*.435,u,-n,1.1,.28,.48,3 if typ=='bookshop'else 11)
 if typ!='cafe':
  if place(2.65,1.1,'checkout_pos_bagging_and_queue_edge',checkout)is None:place(1.65,1.1,'compact_checkout_pos_and_receipt_printer',lambda p:checkout(p,1.45))
 # First wall elements give the shop a recognisable perimeter, without filling any public floor.
 for c,axis,nn,fp in modules:
  if len(occupied)>=(10 if typ=='bookshop'else 2 if typ=='fashion'else 2):break
  if not fits(fp,True,.45):continue
  if typ=='bookshop':books_wall(c,axis,nn);kind='wall_bookcase_with_category_and_shelf_lighting'
  elif typ=='fashion':fold_wall(c,axis,nn);kind='wall_folded_knit_display'
  else:
   # Continuous ribbed wainscot, framed botanical graphic and condiment shelf.
   ex(fp,y,.10,'walnut',True)
   for j in range(24):
    q=c+axis*((j-11.5)*.095)-nn*.20;ex(rect(q,axis,.065,.035),y+.10,1.05,'wood',False)
   panel(c-nn*.16,axis,nn,1.7,1.2,1.35,4+idx%3)
   ex(rect(c,axis,2.2,.40),y+1.08,.045,'oak',False)
   for j in range(4):h['bowl'](c+axis*(j-1.5)*.42,1.125,j%3)
   kind='cafe_wall_joinery_art_condiments'
  mark(fp,kind)
 if typ=='cafe':
  def foodline(p):
   h['cafe_counter'](p,3.3)
   # Staff workline behind the existing serving counter, no new structural room.
   back=p+n*.75;ex(rect(back,u,3.25,.58),y,.85,'metal',True);ex(rect(back,u,3.28,.61),y+.85,.035,'quartz',False)
   for j in[-1,0,1]:
    q=back+u*j*.98;ex(rect(q,u,.86,.028),y+.1,.68,'metal',False)
    bar(tuple(q-u*.14),tuple(q+u*.14),.018,y+.70,.02,'black')
   # Sink bowl and a compact oven front with glazed chamber.
   q=back+u*.9;ex(rect(q,u,.46,.33),y+.887,.025,'dark_stone',False)
   q=back-u*.9-n*.32;ex(rect(q,u,.56,.045),y+.30,.37,'black',False)
   led(p,u,3.15,3.25);spot(p,3.15,.85)
  place(3.55,2.2,'cafe_serving_counter_staff_workline_sink_oven',foodline)
  # Wall-adjacent banquette: upholstered back, two square tables, chair and tableware.
  def booth(p):
   ex(rect(p+n*.53,u,2.35,.58),y,.40,'walnut',True);ex(rect(p+n*.53,u,2.32,.56),y+.40,.11,'fabric_sage',True)
   ex(rect(p+n*.80,u,2.35,.10),y+.46,.70,'fabric_sage',True)
   for j in[-1,1]:
    c=p+u*j*.58-n*.12;tabletop(c,.72,.70,.73);h['bowl'](c,.78,0)
    h['chair'](c-n*.75,math.atan2(-n[1],-n[0]))
  place(2.65,2.5,'upholstered_banquette_tables_and_loose_seating',booth,order=list(reversed(points)))
  for _ in range(6):
   def table(p):
    cyl(p,y,.20,.035,'black',16,True);cyl(p,y+.035,.045,.67,'metal',12,True);surf(Point(p).buffer(.42,quad_segs=8),y+.75,'oak',True)
    for side in[-1,1]:h['chair'](p+n*side*.79,math.atan2(n[1]*side,n[0]*side))
    h['bowl'](p,.76,0)
    # Pendant shade with an actual local light beneath, above 2.65m clear height.
    h['lathe'](p,[(.27,2.69),(.32,2.74),(.22,2.89),(.06,3.01)],'bronze',20)
    cyl(p,y+3.01,.008,ceiling-3.01,'black',8);cyl(p,y+2.70,.20,.015,'light',16);spot(p,2.65,.40)
   if place(2.25,2.25,'round_table_chairs_crockery_pendant',table) is None:break
 elif typ=='bookshop':
  # Tall wall collection, lower islands, broad face-out editorial tables and reading seats.
  for j in range(2):
   def editorial(p):
    tabletop(p,1.85,.92,.79)
    for k in range(5):
     q=p+u*(k-2)*.32
     ex(rect(q,u,.24,.32),y+.835,.075,'book_'+str(k),False)
     # Face-out artwork is genuinely on a sloped display stand.
     panel(q-n*.12,u,-n,.21,.29,.91,k)
    panel(p-n*.47,u,-n,1.2,.17,.57,2)
   place(2.05,1.15,'new_release_faceout_editorial_table',editorial)
  def reading(p):
   for side in[-1,1]:h['chair'](p+u*side*.65,math.atan2(-n[1],-n[0]))
   tabletop(p,.48,.50,.48);h['bowl'](p,.53,0)
  place(2.2,1.65,'reading_nook_side_table',reading,order=list(reversed(points)))
  for j in range(11):
   if place(1.95,.90,'low_double_sided_book_island',lambda p:h['case'](p,0),order=points if j%2==0 else list(reversed(points)),clear=1.15)is None:break
 else:
  def booth(p):
   for side in[-1,1]:ex(rect(p+u*side*.86,u,.06,1.65),y,2.25,'wall_taupe',True)
   ex(rect(p+n*.80,u,1.72,.06),y,2.25,'wall_taupe',True)
   for j in range(9):ex(rect(p-u*(.72-j*.09)-n*.78,u,.085,.035),y+.05,2.12,'fabric_cream',True)
   panel(p-n*.82,u,-n,.70,.18,2.08,10)
  place(1.9,1.9,'fitting_room_curtain_and_sign',booth,order=list(reversed(points)))
  def folds(p):
   tabletop(p,1.8,.88,.81)
   for j in range(4):
    for k in range(3):ex(rect(p+u*(j-1.5)*.39,u,.33,.48),y+.86+k*.04,.035,['fabric_cream','fabric_navy','fabric_sage','fabric_rust'][j],False)
  place(2.05,1.10,'folded_knit_feature_table',folds)
  for j in range(6):
   if place(1.95,.95,'freestanding_fashion_rail',h['rack'],order=points if j%2==0 else list(reversed(points)),clear=1.1)is None:break
  # Low seating for trying shoes, distinct from product display.
  def seat(p):ex(rect(p,u,1.25,.54),y,.35,'walnut',True);ex(rect(p,u,1.26,.56),y+.35,.12,'fabric_sage',True)
  place(1.45,.80,'customer_fitting_bench',seat)
 # Discrete ceiling light rafts above shop fixtures, never the common atrium.
 for feature in features[::3]:
  c=feature['footprint'].centroid;p=np.array([c.x,c.y]);raft=rect(p,u,1.7,.72)
  if sales.buffer(-.05).covers(raft):
   ex(raft,y+3.5,.045,'wall_chalk',False);led(p,u,1.45,3.485);spot(p,3.42,.55)
 details.extend({'bookshop':['壁面書架・カテゴリサイン・棚下照明','新刊平台・レジ・読書席・低い回遊書架'],'cafe':['カウンター・スタッフ作業台・シンク・オーブン','腰壁・アート・食器棚・ベンチ席・吊照明'],'fashion':['壁面ニット陳列・レジ・試着室・ブランドサイン','ハンガーラック・畳み台・試着用ベンチ']}[typ])
 ctx['meta'].setdefault('detailed_fitouts',[]).append({'id':s['id'],'type':typ,'features':features,'sales_area_m2':sales.area,'fixture_reserved_m2':unary_union(occupied).area,'protected_aisle_m2':s['aisles'].area,'wall_modules':sum('wall_'in q['kind']for q in features),'scope':'Nonstructural retail fitout; original plot/entry/aisles/stock door unchanged','not_complete':['MEP sizing','fire/life-safety review','operational kitchen capacity','all customer-reachable fixture faces','human-operated Windows playtest']})
 return occupied,details
