"""Do not count isolated unusable stock fragments as functional backrooms.
Returns them to the existing sales/display area, never takes sales for stock.
Only applies inside the independent 3D validation scope; original drawings remain frozen.
"""
from shapely.geometry import Point,Polygon
from shapely.ops import unary_union
from shapely import maximum_inscribed_circle

def parts(g):return[g]if g.geom_type=='Polygon'else[p for p in getattr(g,'geoms',[])if p.geom_type=='Polygon']
def normalize(s,crop,meta):
 if not s['polygon'].intersects(crop):return
 door=Point(s['back_door']);remove=[]
 for p in parts(s['backroom']):
  if p.distance(door)<.04:continue
  diameter=maximum_inscribed_circle(p,tolerance=.01).length*2
  if p.area<4 or diameter<1.2:
   remove.append(p);meta.setdefault('internal_role_revisions',[]).append({'id':s['id'],'old_role':'isolated stock fragment without its own door','new_role':'sales/display alcove, not a usable backroom','area_m2':p.area,'max_inscribed_diameter_m':diameter,'polygon':p,'basis':'Game planning target only, not a legal or industry minimum: isolated pieces <4sqm or <1.2m inscribed width are not counted as working stock rooms.','sales_area_reduced':False})
 if remove:
  change=unary_union(remove);s['backroom']=s['backroom'].difference(change);s['sales']=s['sales'].union(change);s['shelf_zones']=s['sales'].buffer(-.6).difference(s['aisles'].buffer(.2))
