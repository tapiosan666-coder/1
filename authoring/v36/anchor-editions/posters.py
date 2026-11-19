"""Compose three original shop-edition print strips from the supplied key-art sheet.

Requires Pillow and the OFL Noto Sans CJK and system DejaVu fonts. Cells are 3:4.
"""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

HEIGHT = 576
WIDTH = 432
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SANS = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

def font(size, japanese=True):
    return ImageFont.truetype(SANS if japanese else SERIF, size, index=0)

def artwork(sheet, col, row):
    w,h=sheet.size
    return sheet.crop((round(w*col/3)+3,round(h*row/2)+3,round(w*(col+1)/3)-3,round(h*(row+1)/2)-3))

def lettering(draw,x,y,value,size,color,japanese=True):
    draw.text((x,y),value,font=font(size,japanese),fill=color,anchor="lt")

def photo(im,size,focus=(.5,.48)):
    return ImageOps.fit(im,size,method=Image.Resampling.LANCZOS,centering=focus)

def frame(fg,bg):
    canvas=Image.new('RGB',(WIDTH,HEIGHT),bg);return canvas,ImageDraw.Draw(canvas)

def cinema(im,idx):
    names=["霧の終着駅","弦の余韻","空をほどく町"]
    english=["THE LAST STATION IN THE MIST","AFTER THE LAST NOTE","A TOWN ABOVE THE TIDE"]
    ink=["#ece1c9","#e8d9ac","#273c47"][idx]
    base=["#253340","#32262a","#f0e6ce"][idx]
    canvas,d=frame(ink,base)
    if idx==0:
        canvas.paste(photo(im,(WIDTH,422),(.5,.52)),(0,0))
        lettering(d,22,437,"CERAVA  FILM  SELECTION",12,ink,False)
        lettering(d,20,469,names[idx],49,ink)
        lettering(d,24,548,english[idx],13,ink,False)
    elif idx==1:
        canvas.paste(photo(im,(344,397),(.48,.36)),(66,34))
        d.line((34,21,34,428),fill=ink,width=1)
        for i,char in enumerate("作品選集"):lettering(d,21,84+i*45,char,25,ink)
        lettering(d,28,452,names[idx],53,ink)
        lettering(d,31,534,english[idx],17,ink,False)
    else:
        lettering(d,25,28,'CERAVA  /  ANIMATION',14,ink,False)
        canvas.paste(photo(im,(388,342),(.47,.51)),(22,67))
        d.line((22,423,410,423),fill="#758888")
        lettering(d,24,442,names[idx],46,ink)
        lettering(d,26,526,english[idx],17,ink,False)
    return canvas

def fashion(im,idx):
    names=['街を歩く服','素材の手ざわり','日々の重ね着']
    bg=['#e7dfd0','#343d3d','#d6d1b9'][idx]
    ink=['#383834','#f3ead4','#343c38'][idx]
    canvas,d=frame(ink,bg)
    if idx==0:
        canvas.paste(photo(im,(WIDTH,397),(.5,.45)),(0,0))
        lettering(d,24,420,'LUMEVA',48,ink,False)
        lettering(d,26,492,names[idx],26,ink)
        d.line((25,540,398,540),fill=ink)
    elif idx==1:
        lettering(d,27,29,'MATERIAL  STUDIES',17,ink,False)
        canvas.paste(photo(im,(375,334),(.45,.4)),(28,84))
        lettering(d,27,441,names[idx],35,ink)
        lettering(d,28,523,'LUMEVA  ROOM',18,ink,False)
    else:
        # Original line drawing of a tailored short jacket and two swatches.
        outline=[(98,140),(141,125),(158,111),(188,121),(216,110),(235,126),(278,141),(319,276),(277,288),(250,211),(254,370),(134,370),(139,212),(113,287),(74,276)]
        d.polygon(outline,fill='#606b65',outline=ink,width=3)
        d.line([(158,113),(173,158),(193,189),(186,363)], fill='#efe8d3',width=3)
        d.line([(215,113),(203,161),(193,189)], fill='#efe8d3',width=3)
        for y in (188,223,258,293):d.ellipse((190,y,196,y+6),fill='#e8d5ab')
        for x in (150,215):d.line((x,285,x+22,282),fill='#e2d9bd',width=3)
        lettering(d,27,32,'LUMEVA    /    CUT & FORM',16,ink,False)
        lettering(d,23,420,names[idx],36,ink)
        lettering(d,25,492,'THE EVERYDAY EDIT',19,ink,False)
    return canvas

def food(im,idx):
    bg=['#203c34','#e9ddbd','#f0dec3'][idx]
    ink=['#f4e9cf','#294534','#5c3028'][idx]
    canvas,d=frame(ink,bg)
    if idx==0:
        canvas.paste(photo(im,(WIDTH,377),(.45,.45)),(0,0))
        lettering(d,24,398,'VELORIA',41,ink,False)
        lettering(d,25,461,'季節の食卓',36,ink)
        lettering(d,26,536,'FRESH   MARKET',16,ink,False)
    elif idx==1:
        lettering(d,23,34,'VELORIA   /   VEGETABLES',14,ink,False)
        for x,y,s in ((163,247,83),(263,217,67),(260,308,62)):
            d.ellipse((x-s,y-s,x+s,y+s),fill='#ae432c',outline=ink,width=3)
            d.arc((x-.67*s,y-.70*s,x+.64*s,y+.64*s),130,248,fill='#d77b4d',width=4)
            d.polygon([(x-2,y-s-8),(x+4,y-s+12),(x+31,y-s+21),(x+6,y-s+25),(x-8,y-s+43),(x-10,y-s+20),(x-32,y-s+14),(x-10,y-s+10)],fill='#536343')
        lettering(d,24,423,'青果の便り',43,ink)
        lettering(d,26,515,'FROM THE PRODUCE AISLE',16,ink,False)
    else:
        d.line((24,67,402,67),fill=ink,width=2)
        lettering(d,24,27,'VELORIA   /   PANTRY',15,ink,False)
        for x,y,rot in [(134,203,-12),(248,258,17),(156,298,-6)]:
            bread=Image.new('RGBA',(181,83));b=ImageDraw.Draw(bread)
            b.rounded_rectangle((4,8,174,73),radius=30,fill='#c5854a',outline='#70472d',width=3)
            for k in range(4):b.arc((29+31*k,16,48+31*k,63),259,86,fill='#f1d4a2',width=5)
            bread=bread.rotate(rot,Image.Resampling.BICUBIC,expand=True);canvas.paste(bread,(x-83,y-38),bread)
        lettering(d,24,424,'焼きたての棚',40,ink)
        lettering(d,26,515,'BREAD & DAILY GOODS',17,ink,False)
    return canvas

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('artwork',type=Path);parser.add_argument('out',type=Path);a=parser.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    with Image.open(a.artwork) as master:
        master=master.convert('RGB')
        for key,func,sources in [('cinema',cinema,[(0,0),(1,0),(2,0)]),('fashion',fashion,[(0,1),(2,1),(2,1)]),('food',food,[(1,1)]*3)]:
            panels=[func(artwork(master,*target),i) for i,target in enumerate(sources)]
            strip=Image.new('RGB',(3*WIDTH,HEIGHT))
            for i,img in enumerate(panels):strip.paste(img,(i*WIDTH,0))
            strip.save(a.out/(key+'.webp'),quality=91,method=4)
if __name__=='__main__':main()
