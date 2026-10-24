"""Export review drawings from the proposed B-wing study; never edits game assets.

Optional developer dependency: Pillow. Run from any directory with Python.
"""
import html
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "docs/mall-b-floor-study.json").read_text())
OUT = ROOT / "docs/images"
FONT = ROOT / "assets/fonts/NotoSansCJKjp-Regular.otf"


class Drawing:
    def __init__(self, width, height):
        self.image = Image.new("RGB", (width, height), "#f5f7f9")
        self.draw = ImageDraw.Draw(self.image)
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><rect width="100%" height="100%" fill="#f5f7f9"/>']

    def text(self, xy, text, size=20, color="#243746"):
        font = ImageFont.truetype(str(FONT), size)
        for i, row in enumerate(text.split("\n")):
            x, y = xy[0], xy[1] + i * (size + 5)
            self.draw.text((x, y), row, font=font, fill=color)
            self.svg.append(f'<text x="{x}" y="{y+size}" font-family="Noto Sans CJK JP,sans-serif" font-size="{size}" fill="{color}">{html.escape(row)}</text>')

    def polygon(self, points, fill, outline=None):
        self.draw.polygon(points, fill=fill, outline=outline)
        pairs = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        self.svg.append(f'<polygon points="{pairs}" fill="{fill}" stroke="{outline or fill}"/>')

    def box(self, xy, fill, outline=None):
        x, y, x2, y2 = xy
        self.polygon([(x,y),(x2,y),(x2,y2),(x,y2)], fill, outline)

    def line(self, points, color, width=2):
        self.draw.line(points, fill=color, width=max(1, round(width)), joint="curve")
        pairs = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        self.svg.append(f'<polyline points="{pairs}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"/>')

    def ellipse(self, xy, fill, outline=None):
        self.draw.ellipse(xy, fill=fill, outline=outline, width=2)
        x, y, x2, y2 = xy
        self.svg.append(f'<ellipse cx="{(x+x2)/2}" cy="{(y+y2)/2}" rx="{(x2-x)/2}" ry="{(y2-y)/2}" fill="{fill}" stroke="{outline or fill}"/>')

    def dim(self, a, b, label, label_xy):
        self.line([a, b], "#435c70")
        dx, dy = b[0]-a[0], b[1]-a[1]
        length = math.hypot(dx, dy)
        nx, ny = -dy / length * 6, dx / length * 6
        for x, y in [a, b]: self.line([(x-nx,y-ny),(x+nx,y+ny)], "#435c70")
        self.text(label_xy, label, 18)

    def save(self, name):
        OUT.mkdir(exist_ok=True)
        self.image.save(OUT / f"{name}.png")
        (OUT / f"{name}.svg").write_text("\n".join(self.svg + ["</svg>"]))


def plan():
    d = Drawing(1500, 1120)
    d.text((45,20), "B館1F：広場と分岐を組み合わせる平面案", 34)
    d.text((45,75), "設計検討用・未実装 ／ 寸法はゲーム用の仮設定。実在施設の実測図ではありません。", 20)
    scale = 3.8
    def p(xy): return 130 + xy[0] * scale, 160 + xy[1] * scale
    d.polygon([p(x) for x in DATA["boundary"]], "#e7e3da", "#738089")
    for tenant in DATA["tenants"]:
        d.polygon([p(x) for x in tenant["polygon"]], "#81b3d1" if tenant["kind"] == "anchor" else "#c4d9e4", "#ffffff")
    for path in DATA["paths"]:
        points = [p(x) for x in path["points"]]
        d.line(points, "#fffdf7", path["width"] * scale)
        for point in points:
            r = path["width"] * scale / 2
            d.ellipse((point[0]-r,point[1]-r,point[0]+r,point[1]+r), "#fffdf7")
    for plaza in DATA["plazas"]:
        x, y = p(plaza["center"]); rx, ry = [r*scale for r in plaza["radius"]]
        d.ellipse((x-rx,y-ry,x+rx,y+ry), "#ecf1cd", "#95a978")
        d.text((x-48,y-15),plaza["label"],18)
    for i, core in enumerate(DATA["cores"]):
        x,y,w,h = core["rect"]; a,b = p((x,y)); c,e = p((x+w,y+h))
        d.box((a,b,c,e),"#b0a9c9","#ffffff")
        d.text((a+7,b+10), f"コア{i+1}", 18)
    label_points = [(16,83),(254,26),(231,153),(89,60),(151,42),(183,27),(119,119),(164,116),(177,87)]
    for tenant, at in zip(DATA["tenants"], label_points):
        text = tenant["label"]
        if tenant["kind"] == "retail": text = text.replace("群 ", "群\n").replace("島 ", "島\n")
        d.text(p(at), text, 18)
    d.text(p((28,169)), "主入口", 18)
    d.text(p((96,101)), "主回廊 10m", 18)
    d.text(p((158,149)), "副回廊 8m", 18)
    d.text(p((214,106)), "8m", 18)
    # Bridge reservation is on 2F; no bridge is drawn as a 1F walkable route.
    for at, label, offset in [((218,8),"2F：A館への橋を接続",(-105,-80)),((111,45),"2F：この区画の一部をC館橋ロビーに",(-260,-85))]:
        x,y = p(at)
        d.line([(x,y),(x+offset[0]+80,y+offset[1]+30)],"#6d66a2",3)
        d.text((x+offset[0],y+offset[1]),label,18,"#60568c")
    d.dim(p((0,188)),p((300,188)),"計画枠 300 m",p((125,190)))
    d.dim(p((-12,0)),p((-12,180)),"180 m",(30,490))
    d.text((45,945), "青：大型店　薄青：専門店の区画群　淡黄：広場　紫：階段・エスカレーター・サービス区画", 20)
    d.text((45,983), "コアの計画枠は18×14m。店の区画群は今後分割し、レジ・試着室・倉庫を個別設計します。", 20)
    d.text((45,1021), "白：公開通路。広場・店舗入口で広がる幅を除き、什器設置後の通行幅を確保する設計です。", 20)
    d.text((45,1060), "図はゾーニング案です。出入口・柱・扉・衝突・NPC経路の施工/実装用図面ではありません。", 18)
    d.save("mall-b-floor-study")


