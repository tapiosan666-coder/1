from pathlib import Path
import struct,json,hashlib,io,os
from PIL import Image
P=Path(__file__).resolve().parents[1];file=P/'assets/v20/character/FY-F-01.glb';T=P/'assets/v20/textures';T.mkdir(parents=True,exist_ok=True);raw=file.read_bytes();n=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+n]);blob=raw[28+n:];images=[];removed=set();sha=lambda b:hashlib.sha256(b).hexdigest()
for image in j.get('images',[]):
 if'bufferView'not in image:continue
 k=image.pop('bufferView');view=j['bufferViews'][k];data=blob[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']];source=Image.open(io.BytesIO(data));stream=io.BytesIO();source.save(stream,'WEBP',lossless=True,method=6,exact=True);encoded=stream.getvalue();ext='.webp'
 if len(encoded)>=len(data):encoded=data;ext='.png'
 dest=T/(sha(data)+ext);dest.write_bytes(encoded);original_rgba=source.convert('RGBA').tobytes();assert original_rgba==Image.open(dest).convert('RGBA').tobytes();removed.add(k);image.pop('mimeType',None);image['uri']=os.path.relpath(dest,file.parent);images.append({'uri':image['uri'],'source_png_sha256':sha(data),'stored_sha256':sha(encoded),'decoded_RGBA_sha256':sha(original_rgba),'pixels_unchanged':True,'before_bytes':len(data),'after_bytes':len(encoded)})
views=[];new=bytearray();indices={};streams=[]
for k,view in enumerate(j['bufferViews']):
 if k in removed:continue
 data=blob[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']];streams.append(sha(data));new.extend(b'\0'*((-len(new))%4));indices[k]=len(views);v=view.copy();v['byteOffset']=len(new);new.extend(data);views.append(v)
for a in j.get('accessors',[]):
 if'bufferView'in a:a['bufferView']=indices[a['bufferView']]
 for slot in['indices','values']:
  if slot in a.get('sparse',{}):a['sparse'][slot]['bufferView']=indices[a['sparse'][slot]['bufferView']]
j['bufferViews']=views;j['buffers'][0]['byteLength']=len(new);j['asset'].setdefault('extras',{})['FY20_derived_license_settings']=json.load(open(P/'licenses/v20/derived-model-license-settings.json'));j['asset']['extras']['FY20_source']=json.load(open(P/'licenses/v20/PROVENANCE.json'))
for texture in j.get('textures',[]):
 source=texture.get('source')
 if source is not None and j['images'][source].get('uri','').endswith('.webp'):
  texture.setdefault('extensions',{})['EXT_texture_webp']={'source':source};texture.pop('source')
  for key in ['extensionsUsed','extensionsRequired']:
   if 'EXT_texture_webp'not in j.setdefault(key,[]):j[key].append('EXT_texture_webp')
text=json.dumps(j,separators=(',',':'),ensure_ascii=False).encode();text+=b' '*((-len(text))%4);new.extend(b'\0'*((-len(new))%4));result=b'glTF'+struct.pack('<II',2,28+len(text)+len(new))+struct.pack('<I',len(text))+b'JSON'+text+struct.pack('<I',len(new))+b'BIN\0'+new;file.write_bytes(result);assert[sha(new[v['byteOffset']:v['byteOffset']+v['byteLength']])for v in views]==streams
(P/'source/v20/lossless-character-images.json').write_text(json.dumps({'file':str(file.relative_to(P)),'before_bytes':len(raw),'after_bytes':len(result),'before_sha256':sha(raw),'after_sha256':sha(result),'geometry_and_animation_buffers_unchanged':True,'images':images},indent=2));print('FY20_IMAGES',len(images),'saved embedded',len(raw)-len(result),'texture savings',sum(x['before_bytes']-x['after_bytes']for x in images))
