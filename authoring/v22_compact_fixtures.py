from pathlib import Path
import sys,json
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from v22_blender_common import *
B=json.loads((P/'source/v22/model-bounds.json').read_text());C=json.loads((P/'source/v22/product-catalog.json').read_text())
for name in ['compact_checkout','small_presentation','narrow_wall']:
 if name=='compact_checkout':
  box('Accessible_cashwrap',(0,0,.43),(.92,.56,.86),wood,.018);box('Worktop',(0,0,.88),(1.0,.62,.05),stone,.009);box('POS_foot',(.20,.10,1.0),(.06,.08,.22),metal,.005);o=box('POS_screen',(.2,.08,1.15),(.25,.045,.18),metal,.009);o.rotation_euler.x=-.15
 elif name=='small_presentation':
  for x in [-.35,.35]:box('Leg',(x,0,.35),(.035,.35,.70),metal,.005)
  box('Presentation_top',(0,0,.75),(.85,.45,.06),wood,.01)
 else:
  box('Integrated_back',(0,.20,1.0),(.95,.045,2.0),wood,.009)
  for y in [.3,.78,1.24,1.70]:box('Shallow_shelf',(0,0,y),(.95,.38,.035),white,.007)
 bpy.context.view_layer.update();pts=[o.matrix_world@Vector(c)for o in bpy.context.scene.objects for c in o.bound_box];lo=[min(p[i]for p in pts)for i in range(3)];hi=[max(p[i]for p in pts)for i in range(3)];key='fixture_'+name;B[key]={'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]]};C[key]={'role':name,'provenance':'Original metric Blender compact retail joinery'};finish(key)
(P/'source/v22/model-bounds.json').write_text(json.dumps(B,indent=2));(P/'source/v22/product-catalog.json').write_text(json.dumps(C,indent=2))
