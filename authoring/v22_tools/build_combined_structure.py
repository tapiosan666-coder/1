from pathlib import Path
import json,struct,collections,hashlib,sys
import numpy as np,zstandard as z
P=Path(__file__).resolve().parents[2];O=P/'assets/v22';O.mkdir(exist_ok=True)
def read(p):
 p=P/p
 if p.exists():return json.loads(p.read_text())
 b=Path(str(p)+'.zst').read_bytes();return json.loads(z.ZstdDecompressor().decompress(b[8:]))
def pack(p):
 b=(P/p).read_bytes();raw=z.ZstdDecompressor().decompress(b[8:]);n=struct.unpack_from('<I',raw,4)[0];h=json.loads(raw[8:8+n]);data=raw[8+n:]
 for g in h['surfaces'].values():
  for k,(offset,size)in list(g.items()):g[k]=np.frombuffer(data[offset:offset+size],dtype='<i4'if k=='i'else'<f4').copy()
 for k,(offset,size)in list(h['colliders'].items()):h['colliders'][k]=np.frombuffer(data[offset:offset+size],dtype='<f4').copy()
 return h
paths=['v10/base-b','v10/base-site','v10/fitout','v10/art','v10/architecture','v11/repairs','v12/es-safety','v12/retail','v12/boundary-physics','v12/es-unbuilt-safety','v12/es-landing-plates']
# Runtime merges amenities over public areas, basement over roof; duplicate key precedence is significant.
paths+=['v13/amenities','v13/public-areas','v13/basement-retail','v13/roof-retail']
base={'surfaces':{},'colliders':{}}
for p in paths:
 q=pack('assets/'+p+'.pack.zst')
 for k,v in q['surfaces'].items():base['surfaces'].setdefault(k,v)
 for k,v in q['colliders'].items():base['colliders'].setdefault(k,[]);base['colliders'][k].append(v)
base['colliders']={k:np.concatenate(v)for k,v in base['colliders'].items()}
patches=[pack('assets/v15/C-finish-replacement.pack.zst'),pack('assets/v15/ES-site-replacement.pack.zst')]
infos=[read('source/v15/C-finish-audit.json'),read('source/v15/ES-site-proposal.json')]
# Exact float32 vertices, orientation independent matching; retain original triangle winding in output.
def triangles(a):
 a=a.reshape((-1,3,3));d={}
 for tri in a:
  key=tuple(sorted(tuple(float(x)for x in p)for p in tri));d[key]=tri
 return d
out={'surfaces':{},'colliders':{},'lights':[],'signs':[]};audit=[]
for patch in patches:
 for k,v in patch['surfaces'].items():
  if k in out['surfaces']and any(not np.array_equal(v[f],out['surfaces'][k][f])for f in v):raise ValueError('Conflicting surface '+k)
  out['surfaces'][k]=v
for material in sorted(set(patches[0]['colliders'])|set(patches[1]['colliders'])):
 original=triangles(base['colliders'].get(material,np.array([],dtype='<f4')));remove=set();add={};changes=[]
 for patch in patches:
  if material not in patch['colliders']:changes.append({'removed':0,'added':0});continue
  candidate=triangles(patch['colliders'][material]);removed=original.keys()-candidate.keys();added=candidate.keys()-original.keys();remove.update(removed);add.update({k:candidate[k]for k in added});changes.append({'removed':len(removed),'added':len(added)})
 combined={k:v for k,v in original.items()if k not in remove};combined.update(add);out['colliders'][material]=np.array(list(combined.values()),dtype='<f4').ravel();audit.append({'material':material,'original_triangles':len(original),'C_ES_changes':changes,'combined_triangles':len(combined),'removed_union':len(remove),'added_union':len(add)})
blob=bytearray();head={'surfaces':{},'colliders':{},'lights':[],'signs':[]}
def slot(v):
 offset=len(blob);raw=v.tobytes();blob.extend(raw);return[offset,len(raw)]
for k,v in out['surfaces'].items():head['surfaces'][k]={f:slot(a)for f,a in v.items()}
for k,v in out['colliders'].items():head['colliders'][k]=slot(v)
j=json.dumps(head,separators=(',',':')).encode();raw=b'FYB1'+struct.pack('<I',len(j))+j+blob;b=b'FYZ1'+struct.pack('<I',len(raw))+z.ZstdCompressor(level=14).compress(raw);(O/'combined-structure.pack.zst').write_bytes(b)
info={'erase_surfaces':sorted(set(infos[0]['erase_surfaces'])|set(infos[1]['erase_surfaces'])),'collision_delta':audit,'policy':'Exact triangle-set union of independent C and B deltas against distributed normal v21; runtime never sequentially overwrites whole material colliders.','engineering_verified':False,'physical_tested':False,'sha256':hashlib.sha256(b).hexdigest()}
(P/'source/v22/combined-structure.json').write_text(json.dumps(info,indent=2));print('Combined',len(out['surfaces']),'surfaces',len(out['colliders']),'collision layers',len(b),'bytes')
# Map floor data uses common local coordinate system. Both patches affect separate wings.
normal=read('source/v13/map-data.json');c=read('source/v15/map-data-C-option.json');e=read('source/v15/map-data-ES-option.json')
exec(Path(__file__).with_name('fix_combined_map.py').read_text())
