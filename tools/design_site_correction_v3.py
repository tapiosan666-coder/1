"""v3 is a separate design revision. All original v2/game files remain read-only."""
from site_v2_common import *
import copy,subprocess
from shapely import make_valid
O=R/'docs/site-correction-v3';O.mkdir(exist_ok=True)
# Freeze the game, original designs, and every v2 deliverable/tool actually used.
protected=read(R/'docs/site-completion-v2/protected-baseline-hashes.json')
for root in ['docs/site-completion-v2','docs/b-completion-v2','docs/parking-blocks-v2','docs/c-area-audit-v2']:
 for p in (R/root).rglob('*'):
  if p.is_file():protected[str(p.relative_to(R))]=sha(p)
for p in (R/'tools').glob('*v2.py'):protected[str(p.relative_to(R))]=sha(p)
for p in (R/'downloads').glob('*v2*'):protected[str(p.relative_to(R))]=sha(p)
write(O/'protected-inputs.json',protected)
A=read(R/'docs/a-detailed-design-v1/geometry.json');B=read(R/'docs/b-v4-overlap-correction/geometry.json');C=read(R/'docs/c-detailed-design-v1/geometry.json');BN=read(R/'docs/b-completion-v2/geometry.json');S=read(R/'docs/site-completion-v2/geometry.json');P=read(R/'docs/parking-blocks-v2/geometry.json');fixes=read(R/'docs/site-completion-v2/B-v4.1-local-cleanup-UNAPPLIED.json')
F={w:{f['level']:copy.deepcopy(f)for f in d['floors']}for w,d in [('A',A),('C',C),('B',BN)]}
for raw in B['floors']:
 f=floor_B_world(raw,[core_world(c)for c in B['cores']]);f['escalators']=[]
 for e in B['escalators']:
  if raw['floor']not in e['levels']:continue
  q=translate_geoms(copy.deepcopy(e),-714,-30);q['levels']=[l-1 for l in e['levels']];q['c']=[e['c'][0]-714,e['c'][1]-30];f['escalators'].append(q)
 for st in f['stores']:
  if st.get('loading_door'):st['loading_door']['point']=[st['loading_door']['point'][0]-714,st['loading_door']['point'][1]-30]
 F['B'][f['level']]=f
CHANGES=[]
# Commit the reviewed micro-boundary correction into the NEW revision, not the old source.
for prop in fixes:
 f=F['B'][prop['floor']];before=copy.deepcopy(f);f['public']=prop['public_proposed'];after={s['id']:s for s in prop['stores_proposed']}
 for s in f['stores']:
  old=copy.deepcopy(s);q=after[s['id']];s['polygon']=q['polygon'];s['entry']=q['entry'];s['main_route'][0]=q['entry'];s['front']=[(q['entry'][0]+s['u'][0]*a,q['entry'][1]+s['u'][1]*a)for a in[-s['door_width_m']/2,s['door_width_m']/2]]
  for k in['backroom','sales','shelf_zones','aisles']:
   if k in s:s[k]=s[k].intersection(s['polygon'])
  s['aisles']=s['aisles'].union(LineString(s['main_route']).buffer(.6).intersection(s['polygon']));s['shelf_zones']=s['shelf_zones'].difference(s['aisles'].buffer(.05))
  # New boundary wall with the actual frontage aperture, rather than clipping a stale wall face.
  doorcut=rect(s['entry'],s['u'],s['door_width_m'],.7);s['wall_solids']=s['polygon'].boundary.buffer(.125).intersection(s['polygon']).difference(doorcut)
  if s.get('loading_door'):
   ld=s['loading_door'];s['wall_solids']=s['wall_solids'].difference(rect(ld['point'],ld['u'],ld['width'],.7))
  CHANGES.append(dict(kind='B_store_boundary_and_entry',id=s['id'],level=f['level'],old_polygon=old['polygon'],new_polygon=s['polygon'],changed_area_m2=old['polygon'].symmetric_difference(s['polygon']).area,old_entry=old['entry'],new_entry=s['entry'],entry_shift_m=math.dist(old['entry'],s['entry'])))
 f['residual']=f['residual'].difference(f['public'])
