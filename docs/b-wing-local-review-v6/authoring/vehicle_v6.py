"""Planar rigid-body swept-envelope samples at 0.10m, not Godot vehicle physics or a real driving test."""
from pathlib import Path
import sys,math,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent));from site_v2_common import *
P=Path(__file__).resolve().parents[1];site=read(P/'source/master-site-v3.json');rf=next(f for f in site['floors']if f['wing']=='B'and f['label']=='RF');road=rf['parking']['vehicle_aisles'].union(site['site']['roof_car_bridge']['polygon']);stalls=unary_union([q['polygon']for q in rf['parking']['stalls']]);ped=rf['parking']['protected_pedestrian'];results=[];flare=Polygon()
# A real roof-car-bridge to RF-ROW-04 approach. Japan-style left lane; opposite travel also checked.
xx=-541.75;zz=63.75;radius=6;centre=(xx-radius,zz+radius);poses=[]
for z in np.arange(160,centre[1],-.1):poses.append((xx,z,0.,-1.))
for th in np.arange(0,-math.pi/2,-.1/radius):
 x=centre[0]+radius*math.cos(th);z=centre[1]+radius*math.sin(th);poses.append((x,z,math.sin(th),-math.cos(th)))
for x in np.arange(centre[0],-572,-.1):poses.append((x,zz,-1.,0.))
for reverse in[False,True]:
 shapes=[]
 for x,z,ux,uz in poses:
  if reverse:ux,uz=-ux,-uz
  shapes.append(rect((x+ux*1.4,z+uz*1.4),(ux,uz),4.8,1.85))
 swept=unary_union(shapes);missing=swept.difference(road);protected=missing.intersection(stalls.union(ped));can_fix=protected.area<1e-5
 if can_fix:flare=flare.union(missing.buffer(.15,join_style=2))
 results.append({'id':'RF-BRIDGE-ROW04-'+('RETURN'if reverse else'ARRIVAL'),'sample_poses':len(poses),'rear_axle_turn_radius_m':6,'wheelbase_m':2.7,'body_dimensions_m':[4.8,1.85],'step_m':.1,'maximum_steering_deg':math.degrees(math.atan(2.7/6)),'old_road_departure_m2':missing.area,'conflict_with_stalls_or_protected_ped_m2':protected.area,'local_flare_possible':can_fix,'swept':swept,'method':'analytic constant-curvature bicycle geometry + oriented body sweep, not a dynamic vehicle / ramp / traffic simulation'})
# Flare can use only previous equipment roof, never a stall or protected pedestrian strip.
flare=flare.difference(stalls.union(ped));newroad=road.union(flare)
for q in results:q['revised_road_departure_m2']=q['swept'].difference(newroad).area;q['planar_sweep_pass']=q['revised_road_departure_m2']<1e-5
write(P/'source/vehicle-sweep-v6.json',{'results':results,'new_road_flare':flare,'new_roof_vehicle_aisles':rf['parking']['vehicle_aisles'].union(flare),'vehicle_physics_tested':False,'all_parking_rows_swept':False,'parking_structure_ramps_swept':False,'road_width_source_m':6.5,'roof_bridge_width_m':7,'other_curves_and_ramps':'not tested; no global vehicle-system PASS'});print('VEHICLE',[(q['id'],q['old_road_departure_m2'],q['conflict_with_stalls_or_protected_ped_m2'],q['planar_sweep_pass'])for q in results],'flare',flare.area)
