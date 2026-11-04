from pathlib import Path
import json,struct,hashlib
P=Path(__file__).resolve().parents[1];root=P/'assets/v21';proof=[]
for f in (root/'models').glob('sku_book_[0-5].glb'):f.unlink()
for file in sorted((root/'models').glob('*.glb')):
 raw=file.read_bytes();n=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+n]);blob=raw[28+n:];removed=set();rows=[]
 for im in j.get('images',[]):
  if'bufferView'not in im:continue
  k=im.pop('bufferView');v=j['bufferViews'][k];data=blob[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']];name=hashlib.sha256(data).hexdigest()+'.png';out=root/'art'/name;out.write_bytes(data);im.pop('mimeType',None);im['uri']='../art/'+name;removed.add(k);rows.append(name)
 views=[];new=bytearray();indices={};hashes=[]
 for k,v in enumerate(j['bufferViews']):
  if k in removed:continue
  data=blob[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']];hashes.append(hashlib.sha256(data).hexdigest());new.extend(b'\0'*(-len(new)%4));indices[k]=len(views);vv=v.copy();vv['byteOffset']=len(new);views.append(vv);new.extend(data)
 for a in j['accessors']:
  if'bufferView'in a:a['bufferView']=indices[a['bufferView']]
 j['bufferViews']=views;j['buffers'][0]['byteLength']=len(new);j['asset'].setdefault('extras',{})['FY21_provenance']='Original Blender geometry and product art; inherited CC0 oak/walnut textures retained with licences. No character changes.';text=json.dumps(j,separators=(',',':')).encode();text+=b' '*(-len(text)%4);new.extend(b'\0'*(-len(new)%4));file.write_bytes(b'glTF'+struct.pack('<II',2,28+len(text)+len(new))+struct.pack('<I',len(text))+b'JSON'+text+struct.pack('<I',len(new))+b'BIN\0'+new);assert[hashlib.sha256(new[v['byteOffset']:v['byteOffset']+v['byteLength']]).hexdigest()for v in views]==hashes;proof.append({'file':file.name,'external_images':rows,'geometry_bytes_unchanged':True})
(P/'source/v21/asset-storage.json').write_text(json.dumps(proof,indent=2));print('V21_EXTERNAL_IMAGES',len(proof),'models')
