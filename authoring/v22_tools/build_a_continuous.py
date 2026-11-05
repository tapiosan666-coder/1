from pathlib import Path
import sys,json,copy,math,re,collections,numpy as np
P=Path(__file__).resolve().parents[2];A=P/'authoring'
sys.path.insert(0,str(A));from site_v2_common import *;from pack_tools_v11 import *
from shapely.validation import make_valid
from shapely import contains_xy,intersects_xy,constrained_delaunay_triangles,polygons as triangle_polygons,covers as covers_geom
F=read(P/'source/v11/floors-updated.json');source=P/'source/v22';basepaths=['v10/base-b','v10/base-site','v10/fitout','v10/art','v10/architecture','v11/repairs','v12/es-safety','v12/retail','v12/boundary-physics','v12/es-unbuilt-safety','v12/es-landing-plates','v13/amenities','v13/public-areas','v13/basement-retail','v13/roof-retail'];S={};cols={}
for path in basepaths:
 g=load_pack(P/('assets/'+path+'.pack.zst'))
 for k,v in g['surfaces'].items():S.setdefault(k,v)
 for k,v in g['colliders'].items():cols.setdefault(k,[]).append(v)
cols={k:np.concatenate(v)for k,v in cols.items()};parent=load_pack(P/'assets/v22/combined-structure.pack.zst');info=read(source/'combined-structure.json')
for key in info['erase_surfaces']:S.pop(key,None)
S.update(parent['surfaces']);cols.update(parent['colliders']);changed=dict(parent['surfaces']);erase=set(info['erase_surfaces']);retired=[e for e in read(P/'source/site-manifest-v7.json')['escalators']if e['id'].startswith('A-E1-')and e['levels'][0]>=0];oldids={e['id']for e in retired};oldtri=set()
def fingerprint(t):return tuple(sorted(tuple(float(x)for x in p)for p in t))
for key,d in list(S.items()):
 if any(tag in key for identity in oldids for tag in ['@@ESC-'+identity,'@@V12-ES-'+identity,'@@V12-LANDING-'+identity]):
  oldtri.update(fingerprint(t)for t in triangles(d));erase.add(key);changed.pop(key,None)
centre=np.array([330.,-39.]);outer=box(318,-50,342,-28);huge=box(-2000,-2000,2000,2000);levels=[(HEIGHT[i],huge,huge.difference(outer))for i in [1,2,3]];unsupported_furniture={y:Polygon()for y,_,_ in levels};public_extent_by_y={y:outer.buffer(.03)for y,_,_ in levels};protected_by_y={y:Polygon()for y,_,_ in levels}
exec((A/'v22_clip_geometry.py').read_text());audit=[]
for key,d in S.items():
 if key in erase:continue
 nd,count=clip(d,key)
 if count:
  if len(nd['v']):changed[key]=nd
  else:erase.add(key);changed.pop(key,None)
  audit.append({'surface':key,'triangles_clipped':count})
newcols={}
for mat,v in cols.items():
 t=v.reshape(-1,3,3);keep=np.array([fingerprint(tri)not in oldtri for tri in t]);t=t[keep];d={'v':t.ravel(),'n':np.tile([0.,1.,0.],(len(t)*3,1)).ravel(),'uv':np.zeros(len(t)*6),'c':np.ones(len(t)*12)};nd,count=clip(d,'COLLIDER:'+mat);newcols[mat]=nd['v']
module=load_pack(P/'assets/v15/ES-upper-module.pack.zst');study=read(P/'source/v15/ES-upper-module.json')
for key,d in module['surfaces'].items():
 d['v']=(d['v'].reshape(-1,3)+np.array([centre[0],0,centre[1]])).astype(np.float32).ravel();changed[key.replace('V12-TRANSFER-STUDY','V22-A-WEST-CONTINUOUS')]=d
for mat,v in module['colliders'].items():newcols[mat]=np.concatenate([newcols.get(mat,np.array([])),(v.reshape(-1,3)+np.array([centre[0],0,centre[1]])).ravel()])
M={};coll={};render_group='V22-A-ES-TIE-IN'
def pos(x,y,z):return[float(x),float(y),float(z)]
exec((A/'mesh_primitives.py').read_text());W=lambda g:affinity.translate(g,429,-46);restored=[]
for lev in [0,1,2,3]:
 f=next(f for f in F if f['wing']=='A'and f['level']==lev);parts=[rect((e['c'][0],e['c'][2]),e['u'],e['run_m']+3.6,2.65)for e in retired if lev in e['levels']];g=unary_union(parts).difference(W(f['void'])).difference(outer);g=g.intersection(W(f['public']))
 if not g.is_valid:g=make_valid(g)
 extrude(g,HEIGHT[lev]-.38,.38,'stone',True);surf(g,HEIGHT[lev]+.005,'v10_floor_A');restored.append({'floor':f['label'],'old_flight_slot_filled_m2':g.area})
