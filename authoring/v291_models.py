"""Continuation: purpose-built merchandising and cafe joinery. Project-owned source models only."""
import sys,math,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'))
from v291_common import *
B={};sources=set()
terracotta=material('TERRUNE_terracotta',(.32,.115,.061),.68)
forest=material('ALVENE_woven_sage',(.16,.23,.18),.88)
ivory=material('RIVORA_kids_ivory',(.82,.75,.59),.58)
blue=material('RIVORA_kids_blue',(.12,.28,.37),.68)
led=material('Warm_LED_diffuser',(.94,.80,.55),.4);s=led.node_tree.nodes.get('Principled BSDF');s.inputs['Emission Color'].default_value=(1,.73,.36,1);s.inputs['Emission Strength'].default_value=1.1
screen=material('SUVEL_original_display_graphic',(1,1,1),.3,texture='assets/v291/art/screen.png');s=screen.node_tree.nodes.get('Principled BSDF');tex=next(n for n in screen.node_tree.nodes if n.type=='TEX_IMAGE');screen.node_tree.links.new(tex.outputs['Color'],s.inputs['Emission Color']);s.inputs['Emission Strength'].default_value=.35

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

def ribbing(w,y,z,h,mat):
 for i in range(round(w/.13)):box('Oak_fluting',(-w/2+.065+i*.13,y,z),(.055,.03,h),mat,.009)
def legs(w,d):
 for x in [-w/2+.12,w/2-.12]:
  for y in [-d/2+.12,d/2-.12]:tube('Tapered_frame_leg',[(x,y,.04),(x*.94,y*.94,.70)],.024,metal)

# A bakery island is designed for food display, not the generic bottle table.
box('Shadow_toe',(0,0,.045),(3.38,1.12,.09),metal,.016);box('Fluted_bakery_base',(0,0,.49),(3.55,1.24,.82),walnut,.045);ribbing(3.45,-.637,.49,.72,wood)
box('Honed_countertop',(0,0,.925),(3.68,1.36,.065),stone,.025)
for row in range(2):
 for i,m in enumerate(['sku_v24_croissant','sku_v24_fruit_tart','sku_v24_sandwich','sku_v24_pastry_service']):
  x=-1.35+i*.90;y=-.30+row*.58;box('Removable_bakery_tray',(x,y,.98),(.78,.50,.045),metal,.014)
  for j in range(2):asset(m,x+(-.18+j*.36),y,1.01,height=.105,width=.29)
  box('Brass_product_card',(x,y-.24,1.04),(.22,.025,.09),brass,.005)
for x in [-1.8,1.8]:box('Glass_side_shield',(x,0,1.22),(.012,1.26,.48),glass,.002)
box('Vitrine_glass_roof',(0,0,1.48),(3.62,1.28,.012),glass,.002);tube('Display_light_rail',[(-1.74,.57,1.46),(1.74,.57,1.46)],.018,led)
emit('bakery_vitrine','bread_and_pastry_display')

# Curved upholstery, edged seat, tableware and distinct cafe furniture.
for side in [-1,1]:
 y=side*.93;box('Upholstered_seat',(0,y,.47),(1.65,.55,.18),forest,.09);box('Timber_banquette_base',(0,y,.23),(1.54,.48,.38),walnut,.04)
 back=box('Rounded_upholstered_back',(0,side*1.16,.86),(1.68,.17,.78),forest,.075);back.rotation_euler.x=side*.10
 for x in [-.80,.80]:box('Solid_oak_arm',(x,y,.67),(.07,.57,.12),wood,.028)
lathe('Cafe_pedestal',[(.32,.02),(.34,.055),(.09,.12),(.065,.68),(.49,.71),(.49,.75)],walnut,steps=48)
for x in [-.24,.24]:asset('sku_cup',x,0,.76,height=.11,width=.13)
asset('sku_v24_croissant',.03,.17,.76,height=.08,width=.27)
emit('cafe_banquette','four_place_booth')

# Freestanding cafe tables with actual chairs and carried crockery.
legs(1.45,.8);box('Cafe_rounded_table',(0,0,.75),(1.5,.85,.055),wood,.055)
for x in [-.43,.43]:
 for side in [-1,1]:asset('sku_chair',x,side*.87,.02,height=.87,width=.52,turn=0 if side>0 else math.pi)
for x in [-.48,.42]:asset('sku_bistro_plate',x,0,.79,height=.055,width=.31);asset('sku_cup',x,.19,.80,height=.11,width=.13)
emit('cafe_table','four_place_cafe_table')

box('Cafe_service_base',(0,0,.49),(3.7,.82,.91),terracotta,.035);ribbing(3.6,-.43,.49,.76,walnut);box('Stone_service_counter',(0,0,.98),(3.83,.96,.07),stone,.025)
asset('sku_espresso_machine',-.78,0,1.02,height=.62,width=1.05)
for x in [.15,.52,.90]:asset('sku_cup',x,.15,1.02,height=.13,width=.16)
asset('sku_v24_pastry_service',1.32,0,1.02,height=.14,width=.51)
box('Bar_footrail',(0,-.56,.19),(3.5,.055,.055),brass,.02)
emit('coffee_bar','barista_and_pickup_counter')

