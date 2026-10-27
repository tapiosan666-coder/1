from pathlib import Path
import sys,math,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent));from site_v2_common import *
P=Path(__file__).resolve().parents[1];A=read(P/'source/annex-v6.json');site=read(P/'source/master-site-v3.json');road=A['roof']['parking']['vehicle_aisles'].union(site['site']['roof_car_bridge']['polygon']);cx=-547.75;cz=69.75;R=9.5;poses=[]
for x in np.arange(-572,cx,.1):poses.append((x,cz-R,1.,0.))
for th in np.arange(-math.pi/2,0,.1/R):poses.append((cx+R*math.cos(th),cz+R*math.sin(th),-math.sin(th),math.cos(th)))
for z in np.arange(cz,160,.1):poses.append((cx+R,z,0.,1.))
swept=unary_union([rect((x+ux*1.4,z+uz*1.4),(ux,uz),4.8,1.85)for x,z,ux,uz in poses]);old=read(P/'source/vehicle-sweep-v6.json');arrival=old['results'][0]['swept'];result={'id':'RF-OPPOSITE-LANE-RETURN','radius_m':R,'wheelbase_m':2.7,'body_m':[4.8,1.85],'sample_step_m':.1,'poses':len(poses),'road_departure_m2':swept.difference(road).area,'opposing_sweeps_overlap_m2':swept.intersection(arrival).area,'opposing_sweeps_separation_m':swept.distance(arrival),'swept':swept,'planar_sweep_pass':swept.difference(road).area<1e-5,'dynamic_or_human_driving':False,'all_other_rows_and_parking_structure_ramps_tested':False};write(P/'source/opposite-lane-sweep-v6.json',result);print({k:v for k,v in result.items()if k!='swept'})
