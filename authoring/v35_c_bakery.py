from argparse import ArgumentParser
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

args = ArgumentParser()
args.add_argument("--font-directory", type=Path, default=Path("/usr/share/fonts/opentype/noto"))
settings = args.parse_args()
project = Path(__file__).resolve().parents[1]
destination = project / "assets/v35/c/lumeva-menu.jpg"
canvas = Image.new("RGB", (1800, 510), "#ede4d4")
draw = ImageDraw.Draw(canvas)
font_root = settings.font_directory
gothic = font_root / "NotoSansCJK-Regular.ttc"
serif = font_root / "NotoSerifCJK-Bold.ttc"

def typeset(x, y, value, size, font=gothic, ink="#292e26"):
    draw.text((x, y), value, font=ImageFont.truetype(str(font), size, index=0), fill=ink)

draw.rectangle((0, 0, 1799, 104), fill="#2b4339")
typeset(40, 21, "LUMEVA TABLE", 46, serif, "#fff1d9")
typeset(1338, 30, "BAKED DAILY · C館1F", 29, gothic, "#f1d6ae")
source = Image.open(project / "assets/v17/photos/campaign_cafe.jpg").convert("RGB")
canvas.paste(ImageOps.fit(source, (455, 377), centering=(.51, .56)), (25, 117))
groups = [
    ("パンと焼菓子", "FROM THE OVEN", ("発酵バターのクロワッサン", "全粒粉のカンパーニュ", "季節のタルト")),
    ("珈琲と紅茶", "COFFEE & TEA", ("ルメヴァ ブレンド", "カフェラテ", "アールグレイ")),
    ("軽食", "LIGHT FARE", ("焼きたてパンのセット", "本日のスープ", "フルーツヨーグルト")),
]
for i, group in enumerate(groups):
    x = 527 + i * 415
    title, caption, entries = group
    draw.line((x, 198, x + 359, 198), fill="#ac8664", width=2)
    typeset(x, 121, title, 36, serif)
    typeset(x, 174, caption, 17, gothic, "#795342")
    for line, value in enumerate(entries):
        y = 228 + line * 57
        draw.rounded_rectangle((x, y + 14, x + 8, y + 22), radius=2, fill="#936146")
        typeset(x + 24, y, value, 22)
    draw.line((x, 424, x + 359, 424), fill="#b69a7d", width=1)
typeset(526, 456, "カウンターでご注文ください", 21)
typeset(1450, 456, "LUMEVA · C WING", 18, serif, "#795342")
canvas.save(destination, quality=95, subsampling=0, optimize=True)

canvas = Image.new("RGB", (1460, 520), "#263e35")
draw = ImageDraw.Draw(canvas)
ink = "#e9cca0"
draw.rounded_rectangle((30, 28, 1429, 491), radius=36, outline="#bda17d", width=3)
# The grain emblem is an original drawing for the fictional café.
draw.arc((76, 102, 390, 415), 0, 360, fill=ink, width=4)
draw.line([(240, 359), (235, 255), (238, 157)], fill=ink, width=4)
for x, y, sign in [(238,306,1), (236,267,-1), (237,232,1), (236,195,-1)]:
    draw.line([(x,y), (x + sign * 27,y-18), (x + sign * 49,y-50), (x + sign*25,y-43), (x,y)], fill=ink, width=4)
typeset(451, 130, "窯から、テーブルへ。", 75, serif, "#f6ead4")
draw.line((460, 268, 1333, 268), fill="#b49a77", width=2)
typeset(461, 291, "LUMEVA TABLE", 66, serif, "#e9cca0")
typeset(462, 385, "BAKERY   ·   COFFEE   ·   OUTLET TERRACE", 26, gothic, "#e2caa5")
canvas.save(destination.with_name("lumeva-wall.jpg"), quality=95, subsampling=0, optimize=True)
