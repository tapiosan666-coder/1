"""Independent recomputation from final polygons; no imported PASS flags."""
from pathlib import Path
import sys,json,csv,math,hashlib,collections
sys.path.insert(0,str(Path(__file__).resolve().parent));from site_v2_common import *
import numpy as np,shapely
P=Path(__file__).resolve().parents[1];S=P/'source';D=read(S/'design-v5.json');base=read((Path(__file__).resolve().parents[1]/'source/baseline-v4.json'));old={s['id']:s for f in base['floors']for s in f['stores']};checks=[];led=[];bounds=[]
def ck(name,actual,limit=1e-5,unit='m2'):checks.append({'id':name,'measured':float(actual),'limit':limit,'unit':unit,'pass':float(actual)<=limit})
def net(s):return s['sales'].difference(s['polygon'].boundary.buffer(.12)).difference(s['backroom'].boundary.intersection(s['sales'].buffer(.0005)).buffer(.1)).area
def csvout(name,rows):
 if not rows:return
 with open(S/name,'w',encoding='utf-8-sig',newline='')as fh:w=csv.DictWriter(fh,rows[0].keys());w.writeheader();w.writerows(rows)
prev=list(csv.DictReader(open(P/'source/baseline-followup/56-backroom-followup.csv',encoding='utf-8-sig')));old48={q['id']for q in prev if q['layout_geometry_pass']=='False'};assert len(old48)==48
summary=[];oldids=set(old);newids={s['id']for f in D['floors']for s in f['stores']};ck('existing IDs removed',len(oldids-newids),0,'count')
for f,b in zip(D['floors'],base['floors']):
 ss=f['stores'];plots=unary_union([s['polygon']for s in ss]);roles=[q['polygon']for q in f['floor_roles']];covered=unary_union(roles);floor=f['floor_plate'];ck(f['label']+' floor unassigned',floor.difference(covered).area);ck(f['label']+' role overlap',max(0,sum(q.area for q in roles)-covered.area));ck(f['label']+' plot overlap',sum(s['polygon'].area for s in ss)-plots.area);ck(f['label']+' public/plots overlap',plots.intersection(f['public']).area);ck(f['label']+' services/plots overlap',plots.intersection(unary_union([q['polygon']for q in f['service_zones']])).area);ck(f['label']+' void changed',f['void'].symmetric_difference(b['void']).area);ck(f['label']+' public changed',shapely.symmetric_difference(f['public'],b['public'],grid_size=1e-7).area);ck(f['label']+' opening has slab',floor.intersection(f['floor_openings_v5']).area)
 main_public=max(polys(f['public'].buffer(-.44)),key=lambda p:p.area)
 for s in ss:
  p=s['polygon'];stock=s['backroom'];sales=s['sales'];o=old.get(s['id']);oldnet=net(o)if o else 0;newnet=net(s);s['net_sales_m2']=newnet
  ck(s['id']+' invalid polygon',int(not p.is_valid),0,'bool');ck(s['id']+' disconnected plot',len(polys(p))-1,0,'count');ck(s['id']+' programme uncovered',p.difference(stock.union(sales)).area);ck(s['id']+' sales/stock overlap',stock.intersection(sales).area);ck(s['id']+' net sales loss',max(0,oldnet-newnet),.02);ck(s['id']+' work module outside room',s['work_rectangle'].difference(stock.buffer(-.12)).area)
  e=np.array(s['entry']);n=np.array(s['n']);ck(s['id']+' common concourse connected',Point(e-n*.9).distance(main_public),.003,'m');ck(s['id']+' public approach misses public',Point(e-n*.9).distance(f['public']),.002,'m');ck(s['id']+' sales approach misses sales',Point(e+n).distance(sales),.002,'m')
  gap_to_public=stock.boundary.intersection(f['public'].buffer(.005)).length
  coords=list(max(polys(p.simplify(.01)),key=lambda q:q.area).exterior.coords)[:-1];acute=0
  for i,c in enumerate(coords):
   a=np.array(coords[i-1])-c;bb=np.array(coords[(i+1)%len(coords)])-c;le=np.linalg.norm(a)*np.linalg.norm(bb)
   if le<.15:continue
   angle=math.degrees(math.acos(float(np.clip(np.dot(a,bb)/le,-1,1))))
   if angle<30 and min(np.linalg.norm(a),np.linalg.norm(bb))>.3:acute+=1
  led.append({'id':s['id'],'floor':f['label'],'category':s['category'],'new_unit':o is None,'old_plot_m2':o['polygon'].area if o else 0,'new_plot_m2':p.area,'old_sales_m2':o['sales'].area if o else 0,'new_sales_m2':sales.area,'old_net_sales_m2':oldnet,'new_net_sales_m2':newnet,'net_sales_delta_m2':newnet-oldnet,'old_backroom_m2':o['backroom'].area if o else 0,'new_backroom_m2':stock.area,'backroom_percent':stock.area/p.area*100,'work_module_m':str(s['work_dimensions_m']),'entry_x':e[0],'entry_z':e[1],'old_entry_x':o['entry'][0]if o else'','old_entry_z':o['entry'][1]if o else'','entry_width_m':s['door_width_m'],'old_48':s['id']in old48,'work_module_contained':s['work_rectangle'].difference(stock.buffer(-.12)).area<1e-5,'staff_door_width_m':s.get('back_door_width_m',1.5),'stock_public_wall_m':gap_to_public,'acute_corners_under_30deg':acute,'human_playtest':False})
  if acute:bounds.append({'id':s['id'],'acute_corners':acute,'assessment':'rear/frontage boundary inspect in detailed plan; no architectural PASS from geometry alone'})
 oldassigned=unary_union([b['public'],b['void'],b['shafts'],b.get('egress',Polygon()),*[q['outline']for q in b['cores']],*[s['polygon']for s in b['stores']],*[q['polygon']for q in b['service_zones']]])
 un=b['floor_plate'].difference(oldassigned)
 summary.append({'floor':f['label'],'old_unassigned_m2':un.area,'old_unassigned_components':len(polys(un)),'new_unassigned_m2':floor.difference(covered).area,'old_floor_m2':b['floor_plate'].area,'new_floor_m2':floor.area,'old_shop_count':len(b['stores']),'new_shop_count':len(ss),'old_shop_m2':sum(q['polygon'].area for q in b['stores']),'new_shop_m2':plots.area,'old_service_m2':sum(q['polygon'].area for q in b['service_zones']),'new_service_m2':sum(q['polygon'].area for q in f['service_zones']),'atrium_changed_m2':f['void'].symmetric_difference(b['void']).area})
