"""Dedicated electronics/mobile and beauty joinery; existing store footprint and merchandise supports retained."""
from pathlib import Path
import sys,json
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from v21_blender_common import *
B=json.loads((P/'source/v21/model-bounds.json').read_text());C=json.loads((P/'source/v21/product-catalog.json').read_text());lacquer=material('FY21_porcelain_joinery',(.82,.84,.82),.28);blue=material('FY21_electronics_edge',(.035,.085,.13),.4,.3);rose=material('FY21_beauty_brushed_rose',(.42,.24,.20),.32,.65);frost=material('FY21_frosted_glass_shelf',(.66,.77,.77),.22,.1)
def save(name,category,role):
 bpy.context.view_layer.update();pts=[o.matrix_world@Vector(c)for o in bpy.context.scene.objects if o.type in['MESH','CURVE']for c in o.bound_box];lo=[min(v[i]for v in pts)for i in range(3)];hi=[max(v[i]for v in pts)for i in range(3)];B[name]={'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]],'unit':'metres'};C[name]={'category':category,'role':role,'source':'Original Blender joinery, no external model or texture','repeated_colour_is_not_a_new_shape':True};finish(name)
for name in['fixture_electronics_counter','fixture_electronics_wall','fixture_beauty_counter','fixture_beauty_wall']:
 beauty='beauty'in name;wall=name.endswith('wall');trim=rose if beauty else blue
 # Recessed continuous plinth and accessible solid demonstration pedestal, rather than a duplicated two-tier timber shelf.
 box('Recessed_pedestal',(0,.02,.065),(1.74,.68,.13),metal,.018);box('Service_cabinet',(0,.04,.435),(1.92,.76,.60),lacquer,.045)
 box('Seam_lined_front',(0,-.348,.435),(1.80,.012,.47),lacquer,.008)
 for x in[-.46,.46]:box('Cabinet_panel_reveal',(x,-.358,.435),(.008,.008,.47),trim,.001)
 for x in[-.70,.70]:tube('Machined_pull',[(x-.08,-.37,.59),(x-.08,-.39,.59),(x+.08,-.39,.59),(x+.08,-.37,.59)],.006,steel)
 box('Demo_worktop',(0,0,.78),(2.0,.88,.055),frost if beauty else stone,.018);tube('Edge_band',[(-.98,-.435,.76),(0,-.438,.76),(.98,-.435,.76)],.008,trim)
 if not beauty:
  for x in[-.60,.60]:lathe('Cable_grommet',[(0,0),(.027,0),(.027,.004),(0,.004)],metal,(x,.25,.808),24)
 if wall:
  box('Back_panel',(0,.37,1.025),(2.0,.065,2.05),lacquer,.025)
  for x in[-.97,.97]:box('Vertical_frame',(x,.31,1.025),(.035,.06,2.05),trim,.008)
  if beauty:
   for z in[.32,.78,1.24,1.70]:
    box('Dedicated_glass_shelf',(0,0,z),(2.0,.88,.055),frost,.012);box('Shelf_back_diffuser',(0,.305,z+.045),(1.85,.015,.018),white,.003)
  else:
   for x in[-.80,-.55,-.30,-.05,.20,.45,.70]:box('Accessory_slat',(x,.326,1.48),(.012,.012,.88),trim,.002)
 save(name,'beauty'if beauty else'electronics','Dedicated glass tester wall/counter'if beauty else'Demonstration cabinet with service reveals, cable ports and accessory panel')
(P/'source/v21/model-bounds.json').write_text(json.dumps(B,indent=2));(P/'source/v21/product-catalog.json').write_text(json.dumps(C,indent=2))
