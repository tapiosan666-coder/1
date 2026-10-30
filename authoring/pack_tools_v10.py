from pathlib import Path
import gzip,json,struct,numpy as np

def load_pack(path):
 raw=gzip.decompress(Path(path).read_bytes());hn=struct.unpack_from('<I',raw,4)[0];h=json.loads(raw[8:8+hn]);base=8+hn
 for k,d in h['surfaces'].items():
  for field,slot in d.items():h['surfaces'][k][field]=np.frombuffer(raw,dtype='<i4'if field=='i'else'<f4',count=slot[1]//4,offset=base+slot[0]).copy()
 for k,slot in h['colliders'].items():h['colliders'][k]=np.frombuffer(raw,dtype='<f4',count=slot[1]//4,offset=base+slot[0]).copy()
 return h

def triangles(d):
 v=np.asarray(d['v']).reshape(-1,3)
 if'i'in d:return v[np.asarray(d['i']).reshape(-1,3)]
 return v.reshape(-1,3,3)

def retain(d,keep):
 if'i'in d:d['i']=np.asarray(d['i']).reshape(-1,3)[keep].ravel();return d
 for k,n in [('v',9),('n',9),('uv',6),('c',12)]:d[k]=np.asarray(d[k]).reshape(-1,n)[keep].ravel()
 return d

def write_pack(path,g):
 h={'surfaces':{},'colliders':{},'signs':g.get('signs',[]),'lights':g.get('lights',[])};chunks=[];offset=0
 def buf(a,dtype='<f4'):
  nonlocal offset
  raw=np.asarray(a,dtype=dtype).tobytes();out=[offset,len(raw)];offset+=len(raw);chunks.append(raw);return out
 for k,d in g['surfaces'].items():
  if not len(d['v']):continue
  if'i'in d:
   if not len(d['i']):continue
   used,idx=np.unique(d['i'],return_inverse=True);nd={f:np.asarray(d[f]).reshape(-1,n)[used].ravel()for f,n in [('v',3),('n',3),('uv',2),('c',4)]};nd['i']=idx.astype('<i4')
  else:
   arr=np.concatenate([np.asarray(d[f],dtype='<f4').reshape(-1,n)for f,n in [('v',3),('n',3),('uv',2),('c',4)]],axis=1);_,first,idx=np.unique(arr.view('V48').ravel(),return_index=True,return_inverse=True);a=arr[first];nd={f:a[:,i:j].ravel()for f,i,j in [('v',0,3),('n',3,6),('uv',6,8),('c',8,12)]};nd['i']=idx.astype('<i4')
  h['surfaces'][k]={f:buf(a,'<i4'if f=='i'else'<f4')for f,a in nd.items()}
 for k,d in g['colliders'].items():
  if len(d):h['colliders'][k]=buf(d)
 js=json.dumps(h,separators=(',',':')).encode()
 with gzip.open(path,'wb',compresslevel=8)as z:z.write(b'FY9\0'+struct.pack('<I',len(js))+js+b''.join(chunks))
 return{'path':str(path),'bytes':Path(path).stat().st_size,'surface_count':len(h['surfaces'])}