# Source roof/basement were deliberately not overwritten: calculate consequences, never claim all15levels are updated.
site=read((Path(__file__).resolve().parents[1]/'source/master-site-v3.json'));rf=next(f for f in site['floors']if f['wing']=='B'and f['label']=='RF');basement=next(f for f in site['floors']if f['wing']=='B'and f['label']=='B1');top=D['floors'][2];support=top['building_envelope_v5'];parking=[]
for stall in rf['parking']['stalls']:
 lost=stall['polygon'].difference(support).area
 if lost>.01:parking.append({'id':stall['id'],'outside_revised_upper_envelope_m2':lost,'action':'roof structural span/support and stall disposition need separate design approval; not deleted'})
roof={'old_B_RF_stalls':len(rf['parking']['stalls']),'stalls_outside_new_upper_envelope':len(parking),'affected_stall_ids':[q['id']for q in parking],'original_roof_floor_outside_proposed_support_envelope_m2':rf['floor_plate'].difference(support).area,'basement_projection_outside_revised_1F_m2':basement['floor_plate'].difference(D['floors'][0]['building_envelope_v5']).area,'roof_basement_modified':False,'structural_load_path_verified':False,'site_6699_capacity_revalidated':False}
write(S/'roof-basement-impact.json',roof);csvout('roof-parking-impact.csv',parking);csvout('all-198-store-ledger.csv',led);csvout('floor-comparison.csv',summary);csvout('boundary-design-review.csv',bounds);write(S/'design-v5.json',D)
# Verify every old component has a traced physical action; retain even tiny entries.
inventory=read(S/'unowned-full-inventory.json');ck('all previous unowned components fully traced',max(abs(q['unaccounted_m2'])for q in inventory),1e-5)
paths=read(S/'shop-paths-v5.json');ck('shop routes missing',198-len(paths['routes']),0,'count');ck('shop planned route failures',len(paths['failures']),0,'count')
ck('backroom privacy glazing forbidden overlap',sum(s['backroom'].intersection(s['sales'].boundary.intersection(f['public'].buffer(.006)).buffer(.018).difference(s['backroom'].buffer(.03))).area for f in D['floors']for s in f['stores']))
report={'scope':'B1F-3F standalone only','source_v4_frozen':True,'checks':checks,'passed':sum(q['pass']for q in checks),'failed':sum(not q['pass']for q in checks),'summary':summary,'unowned_before_components':len(inventory),'unowned_before_total_m2':sum(q['old_area_m2']for q in inventory),'old_48_work_module_pass':sum(q['old_48']and q['work_module_contained']for q in led),'architecture_naturalness_approved':False,'acute_boundary_review':bounds,'roof_basement_impact':roof,'methods':'Exact polygon recomputation, tolerance1e-5sqm; consistent net sales after .12m outer/.10m partition; .44m-radius route planning separate from Godot physics. Work modules are game design assumptions, not legal/sales capacity certification.'}
write(P/'evidence/geometric-results.json',report);print('GEOMETRY',report['passed'],report['failed'],'old48',report['old_48_work_module_pass'],'unowned',report['unowned_before_total_m2'],'components',len(inventory),'acute',len(bounds));print('FAILURES',[q for q in checks if not q['pass']]);print('ROOF',roof)
