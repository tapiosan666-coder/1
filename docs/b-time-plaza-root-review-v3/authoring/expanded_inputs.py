"""Generate conservative interior sample routes and 3D joint probes. Targets never snap to nearby floor."""
from pathlib import Path
import sys,json,math,heapq
sys.path.insert(0,'/workspace/1/tools')
from site_v2_common import read,shape,Point,LineString,Polygon,box,unary_union,polys,lines,encode,rect
P=Path(__file__).resolve().parents[1];d=read(P/'source/design-extract.json');M=read(P/'source/scene-manifest.json');fronts=read(P/'source/constructed-fronts.json');origin=M['world_origin_xz'];routes=[];probes=[];door_widths=[];checks=[];review=[]
def local(p,y):return[round(p[0]-origin[0],5),y,round(p[1]-origin[1],5)]
def route(nav,a,b):
 if not nav.covers(Point(a))or not nav.covers(Point(b)):return None
 if nav.covers(LineString([a,b])):return[a,b]
 step=.35;x0,z0,x1,z1=nav.bounds
 def cell(p):return(round((p[0]-x0)/step),round((p[1]-z0)/step))
 def pt(q):return(x0+q[0]*step,z0+q[1]*step)
 def candidates(a):
  c=cell(a);return[q for dx in range(-2,3)for dz in range(-2,3) if nav.covers(Point(pt(q:=(c[0]+dx,c[1]+dz))))and nav.covers(LineString([a,pt(q)]))]
 starts=candidates(a);goals=set(candidates(b));heap=[];cost={};prev={}
 for q in starts:cost[q]=math.dist(a,pt(q));heapq.heappush(heap,(cost[q]+math.dist(pt(q),b),q))
 end=None
 while heap:
  _,q=heapq.heappop(heap)
  if q in goals:end=q;break
  for dx,dz in[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
   v=(q[0]+dx,q[1]+dz);nc=cost[q]+step*math.hypot(dx,dz)
   if nc>=cost.get(v,1e90)or not nav.covers(LineString([pt(q),pt(v)])):continue
   cost[v]=nc;prev[v]=q;heapq.heappush(heap,(nc+math.dist(pt(v),b),v))
 if end is None:return None
 pp=[b,pt(end)]
 while end in prev:end=prev[end];pp.append(pt(end))
 pp.append(a);pp.reverse();out=[pp[0]];i=0
 while i<len(pp)-1:
  j=len(pp)-1
  while j>i+1 and not nav.covers(LineString([pp[i],pp[j]])):j-=1
  out.append(pp[j]);i=j
 return out
for f in d['floors']:
 lev=f['level'];y=f['height'];ceiling=[5.525,10.875,16.4][lev]-y-.7
 byid={s['id']:s for s in f['stores']}
 for m in M['shops']:
  if m['level']!=lev or not m['entrance_in_test_scope']:continue
  s=byid[m['id']];entry=s['entry'];u=s['u'];n=s['n'];begin=(entry[0]+n[0]*.85,entry[1]+n[1]*.85);fixtures=unary_union(m.get('fixture_footprints',[]))
  partition=s['backroom'].boundary.intersection(s['sales'].buffer(.0005)).buffer(.1).difference(rect(s['back_door'],u,1.6,1.0)).intersection(s['polygon'])
  crop=shape(d['crop']).buffer(-.20)
  open_leaves=unary_union([q['open_leaf_world_xz']for q in M.get('staff_doors',[])if q['store']==s['id']])
  free=s['polygon'].intersection(crop).buffer(-.32).difference(fixtures.buffer(.32)).difference(partition.buffer(.32)).difference(open_leaves.buffer(.32))
  overlap=fixtures.intersection(s['aisles']).area
  checks.append({'id':m['id']+'-fixtures-vs-canonical-aisle','pass':overlap<.00001,'intersection_m2':overlap})
  components=polys(free);connected=next((q for q in components if q.covers(Point(begin))),None)
  if connected is None:review.append({'id':m['id'],'reason':'declared entry does not connect to conservative interior free space'});continue
  isolated=[q.area for q in components if q!=connected and q.area>1]
  if isolated:review.append({'id':m['id'],'reason':'conservative free-space fragments; not proof of physical inaccessibility','areas_m2':isolated})
  candidates=[];x0,z0,x1,z1=connected.bounds
  for xx in __import__('numpy').arange(x0+.4,x1,1.4):
   for zz in __import__('numpy').arange(z0+.4,z1,1.4):
    pp=Point(xx,zz)
    if connected.covers(pp)and pp.distance(Point(begin))>1.8:candidates.append((xx,zz))
  # Deepest, left, right, and backroom representative targets.
  targets=[]
  if candidates:
   for key in[lambda q:math.dist(q,begin),lambda q:(q[0]-entry[0])*u[0]+(q[1]-entry[1])*u[1],lambda q:-((q[0]-entry[0])*u[0]+(q[1]-entry[1])*u[1])]:
    target=max(candidates,key=key)
    if target not in targets:targets.append(target)
  back=s['backroom'].buffer(-.38)
  if not back.is_empty:
   for q in polys(back):
    p=q.representative_point()
    if connected.covers(p):targets.append((p.x,p.y));break
  for j,target in enumerate(targets):
   path=route(connected,begin,target)
   if path is None:review.append({'id':m['id'],'reason':'target has no conservative sampled route','target':target});continue
   routes.append({'id':m['id']+'-interior-'+str(j),'store':m['id'],'points':[local(q,y)for q in path],'distance_m':LineString(path).length,'kind':'actual_character_body_shop_interior','target_not_projected':True,'staff_doors_state':'open'})
  # Three laterally separated physical passes through actual entrance width.
  for side in[-1,0,1]:
   off=side*(float(s['door_width_m'])/2-.37);c=(entry[0]+u[0]*off,entry[1]+u[1]*off)
   aa=(c[0]-n[0]*.75,c[1]-n[1]*.75);bb=(c[0]+n[0]*1.05,c[1]+n[1]*1.05)
   door_widths.append({'id':m['id']+'-entrance-'+str(side),'points':[local(aa,y),local(bb,y)],'kind':'entrance_left_center_right_capsule','declared_width_m':s['door_width_m'],'lateral_offset_m':off})
  # Actual horizontal ray probes across glass shoe and ceiling-level wall head.
  fl=fronts.get(m['id'],[])
  if fl:
   ln=max(fl,key=lambda q:q.length);p=ln.interpolate(.5,normalized=True);pa=ln.interpolate(max(0,ln.length*.5-.05));pb=ln.interpolate(min(ln.length,ln.length*.5+.05));dx,dz=pb.x-pa.x,pb.y-pa.y;le=math.hypot(dx,dz)
   if le>1e-6:
    nn=(-dz/le,dx/le);aa=(p.x-nn[0]*.28,p.y-nn[1]*.28);bb=(p.x+nn[0]*.28,p.y+nn[1]*.28)
    for name,h in[('glazing-floor-shoe',.05),('closed-wall-ceiling-joint',ceiling-.045)]:probes.append({'id':m['id']+'-'+name,'a':local(aa,y+h),'b':local(bb,y+h),'expected_hit':True,'kind':'3D_construction_joint_ray'})
# Sample every actual shared tenant boundary, away from declared apertures.
import itertools
for f in d['floors']:
 crop=shape(d['crop']).buffer(-.5);ss=[s for s in f['stores']if s['polygon'].intersects(crop)]
 for a,b in itertools.combinations(ss,2):
  boundary=a['polygon'].boundary.intersection(b['polygon'].boundary).intersection(crop)
  apertures=unary_union([Point(s[key]).buffer(s['door_width_m']/2+.5 if key=='entry'else 1.3)for s in[a,b]for key in['entry','back_door']])
  boundary=boundary.difference(apertures)
  for line_index,line in enumerate(lines(boundary)):
   if line.length<.4:continue
   for sample,dist in enumerate(__import__('numpy').arange(.2,line.length,1.5)):
    p=line.interpolate(dist);pa=line.interpolate(max(0,dist-.03));pb=line.interpolate(min(line.length,dist+.03));dx,dz=pb.x-pa.x,pb.y-pa.y;le=math.hypot(dx,dz)
    if le<1e-7:continue
    nn=(-dz/le,dx/le);aa=(p.x-nn[0]*.30,p.y-nn[1]*.30);bb=(p.x+nn[0]*.30,p.y+nn[1]*.30)
    for suffix,h in[('eye',1.2),('head',[4.825,4.65,4.825][f['level']]-.10)]:
     probes.append({'id':a['id']+'-'+b['id']+f'-shared-{line_index}-{sample}-'+suffix,'a':local(aa,f['height']+h),'b':local(bb,f['height']+h),'structural_only':True,'expected_hit':True,'kind':'sampled_shared_store_boundary_raycast'})
for door in M.get('staff_doors',[]):
 ss=next(s for f in d['floors']for s in f['stores']if s['id']==door['store']);bp=ss['back_door'];nn=ss['n'];yy=d['floors'][door['level']]['height'];hh=[4.825,4.65,4.825][door['level']]
 for name,height in[('staff-door-transom',2.4),('staff-door-ceiling',hh-.045)]:
  aa=(bp[0]-nn[0]*.3,bp[1]-nn[1]*.3);bb=(bp[0]+nn[0]*.3,bp[1]+nn[1]*.3)
  probes.append({'id':door['id']+'-'+name,'a':local(aa,yy+height),'b':local(bb,yy+height),'expected_hit':True,'kind':'3D_construction_joint_ray'})
declared=[];excluded=[]
for f in d['floors']:
 for m in M['shops']:
  if m['level']!=f['level']or not m['entrance_in_test_scope']:continue
  ss=next(s for s in f['stores']if s['id']==m['id'])
  path=LineString(ss['main_route'])
  if not shape(d['crop']).buffer(-.20).covers(path):
   excluded.append({'id':m['id'],'reason':'declared backroom route leaves the frozen validation crop','outside_crop_length_m':path.difference(shape(d['crop'])).length});continue
  declared.append({'id':m['id']+'-declared-backroom-route','store':m['id'],'points':[local(q,f['height'])for q in ss['main_route']],'kind':'declared_sales_to_backroom_route'})
from stock_wall_probes import append_stock_probes
append_stock_probes(d,M,probes,local)
summary={'excluded_out_of_scope_declared_routes':excluded,'declared_backroom_routes':declared,'interior_routes':routes,'entrance_width_passes':door_widths,'joint_ray_probes':probes,'clearance_checks':checks,'review_required':review,'method':'2D routes avoid fixture reservation footprints and source partitions using 0.32m conservative radius and actual open staff-door leaf footprints. Runtime tests use actual Godot colliders; no target projection. Review fragments are not asserted physically unreachable.'}
(P/'source/expanded-qa-inputs.json').write_text(json.dumps(summary,default=encode,ensure_ascii=False,separators=(',',':')))
print('EXPANDED_INPUTS',len(routes),'interior routes',len(door_widths),'entrance traversals',len(probes),'joint rays',len(review),'review flags',flush=True)