# Each A/B shaft is represented in floor slabs and in its actual access/landing layout.
VERTICAL=[]
def cg(c,g):return affinity.translate(affinity.rotate(g,c['angle'],origin=(0,0)),*c['centre'])
for w in ['A','B']:
 for lev,f in F[w].items():
  f['vertical_devices']=[]
  for c in f['cores']:
   lift=c['rooms']['lift'].buffer(-.1,join_style=2);stair=cg(c,box(-11.65,-6.2,-6.35,-1.65));cut=lift.union(stair if lev>-1 else Polygon());f['shafts']=f['shafts'].union(cut);f['floor_plate']=f['floor_plate'].difference(cut)
   front=cg(c,box(-11.65,-1.5,-6.35,5.75));ret=cg(c,box(-11.65,-8.3,-6.35,-6.1));flights=[cg(c,box(-11.5,-6.15,-9.5,-1.65)),cg(c,box(-9.2,-6.15,-7.2,-1.65))];evland=cg(c,box(-2.9,-4.75,-1.1,-3.25));evdoor=next(q for q in c['doors']if q['id']=='EV');stdoor=next(q for q in c['doors']if q['id']=='ST');wallempty=c['room_wall_solids'].union(unary_union(c.get('cubicle_wall_solids',[]))).union(unary_union([x.buffer(.08)for x in c.get('vestibule_screens',[])]));fixtures=unary_union([q['geom']for q in c['fixtures']]);corefree=c['outline'].buffer(-.125).difference(wallempty.union(fixtures).union(lift).union(stair));entrybridge=rect(c['entry'],[-math.sin(math.radians(c['angle'])),math.cos(math.radians(c['angle']))],1.8,next(q['w']for q in c['doors']if q['id']=='CORE'))
   # CORE portal is perpendicular to local z; add the short threshold to the existing public edge.
   corefree=corefree.union(entrybridge).difference(wallempty.union(fixtures).union(f['shafts'])).intersection(f['floor_plate']);f['core_free']=f.get('core_free',Polygon()).union(corefree)
   # The cabin floor is movable equipment, explicitly NOT infilled structural slab.
   cabin=cg(c,box(-3.7,-8.8,-.3,-5.12));v=dict(id=w+'-'+c['id']+'-'+LABEL[lev],wing=w,core=c['id'],level=lev,height=HEIGHT[lev],lift_opening=lift,stair_opening=stair if lev>-1 else Polygon(),lower_flight_projection=flights[0],upper_flight_projection=flights[1],front_landing=front,return_landing=ret,mid_landing=ret,mid_landing_elevation_m=(HEIGHT[lev]+HEIGHT[lev+1])/2 if lev<3 else None,mid_landing_slab_thickness_m=.18,lift_sill_when_docked=cg(c,box(-2.7,-5.12,-1.3,-4.98)),lift_front_gap_m=.02,lift_landing=evland,lift_door=evdoor,stair_door=stdoor,cabin_floor_when_docked=cabin,cabin_is_structural_slab=False,lift_anchor=list(cg(c,Point(-2,-3.8)).coords[0]),stair_anchor=list(cg(c,Point(-8.5,3)).coords[0]),stair_width_m=2.,risers=32,riser_to_next_m=(HEIGHT[lev+1]-HEIGHT[lev])/32 if lev<3 else None,tread_m=.3,flight_run_m=4.5,landing_design_m=2.,state='reflected in new v3 drawings, game unimplemented')
   f['vertical_devices'].append(v);VERTICAL.append(v)
# C's existing internal openings remain fixed; close the same small exterior threshold gap only.
for lev,f in F['C'].items():
 f['core_free']=Polygon()
 for c in f['cores']:
  portal=next(d for d in c['doors']if d['id']=='CORE');axis=portal['axis'];normal=[-axis[1],axis[0]];bridge=rect(c['entry'],normal,1.8,portal['w']);free=c['walkable'].union(bridge).difference(c['room_wall_solids']).intersection(f['floor_plate']);f['core_free']=f['core_free'].union(free)
