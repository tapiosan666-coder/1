"""Original fictional brand identities, exported as one shared in-game atlas.

Uses only the bundled Noto font and vector drawing. No real logos or photos.
"""
import json
import math
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
FONT=ROOT/'assets/fonts/NotoSansCJKjp-Regular.otf'
GROUND=['紙とことば','SILHOUETTE','STEP','常緑生活','AKARI','喫茶 ひと休み','ROOM & FORM','暮らしの道具','FIELD']
# Storefronts outside the repeated specialist units, plus their secondary boards.
# Positions use the same logical plan as the baked world. No geometry is moved.
EXTRA_BOARDS=[
 dict(id='a_market',text='LIFE MARKET  /  食品スーパー',brand='LIFE MARKET',at=[24,4.0,8.2],yaw=180,width=9.6),
 dict(id='a_market_rear',outlet='a_market',text='毎日の食卓に  /  FOOD & DAILY',brand='LIFE MARKET',at=[24,3.0,47.7],yaw=0,width=9.6),
 dict(id='a_reading',outlet='a_0_0_-1',text='紙とことば  /  READING LOUNGE',brand='紙とことば',at=[-81,2.9,-35.7],yaw=0,width=8.8),
]
for i,(x,name) in enumerate(zip([-75,-57,-39,-21,-3,15,33],['焼きたてパン','和のおかず','お弁当','サラダ・惣菜','果物とジュース','お茶と菓子','毎日の食卓'])):
    EXTRA_BOARDS.append(dict(id=f'a_basement_{i}',text=name,brand=name,at=[x,-2.35,-23.4],yaw=0,width=8.0))
for i,(x,name) in enumerate(zip([51,62,73,84],['麦とだし','食堂 まいにち','スパイスの庭','こもれび珈琲'])):
    EXTRA_BOARDS.append(dict(id=f'a_food_{i}',text=name,brand=name,at=[x,3.9,-59.6],yaw=0,width=4.4,replace_label=False))
for level,(height,name) in enumerate(zip([0,5.525,10.875],['デジタルスクエア / 家電','ホーム＆リビング','シネマ・星あかり'])):
    EXTRA_BOARDS.append(dict(id=f'b_anchor_{level}',text=name,brand=name.split(' / ')[0],at=[-373.8,height+4.15,0],yaw=90,width=12.8))
for ident,at,yaw,width,text in [
 ('food_garden_left',[60.24,2.9,-20],90,6.0,'FOOD GARDEN'),
 ('food_garden_right',[79.76,2.9,-20],-90,6.0,'FOOD GARDEN'),
 ('food_garden_entry',[70,3.75,-8.41],0,6.2,'FOOD GARDEN　/　フードコート'),
]:
    EXTRA_BOARDS.append(dict(id=ident,outlet='',text=text,brand='FOOD GARDEN',at=at,yaw=yaw,width=width))
