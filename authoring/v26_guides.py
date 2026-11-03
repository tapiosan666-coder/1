"""Original floor-guide artwork derived from the retained v25 store/map records."""
from pathlib import Path
import json, zstandard, hashlib
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/v26'
OUT.mkdir(parents=True,exist_ok=True)
def read(name):
    p=ROOT/name
    if p.exists():return json.loads(p.read_text())
    return json.loads(zstandard.ZstdDecompressor().decompress(Path(str(p)+'.zst').read_bytes()[8:]))
stores=read('source/v25/retail-plan.json')['stores']
maps=read('source/v22/map-data-integrated.json')
way=read('source/v22/wayfinding.json')['combined']
fontfile=str(ROOT/'assets/NotoSansCJKjp-Regular.otf')
font=lambda size:ImageFont.truetype(fontfile,size)
audit=[]
metadata={}
def polygon_coords(g):
    if g['type']=='Polygon':return [g['coordinates']]
    if g['type']=='MultiPolygon':return g['coordinates']
    if g['type']=='GeometryCollection':return [p for child in g['geometries']for p in polygon_coords(child)]
    return []
for wing,accent in [('A','#376573'),('B','#926343'),('C','#52745e')]:
    im=Image.new('RGB',(1536,2458),'#eeeae0');d=ImageDraw.Draw(im)
    d.rectangle((0,0,1535,270),fill='#17333e');d.text((84,55),wing+'館  FLOOR GUIDE',font=font(82),fill='white')
    d.text((86,172),'1F  現在地の館・階をご確認ください',font=font(38),fill='#d0dede')
    f=next(f for f in maps if f['wing']==wing and f['label']=='1F')
    lo_x,lo_z,hi_x,hi_z=f['bounds'];lo_x+=429;hi_x+=429;lo_z-=46;hi_z-=46
    bounds=(lo_x,lo_z,hi_x,hi_z)
    scale=min(1310/(hi_x-lo_x),760/(hi_z-lo_z))
    ox=768-(hi_x+lo_x)*.5*scale;oy=760-(hi_z+lo_z)*.5*scale
    def xy(p,local=False):
        return (round(ox+(p[0]+(429 if local else 0))*scale),round(oy+(p[1]-(46 if local else 0))*scale))
    def polygons(rings,fill):
        for polygon in rings:
            d.polygon([xy(p,True) for p in polygon[0]],fill=fill,outline='#8e9994')
            for hole in polygon[1:]:d.polygon([xy(p,True)for p in hole],fill='#eeeae0')
    polygons(f['floor'],'#d5d8cf');polygons(f['public'],'#faf8ef')
    for s in stores:
        if s['wing']!=wing or s['floor']!='1F':continue
        geoms=polygon_coords(s['sales_world'])
        for poly in geoms:d.polygon([xy(p)for p in poly[0]],fill=accent,outline='#eeeae0')
    service_rows=[]
    for board in way:
        if board['wing']!=wing or board['floor']!='1F':continue
        for row in board['rows']:
            if row['kind']not in ['WC','EV','ES','INFO','PARK']:continue
            p=row['target_point'];at=xy(p)
            if row['target_id'] in [r['id']for r in service_rows]:continue
            service_rows.append({'id':row['target_id'],'kind':row['kind'],'p':p})
            x,y=at;d.rounded_rectangle((x-24,y-20,x+24,y+20),radius=5,fill='#17333e');d.text((x,y),row['kind'],anchor='mm',font=font(19),fill='white')
    d.text((100,1150),'■ 専門店  □ 共用通路   WC / EV / ES：実設備位置',font=font(31),fill='#243c41')
    d.text((100,1210),'N ↑  /  地図は北が上    赤い点：現在地',font=font(31),fill=accent)
    d.line((90,1280,1446,1280),fill=accent,width=4)
    for i,label in enumerate(['RF','3F','2F','1F','B1']):
        own=sorted((s for s in stores if s['wing']==wing and s['floor']==label),key=lambda s:s['id'])
        y=1310+i*177
        d.text((95,y),label,font=font(56),fill=accent)
        d.text((290,y+4),f'{len(own)}店舗  /  '+('屋上の店舗・施設'if label=='RF'else'専門店・サービス'),font=font(34),fill='#243c41')
        examples=own[:2]
        for j,s in enumerate(examples):
            msg=s['id']+'  '+s['brand']+'  '+s.get('original_category',s['category'])
            d.text((290,y+56+j*42),msg[:48],font=font(25),fill='#425552')
        audit.append({'wing':wing,'floor':label,'store_count':len(own),'displayed_stores':[{'id':s['id'],'brand':s['brand'],'category':s.get('original_category',s['category'])}for s in examples]})
    d.text((95,2230),'全480店舗と詳細施設は M キーの館内図へ',font=font(34),fill='#17333e')
    d.text((95,2300),'独立検証版 / 実施設の案内・避難図ではありません',font=font(26),fill='#60716c')
    im.save(OUT/f'guide-{wing}.png')
    metadata[wing]={'bounds':bounds,'scale':scale,'offset':[ox,oy],'map_source':'source/v22/map-data-integrated.json','services':service_rows}
(ROOT/'source/v26/guide-metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
(ROOT/'source/v26/guide-store-audit.json').write_text(json.dumps({'rows':audit,'total_store_count':sum(r['store_count']for r in audit),'source_sha256':hashlib.sha256((ROOT/'source/v25/retail-plan.json.zst').read_bytes()).hexdigest(),'invented_stores':False},ensure_ascii=False,indent=2))
print('Generated 3 original guides / 15 floor summaries /',sum(r['store_count']for r in audit),'stores')
