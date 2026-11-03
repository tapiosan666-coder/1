from pathlib import Path
import sys,math,json
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from v24_blender_common import *
B=json.loads((P/'source/v24/model-bounds.json').read_text());C=json.loads((P/'source/v24/product-catalog.json').read_text());black=material('Optical_acetate',(.025,.028,.032),.23);silver=material('Optical_titanium',(.55,.58,.60),.22,.9);velvet=material('Optical_display_velvet',(.12,.16,.16),.94)
for typ in['round','rectangular','cat_eye']:
 box('Display_plinth',(0,0,.012),(.16,.10,.024),velvet,.008)
 for side in[-1,1]:
  points=[]
  for k in range(33):
   a=k*math.tau/32
   if typ=='round':x=.028*math.cos(a);z=.025*math.sin(a)
   else:x=.030*math.copysign(abs(math.cos(a))**.40,math.cos(a));z=.020*math.copysign(abs(math.sin(a))**.45,math.sin(a))
   if typ=='cat_eye':z+=.006*side*x/.03
   points.append((side*.034+x,-.020,.056+z))
  tube('Shaped_frame',points,.0015,silver if typ=='round'else black)
  tube('Temples',[(side*.063,-.020,.058),(side*.066,.038,.054),(side*.060,.046,.041)],.0013,black)
 tube('Nose_bridge',[(-.006,-.021,.055),(0,-.024,.061),(.006,-.021,.055)],.0013,silver)
 bpy.context.view_layer.update();pts=[o.matrix_world@Vector(c)for o in bpy.context.scene.objects if o.type in['MESH','CURVE']for c in o.bound_box];lo=[min(q[i]for q in pts)for i in range(3)];hi=[max(q[i]for q in pts)for i in range(3)];name='sku_v24_optical_'+typ;B[name]={'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]]};C[name]={'category':'optics','role':typ+' frame geometry, bridge, temples and individual display support','source':'Original Blender v24'};finish(name)
(P/'source/v24/model-bounds.json').write_text(json.dumps(B,indent=2));(P/'source/v24/product-catalog.json').write_text(json.dumps(C,ensure_ascii=False,indent=2))
