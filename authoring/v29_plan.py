from pathlib import Path
import sys,math,json,csv,hashlib,heapq,collections
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'))
from site_v2_common import read,write,Polygon,Point,LineString,box,affinity,unary_union
from PIL import Image,ImageDraw,ImageFont
plan=read(P/'source/v25/retail-plan.json');stores=[s for s in plan['stores']if s['floor']=='1F'];bounds=read(P/'source/v29/model-bounds.json');own=collections.defaultdict(list)
for f in plan['fixtures']:own[f['store_id']].append(f)
# Balanced 24-store candidate list, prioritising an existing substantial sales area in each category.
focus=[]
for wing,number in [('A',8),('B',12),('C',4)]:
 pool=[s for s in stores if s['wing']==wing];selected=[]
 categories=['apparel','book','beauty','electronics','home','shoes','cafe','food','restaurant','sports','furniture','mobile']
 for cat in categories:
  candidates=[s for s in pool if s['category']==cat and s['id']not in selected]
  if candidates and len(selected)<number:selected.append(max(candidates,key=lambda s:min(s['sales_m2'],700))['id'])
 for s in sorted(pool,key=lambda s:-s['sales_m2']):
  if len(selected)>=number:break
  if s['id']not in selected:selected.append(s['id'])
 focus+=selected
