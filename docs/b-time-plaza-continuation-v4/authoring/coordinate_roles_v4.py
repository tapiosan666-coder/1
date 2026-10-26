"""Typed, idempotent point transform for the fixed legacy B revision. Never translates directions or dimensions."""
from shapely.geometry import Point
SHIFT=(-714.,-30.)
def pt(p):return[p[0]+SHIFT[0],p[1]+SHIFT[1]]
def correct_service(z):
 if z.get('point_coordinate_frame')=='world_xz':
  if Point(z['entry']).distance(z['polygon'].boundary)>.01:raise ValueError('Declared world entry does not match service boundary: '+z['id'])
  return z
 candidate=pt(z['entry'])
 if Point(candidate).distance(z['polygon'].boundary)>.01 or Point(z['entry']).distance(z['polygon'])<100:raise ValueError('Legacy entry frame mismatch; do not guess or apply another transform: '+z['id'])
 z['entry']=candidate;z['main_route']=[pt(p)for p in z.get('main_route',[])];z['point_coordinate_frame']='world_xz';z['point_transform_from']='legacy_B_local_xz';return z
