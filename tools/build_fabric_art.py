"""Original seamless woven cloth micro-surface; no photographs or external art."""
from pathlib import Path
from PIL import Image
import math
root=Path(__file__).resolve().parents[1]
n=128
height=[]
for y in range(n):
 row=[]
 for x in range(n):
  warp=math.cos(x*math.tau/8);weft=math.cos(y*math.tau/8)
  over=1 if (x//8+y//8)%2 else -1
  row.append(.5+.14*(warp+weft)+.08*over*(warp-weft))
 height.append(row)
image=Image.new('RGB',(n,n));normal=Image.new('RGB',(n,n))
for y in range(n):
 for x in range(n):
  v=round(128+60*(height[y][x]-.5));image.putpixel((x,y),(v,v,v))
  dx=(height[y][(x+1)%n]-height[y][(x-1)%n])*.35
  dy=(height[(y+1)%n][x]-height[(y-1)%n][x])*.35
  length=math.sqrt(dx*dx+dy*dy+1)
  normal.putpixel((x,y),tuple(round(127.5+127.5*a/length) for a in [-dx,-dy,1]))
image.save(root/'assets/retail/cloth_weave.png',optimize=True)
normal.save(root/'assets/retail/cloth_normal.png',optimize=True)
print('Created original 128px seamless cloth surface maps')
