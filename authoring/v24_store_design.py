"""Thirty authored style briefs, clipped finish surfaces and original poster atlas."""
from pathlib import Path
import sys,math,json,numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import read,write,Point,LineString,polys,lines
from shapely.ops import triangulate
plan=read(P/'source/v24/retail-plan.json');stores={s['id']:s for s in plan['stores']};focus=read(P/'source/v24/focus-stores.json');dirs=read(P/'source/v22/store-directions.json');atlas=Image.new('RGB',(3072,3840),'#eee9df');font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';bold='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc';themes={
'apparel':('#d8d2c2','#4c6054',0,'#cfb798',.48,[1,.91,.77],'着る、日々の心地よさ。'),
'shoes':('#d7d1c5','#313f44',1,'#a6a19a',.34,[1,.91,.80],'歩幅に合う、かたち。'),
'accessories':('#e4ddd2','#405260',1,'#dbd8d0',.26,[1,.95,.85],'小さな輝き、いつもの私へ。'),
'beauty':('#eee0d2','#9a6261',3,'#ded5c7',.34,[1,.95,.88],'ひと塗りの、ちがい。'),
'home':('#d9d5c8','#586052',0,'#cbb292',.58,[1,.89,.73],'暮らしをつくる、選ぶ道具。'),
'furniture':('#d1c7b5','#4e5547',2,'#aaa293',.91,[1,.86,.69],'ひとつの部屋から。'),
'book':('#d7cbb7','#40534b',0,'#b2916c',.59,[1,.87,.69],'ページの先へ。'),
'electronics':('#dce0de','#214459',1,'#bdc5c7',.37,[.88,.95,1.0],'暮らしを、もっと快適に。'),
'food':('#dcd6c5','#5c6e49',3,'#c4beb0',.58,[1,.94,.82],'採れたてから、食卓へ。'),
'cafe':('#cfc2ab','#654735',0,'#a68b68',.61,[1,.79,.56],'一杯と、ひと休み。'),
'restaurant':('#c6b99f','#5f6251',0,'#a48769',.61,[1,.80,.58],'季節をいただく。'),
'arcade':('#343b49','#427386',2,'#343a43',.94,[.67,.84,1.0],'PLAY IS HERE.'),
'toy':('#e5d9bd','#a56842',2,'#c9be9f',.87,[1,.95,.84],'見つける、つくる、遊ぶ。'),
'sports':('#c8cfcc','#3e5857',2,'#858e8d',.91,[.91,.97,1.0],'動ける自分を、つくる。'),
'pharmacy':('#e0e6dc','#4d7668',1,'#d1d9d4',.54,[.94,1.,.97],'毎日を、すこやかに。')}
rows=[]
def textfit(draw,text,box,size,col,fontpath=bold):
 x,y,w,h=box
 while size>13 and ImageFont.truetype(fontpath,size).getlength(text)>w:size-=1
 draw.text((x+w/2,y+h/2),text,font=ImageFont.truetype(fontpath,size),fill=col,anchor='mm')
