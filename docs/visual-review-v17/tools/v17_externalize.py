"""Lossless geometry/image buffer deduplication; original sources protected. No pixel or geometry simplification."""
from pathlib import Path
import struct,json,hashlib,os
P=Path(__file__).resolve().parents[1];T=P/'assets/shared/textures';T.mkdir(parents=True,exist_ok=True);rows=[];sha=lambda x:hashlib.sha256(x).hexdigest()
for folder in['v17/models']:
 for f in(P/'assets'/folder).glob('*.glb'):
  raw=f.read_bytes();count=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+count]);blob=raw[20+count+8:];removed=set();images=[]
  for im in j.get('images',[]):
   if'bufferView'not in im:continue
   k=im['bufferView'];v=j['bufferViews'][k];data=blob[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']];name=sha(data)+('.png'if im['mimeType']=='image/png'else'.jpg');(T/name).write_bytes(data);removed.add(k);im.pop('bufferView');im['uri']=os.path.relpath(T/name,f.parent);images.append({'sha256':sha(data),'uri':im['uri']})
  if not removed:continue
  newbin=bytearray();views=[];indices={};streams=[]
  for i,v in enumerate(j['bufferViews']):
   if i in removed:continue
   data=blob[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']];streams.append(sha(data));newbin.extend(b'\0'*((-len(newbin))%4));indices[i]=len(views);v['byteOffset']=len(newbin);newbin.extend(data);views.append(v)
  for a in j.get('accessors',[]):
   if'bufferView'in a:a['bufferView']=indices[a['bufferView']]
   for k in['indices','values']:
    if k in a.get('sparse',{}):a['sparse'][k]['bufferView']=indices[a['sparse'][k]['bufferView']]
  j['bufferViews']=views;j['buffers'][0]['byteLength']=len(newbin);text=json.dumps(j,separators=(',',':'),ensure_ascii=False).encode();text+=b' '*((-len(text))%4);newbin.extend(b'\0'*((-len(newbin))%4));result=b'glTF'+struct.pack('<II',2,28+len(text)+len(newbin))+struct.pack('<I',len(text))+b'JSON'+text+struct.pack('<I',len(newbin))+b'BIN\0'+newbin;f.write_bytes(result)
  assert[sha(newbin[v['byteOffset']:v['byteOffset']+v['byteLength']])for v in views]==streams
  assert all(sha((f.parent/q['uri']).resolve().read_bytes())==q['sha256']for q in images)
  rows.append({'path':str(f.relative_to(P)),'before_bytes':len(raw),'after_bytes':len(result),'before_sha256':sha(raw),'after_sha256':sha(result),'geometry_unchanged':True,'image_bytes_unchanged':True,'images':images})
(P/'source/v17/lossless-model-packaging.json').write_text(json.dumps(rows,indent=2));print('DEDUP',len(rows),'glbs, recovered',sum(r['before_bytes']-r['after_bytes']for r in rows),'bytes',flush=True)
