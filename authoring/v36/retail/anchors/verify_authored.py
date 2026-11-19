from pathlib import Path
import json,subprocess,sys,math,struct
from collections import Counter
from shapely.geometry import shape,LineString,Point,box
from shapely.affinity import rotate,translate
from shapely.ops import unary_union

def main():
    project,raw,routes_path,out=map(Path,sys.argv[1:5])
    b=(project/'source/v294/retail-plan.json.zst').read_bytes()
    stores={s['id']:s for s in json.loads(subprocess.check_output(['zstd','-dc'],input=b[8:]))['stores']}
    data=json.loads((project/'source/v36/anchor-programs.json').read_bytes())
    people=json.loads((project/'source/v19/shoppers.json').read_bytes())['people']
    routes={s['id']:s for s in json.loads(routes_path.read_bytes())}
    result=[]
    for r in data['rooms']:
        source=stores[r['id']];area=shape(source['sales_world']).buffer(0);report=routes[r['id']]
        paths=[LineString(report[k]) for k in ['entrance_path','department_path']]
        claimed=unary_union(paths)
        width={'AB1-001':.965,'A2F-001':1.06,'A3F-001':1.14}[r['id']]
        # A conservative envelope includes the entire untrimmed carpet outline.
        carpet=claimed.buffer(width,quad_segs=10)
        rr={'id':r['id'],'area_m2':round(area.area,3),'brand':source['brand'],'floor':r['floor'],
            'floor_finish_outside_sales_m2':round(carpet.difference(area).area,6),
            'minimum_sales_boundary_clearance_m':round(carpet.distance(area.boundary),3),
            'npc_count_same_wing_and_floor':sum(n['wing']==r['wing'] and n['floor']==r['floor'] for n in people),'mesh_checks':[]}
        for set in r['placements']:
            key=set['program'];data_bytes=(raw/('room-'+key+'.bin')).read_bytes()
            pos=0;low=[float('inf')]*3;hi=[float('-inf')]*3;tris=0
            for k in range(5):
                n=struct.unpack_from('<I',data_bytes,pos)[0];pos+=4;tris+=n//3
                for i in range(n):
                    vert=struct.unpack_from('<3f',data_bytes,pos+36*i)
                    for h in range(3):low[h]=min(low[h],vert[h]);hi[h]=max(hi[h],vert[h])
                pos+=n*36
            assert pos==len(data_bytes)
            mesh={'program':key,'triangles':tris,'aabb_min':[round(x,5) for x in low],'aabb_max':[round(x,5) for x in hi]}
            if 'width' in set:
                a=rotate(box(-3.40,-2.15,3.40,2.15),-math.degrees(set['yaw']),origin=(0,0));a=translate(a,set['p'][0],set['p'][2])
                mesh['within_verified_site']=min(low[0],-hi[0])>=-3.4 and min(low[2],-hi[2])>=-2.15 and low[1]>=-.001 and hi[1]<=2.90
                mesh['entire_site_within_sales']=area.covers(a)
                assert mesh['within_verified_site'] and mesh['entire_site_within_sales'],mesh
            assert rr['floor_finish_outside_sales_m2']==0
            rr['mesh_checks'].append(mesh)
        result.append(rr)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
