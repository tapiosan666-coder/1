from pathlib import Path
import sys,math,json,numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from v24_blender_common import *
B=json.loads((P/'source/v24/model-bounds.json').read_text());C=json.loads((P/'source/v24/product-catalog.json').read_text());rng=np.random.default_rng(2406)
for name,col in [('navy',(.055,.09,.14)),('oat',(.62,.56,.45))]:
 y,x=np.mgrid[:512,:512];v=.92+.04*np.sin(x*math.pi/2)+.035*np.sin(y*math.pi/2)+rng.normal(0,.012,(512,512));a=np.clip(v[:,:,None]*np.array(col)[None,None,:]*255,0,255).astype('uint8');Image.fromarray(a).save(P/f'assets/v24/art/cloth-{name}.png')
navy=material('Woven_navy_suiting',(.055,.09,.14),.89,texture='assets/v24/art/cloth-navy.png');oat=material('Woven_linen_suiting',(.62,.56,.45),.9,texture='assets/v24/art/cloth-oat.png');thread=material('Stitching',(.45,.40,.33),.98)
def done(name,role):
 bpy.context.view_layer.update();pts=[o.matrix_world@Vector(c)for o in bpy.context.scene.objects if o.type in['MESH','CURVE']for c in o.bound_box];lo=[min(q[i]for q in pts)for i in range(3)];hi=[max(q[i]for q in pts)for i in range(3)];B[name]={'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]]};C[name]={'category':'apparel','role':role,'source':'Original v24 tailored surfaces, seams and original woven image'};finish(name)
for style in['blazer','long_coat']:
 mat=navy if style=='blazer'else oat;length=.73 if style=='blazer'else .94;v=[];faces=[];uv=[]
 for j in range(33):
  t=j/32;z=.035+(1-t)*(length-.035);rx=.185-.035*math.sin(t*math.pi)+.025*max(0,t-.75)*4;ry=.082-.016*math.sin(t*math.pi)
  for k in range(40):
   a=math.tau*k/40;fold=.003*math.sin(9*a+3*t)*t;v.append(((rx+fold)*math.cos(a),(ry+fold)*math.sin(a),z));uv.append((k/40*4,t*5))
 for j in range(32):
  for k in range(40):
   # Open front seam and neck opening, separate lapels below.
   if k in[29,30]:continue
   a=j*40+k;b=j*40+(k+1)%40;faces.append((a,b,b+40,a+40))
 capv=[];capf=[];capuv=[]
 for ring_index in range(2):
  for k in range(40):
   a=math.tau*k/40;capv.append(((.185 if ring_index==0 else .060)*math.cos(a),(.082 if ring_index==0 else .045)*math.sin(a),length+(.018 if ring_index else 0)));capuv.append((k/40,ring_index))
 for k in range(40):
  if k in[29,30]:continue
  capf.append((k,(k+1)%40,(k+1)%40+40,k+40))
 mesh('Shoulder_yoke_and_neckline',capv,capf,mat,capuv)
 obj=mesh('Shaped_torso_shell',v,faces,mat,uv);mod=obj.modifiers.new('Real_cloth_edge','SOLIDIFY');mod.thickness=.003
 bpy.context.view_layer.objects.active=obj;bpy.ops.object.modifier_apply(modifier=mod.name)
 for side in[-1,1]:
  vv=[];ff=[];uu=[]
  for j in range(21):
   t=j/20;cx=side*(.17+.13*t);cz=length-.09-.54*t;rad=.064-.026*t
   for k in range(24):a=k*math.tau/24;vv.append((cx+math.cos(a)*rad*.70,math.sin(a)*rad,cz+.012*math.sin(a)));uu.append((k/24*2,t*4))
  for j in range(20):
   for k in range(24):a=j*24+k;b=j*24+(k+1)%24;ff.append((a,b,b+24,a+24))
  sleeve=mesh('Curved_tapered_sleeve',vv,ff,mat,uu);mod=sleeve.modifiers.new('Cuff_thickness','SOLIDIFY');mod.thickness=.003;bpy.context.view_layer.objects.active=sleeve;bpy.ops.object.modifier_apply(modifier=mod.name)
  mesh('Folded_lapel',[(side*.026,-.086,length*.47),(side*.145,-.084,length*.83),(side*.055,-.073,length*.99),(side*.016,-.098,length*.80)],[(0,1,2,3)],mat,[(0,0),(1,0),(1,1),(0,1)])
  tube('Lapel_edge',[(side*.026,-.089,length*.47),(side*.145,-.087,length*.83),(side*.055,-.076,length*.99)],.0012,thread)
  box('Patch_pocket',(side*.105,-.082,length*.30),(.10,.005,.075),mat,.006);tube('Pocket_stitch',[(side*.105-.043,-.087,length*.30+.03),(side*.105+.043,-.087,length*.30+.03)],.0008,thread)
 for j in range(3):
  bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,location=(.025,-.09,length*(.40-j*.10)));o=bpy.context.object;o.scale=(.006,.002,.006);o.data.materials.append(metal)
 tube('Hem_stitch',[(-.17,-.04,.04),(-.10,-.079,.04),(0,-.082,.04),(.10,-.079,.04),(.17,-.04,.04)],.0009,thread)
 tube('Shaped_hanger',[(-.20,0,length-.02),(-.12,0,length+.005),(0,0,length+.06),(.12,0,length+.005),(.20,0,length-.02)],.004,wood);tube('Hanger_bar',[(-.20,0,length-.02),(.20,0,length-.02)],.004,wood);tube('Hook',[(0,0,length+.06),(0,0,length+.13),(.03,0,length+.155),(.045,0,length+.125)],.003,metal)
 done('sku_v24_'+style,'Fitted '+style+' with open front, shaped sleeves, folded lapels, pockets, seams and actual fabric edge thickness')
(P/'source/v24/model-bounds.json').write_text(json.dumps(B,indent=2));(P/'source/v24/product-catalog.json').write_text(json.dumps(C,ensure_ascii=False,indent=2))
