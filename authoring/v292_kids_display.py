from pathlib import Path
import sys,math,json
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'))
from v292_common import *
sources=set()
def asset(model,x,y,z,height,width):
 path=list(P.glob('assets/v*/models/'+model+'.glb'))[-1];sources.add(str(path.relative_to(P)));before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(path));new=[o for o in bpy.data.objects if o not in before];objs=[o for o in new if o.type=='MESH'];pts=[o.matrix_world@Vector(c)for o in objs for c in o.bound_box];lo=Vector([min(p[i]for p in pts)for i in range(3)]);hi=Vector([max(p[i]for p in pts)for i in range(3)]);k=min(height/(hi.z-lo.z),width/max(hi.x-lo.x,hi.y-lo.y));center=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z));T=Matrix.Translation(Vector((x,y,z)))@Matrix.Scale(k,4)@Matrix.Translation(-center)
 for o in objs:
  m=o.matrix_world.copy();o.parent=None;o.matrix_world=Matrix.Identity(4);o.data.transform(T@m)
 for o in new:
  if o.type!='MESH':bpy.data.objects.remove(o,do_unlink=True)
 return objs
mint=material('RIVORA_kids_mint',(.42,.58,.49),.72);ivory=material('RIVORA_kids_ivory',(.82,.76,.64),.58)
box('Rounded_child_display_base',(0,0,.07),(1.72,.66,.14),ivory,.06)
for x in [-.73,.73]:tube('Outfit_rail_upright',[(x,.16,.14),(x,.16,1.37)],.016,brass)
tube('Outfit_rail_crossbar',[(-.73,.16,1.37),(.73,.16,1.37)],.016,brass)
for i,(m,x,h)in enumerate([('sku_v23_cardigan',-.44,.53),('sku_v23_pleated_dress',.35,.66)]):
 garment=asset(m,x,.16,0,h,.48);top=max(v.co.z for o in garment for v in o.data.vertices)
 for o in garment:o.data.transform(Matrix.Translation(Vector((0,0,1.24-top))))
 tube('Child_hanger',[(x-.17,.16,1.24),(x,.16,1.32),(x+.17,.16,1.24)],.005,brass);tube('Child_hanger_hook',[(x,.16,1.32),(x,.17,1.39),(x,.135,1.41)],.004,brass)
box('Child_shoe_display_table',(0,-.13,.35),(1.34,.37,.40),mint,.04);box('Display_table_top',(0,-.13,.57),(1.40,.42,.045),wood,.014)
for x in [-.45,-.15]:asset('sku_v23_sneaker',x,-.15,.60,.16,.22)
for x in [.22,.49]:asset('sku_folded_knit',x,-.14,.60,.10,.23)
bpy.context.view_layer.update();pts=[o.matrix_world@Vector(c)for o in bpy.context.scene.objects if o.type in ['MESH','CURVE']for c in o.bound_box];lo=[min(p[i]for p in pts)for i in range(3)];hi=[max(p[i]for p in pts)for i in range(3)];bounds={'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]],'sources':sorted(sources),'role':'child_scale_window_outfits_no_adult_mannequins'}
finish('kids_window_v292');(P/'source/v292/model-bounds.json').write_text(json.dumps({'kids_window_v292':bounds},ensure_ascii=False,indent=2))
