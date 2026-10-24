"""Author deterministic skin and textile data maps from scratch (NumPy/Pillow).
No face photographs, downloaded textures or network service are used.
Run only when authoring assets; Python is not needed to play.
"""
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1] / 'assets/characters/textures'
ROOT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(11031)

def smooth_noise(size, cells):
    coarse = rng.random((cells + 1, cells + 1), dtype=np.float32)
    axis = np.linspace(0, cells, size, endpoint=False, dtype=np.float32)
    cell = axis.astype(int); t = axis - cell; t = t*t*(3-2*t)
    low = coarse[cell[:, None], cell[None, :]]*(1-t)[None, :] + coarse[cell[:, None], (cell+1)[None, :]]*t[None, :]
    high = coarse[(cell+1)[:, None], cell[None, :]]*(1-t)[None, :] + coarse[(cell+1)[:, None], (cell+1)[None, :]]*t[None, :]
    return low*(1-t)[:, None] + high*t[:, None]

def save(name, array):
    Image.fromarray(np.uint8(np.clip(array, 0, 1)*255)).save(ROOT / name)

def normal_map(height, strength):
    dy, dx = np.gradient(height)
    normal = np.stack((-dx*strength, dy*strength, np.ones_like(height)), axis=-1)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    return normal*.5 + .5

size = 1024
macro = smooth_noise(size, 10)
capillary = smooth_noise(size, 45)
pores = smooth_noise(size, 280)
fine = rng.random((size, size), dtype=np.float32)
# Channels are data: pigmentation, vascular variation, oil/roughness.
freckles = np.maximum(0, capillary-.75)*2
skin = np.stack((.5+(macro-.5)*.36-freckles*.25,
                 .5+(capillary-.5)*.3,
                 .5+(pores-.5)*.4), axis=-1)
save('skin_detail.png', skin)
height = pores*.65 + fine*.12 + capillary*.07
save('skin_normal.png', normal_map(height, 1.2))

size = 512
y, x = np.mgrid[:size, :size].astype(np.float32)
warp = np.cos(x*np.pi/2)**8
weft = np.cos(y*np.pi/2)**8
twill = np.sin((x+y)*np.pi/8)*.5+.5
noise = smooth_noise(size, 32)
weave = (warp*.45+weft*.45+twill*.1)
fabric = np.stack((.5+(noise-.5)*.2+(weave-.5)*.12,
                   .5+(weave-.5)*.35,
                   .7+(noise-.5)*.12), axis=-1)
save('fabric_detail.png', fabric)
save('fabric_normal.png', normal_map(weave*.16+noise*.06, 1.4))
print('Created skin/textile detail and tangent-normal maps in', ROOT)
