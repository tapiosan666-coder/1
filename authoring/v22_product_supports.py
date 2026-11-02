from pathlib import Path
import json,math,collections,sys,numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import read,write,Polygon,Point,unary_union
p=read(P/'source/v22/retail-plan.json');B=read(P/'source/v21/model-bounds.json');B.update(read(P/'source/v22/model-bounds.json'));hosts={r['id']:r for r in p['fixtures']};changes=[]
levels={'fixture_table':[.8075],'fixture_produce_bin':[.925],'fixture_library_bay':[.3475,.8075,1.2675,1.7275],'fixture_wall_bay':[.3475,.8075,1.2675,1.7275],'fixture_cold_case':[.3475,.8075,1.2675,1.7275],'fixture_low_island':[.3775,.8275],'fixture_beauty_island':[.9475],'fixture_beauty_counter':[.8075],'fixture_beauty_wall':[.3475,.8075,1.2675,1.7275],'fixture_electronics_counter':[.8075],'fixture_electronics_wall':[.8075],'fixture_shoe_table':[.7775,1.045],'fixture_small_presentation':[.78],'fixture_narrow_wall':[.3175,.7975,1.2575,1.7175],'fixture_sport_wall':[.4725,1.1225,1.7725],'fixture_cafe_table':[.770]}
kept=[];perhost=collections.defaultdict(list)
for r in p['products']:perhost[r['host']].append(r)
for host_id,items in perhost.items():
 h=hosts[host_id];model=h['model'];n=np.array(h['n']);u=np.array([n[1],-n[0]])
 if not host_id.startswith('V22'):kept+=items;continue
 if model=='fixture_cafe_table':
  for j,r in enumerate(items[:2]):
   b=B[r['model']];q=np.array([h['p'][0],h['p'][2]])+u*(-.20 if j==0 else .20);r['p']=[float(q[0]),h['p'][1]+.773-b['min'][1],float(q[1])];kept.append(r)
  changes.append({'host':host_id,'correction':'Circular cafe tabletop: two supported services, not a full-width shelving row','removed_excess':max(0,len(items)-2)});continue
 if any(r['model']=='sku_guitar'for r in items)and model=='fixture_wall_bay':
  # A floor/low-table instrument display, not four tiers of guitars crossing shelves.
  h['model']='fixture_table';h['asset']='../v21/models/fixture_table';model='fixture_table';items=items[:1];changes.append({'host':host_id,'correction':'Instrument showroom single-height stand/table; no stacked full-size guitars'})
 for r in items:
  if model not in levels:kept.append(r);continue
  b=B[r['model']];angle=math.radians(r.get('pitch_deg',0));bottom=min(math.cos(angle)*y-math.sin(angle)*z for y in[b['min'][1],b['max'][1]]for z in[b['min'][2],b['max'][2]]);current=r['p'][1]-h['p'][1]+bottom;target=min(levels[model],key=lambda y:abs(y-current));r['p'][1]=h['p'][1]+target+.003-bottom
  if model=='fixture_shoe_table'and target>1.0:
   q=np.array([r['p'][0],r['p'][2]])-n*.19;r['p'][0]=float(q[0]);r['p'][2]=float(q[1])
  kept.append(r)
p['products']=kept;p['instances']=p['fixtures']+kept
for s in p['stores']:s['sku_count']=sum(r['store_id']==s['id']for r in kept)
write(P/'source/v22/retail-plan.json',p);write(P/'source/v22/product-support-design.json',{'target_shelf_heights_local_m':levels,'special_fixes':changes,'actual_Godot_physics_verified':False});print('PRODUCT_SUPPORT_DESIGN',len(kept),'products',len(changes),'special host corrections')
