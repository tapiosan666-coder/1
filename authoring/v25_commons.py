from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from v25_blender_common import *
from PIL import Image,ImageDraw,ImageFont
B=json.loads((P/'source/v25/model-bounds.json').read_text());C=json.loads((P/'source/v25/product-catalog.json').read_text())
def emit(name,role):
 bpy.context.view_layer.update();points=[o.matrix_world@Vector(c)for o in bpy.context.scene.objects if o.type=='MESH'for c in o.bound_box];a=[min(v[i]for v in points)for i in range(3)];b=[max(v[i]for v in points)for i in range(3)];B[name]={'min':[a[0],a[2],-b[1]],'max':[b[0],b[2],-a[1]]};C[name]={'category':role,'source':'Original v25 Blender authored commons, CC0 timber; inherited event content unchanged'};finish(name)
# Within original 2.4 x .61 envelope; slatted sitting surface at .45, rounded laminated back, tangible armrests.
for y in[-.235,-.14,-.045,.05,.145,.24]:box('Rounded_timber_seat_slat',(0,y,.425),(2.34,.078,.05),wood,.012)
for z in[.60,.70,.80,.90]:
 pts=[(-1.16,.22,z),(-.60,.27,z+.01),(0,.285,z+.015),(.60,.27,z+.01),(1.16,.22,z)];tube('Bent_laminated_back',pts,.035,wood)
for x in[-.91,.91]:
 tube('Steel_leg',[(x,-.24,.02),(x,-.20,.37),(x,.20,.37),(x,.24,.02)],.025,metal);tube('Rounded_armrest',[(x,-.24,.45),(x,-.23,.64),(x,.18,.65),(x,.23,.43)],.022,metal)
emit('commons_v25_terrace_bench','outdoor_seating')
# Refined information housing. Existing live directions/boards remain the actual guidance layer.
box('Weighted_stone_foot',(0,0,.055),(.84,.50,.11),stone,.035);box('Slatted_oak_back',(0,.105,1.18),(.80,.20,2.20),wood,.025);box('Inset_graphite_panel',(0,-.015,1.28),(.70,.035,1.68),metal,.02)
for x in[-.37,.37]:tube('Champagne_edge',[(x,-.03,.16),(x,-.03,2.22)],.011,brass)
for z in[.35,2.13]:box('Fine_wayfinding_edge',(0,-.04,z),(.64,.012,.012),brass,.004)
emit('commons_v25_info_housing','information_housing')
# Aichi Seto ceramics booth: same working envelope, storage at rear, actual open service frontage.
sage=material('V25_fair_indigo',(.055,.10,.16),.70);canvas=material('V25_woven_canopy',(.76,.70,.56),.92)
box('Counter_storage',(0,.24,.46),(3.10,.82,.90),wood,.03);box('Counter_stone',(0,.20,.935),(3.16,.93,.07),stone,.015)
for x in[-1.54,1.54]:
 for y in[-1.35,1.35]:tube('Oak_booth_post',[(x,y,.02),(x,y,2.64)],.038,wood)
# Pitched fabric roof and structural ridge, no arbitrary floating ceiling.
mesh('Woven_roof',[(-1.67,-1.49,2.66),(1.67,-1.49,2.66),(-1.67,0,3.01),(1.67,0,3.01),(-1.67,1.49,2.66),(1.67,1.49,2.66)],[(0,1,3,2),(2,3,5,4)],canvas)
tube('Ridge',[(-1.60,0,2.98),(1.60,0,2.98)],.026,wood);box('Indigo_valance',(0,-1.485,2.54),(3.30,.035,.24),sage,.012)
for x in[-1.06,0,1.06]:
 box('Display_tray',(x,-.04,1.00),(.84,.48,.04),wood,.012)
 for j in range(3):lathe('Handmade_ceramic_bowl',[(.06,0),(.075,.01),(.105,.07),(.12,.10),(.10,.11),(.085,.075),(.055,.018)],ceramics[(j+int(x))%3],(x-.24+j*.24,-.04,1.024),40)
box('Rear_shelf',(0,.95,1.38),(2.74,.42,.045),wood,.01)
for x in[-1.08,-.54,0,.54,1.08]:lathe('Glazed_craft_vase',[(.07,0),(.13,.08),(.11,.25),(.055,.36),(.05,.37)],ceramics[int(abs(x)*4)%3],(x,.96,1.405),40)
emit('commons_v25_seto_booth','Aichi_craft_event')
(P/'source/v25/model-bounds.json').write_text(json.dumps(B,indent=2));(P/'source/v25/product-catalog.json').write_text(json.dumps(C,indent=2));print('V25_COMMON_ASSETS',len(B))
