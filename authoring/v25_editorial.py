from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];A=P/'assets/v25/art';f='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';b='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
rows=json.loads((P/'source/v25/store-finishes.json').read_text());focus={x['id']:x for x in json.loads((P/'source/v25/focus-stores.json').read_text())};atlas=Image.new('RGB',(2560,768),'#e3dccd')
copy={'apparel':['THE EVERYDAY EDIT','重ねる、春のシルエット。','NEW SEASON / FERNELL ATELIER'],'book':['READ / DISCOVER / STAY','本と、暮らしのつづき。','FICTION / ART / DESIGN / CHILDREN'],'cafe':['SLOW MORNINGS','一杯と、心地よいひととき。','COFFEE / PASTRY / LOUNGE'],'beauty':['BOTANICAL RITUAL','肌と、向き合う。','TEST / CONSULT / DISCOVER'],'arcade':['PULSE & VELOCITY','音に乗ろう。遊びを見つけよう。','MUSIC / RACING / PRIZE / PHOTO']}
def text(d,t,y,size,col):
 while ImageFont.truetype(b,size).getlength(t)>466:size-=1
 d.text((256,y),t,font=ImageFont.truetype(b,size),fill=col,anchor='mm')
for i,r in enumerate(rows):
 k=focus[r['id']]['category'];title,jp,small=copy[k];bg='#132438'if k=='arcade'else r['wall_colour'];ink='#e6c9df'if k=='arcade'else r['accent_colour'];tile=Image.new('RGB',(512,768),bg);d=ImageDraw.Draw(tile);text(d,focus[r['id']]['brand'],52,35,ink);d.line((30,95,482,95),fill=ink,width=2);text(d,title,139,29,ink)
 if k=='arcade':
  a=Image.open(A/'original-music-screen.png').resize((286,345));tile.paste(a,(30,205));a=Image.open(A/'original-racing-screen.png').resize((210,275));tile.paste(a,(272,280))
 else:
  category={'cafe':'food'}.get(k,k);im=Image.open(P/f'assets/v24/art/product-portrait-{category}.png').convert('RGBA');im.thumbnail((452,440));tile.paste(im,((512-im.width)//2,184+(440-im.height)//2),im)
 d=ImageDraw.Draw(tile);text(d,jp,653,25,ink);text(d,small,701,16,ink);text(d,'FIND YOURSELF / ORIGINAL BRAND',738,13,ink);atlas.paste(tile,(i*512,0));r['poster_uv']=[i/5,0,1/5,1];r['poster_texture']='res://assets/v25/art/store-editorial-atlas.png'
atlas.save(A/'store-editorial-atlas.png');(P/'source/v25/store-finishes.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));print('V25_ORIGINAL_POSTERS',len(rows))
