"""Compose commissioned original editorial art with the shop's existing name into a wall print."""
from pathlib import Path
import json
import random
import hashlib
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / 'assets/v36/wall_editions'
TILES = ['fashion','clay','beauty','audio','edition','market','coffee','trail','play']
CATEGORIES = {
 'apparel':('fashion','衣服と暮らし'),'shoes':('fashion','シューズコレクション'),
 'accessories':('fashion','アクセサリー'),'optics':('fashion','アイウェア'),
 'beauty':('beauty','ビューティー'),'pharmacy':('beauty','ヘルスケア'),
 'electronics':('audio','音と映像'),'music':('audio','リスニングルーム'),'mobile':('audio','モバイル'),
 'home':('clay','暮らしの道具'),'furniture':('clay','家具と空間'),'garden':('clay','植物と暮らし'),
 'food':('market','季節の食卓'),'restaurant':('market','季節のメニュー'),'cafe':('coffee','珈琲と焼き菓子'),
 'gallery':('edition','企画展示'),'book':('edition','本のある風景'),'stationery':('edition','紙と文具'),
 'sports':('trail','フィールドコレクション'),'toy':('play','木と遊び'),'arcade':('play','アミューズメント'),
 'cinema':('edition','シネマ'),'service':('clay','ご案内')}
PALETTES = [('#193836','#e8e0ce','#b49866'),('#552f2b','#f3e7d6','#d0a37c'),('#283b4a','#e0dcca','#acc4be'),('#ddd3bc','#332f2a','#6d7f73')]
SERIF='/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'
SANS='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'

def split_art(master):
    ART.mkdir(parents=True,exist_ok=True)
    im=Image.open(master).convert("RGB")
    w,h=im.size
    for i,name in enumerate(TILES):
        col,row=i%3,i//3
        tile=im.crop((round(w*col/3)+4,round(h*row/3)+4,round(w*(col+1)/3)-4,round(h*(row+1)/3)-4))
        tile.save(ART/f"image-{name}.webp",quality=91)

def typeface(size,roman=True):
    return ImageFont.truetype(SERIF if roman else SANS,size)

def paint(brand,category,fmt,seed):
    family,title=CATEGORIES[category]
    photo=Image.open(ART/('image-'+family+'.webp'))
    bg,fg,trim=PALETTES[seed%4]
    w,h=1024,384
    canvas=Image.new('RGB',(w,h),bg)
    d=ImageDraw.Draw(canvas)
    block= int(w*(.56 if fmt==0 else .49))
    photo_width=w-block
    right=bool(fmt==2 or (fmt==1 and seed%2))
    start=0 if right else block
    crop=ImageOps.fit(photo,(photo_width,h),centering=(.48 if seed%2 else .55,.48))
    canvas.paste(crop,(start,0))
    off=photo_width if right else 0
    left=off+40
    d.line((left,39,off+block-40,39),fill=trim,width=2)
    words=brand.split()
    size=round(min(68,(block-70)/max(1,len(words[0])*.70)))
    d.text((left,74),words[0],font=typeface(size),fill=fg,stroke_width=0)
    d.text((left+2,162)," ".join(words[1:]),font=typeface(20,False),fill=fg)
    d.text((left,260),title,font=typeface(27,False),fill=fg)
    d.rectangle((left,332,left+35,336),fill=trim)
    return canvas

def generate(records):
    assets={}
    placements=[]
    for r in records:
        m=r['measured']
        if not m or r['id']=='A1F-051':continue
        seed=int.from_bytes(hashlib.blake2s((r['brand']+' '+r['category']).encode(),digest_size=3).digest(),'big')
        fmt=seed%3
        key=f"{r['category']}-{seed:06x}"
        if key not in assets:
            paint(r['brand'],r['category'],fmt,seed).save(ART/(key+'.webp'),quality=84)
            assets[key]=r['brand']
        m=dict(m,id=r['id'],family=CATEGORIES[r['category']][0],tile=key,style=fmt)
        placements.append(m)
    (ROOT/'source/v36/wall-editions.json').write_text(json.dumps(placements,separators=(',',':')))
    print('verified walls',len(placements),'individual brand/category prints',len(assets))

if __name__=='__main__':
    if sys.argv[1]=='split':split_art(sys.argv[2])
    else: generate(json.loads(Path(sys.argv[1]).read_bytes()))
