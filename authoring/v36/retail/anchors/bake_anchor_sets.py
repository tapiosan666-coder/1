"""Compile the six independently furnished market, studio and cinema Anchor programmes."""
from pathlib import Path
import sys,json,math
here=Path(__file__).resolve().parent
def main():
    project,raw,planned,checked=map(Path,sys.argv[1:5])
    sys.path.insert(0,str(project/'authoring/v36/retail'))
    from market_fashion import Department
    from cinema import make_module
    from foyer_floors import assemble
    survey=json.loads(Path(sys.argv[5]).read_bytes());floor_reports=[]
    raw.mkdir(parents=True,exist_ok=True)
    candidates=json.loads(planned.read_bytes()); results=json.loads(checked.read_bytes())
    installed=[];models={}
    for row in candidates:
        stations=[]
        for role in ['entrance','middle']:
            options=[q for q in row['placements'] if q['role']==role]
            q,report=next((q,r) for q in options for r in results if r['store']==row['id'] and
                    r['p']==q['p'] and r['role']==q['role'] and not r['issue'])
            key=q['program'];s=make_module(key) if key.startswith('cinema') else Department(key)
            assert s.solids and (s.posters or key=="cinema_box_office"),key
            for pose in s.solids: assert min(pose['size'])>0
            trade='cinema' if key.startswith('cinema') else 'food' if key.startswith('market') else 'fashion'
            s.save(raw/('room-'+key+'.bin'))
            models[key]={'solids':s.solids,'lights':s.lights,'posters':s.posters,'campaign':trade}
            p=[q['p'][0],round(report['physical_floor']+.002,3),q['p'][2]]
            stations.append(dict(role=role,program=key,p=p,yaw=q['yaw'],width=q['width'],depth=q['depth']))
        floor,report=assemble(row['id'],stations,survey[row['id']],raw)
        stations.append(floor);models[floor['program']]={'solids':[],'lights':[]}
        floor_reports.append(report)
        installed.append(dict(id=row['id'],floor=row['floor'],wing=row['wing'],placements=stations))
    Path(sys.argv[6]).write_text(json.dumps(floor_reports,indent=2))
    dest=project/'source/v36/anchor-programs.json'
    dest.write_text(json.dumps(dict(rooms=installed,models=models),ensure_ascii=False,separators=(',',':'))+'\n')
if __name__=='__main__':main()
