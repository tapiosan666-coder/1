"""Run after v24_assets: genuine product supports and table service, no NPC assets."""
from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from v24_blender_common import *
B=json.loads((P/'source/v24/model-bounds.json').read_text());C=json.loads((P/'source/v24/product-catalog.json').read_text());ceramic=material('V24_service_porcelain',(.82,.80,.73),.34);soup=material('V24_roasted_soup',(.52,.23,.06),.45);leaf=material('V24_herb',(.14,.29,.07),.76)
def done(name,category,role):
 bpy.context.view_layer.update();pts=[o.matrix_world@Vector(c)for o in bpy.context.scene.objects if o.type in['MESH','CURVE']for c in o.bound_box];lo=[min(q[i]for q in pts)for i in range(3)];hi=[max(q[i]for q in pts)for i in range(3)];B[name]={'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]]};C[name]={'category':category,'role':role,'source':'Original v24 display supports and service geometry'};finish(name)
for typ in['electric_bass','ukulele','acoustic_guitar']:
 name='sku_v24_'+typ;bpy.ops.import_scene.gltf(filepath=str(P/f'assets/v24/models/{name}.glb'));scale=.72 if typ=='ukulele'else 1.
 box('Display_stand_base',(0,.02,.008),(.27*scale,.22*scale,.016),metal,.008)
 for side in[-1,1]:
  tube('Padded_rest',[(side*.10*scale,-.035,.015),(side*.10*scale,-.052,.042),(side*.10*scale,-.028,.066)],.009,metal)
  tube('A_frame',[(side*.11*scale,.075,.015),(side*.052*scale,.075,.38*scale),(side*.06*scale,.05,.43*scale)],.008,metal)
 done(name,'music','Dedicated '+typ+' with frets/strings and visible padded adjustable display stand')
bpy.ops.import_scene.gltf(filepath=str(P/'assets/v24/models/sku_v24_croissant.glb'))
for o in bpy.context.scene.objects:
 if o.parent is None:o.location.z+=.016
lathe('Pastry_plate',[(0,0),(.08,0),(.12,.010),(.12,.018),(.108,.021),(.075,.015),(0,.015)],ceramic);box('Folded_napkin',(.03,.075,.008),(.13,.10,.008),fabrics[0],.003);done('sku_v24_pastry_service','dining','Croissant served on a real plate with folded napkin')
lathe('Soup_bowl',[(.035,0),(.055,.012),(.085,.055),(.086,.075),(.078,.076),(.071,.061)],ceramic);lathe('Soup_surface',[(0,.061),(.071,.061)],soup)
for x,y in[(-.02,-.01),(.018,.024),(.03,-.02)]:
 tube('Herbs',[(x,y,.062),(x+.01,y+.006,.064)],.002,leaf)
lathe('Underplate',[(0,0),(.095,0),(.115,.006),(.115,.012),(.085,.014),(0,.01)],ceramic);done('sku_v24_soup_service','dining','Bowl, soup, herbs and underplate rather than a repeated cup')
(P/'source/v24/model-bounds.json').write_text(json.dumps(B,indent=2));(P/'source/v24/product-catalog.json').write_text(json.dumps(C,ensure_ascii=False,indent=2))
