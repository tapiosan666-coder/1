import sys,math,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'))
from v293_common import *
B={};sources=set()
def asset(model,x,y,z,height=None,width=None,turn=0):
 paths=list(P.glob('assets/v*/models/'+model+'.glb'));path=paths[-1];sources.add(str(path.relative_to(P)));before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(path));new=[o for o in bpy.data.objects if o not in before];objs=[o for o in new if o.type=='MESH'];pts=[o.matrix_world@Vector(c)for o in objs for c in o.bound_box];lo=Vector([min(p[i]for p in pts)for i in range(3)]);hi=Vector([max(p[i]for p in pts)for i in range(3)]);k=height/(hi.z-lo.z)if height else 1
 if width:k=min(k,width/max(hi.x-lo.x,hi.y-lo.y))
 center=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z));T=Matrix.Translation(Vector((x,y,z)))@Matrix.Rotation(turn,4,'Z')@Matrix.Scale(k,4)@Matrix.Translation(-center)
 for o in objs:
  world=o.matrix_world.copy();o.parent=None;o.matrix_world=Matrix.Identity(4);o.data.transform(T@world)
 for o in new:
  if o.type!='MESH':bpy.data.objects.remove(o,do_unlink=True)
 return objs

def emit(name,role):
 bpy.context.view_layer.update();pts=[o.matrix_world@Vector(c)for o in bpy.context.scene.objects if o.type in ['MESH','CURVE']for c in o.bound_box];lo=[min(q[i]for q in pts)for i in range(3)];hi=[max(q[i]for q in pts)for i in range(3)];B[name]={'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]],'role':role,'sources':sorted(sources)};finish(name);sources.clear()



box('Bakery_wall_joinery',(0,.0,1.30),(3.60,.085,2.60),walnut,.025)
for x in [-1.77,1.77]:box('Champagne_edge',(x,-.055,1.3),(.025,.025,2.52),brass,.004)
for z in [.80,1.20,1.60]:
 box('Shallow_bread_ledge',(-.70,-.16,z),(1.95,.26,.045),wood,.014)
 for i,m in enumerate(['sku_v24_croissant','sku_v24_fruit_tart','sku_v24_sandwich']):asset(m,-1.34+i*.61,-.16,z+.03,height=.12,width=.44)
box('Chalk_menu_field',(.99,-.065,1.30),(1.20,.04,1.84),metal,.018)
emit('bakery_wall_v293','bakery_wall_merchandising_and_menu')
(P/'source/v293/bakery-model-bounds.json').write_text(json.dumps(B,ensure_ascii=False,indent=2))
