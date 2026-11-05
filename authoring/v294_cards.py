"""Original fictional retail sample cards, not real product offers."""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
from fontTools.ttLib import TTFont
P=Path(__file__).resolve().parents[1];fontpath=P/'assets/NotoSansCJKjp-Regular.otf';cmap=TTFont(fontpath).getBestCmap()
rows=[('pc14','ノートパソコン','NOTE R14','16GB / 512GB SSD','129,800'),('pc16','ノートパソコン','NOTE R16','32GB / 1TB SSD','159,800'),('tablet','タブレット','PAD T11','128GB / Wi-Fi','54,800'),('phone','スマートフォン','PHONE S6','256GB / OLED','79,800'),('audio1','ヘッドホン','LISTEN C1','LIGHTWEIGHT / WIRELESS','19,800'),('audio2','ヘッドホン','LISTEN C2','RICH BASS / WIRELESS','24,800'),('audio3','ヘッドホン','LISTEN C3','CLEAR VOICE / WIRELESS','29,800'),('speaker','スピーカー','SOUND B2','STEREO / COMPACT','24,800'),('watch','スマートウォッチ','WATCH W1','DAILY / FITNESS','18,800'),('tv1','テレビ','DISPLAY D1','COLOR / HOME CINEMA','129,800'),('tv2','テレビ','DISPLAY D2','LOW REFLECTION','159,800'),('cinema','映像と音の体験','LIVING CINEMA','TV + SOUND + LIVING',''),('kitchen','キッチンと暮らし','KITCHEN LAB','COFFEE / HOME COOKING',''),('work','ワークスペース','WORK AT HOME','DESK / PC / LIGHTING',''),('bread','クロワッサン','BAKERY SELECTION','TERRUNE BAKERY','280'),('tart','フルーツタルト','FRUIT TART','TERRUNE BAKERY','420'),('sandwich','サンドイッチ','SANDWICH','TERRUNE BAKERY','380')]
cols=4;cw,ch=640,320;atlas=Image.new('RGB',(cols*cw,((len(rows)+cols-1)//cols)*ch),'#f4f1e9');D=ImageDraw.Draw(atlas)
def font(n):return ImageFont.truetype(str(fontpath),n)
records={};missing=set()
for i,(key,jp,model,spec,price)in enumerate(rows):
 x=(i%cols)*cw;y=(i//cols)*ch
 missing.update(c for c in jp+'参考価格展示用サンプル円'if ord(c)not in cmap)
 if any(ord(c)not in cmap for c in jp):jp={'tart':'ケーキ'}.get(key,model)
 D.rectangle((x,y,x+cw,y+48),fill='#234647');D.text((x+22,y+7),'TERRUNE  /  BAKERY'if i>=14 else'SUVEL STUDIO  /  DEMO',font=font(22),fill='#f6f2df')
 D.text((x+25,y+62),jp,font=font(35),fill='#183838');D.text((x+25,y+110),model,font=font(25),fill='#435b5c');D.text((x+25,y+152),spec,font=font(23),fill='#536867')
 if price:D.text((x+25,y+191),price+' 円',font=font(49),fill='#9c4d2f');D.text((x+407,y+223),'参考価格',font=font(22),fill='#6f766c')
 D.line((x+25,y+279,x+cw-25,y+279),fill='#b7c4b7',width=2);D.text((x+25,y+287),'展示用サンプル  /  NOT FOR SALE',font=font(18),fill='#63756d')
 records[key]={'label':jp,'model':model,'spec':spec,'reference_price_yen':price,'region':[(i%cols)/cols,(i//cols)/5,1/cols,1/5]}
atlas.save(P/'assets/v294/art/product-cards.png');(P/'source/v294/product-cards.json').write_text(json.dumps({'cards':records,'not_purchase_logic':True,'font_missing_characters_replaced':sorted(missing)},ensure_ascii=False,indent=2));print('cards',len(rows),'missing',missing)
