"""Full B architecture model, same generator for before/after. No original game load or writes."""
from pathlib import Path
import sys,json,math,hashlib,copy,random,gzip
sys.path.insert(0,str(Path(__file__).resolve().parent));from site_v2_common import *
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from shapely import constrained_delaunay_triangles
from shapely.ops import linemerge
P=Path(__file__).resolve().parents[1];A=P/'assets';S=P/'source';before='--baseline'in sys.argv
D=read((Path(__file__).resolve().parents[1]/'source/baseline-v4.json'))if before else read(S/'design-v5.json');fs=D['floors'];ORIGIN=(-429,46);CROP=box(-800,-120,-100,190);M={};coll={};render_group='';lights=[];signs=[];meta={'revision':'v4-plan-reconstruction'if before else'v5-reconfigured','world_origin_xz':ORIGIN,'floors':[],'shops':[],'staff_doors':[],'escalators':[],'fixture_footprints':{},'baseline_reconstruction':before,'NPC_count':0,'main_game_loaded':False,'source_original_sha256':sha((P/'source/master-site-v3.json'))}
def pos(x,y,z):return[round(x-ORIGIN[0],5),round(y,5),round(z-ORIGIN[1],5)]
exec((P/'authoring/mesh_primitives.py').read_text())
def geom(g):
 if g is None:return Polygon()
 if hasattr(g,'geom_type'):return g
 return unary_union([geom(x)for x in g])
def merge(g):return g if g.geom_type=='LineString'else linemerge(g)
def sign(text,c,n,w=4,h=.62,style=0):
 name='arch-sign-'+hashlib.sha256((text+str(style)).encode()).hexdigest()[:14]+'.png';p=A/name
 if not p.exists():
  im=Image.new('RGB',(1024,160),[(33,54,49),(232,225,206),(46,50,63),(108,73,49)][style%4]);dr=ImageDraw.Draw(im);font=ImageFont.truetype(str(A/'NotoSansCJKjp-Regular.otf'),55);sub=ImageFont.truetype(str(A/'NotoSansCJKjp-Regular.otf'),24);color=(237,233,216)if style%4!=1 else(42,65,56);dr.line((30,24,90,24),fill=color,width=4);dr.text((110,17),text,font=font,fill=color);dr.text((110,102),'FIND YOURSELF  |  B WING',font=sub,fill=color);im.save(p)
 signs.append({'file':name,'p':c,'n':n,'w':w,'h':h})
def door(d):meta['staff_doors'].append(d)
def add_staff(s,f,room=False):
 if room:
  bp=s['entry'];u=s['u'];n=s['n'];width=s.get('door_width_m',1.8);label=s['name'];id=s['id']+'-SERVICE'
 else:
  bp=s['back_door'];u=s.get('back_door_u',s['u']);n=s.get('back_door_n',s['n']);width=s.get('back_door_width_m',1.5);label=s['id']+' / 店舗バックヤード';id=s['id']+'-BOH'
 # Pocket door is a declared diagnostic staff door. It never swings into the public route.
 door({'id':id,'store':s['id'],'level':f['level'],'p':pos(bp[0],f['height'],bp[1]),'u':u,'n':n,'clear_width_m':width,'leaf_width_m':width-.006,'height_m':2.2,'hinge_side':-1,'mechanism':'sliding','slide_side':1,'room_label':label,'role':'staff'})
def simple_shelf(fp,y,cat,u,detail=False):
 extrude(fp,y,.12,'walnut',True)
 for hh in[.55,1.1,1.65]:
  extrude(fp,y+hh,.05,'oak',True)
  # Merchandise is a coherent low-detail display, not thousands of individual mesh nodes.
  cc=fp.representative_point();w=max(.4,min(2.4,math.sqrt(fp.area*3)));p=rect((cc.x,cc.y),u,w*.78,.26)
  if fp.buffer(.01).covers(p):extrude(p,y+hh+.05,.28,'goods_green'if'書'in cat else'goods_cream',False)