# Local access fixes exposed by the full-width audit: do not route through a shop wall.
for w in ['A','B']:
 for lev,f in F[w].items():
  for c in f['cores']:
   d=next(q for q in c['doors']if q['id']=='CORE');axis=d['axis'];bridge=rect(c['entry'],[-axis[1],axis[0]],1.8,d['w']);f['public']=f['public'].union(bridge.difference(c['outline']));f['residual']=f['residual'].difference(bridge)
   for st in f['stores']:
    if st['polygon'].intersection(bridge).area<EPS:continue
    old=st['polygon'];st['polygon']=old.difference(bridge)
    for k in['backroom','sales','shelf_zones','aisles']:st[k]=st[k].intersection(st['polygon'])
    aperture=rect(st['entry'],st['u'],st['door_width_m'],.8)
    if st.get('secondary_entry'):aperture=aperture.union(rect(st['secondary_entry'],st.get('secondary_u',st['u']),st['secondary_door_width_m'],.8))
    st['wall_solids']=st['polygon'].boundary.buffer(.125).intersection(st['polygon']).difference(aperture);CHANGES.append(dict(kind=w+'_core_threshold_local_store_recess',id=st['id'],level=lev,removed_m2=old.difference(st['polygon']).area,old_polygon=old,new_polygon=st['polygon']))
# Move existing C benches/planters out of equipment-door approaches; no new floor/corridor.
for lev,f in F['C'].items():
 zones=[]
 for c in f['cores']:
  dc=next(q for q in c['doors']if q['id']=='CORE');axis=dc['axis'];zones.append(rect(c['entry'],[-axis[1],axis[0]],3.5,dc['w']+.6))
 keepclear=unary_union(zones)
 for obj in f.get('furniture',[]):
  if obj['geom'].intersection(keepclear).area<EPS:continue
  old=obj['geom'];choice=[]
  for c in f['cores']:
   axis=next(q for q in c['doors']if q['id']=='CORE')['axis']
   for offset in[-3,3,-4,4,-5,5,-6,6,-8,8]:
    dx,dz=axis[0]*offset,axis[1]*offset;g=affinity.translate(old,dx,dz);other=unary_union([q['geom']for q in f['furniture']if q is not obj])
    if f['public'].buffer(.001).covers(g.buffer(.1))and g.distance(keepclear)>.2 and g.distance(other)>.25:choice.append((abs(offset),dx,dz,g))
  if not choice:raise RuntimeError(('cannot place existing C furniture',lev,obj.get('id')))
  _,dx,dz,g=min(choice,key=lambda q:q[0]);obj['geom']=g;CHANGES.append(dict(kind='C_equipment_approach_furniture_shift',id=obj.get('id',obj.get('kind')),level=lev,old=old,new=g,shift_x_m=dx,shift_z_m=dz))
# v3 façade solids, retaining old bridge and emergency openings rather than closing them.
for w,ff in F.items():
 for lev,f in ff.items():
  if w=='B':
   wall=f['shell'].boundary.buffer(.125).intersection(f['floor_plate']);wall=wall.difference(f['public'])
  else:wall=f.get('facade_wall_solids',Polygon())
  f['envelope_walls']=wall;f['vestibule_walls']=Polygon();f['doors_v3']=[]
