from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from v23_blender_common import *
B=json.loads((P/'source/v23/model-bounds.json').read_text());C=json.loads((P/'source/v23/product-catalog.json').read_text());blue=material('V23_sneaker_canvas',(.14,.22,.25),.82);leather=material('V23_smooth_leather',(.12,.085,.06),.36)
for typ in['sneaker','heel','boot']:
 v=[];faces=[]
 for j in range(18):
  t=j/17;y=-.15+j*.017;w=.038+.025*math.sin(math.pi*t);z0=.036+(.075*t**3 if typ=='heel'else .002*math.cos(t*math.pi));top=.035+(.065 if typ!='heel'else .04)*math.exp(-((j-11)/4)**2)
  for k in range(24):a=math.tau*k/24;v.append((math.cos(a)*w,y,z0+math.sin(a)*(top if math.sin(a)>=0 else .012)))
 for j in range(17):
  for k in range(24):a=j*24+k;b=j*24+(k+1)%24;faces.append((a,a+24,b+24,b))
 faces+=[tuple(range(24)),tuple(range(18*24-1,17*24-1,-1))];mesh('Closed_toe_and_heel_last',v,faces,blue if typ=='sneaker'else leather)
 sv=[];ff=[]
 for j in range(18):
  t=j/17;y=-.15+j*.017;w=.039+.026*math.sin(math.pi*t);z=.020+(.075*t**3 if typ=='heel'else 0)
  sv +=[(-w,y,z),(w,y,z),(-w,y,z+.010),(w,y,z+.010)]
 for j in range(17):
  a=j*4;b=a+4;ff +=[(a,b,b+1,a+1),(a+2,a+3,b+3,b+2),(a,a+2,b+2,b),(a+1,b+1,b+3,a+3)]
 ff +=[(0,1,3,2),(68,70,71,69)];mesh('Profiled_outsole',sv,ff,rubber)
 if typ=='heel':box('Slim_heel',(0,.112,.035),(.032,.042,.07),leather,.005);tube('Heel_strap',[(-.045,.08,.12),(-.035,.10,.19),(.035,.10,.19),(.045,.08,.12)],.005,leather)
 elif typ=='boot':
  o=lathe('Ankle_shaft',[(.047,.07),(.048,.20),(.052,.29),(.044,.29),(.040,.09)],leather,(0,.085,0),32);tube('Boot_pull_tab',[(-.027,.13,.27),(0,.14,.31),(.027,.13,.27)],.006,leather)
 else:
  for j in range(5):tube('Laces',[(-.029,.015+j*.015,.12),(.029,.025+j*.015,.12)],.002,white)
 name='sku_v23_'+typ;bpy.context.view_layer.update();pts=[o.matrix_world@Vector(c)for o in bpy.context.scene.objects if o.type in['MESH','CURVE']for c in o.bound_box];lo=[min(q[i]for q in pts)for i in range(3)];hi=[max(q[i]for q in pts)for i in range(3)];B[name]={'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]]};C[name]={'category':'shoes','role':'Closed 3D last, profiled sole and purpose-specific upper','source':'Original Blender v23'};finish(name)
(P/'source/v23/model-bounds.json').write_text(json.dumps(B,indent=2));(P/'source/v23/product-catalog.json').write_text(json.dumps(C,ensure_ascii=False,indent=2))
