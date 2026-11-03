"""Original role-led merchandising collections; uses only existing project-owned models.
Not a substitute for per-store art approval. Authoring coordinates Blender Z-up.
"""
import sys,math,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'))
from v29_blender_common import *
B={};sources=set()
cream=material('V29_ivory_lacquer',(.73,.69,.59),.42)
plum=material('V29_oxblood_lacquer',(.20,.065,.055),.43)
teal=material('V29_petrol_enamel',(.035,.16,.18),.35)
glow=material('V29_opal_LED',(.85,.78,.62),.45)
glow.node_tree.nodes.get('Principled BSDF').inputs['Emission Color'].default_value=(1,.85,.61,1)
glow.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=.75

def asset(model,x,y,z,height=None,width=None,turn=0):
 paths=list(P.glob('assets/v*/models/'+model+'.glb'))
 if not paths:raise FileNotFoundError(model)
 path=paths[-1];sources.add(str(path.relative_to(P)));before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(path));new=[o for o in bpy.data.objects if o not in before];objs=[o for o in new if o.type=='MESH']
 points=[o.matrix_world@Vector(c)for o in objs for c in o.bound_box];lo=Vector([min(p[i]for p in points)for i in range(3)]);hi=Vector([max(p[i]for p in points)for i in range(3)]);k=height/(hi.z-lo.z)if height else 1
 if width:k=min(k,width/max(hi.x-lo.x,hi.y-lo.y))
 center=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z));T=Matrix.Translation(Vector((x,y,z)))@Matrix.Rotation(turn,4,'Z')@Matrix.Scale(k,4)@Matrix.Translation(-center)
 for o in objs:
  world=o.matrix_world.copy();o.parent=None;o.matrix_world=Matrix.Identity(4);o.data.transform(T@world)
 for o in new:
  if o.type!='MESH':bpy.data.objects.remove(o,do_unlink=True)

