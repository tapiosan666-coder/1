"""Original print graphics for B1's Fernell Coffee and Ovelis Home."""
from math import cos, pi, sin
from pathlib import Path
import random

from PIL import Image, ImageDraw, ImageFont

PROJECT = Path(__file__).resolve().parents[2]
OUT = PROJECT / "assets/v35/b_gallery"
SANS = PROJECT / "assets/NotoSansCJKjp-Regular.otf"
SERIF = "/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf"
PAPER = (240, 228, 204)
INK = (33, 43, 39)
FIR = (37, 59, 50)
CLAY = (183, 106, 72)


def font(size, family=SANS):
    return ImageFont.truetype(str(family), size)


def canvas(width, height, color, seed):
    rng = random.Random(seed)
    im = Image.new("RGB", (width, height))
    im.putdata(
        [
            tuple(max(0, min(255, c + k)) for c in color)
            for k in (rng.choice([-2, -1, -1, 0, 0, 0, 1, 1, 2]) for _ in range(width * height))
        ]
    )
    return im, ImageDraw.Draw(im)


def letterspace(draw, text, x, y, size, color, spacing=3):
    style = font(size)
    for char in text:
        draw.text((round(x), y), char, color, font=style)
        x += style.getlength(char) + spacing


def menu():
    im, d = canvas(1120, 704, FIR, 35)
    d.rounded_rectangle((19, 19, 1101, 685), radius=10, outline=(184, 148, 113), width=2)
    letterspace(d, "FERNELL  /  COFFEE ROASTERY", 64, 50, 23, PAPER, 4)
    d.text((60, 109), "今日のコーヒー", PAPER, font=font(72))
    d.text((64, 225), "豆の個性が際立つ、自家焙煎の一杯。", (219, 204, 171), font=font(29))
    d.line((65, 285, 1054, 285), fill=(155, 141, 108), width=2)
    groups = (
        (65, "BREW  /  コーヒー", [("季節のハンドドリップ", "¥ 580"), ("カフェラテ", "¥ 620"), ("水出しコーヒー", "¥ 600")]),
        (596, "BAKED  /  焼 き 菓 子", [("発酵バターのスコーン", "¥ 420"), ("胡桃のキャロットケーキ", "¥ 510"), ("カカオのフィナンシェ", "¥ 320")]),
    )
    for x, title, rows in groups:
        letterspace(d, title, x, 322, 22, (229, 176, 128), 2)
        for i, (item, price) in enumerate(rows):
            y = 383 + 58 * i
            d.text((x, y), item, PAPER, font=font(27))
            d.text((x + 375, y + 4), price, PAPER, font=font(23), anchor="rt")
    d.line((65, 586, 1054, 586), fill=(155, 141, 108), width=1)
    d.text((65, 607), "B 1F     FERNELL COFFEE     /     時の広場", (221, 196, 158), font=font(21))
    im.save(OUT / "fernell-menu.png", optimize=True)


def fern():
    im, d = canvas(1120, 672, (231, 211, 177), 91)
    d.rectangle((17, 17, 1102, 653), outline=(184, 147, 118), width=2)
    d.rectangle((661, 17, 1102, 653), fill=(62, 80, 65))
    letterspace(d, "FERNELL  COFFEE", 61, 53, 24, FIR, 4)
    d.text((54, 141), "Slow", fill=FIR, font=font(151, SERIF))
    d.text((120, 290), "roast.", fill=FIR, font=font(151, SERIF))
    d.line((64, 492, 617, 492), (170, 120, 87), width=3)
    d.text((64, 531), "香りからはじまる、午後の休憩。", fill=FIR, font=font(32))
    cup = (872, 368)
    d.ellipse((726, 474, 1039, 518), fill=(37, 52, 42), outline=(199, 152, 108), width=3)
    d.rounded_rectangle((921, 350, 1029, 452), radius=42, fill=(213, 161, 111))
    d.rounded_rectangle((949, 375, 1009, 430), radius=24, fill=(62, 80, 65))
    d.rounded_rectangle((745, 336, 963, 491), radius=48, fill=(220, 177, 126))
    d.ellipse((745, 312, 963, 372), fill=(166, 115, 79), outline=(231, 189, 137), width=5)
    d.ellipse((756, 324, 952, 365), fill=(65, 48, 37), outline=(193, 142, 90), width=3)
    for n in range(6):
        rise = []
        for i in range(80):
            t = i / 79
            rise.append((822 + n * 17 + sin(2*pi*t+.55*n)*(8+17*t), 295 - 169*t + 9*n))
        d.line(rise, fill=(180+n*6, 149+n*6, 117+n*5), width=3)
    d.text((884, 566), "小ロット焙煎", fill=PAPER, font=font(32), anchor="mt")
    im.save(OUT / "fernell-poster.png", optimize=True)


def home():
    im, d = canvas(920, 770, PAPER, 23)
    letterspace(d, "OVELIS HOME    /    MATERIAL LIBRARY", 57, 47, 18, FIR, 2)
    d.text((56, 98), "手に触れるもの", fill=FIR, font=font(63))
    d.text((57, 177), "土、木、釉薬。　素材の手ざわりを、暮らしへ。", fill=INK, font=font(25))
    d.line((58, 232, 860, 232), fill=(148, 126, 97), width=2)
    samples = (
        ("TER RACOTTA".replace(" ", "", 1), (174, 107, 76), (86, 51, 41), "素焼きの土"),
        ("WHITE GLAZE", (219, 213, 193), (94, 121, 111), "白い釉薬"),
        ("DARK STONE", (90, 92, 73), (47, 60, 48), "黒色の石"),
    )
    for i, (name, color, vessel_color, title) in enumerate(samples):
        x = 59 + 269*i
        d.rectangle((x, 289, x+243, 575), fill=color)
        d.ellipse((x+51, 516, x+202, 536), fill=tuple(max(0,k-14) for k in color))
        for row in range(140):
            at = row / 139
            if i == 0:
                half = 49 * sin(pi*min(.93, max(.12, at+.11)))**1.18 + 7
            elif i == 1:
                half = 68 * ((1-at)**.63) + 10
            else:
                half = 39 + 17*sin(pi*at*1.12)
            tone = tuple(min(255,c+round(14*cos(at*6)+6)) for c in vessel_color)
            d.line((x+122-half, 379+row, x+122+half, 379+row), fill=tone, width=2)
        d.ellipse((x+89, 374, x+155, 394), outline=(237, 220, 189), width=2)
        letterspace(d, name, x+3, 601, 17, FIR, 2)
        d.text((x+3, 642), title, fill=INK, font=font(25))
    d.line((58, 700, 860, 700), fill=(148, 126, 97), width=2)
    d.text((58, 719), "器のコレクション　/　B 1F", fill=INK, font=font(20))
    im.save(OUT / "ovelis-materials.png", optimize=True)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    menu()
    fern()
    home()