changes=[];deferred=[];catalog=[];retired_hosts=set();entry_data=[];surveys=[]
for index,s in enumerate(stores):
 e=np.array(s['entry_world']);route=s['main_route_world'];v=np.array(route[1])[[0,2]]-e;n=v/max(np.linalg.norm(v),1e-6);u=np.array([n[1],-n[0]]);variants=int(hashlib.sha256(s['id'].encode()).hexdigest()[:4],16)%2
 cat=s['category'];kit='collection_v29_'+cat+'_'+str(variants);bound=bounds[kit];nb=np.array([bound['min'][0],bound['min'][2],bound['max'][0],bound['max'][2]])
 # Each shop uses an existing physically placed fixture footprint, never the clear entry spine.
 candidates=[]
 for f in own[s['id']]:
  role=f['role'].lower();model=f['model'].lower()
  if model.startswith('fixture_v25_')or model in ['fixture_v24_double_library','fixture_v24_coffee_station','fixture_v24_jewellery_case']:continue
  if any(k in role+' '+model for k in ['checkout','kitchen','chair','banquette','fitting','seating','tray_return','photo']):continue
  old=f['footprint']
  if old.geom_type!='Polygon' or old.area<.03:continue
  nn=np.array(f['n']);uu=np.array([nn[1],-nn[0]]);c=np.array(old.centroid.coords[0]);pts=np.array(old.exterior.coords);local=np.column_stack(((pts-c)@uu,(pts-c)@nn));lo=local.min(axis=0);hi=local.max(axis=0)
  k=min((hi[0]-lo[0]-.06)/(nb[2]-nb[0]),(hi[1]-lo[1]-.06)/(nb[3]-nb[1]),1.05)
  if k<.68:continue
  centre=(nb[:2]+nb[2:])/2;pos=c-uu*centre[0]*k-nn*centre[1]*k
  shape=Polygon([pos+uu*x*k+nn*z*k for x,z in[(nb[0],nb[1]),(nb[2],nb[1]),(nb[2],nb[3]),(nb[0],nb[3])]])
  if not old.buffer(.001).covers(shape)or not s['sales_world'].buffer(.02).covers(shape):continue
  if shape.intersects(s['protected_aisles_world'].buffer(.03)):continue
  distance=np.linalg.norm(c-e);candidates.append((distance,f,k,pos,shape))
 if not candidates:
  # Vacant sales-only window zone: retain existing furnishings, a 1.2m clear entry spine, and staff paths.
  blocked=unary_union([f['footprint'].buffer(.48) for f in own[s['id']] if hasattr(f['footprint'],'buffer')]+[s['protected_aisles_world'].buffer(.18)])
  found=False
  for depth in [1.5,2.5,3.5,5.,7.]:
   if found:break
   for side in [-1.,1.]:
    if found:break
    for across in [2.,3.,4.5,6.]:
     c=e+n*depth+u*side*across;nn=-n;uu=-u;centre=(nb[:2]+nb[2:])/2;pos=c-uu*centre[0]-nn*centre[1]
     shape=Polygon([pos+uu*x+nn*z for x,z in [(nb[0],nb[1]),(nb[2],nb[1]),(nb[2],nb[3]),(nb[0],nb[3])]])
     if not s['sales_world'].buffer(-.12).covers(shape)or blocked.intersects(shape):continue
     f={'id':'V29-'+s['id']+'-window-collection','store_id':s['id'],'wing':s['wing'],'floor':'1F','level':0,'model':kit,'asset':'../v29/models/'+kit,'p':[float(pos[0]),.02,float(pos[1])],'n':nn.tolist(),'scale':1.,'scale_x':1.,'collision':'mesh','activation':'always','role':'window_collection','footprint':shape,'brand_ref':s['id']}
     plan['fixtures'].append(f);own[s['id']].append(f);candidates.append((float(np.linalg.norm(c-e)),f,1.,pos,shape));found=True;break
 candidates.sort(key=lambda q:q[0]);chosen=[]
 if candidates:
  chosen=[candidates[0]]
  if s['id']in focus:
   for fraction in [.16,.30,.44,.58,.72,.86,1.]:
    if len(chosen)>=8:break
    options=[q for q in candidates if q[1]['id']not in{a[1]['id']for a in chosen}]
    if options:chosen.append(min(options,key=lambda q:abs(q[0]-candidates[-1][0]*fraction)))
 if s['id']not in focus:
  chosen=candidates[:min(3,len([q for q in candidates if q[0]<14.]))]or chosen
 for i,(distance,f,k,pos,shape)in enumerate(chosen):
  # Mix different display roles inside a single store; never repeat one complete story unit throughout it.
  alternate='collection_v29_'+cat+'_'+str((variants+i)%(4 if cat=='apparel'else 2))
  alt=bounds[alternate];bb=np.array([alt['min'][0],alt['min'][2],alt['max'][0],alt['max'][2]]);nn=np.array(f['n']);uu=np.array([nn[1],-nn[0]]);oldpoly=f['footprint'];cc=np.array(oldpoly.centroid.coords[0]);pts=np.array(oldpoly.exterior.coords);local=np.column_stack(((pts-cc)@uu,(pts-cc)@nn));lo=local.min(axis=0);hi=local.max(axis=0);kk=min((hi[0]-lo[0]-.06)/(bb[2]-bb[0]),(hi[1]-lo[1]-.06)/(bb[3]-bb[1]),1.05);centre=(bb[:2]+bb[2:])/2;pp=cc-uu*centre[0]*kk-nn*centre[1]*kk;polynew=Polygon([pp+uu*x*kk+nn*z*kk for x,z in[(bb[0],bb[1]),(bb[2],bb[1]),(bb[2],bb[3]),(bb[0],bb[3])]])
  selected_kit=kit
  if kk>=.68 and oldpoly.buffer(.001).covers(polynew)and not s['protected_aisles_world'].buffer(.03).intersects(polynew):selected_kit=alternate;k=kk;pos=pp;shape=polynew

  retired_hosts.add(f['id']);oldmodel=f['model'];f['model']=selected_kit;f['asset']='../v29/models/'+selected_kit;f['scale']=float(k);f['scale_x']=1.;f['p']=[float(pos[0]),s['height']+.02,float(pos[1])];f['v29_collection']=True
  changes.append({'fixture_id':f['id'],'store_id':s['id'],'industry':cat,'old_model':oldmodel,'new_model':selected_kit,'scale':float(k),'front_distance_m':float(distance),'footprint_preserved':True,'new_visual_footprint':shape,'old_reserved_footprint':f['footprint'],'stage':'front'if i==0 else'central_or_rear','composite_merchandise':True})
 # Existing sign/entry maintained; new fine portal trim is fitted to a real shopfront segment.
 poly=s['sales_world'];best=None
 for a,b in [(a,b) for pp in ([poly]if poly.geom_type=='Polygon'else poly.geoms) if pp.geom_type=='Polygon' for a,b in zip(list(pp.exterior.coords)[:-1],list(pp.exterior.coords)[1:])]:
  edge=LineString([a,b]);dist=edge.distance(Point(e));length=edge.length
  if dist<.12 and length>2.5:
   mid=(np.array(a)+np.array(b))/2;v=(np.array(b)-np.array(a))/length
   if best is None or length>best[0]:best=(length,mid,v)
 if best:
  width,mid,v=best;nn=np.array([v[1],-v[0]])
  if poly.contains(Point(mid+nn*.18)):nn=-nn # storefront normal faces public circulation
  width=min(width-.10,18.)
  entry_data.append({'store_id':s['id'],'wing':s['wing'],'category':cat,'brand':s['brand'],'p':[float(mid[0]),0.,float(mid[1])],'n':nn.tolist(),'entry':[float(e[0]),0.,float(e[1])],'width':float(width),'variant':variants,'accent':['#294a52','#77513c','#4f6656'][ord(s['wing'])-65],'kit_count':len(chosen)})
 else:deferred.append({'store_id':s['id'],'reason':'No unambiguous straight shopfront edge containing actual entry; retained original facade'})
 if not chosen:deferred.append({'store_id':s['id'],'reason':'No collection fits existing display footprints without occupying protected aisles'})
 catalog.append({'store_id':s['id'],'wing':s['wing'],'brand':s['brand'],'industry':cat,'sales_m2':s['sales_m2'],'focus':s['id']in focus,'collections':len(chosen),'visual_quality':'NOT TESTED','entry':s['entry_world'],'fixture_count':len(own[s['id']]),'front_layer_status':'PROVISIONAL_APPLIED'if chosen else'RETAINED_NOT_COMPLETE'})
 def camera(id,at,target):return {'id':id,'eye':[float(at[0]),1.65,float(at[1])],'look':[float(target[0]),1.55,float(target[1])],'fov':78 if id.endswith('-front')else 72,'wing':s['wing'],'store_id':s['id']}
 shot=camera(s['id']+'-front',e-n*3.2,e+n*3);shot['look'][1]=2.5;surveys.append(shot)
 if s['id']in focus:
  pts=[np.array(p)[[0,2]]for p in route];line=LineString(pts)
  for phase,t in [('centre',.48),('rear',.85)]:
   at=np.array(line.interpolate(t,normalized=True).coords[0]);target=e+n*2 if phase=='rear'else np.array(line.interpolate(min(.95,t+.3),normalized=True).coords[0]);surveys.append(camera(s['id']+'-'+phase,at,target))
