#!/usr/bin/env python3
"""Build the isolated B Time Plaza from immutable site-v3 polygons. No game writes."""
from pathlib import Path
import sys,json,hashlib,math,shutil,random
sys.path.append('/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
from retail_v2 import fit_shop
from stock_roles import normalize as normalize_stock_roles
from floor_contract import production_gate,apply_review_proposals
from materials_v2 import build_assets
from editorial_assets_v3 import build as build_editorial
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
from shapely.geometry import shape,mapping,Polygon,LineString,Point,box
from shapely.ops import unary_union,nearest_points
from shapely import constrained_delaunay_triangles,affinity
P=Path(__file__).resolve().parents[1]; R=Path('/workspace/1'); A=P/'assets';S=P/'source'
for x in [A,S,P/'evidence',P/'licenses']:x.mkdir(exist_ok=True)
rng=np.random.default_rng(42626);random.seed(42626)
source=R/'docs/site-correction-v3/geometry.json';raw=json.loads(source.read_text())
def dec(v):
 if isinstance(v,dict):return shape(v)if 'type'in v and ('coordinates'in v or 'geometries'in v) else{k:dec(x)for k,x in v.items()}
 if isinstance(v,list):return[dec(x)for x in v]
 return v
baseline_privacy=dec(json.loads((S/'baseline-stock-privacy.json').read_text()))
D=dec(raw);fs=[f for f in D['floors']if f['wing']=='B' and f['level']in[0,1,2]]
proposal=dec(json.loads((S/'root-gap-review/refined-enclosure-proposals.json').read_text()));audit=json.loads((S/'root-gap-review/full-B-root-audit.json').read_text());gate=production_gate(audit)
if not gate['can_export_production']and '--review-draft'not in sys.argv:raise SystemExit('PRODUCTION_EXPORT_BLOCKED: unowned floor remains. See root-gap-review. Use --review-draft only for a clearly labelled comparison prototype.')
CROP=box(-512,-16,-349,124);ORIGIN=(-429,46)
def polys(g):return[]if g.is_empty else[g]if g.geom_type=='Polygon'else[p for p in getattr(g,'geoms',[])if p.geom_type=='Polygon']
def lines(g):return[]if g.is_empty else[g]if g.geom_type=='LineString'else[p for p in getattr(g,'geoms',[])if p.geom_type=='LineString']
def enc(v):return mapping(v)if hasattr(v,'geom_type')else v.item()if hasattr(v,'item')else str(v)
def save(p,d):p.write_text(json.dumps(d,default=enc,ensure_ascii=False,separators=(',',':')))
def pos(x,y,z):return[round(x-ORIGIN[0],5),round(y,5),round(z-ORIGIN[1],5)]
M={};coll={};counts={};meta={'construction_repairs':[],'staff_doors':[],'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source':'docs/site-correction-v3/geometry.json','world_origin_xz':ORIGIN,'crop_world_xz':CROP.bounds,'unit':'metre','floors':[],'escalators':[],'shops':[],'art_proposals':[]}
# Material-batched triangle data. Clockwise front faces, explicit physically oriented normals.
def tri(mat,pts,n,uv=None,solid=False,shade=1):
 a,b,c=[np.array(p,dtype=float)for p in pts]
 if np.dot(np.cross(b-a,c-a),n)>0:pts=[pts[0],pts[2],pts[1]];uv=[uv[0],uv[2],uv[1]]if uv else None
 group=str(globals().get('render_group',''))
 if not group:
  center=np.mean(pts,axis=0);group='ARCH-%d-%d-%d'%(math.floor(center[0]/24),math.floor(center[1]/5.5),math.floor(center[2]/24))
 k=mat+'@@'+group;data=M.setdefault(k,{'v':[],'n':[],'uv':[],'c':[]})
 for i,p in enumerate(pts):data['v']+=p;data['n']+=list(n);data['uv']+=(uv[i]if uv else[p[0],p[2]]);data['c']+=[shade,shade,shade,1]
 if solid:coll.setdefault(mat,[]).extend(sum(pts,[]))
def quad(mat,pts,n,uv=None,solid=False,shade=1):
 for ids in[(0,1,2),(0,2,3)]:tri(mat,[pts[i]for i in ids],n,[uv[i]for i in ids]if uv else None,solid,shade)
def surf(g,y,mat,up=True,solid=False,shade=1):
 for poly in polys(g):
  if poly.area<1e-8:continue
  cells=[]
  if poly.area>35:
   x0,z0,x1,z1=poly.bounds
   grid=1.25 if mat=='stone'and solid else 3
   for xx in np.arange(math.floor(x0/grid)*grid,x1,grid):
    for zz in np.arange(math.floor(z0/grid)*grid,z1,grid):cells.extend(polys(poly.intersection(box(xx,zz,xx+grid,zz+grid))))
  else:cells=[poly]
  triangles=[t for cell in cells for t in constrained_delaunay_triangles(cell).geoms]
  for t in triangles:
   if not poly.covers(t.representative_point()):continue
   coords=list(t.exterior.coords)[:3];tri(mat,[pos(x,y,z)for x,z in coords],(0,1 if up else -1,0),[[x,z]for x,z in coords],solid,shade)
def extrude(g,y,h,mat,solid=True,shade=1):
 if g.is_empty or h<=0:return
 surf(g,y+h,mat,True,solid,shade);surf(g,y,mat,False,solid,shade*.85)
 for po in polys(g):
  if mat in ['plaster','wall_sand','wall_sage','wall_chalk','wall_taupe']and po.area<.00001:continue
  for ring in[po.exterior,*po.interiors]:
   co=list(ring.coords)
   # derive wall normal by testing which side is outside the solid, including holes
   for (x,z),(xx,zz)in zip(co,co[1:]):
    dx,dz=xx-x,zz-z;length=math.hypot(dx,dz)
    if length<1e-7:continue
    nx,nz=dz/length,-dx/length
    if po.contains(Point((x+xx)/2+nx*.001,(z+zz)/2+nz*.001)):nx,nz=-nx,-nz
    quad(mat,[pos(x,y,z),pos(xx,y,zz),pos(xx,y+h,zz),pos(x,y+h,z)],(nx,0,nz),[[0,y],[length,y],[length,y+h],[0,y+h]],solid,shade)
def rect(c,u,l,w):
 n=(-u[1],u[0]);return Polygon([(c[0]+a*u[0]+b*n[0],c[1]+a*u[1]+b*n[1])for a,b in[(-l/2,-w/2),(l/2,-w/2),(l/2,w/2),(-l/2,w/2)]])
def bar(a,b,width,y,h,mat,solid=False,shade=1):
 l=math.dist(a,b)
 if l>.002:extrude(rect(((a[0]+b[0])/2,(a[1]+b[1])/2),((b[0]-a[0])/l,(b[1]-a[1])/l),l,width),y,h,mat,solid,shade)
def cylinder(c,y,r,h,mat,segments=16,solid=False):
 extrude(Point(c).buffer(r,quad_segs=segments//4),y,h,mat,solid)
def texture(name,base,noise=.02,wood=False):
 n=512;zz,xx=np.mgrid[:n,:n];field=rng.normal(0,noise,(n,n));
 if wood:field+=np.sin(xx*.075+np.sin(zz*.012)*3)*.025+np.sin(xx*.3+np.sin(zz*.005)*5)*.02
 a=np.clip(np.array(base)[None,None,:]+field[:,:,None],0,1)
 if not wood:
  for j in range(900):
   x,z=rng.integers(0,n,2);r=int(rng.integers(1,4));a[max(0,z-r):z+r,max(0,x-r):x+r]+=rng.uniform(-.08,.08)
 Image.fromarray((np.clip(a,0,1)*255).astype('uint8')).save(A/(name+'_albedo.png'))
 height=field;dx=(np.roll(height,-1,1)-np.roll(height,1,1))*.8;dy=(np.roll(height,-1,0)-np.roll(height,1,0))*.8
 normals=np.stack([-dx,-dy,np.ones_like(dx)],2);normals/=np.linalg.norm(normals,axis=2,keepdims=True)
 Image.fromarray(((normals*.5+.5)*255).astype('uint8')).save(A/(name+'_normal.png'))
 rough=np.clip(.48+field*.8,.15,.85);Image.fromarray((rough*255).astype('uint8')).save(A/(name+'_roughness.png'))
for name,base,wood in[('stone',(.79,.77,.71),False),('wood',(.43,.27,.145),True),('plaster',(.88,.865,.82),False),('dark_stone',(.24,.26,.25),False)]:texture(name,base,.012,wood)
shutil.copy(R/'assets/fonts/NotoSansCJKjp-Regular.otf',A/'NotoSansCJKjp-Regular.otf')
shutil.copy(R/'third_party/noto-cjk-COPYRIGHT.txt',P/'licenses/Noto-OFL.txt')
shutil.copy(R/'third_party/godot-LICENSE.txt',P/'licenses/Godot-MIT.txt');shutil.copy(R/'third_party/godot-COPYRIGHT.txt',P/'licenses/Godot-COPYRIGHT.txt')
build_assets(A);build_editorial(A)
font_path=str(A/'NotoSansCJKjp-Regular.otf');font=lambda n:ImageFont.truetype(font_path,n)
# Original, fictional storefront designs. No real tenant logos.
brands=['TONE & TABLE','栞書房','SORA / LIVING','ATELIER 07','木と、日々。','mellow cafe','LINO SHOES','TRAVEL NOTE','白花 / HAKKA','petit voyage','COFFEE / 1986','BOOKS & PAPER']
categories={'衣料':'FASHION & DAILY WEAR','書籍・文具':'BOOKS · STATIONERY','生活雑貨':'LIVING · HOME','食品・カフェ':'COFFEE & BAKERY','靴・鞄':'SHOES & BAGS','美容・ケア':'BEAUTY & CARE','カフェ・焼菓子':'COFFEE & BAKERY','旅行・雑貨':'TRAVEL & GIFTS','飲食':'DINING & KITCHEN','ホビー':'HOBBY & CULTURE','楽器':'MUSIC & SOUND','体験・ゲーム':'PLAY & EXPERIENCE','キッズ':'KIDS & FAMILY'}
def sign_asset(i,brand,cat):
 bg=[(28,48,44),(242,235,216),(41,48,57),(80,46,34)][i%4];fg=(226,214,178)if i%4!=1 else(39,59,52)
 im=Image.new('RGB',(1536,384),bg);dr=ImageDraw.Draw(im)
 dr.line((50,46,1486,46),fill=fg,width=2);dr.line((50,338,1486,338),fill=fg,width=2)
 dr.ellipse((80,108,208,236),outline=fg,width=3);dr.line((110,175,178,175),fill=fg,width=3);dr.line((144,142,144,208),fill=fg,width=3)
 dr.text((850,146),brand,font=font(76 if len(brand)<18 else 62),fill=fg,anchor='mm');dr.text((850,259),categories.get(cat,'LIFESTYLE & CULTURE'),font=font(28),fill=fg,anchor='mm')
 fn=f'sign-{i:03}.png';im.save(A/fn);return fn
# Build source-exact slabs, walls, apertures, tenant fitouts and common ceiling assemblies.
esc_unique={}; floor_walk={};shop_tests=[];signs=[];lights=[];fronts={};routing_solids={i:[]for i in range(3)};slab_additions=[]
applied_proposals=apply_review_proposals(fs,proposal,rect,Polygon,unary_union)
meta['root_enclosure_proposals']=applied_proposals;meta['production_export_gate']=gate;meta['review_draft']=True;meta['design_proposal_sha256']=hashlib.sha256((S/'root-gap-review/refined-enclosure-proposals.json').read_bytes()).hexdigest()
for f in fs:
 lev=f['level'];y=f['height'];top=[5.525,10.875,16.4][lev];meta['floors'].append({'label':f['label'],'height':y,'floor_area_in_slice_m2':f['floor_plate'].intersection(CROP).area,'void_area_in_slice_m2':f['void'].intersection(CROP).area})
 floor=f['floor_plate'].intersection(CROP);public=f['public'].intersection(CROP)
 # 3D finding: departure-floor shaft masks incorrectly remove the floor below the rising flight.
 # Close ONLY departure bank underside in the isolated model. Incoming upper openings stay untouched.
 for e in f['escalators']:
  if e['atrium']==2 and e['levels'][0]==lev:
   added=e['shaft'].intersection(CROP).difference(floor)
   slab_additions.append({'id':e['id']+'-departure-underfloor','level':lev,'polygon':mapping(added),'area_m2':added.area,'status':'isolated-scene proposal; source drawing unchanged'})
   floor=floor.union(added)

 extrude(floor,y-.38,.38,'stone',True)
 # soffit is the underside of the following slab; no ceiling spanning a source atrium void.
 ceiling=(fs[lev+1]['floor_plate'].intersection(CROP) if lev<2 else floor).buffer(-.05)
 surf(ceiling,top-.7,'plaster',False,True,.88)
 # Actual source perimeter and closed service bands prevent walking through unbuilt outside walls.
 envelope=f['envelope_walls'].intersection(CROP)
 extrude(envelope,y,top-y-.4,'plaster',True);routing_solids[lev].append(envelope)
 # residual is a classification remainder, NOT a closed wall volume (it includes some public floor).
 closed=unary_union([z['polygon']for z in f.get('service_zones',[])]).intersection(CROP)
 extrude(closed,y,top-y-.7,'plaster',True);routing_solids[lev].append(closed)
 # Equipment cores are outside this plaza validation scope. Preserve their source perimeter and seal access.
 for core in f['cores']:
  outline=core.get('outline')
  if outline is not None and outline.intersects(CROP):
   corewall=outline.boundary.buffer(.12).intersection(CROP)
   extrude(corewall,y,top-y-.7,'plaster',True);routing_solids[lev].append(corewall)
 # Discrete recessed ceiling panels, joints and luminaires only over actual common floor.
 for x in np.arange(-506,-350,6):
  for z in np.arange(-10,123,6):
   panel=box(x-2.83,z-2.83,x+2.83,z+2.83)
   if public.covers(panel) and ceiling.covers(panel):
    # Continuous suspended gypsum; no giant six-metre decorative squares.
    cylinder((x,z),top-.78,.095,.025,'black',16)
    cylinder((x,z),top-.805,.068,.025,'light',16)
    for side in[-1,1]:
     bar((x-.9,z+side*2.35),(x+.9,z+side*2.35),.09,top-.75,.025,'black',False)
     bar((x-.84,z+side*2.35),(x+.84,z+side*2.35),.045,top-.765,.018,'light',False)
    # slot ventilation, downlight baffles, sprinkler head
    for dz in[-1.75,-1.68,-1.61]:bar((x-1.25,z+dz),(x+1.25,z+dz),.025,top-.75,.018,'black',False)
    cylinder((x+1.9,z+1.9),top-.78,.07,.04,'metal',12)
    if abs(x+429)<40 and abs(z-46)<45 and int(x+z)%3==0:lights.append({'p':pos(x,top-.9,z),'level':lev,'type':'common','energy':.25})
 # inlaid paving datum strips and movement joints; geometry ends at real voids.
 for x in np.arange(-512,-349,6):
  q=box(x-.009,-16,x+.009,124).intersection(public)
  surf(q,y+.002,'grout',solid=False)
 for z in np.arange(-16,124,6):surf(box(-512,z-.009,-349,z+.009).intersection(public),y+.002,'grout')
 # fascia reveal on edges of all real upper-level holes
 if lev>0:
  for po in polys(f['void'].intersection(CROP)):
   for ring in[po.exterior,*po.interiors]:
    co=list(ring.coords)
    for a,b in zip(co,co[1:]):
     if math.dist(a,b)<.1:continue
     bar(a,b,.06,y-.32,.12,'bronze');bar(a,b,.065,y-.16,.035,'black')
     bar(a,b,.075,y-.38,.028,'light')
 # Source railing band -> laminated glass, caprail and base shoe; geometry remains source footprint.
 guard=f['guardrails'].intersection(CROP)
 if not guard.is_empty:
  extrude(guard,y,.1,'metal',True)
  extrude(guard.buffer(-.025),y+.1,.98,'glass',True)
  extrude(guard,y+1.08,.055,'metal',True)
  for po in polys(guard):
   ring=po.exterior;length=ring.length
   for s in np.arange(.3,length,1.7):
    p=ring.interpolate(s);cylinder((p.x,p.y),y+.08,.026,1.0,'metal',8,False)
 # Store source boundaries and storefront lines. Whole partitions, open portal and separate glazing.
 stores=[s for s in f['stores']if s['polygon'].intersects(CROP)]
 for s in stores:
  render_group=s['id']
  normalize_stock_roles(s,CROP,meta)
  poly=s['polygon'].intersection(CROP);e=s['entry'];u=s['u'];n=s['n'];dw=s['door_width_m'];idx=len(meta['shops']);brand={'衣料':['ATELIER 07','TONE / WEAR'],'書籍・文具':['栞書房','BOOKS & PAPER'],'生活雑貨':['木と、日々。','SORA / LIVING'],'食品・カフェ':['mellow cafe','BREAD & BUTTER'],'靴・鞄':['LINO SHOES','STRIDE & BAG'],'美容・ケア':['白花 / HAKKA','SOIN / CARE'],'カフェ・焼菓子':['mellow cafe','BREAD & BUTTER'],'旅行・雑貨':['TRAVEL NOTE','petit voyage'],'飲食':['食堂 木の実','KITCHEN / TIME'],'ホビー':['HOBBY & DAYS','CULTURE / NOTE'],'楽器':['SOUND / ROOM','楽器と音楽'],'体験・ゲーム':['PLAY / TIME','ARCADE 09'],'キッズ':['little days','KIDS / NOTE']}.get(s['category'],['LIVING / TIME','DAILY / GOODS'])[idx%2]
  ceiling_h=top-y-.7
  # Use the actual shared public/shop edge. Legacy glazing chords may cross clipped corners.
  door_cut=rect(e,u,dw+.06,1.0)
  contact=s['polygon'].boundary.intersection(f['public'].buffer(.025)).intersection(Point(e).buffer(s['frontage_m']*1.2+3)).difference(door_cut)
  # Windows are sales-only. External stock/non-occupiable boundaries remain opaque.
  stock_exclusion=s['backroom'].union(s.get('nonoccupiable_enclosure_allowance',Polygon())).buffer(.025)
  sales_contact=contact.intersection(s['sales'].buffer(.005)).difference(stock_exclusion)
  real_fronts=[q for q in lines(sales_contact) if q.length>.15]
  frontage_style='wall_window' if s['category'] in ['美容・ケア','楽器','ホビー','生活雑貨'] else 'display_portal' if s['category'] in ['衣料','キッズ','靴・鞄'] else 'framed_glass'
  if frontage_style=='wall_window' and len(real_fronts)>1:real_fronts=sorted(real_fronts,key=lambda g:g.length,reverse=True)[:1]
  old=baseline_privacy[s['id']];old_lines=unary_union(old['fronts']).intersection(CROP);new_lines=unary_union(real_fronts).intersection(CROP)
  old_issue=old_lines.intersection(old['backroom'].buffer(.025))
  meta.setdefault('stock_glass_audit',[]).append({'id':s['id'],'level':lev,'baseline_glazing_m':old_lines.length,'baseline_stock_facing_glazing_m':old_issue.length,'new_glazing_m':new_lines.length,'remaining_stock_facing_glazing_m':new_lines.intersection(s['backroom'].buffer(.025)).length,'resolved_by_role_reclassification_m':old_issue.intersection(s['sales'].difference(old['sales']).buffer(.005)).length,'exception':'none; no open-kitchen exception authored','rule':'windows on sales-adjacent faces only; full-height opaque walls on stock and enclosure allowance; isolated unusable stock fragments returned to sales/display without reducing original sales'})
  fronts[s['id']]=real_fronts
  frontcuts=unary_union([g.buffer(.14,cap_style=2)for g in real_fronts]).intersection(s['sales']).difference(stock_exclusion)
  wall=s['wall_solids'].intersection(CROP).simplify(.0005,preserve_topology=True)
  partition_full=s['backroom'].boundary.intersection(s['sales'].buffer(.0005)).buffer(.10).intersection(poly)
  stock_opening=rect(s['back_door'],u,1.6,1.0)
  declared_partition=partition_full.difference(stock_opening)
  # Restore the partition already defined in B v4.1 sales/backroom geometry; no new plot.
  wall=wall.union(declared_partition);opaque=wall.difference(frontcuts)
  if not declared_partition.is_empty and CROP.buffer(-1).contains(Point(s['back_door'])):
   bp=s['back_door'];meta['staff_doors'].append({'id':s['id']+'-BOH','store':s['id'],'level':lev,'p':pos(bp[0],y,bp[1]),'u':u,'n':n,'clear_width_m':1.6,'leaf_width_m':1.594,'height_m':2.2,'source':'existing back_door / backroom / sales'})
  meta['construction_repairs'].append({'id':s['id'],'old_wall_ceiling_gap_m':ceiling_h-4.49,'new_gap_m':0,'old_glazing_base_open_height_m':.10,'new_base_open_height_m':0,'glazing_path':'actual tenant/public boundary, not legacy chord','style':frontage_style,'wall_cleanup_max_m':.0005})
  wall_mat=['wall_sand','wall_sage','wall_chalk','wall_taupe'][idx%4]
  extrude(opaque,y+.12,ceiling_h-.12,wall_mat,True);routing_solids[lev].append(opaque)
  # limestone skirting, plaster wall head, shadow gap
  extrude(opaque,y,.12,'dark_stone',True)
  window_header=wall.intersection(frontcuts)
  extrude(window_header,y+3.335,ceiling_h-3.335,wall_mat,True)
  extrude(partition_full.intersection(stock_opening),y+2.218,ceiling_h-2.218,wall_mat,True)
  extrude(rect(e,u,dw+.34,.14),y+3.45,ceiling_h-3.45,wall_mat,True)
  # glazed fronts, segmented mullions, stone portal jambs; portal itself stays clear.
  door=rect(e,u,dw+.06,1.0)
  for g in real_fronts:
   g=g.intersection(CROP)
   for line in lines(g):
    gl=line.buffer(.025,cap_style=2).difference(door).intersection(poly.buffer(-.008)).intersection(s['sales']).difference(stock_exclusion)
    extrude(gl,y+.12,3.18,'glass',True);routing_solids[lev].append(gl)
    base_shoe=line.buffer(.045,cap_style=2).difference(door).intersection(poly)
    extrude(base_shoe,y,.13,'bronze',True);routing_solids[lev].append(base_shoe)
    extrude(base_shoe,y+3.28,.055,'bronze',False)
    for dist in sorted(set([*np.arange(0,line.length+.01,2.8),line.length])):
     p=line.interpolate(dist)
     if door.distance(p)<.12:continue
     frame=rect((p.x,p.y),u,.055,.085).intersection(poly)
     extrude(frame,y,3.35,'bronze',True);routing_solids[lev].append(frame)
  # explicit portal clear width, recessed wood trim and sign mounted on own upper fascia.
  for side in[-1,1]:
   c=(e[0]+u[0]*(dw/2+.095)*side,e[1]+u[1]*(dw/2+.095)*side)
   extrude(rect(c,u,.16,.22),y,3.45,'wood',True);routing_solids[lev].append(rect(c,u,.16,.22))
  sw=max(dw+.5,min(s['frontage_m']-.3,8.0));fascia=rect(e,u,sw,.28).intersection(poly.buffer(.18))
  extrude(fascia,y+3.45,ceiling_h-3.45,'wood'if idx%2 else'dark_stone',False)
  si=sign_asset(idx,brand,s['category']);signs.append({'file':si,'p':pos(e[0]-n[0]*.17,y+3.93,e[1]-n[1]*.17),'u':u,'n':[-n[0],-n[1]],'w':min(sw-.14,4.8),'h':min(sw-.14,4.8)/4})
  # Portal threshold and slim entrance light. No opaque virtual door in this art trial.
  surf(rect(e,u,dw,.32).intersection(floor),y+.005,'dark_stone')
  bar((e[0]-u[0]*(dw/2),e[1]-u[1]*(dw/2)),(e[0]+u[0]*(dw/2),e[1]+u[1]*(dw/2)),.08,y+3.38,.04,'light')
  # Actual backroom and shop floor materials remain on source footprints.
  surf(s['sales'].intersection(CROP),y+.006,'oak_floor'if s['category'] in ['書籍・文具','食品・カフェ','カフェ・焼菓子','飲食'] else 'retail_terrazzo'if idx%2 else 'stone')
  surf(s['backroom'].intersection(CROP),y+.006,'dark_stone')
  fixtures,fitout_details=fit_shop(globals(),s,lev,y,idx,poly,s['shelf_zones'])
  # Wall-wash strips over display fixtures, source ceiling footprint maintained.
  for line in real_fronts:
   le=line.intersection(CROP)
   for l in lines(le):
    a=l.interpolate(.1);b=l.interpolate(max(.1,l.length-.1))
    bar((a.x+n[0]*1.1,a.y+n[1]*1.1),(b.x+n[0]*1.1,b.y+n[1]*1.1),.08,y+ceiling_h-.20,.045,'light')
  # Shop collision partitions, merchandise and open storefront are all tested in Godot.
  within=CROP.buffer(-2).contains(Point(e));target=(e[0]+n[0]*1.0,e[1]+n[1]*1.0)
  meta['shops'].append({'id':s['id'],'level':lev,'category':s['category'],'brand':brand,'entry_world':e,'entry_local':pos(e[0],y,e[1]),'target_local':pos(target[0],y,target[1]),'clear_width_m':dw,'frontage_m':s['frontage_m'],'depth_m':s['depth_m'],'full_polygon_in_scope':CROP.covers(s['polygon']),'entrance_in_test_scope':within,'fixtures':len(fixtures),'fitout_details':fitout_details,'finish_palette':idx%4,'fixture_footprints':fixtures})
  if within:
   route=LineString(s['main_route'])
   for fraction in[.28,.65]:
    lp=route.interpolate(route.length*fraction)
    if s['sales'].buffer(.1).covers(lp):
     lights.append({'p':pos(lp.x,y+ceiling_h-.35,lp.y),'level':lev,'type':'shop','energy':1.4,'store':s['id'],'room_index':idx})
     cylinder((lp.x,lp.y),y+ceiling_h-.25,.085,.05,'black',12)
     cylinder((lp.x,lp.y),y+ceiling_h-.27,.060,.025,'light',12)
  if within:shop_tests.append({'id':s['id'],'level':lev,'entry':e,'inside':target,'fixtures':unary_union(fixtures)})
 render_group=''
 for obj in f.get('furniture',[]):
  g=obj['geom'].intersection(CROP)
  if g.is_empty:continue
  if obj['kind']=='bench':
   extrude(g.buffer(-.06),y+.38,.10,'wood',True);extrude(g.buffer(-.25),y,.39,'dark_stone',True)
   # slatted seat and back with open view to the plaza
   a,b,c,d=g.bounds
   for z in np.arange(b+.07,d,.12):surf(box(a+.04,z,c-.04,min(z+.075,d)),y+.49,'wood')
  else:
   extrude(g,y,.58,'plaster',True);extrude(g.buffer(-.12),y+.58,.06,'soil')
   c=g.centroid
   for j in range(8):
    ang=j*math.tau/8;cc=(c.x+math.cos(ang)*.35,c.y+math.sin(ang)*.25)
    cylinder(cc,y+.62,.025,.9,'wood',8)
    for h in[.9,1.2,1.5]:
     leaf=rect((cc[0]+math.cos(ang)*.18,cc[1]+math.sin(ang)*.18),(math.cos(ang),math.sin(ang)),.60,.18)
     extrude(leaf,y+h,.015,'leaf',False)
 # Faithful plate is sealed only at explicit scope cut lines; export caps distinctly as staging boundaries.
 boundary=CROP.boundary.intersection(floor)
 for line in lines(boundary):
  co=list(line.coords)
  for a,b in zip(co,co[1:]):bar(a,b,.12,y,top-y-.4,'scope_wall',True)
 floor_walk[lev]=f['nav_free'].intersection(CROP.buffer(-.6))
 for e in f['escalators']:
  if e['atrium']==2:esc_unique[e['id']]=e
# Existing source banks: separate steel structure, ribbed steps, glass panels, combs and both landings.
for id,e in esc_unique.items():
 lo,hi=e['levels'];yl=fs[lo]['height'];yh=fs[hi]['height'];cx,cz=e['c'];ux,uz=e['u'];nx,nz=-uz,ux;run=e['run_m'];half=run/2
 # UP and DOWN have the same elevation direction; direction controls belt travel.
 def at(s,t,y):return pos(cx+ux*s+nx*t,y,cz+uz*s+nz*t)
 # walkable escalator inclined tread support, excludes source flat landing projections
 quad('step',[at(-half,-.66,yl),at(half,-.66,yh),at(half,.66,yh),at(-half,.66,yl)],(0,1,0),[[0,0],[run,0],[run,1.32],[0,1.32]],True)
 # Moving treads and rounded return handrails are built by escalator_v2.gd.
 quad('metal',[at(-half,-1.12,yl-.85),at(half,-1.12,yh-.85),at(half,1.12,yh-.85),at(-half,1.12,yl-.85)],(0,-1,0))
 for side in[-1,1]:
  t=side*.94
  for mat,ya,yb,w in[('metal',-.80,.18,.19),('glass',.18,.99,.035),('metal',.06,.10,.12)]:
   quad(mat,[at(-half,t-w/2,yl+ya),at(half,t-w/2,yh+ya),at(half,t-w/2,yh+yb),at(-half,t-w/2,yl+yb)],(-nx*side,0,-nz*side),solid=True)
   quad(mat,[at(-half,t+w/2,yl+yb),at(half,t+w/2,yh+yb),at(half,t-w/2,yh+yb),at(-half,t-w/2,yl+yb)],(0,1,0),solid=False)
  # side enclosure skirt underside, real structural depth
  quad('dark_stone',[at(-half,t,yl-.90),at(half,t,yh-.90),at(half,t,yh-.22),at(-half,t,yl-.22)],(nx*side,0,nz*side))
 for s,yy in[(-half,yl),(half,yh)]:
  # flat 1.5m comb deck and mechanical cover within the prescribed 14.8m shaft
  sign=-1 if s<0 else 1;fp=rect((cx+ux*(s+sign*.75),cz+uz*(s+sign*.75)),(ux,uz),1.5,1.38)
  surf(fp,yy+.004,'step',True,True)
  for t in np.arange(-.62,.63,.065):
   center=(cx+ux*s+nx*t,cz+uz*s+nz*t);bar((center[0]-.15*ux,center[1]-.15*uz),(center[0]+.15*ux,center[1]+.15*uz),.025,yy+.012,.012,'yellow')
 meta['escalators'].append({'id':id,'levels':e['levels'],'direction':e['direction'],'c':pos(cx,0,cz),'u':e['u'],'run_m':run,'rise_m':yh-yl,'tread_width_m':1.32,'shaft_width_m':2.4,'landing_width_m':3.6,'landings':[mapping(p)for p in e['landings']],'test_start':at(-half-2,0,yl),'test_end':at(half+2,0,yh)})
render_group=''
# Long-span skylight over the offset Time atrium: perimeter ring, steel rafters, glazing and clerestory.
roof_y=16.4;sk=box(-444,28,-414,64);ring=sk.buffer(.5).difference(sk.buffer(-.5))
extrude(ring,roof_y,.65,'plaster',False)
for x in np.arange(-444,-413,3):bar((x,28),(x,64),.12,roof_y+.65,.28,'metal')
for z in np.arange(28,65,4):bar((-444,z),(-414,z),.10,roof_y+.65,.22,'metal')
surf(sk,roof_y+.96,'roof_glass',True)
# Natural structural bays at corners of source atrium, perimeter legs kept out of shop portals.
for x,z in[(-442.1,29.9),(-415.9,29.9),(-442.1,62.1),(-415.9,62.1)]:
 extrude(box(x-.30,z-.30,x+.30,z+.30),0,16.4,'plaster',True)
 extrude(box(x-.305,z-.305,x+.305,z+.305),0,1.12,'quartz',False)
 extrude(box(x-.31,z-.31,x+.31,z+.31),1.12,.025,'bronze',False)
 extrude(box(x-.32,z-.32,x+.32,z+.32),0,.18,'dark_stone',True)
meta['art_proposals']=['設備核は既存outlineで閉鎖。階段・EV・トイレ内部は今回の広場検証の対象外。閉鎖帯は代理ボリューム。','時の広場開口外の600mm角柱4本・トップライト骨組は検証用の建築意匠案。設計原本には未反映。','各店舗の造作棚は既存shelf_zones内のみ。共用床と入口、原本の主通路は保持。','上下階の自動搬送は検証用の方式。実機の段差と安全制御は未実装。','切出し境界は検証用の閉鎖面であり、館全体の外壁ではない。']
# Readable spatial landmark and wayfinding, matching designed Time plaza, on southern clock lounge.
extrude(box(-432.5,78.6,-425.5,78.9),0,.40,'dark_stone',True)
# Above low seating, a suspended original clock face, not a floor obstacle.
clock=Image.new('RGB',(512,512),(238,232,217));dr=ImageDraw.Draw(clock)
dr.ellipse((30,30,482,482),outline=(61,72,63),width=8)
for i in range(60):
 a=i*math.tau/60;ra=192 if i%5 else 180;dr.line((256+math.sin(a)*ra,256-math.cos(a)*ra,256+math.sin(a)*210,256-math.cos(a)*210),fill=(45,60,53),width=6 if i%5==0 else 2)
dr.line((256,256,256,110),fill=(45,60,53),width=8);dr.line((256,256,350,300),fill=(45,60,53),width=10);dr.ellipse((247,247,265,265),fill=(163,125,57));clock.save(A/'clock.png')
signs.append({'file':'clock.png','p':pos(-429,8.5,77.9),'u':[1,0],'n':[0,-1],'w':2.8,'h':2.8})
for x in[-430.2,-427.8]:cylinder((x,77.9),9.9,.012,.275,'metal',8)
# Plan-derived navigable routes; visibility graph uses no point snapping, and actual runtime still tests collisions.
from heapq import heappush,heappop
from shapely import simplify
routes=[];routing_fail=[]
# one home point per floor (same safe public court location)
home=(-432,74.3)
for lev in range(3):
 nav=floor_walk[lev].buffer(-.06).difference(unary_union(routing_solids[lev]).buffer(.36))
 # reserve new pillar footprint + capsule radius and the clock lounge seat
 obstacles=unary_union([box(x-.30,z-.30,x+.30,z+.30).buffer(.34)for x,z in[(-442.1,29.9),(-415.9,29.9),(-442.1,62.1),(-415.9,62.1)]])
 nav=nav.difference(obstacles)
 if lev==0:nav=nav.difference(box(-432.5,78.6,-425.5,78.9).buffer(.34))
 # reduced visibility graph inset with conservative simplification, kept only if exact line fits
 components=polys(nav);component=next((p for p in components if p.covers(Point(home))),None)
 if component is None:raise RuntimeError('home not navigable')
 # modest angular simplification vertices, all edges checked against original safe component
 simple=component.simplify(.10,preserve_topology=True)
 verts=[home]
 for ring in[simple.exterior,*simple.interiors]:
  for x,z in list(ring.coords)[:-1]:
   # retain only vertices on/on safe side of nav, nudge inward only graph nodes (never targets)
   p=Point(x,z)
   if component.covers(p):verts.append((x,z))
 # use buffered tight graph so corners have breathing room; limit to slice paths reasonably close
 print('routing',lev,'verts',len(verts),flush=True)
 def route(a,b):
  if component.covers(LineString([a,b])):return[a,b]
  # A grid A* independent of shape vertices, exact segment cover required at every edge.
  step=1.1;mnx,mnz,mxx,mxz=CROP.bounds
  def cell(p):return(round((p[0]-mnx)/step),round((p[1]-mnz)/step))
  def pt(q):return(mnx+q[0]*step,mnz+q[1]*step)
  def valid(q):return component.covers(Point(pt(q)))
  starts=[(cell(a)[0]+dx,cell(a)[1]+dz)for dx in range(-2,3)for dz in range(-2,3)]
  starts=[q for q in starts if valid(q)and component.covers(LineString([a,pt(q)]))]
  goals=[(cell(b)[0]+dx,cell(b)[1]+dz)for dx in range(-2,3)for dz in range(-2,3)]
  goals=[q for q in goals if valid(q)and component.covers(LineString([b,pt(q)]))]
  if not starts or not goals:return None
  gs=set(goals);heap=[];dist={};prev={}
  for q in starts:dist[q]=math.dist(a,pt(q));heappush(heap,(dist[q]+math.dist(pt(q),b),q))
  end=None
  while heap:
   _,q=heappop(heap)
   if q in gs:end=q;break
   for dx,dz in[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
    v=(q[0]+dx,q[1]+dz);new=dist[q]+step*math.hypot(dx,dz)
    if new>=dist.get(v,1e99)or not valid(v)or not component.covers(LineString([pt(q),pt(v)])):continue
    dist[v]=new;prev[v]=q;heappush(heap,(new+math.dist(pt(v),b),v))
  if end is None:return None
  pp=[b,pt(end)]
  while end in prev:end=prev[end];pp.append(pt(end))
  pp.append(a);pp=pp[::-1]
  # maximal visible shortcuts using exact inset geometry
  out=[pp[0]];i=0
  while i<len(pp)-1:
   j=len(pp)-1
   while j>i+1 and not component.covers(LineString([pp[i],pp[j]])):j-=1
   out.append(pp[j]);i=j
  return out
 for s in [s for s in shop_tests if s['level']==lev]:
  # public approach 1m outside threshold, entrance itself then exact inside point
  source_store=next(x for x in fs[lev]['stores']if x['id']==s['id']);e=s['entry'];n=source_store['n'];outside=(e[0]-n[0]*.8,e[1]-n[1]*.8)
  path=route(home,outside)
  if path is None:routing_fail.append({'id':s['id'],'reason':'outside source nav / no exact route'});continue
  points=path+[e,s['inside']]
  routes.append({'id':s['id'],'level':lev,'points':[pos(x,fs[lev]['height'],z)for x,z in points],'distance_m':LineString(points).length})
 # named promenade segments for continuous public-walk checks
 for name,target in[('北店舗街',(-432,16)),('東側回廊',(-402,49)),('西側回廊',(-460,42))]:
  pp=route(home,target)
  if pp:routes.append({'id':f'{lev}-{name}','level':lev,'points':[pos(x,fs[lev]['height'],z)for x,z in pp],'distance_m':LineString(pp).length})
  else:routing_fail.append({'id':f'{lev}-{name}','reason':'public waypoint unreachable'})
meta['graphics_revision']='v2';meta['animation']='separate instanced closed-loop steps and rubber handrail';meta['layout_baseline']='unchanged v1';meta['routing_failures']=routing_fail;meta['isolated_slab_additions']=slab_additions
meta['mesh_triangles']=sum(len(v['v'])//9 for v in M.values());meta['collision_triangles']=sum(len(v)//9 for v in coll.values());meta['material_batches']=len(M);meta['generated_fixtures']=sum(x['fixtures']for x in meta['shops'])
save(A/'geometry.json',{'surfaces':M,'colliders':coll,'signs':signs,'lights':lights});save(S/'scene-manifest.json',meta);save(S/'constructed-fronts.json',fronts);save(S/'walk-routes.json',routes)
# minimal source copy for audit, geometry not changed; all measured world coordinates retained
save(S/'design-extract.json',{'source_sha256':meta['source_sha256'],'floors':fs,'crop':CROP,'origin':ORIGIN})
print('BUILT',meta['mesh_triangles'],'triangles',len(meta['shops']),'shops',len(routes),'routes','routing failures',routing_fail,flush=True)