# Three children's sizes, lower rails and rounded safe display edges.
for child in [False,True]:
 h=1.25 if child else 1.78;w=1.90 if child else 1.95;col=blue if child else forest
 box('Rounded_fashion_plinth',(0,0,.07),(w+.12,.88,.14),ivory if child else walnut,.065)
 tube('Straight_hanger_crossrail',[(-w*.45,0,h),(w*.45,0,h)],.022,brass)
 for xx in [-w*.45,w*.45]:tube('Upright_rack_support',[(xx,0,.14),(xx,0,h)],.022,brass)
 for i,m in enumerate(['sku_v24_blazer','sku_v23_cardigan','sku_trousers','sku_v23_pleated_dress','sku_v23_cardigan','sku_v24_blazer']):
  hh=([.52,.55,.59,.67,.49,.54]if child else[.87,.92,1.03,1.18,.86,.90])[i];x=-w*.38+i*w*.76/5
  garment=asset(m,x,0,0,height=hh,width=.36 if child else .47,turn=math.pi/2)
  top=max(v.co.z for obj in garment for v in obj.data.vertices)
  for obj in garment:obj.data.transform(Matrix.Translation(Vector((0,0,h-.13-top))))
  tube('Individual_hanger',[(x,-.16,h-.13),(x,0,h-.045),(x,.16,h-.13)],.006,brass)
  tube('Hanger_hook',[(x,0,h-.045),(x,.018,h+.025),(x,-.025,h+.045),(x,-.04,h+.01)],.005,brass)
 emit('kids_rail'if child else'fashion_rail','child_scale_clothing'if child else'adult_clothing')

legs(2.15,1.05);box('Fashion_merchandising_table',(0,0,.76),(2.25,1.15,.08),wood,.035)
for i in range(4):
 for j in range(2):asset('sku_folded_knit',-.82+i*.55,-.24+j*.48,.81,height=.11,width=.43)
asset('sku_v23_tote',.70,.20,1.04,height=.41,width=.38);asset('sku_v23_heel',-.78,.25,.97,height=.23,width=.32)
emit('fashion_table','coordinated_fashion_table')

# Full-size electronics demonstration rather than miniature devices on uniform counters.
box('TV_display_toe',(0,0,.04),(3.75,1.05,.08),metal,.01);box('Acoustic_timber_back',(0,.30,1.27),(3.8,.14,2.48),walnut,.025)
for i,x in enumerate([-1.,1.]):
 box('OLED_bezel',(x,.15,1.57),(1.77,.075,1.03),metal,.022)
 o=mesh('Original_landscape_screen',[(x-.86,.102,1.085),(x+.86,.102,1.085),(x+.86,.102,2.055),(x-.86,.102,2.055)],[(0,1,2,3)],screen,uv=[(0,0),(1,0),(1,1),(0,1)])
 box('TV_console',(x,-.05,.54),(1.78,.67,.66),white,.025)
 asset('sku_v23_headphones',x-.46,-.12,.89,height=.27,width=.28)
 box('TV_specification_card',(x+.53,-.29,.96),(.24,.035,.16),paper,.007)
 tube('TV_cabinet_shadow_light',[(x-.80,-.38,.18),(x+.80,-.38,.18)],.012,led)
emit('television_demo','television_and_audio_experience')

box('Laundry_showroom_base',(0,0,.055),(3.6,1.45,.11),stone,.025)
for i,x in enumerate([-1.15,0,1.15]):
 asset('sku_washer'if i!=1 else'sku_fridge',x,.10,.12,height=.91 if i!=1 else 1.92,width=.78)
 if i!=1:asset('sku_towels',x,.15,1.04,height=.15,width=.46)
 box('Appliance_information_pedestal',(x,-.54,.43),(.26,.10,.64),metal,.02);box('Appliance_info_card',(x,-.59,.80),(.32,.035,.19),paper,.005)
emit('laundry_demo','large_appliance_department')

# Kitchen demo vignettes define a department through usable equipment and scale.
box('Kitchen_cabinet_plinth',(0,0,.06),(3.58,.73,.12),metal,.015);box('Kitchen_cabinet',(0,0,.50),(3.65,.78,.82),forest,.028)
for x in [-1.36,-.45,.45,1.36]:
 box('Cabinet_front',(x,-.407,.49),(.84,.032,.71),forest,.016);tube('Cabinet_handle',[(x-.17,-.44,.72),(x+.17,-.44,.72)],.009,brass)
box('Kitchen_demo_worktop',(0,0,.95),(3.78,.90,.06),stone,.019)
asset('sku_espresso_machine',-.95,0,.99,height=.52,width=.78);asset('sku_v23_tea_pot',.55,0,.99,height=.28,width=.35)
for i in range(3):asset('sku_cup',1.18+i*.12,-.1,.99,height=.11,width=.13)
box('Kitchen_splashback',(0,.39,1.36),(3.7,.055,.75),stone,.015);tube('Kitchen_under_shelf_LED',[(-1.7,.28,1.73),(1.7,.28,1.73)],.015,led)
emit('kitchen_demo','kitchen_appliance_department')
(P/'source/v291/model-bounds.json').write_text(json.dumps(B,ensure_ascii=False,indent=2))
