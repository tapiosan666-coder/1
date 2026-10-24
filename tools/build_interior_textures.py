#!/usr/bin/env python3
"""Author seamless material maps from numeric fields; no source photographs.

Optional NumPy/Pillow authoring dependencies are in art-requirements.txt.
Color maps are sRGB. Surface maps store tangent normal XY in RG, roughness in B.
"""
from pathlib import Path
import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parents[1] / 'assets/interiors'
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(12012)


def field(n, frequency):
    spectrum = np.fft.rfft2(rng.normal(size=(n, n)))
    fx = np.fft.rfftfreq(n)[None, :] * n
    fy = np.fft.fftfreq(n)[:, None] * n
    spectrum *= np.exp(-(fx * fx + fy * fy) / (2 * frequency ** 2))
    result = np.fft.irfft2(spectrum, s=(n, n))
    return result / max(result.std(), 1e-9)


def save(name, color, height, roughness, normal_gain):
    if color is not None:
        Image.fromarray(np.uint8(np.clip(color, 0, 1) * 255)).save(OUT / f'{name}_color.png')
    dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * normal_gain
    dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * normal_gain
    inverse = 1 / np.sqrt(1 + dx * dx + dy * dy)
    data = np.stack([.5 - dx * inverse * .5, .5 - dy * inverse * .5,
                     np.broadcast_to(roughness, height.shape)], axis=-1)
    Image.fromarray(np.uint8(np.clip(data, 0, 1) * 255)).save(OUT / f'{name}_surface.png')


n = 1024
large, medium, fine = field(n, 2), field(n, 12), field(n, 120)
pores = np.maximum(field(n, 210) - 1.4, 0)
strata = np.exp(-np.square((medium + large * .24) * 7))
variation = large * .017 + medium * .012 + fine * .005 - pores * .012
stone = np.array([.78, .755, .70])[None, None, :] + variation[..., None]
stone -= strata[..., None] * np.array([.012, .013, .015])
save('limestone', stone, fine * .07 - pores * .18,
     np.clip(.39 + medium * .025 + pores * .05, .32, .57), .24)

y, x = np.mgrid[0:n, 0:n] / n
slow, fibers = field(n, 3), field(n, 65)
warp = .7 * np.sin(y * np.pi * 2) + .23 * np.sin(y * np.pi * 6 + x * np.pi * 2)
grain = np.sin(x * np.pi * 128 + warp * 3) * .5
growth = np.sin(x * np.pi * 20 + warp) * .5
vessels = np.maximum(np.sin(x * np.pi * 220 + warp * 5) - .72, 0)
wood_value = grain * .019 + growth * .033 + slow * .012 + fibers * .004 - vessels * .055
wood = np.array([.66, .49, .32])[None, None, :] + wood_value[..., None]
save('oak', wood, grain * .06 + growth * .05 - vessels * .22,
     np.clip(.48 + growth * .035 + vessels * .08, .4, .63), .35)

n = 512
fine = field(n, 135)
save('paint', None, fine * .1, np.clip(.88 + fine * .018, .82, .95), .17)
for path in sorted(OUT.glob('*.png')):
    print(path.name, path.stat().st_size)