def fixture_plan(s,f):
 y=f['height'];sales=s['sales'];u=s['u'];e=s['entry'];occupied=[];aisle=s.get('aisles',LineString([e,[e[0]+s['n'][0],e[1]+s['n'][1]]]).buffer(.8));safe=sales.buffer(-.4).difference(aisle.buffer(.15));x0,z0,x1,z1=safe.bounds
 # Category-specific zoning: tall walls + lower islands / garment rails / cafe tables. Keep the protected route free.
 maxcount=36 if s['polygon'].area>1500 else 18 if s['polygon'].area>500 else 10
 for xx in np.arange(x0+1,x1,3.5):
  for zz in np.arange(z0+1,z1,3.5):
   if len(occupied)>=maxcount:break
   dining=any(k in s['category']for k in ['カフェ','飲食','レストラン','フード'])
   fp=rect((xx,zz),u,1.5,1.5)if dining else rect((xx,zz),u,2.4,.65)
   if not safe.covers(fp)or any(fp.distance(q)<1.2 for q in occupied):continue
   occupied.append(fp)
   if dining:
    extrude(fp,y+.73,.06,'oak',True);cylinder((xx,zz),y,.12,.73,'metal',8,True)
    for sg in[-1,1]:
     pp=(xx+s['n'][0]*sg*.98,zz+s['n'][1]*sg*.98);seat=rect(pp,u,.45,.45)
     if sales.covers(seat)and not seat.intersects(aisle):extrude(seat,y+.43,.07,'fabric_cream',True)
   elif'衣料'in s['category']or'キッズ'in s['category']:
    a=(xx-u[0]*1.1,zz-u[1]*1.1);b=(xx+u[0]*1.1,zz+u[1]*1.1);bar(a,b,.06,y+1.55,.05,'metal',True)
    for t in np.linspace(-.85,.85,7):extrude(rect((xx+u[0]*t,zz+u[1]*t),s['n'],.40,.05),y+.65,.85,'fabric_sage',False)
    extrude(fp,y,.12,'walnut',True)
   else:simple_shelf(fp,y,s['category'],u)
 # Counter adjacent to the entrance, clear of the protected spine.
 for sg in[-1,1]:
  cc=(e[0]+s['n'][0]*2.6+u[0]*sg*2.2,e[1]+s['n'][1]*2.6+u[1]*sg*2.2);fp=rect(cc,u,1.8,.7)
  if safe.covers(fp)and all(fp.distance(q)>.6 for q in occupied):extrude(fp,y,.95,'walnut',True);extrude(fp,y+.95,.04,'quartz',False);occupied.append(fp);break
 meta['fixture_footprints'][s['id']]=occupied
