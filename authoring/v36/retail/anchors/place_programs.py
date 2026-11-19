from pathlib import Path
import json,math,subprocess,sys
from collections import Counter,defaultdict
from shapely.geometry import shape,Point,LineString,Polygon,box,mapping
from shapely.ops import unary_union
from shapely.affinity import rotate,translate
from shapely.prepared import prep
project,route_file,target=map(Path,sys.argv[1:4])
def get(f):
    b=(project/f).read_bytes()
    if b[:4]==b'FYJZ':b=subprocess.check_output(['zstd','-dc'],input=b[8:])
    return json.loads(b)
def line(pts):return LineString([(v[0],v[-1]) for v in pts])
def poly(shape_):return shape(shape_).buffer(0)
def rect(x,z,w,d,yaw,clear=.0):return translate(rotate(box(-w*.5-clear,-d*.5-clear,w*.5+clear,d*.5+clear),-math.degrees(yaw)),x,z)
plan=get('source/v294/retail-plan.json.zst'); fixtures=plan['fixtures']; sales=get('source/v32/sales-design.json')['stores']
v36={a['id']:a for a in get('source/v36/store-studios.json')}
npcs=get('source/v19/shoppers.json')['people']
qa=json.loads(route_file.read_bytes())
rooms={'AB1-001':('market_produce','market_deli'),'A2F-001':('fashion_lookbook','fashion_atelier'),'A3F-001':('cinema_box_office','cinema_lounge')}
result=[]
for sid,(first,center) in rooms.items():
 s=next(s for s in plan['stores'] if s['id']==sid)
 area=poly(s['sales_world']); pt=Point(s['entry_world']);y=s['height']
 forbidden=[poly(s['protected_aisles_world']).buffer(.25)]
 if s.get('backroom_world'):forbidden.append(poly(s['backroom_world']).buffer(.75))
 forbidden.append(pt.buffer(2.85))
 if len(s.get('main_route_world',[]))>=2:forbidden.append(line(s['main_route_world']).buffer(.89))
 for obj in fixtures:
    if obj.get('store_id')==sid and obj.get('footprint'):forbidden.append(poly(obj['footprint']).buffer(.62))
 for obj in sales:
    if obj['id']!=sid:continue
    forbidden.append(poly(obj['protected']).buffer(.35))
    forbidden.extend(poly(f['footprint']).buffer(.58) for f in obj['placements'])
 for obj in qa+get('source/v21/store-walk-routes.json'):
    if obj.get('store_id',obj.get('id'))==sid and len(obj.get('points',[]))>=2:forbidden.append(line(obj['points']).buffer(.90))
 for n in npcs:
    if n.get('wing')==s['wing'] and n.get('floor')==s['floor']:
        for key in ('p','seat_point','home_point','stand_point'):
            if n.get(key):forbidden.append(Point(n[key][0],n[key][-1]).buffer(1.1))
        for key in ('path','route'):
            if isinstance(n.get(key),list) and len(n[key])>=2:forbidden.append(line(n[key]).buffer(1.1))
 for b in v36[sid]['placements']:forbidden.append(rect(b['p'][0],b['p'][2],b['width'],.75,b['yaw'],.64))
 limit=area.buffer(-.8).difference(unary_union(forbidden));allowed=prep(limit)
 axis=[area.representative_point().x-pt.x,area.representative_point().y-pt.y];l=math.hypot(*axis);ax,az=[v/l for v in axis];tx,tz=az,-ax
 print(sid,round(area.area,1),area.bounds,'entry',pt,'aisle',s['main_route_world'][:3], 'rep',area.representative_point().wkt)
 bays=[]
 for role,name,dist in [('entrance',first,10.8),('middle',center,30.)]:
    options=[]
    min_x,min_z,max_x,max_z=limit.bounds
    rear=s['main_route_world'][1]
    front_dir=[rear[0]-pt.x,rear[-1]-pt.y]
    front_dist=math.hypot(*front_dir)
    front_dir=[v/front_dist for v in front_dir]
    for x in range(math.ceil(min_x),math.floor(max_x)+1,2):
      for z in range(math.ceil(min_z),math.floor(max_z)+1,2):
       dd=math.hypot(x-pt.x,z-pt.y)
       if dd>80. or dd<5.:continue
       along=(x-pt.x)*front_dir[0]+(z-pt.y)*front_dir[1]
       lateral=(z-pt.y)*front_dir[0]-(x-pt.x)*front_dir[1]
       phi=math.atan2(pt.x-x,pt.y-z)
       for ang in [phi,round(phi/(math.pi/2))*math.pi/2,round((phi+math.pi/4)/(math.pi/2))*math.pi/2-math.pi/4]:
        foot=rect(x,z,6.8,4.3,ang,.35)
        if not allowed.covers(foot):continue
        # Preserve customer access on the entire front, plus one lateral route.
        front=translate(foot,math.sin(ang)*1.18,math.cos(ang)*1.18)
        if not allowed.covers(front):continue
        score=abs(dd-dist)*1.65+max(0.,-along)*2.2+abs(lateral)*(.4 if role=='entrance' else .14)
        if role=='middle' and bays and math.hypot(x-bays[0]['p'][0],z-bays[0]['p'][2])<12.:continue
        options.append((score,x,z,ang))
    picked=[]
    for score,x,z,ang in sorted(options):
       if any(math.hypot(x-a['p'][0],z-a['p'][2])<3.6 for a in picked):continue
       picked.append(dict(role=role,program=name,p=[round(x,3),y,round(z,3)],yaw=round(ang,5),width=6.8,depth=4.3,
                          distance=round(math.hypot(x-pt.x,z-pt.y),3)))
       if len(picked)==7:break
    print(role,len(options),picked[:2]);bays+=picked
 result.append(dict(id=sid,wing='A',floor=s['floor'],placements=bays))
target.write_text(json.dumps(result,indent=2))