DESCRIPTIONS={
 '紙とことば':'BOOKS / STATIONERY', 'SILHOUETTE':'STYLE FOR EVERYDAY', 'STEP':'FOOTWEAR / SELECT',
 '常緑生活':'GREEN / HOME / LIVING','AKARI':'SMART LIFE / ELECTRONICS','喫茶 ひと休み':'COFFEE / TEA / BAKERY',
 'ROOM & FORM':'FURNITURE / INTERIOR','暮らしの道具':'TOOLS FOR DAILY LIFE','FIELD':'SPORTS / OUTDOOR',
 'KITCHEN LAB':'TOOLS FOR EVERYDAY COOKING','LUMI':'BEAUTY / COSMETICS / CARE','NOVA':'NEW FORMS / EVERYDAY WEAR',
 'FRAME':'OPTICAL / EYEWEAR','ORBIT':'TRAVEL / BAGS / GOODS','ROOM':'BED / LINEN / LIVING','AURA':'JEWELRY / ACCESSORIES',
 'STUDIO':'MENSWEAR / ESSENTIALS','SELECT':'ACCESSORIES / DAILY SELECT','MELLOW':'COFFEE / SLOW MOMENTS','FOCUS':'DESIGN / DIGITAL LIFE',
 'COLOR':'ART MATERIALS / STATIONERY','KIDS CLOSET':'SMALL CLOTHES / BIG DAYS','BLOCK':'TOYS / PLAY / DISCOVER',
 'HOBBY BASE':'MODEL / CRAFT / COLLECT','SOUND':'INSTRUMENTS / SOUND STUDIO','PLAY':'ARCADE / GAMES','ACTIVE':'SPORTS / MOVEMENT',
 'STORY':'BOOKS FOR LITTLE READERS','TRAIL':'OUTDOOR / NEW PATHS','JOURNEY':'TRAVEL / NEW HORIZONS','SWEET':'DESSERT / CAFE','CAMPUS':'WRITE / DRAW / CREATE',
 'CLOSET':'FASHION / EVERYDAY STYLE','DIGITAL':'ELECTRONICS / NEW LIVING','LIVING':'HOME / INTERIOR SELECT','WALK':'SHOES / BAGS',
 '日々の道具':'GOOD TOOLS / GOOD DAYS','ページの庭':'BOOKS / CULTURE / STATIONERY','喫茶 リズム':'COFFEE / RELAX / REPEAT',
 '木かげの喫茶':'TERRACE / COFFEE / REST','日々の服':'CLOTHING / EVERYDAY','ホーム・セレクト':'HOME / SELECTED GOODS',
 'LIFE MARKET':'食品・日用品 / FRESH & DAILY','焼きたてパン':'焼きたての香りを、毎日。 / BAKERY',
 '和のおかず':'旬の味わい、手づくり惣菜','お弁当':'お昼のひと箱 / BENTO & DELI','サラダ・惣菜':'彩り野菜 / SALAD & DELI',
 '果物とジュース':'しぼりたて / FRUIT & JUICE','お茶と菓子':'一服の時間 / TEA & SWEETS','毎日の食卓':'おいしい日常 / DAILY FOOD',
 '麦とだし':'うどん・そば / NOODLE KITCHEN','食堂 まいにち':'定食・ごはん / DAILY DINING','スパイスの庭':'香るカレーとサラダ',
 'こもれび珈琲':'珈琲・軽食 / COFFEE & REST','デジタルスクエア':'家電・デジタル / ELECTRONICS',
 'ホーム＆リビング':'家具・インテリア / HOME & LIVING','シネマ・星あかり':'映画のある時間 / CINEMA','FOOD GARDEN':'フードコート / EAT & RELAX'
}

def identity(name):
    if name=='シネマ・星あかり':return ('#20283f','#f7ecd2','#c8a763','star',4)
    if name in ['焼きたてパン','お弁当','和のおかず','食堂 まいにち','麦とだし']:
        return ('#704e38','#fff2d8','#d7b276','wheat' if name=='焼きたてパン' else 'bowl',4)
    if name in ['果物とジュース','スパイスの庭']:return ('#a46438','#fff2d8','#e6cc79','fruit',4)
    if name in ['お茶と菓子','こもれび珈琲']:return ('#46604c','#f6efdc','#d6c18a','cup',4)
    if name in ['LIFE MARKET','サラダ・惣菜','毎日の食卓','FOOD GARDEN']:return ('#345d4d','#f8f1da','#d8b777','leaf',4)
    if name=='デジタルスクエア':return ('#202936','#f4efe0','#d8b478','grid',4)
    if name in ['LUMI','AURA','SELECT']:
        return ('#f2e7e1','#634653','#b48b62','flower' if name=='LUMI' else 'diamond',6)
    if name in ['SOUND','PLAY','HOBBY BASE','DIGITAL','FOCUS','AKARI']:
        return ('#202936','#f4efe0','#d8b478','sound' if name=='SOUND' else 'grid',4)
    if name in ['KIDS CLOSET','BLOCK','COLOR','CAMPUS','STORY']:
        return ('#f3edda','#455b55','#c77958','blocks' if name in ['BLOCK','KIDS CLOSET'] else 'book',3)
    if name in ['FIELD','ACTIVE','TRAIL','常緑生活','木かげの喫茶']:
        return ('#334f45','#f0e9d7','#b7c49a','leaf',6)
    if name in ['NOVA','STUDIO','SILHOUETTE','CLOSET','日々の服']:
        return ('#eeeae2','#292c31','#8f7960','monogram',8)
    if name in ['FRAME','STEP','WALK']:
        return ('#dce9e7','#294744','#8fa89c','glasses' if name=='FRAME' else 'chevron',7)
    if name in ['ORBIT','JOURNEY']:
        return ('#2d3a50','#f5edde','#c4a271','orbit',6)
    if name in ['MELLOW','SWEET','喫茶 ひと休み','喫茶 リズム']:
        return ('#755746','#fcf1d9','#e2c190','cup',3)
    if name in ['紙とことば','ページの庭']:
        return ('#f4efe0','#425347','#b59b68','book',4)
    return ('#e6deca','#4d544d','#a68658','home',4)

