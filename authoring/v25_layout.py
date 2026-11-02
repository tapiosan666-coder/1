from pathlib import Path
import sys,numpy as np,math,collections
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import read,write,Polygon,Point,LineString
plan=read(P/'source/v24/retail-plan.json');focus=read(P/'source/v25/focus-stores.json');pilot='--pilot'in sys.argv;selected=[d for d in focus if not pilot or d['category']=='apparel'];B={}
for v in[21,22,23,24,25]:B.update(read(P/f'source/v{v}/model-bounds.json'))
records=[];decor=[];rejected=[];oldphysics=read(P/'source/v24/shopping-physics.json');paths=read(P/'source/v24/shopping-body-routes.json')['routes'];serial=0
for d in selected:
 if d['category']!='apparel':continue
 sid=d['id'];s=next(s for s in plan['stores']if s['id']==sid);e=np.array(d['entry_world']);n=np.array(d['n']);u=np.array(d['u']);own=[f for f in plan['fixtures']if f['store_id']==sid];block=s['protected_aisles_world'].buffer(.05)
 for a in oldphysics['equipment']:
  if a['store_id']==sid and a['standing_clear']:block=block.union(Point(a['approach'][0],a['approach'][2]).buffer(.50))
 for path in paths:
  if path['store_id']==sid:block=block.union(LineString([(p[0],p[2])for p in path['points']]).buffer(.45))
 mapping={'fixture_v23_bag_wall':'fixture_v25_bag_gallery','fixture_v23_nested_display':'fixture_v25_nested_atelier','fixture_checkout':'fixture_v25_atelier_checkout','fixture_v23_outfit_display':'fixture_v25_window_outfits'}
 for f in own:
  old=f['model'];model=mapping.get(old)
  if old=='fixture_apparel_rail':model='fixture_v25_wardrobe'if f['role']=='wall_department'else'fixture_v25_gallery_rail'
  if not model:continue
  f['model']=model;f['asset']='../v25/models/'+model;f['source_model_v24']=old;records.append({'id':f['id'],'store_id':sid,'from':old,'to':model,'position_retained':True,'approach_IDs_retained':True})
 # New central feature occupies an existing empty selling zone, not the protected diagonal circulation.
 for k,(x,z)in enumerate([(-4.6,9.4),(1.1,8.0)]):
  model='fixture_v25_nested_atelier'if k==0 else'fixture_v25_gallery_rail';q=e+u*x+n*z;bb=B[model];normal=-n;uu=np.array([normal[1],-normal[0]]);poly=Polygon([q+uu*xx+normal*zz for xx,zz in[(bb['min'][0],bb['min'][2]),(bb['max'][0],bb['min'][2]),(bb['max'][0],bb['max'][2]),(bb['min'][0],bb['max'][2])]])
  if not s['sales_world'].buffer(-.12).covers(poly)or block.intersects(poly)or any(poly.distance(f['footprint'])<.65 for f in own):rejected.append({'store':sid,'model':model,'local':[x,z],'reason':'Existing approach/path or fixture clearance'});continue
  serial+=1;f={'id':f'V25-{sid}-collection-{serial}','store_id':sid,'wing':s['wing'],'floor':s['floor'],'level':0,'model':model,'asset':'../v25/models/'+model,'p':[float(q[0]),s['height']+.02,float(q[1])],'n':normal.tolist(),'scale':1.,'scale_x':1.,'collision':'mesh','activation':'always','role':'collection_story','footprint':poly,'brand_ref':sid};plan['fixtures'].append(f);own.append(f)
  # Merchandise is copied from a compatible fixture role and translated, not from another industry's display.
  source=next(h for h in own if h['id']!=f['id']and h['model']==model);source_items=[r for r in plan['products']if r['host']==source['id']];sn=np.array(source['n']);su=np.array([sn[1],-sn[0]])
  for j,r in enumerate(source_items):
   rec=r.copy();offset=np.array(r['p'])[[0,2]]-np.array(source['p'])[[0,2]];local=[offset@su,offset@sn];point=q+uu*local[0]+normal*local[1];rec.update(id=f['id']+'-item-'+str(j),host=f['id'],p=[float(point[0]),f['p'][1]+r['p'][1]-source['p'][1],float(point[1])]);rn=np.array(r['n']);rec['n']=(uu*(rn@su)+normal*(rn@sn)).tolist();plan['products'].append(rec)
  records.append({'id':f['id'],'store_id':sid,'to':model,'role':'centre capsule collection','position_retained':False})
 for x,z in[(-4.6,5.8),(1.1,7.5),(-4.6,12.7),(1.0,14.2)]:
  q=e+u*x+n*z;poly=Polygon([q+u*a+n*b for a,b in[(-1.65,-1.25),(1.65,-1.25),(1.65,1.25),(-1.65,1.25)]])
  if s['sales_world'].buffer(-.08).covers(poly):decor.append({'store_id':sid,'model':'finish_v25_raft','p':[float(q[0]),s['height']+3.58,float(q[1])],'n':n.tolist(),'role':'suspended_acoustic_raft','floor_height':s['height'],'support_half_width':1.45})
 q=e+u*(-2)+n*.7;decor.append({'store_id':sid,'model':'finish_v25_fernell_fascia','p':[float(q[0]),s['height']+3.5,float(q[1])],'n':(-n).tolist(),'role':'suspended_brand_fascia','floor_height':s['height'],'support_half_width':2.4})
retired=[r for r in plan['boards']if r['store_id']in{d['id']for d in selected}and r.get('fixture_id')]
plan['boards']=[r for r in plan['boards']if r not in retired];write(P/'source/v25/retired-department-boards.json',retired)
plan['revision']='v25-five-authored-interiors';plan.pop('instances',None);plan.pop('retirement_stores',None);write(P/'source/v25/retail-plan.json',plan);write(P/'source/v25/changes.json',{'pilot':pilot,'changes':records,'rejected':rejected,'architecture_changed':False,'old_fixture_positions_retained':True});write(P/'source/v25/suspended-finishes.json',decor)
# Retain v24 finishing outside the selected store, and use an independent finish pass inside it.
release=read(P/'source/v24/finish-release.json');release['enabled_store_ids']=[sid for sid in release['enabled_store_ids']if sid not in{d['id']for d in selected}];write(P/'source/v25/retained-v24-finishes.json',release)
finishes=[d for d in read(P/'source/v24/store-finishes.json')if d['id']in{x['id']for x in selected}]
for d in finishes:d['wall_colour']='#d7cdbb';d['accent_colour']='#294f3d';d['floor_colour']='#c3ac88';d['floor_roughness']=.54;d['style']='v25-authored-atelier'
write(P/'source/v25/store-finishes.json',finishes);write(P/'source/v25/finish-release.json',{'enabled_store_ids':[d['id']for d in selected]});print('V25_LAYOUT',len(records),'changes',len(decor),'suspended features','rejected',rejected)
