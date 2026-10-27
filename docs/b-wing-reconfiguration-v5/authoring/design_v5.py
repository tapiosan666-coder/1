"""Independent architectural reconfiguration. Frontage-driven shared parcels; no changes to original/game/v4 files."""
from pathlib import Path
import sys,json,math,copy,collections,itertools,hashlib,csv
sys.path.insert(0,str(Path(__file__).resolve().parent));from site_v2_common import *
import numpy as np
from scipy.optimize import minimize,LinearConstraint
from shapely import make_valid,maximum_inscribed_circle
P=Path(__file__).resolve().parents[1];S=P/'source';base=read(S/'baseline-v4.json');floors=copy.deepcopy(base['floors']);old={s['id']:copy.deepcopy(s)for f in floors for s in f['stores']};design=[];logs=[]
M=2000.;WORLD=box(-1000,-300,0,400)
def clip(g,n,t,less=True):
 n=np.array(n,dtype=float);le=np.linalg.norm(n)
 if le<1e-10:return g if (t>=0 if less else t<=0)else Polygon()
 n=n/le;t=t/le;u=np.array([-n[1],n[0]]);c=n*t
 v=[c-u*M,c+u*M,c+u*M+(-n if less else n)*M*2,c-u*M+(-n if less else n)*M*2]
 return unary_union(polys(g.intersection(Polygon(v))))
def save(name,x):write(S/name,x)
def polysort(g):return sorted(polys(make_valid(g)),key=lambda p:-p.area)
def owned(f):return unary_union([f['public'],f['void'],f['shafts'],f.get('egress',Polygon()),*[c['outline']for c in f['cores']],*[s['polygon']for s in f['stores']],*[z['polygon']for z in f.get('service_zones',[])]])
prot=[unary_union([f['public'],f['void'],f['shafts'],f.get('egress',Polygon()),*[c['outline']for c in f['cores']]])for f in floors];common_public=unary_union(prot);unowned=[f['shell'].difference(owned(f))for f in floors];shared_unknown=unowned[0].intersection(unowned[1]).intersection(unowned[2]);exterior_cut=unary_union([q for q in polys(shared_unknown)if q.boundary.intersects(floors[0]['shell'].boundary.buffer(.01))]);shell=floors[0]['shell'].difference(exterior_cut)
blocks=polysort(shell.difference(common_public));blocks=[q for q in blocks if q.area>10];blocks=sorted(blocks,key=lambda q:-q.area)
# These 22 masses follow existing public streets; common envelope prevents unexplained floor-to-floor offsets.
# The long, entrance-free east-edge strip loses the former warehouse dependency when that function is replanned.
strip=blocks[21];assert strip.area<130 and strip.bounds[2]>-180;shell=shell.difference(strip);exterior_cut=exterior_cut.union(strip);blocks=blocks[:21]
def entry_point(s):return Point(s['entry'][0]+s['n'][0]*.4,s['entry'][1]+s['n'][1]*.4)
allentries=unary_union([entry_point(s).buffer(1.25)for f in floors for s in f['stores']])
def room_on_front(block,area,ref,name,widths):
 options=[];contact=block.boundary.intersection(common_public.buffer(.015))
 for line in lines(contact):
  if line.length<3:continue
  for t in np.arange(.5,line.length,.8):
   pt=line.interpolate(t);a=line.interpolate(max(0,t-.04));b=line.interpolate(min(line.length,t+.04));u=np.array([b.x-a.x,b.y-a.y]);u=u/max(np.linalg.norm(u),1e-12);n=np.array([-u[1],u[0]])
   if not block.covers(Point(pt.x+n[0]*.3,pt.y+n[1]*.3)):n=-n
   for width in widths:
    depth=area/width;center=np.array([pt.x,pt.y])+n*(depth/2+.001);r=rect(center,u,width,depth)
    if not block.buffer(.002).covers(r)or r.intersection(allentries).area>.0001:continue
    score=pt.distance(Point(ref))+abs(width-10)*2;options.append((score,r,[pt.x,pt.y],u.tolist(),n.tolist(),width,depth))
 if not options:raise RuntimeError('No real frontage/clearance for '+name)
 best=min(options,key=lambda a:a[0]);_,r,e,u,n,w,d=best
 return{'id':name,'polygon':r,'entry':e,'u':u,'n':n,'door_width_m':1.8,'main_route':[e,[e[0]+n[0]*min(2,d/2),e[1]+n[1]*min(2,d/2)],[e[0]+n[0]*(d/2),e[1]+n[1]*(d/2)]],'planned_width_m':w,'planned_depth_m':d,'area_target_m2':area,'actual_area_m2':r.area,'coordinate_frame':'world_xz'}
