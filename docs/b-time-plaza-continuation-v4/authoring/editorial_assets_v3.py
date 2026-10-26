from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def build(A):
 im=Image.new('RGB',(2048,1536),'white');d=ImageDraw.Draw(im);font=lambda n:ImageFont.truetype(str(A/'NotoSansCJKjp-Regular.otf'),n)
 labels=[('小説と物語','FICTION / STORIES'),('建築と暮らし','ART / ARCHITECTURE'),('旅と日々','TRAVEL / ESSAYS'),('栞書房','BOOKS / PAPER'),('BOTANICAL NOTES','珈琲と、ひと息。'),('SLOW MORNING','一杯からはじまる日'),('COFFEE / BAKERY','焼きたてと季節の味'),('PICK UP','お受け取りはこちら'),('ATELIER / 07','ESSENTIAL WARDROBE'),('KNIT / LAYERS','素材と重ねる'),('FITTING ROOM','試着室'),('ATELIER / 07','CASH DESK'),('NEW / SELECTED','今月の本'),('READ / REST','本を選ぶ、ひと休み'),('SEASONAL EDIT','秋のワードローブ'),('mellow cafe','COFFEE / BAKERY')]
 for i,(a,b)in enumerate(labels):
  x=(i%4)*512;y=(i//4)*384;bg=[(32,56,53),(214,201,174),(44,52,65),(135,79,56)][i%4];fg=(241,231,203)if i%4!=1 else(50,62,53)
  d.rectangle((x,y,x+511,y+383),fill=bg);d.rectangle((x+18,y+18,x+494,y+366),outline=fg,width=2)
  if i in[4,5,6]:
   for j in range(5):
    xx=x+85+j*70;d.arc((xx-33,y+60,xx+30,y+240),0,180,fill=fg,width=3);d.line((xx,y+230,xx+12,y+100),fill=fg,width=2)
   yy=y+265
  else:yy=y+157
  d.text((x+256,yy),a,font=font(33 if len(a)<15 else 25),fill=fg,anchor='mm');d.text((x+256,yy+60),b,font=font(21),fill=fg,anchor='mm')
  d.text((x+256,y+339),'FIND YOURSELF / TIME COURT',font=font(13),fill=fg,anchor='mm')
 im.save(A/'editorial_v3.png')
if __name__=='__main__':build(P/'assets')
