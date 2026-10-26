"""Independent cross-wing drawing audit. Never executes or modifies a Godot project."""
from pathlib import Path
import json,sys,hashlib,math,csv,collections
sys.path.append('/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
from shapely.geometry import shape,Point,LineString,Polygon,box,mapping
from shapely.ops import unary_union,nearest_points
from shapely import affinity
R=Path(__file__).resolve().parents[1];O=R/'docs/ac-detailed-design-v1';EPS=1e-8
HEIGHT={-1:-5.35,0:0.,1:5.525,2:10.875,3:16.4};LABEL={-1:'B1',0:'1F',1:'2F',2:'3F',3:'RF'};CHECKS=[]
def dec(v):
 if isinstance(v,dict):return shape(v)if'type'in v and('coordinates'in v or'geometries'in v)else{k:dec(x)for k,x in v.items()}
 if isinstance(v,list):return[dec(x)for x in v]
 return v

def poly(g):return[]if g.is_empty else[g]if g.geom_type=='Polygon'else[x for x in getattr(g,'geoms',[])if x.geom_type=='Polygon']
def ck(kind,id,ok,value=None,level=None):CHECKS.append(dict(kind=kind,id=id,pass_=bool(ok),value=value,level=level))
D={};sources={};floors={}
for wing in['A','C']:
 p=R/f'docs/{wing.lower()}-detailed-design-v1/geometry.json';sources[wing]=hashlib.sha256(p.read_bytes()).hexdigest();D[wing]=dec(json.loads(p.read_text()))
 for f in D[wing]['floors']:
  level=f['level'];floors[(wing,level)]=f;ck('common_height',wing,abs(f['height']-HEIGHT[level])<1e-10,f['height'],level)
  for key in['public','walkable','floor_plate','void','shafts','shell']:ck('valid_floor_geometry',wing+'/'+key,f[key].is_valid,None,level)
  for key in['void','shafts']:
   for which in['public','walkable','floor_plate']:ck('floor_excludes_opening',wing+'/'+which+'/'+key,f[which].intersection(f[key]).area<EPS,f[which].intersection(f[key]).area,level)
  missing=f['public'].difference(f['floor_plate']).area;ck('slab_supports_public',wing,missing<EPS,missing,level)
# Independent local-space checks supplement each wing's own authored validator.
for wing in['A','C']:
 for f in D[wing]['floors']:
  level=f['level'];clear=f['walkable'].buffer(-.45);parts=[x for x in poly(clear)if x.area>EPS];largest=max(parts,key=lambda x:x.area)
  ck('clear_customer_floor_connected',wing,len(parts)==1,len(parts),level)
  for i,store in enumerate(f['stores']):
   lot=store['polygon'];ep=Point(store['entry']);line=LineString(store['main_route']);distance=largest.distance(ep)
   ck('unit_portal_reaches_connected_clear_floor',wing+'/'+store['id'],distance<.6,distance,level)
   ck('unit_portal_on_own_boundary',wing+'/'+store['id'],lot.boundary.distance(ep)<1e-6,lot.boundary.distance(ep),level)
   a=lot.intersection(f['public']).area;ck('unit_public_no_area_overlap',wing+'/'+store['id'],a<EPS,a,level)
   ck('unit_internal_route_in_lot',wing+'/'+store['id'],line.difference(lot.buffer(1e-7)).length<1e-6,None,level)
   ck('unit_interior_route_avoids_shelves',wing+'/'+store['id'],line.intersection(store['shelf_zones']).length<1e-6,None,level)
   ck('unit_primary_route_avoids_solid_walls',wing+'/'+store['id'],line.intersection(store.get('wall_solids',Polygon())).length<1e-6,None,level)
   if store.get('secondary_entry'):
    sec=Point(store['secondary_entry']);ln=LineString(store['secondary_main_route'])
    ck('unit_secondary_portal_reaches_clear_floor',wing+'/'+store['id'],largest.distance(sec)<.6,largest.distance(sec),level)
    ck('unit_secondary_portal_on_lot',wing+'/'+store['id'],lot.boundary.distance(sec)<1e-6,lot.boundary.distance(sec),level)
    ck('unit_secondary_route_in_lot',wing+'/'+store['id'],ln.difference(lot.buffer(1e-7)).length<1e-6,None,level)
    ck('unit_secondary_route_avoids_shelves',wing+'/'+store['id'],ln.intersection(store['shelf_zones']).length<1e-6,None,level)
    ck('unit_secondary_route_avoids_solid_walls',wing+'/'+store['id'],ln.intersection(store.get('wall_solids',Polygon())).length<1e-6,None,level)
   for other in f['stores'][i+1:]:
    a=lot.intersection(other['polygon']).area;ck('unit_pair_no_area_overlap',wing+'/'+store['id']+'/'+other['id'],a<EPS,a,level)

# C's outdoor court centres remain open to the sky on every elevated level.
for plaza in D['C']['plazas']:
 sky=plaza['sky_void_reservation']
 for f in D['C']['floors']:
  if f['level']>0:
   area=f['floor_plate'].intersection(sky).area;ck('C_garden_sky_opening_not_roofed',plaza['id'],area<EPS,area,f['level'])
# Existing commercial aliases must be neither omitted nor duplicated.
source_legacy=json.loads((R/'docs/map-master-floor-plans.json').read_text())
for wing in['A','C']:
 expected={s['id']for f in source_legacy if f['building']==wing for s in f['shops']}
 if wing=='A':expected|={f'a_basement_{i}'for i in range(7)}|{f'a_food_{i}'for i in range(4)}
 assigned=[]
 for f in D[wing]['floors']:
  for s in f['stores']:
   aliases=s.get('legacy_ids',[])+([s['legacy_id']]if s.get('legacy_id')else[]);assigned.extend(aliases)
 for id in expected:ck('legacy_commercial_ID_preserved_once',wing+'/'+id,assigned.count(id)==1,assigned.count(id))

# B remains the exact v4.1 source, with only a read-only coordinate conversion for comparison.
p=R/'docs/b-v4-overlap-correction/geometry.json';sources['B']=hashlib.sha256(p.read_bytes()).hexdigest();B=dec(json.loads(p.read_text()));D['B']=B
for src in B['floors']:
 level=src['floor']-1;f={k:v for k,v in src.items()};f['level']=level;f['label']=LABEL[level]
 for k in['shell','public','walkable','floor_plate','void','shafts','residual']:f[k]=affinity.translate(src[k],-714,-30)
 f['cores']=[{**c,'outline':affinity.translate(c['outline'],-714,-30)}for c in B['cores']]
 f['stores']=[{**s,'polygon':affinity.translate(s['polygon'],-714,-30),'entry':[s['entry'][0]-714,s['entry'][1]-30]}for s in src['stores']]
 floors[('B',level)]=f
# Cross-wing envelopes and private lots may not intrude into other-wing customer space.
for level in[0,1,2]:
 for one,two in[('A','B'),('B','C'),('A','C')]:
  f,g=floors[(one,level)],floors[(two,level)]
  a=f['shell'].intersection(g['shell']).area;ck('building_envelopes_disjoint',one+'/'+two,a<EPS,a,level)
  for w,u,x,y in[(one,two,f,g),(two,one,g,f)]:
   closed=x.get('residual',Polygon());a=closed.intersection(y['public']).area;ck('no_cross_wing_closed_band_public_overlap',w+'/'+u,a<EPS,a,level)
   coreout=unary_union([c['outline']for c in x.get('cores',[])if'outline'in c]);a=coreout.intersection(y['public']).area;ck('no_cross_wing_core_public_overlap',w+'/'+u,a<EPS,a,level)
   for s in x['stores']:
    area=s['polygon'].intersection(y['public']).area;ck('no_cross_wing_store_public_overlap',w+'/'+s['id']+'/'+u,area<EPS,area,level)
# Exact gateway seam: the B receiver point and full declared width are immutable.
seams=[];conn_graph=collections.defaultdict(set)
for name,wing,level,end,width,axis in [('AB-1','A',0,[-174,-5.5],5,[0,1]),('AB-2','A',1,[-110,-5.5],5,[0,1]),('BC-1','C',0,[-370,-80],8,[1,0]),('BC-2','C',1,[-432,-117],5,[1,0])]:
 f=floors[(wing,level)];bf=floors[('B',level)];seam=LineString([(end[0]-axis[0]*width/2,end[1]-axis[1]*width/2),(end[0]+axis[0]*width/2,end[1]+axis[1]*width/2)])
 bsource=next(c for c in B['floors'][level]['connectors']if c['id']==name);actual=[bsource['route'][-1][0]-714,bsource['route'][-1][1]-30];ck('B_gateway_endpoint_unchanged',name,actual==end,actual,level)
 missing_a=seam.difference(f['public'].buffer(1e-7)).length;missing_b=seam.difference(bf['public'].buffer(1e-7)).length;ck('gateway_full_width_supported_A_or_C',name,missing_a<1e-6,missing_a,level);ck('gateway_full_width_supported_B',name,missing_b<1e-6,missing_b,level)
 union=unary_union([f['walkable'],bf['walkable']]);clear=union.buffer(-.45);comps=poly(clear);at=Point(end);nearest=min(comps,key=lambda x:x.distance(at));ck('gateway_clearance_at_centre',name,nearest.distance(at)<.05,nearest.distance(at),level)
 # Genuine area overlap is a joined receiving floor, not a gap concealed by a navigation edge.
 overlap=f['public'].intersection(bf['public']).area;ck('gateway_floor_continuous',name,union.buffer(.0000001).covers(seam),overlap,level)
 private=unary_union([s['polygon']for s in f['stores']]);area=private.intersection(bf['public']).area;ck('B_bridge_does_not_pierce_new_private',name,area<EPS,area,level)
 seams.append(dict(id=name,wing=wing,level=level,floor=LABEL[level],world_xz=end,height=HEIGHT[level],width_m=width,missing_width_new_m=missing_a,missing_width_B_m=missing_b,joined_public_overlap_m2=overlap,private_overlap_m2=area,changed_B=False))
 conn_graph[(wing,level)].add(('B',level));conn_graph[('B',level)].add((wing,level))
# Vertical planned connectivity is explicit. Exact field values remain in each wing design file.
vertical=[]
for wing in['A','C']:
 links=D[wing].get('vertical_links',[])
 if not links:
  # Accept only an explicit levels declaration on each core, never infer five-storey service from a shaft symbol.
  links=[c for c in D[wing].get('cores',[])if'levels'in c]
 ck('explicit_vertical_connections',wing,bool(links),len(links))
 for link in links:
  levels=sorted(link.get('levels',[link.get('from_level'),link.get('to_level')]));entry=link.get('entry',link.get('entry_xz'));ck('vertical_link_has_portal',wing+'/'+link['id'],entry is not None)
  if entry is None:continue
  distances={}
  for level in levels:
   if(wing,level)not in floors:continue
   free=floors[(wing,level)]['walkable'];dist=free.distance(Point(entry));distances[level]=dist;ck('vertical_portal_reaches_floor',wing+'/'+link['id'],dist<1.,dist,level)
  for lo,hi in zip(levels,levels[1:]):
   ck('vertical_levels_adjacent',wing+'/'+link['id'],hi==lo+1,[lo,hi])
   if(wing,lo)in floors and(wing,hi)in floors:conn_graph[(wing,lo)].add((wing,hi));conn_graph[(wing,hi)].add((wing,lo))
  vertical.append(dict(wing=wing,id=link['id'],levels=levels,entry=entry,distance_to_walkable=distances,kind=link.get('kind','stair_and_EV'),runtime_tested=False))
# B v4.1 explicitly contains its three levels with repeated aligned service cores.
for core in B['cores']:
 entry=[core['entry'][0]-714,core['entry'][1]-30]
 for level in[0,1,2]:
  dist=floors[('B',level)]['walkable'].distance(Point(entry));ck('B_fixed_core_portal',core['id'],dist<1.,dist,level)
 for lo,hi in[(0,1),(1,2)]:conn_graph[('B',lo)].add(('B',hi));conn_graph[('B',hi)].add(('B',lo))
 vertical.append(dict(wing='B',id=core['id'],levels=[0,1,2],entry=entry,kind='existing_v4_1_planned_stair_and_EV',runtime_tested=False))
start=('A',0);seen={start};todo=[start]
while todo:
 for q in conn_graph[todo.pop()]:
  if q not in seen:seen.add(q);todo.append(q)
for node in floors:ck('defined_floor_network_connected',node[0],node in seen,None,node[1])
# User-approved B baseline and game bytes must remain untouched.
protected=json.loads((O/'protected-baseline-hashes.json').read_text());mismatch=[]
for path,h in protected.items():
 actual=hashlib.sha256((R/path).read_bytes()).hexdigest();ck('protected_file_unchanged',path,actual==h)
 if actual!=h:mismatch.append(path)
summary=collections.Counter(c['kind']for c in CHECKS);failed=[c for c in CHECKS if not c['pass_']]
(O/'connection-register.json').write_text(json.dumps(seams,ensure_ascii=False,indent=2));(O/'vertical-connection-register.json').write_text(json.dumps(vertical,ensure_ascii=False,indent=2));(O/'integration-checks.json').write_text(json.dumps(CHECKS,ensure_ascii=False,indent=2))
with(O/'connection-register.csv').open('w',encoding='utf-8-sig',newline='')as fp:
 w=csv.writer(fp);w.writerow(['ID','A/C側','階','World X','World Z','床高m','幅m','A/C支持不足m','B支持不足m','接続重複㎡','私有区画競合㎡','B変更'])
 for x in seams:w.writerow([x['id'],x['wing'],x['floor'],*x['world_xz'],x['height'],x['width_m'],x['missing_width_new_m'],x['missing_width_B_m'],x['joined_public_overlap_m2'],x['private_overlap_m2'],False])
with(O/'integration-check-summary.csv').open('w',encoding='utf-8-sig',newline='')as fp:
 w=csv.writer(fp);w.writerow(['検査','件数','不合格']);w.writerows([k,v,sum(c['kind']==k and not c['pass_']for c in CHECKS)]for k,v in sorted(summary.items()))
proof=dict(design_only=True,game_modified=False,B_modified=False,source_geometry_sha256=sources,total_checks=len(CHECKS),failed=failed,defined_floor_surfaces=len(floors),connected_defined_floor_surfaces=len(seen),unplanned_B_levels=[{'level':-1,'label':'B1','status':'B v4.1詳細データ対象外・新規設計していない'},{'level':3,'label':'RF','status':'B v4.1詳細データ対象外・新規設計していない'}],runtime_walking_tests=0,area_tolerance_m2=EPS,protected_file_count=len(protected),protected_mismatches=mismatch)
(O/'integration-verification.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2));print(json.dumps(proof,ensure_ascii=False,indent=2));assert not failed,failed[:20]