# Three actual customer doors: telescopic sliding panels park OUTSIDE the clear opening.
DOORS=[]
for prop in S['arrival_proposals']:
 w=prop['wing'];lev=prop['level'];f=F[w][lev];oldpub=f['public'];n=prop['normal'];ll=math.hypot(*n);n=[n[0]/ll,n[1]/ll];u=[-n[1],n[0]];ep=prop['entry'];axis=LineString([(ep[0]-n[0]*3,ep[1]-n[1]*3),(ep[0]+n[0]*7,ep[1]+n[1]*7)]);cross=axis.intersection(f['shell'].boundary)
 candidates=[]
 def pts(g):
  if g.geom_type=='Point':return[g]
  if g.geom_type=='MultiPoint':return list(g.geoms)
  if g.geom_type=='LineString':return[Point(g.coords[0]),Point(g.coords[-1])]
  return[p for x in getattr(g,'geoms',[])for p in pts(x)]
 for q in pts(cross):
  dot=(q.x-ep[0])*n[0]+(q.y-ep[1])*n[1]
  if dot>=-.01:candidates.append((dot,q))
 t,center=min(candidates,key=lambda q:q[0]);cen=list(center.coords[0]);clear=3.6 if w=='B'else 2.4;leaf=clear/4;frame_open=clear+2*leaf;total=frame_open+.2;rough=total+.04
 # Main vestibule floor, threshold, open/closed leaf states, frame and rail pocket are distinct solids.
 f['public']=f['public'].union(prop['polygon']);f['floor_plate']=f['floor_plate'].union(prop['polygon']);f['residual']=f['residual'].difference(prop['polygon']);f['envelope_walls']=f['envelope_walls'].difference(prop['polygon'])
 aperture=rect(cen,u,rough,.8);clearpath=rect(cen,u,clear,1.0);jambs=unary_union([rect((cen[0]+u[0]*a,cen[1]+u[1]*a),u,.1,.3)for a in[-(frame_open/2+.05),(frame_open/2+.05)]]);opened=unary_union([rect((cen[0]+u[0]*a,cen[1]+u[1]*a),u,leaf,.14)for a in[-(clear/2+leaf/2),(clear/2+leaf/2)]]);closed=rect(cen,u,clear,.06)
 sides=[]
 for sign in[-1,1]:
  line=LineString([(ep[0]+n[0]*a+u[0]*sign*prop['width_m']/2,ep[1]+n[1]*a+u[1]*sign*prop['width_m']/2)for a in[-1.5,4]])
  sides.append(line.buffer(.08,cap_style=2).difference(oldpub))
 infill=rect(cen,u,prop['width_m']+.16,.3).difference(rect(cen,u,total,.5));side=unary_union(sides);f['vestibule_walls']=f['vestibule_walls'].union(side).union(infill);landings=[rect((cen[0]+n[0]*sign*1.05,cen[1]+n[1]*sign*1.05),u,clear,1.5)for sign in[-1,1]]
 d=dict(id=prop['id'],wing=w,level=lev,height=HEIGHT[lev],center=cen,normal=n,u=u,clear_width_m=clear,frame_opening_width_m=rough,frame_internal_width_m=frame_open,installation_seal_each_side_m=.02,overall_frame_width_m=total,infill_panels=infill,door_height_m=2.8 if w=='B'else 2.6,vestibule_width_m=prop['width_m'],vestibule_floor=prop['polygon'],aperture=aperture,clear_path=clearpath,frames=jambs,open_leaves=opened,closed_leaves=closed,side_walls=side,landings=landings,threshold_step_m=0,leaf_count=4,type='telescopic automatic sliding',design_applied_to_revision=True,game_implemented=False,inside_anchor=[cen[0]-n[0],cen[1]-n[1]],outside_anchor=[cen[0]+n[0],cen[1]+n[1]])
 f['doors_v3'].append(d);DOORS.append(d);prop.update(applied=True,applied_to_revision=True,applied_to_original=False,status='v3設計へ反映、ゲーム未実装')
# Keep the separate A loading door explicitly out of the approved customer scope.
S['approval_conditions']=['ゲーム実装は未承認','車両未検証軌跡は車両報告でNOT_TESTED','A東追加搬入扉は従来別案のまま。今回の来客入口3か所と区別。']
for fac in P['facilities']:
 for f in fac['floors']:
  aprons=[]
  for st in f['stalls']:
   link=st['pedestrian_access_link'];coords=list(link.coords);a,b=coords[-2:];length=math.dist(a,b);u=[(b[j]-a[j])/length for j in[0,1]];end=[b[j]+u[j]*.5 for j in[0,1]];apron=LineString([coords[0],end]).buffer(.5,cap_style=2).difference(st['polygon']);aprons.append(apron)
  added=unary_union(aprons);f['rear_access_aprons']=added;f['pedestrian']=f['pedestrian'].union(added);f['protected_pedestrian']=f['protected_pedestrian'].union(added).difference(f['vehicle_aisles']);f['crossings']=f['pedestrian'].intersection(f['vehicle_aisles'])