def emblem(draw,cx,cy,motif,ink,accent,letter):
    draw.ellipse((cx-43,cy-43,cx+43,cy+43),outline=accent,width=2)
    if motif=='star':
        points=[(cx+math.sin(i*math.pi/5)*(31 if i%2==0 else 13),cy-math.cos(i*math.pi/5)*(31 if i%2==0 else 13)) for i in range(10)]
        draw.polygon(points,fill=ink)
    elif motif=='wheat':
        draw.line([(cx,cy+31),(cx,cy-30)],fill=accent,width=3)
        for y in [-19,-3,13]:
            draw.ellipse((cx-22,cy+y-14,cx-2,cy+y+1),fill=ink)
            draw.ellipse((cx+2,cy+y-20,cx+22,cy+y-5),fill=ink)
    elif motif=='fruit':
        draw.ellipse((cx-27,cy-15,cx+27,cy+30),outline=ink,width=4)
        draw.line([(cx,cy-16),(cx+5,cy-30)],fill=accent,width=3)
        draw.ellipse((cx+5,cy-33,cx+25,cy-22),fill=ink)
    elif motif=='bowl':
        draw.arc((cx-28,cy-13,cx+28,cy+31),0,180,fill=ink,width=4)
        draw.line([(cx-29,cy+7),(cx+29,cy+7)],fill=ink,width=3)
        draw.line([(cx-11,cy+30),(cx+11,cy+30)],fill=accent,width=3)
        for x in [-13,0,13]:draw.arc((cx+x-5,cy-29,cx+x+6,cy),80,240,fill=ink,width=2)
    elif motif=='sound':
        for i,h in enumerate([22,47,65,38,18]):
            x=cx-28+i*14;draw.rounded_rectangle((x,cy-h/2,x+6,cy+h/2),3,fill=ink)
    elif motif=='flower':
        for dx,dy in [(-14,0),(14,0),(0,-14),(0,14)]:
            draw.ellipse((cx+dx-14,cy+dy-14,cx+dx+14,cy+dy+14),outline=ink,width=3)
        draw.ellipse((cx-5,cy-5,cx+5,cy+5),fill=accent)
    elif motif=='diamond':
        draw.polygon([(cx,cy-31),(cx+30,cy-5),(cx,cy+31),(cx-30,cy-5)],outline=ink,width=3)
        draw.line([(cx-30,cy-5),(cx+30,cy-5)],fill=accent,width=2)
        draw.line([(cx-13,cy-5),(cx,cy+31),(cx+13,cy-5),(cx,cy-31),(cx-13,cy-5)],fill=accent,width=2)
    elif motif=='blocks':
        for x,y,c in [(-25,-24,ink),(3,-24,accent),(-25,5,accent),(3,5,ink)]:
            draw.rounded_rectangle((cx+x,cy+y,cx+x+22,cy+y+22),4,fill=c)
    elif motif=='book':
        draw.line([(cx-29,cy-22),(cx-7,cy-19),(cx,cy-12),(cx+7,cy-19),(cx+29,cy-22),(cx+29,cy+21),(cx+8,cy+23),(cx,cy+29),(cx-8,cy+23),(cx-29,cy+21),(cx-29,cy-22)],fill=ink,width=3)
        draw.line([(cx,cy-10),(cx,cy+25)],fill=accent,width=2)
    elif motif=='leaf':
        pts=[(cx-25,cy+22),(cx-25,cy-8),(cx-13,cy-25),(cx+26,cy-28),(cx+25,cy+9),(cx+8,cy+24)]
        draw.polygon(pts,fill=ink);draw.line([(cx-23,cy+25),(cx+20,cy-20)],fill=accent,width=3)
    elif motif=='glasses':
        for dx in [-19,19]:draw.rounded_rectangle((cx+dx-17,cy-12,cx+dx+17,cy+12),8,outline=ink,width=4)
        draw.line([(cx-3,cy-6),(cx+3,cy-6)],fill=ink,width=4)
    elif motif=='chevron':
        for dx in [-15,7]:draw.line([(cx+dx-12,cy-25),(cx+dx+12,cy),(cx+dx-12,cy+25)],fill=ink if dx<0 else accent,width=6)
    elif motif=='orbit':
        draw.ellipse((cx-29,cy-16,cx+29,cy+16),outline=ink,width=3)
        draw.ellipse((cx-16,cy-29,cx+16,cy+29),outline=accent,width=3)
        draw.ellipse((cx+18,cy-19,cx+30,cy-7),fill=ink)
    elif motif=='cup':
        draw.rounded_rectangle((cx-24,cy-12,cx+17,cy+20),6,outline=ink,width=3)
        draw.arc((cx+9,cy-8,cx+33,cy+12),-90,90,fill=ink,width=3)
        draw.line([(cx-27,cy+27),(cx+27,cy+27)],fill=accent,width=3)
        for x in [-12,1,13]:draw.arc((cx+x-6,cy-34,cx+x+5,cy-14),80,240,fill=ink,width=2)
    elif motif=='monogram':
        if letter=='N':draw.line([(cx-23,cy+27),(cx-23,cy-27),(cx+23,cy+27),(cx+23,cy-27)],fill=ink,width=6)
        else:draw.text((cx,cy),letter,font=ImageFont.truetype(str(FONT),54),anchor='mm',fill=ink)
        draw.line([(cx-30,cy+32),(cx+30,cy+32)],fill=accent,width=2)
    elif motif=='grid':
        for y in range(3):
            for x in range(3):
                if (x,y)==(2,0):continue
                draw.rectangle((cx-25+x*20,cy-25+y*20,cx-12+x*20,cy-12+y*20),fill=accent if x==y else ink)
    else:
        draw.line([(cx-29,cy),(cx,cy-27),(cx+29,cy),(cx+22,cy),(cx+22,cy+25),(cx-22,cy+25),(cx-22,cy),(cx-29,cy)],fill=ink,width=3)