# Two genuine public connections: west promenade and north frontage. East/south sides still face an atrium.
from triangle_cut_v15 import cut
mouths=[(317.5,-41.05,318.5,-36.95),(327.95,-50.5,332.05,-49.5)];rail_mats=['glass','v10_guard_glass','v10_darkstone','dark_stone','v10_metal','metal','v10_chalk'];allSurfaces=dict(S);allSurfaces.update(changed)
for key in erase:allSurfaces.pop(key,None)
for key,d in allSurfaces.items():
 if key.split('@@')[0]not in rail_mats:continue
 nd,count=cut(d,mouths,[HEIGHT[i]for i in [0,1,2,3]])
 if count:
  if len(nd['v']):changed[key]=nd
  else:erase.add(key);changed.pop(key,None)
for mat,v in list(newcols.items()):
 if mat not in rail_mats:continue
 t=v.reshape(-1,3,3);d={'v':t.ravel(),'n':np.tile([0.,1.,0.],(len(t)*3,1)).ravel(),'uv':np.zeros(len(t)*6),'c':np.ones(len(t)*12)};nd,count=cut(d,mouths,[HEIGHT[i]for i in [0,1,2,3]]);newcols[mat]=nd['v']
changed.update(M)
for mat,v in coll.items():newcols[mat]=np.concatenate([newcols.get(mat,np.array([])),np.array(v)])
for key in erase:changed.pop(key,None)
save_zst(P/'assets/v22/integrated-ABC.pack.zst',{'surfaces':changed,'colliders':newcols,'signs':[],'lights':[]})
es=copy.deepcopy(study['escalators']);transfers=copy.deepcopy(study['transfers'])
for e in es:
 e['id']=e['id'].replace('STUDY','A-WEST-V22');e['wing']='A'
 for field in ['c','test_start','test_end']:e[field][0]+=centre[0];e[field][2]+=centre[1]
for t in transfers:
 t['from']=t['from'].replace('STUDY','A-WEST-V22');t['to']=t['to'].replace('STUDY','A-WEST-V22')
 for q in t['points']:q[0]+=centre[0];q[2]+=centre[1]
write(source/'A-continuous-ES.json',{'status':'SITE_CANDIDATE_PHYSICS_PENDING','centre_world':[330,0,-39],'escalators':es,'transfers':transfers,'retired_machine_ids':sorted(oldids),'floor_slot_restorations':restored,'surface_clipping':audit,'controller_changed':False,'stores_relocated':False,'structural_capacity_verified':False,'supports_foundation_egress':'UNVERIFIED','chosen_reason':'Zero store/building boundary overlap at all four floors; west and north mouths connect to existing A public promenade, east/south remain guarded at atrium.'})
info['erase_surfaces']=sorted(erase);info['includes_A_continuous']=True;info['physical_tested']=False;write(source/'integrated-ABC.json',info)
# Update the same authoritative floor-map data as geometry, retaining every store entry and other facility.
md=read(source/'map-data-combined.json')
def geom(a):return unary_union([Polygon(r[0],r[1:])for r in a])
def pg(g):return[[list(map(list,p.exterior.coords))]+[list(map(list,r.coords))for r in p.interiors]for p in polys(g)]
for f in md:
 if f['wing']!='A'or f['level']<0:continue
 lev=f['level'];void=box(322.6,-46.4,337.4,-31.6)if lev>0 else Polygon();modulefloor=outer.difference(void);floor=geom(f['floor']);public=geom(f['public']);local=affinity.translate(outer,-429,46);m=affinity.translate(modulefloor,-429,46);f['floor']=pg(floor.difference(local).union(m));f['public']=pg(public.difference(local).union(m))
 f['items']=[r for r in f.get('items',[])if not any(identity in str(r['id'])for identity in oldids)]
 for e in es:
  if lev not in e['levels']:continue
  q=(e['test_start']if lev==e['levels'][0]else e['test_end']);g=rect((e['c'][0]-429,e['c'][2]+46),e['u'],e['run_m']+3.6,2.0);f['items'].append({'id':e['id'],'kind':'エスカレーター','point':[q[0]-429,q[2]+46],'geometry':pg(g),'implemented':True})
write(source/'map-data-integrated.json',md);print('A_CONTINUOUS built',len(es),'flights;',len(changed),'changed surfaces;',len(erase),'retired surfaces')
