from pathlib import Path
import json,numpy as np,shutil
P=Path(__file__).resolve().parents[1];S=P/'authoring/v19-source';shutil.copy2('/workspace/1/tools/source_assets/makehuman-base.obj',S/'makehuman-base.obj')
v=[];uv=[];faces=[];active='';allgroups={}
for l in(S/'makehuman-base.obj').read_text().splitlines():
 if l.startswith('v '):v.append(list(map(float,l.split()[1:4])))
 elif l.startswith('vt '):uv.append(list(map(float,l.split()[1:3])))
 elif l.startswith('g '):active=l[2:]
 elif l.startswith('f '):
  t=[(int(s.split('/')[0])-1,int(s.split('/')[1])-1)for s in l.split()[1:]];allgroups.setdefault(active,[]).append(t)
  if active=='body':faces.append(t)
v=np.array(v);original=v.copy()
for name,w in [('asian-female-young.target',.80),('caucasian-female-young.target',.20),('universal-female-young-averagemuscle-averageweight.target',1.)]:
 for l in(S/name).read_text().splitlines():
  if not l or l.startswith('#'):continue
  parts=l.split()
  if len(parts)==4:v[int(parts[0])]+=np.array(list(map(float,parts[1:])))*w
ids=sorted({i for f in faces for i,u in f});low=v[ids,1].min();high=v[ids,1].max();scale=1.665/(high-low)
# Source X right, Y up, Z forward -> Blender X right, Y back, Z up.
world=np.column_stack([v[:,0]*scale,-v[:,2]*scale,(v[:,1]-low)*scale]);rig=json.load(open(S/'default.mhskel'));joints={name:world[indices].mean(axis=0).tolist()for name,indices in rig['joints'].items()}
result={'vertices':world.tolist(),'original_vertices':original.tolist(),'body_faces':faces,'uvs':uv,'joints':joints,'bones':rig['bones'],'height_m':1.665,'scale':scale,'source_floor_y':float(low),'groups':{k:len(f)for k,f in allgroups.items()}}
(S/'female-anatomy.json').write_text(json.dumps(result,separators=(',',':')))
for name in rig['bones']:
 if name in['root','pelvis','head','jaw','eye.L','eye.R','upperarm01.L','lowerarm01.L','wrist.L','upperleg01.L','lowerleg01.L','foot.L']or 'lid'in name:print(name,joints[rig['bones'][name]['head']],joints[rig['bones'][name]['tail']])
print('ANATOMY',len(v),'bodyfaces',len(faces),'height',high-low,'scale',scale,'groups',list(allgroups)[:12]);print('bones',list(rig['bones'])[-20:])