def tracked(draw,at,text,font,spacing,ink):
    x,y=at
    for letter in text:
        draw.text((x,y),letter,font=font,fill=ink,stroke_width=0)
        x+=draw.textlength(letter,font=font)+spacing

def build():
    upper=(ROOT/'scripts/tenant_catalog.gd').read_text().split('const THEMES')[0]
    names=GROUND+re.findall(r'\["([^"]+)","[^\"]+"\]',upper)
    for file in ['b_wing.gd','c_wing.gd']:
        names+=re.findall(r'"name":"([^"]+)"',(ROOT/'scripts'/file).read_text())
    brands=list(dict.fromkeys(name.split(' / ')[0] for name in names))
    aliases={name:brands.index(name.split(' / ')[0]) for name in names}
    for board in EXTRA_BOARDS:
        if board['brand'] not in brands:brands.append(board['brand'])
        aliases[board['text']]=brands.index(board['brand'])
    cols=4;cw,ch=1024,128;rows=math.ceil(len(brands)/cols)
    atlas=Image.new('RGB',(cols*cw,rows*ch),'#e7e1d6')
    for index,name in enumerate(brands):
        bg,ink,accent,motif,spacing=identity(name)
        card=Image.new('RGB',(cw,ch),bg);d=ImageDraw.Draw(card)
        d.line([(18,14),(18,ch-14)],fill=accent,width=5)
        d.line([(155,20),(155,ch-20)],fill=accent,width=1)
        d.line([(185,120),(cw-45,120)],fill=accent,width=1)
        emblem(d,88,64,motif,ink,accent,name[0])
        size=72
        while size>34:
            font=ImageFont.truetype(str(FONT),size)
            if d.textlength(name,font=font)+(len(name)-1)*spacing<770:break
            size-=2
        tracked(d,(190,-2+(72-size)/2),name,font,spacing,ink)
        subtitle=DESCRIPTIONS.get(name,'SELECTED GOODS / EVERYDAY LIFE')
        tracked(d,(193,91),subtitle,ImageFont.truetype(str(FONT),17),2,ink)
        d.rectangle((cw-30,23,cw-22,31),fill=accent)
        atlas.paste(card,((index%cols)*cw,(index//cols)*ch))
    atlas.save(ROOT/'assets/retail/store_signs.png',optimize=True)
    payload={'columns':cols,'rows':rows,'cell':[cw,ch],'ground_names':GROUND,'brands':brands,'aliases':aliases,'additional_boards':EXTRA_BOARDS}
    generated='class_name StoreSignCatalog\nextends RefCounted\n## Generated by tools/build_store_signs.py; original fictional brand identities.\n'
    generated+='const DATA := '+json.dumps(payload,ensure_ascii=False,indent=2)+'\n'
    (ROOT/'scripts/store_sign_catalog.gd').write_text(generated)
    print(f'Created {len(brands)} designed brand signs, {len(aliases)} aliases, {atlas.size}.')

if __name__=='__main__':build()