# Open only active upper parking bridge apertures in the new parking revision.
PCH=[]
for fac in P['facilities']:
 for f in fac['floors']:
  active=[q for q in fac['portals']if q['level']==f['level']and(q['level']==0 or(fac['id']=='P-A-E'and q['level']==2)or(fac['id']=='P-B-S'and q['level']==6))]
  for q in active:
   n=q['normal'];u=[-n[1],n[0]];cut=rect(q['point'],u,q['width_m']+.05,1.0)
   for key in['edge_guard','temporary_guard_until_bridge_built']:
    if key in f:
     old=f[key];f[key]=old.difference(cut)
     if old.difference(f[key]).area>EPS:PCH.append(dict(facility=fac['id'],level=f['level'],port=q['id'],kind=key,removed=old.difference(f[key])))
# Rebuild useful navigation floor: actual slabs, fixed walls, fixtures and open door state.
for w,ff in F.items():
 for lev,f in ff.items():
  furniture=unary_union([q['geom']for q in f.get('furniture',[])if isinstance(q,dict)and'geom'in q]);doorblock=unary_union([d['frames'].union(d['open_leaves'])for d in f['doors_v3']]);walls=f['envelope_walls'].union(f['vestibule_walls']).union(doorblock)
  f['public']=f['public'].intersection(f['floor_plate']).difference(f['void'].union(f['shafts']));coreout=unary_union([c['outline']for c in f['cores']]);storewalls=unary_union([s.get('wall_solids',Polygon())for s in f['stores']]);f['walkable']=f['public'].difference(coreout).union(f.get('core_free',Polygon())).difference(furniture.union(walls).union(storewalls)).intersection(f['floor_plate']);f['nav_free']=f['walkable'];f['nav_avatar_radius_m']=.30;f['wing']=w;f['revision']='v3';f['game_implemented']=False
  if f.get('parking'):
   f['parking']['protected_pedestrian']=f['public'];f['parking']['crossings']=f['public'].intersection(f['parking']['vehicle_aisles'])
  CHANGES.append(dict(kind='floor_revision',id=w+'-'+LABEL[lev],public_m2=f['public'].area,slab_m2=f['floor_plate'].area,store_count=len(f['stores'])))
S['version']='Whole site design correction v3';S['game_modified']=False
write(O/'geometry.json',dict(version='site correction v3',design_only=True,game_modified=False,coordinate_system='World XZ metres',floors=[F[w][l]for w in['A','B','C']for l in[-1,0,1,2,3]],site=S,doors=DOORS,vertical_devices=VERTICAL,changes=CHANGES,parking_guard_changes=PCH,old_originals_modified=False))
write(O/'parking-geometry.json',P);write(O/'change-register.json',CHANGES);write(O/'customer-doors.json',DOORS);write(O/'vertical-devices.json',VERTICAL)
csvwrite(O/'door-ledger.csv',['ID','館','階','X','Y','Z','有効幅m','躯体開口幅m','枠外寸m','扉高さm','段差m','設計版反映','Godot実装'],[[d['id'],d['wing'],LABEL[d['level']],d['center'][0],d['height'],d['center'][1],d['clear_width_m'],d['frame_opening_width_m'],d['overall_frame_width_m'],d['door_height_m'],0,True,False]for d in DOORS])
csvwrite(O/'65-issue-corrections.csv',['旧不合格種別','旧ID','旧値','新設計版','旧原本変更'],[[q['kind'],q['id'],q['value'],'v3',False]for q in read(R/'docs/site-completion-v2/independent-verification.json')['failed']])
print('generated',len(F['A'])+len(F['B'])+len(F['C']),'floors',len(DOORS),'doors',len(VERTICAL),'core floors',len(PCH),'parking guard cuts')
