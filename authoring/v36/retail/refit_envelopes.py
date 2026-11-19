from pathlib import Path
import struct, json, sys
import numpy as np
root=Path(__file__).resolve().parents[3]
raw=Path(sys.argv[1])
evidence=Path(sys.argv[2])
def read(path):return json.loads((root/path).read_bytes())
sizes={}
for path in sorted(raw.glob('*.bin')):
    data=path.read_bytes();off=0;mins=np.full(3,np.inf);maxs=-mins
    for section in range(5):
        n=struct.unpack_from('<I',data,off)[0];off+=4
        if n:
            coords=np.frombuffer(data,dtype='<f4',offset=off,count=n*9).reshape(n,9)[:,:3]
            mins=np.minimum(mins,coords.min(axis=0));maxs=np.maximum(maxs,coords.max(axis=0))
        off+=36*n
    sizes[path.stem]=(mins,maxs)
fixtures={f['id']:f for store in read('source/v32/sales-design.json')['stores'] for f in store['placements']}
refits=read('source/v36/store-refits.json');bad=[];over_height=[]
for id, new in refits.items():
    bounds=fixtures[id]['bounds']
    floor=np.asarray(bounds['p']);limit=floor+bounds['size']
    mn,mx=sizes[new['mesh']]
    if '--fit-refits' in sys.argv:
        new['scale'][1] = min(new['scale'][1],(limit[1]-.001-new['offset'][1])/mx[1])
    mn=mn*new['scale']+new['offset'];mx=mx*new['scale']+new['offset']
    if ((mn < floor-.001)|(mx>limit+.001))[[0,2]].any(): bad.append(id)
    if mx[1]>limit[1]+.03: over_height.append([id,round(float(mx[1]-limit[1]),3)])
if '--fit-refits' in sys.argv:
    (root/'source/v36/store-refits.json').write_text(json.dumps(refits,ensure_ascii=False,separators=(',',':'))+'\n')
open_cases=[k for k in sizes if 'dining' not in k]
print('prototypes',len(open_cases),'horizontal-outside',[(k,x.tolist(),y.tolist()) for k in open_cases for x,y in [sizes[k]] if np.any(x[[0,2]]<[-1.291,-.371]) or np.any(y[[0,2]]>[1.291,.371])])
print('refits',len(refits),'bad footprint',bad,'above original',over_height)
evidence.write_text(json.dumps({'tested':len(refits),'xz_out_of_legacy_envelope':bad,'above_prior_fixture_top_m':over_height,'method':'Transformed rendered vertex extents after final silhouette revision against old fixture-local envelope. Vertical changes may include separately supported signs.'}))
