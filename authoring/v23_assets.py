"""Original shape-specific merchandise and functional retail fixtures; no borrowed brands or NPC changes."""
from pathlib import Path
import sys,json,math,random
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from v23_blender_common import *
from PIL import Image,ImageDraw,ImageFont
ART=P/'assets/v23/art';ART.mkdir(exist_ok=True,parents=True);im=Image.new('RGB',(2048,2048),'#ece7dc');d=ImageDraw.Draw(im);font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';bold='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc';titles=['旅の余白','暮らしの設計','季節の料理','夜明けの物語','子どもの図鑑','写真と光','街の音楽','小さな庭','BOTANIC LAB','SOFT COLOR','SKIN LAYER','SCENT NOTES','LILVA STUDY','ROOM OBJECTS','DAILY MARKET','CERAVA CAFE','文庫 / FICTION','ART / DESIGN','COOK / LIFE','KIDS / NATURE','PURE SERUM','MOISTURE','COLOR PALETTE','EAU DE PARFUM','FRESH HARVEST','BAKERY OVEN','ROAST COFFEE','RICE & TABLE','FORM / LEATHER','WEEKEND SHOES','HOME / TEXTILE','SOUND / TOOLS'];colours=['#23453f','#a05e45','#344b66','#755160','#807345','#3c6b73','#ad714c','#485d3e']
for k,title in enumerate(titles):
 x=k%8*256;y=k//8*512;c=colours[k%8];d.rectangle((x+3,y+3,x+252,y+508),fill='#eee8d9');d.rectangle((x+3,y+3,x+252,y+70),fill=c);d.text((x+20,y+22),'COLLECTION / %02d'%k,font=ImageFont.truetype(bold,16),fill='#f3e9d8');
 if k%4==0:
  for j in range(6):d.arc((x+25+j*5,y+125+j*14,x+228-j*3,y+360),10+j*15,270+j*7,fill=c,width=4)
 elif k%4==1:
  for j in range(5):d.rectangle((x+30+j*22,y+140+j*21,x+155+j*12,y+310+j*17),outline=c,width=4)
 elif k%4==2:
  for j in range(8):d.line((x+32,y+135+j*22,x+210,y+315-j*11),fill=c,width=5)
 else:
  for j in range(4):d.ellipse((x+35+j*14,y+125+j*26,x+215-j*10,y+300+j*12),outline=c,width=5)
 d.text((x+128,y+390),title,font=ImageFont.truetype(bold,22),fill=c,anchor='mm');d.text((x+128,y+443),'FIND YOURSELF / ORIGINAL',font=ImageFont.truetype(font,12),fill=c,anchor='mm');d.text((x+128,y+478),'DESIGN SERIES  /  %02d'%k,font=ImageFont.truetype(font,12),fill=c,anchor='mm')
