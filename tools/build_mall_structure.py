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
    base=unary_union([concourse,loop.buffer(b['loop_width']/2,quad_segs=8,join_style='round'),rect(b['anchor']),rect(b['court'])]+[store_shape(s) for s in b['stores']])
    # Public cross-passages make the inner stores actual islands in the circulation network.
    for path in b['cross_paths']:base=base.union(LineString(path).buffer(4,quad_segs=8))
    public=unary_union([concourse,loop.buffer(b['loop_width']/2,quad_segs=8)]+[LineString(path).buffer(4,quad_segs=8) for path in b['cross_paths']])
    from shapely.ops import nearest_points
    for st in b['stores']:
        x,w,side=st['legacy'];front=move(Point(0,side*9.2),st['placement']);target=nearest_points(front,public)[1]
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
    walls=[];floor=[];rails=[]
    for level in range(3):
        shell=base
        if level==0:shell=shell.union(LineString(b['c_access']).buffer(4,quad_segs=4,cap_style='flat'))
        f=shell if level==0 else shell.difference(void).union(bridges.intersection(shell)).union(court_upper)
        if level==1:f=f.difference(box(-332.2,54,-329.8,66))
        if level==2:f=f.difference(box(-317.7,54,-315.3,66))
        f=f.union(rect(b['ground_link'] if level==0 else b['sky_link'])) if level<2 else f
        assert len(polys(f))==1, 'B floor must be connected'
        floor.append(floor_data(f))
        rail=f.boundary.difference(shell.boundary.buffer(.10))
        if level==1:rail=rail.difference(unary_union([box(-332.4,65.8,-329.6,66.2),box(-317.9,65.8,-315.1,66.2)]))
        if level==2:rail=rail.difference(box(-317.9,53.8,-315.1,54.8))
        rails.append([list(line.coords) for line in (list(rail.geoms) if hasattr(rail,'geoms') else [rail]) if line.geom_type=='LineString'])
        wall=shell.boundary.difference(wall_cut)
        # Upper openings have physical guardrails; service courtyards are enclosed by the shell walls.
        walls.append([list(line.coords) for line in (list(wall.geoms) if hasattr(wall,'geoms') else [wall])])
    d['B']={'floors':floor,'walls':walls,'rails':rails,'voids':packet(void.difference(bridges).difference(court_upper)),'roof':floor_data(base.difference(box(-496,-26,-466,26))),'ground_roof':floor_data(LineString(b['c_access']).buffer(4,quad_segs=4,cap_style='flat').difference(base)),'stores':b['stores'],'plazas':b['plazas'],'main':b['main'],'loop':b['loop'],'c_access':b['c_access']}
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
    d['C']={'floors':[floor_data(cf)],'stores':c['stores'],'plazas':c['plazas']}
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