for i,d in enumerate(focus):
 s=stores[d['id']];cat=d['design_category'];wall,accent,kind,floor,rough,light,copy=themes[cat];style=d['style']
 if style=='formal_tailoring':wall,accent,kind,floor,rough='#c6c8c6','#293841',2,'#50565a',.92
 if style=='women_select':wall,accent,kind,floor='#e5dace','#8e7167',3,'#ddd6ca'
 if style=='botanical_beauty':wall,accent='#dce2d5','#596f57'
 if style=='warm_jewellery':wall,accent,kind,floor='#d5c4b0','#5e4d41',0,'#bba17e'
 if style=='technical_footwear':wall,accent,kind,floor='#d9dfdc','#31484d',2,'#7b8988'
 if style=='patisserie':wall,accent,kind,floor='#e5d5c6','#946252',3,'#d5c4b8'
 if style=='garden_cafe':wall,accent,kind,floor='#d6d9c8','#526950',1,'#c5c4b7'
 x=i%6*512;y=i//6*768;tile=Image.new('RGB',(512,768),wall);draw=ImageDraw.Draw(tile);draw.rectangle((0,0,512,162),fill=accent);textfit(draw,s['brand'],(24,28,464,64),42,'#f6f0e5');textfit(draw,'COLLECTION / '+style.replace('_',' ').upper(),(30,105,452,34),18,'#e4d9c4');draw.line((30,151,482,151),fill='#beaa85',width=2)
 photo_cat={'furniture':'home','restaurant':'food','cafe':'food','arcade':'electronics','pharmacy':'beauty'}.get(cat,cat);photo=Image.open(P/f'assets/v24/art/product-portrait-{photo_cat}.png').convert('RGBA');photo.thumbnail((445,448));tile.paste(photo,((512-photo.width)//2,174+(448-photo.height)//2),photo);draw=ImageDraw.Draw(tile);textfit(draw,copy,(30,635,452,58),27,accent);textfit(draw,'FIND YOURSELF / ORIGINAL BRAND',(30,704,452,24),14,accent,font);draw.rectangle((30,741,482,744),fill=accent);atlas.paste(tile,(x,y))
 sales=s['sales_world'].buffer(-.055);triangles=[]
 for poly in polys(sales):
  for tri in triangulate(poly):
   if poly.covers(tri)and tri.area>1e-5:triangles.append([list(q)for q in list(tri.exterior.coords)[:3]])
 edges=[]
 for poly in polys(sales):
  coords=list(poly.exterior.simplify(.045).coords)
  for a,b in zip(coords,coords[1:]):
   line=LineString([a,b])
   if line.length<1.35:continue
   for seg in lines(line.difference(Point(*s['entry_world']).buffer(2.4))):
    if seg.length<1.3:continue
    aa=np.array(seg.coords[0]);bb=np.array(seg.coords[-1]);t=(bb-aa)/np.linalg.norm(bb-aa);n=np.array([-t[1],t[0]]);mid=(aa+bb)/2
    if not sales.covers(Point(*(mid+n*.12))):n=-n
    edges.append({'a':aa.tolist(),'b':bb.tolist(),'inward':n.tolist(),'length_m':float(np.linalg.norm(bb-aa))})
 edges.sort(key=lambda e:e['length_m'],reverse=True)
 route=LineString([(q[0],q[2])for q in s['main_route_world']]);centres=[];forward=np.array(dirs[s['id']])[[0,2]];side=np.array([forward[1],-forward[0]])
 for fraction in[.32,.67]:
  point=route.interpolate(fraction,normalized=True);q=np.array([point.x,point.y]);axis=forward if cat in['book','cafe','restaurant']else side;scale=1.
  if not sales.covers(LineString([q-axis*1.34,q+axis*1.34]).buffer(.03)):scale=.65
  if sales.covers(LineString([q-axis*1.34*scale,q+axis*1.34*scale]).buffer(.03)):centres.append({'p':[float(q[0]),s['height'],float(q[1])],'axis':axis.tolist(),'scale_x':scale})
 rows.append({**d,'wall_colour':wall,'accent_colour':accent,'floor_type':kind,'floor_colour':floor,'floor_roughness':rough,'light_colour':light,'floor_triangles':triangles,'wall_candidates':edges[:10],'ceiling_units':centres,'poster_uv':[x/3072,y/3840,512/3072,768/3840],'poster_texture':'res://assets/v24/art/store-editorial-atlas.png','floor_level':s['height'],'entry':s['entry_world'],'backroom':s['backroom_world'],'no_collision_added':True,'floor_is_finish_not_new_structural_slab':True})
atlas.save(P/'assets/v24/art/store-editorial-atlas.png',optimize=True);write(P/'source/v24/store-finishes.json',rows)
release=P/'source/v24/finish-release.json'
if not release.exists():write(release,{'enabled_store_ids':[d['id']for d in focus if d['stage']=='pilot'],'scope':'Pilot visual review before deployment to other stores'})
print('STORE_DESIGN',len(rows),'floor triangles',sum(len(x['floor_triangles'])for x in rows),'poster atlas',atlas.size)