im.save(ART/'retail-editorial-atlas.png',optimize=True);atlas=material('V23_original_editorial',(1,1,1),.63,texture='assets/v23/art/retail-editorial-atlas.png');blue=material('V23_technical_ink',(.035,.10,.16),.38);rose=material('V23_mineral_rose',(.46,.24,.22),.51);sage=material('V23_soft_sage',(.19,.30,.23),.57);sand=material('V23_natural_canvas',(.65,.59,.47),.86);dark=material('V23_ceramic_graphite',(.045,.053,.051),.29);gold=material('V23_satin_brass',(.47,.32,.14),.31,.7);rub=material('V23_shoe_rubber',(.035,.038,.039),.84)
B={};C={}
def label(p,w,h,k):
 x,y,z=p;u=(k%8)/8;v=1-(k//8+1)/4;return mesh('Original_print',[(x-w/2,y,z-h/2),(x+w/2,y,z-h/2),(x+w/2,y,z+h/2),(x-w/2,y,z+h/2)],[(0,1,2,3)],atlas,[(u,v),(u+.125,v),(u+.125,v+.25),(u,v+.25)])
def done(name,category,role,shelves=None):
 bpy.context.view_layer.update();points=[o.matrix_world@Vector(c)for o in bpy.context.scene.objects if o.type in['MESH','CURVE']for c in o.bound_box];lo=[min(p[i]for p in points)for i in range(3)];hi=[max(p[i]for p in points)for i in range(3)];B[name]={'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]],'unit':'metres'};C[name]={'category':category,'role':role,'source':'Original Blender v23','shelf_surfaces_m':shelves or[]};finish(name)
def ellipse_body(name,w,d,h,mat):
 v=[];faces=[]
 for j in range(15):
  t=j/14;rx=w/2*(.85+.15*math.sin(t*math.pi));ry=d/2*(.87+.13*math.sin(t*math.pi))
  for k in range(32):a=k*math.tau/32;v.append((rx*math.cos(a),ry*math.sin(a),.02+t*h))
 for j in range(14):
  for k in range(32):a=j*32+k;b=j*32+(k+1)%32;faces.append((a,b,b+32,a+32))
 faces+=[tuple(range(31,-1,-1)),tuple(range(448,480))];return mesh(name,v,faces,mat)
# Three genuinely different footwear lasts and soles; no colour-only variation.
for typ in ['sneaker','heel','boot']:
 v=[];ff=[]
 for j in range(18):
  y=-.15+j*.017;w=.042+.018*math.sin(j*math.pi/17);top=.045+(.07 if typ!='heel'else .045)*math.exp(-((j-11)/4)**2)
  for k in range(24):a=k*math.tau/24;v.append((math.cos(a)*w,y,.025+abs(math.sin(a))*top))
 for j in range(17):
  for k in range(24):a=j*24+k;b=j*24+(k+1)%24;ff.append((a,b,b+24,a+24))
 mesh('Footwear_last',v,ff,sand if typ=='sneaker'else dark);box('Shaped_outsole',(0,-.005,.019),(.132,.33,.026),rub,.012)
 if typ=='boot':ellipse_body('Ankle_upper',.105,.095,.22,dark);tube('Pull_tab',[(-.035,.055,.22),(0,.065,.26),(.035,.055,.22)],.008,sand)
 elif typ=='heel':box('Heel',(0,.10,.025),(.028,.035,.055),gold,.005);tube('Ankle_strap',[(-.045,.08,.10),(-.04,.095,.17),(.04,.095,.17),(.045,.08,.10)],.006,dark)
 else:
  for j in range(5):tube('Lace',[(-.035,.01+j*.015,.10),(.035,.02+j*.015,.10)],.0025,white)
 done('sku_v23_'+typ,'shoes','distinct footwear silhouette')
for typ in ['tote','crossbody','backpack']:
 w=.30 if typ=='tote'else .22;h=.28 if typ!='crossbody'else .18;ellipse_body('Structured_bag',w,.11,h,sand if typ=='tote'else rose if typ=='crossbody'else sage)
 if typ=='tote':
  for y in[-.045,.045]:tube('Canvas_handle',[(-.095,y,h),(-.09,y,h+.13),(.09,y,h+.13),(.095,y,h)],.009,sand)
 elif typ=='crossbody':tube('Shoulder_strap',[(-w/2,0,.16),(-.12,0,.41),(.12,0,.41),(w/2,0,.16)],.005,gold);box('Foldover_flap',(0,-.063,.18),(.21,.012,.09),rose,.018)
 else:
  box('Front_pocket',(0,-.065,.11),(.16,.035,.12),sage,.015)
  for x in[-.075,.075]:tube('Back_strap',[(x,.06,.03),(x,.105,.14),(x,.06,.28)],.008,sand)
 done('sku_v23_'+typ,'bags','different carry system and outline')
for typ in ['palette','lip_open','pump','perfume','compact_open','brush_cup']:
 if typ=='palette':box('Palette',(0,0,.018),(.16,.11,.035),dark,.008);o=box('Hinged_lid',(0,.045,.09),(.16,.012,.14),gold,.005);o.rotation_euler.x=.15
 if typ=='palette':
  for x in[-.05,0,.05]:
   for y in[-.025,.025]:lathe('Pigment_pan',[(0,0),(.017,0),(.017,.004),(0,.004)],rose if x<0 else sand if x==0 else sage,(x,y,.037),20)
 elif typ=='lip_open':lathe('Lipstick_case',[(0,0),(.016,0),(.016,.065),(.012,.07),(.010,.105),(0,.108)],dark);lathe('Lip_colour',[(0,.070),(.010,.070),(.010,.10),(0,.112)],rose)
 elif typ=='pump':ellipse_body('Serum_container',.055,.045,.105,white);box('Pump_neck',(0,0,.125),(.026,.025,.035),gold,.004);box('Nozzle',(0,-.012,.147),(.026,.038,.010),gold,.003);label((0,-.024,.063),.038,.067,20)
 elif typ=='perfume':box('Faceted_perfume',(0,0,.055),(.085,.045,.10),sand,.013);box('Decanter_cap',(0,0,.12),(.040,.035,.035),gold,.006);label((0,-.024,.055),.060,.065,23)
 elif typ=='compact_open':lathe('Powder_compact',[(0,0),(.049,0),(.050,.018),(0,.018)],gold);lathe('Powder_pan',[(0,.018),(.041,.018),(.041,.022),(0,.022)],sand);o=lathe('Mirror_lid',[(0,0),(.048,0),(.048,.005),(0,.005)],steel,(0,.044,.061),32);o.rotation_euler.x=math.pi/2
 elif typ=='brush_cup':lathe('Brush_holder',[(0,0),(.028,0),(.03,.062),(.025,.067)],dark)
 if typ=='brush_cup':
  for j in range(5):tube('Brush_handle',[(math.cos(j)*.014,math.sin(j)*.014,.02),(math.cos(j)*.02,math.sin(j)*.02,.14+j*.006)],.003,wood);lathe('Soft_brush',[(0,0),(.009,.008),(.012,.025),(0,.034)],sand,(math.cos(j)*.02,math.sin(j)*.02,.14+j*.006),20)
 done('sku_v23_'+typ,'beauty','dedicated makeup/skincare form')
# Different book formats, not a single spine recoloured.
for k in range(8):
 w=[.105,.145,.19,.22,.15,.13,.18,.16][k];h=[.17,.215,.265,.29,.20,.19,.24,.23][k];t=[.020,.031,.015,.023,.038,.018,.027,.022][k];box('Paper_block',(0,0,h/2),(w-.004,t-.004,h-.008),paper,.0007)
 for y in[-t/2,t/2]:box('Cover_board',(0,y,h/2),(w,.0015,h),white,.0005)
 box('Book_spine',(-w/2,0,h/2),(.003,t,h),dark,.0005);label((0,-t/2-.001,h/2),w-.002,h-.003,k);done('sku_v23_book_'+str(k),'book','paperback/hardcover/magazine/art/children formats')
for typ in ['storage_basket','tea_pot','desk_lamp','headphones','tablet','melon','citrus','bakery_bag','salad']:
 if typ=='storage_basket':
  for z in[.025,.055,.085,.115]:tube('Woven_ring',[(-.12,-.08,z),(.12,-.08,z),(.12,.08,z),(-.12,.08,z),(-.12,-.08,z)],.006,sand)
  for x in[-.1,-.06,-.02,.02,.06,.10]:tube('Basket_weave',[(x,-.08,.01),(x,-.08,.12),(x,.08,.12),(x,.08,.01)],.003,sand)
 elif typ=='tea_pot':lathe('Stoneware_pot',[(0,0),(.07,0),(.085,.06),(.07,.12),(.03,.13),(0,.13)],ceramics[1]);tube('Pouring_spout',[(.06,0,.04),(.12,0,.08),(.14,0,.12)],.018,ceramics[1]);tube('Handle',[(-.06,0,.03),(-.13,0,.06),(-.12,0,.11),(-.06,0,.12)],.012,ceramics[1])
 elif typ=='desk_lamp':lathe('Lamp_base',[(0,0),(.08,0),(.08,.015),(0,.015)],dark);tube('Lamp_arm',[(0,0,.015),(0,0,.22),(.1,0,.33)],.009,gold);lathe('Shade',[(.035,0),(.07,.07),(.065,.075),(.03,.01)],sage,(.1,0,.28))
 elif typ=='headphones':tube('Padded_headband',[(-.07,0,.05),(-.08,0,.18),(0,0,.22),(.08,0,.18),(.07,0,.05)],.011,dark)
 if typ=='headphones':
  for x in[-.07,.07]:o=lathe('Ear_cushion',[(0,0),(.035,0),(.035,.025),(0,.025)],rub,(x,0,.06));o.rotation_euler.y=math.pi/2
 elif typ=='tablet':o=box('Tablet_demo',(0,0,.10),(.20,.012,.27),dark,.009);o.rotation_euler.x=.22;label((0,-.008,.10),.17,.22,31)
 elif typ in['melon','citrus']:
  radius=.08 if typ=='melon'else .045;lathe('Fresh_fruit',[(max(.001,radius*math.sin(math.pi*i/24)),radius-radius*math.cos(math.pi*i/24))for i in range(25)],sage if typ=='melon'else pastry,steps=32)
 elif typ=='bakery_bag':ellipse_body('Paper_bakery_bag',.16,.075,.22,sand);label((0,-.04,.12),.115,.15,25)
 elif typ=='salad':lathe('Salad_bowl',[(.03,0),(.09,.04),(.095,.055),(.085,.05),(.027,.005)],ceramics[0]);
 if typ=='salad':
  for j in range(7):box('Folded_leaf',(.045*math.cos(j),.045*math.sin(j),.055),(.047,.033,.014),sage,.008)
 done('sku_v23_'+typ,{'melon':'food','citrus':'food','bakery_bag':'food','salad':'restaurant','headphones':'electronics','tablet':'electronics'}.get(typ,'home'),'shape-specific merchandise')
# Empty dedicated fixtures. Stock remains a separate data layer.
for typ in ['nested_display','round_tester','bag_wall','shoe_bench_mirror','magazine_cascade','electronics_demo','dining_banquette','racing_cabinet','medal_game','photo_pod']:
 shelves=[]
 if typ=='nested_display':
  for x,z,w,depth in[(-.45,.80,1.3,.85),(.65,.50,.8,.65)]:
   for px in[-w*.4,w*.4]:box('Tapered_leg',(x+px,0,z/2),(.045,depth*.7,z),metal,.006)
   box('Stone_presentation',(x,0,z),(w,depth,.05),stone,.015)
  shelves=[.825,.525]
 elif typ=='round_tester':lathe('Oval_test_counter',[(0,0),(.70,0),(.70,.12),(.65,.15),(.65,.86),(.73,.90),(.73,.94),(0,.94)],stone);tube('Double_mirror_stem',[(0,.20,.94),(0,.20,1.65)],.025,gold);box('Back_to_back_mirror',(0,.20,1.45),(.72,.05,.58),steel,.025);shelves=[.94]
 elif typ=='bag_wall':
  box('Slatted_back',(0,.30,1.1),(2.0,.06,2.2),wood,.015)
  for x in[-.65,0,.65]:
   for z in[.55,1.2,1.85]:tube('Bag_peg',[(x,.25,z),(x,-.12,z)],.012,gold)
  for z in[.48,1.13,1.78]:box('Bag_shelf',(0,0,z),(2.0,.6,.035),white,.008)
  shelves=[.50,1.15,1.80]
 elif typ=='shoe_bench_mirror':
  box('Padded_try_seat',(-.35,0,.46),(1.35,.68,.12),sand,.055)
  for x in[-.85,.15]:box('Try_seat_leg',(x,0,.20),(.05,.52,.40),metal,.007)
  box('Mirror_frame',(.6,.25,1.05),(.62,.08,2.1),gold,.012);box('Full_length_mirror',(.6,.20,1.05),(.55,.012,2.0),steel,.006)
 elif typ=='magazine_cascade':
  for x in[-.85,.85]:box('Rack_leg',(x,0,.75),(.07,.50,1.5),metal,.01)
  for j in range(4):z=.32+j*.38;y=.24-j*.13;o=box('Angled_book_tray',(0,y,z),(1.9,.32,.04),wood,.01);o.rotation_euler.x=-.24;box('Book_stop',(0,y-.15,z+.06),(1.9,.025,.10),gold,.005);shelves.append(z+.06)
 elif typ=='electronics_demo':
  for x in[-.82,.82]:box('Cable_managed_pedestal',(x,0,.40),(.12,.65,.8),white,.012)
  box('Demonstration_worktop',(0,0,.85),(2.0,.85,.065),wood,.012)
  for x in[-.60,0,.60]:box('Demo_security_stand',(x,0,.91),(.14,.15,.06),metal,.008)
  shelves=[.885]
 elif typ=='dining_banquette':
  box('Upholstered_bench',(0,.43,.46),(2.0,.58,.14),sage,.045);box('High_back',(0,.67,.95),(2.05,.12,1.15),sage,.04);box('Plinth',(0,.45,.22),(1.8,.5,.44),wood,.012);box('Dining_top',(0,-.3,.78),(1.55,.70,.045),stone,.015);lathe('Table_pedestal',[(.27,0),(.27,.04),(.05,.05),(.05,.75)],metal,(0,-.3,0));shelves=[.8025]
 elif typ=='racing_cabinet':
  box('Simulator_platform',(0,0,.10),(1.0,1.8,.20),dark,.04);box('Bucket_seat',(0,.35,.48),(.65,.60,.18),blue,.06);o=box('Seat_back',(0,.61,.85),(.65,.14,.85),blue,.06);o.rotation_euler.x=-.15;box('Dashboard',(0,-.42,.86),(.85,.30,.23),dark,.025);o=lathe('Steering_wheel',[(.115,0),(.14,0),(.14,.035),(.115,.035)],rub,(0,-.30,1.06));o.rotation_euler.x=math.pi/2;box('Monitor',(0,-.72,1.45),(.90,.10,.56),blue,.018);label((0,-.777,1.45),.80,.46,31)
 elif typ=='medal_game':lathe('Medal_machine',[(0,0),(.82,0),(.82,.15),(.70,.18),(.70,.75),(.83,.80),(.83,.88),(.58,.90),(.58,1.55),(0,1.55)],blue,steps=12)
 if typ=='medal_game':
  for ang in[0,math.pi/2,math.pi,math.pi*1.5]:
   x,y=.60*math.cos(ang),.60*math.sin(ang);o=box('Player_control',(x,y,.85),(.38,.28,.08),gold,.018);o.rotation_euler.z=ang;lathe('Token_push_button',[(0,0),(.03,0),(.03,.015),(0,.015)],rose,(x,y,.90),20)
 elif typ=='photo_pod':
  # Two genuine 1.15m openings; concave collision preserves room and entrance geometry.
  for x in[-1.4,1.4]:box('Side_wall',(x,0,1.2),(.08,2.8,2.4),rose,.015)
  box('Background_wall',(0,1.36,1.2),(2.8,.08,2.4),sage,.015);box('Roof_sign_frame',(0,0,2.43),(2.88,2.88,.10),white,.02);box('Entry_centre_post',(0,-1.36,1.2),(.30,.08,2.4),rose,.01);box('Camera_panel',(0,-1.41,1.45),(.22,.08,.65),blue,.01);lathe('Camera_lens',[(0,0),(.025,0),(.025,.03),(0,.03)],dark,(0,-1.48,1.65));box('Photo_bench',(0,.94,.45),(2.1,.52,.15),sand,.045);box('Editing_table',(1.77,0,.90),(.62,1.25,.10),stone,.02);box('Editing_screen',(1.81,.27,1.3),(.48,.08,.62),blue,.018);label((1.81,.22,1.3),.42,.54,7);label((0,-1.45,2.20),2.25,.30,13)
 done('fixture_v23_'+typ,'fixture',typ,shelves)
(P/'source/v23/model-bounds.json').write_text(json.dumps(B,indent=2));(P/'source/v23/product-catalog.json').write_text(json.dumps(C,ensure_ascii=False,indent=2));print('V23_ASSETS',len(B))
