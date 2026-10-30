from pack_tools_v10 import *
import zstandard

def load_pack(path):
 p=Path(path);b=p.read_bytes();raw=zstandard.ZstdDecompressor().decompress(b[8:])if p.suffix=='.zst'else gzip.decompress(b)
 hn=struct.unpack_from('<I',raw,4)[0];h=json.loads(raw[8:8+hn]);base=8+hn
 for k,d in h['surfaces'].items():
  for field,slot in d.items():h['surfaces'][k][field]=np.frombuffer(raw,dtype='<i4'if field=='i'else'<f4',count=slot[1]//4,offset=base+slot[0]).copy()
 for k,slot in h['colliders'].items():h['colliders'][k]=np.frombuffer(raw,dtype='<f4',count=slot[1]//4,offset=base+slot[0]).copy()
 return h

def save_zst(path,g):
 p=Path(path);tmp=p.with_suffix('.intermediate.gz');write_pack(tmp,g);raw=gzip.decompress(tmp.read_bytes());b=zstandard.ZstdCompressor(level=19,threads=2).compress(raw);p.write_bytes(b'FYZ1'+struct.pack('<I',len(raw))+b);tmp.unlink();return{'file':str(p),'bytes':p.stat().st_size,'decoded_bytes':len(raw),'decoded_sha256':__import__('hashlib').sha256(raw).hexdigest()}
