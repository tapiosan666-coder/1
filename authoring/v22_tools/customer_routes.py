from pathlib import Path
import sys,numpy as np
P=Path(__file__).resolve().parents[2];sys.path.insert(0,str(P/'authoring'));from site_v2_common import *
p=read(P/'source/v22/retail-plan.json');changes=[]
for s in p['stores']:
 original=s.get('delivery_reference_route_world',s['main_route_world']);s['delivery_reference_route_world']=original;line=LineString([(r[0],r[2])for r in original]);sales=s['sales_world'].buffer(-.48);parts=lines(line.intersection(sales))
 if not parts:changes.append({'id':s['id'],'unresolved':'No original aisle segment inside sales'});continue
 e=Point(*s['entry_world']);part=min(parts,key=lambda a:a.distance(e));coords=list(part.coords)
 if Point(coords[-1]).distance(e)<Point(coords[0]).distance(e):coords.reverse()
 # The inherited main_route is a delivery route terminating INSIDE the locked stock room.
 # Customer destination is the last supported point of its sales-only segment, not the staff room.
 target=coords[-1];new=[[s['entry_world'][0],s['height'],s['entry_world'][1]]]+[[x,s['height'],z]for x,z in coords];s['main_route_world']=new;s['customer_route_scope']='Entry to end of first contiguous sales-only delivery-spine segment, 0.48m from plot/backroom walls. Not the locked staff-room endpoint.';changes.append({'id':s['id'],'old_endpoint':original[-1],'new_endpoint':new[-1],'retail_geometry_changed':False})
write(P/'source/v22/retail-plan.json',p);write(P/'source/v22/customer-route-semantics.json',{'corrections':changes,'source_plot_changed':False,'reason':'Inherited main_route is explicitly used for after-hours delivery and ends in stock rooms. Do not test customer access to a locked staff endpoint as a missing retail route.'});print('CUSTOMER_ROUTES',len(changes))