rooms={}
for b,key,area,ref,widths in [(blocks[10],'W',160,(-552,74),[10,8,12]),(blocks[6],'L',160,(-374,83),[10,8,12]),(blocks[2],'T',120,(-485,7),[10,8,12])]:
 rooms[key]=room_on_front(b,area,ref,key,widths);print('ROOM',key,rooms[key]['entry'],rooms[key]['planned_width_m'],rooms[key]['planned_depth_m'],flush=True)
# Shared straight-wall cells, initially fit to frontage station cuts where all front normals agree.
def partition(domain,ss,targets):
 N=len(ss)
 if N==1:return[domain],{'method':'single existing frontage','area_error':0}
 e=np.array([s['entry']for s in ss]);ns=np.array([s['n']for s in ss]);single=np.min(ns@ns.T)>.90
 if single:
  u=np.array(ss[0]['u']);u=u/np.linalg.norm(u);order=sorted(range(N),key=lambda i:e[i]@u);cum=0;cuts=[];xy=[np.array(c)for p in polys(domain)for c in p.exterior.coords];lo=min(c@u for c in xy)-1;hi=max(c@u for c in xy)+1
  for k in order[:-1]:
   cum+=targets[k];aa,bb=lo,hi
   for _ in range(45):
    mid=(aa+bb)/2
    if clip(domain,u,mid).area<cum:aa=mid
    else:bb=mid
   cuts.append((aa+bb)/2)
  cells=[Polygon()for _ in ss]
  for j,k in enumerate(order):
   p=domain
   if j:p=clip(p,u,cuts[j-1],False)
   if j<N-1:p=clip(p,u,cuts[j],True)
   cells[k]=p
  return cells,{'method':'parallel shared side walls / area-budgeted frontage stations','cuts':cuts,'u':u.tolist()}
 # Multi-sided island: joint straight walls weighted by required shop programme, then audited for real entrances/stock geometry.
 # Frontage seed stays inward of source doorway; area budgets are solved simultaneously, not greedy nearest-gap annexation.
 origin=e.mean(axis=0);seed=e-origin+ns*.5;seednorm=(seed*seed).sum(axis=1);minimum=np.array([0 if q.get('v5_anchor_annex')else q['sales'].area+max(12,min(q['backroom'].area,35))for q in ss])
 def cells(weights):
  out=[]
  for i in range(N):
   p=domain
   for j in range(N):
    if i==j:continue
    normal=2*(seed[j]-seed[i]);p=clip(p,normal,seednorm[j]-seednorm[i]+weights[i]-weights[j]+normal@origin)
    if p.is_empty:break
   out.append(p)
  return out
 def objective(x):
  w=np.r_[x,0.];cc=cells(w);areas=np.array([q.area for q in cc]);# dual power-cell integral gradient, use robust area least squares for small blocks
  return ((areas-targets)**2/np.maximum(targets,20)).sum()+1000*(np.maximum(0,minimum-areas)**2).sum()
 # Linear constraints protect an actual source doorway approach; dummy annexes belong to the existing locked anchor.
 A=[];B=[]
 for i,shop in enumerate(ss):
  if shop.get('v5_anchor_annex'):continue
  ee=np.array(shop['entry']);uu=np.array(shop['u']);nn=np.array(shop['n'])
  for rr in[ee+nn*.4,ee+nn*.35-uu*.85,ee+nn*.35+uu*.85]:
   if not domain.buffer(.01).covers(Point(rr)):continue
   for j in range(N):
    if i==j:continue
    row=np.zeros(N)
    row[j]+=1;row[i]-=1
    A.append(row[:-1]);B.append(np.sum((seed[j]-(rr-origin))**2)-np.sum((seed[i]-(rr-origin))**2))
 constraint=LinearConstraint(np.array(A),-np.inf,np.array(B))if A else()
 result=minimize(objective,np.zeros(N-1),method='SLSQP',constraints=[constraint]if A else[],options={'maxiter':400,'ftol':1e-7,'eps':.01})
 cc=cells(np.r_[result.x,0.]);return cc,{'method':'joint frontage-protected straight boundaries; programme area and workroom validation','weights':np.r_[result.x,0.].tolist(),'area_error':max(abs(c.area-t)for c,t in zip(cc,targets)),'optimizer_success':bool(result.success)}

