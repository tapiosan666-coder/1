"""Original layered hair strand maps; no photographs or downloaded artwork."""
from pathlib import Path
import numpy as np
from PIL import Image
out=Path(__file__).resolve().parents[1]/'assets/characters/textures';out.mkdir(exist_ok=True)
n=512;y,x=np.mgrid[:n,:n]/n;rng=np.random.default_rng(15015)
# Fine fibres grouped into soft locks, with a slight side sweep.
phase=x*160+np.sin(y*4.0)*1.8
fine=np.sin(phase*np.pi*2)*.5+.5
clumps=(np.sin((x+np.sin(y*3)*.03)*24*np.pi)**2)
noise=rng.random((n,n))
value=np.clip(.60+fine*.16+clumps*.12+(noise-.5)*.06,0,1)
rough=.58+fine*.13
height=fine*.05+clumps*.08;dy,dx=np.gradient(height)
norm=np.stack((-dx*2.5,dy*2.5,np.ones_like(x)),axis=-1);norm/=np.linalg.norm(norm,axis=-1,keepdims=True)
Image.fromarray(np.uint8(np.stack((value,rough,value),axis=-1)*255)).save(out/'hair_strands.png')
Image.fromarray(np.uint8((norm*.5+.5)*255)).save(out/'hair_normal.png')
print('Authored hair strand maps')
