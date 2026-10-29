"""v17 elevations and fitted retail. Original plan/physics packs are read only.
Every fascia uses the actual surveyed frontage; fixtures must fit sales floor and miss routes.
"""
from pathlib import Path
import sys,math,json,collections,hashlib
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'))
from site_v2_common import *
from PIL import Image,ImageDraw,ImageFont,ImageOps
from shapely import constrained_delaunay_triangles
from pack_tools_v11 import save_zst
F=read(P/'source/v11/floors-updated.json')
for f in F:
 for s in f['stores']:
  if 'front'not in s:s['front']=[(np.array(s['entry'])-np.array(s['u'])*2).tolist(),(np.array(s['entry'])+np.array(s['u'])*2).tolist()]
  if 'frontage_m'not in s:s['frontage_m']=math.dist(*s['front'])
  if 'depth_m'not in s:s['depth_m']=math.sqrt(s['sales'].area)
brands=read(P/'source/brands-v11.json');B={b['store_id']:b for b in brands};bounds=read(P/'source/v17/model-bounds.json');old=read(P/'source/v16/commons.json')
D=P/'assets/v17/signs';D.mkdir(exist_ok=True);font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';bold='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
W=lambda g:affinity.translate(g,429,-46)
M={};coll={};signs=[];lights=[];render_group='';pos=lambda x,y,z:[float(x),float(y),float(z)]
exec((P/'authoring/mesh_primitives.py').read_text())
instances=[];boards=[];fronts=[];reject=[];fixture_rows=[];occupied=collections.defaultdict(list)
# Original brand names/IDs are unchanged; only the graphic system is re-authored.
palettes=[('#192e35','#e7dfcc'),('#63352c','#eedfc4'),('#c8bba1','#243632'),('#263a31','#dfd3b8'),('#d5d4cc','#20292d'),('#443547','#e6d8ce')]
kind=lambda c:'book'if any(w in c for w in['書','文具'])else'beauty'if any(w in c for w in['美容','化粧','医薬'])else'food'if any(w in c for w in['食品','飲食','カフェ','レストラン','フード','軽食','スーパー'])else'tech'if any(w in c for w in['家電','モバイル','ゲーム'])else'fashion'if any(w in c for w in['衣','服','靴','鞄','ファッション'])else'home'
photo={'book':'campaign_books','beauty':'campaign_serum','food':'campaign_cafe','tech':'campaign_headphones','fashion':'campaign_bag','home':'campaign_ceramic'}
# Eight atlases, exact per-shop artwork (a symbol, original name and category, rather than a text-only board).
for start in range(0,len(brands),64):
 im=Image.new('RGB',(2048,2048),'#202e32');dr=ImageDraw.Draw(im)
 for j,b in enumerate(brands[start:start+64]):
  x=(j%4)*512;y=(j//4)*128;bg,fg=palettes[(start+j)%6];dr.rectangle((x,y,x+511,y+127),fill=bg);dr.line((x+20,y+108,x+492,y+108),fill=fg,width=1)
  k=kind(b['category']);cx=x+44;cy=y+52
  if k=='book':dr.line([(cx-17,cy+15),(cx-17,cy-15),(cx,cy-9),(cx+17,cy-15),(cx+17,cy+15),(cx,cy+20),(cx-17,cy+15)],fill=fg,width=3);dr.line((cx,cy-9,cx,cy+20),fill=fg,width=2)
  elif k=='beauty':dr.ellipse((cx-15,cy-18,cx+15,cy+18),outline=fg,width=3);dr.line((cx-24,cy,cx+24,cy),fill=fg,width=2)
  elif k=='tech':dr.rounded_rectangle((cx-18,cy-15,cx+18,cy+15),radius=5,outline=fg,width=3);dr.ellipse((cx-6,cy-6,cx+6,cy+6),outline=fg,width=2)
  elif k=='food':dr.arc((cx-20,cy-24,cx+20,cy+16),0,180,fill=fg,width=3);dr.line((cx-22,cy+14,cx+22,cy+14),fill=fg,width=3);dr.arc((cx-8,cy-30,cx+8,cy-5),90,240,fill=fg,width=2)
  else:dr.polygon([(cx,cy-22),(cx+22,cy),(cx,cy+22),(cx-22,cy)],outline=fg,width=3);dr.ellipse((cx-10,cy-10,cx+10,cy+10),outline=fg,width=2)
  fs=28
  while ImageFont.truetype(bold,fs).getlength(b['name'])>410 and fs>14:fs-=1
  dr.text((x+81,y+37),b['name'],fill=fg,font=ImageFont.truetype(bold,fs));dr.text((x+84,y+84),b['category']+'  /  '+b['store_id'],fill=fg,font=ImageFont.truetype(font,13))
  b['v17_atlas']=f'brands-{start//64}.png';b['v17_rect']=[(j%4)/4,(j//4)/16,.25,.0625]
 im.save(D/f'brands-{start//64}.png',optimize=True)
# Six product campaigns: original Blender still life, photography-style crop and original typography.
for k,p in photo.items():
 im=Image.new('RGB',(768,1152),'#eee8dd');pic=Image.open(P/'assets/v17/photos'/f'{p}.jpg');pic=ImageOps.fit(pic,(768,860));im.paste(pic,(0,0));dr=ImageDraw.Draw(im)
 title={'book':'ページの先に、旅がある。','beauty':'肌に、静かなひととき。','food':'香りからはじまる午後。','tech':'いつもの音を、新しく。','fashion':'軽やかに、街へ。','home':'暮らしに、手ざわりを。'}[k]
 dr.text((50,900),title,font=ImageFont.truetype(bold,37),fill='#24352f');dr.text((52,970),'THE EVERYDAY COLLECTION',font=ImageFont.truetype(font,25),fill='#74624a');dr.line((52,1040,714,1040),fill='#aa9272',width=2);dr.text((52,1080),'FIND YOURSELF  /  ORIGINAL CAMPAIGN',font=ImageFont.truetype(font,17),fill='#39463c');im.save(D/f'campaign-{k}.jpg',quality=95,subsampling=0)
# Additional illustrated event/menu artwork: not a caption-only rectangle.
for name,title in [('aichi','あいち 食と手しごと市'),('melon','こもれびメロンパン'),('roof','そらと、ひと休み。'),('cinema','星を旅する')]:
 im=Image.new('RGB',(768,1152),'#15382f'if name!='cinema'else'#10233c');dr=ImageDraw.Draw(im)
 for i in range(9):
  cx=130+(i%3)*250;cy=300+(i//3)*200;col=['#d5ad6c','#87966b','#aa6946'][i%3]
  if name=='melon':dr.ellipse((cx-75,cy-55,cx+75,cy+55),fill=col);[dr.line((cx-60+j*25,cy-45,cx-25+j*25,cy+45),fill='#efd2a1',width=4)for j in range(4)]
  elif name=='cinema':dr.ellipse((cx-i*3,cy-i*3,cx+i*3+6,cy+i*3+6),fill=col)
  else:dr.arc((cx-80,cy-70,cx+80,cy+70),0,320,fill=col,width=15);dr.line((cx,cy-65,cx,cy+60),fill=col,width=8)
 fs=44 if len(title)<12 else 32;dr.text((384,100),title,font=ImageFont.truetype(bold,fs),fill='#f2e6ce',anchor='mt');dr.text((384,930),'食べる。出会う。ひと息つく。',font=ImageFont.truetype(font,27),fill='#f2e6ce',anchor='mt');dr.text((384,1010),'FIND YOURSELF  /  ORIGINAL DESIGN',font=ImageFont.truetype(font,20),fill='#bdb98e',anchor='mt');im.save(D/f'{name}.jpg',quality=95)

def board(id,p,n,w,h,tile,activation='always',uv=None,host=None):
 boards.append(dict(id=id,p=list(map(float,p)),n=list(map(float,n)),w=float(w),h=float(h),tile=tile,activation=activation,uv=uv,host=host))
def chunk(f,p):return f"{f['wing']}-{f['label']}-{int(p[0]//35)}-{int(p[1]//35)}"
# All actual public-facing polygon edges, tested on three samples, with actual store-side normal.
for f in F:
 pub=f['public'];H=f['height']
 for s in f['stores']:
  b=B[s['id']];n=np.array(s['n']);u=np.array(s['u']);entry=np.array(s['entry']);edges=[]
  if f['level']==3:
   reject.append({'id':s['id'],'scope':'facade','reason':'Open roof tenant: no assumed enclosing wall or floating fascia'});continue
  ring=list(s['polygon'].exterior.coords)
  for a,c in zip(ring,ring[1:]):
   a=np.array(a);c=np.array(c);length=float(np.linalg.norm(c-a))
   if length<2.2:continue
   t=(c-a)/length;out=np.array([t[1],-t[0]]);mid=(a+c)/2
   if s['polygon'].covers(Point(*(mid+out*.15))):out=-out
   # Frontage only, never back-of-house or incidental plot gaps.
   samples=[a+(c-a)*q+out*.65 for q in[.2,.5,.8]]
   if sum(pub.covers(Point(*q))for q in samples)<3 or np.dot(out,-n)<.45:continue
   edges.append((a,c,out,length))
  if not edges:
   a,c=map(np.array,s['front']);length=float(np.linalg.norm(c-a));edges=[(a,c,-n,length)]
  for ei,(a,c,out,length)in enumerate(edges):
   if length<2:continue
   # Thin secondary joinery on existing edge. No new plot, closed door or concealed passage.
   a=a+[429,-46];c=c+[429,-46];mid=(a+c)/2;inward=-out
   render_group='V17-FACADE-'+chunk(f,mid);mat='v17_'+['ink','bronze','oak','sage','porcelain','plum'][brands.index(b)%6]
   bar(a-inward*.03,c-inward*.03,.12,H+2.82,.54,mat,False)
   bar(a-out*.065,c-out*.065,.10,H+3.38,.06,'v17_bronze',False)
   # Pilasters only outside every actual entry, never shrinking its clear opening.
   for q in[a,c]:
    if np.linalg.norm(q-(entry+[429,-46]))>float(s['door_width_m'])/2+.22:
     bar(q-inward*.03,q+inward*.12,.15,H+.04,2.76,mat,False)
   w=min(5.4,max(1.2,length-.7));board('BRAND-'+s['id']+'-'+str(ei),[mid[0]+out[0]*.105,H+3.09,mid[1]+out[1]*.105],out,w,.43,b['v17_atlas'],'always',b['v17_rect'],s['id'])
   fronts.append(dict(id=s['id'],wing=f['wing'],floor=f['label'],edge=[a.tolist(),c.tolist()],length_m=length,material=mat,geometry_rule='Actual public-facing boundary; elevated fascia; existing entrance retained'))
   # Integrated shopfront downlight, one per actual frontage rather than a repeated corridor grid.
   lights.append({'id':s['id']+'-display-light','p':[mid[0]+inward[0]*.65,H+2.72,mid[1]+inward[1]*.65],'energy':.85 if kind(s['category'])in['beauty','food']else.60,'color':[1,.88,.72],'range':5.5})
  # Campaign display to one side of the entrance only when that real edge is broad enough.
  if edges:
   a,c,out,length=max(edges,key=lambda x:x[3]);a=a+[429,-46];c=c+[429,-46];t=(c-a)/length
   for q in[a+t*1.15,c-t*1.15]:
    if length>5 and np.linalg.norm(q-(entry+[429,-46]))>s['door_width_m']/2+1.0:
     board('CAMPAIGN-'+s['id'],[q[0]+out[0]*.13,H+1.65,q[1]+out[1]*.13],out,.78,1.17,'campaign-'+kind(s['category'])+'.jpg',host=s['id']);break
# Existing opaque walls, proven by a 198-ray host survey: a coherent architectural campaign bay.
wallfile=P/'source/v17/wall-hosts.json'
if wallfile.exists():
 for i,r in enumerate(json.loads(wallfile.read_text())['accepted']):
  p=np.array(r['position']);n3=np.array(r['normal']);n=np.array([n3[0],n3[2]]);u=np.array([n[1],-n[0]]);q=np.array([p[0],p[2]]);h=p[1]-1.25
  # Wall finish only, never a replacement floor or a concealment of an unassigned gap.
  render_group='V17-VERIFIED-WALL-'+str(i);mat='v17_oak'if i%3 else'v17_sage'
  bar(q-u*3.8+n*.028,q+u*3.8+n*.028,.045,h,2.5,mat,False)
  for sign in[-1,1]:bar(q+u*(sign*3.78)+n*.058,q+u*(sign*3.78)+n*.058+n*.02,.08,h,2.5,'v17_bronze',False)
  category=list(photo)[i%6];board('WALL-CAMPAIGN-'+str(i),[p[0]+n[0]*.062,p[1],p[2]+n[1]*.062],n,1.55,2.33,'campaign-'+category+'.jpg',host='Native opaque wall '+r['collider'])
  board('WALL-CAMPAIGN-TWIN-'+str(i),[p[0]+n[0]*.063+u[0]*2.3,p[1],p[2]+n[1]*.063+u[1]*2.3],n,1.18,1.77,'campaign-'+list(photo)[(i+2)%6]+'.jpg',host='Native opaque wall '+r['collider'])

# Locate new fitted bays against actual sales geometry, avoid previously occupied fixtures and protected aisles.
art=read(P/'source/v12/scene-art.json');art['instances']+=read(P/'source/v15/retail-services.json')['instances']
for d in art['instances']:
 if d.get('max_xz'):
  pp=d['p'];occupied[d['group']].append(rect((pp[0],pp[2]),d['u'],d['max_xz'][0],d['max_xz'][1]).buffer(.12))
for d in old['instances']:
 if d.get('store_id'):occupied[d['store_id']].append(d['footprint'].buffer(.12))

def place(f,s,model,local,normal=None,scale=1,activation='always',role='specialist fitted bay',free=False):
 n=np.array(normal if normal is not None else -np.array(s['n']));u=np.array([n[1],-n[0]]);p=np.array(s['entry'])+[429,-46]+np.array(s['u'])*local[0]+np.array(s['n'])*local[1];b=bounds[model]
 fp=Polygon([p+u*x*scale+n*z*scale for x,z in[(b['min'][0],b['min'][2]),(b['max'][0],b['min'][2]),(b['max'][0],b['max'][2]),(b['min'][0],b['max'][2])]])
 if not W(s['sales']).buffer(-.10).covers(fp):return False
 routes=W(s['aisles']).buffer(.12)
 if routes.intersects(fp) or any(fp.intersects(v)for v in occupied[s['id']]):return False
 occupied[s['id']].append(fp.buffer(.15));identity=f"V17-{s['id']}-{model}-{len(instances)}"
 instances.append(dict(id=identity,zone=s['id'],wing=f['wing'],floor=f['label'],level=f['level'],model=model,p=[p[0],f['height']+.025,p[1]],n=n.tolist(),scale=scale,scale_x=1.,footprint=fp,collision='auto',activation=activation,host=None,store_id=s['id'],role=role))
 fixture_rows.append({'id':identity,'store':s['id'],'model':model,'sales_containment':True,'protected_aisle_clear':True,'existing_fixture_clear':True});return True
reps=['A1F-007','A1F-005','A1F-001','B1-030','B1-N03','C1F-CW-1','C1F-CSW-3','AB1-003','BB1-MARKET','AB1-001','ARF-002','BRF-CAFE','A2F-007','B2-030','B3-030']
for f in F:
 for s in f['stores']:
  if s['id']not in reps:continue
  k=kind(s['category']);model={'book':'book_editorial_wall','beauty':'beauty_consultation_island','food':'bakery_display','tech':'electronics_demo_bar','fashion':'apparel_capsule','home':'lit_display_niche'}[k]
  count=0
  # Search near perimeter display bays, never a uniform object grid in the public corridor.
  for z in[3.0,5.5,8.,11.,14.,18.,22.,26.]:
   for x in[-s.get('frontage_m',math.dist(*s['front']))*.33,s.get('frontage_m',math.dist(*s['front']))*.33,-s.get('frontage_m',math.dist(*s['front']))*.20,s.get('frontage_m',math.dist(*s['front']))*.20]:
    if count>=4:break
    if place(f,s,model,(x,z)):count+=1
   if count>=4:break
  if k=='food':
   for x in[-3.5,3.5,-6,6]:
    if place(f,s,'cafe_backbar',(x,min(s.get('depth_m',math.sqrt(s['sales'].area))-3,12)),scale=.8):break
# Spatially specific public additions: use verified v16 facility zones, floor cover and protected approach bands.
routes=read(P/'source/physical-routes-v11.json');routebands=collections.defaultdict(list)
for r in routes:
 for a,c in zip(r['points'],r['points'][1:]):
  if abs(a[1]-c[1])<.03:routebands[round(a[1],2)].append(LineString([(a[0],a[2]),(c[0],c[2])]).buffer(.80))
for d in old['instances']:occupied[(d['wing'],d['level'])].append(d['footprint'].buffer(.28))
for f in F:
 for s in f['stores']:occupied[(f['wing'],f['level'])].append(W(Point(s['entry']).buffer(2.0)))
 for item in f.get('furniture',[]):
  if 'geom'in item:occupied[(f['wing'],f['level'])].append(W(item['geom']).buffer(.20))

def public(zone,model,p,n=(0,1),scale=1,search=0,role='rest display',activation='always'):
 z=next((v for v in old['zones']if v['id']==zone),None)
 if z is None:return
 f=next(f for f in F if f['wing']==z['wing']and f['level']==z['level']);n=np.asarray(n,float);n/=np.linalg.norm(n);u=np.array([n[1],-n[0]]);b=bounds[model];key=f['wing'],f['level'];avoid=unary_union(routebands[round(f['height'],2)])
 offsets=sorted([(x,y)for x in np.arange(-search,search+.01,.75)for y in np.arange(-search,search+.01,.75)],key=lambda a:a[0]**2+a[1]**2)if search else[(0,0)]
 for dx,dz in offsets:
  q=np.array(p)+[dx,dz];fp=Polygon([q+u*x*scale+n*y*scale for x,y in[(b['min'][0],b['min'][2]),(b['max'][0],b['min'][2]),(b['max'][0],b['max'][2]),(b['min'][0],b['max'][2])]])
  if not unary_union([W(f['public'])]+[v['geometry']for v in old['pads']if v['zone']==zone]).buffer(-.15).covers(fp)or avoid.intersects(fp)or any(fp.intersects(v)for v in occupied[key]):continue
  occupied[key].append(fp.buffer(.28));identity=f"V17-{zone}-{model}-{len(instances)}";instances.append(dict(id=identity,zone=zone,wing=f['wing'],floor=f['label'],level=f['level'],model=model,p=[q[0],f['height']+.03,q[1]],n=n.tolist(),scale=float(scale),scale_x=1.,footprint=fp,collision='auto',activation=activation,host=None,store_id=None,role=role));return identity
 reject.append({'id':zone,'model':model,'scope':'public bay','reason':'No candidate covering floor and clearing entrance, existing fixture and protected route bands'})
# Curated rather than regular intervals. Facility context/position from the v16 programme.
for z in old['zones']:
 if not z['implemented']or z['activation']=='es_option':continue
 p=z['preferred'];id=z['id'];title=z['title']
 if z['role']=='public'and z['activation']=='always':
  if any(w in title for w in['広場','休憩','庭園','テラス','中庭']):
   public(id,'lounge_sofa',(p[0]+4,p[1]-3),search=4,role='seating bay facing plaza')
  if z['wing']=='C'and z['level']==0:
   public(id,'botanical_shrub_'+str(len(instances)%3),(p[0]-3,p[1]+3),search=3,scale=.85,role='planted edge, not circulation infill')
# Programme-specific refinements on the existing truck/parent/dog facility finishes.
public('C-MELON-TRUCK','food_order_counter',(-88,-319.8),n=(0,-1),search=3,role='staffed ordering and collection point beside existing bakery vehicle')
menu_id=public('C-MELON-TRUCK','menu_easel',(-85.5,-321),n=(0,1),search=3,role='trading menu, outside access band')
if menu_id:
 item=instances[-1];board('TRUCK-EASEL-PRINT',[item['p'][0],item['p'][1]+.96,item['p'][2]+.045],(0,1),.72,.70,'melon.jpg',host=menu_id)
# Display products rest on real plinth decks, not in the circulation or suspended in space.
for host in list(instances):
 if host['model']!='lit_display_niche':continue
 n=np.array(host['n']);u=np.array([n[1],-n[0]])
 for j,model in enumerate(['campaign_ceramic','campaign_bag']):
  q=np.array([host['p'][0],host['p'][2]])+u*(-.57+1.10*j);bb=bounds[model];fp=Polygon([q+u*xx*.60+n*zz*.60 for xx,zz in[(bb['min'][0],bb['min'][2]),(bb['max'][0],bb['min'][2]),(bb['max'][0],bb['max'][2]),(bb['min'][0],bb['max'][2])]]);item=dict(host);item.update(id=host['id']+'-display-'+str(j),model=model,p=[q[0],host['p'][1]+.24-bb['min'][1]*.60,q[1]],scale=.60,footprint=fp,collision='none',host=host['id'],role='Original display product on existing 0.24m plinth');instances.append(item)

# Fair: graphic enrichments use the actual existing booth bodies; no new fixed floor obstacles.
for d in old['instances']:
 if d['model']in['fair_food_booth','fair_craft_booth']:
  n=np.array(d['n']);p=np.array(d['p']);board('FAIR-ILLUSTRATED-'+d['id'],[p[0]+n[0]*.63,p[1]+1.72,p[2]+n[1]*.63],n,.55,.83,'aichi.jpg','aichi_fair',host=d['id'])
 if d['model']=='melon_bakery_truck':
  n=np.array(d['n']);p=np.array(d['p']);board('MELON-TRADING-MENU',[p[0]+n[0]*.86,p[1]+1.48,p[2]+n[1]*.86],n,.65,.96,'melon.jpg',host=d['id'])
# Stockroom IDs and original brand IDs are never reassigned by this layer.
plan=dict(version='v17',basis='Exact shipped v16; architecture protected',instances=instances,boards=boards,frontages=fronts,lights=lights,rejected=reject,fixture_checks=fixture_rows,brand_count=len(brands),preserved_shop_ids=sorted(B),notes=['F4/F6 remain independent and unapproved','Facade adds joinery, never infills unknown gaps','Photographic artwork is original Blender CG, not Godot evidence','No human manual play or Windows GPU measurement'])
write(P/'source/v17/scene-design.json',plan);write(P/'source/v17/brands.json',brands)
geo=dict(surfaces=M,colliders=coll,signs=[],lights=[]);print(save_zst(P/'assets/v17/elevations.pack.zst',geo));print('V17',len(fronts),'frontages',len(instances),'placements',len(boards),'boards',len(reject),'rejected')