for fi,f in enumerate(floors):
 floorblocks=copy.deepcopy(blocks);reserve=f['shell'].intersection(shell).difference(prot[fi].union(unary_union(floorblocks)));attachments=[]
 for part in polysort(reserve):
  width=maximum_inscribed_circle(part,tolerance=.01).length*2
  contacts=[part.boundary.intersection(b.buffer(.002)).length for b in floorblocks];idx=int(np.argmax(contacts))
  if width>1.2 and contacts[idx]>1:
   floorblocks[idx]=floorblocks[idx].union(part);attachments.append({'block':idx+1,'area_m2':part.area,'reason':'floor-specific non-public rear parcel, adjacent common retail block','polygon':part})
 f['v5_floor_block_extensions']=attachments
 newstores=[];newservices=[];blockrecords=[]
 for key,r in rooms.items():
  z=copy.deepcopy(r);z['id']=f'S-{f["level"]+1}-{key}';z['name']={'W':'西共用荷受・店舗別在庫室','L':'東共用荷受・店舗別在庫室','T':'運営・救護・清掃室'if f['level']==0 else'従業員休憩・運営・清掃室'}[key];z['programme']=('12区画×2.2×3mの店舗別在庫、4m中央作業帯、28㎡の荷受/作業端部'if key!='T'else'運営・スタッフ・救護/清掃の寸法付き区分。法規や運営体制の認定ではない。');newservices.append(z)
 newcounter=0
 for bi,block in enumerate(floorblocks,1):
  ss=[copy.deepcopy(s)for s in f['stores']if block.buffer(.02).covers(entry_point(s))];room_polys=[r['polygon']for r in newservices if r['polygon'].intersects(block)];domain=block.difference(unary_union(room_polys));locked=[s for s in ss if s['polygon'].area>=500];small=[s for s in ss if s not in locked]
  # Preserve the reviewed anchor/large-shop plan wherever multiple frontages coexist.
  if len(ss)==1 and not room_polys:
   s=ss[0];s['polygon']=domain;s['v5_block']=bi;s['v5_partition_method']='one existing frontage / coherent outer mass';s['v5_original_plot_m2']=old[s['id']]['polygon'].area;newstores.append(s);blockrecords.append({'block':bi,'area':block.area,'stores':[s['id']],'method':'single existing unit'});continue
  domain=domain.difference(unary_union([s['polygon']for s in locked]));newstores.extend(locked)
  if not small and locked:
   anchor=max(locked,key=lambda q:q['polygon'].area);anchor['polygon']=anchor['polygon'].union(domain);anchor['v5_rear_support_annex']=domain;continue
  if not small:
   if domain.area>30:
    # A genuine new tenant only where another floor already has this corner tenancy (SW11).
    if bi==21:
     template=copy.deepcopy(next(s for s in floors[0]['stores']if s['id']=='B1-SW11'));newcounter+=1;template['id']=f'B{f["level"]+1}-N{newcounter:02}';template['category']='親子読書カフェ';old[template['id']]=copy.deepcopy(template);small=[template]
    else:print('NO_FRONTAGE',f['label'],bi,domain.area,flush=True);blockrecords.append({'block':bi,'area':block.area,'unresolved_domain':domain});continue
   else:continue
  # Anchor rear annexes and new corner tenants are planned programmes, not arbitrary nearest-gap labels.
  if locked and domain.area>sum(s['polygon'].area for s in small)+30:
   anchor=max(locked,key=lambda q:q['polygon'].area);dummy=copy.deepcopy(anchor);dummy['id']=anchor['id']+'-ANNEX';dummy['v5_anchor_annex']=anchor['id'];dummy['entry']=[anchor['backroom'].representative_point().x,anchor['backroom'].representative_point().y];dummy['n']=[0,0];dummy['polygon']=Polygon();dummy['sales']=Polygon();dummy['backroom']=Polygon();small.append(dummy)
  elif domain.area>sum(s['polygon'].area for s in small)*1.45+200:
   contact=domain.boundary.intersection(f['public'].buffer(.02)).difference(unary_union([Point(s['entry']).buffer(3)for s in small]))
   segments=sorted(lines(contact),key=lambda q:-q.length)
   if segments and segments[0].length>5:
    line=segments[0];ep=line.interpolate(.5,normalized=True);aa=line.interpolate(max(0,line.length/2-.2));bb=line.interpolate(min(line.length,line.length/2+.2));uu=np.array([bb.x-aa.x,bb.y-aa.y]);uu/=np.linalg.norm(uu);nn=np.array([-uu[1],uu[0]])
    if not domain.covers(Point(ep.x+nn[0]*.5,ep.y+nn[1]*.5)):nn=-nn
    newcounter+=1;id=f'B{f["level"]+1}-N{newcounter:02}';category={0:'暮らし・家電体験',1:'書籍・文具',2:'スポーツ・創作体験'}[f['level']]
    template={'id':id,'category':category,'entry':[ep.x,ep.y],'u':uu.tolist(),'n':nn.tolist(),'polygon':Polygon(),'sales':Polygon(),'backroom':Polygon(),'door_width_m':3.6,'frontage_m':min(14,line.length),'depth_m':20,'back_door':[ep.x+nn[0]*10,ep.y+nn[1]*10],'main_route':[[ep.x,ep.y],[ep.x+nn[0]*3,ep.y+nn[1]*3]],'kind':'v5-purpose-designed-new-tenant'};old[id]=copy.deepcopy(template);small.append(template)
  need=np.array([max(180,s['sales'].area+max(12,s['backroom'].area))if s.get('kind')=='v5-purpose-designed-new-tenant'else s['sales'].area+max(12,min(s['backroom'].area,35))if not s.get('v5_anchor_annex')else 5 for s in small]);extra=domain.area-need.sum()
  if extra<-.1:print('BLOCK_CAPACITY_DEFICIT',f['label'],bi,extra,flush=True)
  growth=np.array([max(5,s.get('frontage_m',8))if not s.get('v5_anchor_annex')else 0 for s in small])
  if any(s.get('v5_anchor_annex')for s in small):
   targets=need.copy()
   for i,s in enumerate(small):
    if not s.get('v5_anchor_annex'):targets[i]=min(s['polygon'].area*1.15,need[i]+max(0,extra)*.35*growth[i]/max(growth.sum(),1))
   ai=next(i for i,s in enumerate(small)if s.get('v5_anchor_annex'));targets[ai]=domain.area-targets.sum()+targets[ai]
  else:targets=need+extra*growth/growth.sum()
  cc,method=partition(domain,small,targets)
  for s,c,t in zip(small,cc,targets):
   if s.get('v5_anchor_annex'):
    anchor=next(q for q in newstores if q['id']==s['v5_anchor_annex']);anchor['polygon']=anchor['polygon'].union(c);anchor['v5_rear_support_annex']=c;continue
   s['polygon']=c;s['v5_block']=bi;s['v5_partition_method']=method['method'];s['v5_original_plot_m2']=old[s['id']]['polygon'].area;s['v5_target_plot_m2']=float(t);s['v5_entry_inside']=c.buffer(.01).covers(entry_point(s));newstores.append(s)
  blockrecords.append({'block':bi,'area':block.area,'stores':[s['id']for s in ss],'method':method,'targets':targets.tolist(),'cells':[{'id':s['id'],'area':c.area,'entry_ok':c.buffer(.01).covers(entry_point(s)),'parts':len(polys(c))}for s,c in zip(small,cc)]})
 f['stores']=newstores;f['service_zones']=newservices;f['shell']=shell;f['v5_blocks']=blockrecords
 print('FLOOR_CELLS',f['label'],len(newstores),'bad entries',[s['id']for s in newstores if not s['polygon'].buffer(.01).covers(entry_point(s))],flush=True)
 design.append(f)
save('prototype-cells.json',{'floors':design,'old_stores':old,'common_shell':shell,'exterior_cut':exterior_cut,'blocks':blocks,'rooms':rooms,'status':'WORKING STUDY; no production/architecture pass'})
