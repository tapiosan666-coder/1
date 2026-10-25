#!/usr/bin/env python3
"""Compile authored mall polygons/holes to Godot data. Requires Shapely 2.1; not needed to play."""
from pathlib import Path
import json, math, hashlib, argparse
from shapely import constrained_delaunay_triangles
from shapely.geometry import Polygon, LineString, Point, box
from shapely.affinity import scale, affine_transform
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'assets/layout/mall_structure.json'
OUT=ROOT/'scripts/mall_structure_data.gd'
def polys(g):
    return [g] if g.geom_type=='Polygon' else [p for p in g.geoms if p.geom_type=='Polygon']
def coords(r):return [[round(x,5),round(y,5)] for x,y in list(r.coords)[:-1]]
def packet(g):
    return [{'outer':coords(p.exterior),'holes':[coords(r) for r in p.interiors]} for p in polys(g)]
def ellipse(at,r):return scale(Point(at).buffer(1,quad_segs=16),*r,origin=tuple(at))
def rect(r):return box(r[0],r[1],r[0]+r[2],r[1]+r[3])
def move(g,t):
    x,z,yaw=t;a=math.cos(yaw);b=math.sin(yaw)
    return affine_transform(g,[a,b,-b,a,x,z])
def store_shape(s):
    if "footprint" in s:return move(rect(s["footprint"]),s["placement"])
    x,w,side=s['legacy'];t=s['placement']
    return move(box(-w/2,-26 if side<0 else 8,w/2,-8 if side<0 else 26),t)
def floor_data(g):
    assert g.is_valid
    triangles=[]
    for t in constrained_delaunay_triangles(g).geoms:
        c=coords(t.exterior)
        area=sum(c[i][0]*c[(i+1)%3][1]-c[(i+1)%3][0]*c[i][1] for i in range(3))
        triangles.append(c if area>0 else c[::-1])
    error=abs(sum(Polygon(t).area for t in triangles)-g.area)
    assert error<.01,(error,g.area)
    return {'polygons':packet(g),'triangles':triangles,'area':round(g.area,3),'bounds':list(g.bounds)}
def curve(points):
    pts=[tuple(p) for p in points]
    for _ in range(2):
        result=[pts[0]]
        for a,b in zip(pts,pts[1:]):
            result.extend([(a[0]*.75+b[0]*.25,a[1]*.75+b[1]*.25),(a[0]*.25+b[0]*.75,a[1]*.25+b[1]*.75)])
        result.append(pts[-1]);pts=result
    return LineString(pts)