removed=[d for d in plan['products']if d['host']in retired_hosts];plan['products']=[d for d in plan['products']if d['host']not in retired_hosts];plan.pop('instances',None);plan.pop('retirement_stores',None);plan['revision']='v29-role-led-1F-collections-provisional';write(P/'source/v29/retail-plan.json',plan)
write(P/'source/v29/collection-changes.json',{'changes':changes,'retired_individual_product_records':len(removed),'composite_merchandise_note':'Original products inside replaced fixtures are rendered in the new authored collection mesh, not separate purchasable SKU records. No purchase gameplay implemented.','deferred':deferred});write(P/'source/v29/storefronts.json',entry_data);write(P/'source/v29/store-audit.json',catalog);write(P/'source/v29/focus-stores.json',focus)
# Main-route graph: union actual archived grid paths linking each real shop entry to its wing hub.
graphs=read(P/'source/v22/navigation-grids.json');routes=[];route_cameras=[];corridor_points=[];route_i=0
for wing in 'ABC':
 d=graphs['normal-'+wing+'-1F'];origin=np.array(d['origin']);step=d['step_m'];cells={tuple(v)for v in d['cells']};nodes=list(cells)
 def nearest(p):
  q=(np.array(p)-origin)/step;return min(nodes,key=lambda c:(c[0]-q[0])**2+(c[1]-q[1])**2)
 positions={c:origin+np.array(c)*step for c in nodes};centres={'A':[418,-50],'B':[5.5,9.3],'C':[-145,-289]};start=nearest(centres[wing]);dist={start:0.};parents={};queue=[(0,start)]
 while queue:
  dd,c=heapq.heappop(queue)
  if dd!=dist[c]:continue
  for dx,dz in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
   h=(c[0]+dx,c[1]+dz)
   if h not in cells or (dx and dz and((c[0]+dx,c[1])not in cells or(c[0],c[1]+dz)not in cells)):continue
   nd=dd+math.hypot(dx,dz)
   if nd<dist.get(h,1e20):dist[h]=nd;parents[h]=c;heapq.heappush(queue,(nd,h))
 edges=set();destinations={}
 for s in stores:
  if s['wing']!=wing:continue
  end=nearest(s['entry_world']);destinations.setdefault(end,[]).append(s['id']);c=end
  while c in parents:
   p=parents[c];edges.add(tuple(sorted([c,p])));c=p
 adj=collections.defaultdict(set)
 for a,b in edges:adj[a].add(b);adj[b].add(a)
 breaks={c for c in adj if len(adj[c])!=2 or c in destinations or c==start};used=set()
 for c in sorted(breaks):
  for q in sorted(adj[c]):
   edge=tuple(sorted([c,q]))
   if edge in used:continue
   chain=[c,q];used.add(edge);prev=c;cur=q
   while cur not in breaks:
    other=next(a for a in adj[cur]if a!=prev);used.add(tuple(sorted([cur,other])));chain.append(other);prev,cur=cur,other
   line=LineString([positions[a]for a in chain]).simplify(.12)
   if line.length<3.:continue
   route_i+=1;rid=f'{wing}-1F-R{route_i:03}';points=[[float(x),0.,float(z)]for x,z in line.coords];routes.append({'id':rid,'wing':wing,'points':points,'length_m':line.length,'role':'Existing customer circulation linking shop access, junctions and plaza','connected_store_ids':destinations.get(chain[0],[])+destinations.get(chain[-1],[]),'walk_status':'NOT TESTED','art_status':'NOT TESTED','source_grid':'normal-'+wing+'-1F'})
 # Long route views must include the whole wing, not only three hubs.
 wr=sorted([r for r in routes if r['wing']==wing],key=lambda r:-r['length_m'])
 selected=wr[:max(6,min(15,len(wr)))]
 for r in selected:
  line=LineString([(p[0],p[2])for p in r['points']])
  for direction in [1,-1]:
   t=.12 if direction==1 else .88;at=np.array(line.interpolate(t,normalized=True).coords[0]);target=np.array(line.interpolate(.8 if direction==1 else .2,normalized=True).coords[0]);route_cameras.append({'id':r['id']+('-forward'if direction==1 else'-reverse'),'route_id':r['id'],'wing':wing,'eye':[float(at[0]),1.65,float(at[1])],'look':[float(target[0]),1.65,float(target[1])],'fov':75})
 # Supported overhead finishing candidates sample these actual route chains; no ground furniture inserted.
 sampled=[]
 for r in wr:
  line=LineString([(p[0],p[2])for p in r['points']])
  for dis in np.arange(2,line.length,7.5):
   p=np.array(line.interpolate(float(dis)).coords[0]);ahead=np.array(line.interpolate(min(line.length,float(dis)+.4)).coords[0]);v=ahead-p
   if np.linalg.norm(v)<.01:continue
   if any(np.linalg.norm(p-old)<5.0 for old in sampled):continue
   sampled.append(p);corridor_points.append({'p':[float(p[0]),0.,float(p[1])],'n':(v/np.linalg.norm(v)).tolist(),'wing':wing,'route_id':r['id']})