def section():
    d = Drawing(1500, 970)
    d.text((45,20), "吹き抜け断面案：1〜3階をつなぐ視線と回廊", 34)
    d.text((45,75), "未実装の計画断面 ／ 既存の床高さを維持して検討。B館「時の広場」を横断する想定。", 20)
    s = DATA["section"]; sx,sy = 17,24
    def p(x,y): return 135+x*sx, 660-y*sy
    d.box((*p(0,s['roof_height']),*p(s['width'],0)),"#ffffff")
    for i,height in enumerate(s["floor_heights"]):
        pieces = [(0,72)] if i == 0 else [(0,24),(48,72)]
        for left,right in pieces:
            a=p(left,height); b=p(right,height-s['slab'])
            d.box((*a,*b),"#a8b1b7")
        for left,right in [(0,18),(54,72)]:
            ceiling = (s['floor_heights'][i+1] if i < 2 else s['roof_height'])-.7
            d.box((*p(left,ceiling),*p(right,height)),"#dce7ee")
        d.text((30,p(0,height)[1]-15),f"{i+1}F",22)
        d.text((1365,p(0,height)[1]-15),f"+{height:g}m",18)
        if i > 0:
            for x in (24,48):
                a=p(x,height); b=p(x,height+s['rail_height'])
                d.line([a,b],"#5990a8",4)
        for x in (21,51):
            # Reference person, drawn identically on each floor for scale.
            a,b=p(x,height)
            d.line([(a,b),(a,b-1.45*sy)],"#42576a",4)
            d.ellipse((a-5,b-1.7*sy,a+5,b-1.3*sy),"#42576a")
    for left,right in [(0,24),(48,72)]:
        d.box((*p(left,s['roof_height']+.35),*p(right,s['roof_height'])),"#a8b1b7")
    d.line([p(24,s['roof_height']+.35),p(48,s['roof_height']+.35)],"#77b1cc",6)
    d.text(p(28,18.5),"採光屋根の計画位置",20)
    d.text(p(28,9),"3層の吹き抜け",24)
    d.text(p(28,7.5),"上階に床を張らない",18)
    for l,r,label in [(0,18,"店舗 18m"),(18,24,"回廊 6m"),(24,48,"開口 24m"),(48,54,"回廊 6m"),(54,72,"店舗 18m")]:
        d.dim(p(l,-2),p(r,-2),label,p(l+.3,-2.3))
    d.dim(p(0,-4),p(72,-4),"横断計画幅 72 m",p(29,-4.3))
    d.text((45,817),"床スラブ0.35m・手すり1.2mは仮設定。柱・梁・防火区画・設備・避難経路は次の詳細設計で検討。",20)
    d.text((45,857),"エスカレーターは図の奥のコアに配置する案。斜路の乗降口と猫の経路を一緒に設計します。",20)
    d.text((45,898),"地下・屋上の用途は別途設計。この断面は商業3層の見え方を確認するための図です。",20)
    d.text((45,938),"水平と鉛直の表示縮尺は異なります。寸法値を参照してください。",18)
    d.save("mall-atrium-section-study")


if __name__ == "__main__":
    plan()
    section()
    print("Exported B-wing floor/atrium review drawings (PNG/SVG).")