def compile_plan(source):
    d={};b=source['B'];main=LineString(b['main']);loop=curve(b['loop'])
    concourse=main.buffer(b['main_width']/2,quad_segs=8,join_style='round')
    for p in b['plazas']:concourse=concourse.union(ellipse(p['at'],p['radius']))
    base=unary_union([concourse,loop.buffer(b['loop_width']/2,quad_segs=8,join_style='round'),rect(b['anchor']),rect(b['court'])]+[store_shape(s) for s in b['stores']+b['rear_stores']])
    # Public cross-passages make the inner stores actual islands in the circulation network.
    for path in b['cross_paths']:base=base.union(LineString(path).buffer(4,quad_segs=8))
    public=unary_union([concourse,loop.buffer(b['loop_width']/2,quad_segs=8)]+[LineString(path).buffer(4,quad_segs=8) for path in b['cross_paths']])
    from shapely.ops import nearest_points
    for st in b['stores']:
        x,w,side=st['legacy'];front=move(Point(0,side*9.2),st['placement']);target=nearest_points(front,public)[1]
        base=base.union(LineString([front,target]).buffer(3.5,quad_segs=4))
    for st in b['rear_stores']:
        front=Point(st['placement'][:2]);target=nearest_points(front,public)[1]
        base=base.union(LineString([front,target]).buffer(3.5,quad_segs=4))
    void=main.buffer((b['main_width']-2*b['gallery_width'])/2,quad_segs=8)
    # Keep foyer and anchor approach as solid upper-floor landings.
    void=void.intersection(box(-446,-100,-202,150))
    for p in b['plazas']:void=void.union(ellipse(p['at'],[r-b['gallery_width'] for r in p['radius']]))
    # Crossings at the transitions between courts, away from the main openings.
    bridges=unary_union([move(box(-2.5,-17,2.5,17),x) for x in b['bridges']])
    court_upper=unary_union([rect(r) for r in b['court_upper']])
    ports=[box(-201,-8.1,-169,-2.9),box(-374.2,-30,-365.8,-22)]
    wall_cut=unary_union(ports)
    rear_walls=unary_union([store_shape(st).buffer(.22) for st in b['rear_stores']])
    bank_public=[];shafts=[];north_ports=[];south_ports=[]
    for bank in b['escalator_banks']:
        cx,cz=bank['at'];side=bank['side'];lo=min(cx+side*11.5,cx+side*23);hi=max(cx+side*11.5,cx+side*23)
        bank_public.extend([box(lo,cz-9,hi,cz-6),box(lo,cz+6,hi,cz+9),box(cx+side*21.5-1.5,cz-9,cx+side*21.5+1.5,cz+9)])
        for offset in [13.5,16.5]:
            x=cx+side*offset;shafts.append(box(x-1.2,cz-6,x+1.2,cz+6))
            north_ports.append(box(x-1.4,cz-6.3,x+1.4,cz-5.7));south_ports.append(box(x-1.4,cz+5.7,x+1.4,cz+6.3))
    bank_public=unary_union(bank_public).intersection(base);shafts=unary_union(shafts)
    north_ports=unary_union(north_ports);south_ports=unary_union(south_ports)

    walls=[];floor=[];rails=[];b_geometries=[]
    for level in range(3):
        shell=base
        if level==0:shell=shell.union(LineString(b['c_access']).buffer(4,quad_segs=4,cap_style='flat'))
        f=shell if level==0 else shell.difference(void).union(bridges.intersection(shell)).union(court_upper)
        if level>0:f=f.union(bank_public).difference(shafts)
        f=f.union(rect(b['ground_link'] if level==0 else b['sky_link'])) if level<2 else f
        assert len(polys(f))==1, 'B floor must be connected'
        floor.append(floor_data(f));b_geometries.append(f)
        rail=f.boundary.difference(shell.boundary.buffer(.10))
        if level==1:rail=rail.difference(north_ports.union(south_ports))
        if level==2:rail=rail.difference(south_ports)
        rails.append([list(line.coords) for line in (list(rail.geoms) if hasattr(rail,'geoms') else [rail]) if line.geom_type=='LineString'])
        wall=shell.boundary.difference(wall_cut.union(rect(source['C']['upper']['bridge_port'])) if level==1 else wall_cut)
        wall=wall.difference(rear_walls)
        # Upper openings have physical guardrails; service courtyards are enclosed by the shell walls.
        walls.append([list(line.coords) for line in (list(wall.geoms) if hasattr(wall,'geoms') else [wall])])
    d['B']={'floors':floor,'walls':walls,'rails':rails,'voids':packet(void.difference(bridges).difference(court_upper).difference(bank_public).union(shafts.intersection(base))),'roof':floor_data(base.difference(box(-496,-26,-466,26))),'ground_roof':floor_data(LineString(b['c_access']).buffer(4,quad_segs=4,cap_style='flat').difference(base)),'stores':b['stores'],'rear_stores':b['rear_stores'],'escalator_banks':b['escalator_banks'],'plazas':b['plazas'],'main':b['main'],'loop':b['loop'],'c_access':b['c_access']}
    c=source['C']
    street=unary_union([curve(points).buffer(c['width']/2,quad_segs=8,join_style='round',cap_style='flat') for points in c['streets']]+[ellipse(p['at'],p['radius']) for p in c['plazas']])
    # Each entrance gets a short public approach; no detached shop floors.
    from shapely.ops import nearest_points
    approaches=[]
    for st in c['stores']:
        front=Point(st['placement'][:2]);target=nearest_points(front,street)[1]
        approaches.append(LineString([front,target]).buffer(3.5,quad_segs=4))
    cf=unary_union([street,rect([-374,-80,8,54])]+approaches+[store_shape(st) for st in c['stores']])
    assert len(polys(cf))==1,'C must be connected'
    upper=c['upper'];upper_plazas=[p for p in c['plazas'] if p['id'] in upper['plazas']]
    rings=[ellipse(p['at'],p['radius']) for p in upper_plazas]
    holes=unary_union([ellipse(p['at'],[v-upper['gallery_width'] for v in p['radius']]) for p in upper_plazas])
    upper_stores=[]
    for spec in upper['stores']:
        upper_stores.append(dict(c['stores'][spec['ground_index']],**spec))
    path=curve(upper['street']).buffer(upper['gallery_width']/2,quad_segs=8,cap_style='flat')
    upper_public=unary_union(rings+[path])
    upper_approaches=[]
    for st in upper_stores:
        front=Point(st['placement'][:2]);target=nearest_points(front,upper_public)[1]
        upper_approaches.append(LineString([front,target]).buffer(3.5,quad_segs=4))
    bridge=LineString(upper['bridge']).buffer(upper['bridge_width']/2,quad_segs=8,cap_style='flat')
    uf=unary_union([upper_public,bridge]+upper_approaches+[store_shape(st) for st in upper_stores]).difference(holes).difference(rect(upper['stair_shaft'])).difference(b_geometries[1])
    assert len(polys(uf))==1,'C upper floor must be connected'
    # Railings stop at the real B landing, storefront walls, and the upper stair landing.
    rail_cut=unary_union([b_geometries[1].buffer(.08),rect([-360.4,-91.1,1.5,4.2])]+[store_shape(st).buffer(.20) for st in upper_stores])
    rail=uf.boundary.difference(rail_cut)
    upper_rails=[list(line.coords) for line in (list(rail.geoms) if hasattr(rail,'geoms') else [rail]) if line.geom_type=='LineString']
    d['C']={'floors':[floor_data(cf),floor_data(uf)],'stores':c['stores'],'plazas':c['plazas'],'upper_stores':upper_stores,'upper_rails':upper_rails,'bridge':upper['bridge'],'stair_shaft':upper['stair_shaft'],'supports':upper['supports']}

    a=source['A'];ap=unary_union([rect(r) for r in a['rects']]+[ellipse(p['at'],p['radius']).intersection(box(-100,-100,100,-24)) for p in a['plazas']])
    av=ellipse(a['void']['at'],a['void']['radius'])
    existing_gallery=unary_union([rect([-48,-15,3,7]),rect([-33,-15,3,7]),rect([-48,-15,18,3])])
    af=[ap,ap.difference(av).difference(existing_gallery),ap.difference(av).difference(existing_gallery)]
    # Interface to A's existing north gallery remains open. Ground outer walls are rebuilt by Mall.
    ports=unary_union([box(-49,-9,-29,-7),box(59,-9,79,-7),box(45,-45,79,-23)])
    aw=ap.boundary.difference(ports)
    lines=[list(line.coords) for line in (list(aw.geoms) if hasattr(aw,'geoms') else [aw])]
    rails=[[],[list(av.exterior.coords)],[list(av.exterior.coords)]]
    d['A']={'floors':[floor_data(g) for g in af],'walls':[[],lines,lines],'rails':rails,'roof':floor_data(ap),'plazas':a['plazas'],'stores':a['stores'],'private':a['private']}
    return d

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    raw=SOURCE.read_bytes();source=json.loads(raw);d=compile_plan(source)
    result='class_name MallStructureData\nextends RefCounted\n## Generated by tools/build_mall_structure.py. Do not edit.\nconst SOURCE_SHA256 := '+json.dumps(hashlib.sha256(raw).hexdigest())+'\nconst DATA := '+json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n'
    if args.check:assert OUT.read_text()==result,'Regenerate mall structure data'
    else:OUT.write_text(result)
    print({k:{'area':[f['area'] for f in v['floors']],'triangles':[len(f['triangles']) for f in v['floors']]} for k,v in d.items()})
if __name__=='__main__':main()