write(P/'source/v29/routes.json',routes);write(P/'source/v29/ceiling-candidates.json',corridor_points);write(P/'source/v29/review-cameras.json',route_cameras+surveys)
# Original brand-specific editorial graphics; no copied logo or photographic asset.
ART=P/'assets/v29/art';ART.mkdir(exist_ok=True);font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';fontjp='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
labels={'apparel':'NEW SILHOUETTES','shoes':'FORM & FUNCTION','beauty':'DAILY RITUALS','home':'ROOM TO LIVE','book':'READ / DISCOVER','electronics':'TRY THE EVERYDAY','food':'FRESH MARKET','cafe':'COFFEE & BAKES','restaurant':'SEASONAL TABLE','sports':'MOVE OUTSIDE','furniture':'LIVING STUDIES','mobile':'CONNECTED LIFE'}
for i,s in enumerate(stores):
 bg=['#e8e1d2','#dae3df','#e6d7cf'][i%3];accent=['#294b50','#713f34','#365241'][i%3];im=Image.new('RGB',(640,960),bg);dr=ImageDraw.Draw(im);dr.text((42,40),'COLLECTION / 01',font=ImageFont.truetype(font,22),fill=accent);dr.line((42,85,598,85),fill=accent,width=2)
 # A different structural illustration per industry, not a generic text-only board.
 cat=s['category'];cx=320;cy=420
 if cat in ['apparel','sports']:
  dr.polygon([(200,240),(270,210),(370,210),(440,250),(495,390),(410,430),(390,350),(390,620),(250,620),(250,350),(220,430),(140,390)],fill=accent);dr.line((320,220,320,610),fill=bg,width=4)
 elif cat in ['book','electronics','mobile']:
  for j in range(3):
   x=130+j*115;y=260+(j%2)*60;dr.rounded_rectangle((x,y,x+150,y+280),radius=6,fill=accent,outline=bg,width=8);dr.line((x+20,y+30,x+125,y+30),fill=bg,width=3)
 elif cat in ['cafe','restaurant','food']:
  dr.ellipse((145,270,495,620),fill=accent);dr.ellipse((175,300,465,590),outline=bg,width=4)
  for j in range(6):dr.arc((225+j*10,325,380+j*10,520),40,230,fill=bg,width=3)
 elif cat in ['beauty']:
  for j in range(3):
   x=150+j*120;dr.rounded_rectangle((x,310-j*30,x+90,600),radius=18,fill=accent);dr.rectangle((x+22,250-j*30,x+68,325-j*30),fill=accent)
 else:
  for j in range(3):dr.rounded_rectangle((110+j*130,310+(j%2)*70,245+j*130,570+(j%2)*40),radius=40 if cat=='shoes'else 8,fill=accent)
 dr.text((42,745),labels[cat],font=ImageFont.truetype(font,25),fill=accent);sz=32
 while ImageFont.truetype(font,sz).getlength(s['brand'])>555:sz-=1
 dr.text((42,820),s['brand'],font=ImageFont.truetype(font,sz),fill=accent);dr.text((42,885),'1F  /  '+s['wing']+' WING',font=ImageFont.truetype(font,20),fill=accent);im.save(ART/(s['id']+'.webp'),quality=91)
print('STORES',len(stores),'FRONTS',len(entry_data),'FOCUS',len(focus),'COLLECTIONS',len(changes),'DEFERRED',len(deferred),'ROUTES',len(routes),'CAMERAS',len(route_cameras+surveys),'CEILING',len(corridor_points))