for f in fs:
 lev=f['level'];y=f['height'];top=[5.525,10.875,16.4][lev];h=top-y-.7;meta['floors'].append({'label':f['label'],'height':y});floor=f['floor_plate'];envelope=f.get('building_envelope_v5',f['shell'].union(floor.difference(f['shell'])))
 render_group='ARCH-'+str(lev)
 extrude(floor,y-.38,.38,'stone',True)
 ceiling=fs[lev+1]['floor_plate']if lev<2 else floor
 surf(ceiling,y+h,'plaster',False,False,.9)
 # Per-floor exterior follows the corrected bridge lobby width, not the old repeated BODY.
 envelopewall=envelope.boundary.buffer(.12)
 # Preserve source public openings to external links and customer entrances. A physical boundary terminates at the other-wing preview limit.
 for line in lines(f['public'].intersection(envelopewall).boundary):pass
 openingstrips=f['public'].boundary.buffer(.3).intersection(envelopewall)
 outer=envelopewall.difference(f['public'].buffer(.02)).difference(unary_union([s['polygon']for s in f['stores']]+[z['polygon']for z in f['service_zones']]))
 extrude(outer,y,h,'plaster',True)
 if not before:
  extrude(f['construction_poche'],y,h,'plaster',True)
 # Shop solids derive from one shared boundary; glazing only touches sales, never stock.
 for idx,s in enumerate(f['stores']):
  render_group=s['id'];p=s['polygon'];sales=s['sales'];stock=s['backroom'];e=s['entry'];u=s['u'];n=s['n'];dw=s.get('door_width_m',2.4);bp=s['back_door'];bu=s.get('back_door_u',u)
  outside=p.boundary.buffer(.125).intersection(p);partition=stock.boundary.intersection(sales.buffer(.002)).buffer(.10).intersection(p);wall=outside.union(partition);front=sales.boundary.intersection(f['public'].buffer(.006)).difference(stock.buffer(.02));frontlines=lines(front);windows=unary_union([l.buffer(.14,cap_style=2)for l in frontlines]);windowwall=wall.intersection(windows);entrycut=rect(e,u,dw,.9);staffcut=rect(bp,bu,s.get('back_door_width_m',1.5),.9)
  opaque=wall.difference(windows).difference(entrycut).difference(staffcut);mat=['wall_chalk','wall_sand','wall_sage','wall_taupe'][idx%4];extrude(opaque,y,h,mat,True)
  extrude(windowwall.difference(entrycut),y+3.2,h-3.2,mat,True)
  extrude(wall.intersection(entrycut),y+3.5,h-3.5,mat,True);extrude(wall.intersection(staffcut),y+2.218,h-2.218,mat,True)
  for line in frontlines:
   glass=line.buffer(.018,cap_style=2).difference(entrycut).difference(stock.buffer(.03));extrude(glass,y+.10,3.1,'glass',True)
   for t in np.arange(.1,line.length,2.7):
    q=line.interpolate(t)
    if before or not entrycut.buffer(.35).covers(q):extrude(Point(q).buffer(.035,quad_segs=1),y,3.23,'metal',True)
  surf(sales.buffer(-.12),y+.004,['oak_floor','retail_terrazzo','stone'][idx%3],True,False)
  surf(stock.buffer(-.12),y+.006,'service_floor',True,False)
  add_staff(s,f);fixture_plan(s,f)
  # Actual work module has two side racks and a usable middle work aisle.
  if not before and s.get('work_rectangle')is not None:
   co=list(s['work_rectangle'].exterior.coords);a=np.array(co[0]);b=np.array(co[1]);uu=(b-a)/max(np.linalg.norm(b-a),1e-8);nn=np.array([-uu[1],uu[0]]);center=np.array(s['work_rectangle'].centroid.coords[0]);length=np.linalg.norm(b-a)
   for sg in[-1,1]:
    fp=rect(center+nn*sg*.78,uu,max(.8,length-.3),.34)
    protected=LineString(s.get('stock_path',s['main_route'])).buffer(.52)
    if not fp.intersects(protected):simple_shelf(fp,y,'在庫',uu)
  sign(s['category']+' / '+s['id'],pos(e[0]-n[0]*.04,y+3.66,e[1]-n[1]*.04),[-n[0],-n[1]],min(6,max(2.8,dw+1.0)),.58,idx%4)
  meta['shops'].append({'id':s['id'],'level':lev,'category':s['category'],'entry_world':e,'entry_local':pos(e[0],y,e[1]),'target_local':pos(e[0]+n[0],y,e[1]+n[1]),'plot_m2':p.area,'source_net_sales_m2':s.get('old_net_sales_m2'),'net_sales_m2':s.get('net_sales_m2')})
 render_group='ARCH-'+str(lev)
 for z in f['service_zones']:
  p=z['polygon'];e=z['entry'];u=z['u'];n=z.get('n',[-u[1],u[0]])
  if not p.covers(Point(e[0]+n[0]*.4,e[1]+n[1]*.4)):n=[-n[0],-n[1]]
  z['n']=n;wall=p.boundary.buffer(.125).intersection(p);cut=rect(e,u,z.get('door_width_m',1.8),.9);extrude(wall.difference(cut),y,h,'plaster',True);extrude(wall.intersection(cut),y+2.218,h-2.218,'plaster',True);surf(p.buffer(-.13),y+.005,'service_floor',True,False);add_staff(z,f,True)
  if before:continue
  surf(p.buffer(-.13),y+3.15,'plaster',False,False)
  w=z['planned_width_m'];d=z['planned_depth_m'];E=np.array(e);U=np.array(u);N=np.array(n);local=lambda x,zz:tuple(E+U*x+N*zz)
  if'-T'in z['id']:
   # A 120sqm programme with actual divided functions, not a 1000sqm anonymous closed room.
   for xx,aa,bb in[(1,2,d)]:
    g=rect(local(xx,(aa+bb)/2),N,bb-aa,.15);g=g.difference(unary_union([rect(local(xx,zz),N,1.2,.8)for zz in[4,7.5,10.5]]));extrude(g,y,3.1,'plaster',True)
   for zz,aa,bb in[(2,-w/2,w/2),(8,-w/2,1),(6,1,w/2),(9,1,w/2)]:
    g=rect(local((aa+bb)/2,zz),U,bb-aa,.15);gap=rect(local((aa+bb)/2,zz),U,1.2,.8);extrude(g.difference(gap),y,3.1,'plaster',True)
   for xx,zz in[(-3.6,3.5),(-1.8,3.5),(-3.6,6),(-1.8,6)]:
    fp=rect(local(xx,zz),U,1.4,.7);extrude(fp,y,.74,'oak',True);extrude(rect(local(xx,zz+.6),U,.45,.45),y+.43,.08,'fabric_navy',True)
   extrude(rect(local(-2,10),U,2.4,1.2),y+.73,.06,'oak',True)
   for zz in[7,10.5]:simple_shelf(rect(local(4.2,zz),N,2,.45),y,'清掃用品',N)
  else:
   # Two rows of 2.2x3m cages, 4m central working aisle; exact row count follows the actual room dimensions.
   count=int(math.floor((d-2.8+1e-8)/2.2));z['cage_count']=2*count;z['cage_dimensions_m']=[2.2,3.0];z['cage_polygons']=[]
   for side in[-1,1]:
    for j in range(count):
     cc=local(side*(w/2-1.5),2.8+(j+.5)*2.2);fp=rect(cc,N,2.2,3.0);z['cage_polygons'].append(fp)
     for t in[-1,1]:simple_shelf(rect(np.array(cc)+U*t*1.15,N,1.9,.42),y,'共用在庫',N)
   extrude(rect(local(-w/2+2,1.4),U,3.2,1.1),y,.85,'wood',True)
  meta.setdefault('service_rooms',[]).append(z)
 # Existing core rooms, partitions and fixtures retain their source geometry; elevator control is not added.
 for c in f['cores']:
  corewall=geom(c.get('room_wall_solids')).union(geom(c.get('cubicle_wall_solids')));outercore=c['outline'].boundary.buffer(.12);e=c['entry'];angle=math.radians(c['angle']);u=[math.cos(angle),math.sin(angle)];outercore=outercore.difference(rect(e,u,3.6,1.0));extrude(corewall.union(outercore),y,3.3,'plaster',True)
  for door0 in c.get('doors',[]):
   p=door0['p'];axis=door0['axis'];ww=door0['w'];extrude(rect(p,axis,ww,.20),y+2.25,1.05,'plaster',True)
   if door0['id']in ['ST','EV']:extrude(rect(p,axis,ww-.015,.05),y,2.22,'metal',True)
  for obj in c.get('fixtures',[]):
   g=obj.get('geom',obj.get('polygon'))
   if g is not None:extrude(g,y,.85,'ceramic_0',True)
  for label in ['EV','WC','階段']:sign(label+' / '+c['id'],pos(e[0],y+3.4,e[1]),[0,-1],3.4,.48,1)
 # Plazas stay open; use source seats and planters, no packing unused floor with arbitrary props.
 for obj in f.get('furniture',[]):
  g=obj['geom'];kind=obj['kind'];cc=g.representative_point()
  if kind=='bench':extrude(g,y+.42,.08,'oak',True)
  elif'plant'in kind:
   extrude(g,y,.5,'dark_stone',True);cylinder((cc.x,cc.y),y+.5,.65,1.0,'leaf',8,False)
 # Balustrades have a real base and glass edge; the 0.28m floor collar is counted as structure.
 for vp in polys(f['void']):
  ring=vp.exterior;g=LineString(ring.coords).buffer(.05);extrude(g,y+.20,.95,'glass',True);barrier=LineString(ring.coords).buffer(.13).difference(vp);extrude(barrier,y,.20,'dark_stone',True)
 for obj in f.get('machine_islands',[]):extrude(obj['polygon'],y,.12,'metal',True)
 # Discrete ceiling luminaires along actual public floor only.
 x0,z0,x1,z1=f['public'].bounds
 for xx in np.arange(x0+4,x1,12):
  for zz in np.arange(z0+4,z1,12):
   fp=rect((xx,zz),(1,0),2.4,.12)
   if f['public'].buffer(-1).covers(fp):extrude(fp,y+h-.04,.04,'light',False)
