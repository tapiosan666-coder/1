from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from v23_blender_common import *
B=json.loads((P/'source/v23/model-bounds.json').read_text());C=json.loads((P/'source/v23/product-catalog.json').read_text())
def done(name,role):
 bpy.context.view_layer.update();pts=[o.matrix_world@Vector(c)for o in bpy.context.scene.objects if o.type in['MESH','CURVE']for c in o.bound_box];lo=[min(q[i]for q in pts)for i in range(3)];hi=[max(q[i]for q in pts)for i in range(3)];B[name]={'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]]};C[name]={'category':'apparel','role':role,'source':'Original Blender v23 garment surfaces and retained original v15 display asset'};finish(name)
for typ in ['hoodie','pleated_dress','cardigan']:
 v=[];ff=[];length=.90 if typ=='pleated_dress'else .68;mat=fabrics[2]if typ=='hoodie'else fabrics[1]if typ=='cardigan'else fabrics[3]
 for j in range(25):
  t=j/24;z=length*(1-t);rx=(.16-.055*math.sin(math.pi*min(t/.5,1))+.16*max(0,t-.4))if typ=='pleated_dress'else .22-.07*(1-min(t/.14,1));ry=.067+.008*math.sin(t*math.pi)
  for k in range(32):
   a=math.tau*k/32;fold=.009*t*math.sin(10*a+t*.6)if typ=='pleated_dress'else .004*math.sin(7*a+t*3);v.append(((rx+fold)*math.cos(a),(ry+fold)*math.sin(a),z))
 for j in range(24):
  for k in range(32):
   if typ=='cardigan'and k in[22,23,24,25]:continue
   a=j*32+k;b=j*32+(k+1)%32;ff.append((a,b,b+32,a+32))
 mesh('Tailored_cloth_'+typ,v,ff,mat)
 if typ!='pleated_dress':
  for side in[-1,1]:
   vv=[];faces=[]
   for j in range(14):
    t=j/13
    for k in range(20):a=k*math.tau/20;r=.073-.03*t;vv.append((side*(.21+.15*t)+math.cos(a)*r*.55,math.sin(a)*r,length-.13-.45*t))
   for j in range(13):
    for k in range(20):a=j*20+k;b=j*20+(k+1)%20;faces.append((a,b,b+20,a+20))
   mesh('Sleeve_with_cuff',vv,faces,mat)
 if typ=='hoodie':
  vv=[];faces=[]
  for j in range(14):
   t=j/13
   for k in range(25):a=math.pi*k/24;vv.append((.12*math.cos(a)*math.sin(.5+t*1.8),.055+.09*math.sin(a),length-.06+.23*t))
  for j in range(13):
   for k in range(24):a=j*25+k;faces.append((a,a+1,a+26,a+25))
  mesh('Empty_hood_shell',vv,faces,mat);box('Kangaroo_pocket',(0,-.07,.23),(.24,.012,.15),mat,.025)
 if typ=='cardigan':
  for side in[-1,1]:tube('Front_placket',[(side*.055,-.065,.03),(side*.055,-.070,.35),(side*.09,-.045,.59)],.006,wood)
 tube('Display_hanger',[(-.20,0,.85),(0,0,.95),(.20,0,.85),(-.20,0,.85)],.005,wood);tube('Hook',[(0,0,.95),(0,0,1.02),(.025,0,1.05),(.045,0,1.02)],.003,metal);done('sku_v23_'+typ,typ+' different silhouette and construction')
bpy.ops.import_scene.gltf(filepath=str(P/'assets/v15/models/apparel_window_mannequin.glb'));done('fixture_v23_outfit_display','Existing original v15 outfit mannequin reused, no NPC changes')
(P/'source/v23/model-bounds.json').write_text(json.dumps(B,indent=2));(P/'source/v23/product-catalog.json').write_text(json.dumps(C,ensure_ascii=False,indent=2))
