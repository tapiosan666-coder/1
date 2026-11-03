from pathlib import Path
import sys,json
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from v23_blender_common import *
from PIL import Image,ImageDraw,ImageFont
art=P/'assets/v23/art';im=Image.open(art/'retail-editorial-atlas.png').copy();d=ImageDraw.Draw(im);f='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';b='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
for k,title in[(31,'RAY SHIFT 88'),(13,'PHOTO BLOOM'),(7,'撮影 / EDIT / PRINT')]:
 x=k%8*256;y=k//8*512;d.rectangle((x,y,x+255,y+511),fill='#142b3e'if k==31 else'#f0dce0');c='#8de3cc'if k==31 else'#684759';d.text((x+128,y+38),title,font=ImageFont.truetype(b,23),fill=c,anchor='mm')
 if k==31:
  d.polygon([(x+20,y+460),(x+101,y+125),(x+155,y+125),(x+235,y+460)],fill='#475b64');d.line((x+127,y+150,x+127,y+450),fill='#eee9cb',width=4);d.rounded_rectangle((x+98,y+320,x+156,y+415),9,fill='#de9e42');d.text((x+128,y+84),'01 / LAP 02',font=ImageFont.truetype(f,16),fill=c,anchor='mm')
 else:
  d.rounded_rectangle((x+24,y+110,x+231,y+355),18,outline=c,width=5);d.ellipse((x+83,y+146,x+172,y+235),outline=c,width=5);d.arc((x+55,y+215,x+200,y+375),180,360,fill=c,width=5);d.text((x+128,y+416),'ふたりの、今日の記録。',font=ImageFont.truetype(f,15),fill=c,anchor='mm');d.text((x+128,y+470),'ENTRY → PHOTO → EXIT',font=ImageFont.truetype(b,12),fill=c,anchor='mm')
im.save(art/'arcade-original-interface.png',optimize=True)
for model in['fixture_v23_racing_cabinet','fixture_v23_photo_pod']:
 bpy.ops.import_scene.gltf(filepath=str(P/f'assets/v23/models/{model}.glb'))
 for obj in bpy.context.scene.objects:
  if obj.type!='MESH':continue
  for m in obj.data.materials:
   if m is not None and'original_editorial'in m.name:
    for node in m.node_tree.nodes:
     if node.type=='TEX_IMAGE':node.image=bpy.data.images.load(str(art/'arcade-original-interface.png'),check_existing=True)
 finish(model)