# Whole-wing escalators: preserve all twelve source banks and their positions; inclined support + visible animated tread system.
esc={e['id']:e for f in fs for e in f['escalators']}
for id,e in esc.items():
 lo=fs[e['levels'][0]]['height'];hi=fs[e['levels'][1]]['height'];cx,cz=e['c'];u=e['u'];lat=(-u[1],u[0]);run=e['run_m'];rise=hi-lo;render_group='ESC-'+id
 a=np.array(e['c'])-np.array(u)*run/2;b=np.array(e['c'])+np.array(u)*run/2
 pts=[pos(*(a+np.array(lat)*side),lo if j==0 else hi)for j in[] for side in[]]if False else[]
 p0=pos(a[0]+lat[0]*1.2,lo,a[1]+lat[1]*1.2);p1=pos(a[0]-lat[0]*1.2,lo,a[1]-lat[1]*1.2);p2=pos(b[0]-lat[0]*1.2,hi,b[1]-lat[1]*1.2);p3=pos(b[0]+lat[0]*1.2,hi,b[1]+lat[1]*1.2);normal=(0,1,0);quad('step',[p0,p1,p2,p3],normal,solid=True)
 for side in[-1,1]:
  aa=a+np.array(lat)*side*1.0;bb=b+np.array(lat)*side*1.0
  vertices=[pos(aa[0],lo+.12,aa[1]),pos(bb[0],hi+.12,bb[1]),pos(bb[0],hi+1.0,bb[1]),pos(aa[0],lo+1.0,aa[1])];quad('glass',vertices,(lat[0],0,lat[1]),solid=True)
 for end,yy,sg in[(a,lo,-1),(b,hi,1)]:
  center=end+np.array(u)*sg*.75;extrude(rect(center,u,1.5,2.4),yy-.25,.25,'step',True)
 meta['escalators'].append({'id':id,'levels':e['levels'],'direction':e['direction'],'c':pos(cx,lo,cz),'u':u,'run_m':run,'rise_m':rise,'tread_width_m':1.32,'shaft_width_m':2.4,'landing_width_m':3.6,'test_start':pos(*(a-np.array(u)*.8),lo)if False else pos(a[0]-u[0]*.8,lo,a[1]-u[1]*.8),'test_end':pos(b[0]+u[0]*.8,hi,b[1]+u[1]*.8)})
# Structural skylight/soffit with outdoor sky over the existing three large atria.
f=fs[2];roof_y=16.4
for q in polys(f['void']):
 surf(q,roof_y,'roof_glass',True,False,.95)
 x0,z0,x1,z1=q.bounds
 for xx in np.arange(x0,x1,8):
  line=LineString([(xx,z0),(xx,z1)]).intersection(q)
  for part in lines(line):aa=part.coords[0];bb=part.coords[-1];bar(aa,bb,.14,roof_y-.22,.22,'metal',False)
meta['mesh_triangles']=sum(len(v['v'])//9 for v in M.values());meta['collision_triangles']=sum(len(v)//9 for v in coll.values());meta['NPC_count']=0
name='-before'if before else''
with gzip.open(A/('geometry'+name+'.json.gz'),'wt',encoding='utf8',compresslevel=6)as fh:json.dump({'surfaces':M,'colliders':coll,'signs':signs,'lights':lights},fh,separators=(',',':'))
write(S/('scene-manifest'+name+'.json'),meta)
print('MODEL_EXPORT',name or'after',meta['mesh_triangles'],'triangles',len(meta['shops']),'shops',len(meta['escalators']),'escalators',flush=True)
