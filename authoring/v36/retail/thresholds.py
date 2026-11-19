"""Lay out ID-specific, location-appropriate threshold finishes inside the shop.

Source categories and route polylines are authoritative. All proposals undergo a
second pass against the actual Godot floor before admission to the runtime file.
"""
from pathlib import Path
from collections import defaultdict
from random import Random
import json,math,zlib
from PIL import Image,ImageFont,ImageDraw,ImageFilter,ImageOps
from shapely.geometry import Point,shape
from shapely import STRtree
from lay_out import read,rect,world_line,PROJECT
from art import CATEGORIES,PALETTES
W,H=336,108
FONTS='/usr/share/fonts/truetype/dejavu/DejaVu'
def font(name,size):return ImageFont.truetype(FONTS+name+'.ttf',size)
def ink_art(store,style,seed):
    rng=Random(seed);v=seed%3
    groups={'loom':(('#405052','#dacfb4','#a9a99b'),('#7c4e3d','#f1d9b5','#c19e77')),
            'tile':(('#ded8c9','#263e48','#7d7770'),('#e7ded0','#544936','#8a784d')),
            'bronze':(('#52615f','#e5dac0','#9d9b82'),('#766656','#fff1cd','#c1aa8c')),
            'marquetry':(('#7e5b47','#f5e6ba','#b6a182'),('#615245','#f4e8c8','#bda68d'))}
    bg,ink,trim=groups[style][v%2];im=Image.new('RGB',(W,H),bg);d=ImageDraw.Draw(im)
    if style=='loom':
        for xx in range(0,W,4): d.line((xx,0,xx,H),fill=tuple(max(0,x-7) for x in bytes.fromhex(bg[1:])))
        for yy in range(0,H,3):d.line((0,yy,W,yy),fill=tuple(min(255,x+6) for x in bytes.fromhex(bg[1:])))
        for xx in range(8,W-4,8):d.line((xx,7,xx+3,7),trim,2);d.line((xx,H-8,xx+3,H-8),trim,2)
    elif style=='tile':
        for xx in (28,61,W-28,W-61):
            d.line((xx,0,xx+24,H),trim,1)
        for j in range(2):
            for k in range(3):
                cx=20+k*8;cy=32+j*32
                d.polygon([(cx,cy-8),(cx+4,cy),(cx,cy+8),(cx-4,cy)],outline=trim)
    elif style=='bronze':
        for i in range(22): 
            x,y=rng.randrange(12,W-82),rng.randrange(H);d.line((x,y,x+rng.randrange(12,66),y),fill=tuple(min(255,t+5) for t in bytes.fromhex(bg[1:])))
        for x in (7,W-8):
            for y in (9,H-10):d.ellipse((x-2,y-2,x+2,y+2),trim)
        d.line((18,9,W-18,9),trim);d.line((18,H-10,W-18,H-10),trim)
    else:
        for x in range(-26,W+50,19):
            d.line((x-25,0,x+20,H),fill=tuple(max(0,t-7) for t in bytes.fromhex(bg[1:])),width=1)
        d.rectangle((5,5,W-6,H-6),outline=trim)
        d.line((12,13,36,13,36,20),trim,width=2);d.line((W-13,H-14,W-37,H-14,W-37,H-21),trim,width=2)
    name=store['brand'];face=font('Serif' if style in ('marquetry','tile') else 'SansCondensed-Bold',27)
    while d.textlength(name,font=face)>W-34:face=font('Serif' if style in ('marquetry','tile') else 'SansCondensed-Bold',face.size-1)
    d.text((W//2,46),name,font=face,fill=ink,anchor='mm')
    line=CATEGORIES[store['category']][1]
    d.text((W//2,75),line,font=font('SansCondensed',11),fill=ink,anchor='mm')
    return im
def choose(s,fixture,front):
    entry=Point(s['entry_world']);sales=shape(s['sales_world']).buffer(0)
    route=world_line(s['main_route_world'])
    normal=front['normal'];u=(-normal[0],-normal[1])
    candidates=[u,(-u[0],-u[1])]
    if len(route)>1:
        for q in route[1:4]:
            dx,dz=q[0]-entry.x,q[1]-entry.y;l=math.hypot(dx,dz)
            if l>.05:candidates.append((dx/l,dz/l))
    tree=STRtree(fixture);clearance=sales.buffer(.006)
    for width,depth in [(2.22,.71),(1.64,.66),(1.26,.55)]:
        for nx,nz in candidates:
            for gap in (1.15,1.52,.82,1.95,2.36):
                x,z=entry.x+gap*nx,entry.y+gap*nz
                foot=rect(x,z,nz,-nx,nx,nz,width,depth)
                if clearance.covers(foot) and len(tree.query(foot,predicate='intersects'))==0:
                    return dict(role='threshold',p=[round(x,3),s['height']+.03,round(z,3)],yaw=round(math.atan2(-nx,-nz),5),width=width,depth=depth)
    return None
def main():
    plan=read('source/v294/retail-plan.json.zst')
    fixtures=defaultdict(list)
    for f in plan['fixtures']:
        if f.get('footprint'): fixtures[f['store_id']].append(shape(f['footprint']).buffer(.06))
    for s in read('source/v32/sales-design.json')['stores']:
        fixtures[s['id']].extend(shape(f['footprint']).buffer(.06) for f in s['placements'])
    fronts={f['store_id']:f for f in read('source/brands-v11.json')}
    previous={s['id']:s for s in read('source/v36/store-studios.json')}
    groups=defaultdict(list);allrows=[]
    for s in plan['stores']:
        for b in previous[s['id']]['placements']:
            if b.get('refit'):continue
            nx,nz=math.sin(b['yaw']),math.cos(b['yaw']);x,_,z=b['p']
            fixtures[s['id']].append(rect(x,z,nz,-nx,nx,nz,b['width'],.80))
        patch=choose(s,fixtures[s['id']],fronts[s['id']])
        if not patch:continue
        cat=s['category']
        style=('loom' if (s['wing']=='C' or cat in ('garden','sports','food')) else
               'bronze' if cat in ('electronics','service','mobile','arcade') else 
               'marquetry' if cat in ('book','music','home','cafe','furniture','stationery') else 'tile')
        key=s['wing']+'-'+s['floor'];seed=zlib.crc32(s['brand'].encode())
        row=dict(id=s['id'],wing=s['wing'],floor=s['floor'],brand=s['brand'],cat=cat,material=style,placements=[patch])
        groups[key].append((s,row,ink_art(s,style,seed)));allrows.append(row)
    for key,rows in groups.items():
        cols=min(5,len(rows));count=math.ceil(len(rows)/cols);atlas=Image.new('RGB',(cols*W,count*H))
        for i,(s,row,img) in enumerate(rows):
            x=i%cols*W;y=i//cols*H;atlas.paste(img,(x,y))
            row['atlas']=key;row['uv']=[round((x+1)/(W*cols),7),round((y+1)/(H*count),7),round((x+W-1)/(W*cols),7),round((y+H-1)/(H*count),7)]
        atlas.save(PROJECT/'assets/v36/studios'/('threshold-'+key+'.webp'),quality=91,method=5)
    (PROJECT/'source/v36/thresholds.json').write_text(json.dumps(allrows,separators=(',',':'))+'\n')
    print('accepted preliminary',len(allrows),'sheets',len(groups))
if __name__=='__main__': main()
