from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from v22_blender_common import *
B={};C={}
def done(name,role):
 bpy.context.view_layer.update();pts=[o.matrix_world@Vector(c)for o in bpy.context.scene.objects if o.type in ['MESH','CURVE']for c in o.bound_box];lo=[min(v[i]for v in pts)for i in range(3)];hi=[max(v[i]for v in pts)for i in range(3)];B[name]={'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]]};C[name]={'role':role,'provenance':'Original Blender geometry v22; inherited CC0 wood textures with existing licenses'};finish(name)
leather=material('Leather_stitching',(.23,.11,.055),.65);blue=material('Technical_blue',(.05,.14,.20),.62);red=material('Toy_red',(.58,.11,.035),.4);yellow=material('Sport_tan',(.62,.38,.12),.58)
# Soft shoe last with continuous profile, outsole and separate laces.
v=[];faces=[]
for j in range(16):
 y=-.14+j*.018;w=.032+.022*math.sin(math.pi*j/15);h=.028+.057*math.exp(-((j-10)/4)**2)
 for k in range(16):a=math.tau*k/16;v.append((math.cos(a)*w,y,.035+abs(math.sin(a))*h))
for j in range(15):
 for k in range(16):a=j*16+k;b=j*16+(k+1)%16;faces.append((a,b,b+16,a+16))
mesh('Stitched_shoe_upper',v,faces,blue);box('Moulded_sole',(0,-.005,.018),(.125,.32,.025),rubber,.01)
for j in range(4):tube('Shoelace',[(-.032,.01+j*.018,.10),(.032,.025+j*.018,.102)],.0025,white)
done('sku_shoe','footwear')
box('Bag_body',(0,0,.16),(.28,.11,.28),leather,.028)
for y in [-.045,.045]:tube('Leather_handle',[(-.08,y,.28),(-.07,y,.41),(.07,y,.41),(.08,y,.28)],.009,leather)
box('Bag_clasp',(0,-.06,.24),(.035,.012,.025),brass,.003);done('sku_bag','travel handbags')
for x in [-.034,.034]:tube('Optical_frame',[(x+math.cos(a)*.03,-.004,.035+math.sin(a)*.021)for a in [math.tau*i/24 for i in range(25)]],.002,brass)
tube('Bridge',[(-.008,0,.039),(0,-.003,.042),(.008,0,.039)],.002,brass)
for x in [-.064,.064]:tube('Temple',[(x,0,.036),(x,.11,.035),(x,.135,.020)],.002,metal)
done('sku_glasses','optical frames')
for kind in ['ball','toy','pet_food','medicine','guitar','racket','shoe_table','service_desk','cinema_seat','cinema_screen','furniture_set','sport_wall']:
 if kind=='ball':lathe('Panelled_sport_ball',[(max(.001,.115*math.sin(math.pi*i/16)),.115-.115*math.cos(math.pi*i/16))for i in range(17)],yellow,steps=24);tube('Ball_seam',[(.116*math.cos(a),.116*math.sin(a),.115)for a in [math.tau*i/32 for i in range(33)]],.0015,rubber)
 elif kind=='toy':
  for x,y in [(-.08,-.06),(-.08,.06),(.08,-.06),(.08,.06)]:o=lathe('Toy_wheel',[(0,0),(.026,0),(.026,.018),(0,.018)],rubber,(x,y,.026),16);o.rotation_euler.x=math.pi/2
  box('Toy_car',(0,0,.055),(.22,.10,.055),red,.015);box('Toy_cabin',(0,.005,.095),(.09,.09,.055),blue,.014)
 elif kind in ['pet_food','medicine']:
  box('Original_package',(0,0,.15),(.16,.10,.30)if kind=='pet_food'else(.09,.04,.13),blue if kind=='pet_food'else white,.012);box('Brand_label',(0,-.053,.15),(.10,.003,.12),yellow if kind=='pet_food'else blue,.003)
 elif kind=='guitar':
  v=[];ff=[]
  for y in [-.045,.045]:
   for i in range(48):a=i*math.tau/48;r=.19*(.8+.20*math.cos(2*a));v.append((r*math.cos(a),y,.25+r*1.3*math.sin(a)))
  ff=[tuple(range(47,-1,-1)),tuple(range(48,96))]+[(i,(i+1)%48,(i+1)%48+48,i+48)for i in range(48)];mesh('Resonant_guitar_body',v,ff,wood);box('Fretboard',(0,-.048,.68),(.055,.024,.62),walnut,.006);box('Headstock',(0,0,1.03),(.07,.06,.16),wood,.012)
  for x in [-.014,-.008,-.002,.004,.010,.016]:tube('String',[(x,-.063,.18),(x,-.063,1.06)],.0007,steel)
 elif kind=='racket':
  tube('Racket_hoop',[(.14*math.cos(a),0,.43+.19*math.sin(a))for a in [math.tau*i/32 for i in range(33)]],.009,blue);tube('Handle',[(0,0,.25),(0,0,.03)],.018,rubber)
  for x in [-.09,-.06,-.03,0,.03,.06,.09]:tube('Strings',[(x,0,.29),(x,0,.56)],.0009,white)
 elif kind=='shoe_table':
  for x in [-.7,.7]:box('Gallery_leg',(x,0,.36),(.045,.55,.72),metal,.006)
  box('Presentation_top',(0,0,.75),(1.75,.75,.055),wood,.01);box('Inset_display',(0,.19,1.02),(1.4,.25,.05),white,.01)
 elif kind=='service_desk':
  box('Service_counter',(0,0,.46),(2.2,.75,.92),wood,.02);box('Counter_surface',(0,0,.94),(2.3,.85,.05),stone,.012);box('Privacy_screen',(.7,.25,1.2),(.40,.05,.26),metal,.008)
 elif kind=='cinema_seat':
  box('Upholstered_base',(0,0,.42),(.62,.60,.17),fabrics[3],.055);o=box('Upholstered_back',(0,.25,.85),(.64,.18,.85),fabrics[3],.06);o.rotation_euler.x=-.12
  for x in [-.38,.38]:box('Armrest',(x,.04,.60),(.12,.67,.16),rubber,.028)
 elif kind=='cinema_screen':box('Projection_frame',(0,0,1.5),(5.8,.20,2.9),metal,.035);box('Projection_screen',(0,-.115,1.5),(5.55,.025,2.65),white,.012)
 elif kind=='furniture_set':
  box('Sofa_base',(0,0,.40),(2.2,.85,.26),fabrics[1],.08);box('Sofa_back',(0,.35,.76),(2.2,.20,.77),fabrics[1],.06)
  for x in [-1.02,1.02]:box('Sofa_arm',(x,0,.67),(.20,.88,.30),fabrics[1],.05)
 elif kind=='sport_wall':
  box('Technical_backboard',(0,.33,1.1),(2.0,.07,2.2),blue,.01)
  for y in [.45,1.10,1.75]:box('Dedicated_equipment_shelf',(0,0,y),(2.0,.65,.045),metal,.006)
 done(('fixture_'if kind in ['shoe_table','service_desk','cinema_seat','cinema_screen','furniture_set','sport_wall']else'sku_')+kind,kind)
(P/'source/v22/model-bounds.json').write_text(json.dumps(B,indent=2));(P/'source/v22/product-catalog.json').write_text(json.dumps(C,indent=2));print('V22_KIT',len(B))