def emit(name,cat):
 bpy.context.view_layer.update();pts=[o.matrix_world@Vector(c)for o in bpy.context.scene.objects if o.type in['MESH','CURVE']for c in o.bound_box];lo=[min(q[i]for q in pts)for i in range(3)];hi=[max(q[i]for q in pts)for i in range(3)]
 B[name]={'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]],'category':cat,'sources':sorted(sources)};finish(name);sources.clear()

def plinth(w=1.8,d=.78,col=cream):
 box('Recessed_shadow_base',(0,0,.035),(w-.12,d-.10,.07),metal,.012)
 box('Rounded_display_base',(0,0,.105),(w,d,.14),col,.025)

for category in ['apparel','shoes','beauty','home','book','electronics','food','cafe','restaurant','sports','furniture','mobile']:
 for variant in range(4 if category=="apparel"else 2):
  accent=teal if variant==0 else plum
  if category=='apparel':
   if variant==0:asset('fixture_v25_window_outfits',0,0,0,height=1.9,width=1.9)
   elif variant==2:
    plinth();box('Tailored_display_table',(0,0,.56),(1.75,.72,.76),wood,.045);box('Inset_stone_top',(0,0,.96),(1.86,.82,.045),stone,.015)
    for i in range(3):
     for j in range(2):asset('sku_folded_knit',-.55+i*.55,-.14+j*.28,.99,height=.12,width=.42)
    asset('sku_v23_tote',.56,.12,1.12,height=.38,width=.34)
   elif variant==3:
    plinth();box('Leather_goods_console',(0,.10,.63),(1.76,.55,.88),wood,.025)
    for i,m in enumerate(['sku_v23_tote','sku_v23_crossbody','sku_v23_backpack']):asset(m,-.58+i*.58,.06,1.08,height=.40,width=.43)
    for x in [-.50,.48]:asset('sku_v23_heel',x,-.18,.18,height=.24,width=.38)
   else:
    plinth();tube('Sweeping_clothes_rail',[(-.74,0,.18),(-.74,0,1.72),(-.55,0,1.85),(.55,0,1.85),(.74,0,1.72),(.74,0,.18)],.021,brass)
    for i,model in enumerate(['sku_v24_blazer','sku_v23_pleated_dress','sku_v23_cardigan','sku_trousers']):asset(model,-.57+i*.38,(i%2)*.06,1.79-[.90,1.24,1.05,1.12][i],height=[.90,1.24,1.05,1.12][i],turn=math.pi/2)
    asset('sku_v23_tote',.57,-.22,.18,height=.35)
  elif category=='shoes':
   plinth()
   for j,(x,h)in enumerate([(-.57,.38),(0,.72),(.58,.49)]):
    lathe('Sculpted_shoe_pedestal',[(.22,.18),(.20,h-.05),(.24,h),(.24,h+.035)],accent,(x,0,0),32)
    asset(['sku_v23_boot','sku_v23_sneaker','sku_v23_heel'][((j+variant)%3)],x,-.03,h+.04,height=.28,width=.37,turn=variant*.28)
   asset('sku_v23_crossbody',-.65,.24,1.0,height=.33)
   tube('Cantilever_bag_display',[(-.65,.26,.18),(-.65,.26,1.36)],.016,brass)
  elif category=='beauty':
   plinth();box('Tester_counter',(0,0,.58),(1.72,.70,.80),accent,.07)
   box('Solid_surface_tester',(0,0,1.0),(1.8,.78,.045),stone,.018)
   for j,m in enumerate(['sku_v23_compact_open','sku_v23_lip_open','sku_v23_palette','sku_v25_fragrance','sku_v23_brush_cup']):asset(m,-.66+j*.32,-.08,1.03,height=.13+.035*(j%3),width=.26)
   for x in [-.58,.58]:
    tube('Mirror_stem',[(x,.25,1.03),(x,.25,1.45)],.012,brass)
    lathe('Round_illuminated_mirror',[(.15,0),(.15,.022)],brass,(x,0,0))
    o=bpy.context.scene.objects[-1];o.rotation_euler.x=math.pi/2;o.location=(x,.26,1.48)
  elif category=='book':
   plinth();box('Editorial_bookcase_spine',(0,.24,.86),(1.8,.10,1.4),wood,.02)
   for row in range(3):
    y=.14-row*.16;z=1.34-row*.43
    box('Inclined_faceout_shelf',(0,y,z),(1.75,.32,.035),wood,.01)
    box('Book_retaining_lip',(0,y-.15,z+.035),(1.75,.025,.06),brass,.004)
    for i in range(6):asset('sku_v24_book_'+str((row+variant*3)%8)+'_'+str(i%4),-.70+i*.28,y,z+.025,height=.31,width=.23,turn=(i%2-.5)*.10)
  elif category=='home':
   plinth();box('Open_sideboard',(0,.08,.57),(1.75,.68,.82),wood,.035)
   for x in [-.55,0,.55]:box('Recessed_cabinet_door',(x,-.275,.57),(.52,.025,.70),accent,.015)
   asset('sku_v23_desk_lamp',-.58,0,1.0,height=.62,width=.38)
   asset('sku_v23_tea_pot',.10,-.03,1.0,height=.22)
   for i in range(3):asset('sku_cup',.48+i*.10,-.12+i*.12,1.0,height=.11)
   asset('sku_towels',.52,.13,1.,height=.24,width=.40)
  elif category in ['electronics','mobile']:
   plinth();box('Experience_counter',(0,0,.61),(1.78,.74,.86),accent,.035);box('Demo_worktop',(0,0,1.07),(1.88,.82,.055),stone,.015)
   if category=='mobile':
    for i in range(4):
     x=-.65+i*.43;box('Angled_security_stand',(x,0,1.14),(.20,.20,.10),metal,.016);asset('sku_phone',x,0,1.20,height=.20,width=.18)
   else:
    asset('sku_laptop',-.46,-.05,1.1,height=.30,width=.65);asset('sku_v23_tablet',.30,-.08,1.12,height=.32,width=.30);asset('sku_v23_headphones',.68,.08,1.1,height=.27,width=.28)
   tube('Cable_management_rail',[(-.76,.30,1.09),(.76,.30,1.09)],.014,brass)
  elif category=='food':
   plinth();box('Market_slat_counter',(0,0,.50),(1.78,.74,.66),wood,.02)
   for i in range(7):box('Counter_vent_slot',(-.70+i*.23,-.38,.49),(.13,.018,.51),accent,.008)
   for x in [-.56,0,.56]:
    box('Produce_crate',(x,0,.88),(.51,.65,.12),wood,.01)
    for i in range(3):
     for j in range(2):asset(['sku_v23_citrus','sku_v23_melon','sku_tomatoes'][(int((x+.6)*2)+variant)%3],x+(i-1)*.15,-.15+j*.26,.95,height=.12,width=.14)
  elif category in ['cafe','restaurant']:
   plinth();box('Fluted_service_joinery',(0,0,.59),(1.78,.74,.83),wood,.025)
   for x in range(-8,9):box('Counter_fluting',(x*.10,-.386,.58),(.045,.025,.69),accent,.008)
   box('Cafe_stone_top',(0,0,1.03),(1.87,.82,.065),stone,.018)
   if category=='cafe':
    asset('sku_espresso_machine',-.55,.05,1.08,height=.50,width=.65)
    for i,m in enumerate(['sku_v24_croissant','sku_v24_fruit_tart','sku_v24_sandwich']):asset(m,.05+i*.27,-.08,1.08,height=.09,width=.24)
   else:
    for i,m in enumerate(['sku_v24_soup_service','sku_bistro_plate','sku_v24_pastry_service']):asset(m,-.57+i*.57,0,1.08,height=.18,width=.47)
   for i in range(4):asset('sku_cup',.50,.22,1.08+i*.085,height=.09)
  elif category=='sports':
   plinth();tube('Equipment_halo',[(-.8,.18,.18),(-.8,.18,1.72),(.8,.18,1.72),(.8,.18,.18)],.022,metal)
   for i in range(3):asset('sku_racket',-.52+i*.52,.12,.55,height=1.15,width=.42,turn=i*.16)
   for x in [-.53,.48]:asset('sku_ball',x,-.16,.18,height=.25)
  elif category=='furniture':
   plinth(1.9,1.1);asset('sku_chair',-.50,.08,.18,height=.94,width=.72);asset('sku_v23_desk_lamp',.57,.20,.65,height=.62,width=.42)
   lathe('Round_occasional_table',[(.30,.16),(.25,.59),(.35,.63),(.35,.67)],wood,(.52,0,0))
   asset('sku_vase',.45,-.06,.68,height=.24)
  emit('collection_v29_'+category+'_'+str(variant),category)
(P/'source/v29/model-bounds.json').write_text(json.dumps(B,indent=2))
