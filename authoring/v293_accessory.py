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


# Dedicated accessories wall, separate from the mobile try-out counter.
box('Accessory_toe',(0,0,.07),(2.48,1.22,.14),metal,.025)
box('Accessory_joinery',(0,0,.46),(2.72,1.44,.73),white,.04)
box('Accessory_surface',(0,0,.865),(2.80,1.52,.075),wood,.03)
box('Perforated_display_back',(0,.53,1.43),(2.70,.07,1.04),metal,.018)
for x in [-1.,-.50,0.,.50,1.]:
 for z in [1.10,1.35,1.60,1.85]:box('Pegboard_horizontal_slot',(x,.484,z),(.12,.008,.018),white,.004)
asset('sku_v24_watch',-.92,-.12,.91,height=.08,width=.13)
asset('sku_speaker',0,-.06,.91,height=.36,width=.29)
asset('sku_v23_headphones',.88,-.09,.91,height=.29,width=.30)
for x in [-.92,0,.88]:box('Accessory_info_card',(x,-.54,.98),(.27,.06,.14),paper,.01)
emit('accessory_consult_v293','wearables_speakers_and_headphones')
old=json.loads((P/'source/v293/model-bounds.json').read_text());old.update(B);(P/'source/v293/model-bounds.json').write_text(json.dumps(old,ensure_ascii=False,indent=2))
