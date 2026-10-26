"""Read current source/static export for legacy A/C references; never run Godot."""
from pathlib import Path
import re,json,math,hashlib
R=Path(__file__).resolve().parents[1];O=R/'docs/ac-detailed-design-v1';O.mkdir(exist_ok=True)
def world(x,y,z):
 if x>-35:
  angle=(x+35)/130;qx=-35+(130-z)*math.sin(angle);qz=130-(130-z)*math.cos(angle)
 else:qx,qz=x,z
 expansion=1+.2*max(0,min(1,(qx+190)/100))
 return[qx,y,qz*expansion]
legacy=[]
for i in range(7):
 p=[-75+i*18,-5.35,-17];legacy.append({'id':f'a_basement_{i}','wing':'A','level':-1,'kind':'food-counter','basis':'retail_density.gd Transform3D origin; not a portal coordinate','old_logical_xyz':p,'old_world_xyz_source_derived':world(*p)})
for i in range(4):
 p=[51+i*11,0,-59.5];legacy.append({'id':f'a_food_{i}','wing':'A','level':0,'kind':'food-counter','basis':'retail_density.gd Transform3D origin; not a portal coordinate','old_logical_xyz':p,'old_world_xyz_source_derived':world(*p)})
s=(R/'scripts/store_sign_catalog.gd').read_text();d=json.loads(s.split('const DATA :=',1)[1])
for board in d['additional_boards']:
 if board['id']in['a_market_rear','a_reading']:
  p=board['at'];legacy.append({'id':board['id'],'wing':'A','level':0,'kind':'auxiliary-sign-not-store','parent_legacy_id':board.get('outlet'),'basis':'store_sign_catalog.gd board centre including sign height, not store entrance','old_logical_xyz':p,'old_world_xyz_source_derived':world(*p)})
s=(R/'scripts/mall.gd').read_text();hubblock=s.split('const HUBS :=',1)[1].split('\n',1)[0];points={key:[float(n)for n in xyz.split(',')]for key,xyz in re.findall(r'"([^"]+)":\s*Vector3\(([^)]+)\)',hubblock)}
s=(R/'scripts/mall_layout.gd').read_text().split('const HUBS :=',1)[1].split('static var',1)[0];hubs=[]
for id,label,floor in re.findall(r'\["([^"]+)",\s*"([^"]+)",\s*"([^"]+)"\]',s):
 p=points[label];hubs.append({'id':id,'legacy_visited_key':label,'old_floor_id':floor,'old_logical_xyz':p,'old_world_xyz_source_derived':world(*p),'basis':'Mall.HUBS through MallCurve.world; static source-derived landing reference, runtime untested'})
for name,value in[('legacy-additional-a-ids.json',legacy),('legacy-travel-hubs.json',hubs)]:
 (O/name).write_text(json.dumps(value,ensure_ascii=False,indent=2))
(O/'legacy-source-provenance.json').write_text(json.dumps({'source_commit':'9dd0b1a712340118586c266f1c8c172bf64edea1','runtime_executed':False,'world_conversion':'Exact formula port of MallCurve.world/raw_world/expansion in Python double arithmetic; not mesh vertices or measured runtime positions','files':{p:hashlib.sha256((R/p).read_bytes()).hexdigest()for p in['scripts/retail_density.gd','scripts/mall_curve.gd','scripts/mall.gd','scripts/mall_layout.gd','scripts/store_sign_catalog.gd','docs/map-master-floor-plans.json']}},ensure_ascii=False,indent=2));print('Additional A references',len(legacy),'Travel hubs',len(hubs))
