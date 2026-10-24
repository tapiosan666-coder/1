#!/usr/bin/env python3
"""Original fictional shop posters, price cards and screen artwork. No photos."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parents[1]
out = root / 'assets/retail'
out.mkdir(parents=True, exist_ok=True)
font = root / 'assets/fonts/NotoSansCJKjp-Regular.otf'
image = Image.new('RGB', (2048, 2048), '#f0eee6')
draw = ImageDraw.Draw(image)
categories = [
    ('紙と過ごす時間', '新刊・文庫・文具', '文庫と新刊', '880', '#425b59'),
    ('毎日を、心地よく。', '綿のシャツ・日常の服', 'コットンシャツ', '2,980', '#7b6654'),
    ('歩きたくなる一足', '靴と鞄のセレクション', 'デイリーシューズ', '5,980', '#596779'),
    ('小さな暮らしの道具', '器・ボトル・キッチン', 'マグカップ', '1,280', '#65725a'),
    ('暮らしをつなぐ', '音楽・デジタル・家電', 'ワイヤレスヘッドホン', '6,980', '#456c78'),
    ('ひと息、いかがですか', 'COFFEE / TEA / BAKERY', 'ブレンドコーヒー', '420', '#886346'),
    ('部屋に、余白を。', '灯り・布・インテリア', 'デスクライト', '3,980', '#706b5f'),
    ('今日の暮らしを整える', 'タオル・収納・日用品', 'コットンタオル', '680', '#697f7d'),
    ('いつもの先へ', '歩く・走る・出かける', 'スポーツボトル', '1,980', '#666b4c'),
]
for i, (title, subtitle, product, price, color) in enumerate(categories):
    x, y = i % 3 * 512, i // 3 * 512
    draw.rectangle((x+8, y+8, x+503, y+503), fill='#e7e3d7')
    draw.rectangle((x+8, y+8, x+503, y+36), fill=color)
    # Restrained original graphic, rather than a photograph or a real brand ad.
    draw.ellipse((x+105, y+80, x+407, y+382), fill=color)
    draw.rectangle((x+70, y+238, x+441, y+258), fill='#e7e3d7')
    draw.arc((x+135, y+110, x+377, y+352), 10, 320, fill='#d5c8ac', width=10)
    draw.text((x+256,y+390), title, font=ImageFont.truetype(str(font), 27), fill=color, anchor='mt')
    draw.text((x+256,y+442), subtitle, font=ImageFont.truetype(str(font), 17), fill=color, anchor='mt')
    px, py = 1536, i * 128
    draw.rectangle((px+4,py+4,2043,py+123), fill='#f7f4e9')
    draw.text((px+20,py+10), product, font=ImageFont.truetype(str(font),24), fill='#303c3e')
    draw.text((px+20,py+49), '¥'+price, font=ImageFont.truetype(str(font),43), fill=color)
    draw.text((2024,py+91),'税込 / 展示品',font=ImageFont.truetype(str(font),15),fill='#56615b',anchor='rt')
draw.rectangle((1540,1284,2043,1403),fill='#d9c7a4')
draw.text((1792,1310),'FIND MALL',font=ImageFont.truetype(str(font),40),fill='#47584d',anchor='mt')
draw.text((1792,1360),'日々の、いいもの。',font=ImageFont.truetype(str(font),21),fill='#47584d',anchor='mt')
draw.rectangle((1540,1412,2043,1787),fill='#234b59')
draw.rounded_rectangle((1570,1440,2014,1510),radius=12,fill='#aec6c1')
for i in range(3):
    draw.rounded_rectangle((1570+i*150,1550,1690+i*150,1700),radius=10,fill=['#d7c6a5','#80a3a1','#b1bdc4'][i])
draw.text((1580,1725),'暮らしをつなぐ',font=ImageFont.truetype(str(font),25),fill='#e3ede9')
image.save(out / 'shop_atlas.png')
print('shop_atlas.png', (out/'shop_atlas.png').stat().st_size)
