#!/usr/bin/env python3
"""Draw exported full-floor map definitions. Pillow only; not a gameplay screenshot."""
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
font=ImageFont.truetype(str(ROOT/'assets/fonts/NotoSansCJKjp-Regular.otf'),17)
small=ImageFont.truetype(str(ROOT/'assets/fonts/NotoSansCJKjp-Regular.otf'),13)
for f in json.loads((ROOT/'docs/structure-floor-plans.json').read_text()):
    points=[p for poly in f['base'] for p in poly]+[p for packet in f['structure'] for p in packet['outer']]
    xs=[p[0] for p in points];ys=[p[1] for p in points];x0,x1,y0,y1=min(xs),max(xs),min(ys),max(ys)
    k=min(1100/(x1-x0),620/(y1-y0));im=Image.new('RGB',(1200,760),'#14272d');dr=ImageDraw.Draw(im)
    def xy(p):return (round(45+(p[0]-x0)*k),round(65+(p[1]-y0)*k))
    for poly in f['base']:dr.polygon([xy(p) for p in poly],fill='#c2ccc0')
    for packet in f['structure']:
        dr.polygon([xy(p) for p in packet['outer']],fill='#c2ccc0',outline='#eef2e9')
        for poly in packet['holes']:dr.polygon([xy(p) for p in poly],fill='#14272d')
    if 'private' in f:dr.polygon([xy(p) for p in f['private']],fill='#33474b')
    for shop in f['shops']:dr.polygon([xy(p) for p in shop['polygon']],fill='#607d88',outline='#eef2e9')
    for p in f['plazas']:dr.text(xy(p['at']),p['name'],font=small,fill='#e1b77f',anchor='mm',stroke_width=1,stroke_fill='#14272d')
    title=f"{f['building']}館 {f['level']+1}F / ゲームの床・店舗定義から出力（ゲーム画面ではありません）"
    dr.text((35,15),title,font=font,fill='white')
    dr.text((35,722),'灰緑：床　青：売場　濃色：開口・屋外・非公開区画　／　実施設の実測図ではありません',font=small,fill='#c8d6cc')
    im.save(ROOT/f"docs/images/mall20-{f['building'].lower()}-{f['level']+1}f.png")
