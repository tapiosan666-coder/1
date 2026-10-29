"""Original retail merchandise and rooted planting. No image-generation evidence or copied trademarks."""
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];exec((P/'authoring/v17_models.py').read_text().split('# Original campaign products;')[0]);OUT=P/'assets/v19/models';OUT.mkdir(parents=True,exist_ok=True);ART=P/'assets/v19/art';ART.mkdir(exist_ok=True)
from PIL import Image,ImageDraw,ImageFont
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';bold='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc';titles=['森の記憶','街を歩く','春の台所','旅する休日','暮らしの道具','珈琲の時間','小さな庭','建築と光','星を読む','日々の記録','装いのかたち','海辺の物語','こめと穀物','朝のグラノーラ','果実のジャム','完熟トマト'];colors=['#30574a','#a95438','#b79c64','#41607b','#5d6358','#72553e','#526d4d','#8a706a','#343f64','#b6a389','#68616e','#54838c','#80643a','#a56337','#85423e','#9f4638']
im=Image.new('RGB',(1024,1536),'#eee8d8');dr=ImageDraw.Draw(im)
for i,title in enumerate(titles):
 x=(i%4)*256;y=(i//4)*384;col=colors[i];dr.rectangle((x,y,x+255,y+383),fill='#eee8d8');dr.rectangle((x,y,x+255,y+42),fill=col);dr.text((x+128,y+290),title,font=ImageFont.truetype(bold,22),fill=col,anchor='mt');dr.text((x+128,y+335),'ORIGINAL / '+str(i+1).zfill(2),font=ImageFont.truetype(font,13),fill=col,anchor='mt')
 if i%4==0:
  for k in range(9):xx=x+35+k*23;yy=y+200-(k%3)*17;dr.polygon([(xx-20,yy),(xx,yy-90),(xx+20,yy)],fill=col);dr.line((xx,yy,xx,yy+28),fill='#9b7e55',width=3)
 elif i%4==1:
  for k in range(5):xx=x+27+k*45;dr.rectangle((xx,y+155-(k%3)*30,xx+36,y+247),fill=col);dr.rectangle((xx+8,y+180,xx+14,y+188),fill='#eee8d8')
 elif i%4==2:
  dr.ellipse((x+38,y+113,x+218,y+247),fill=col);dr.arc((x+68,y+141,x+190,y+220),0,180,fill='#e8c47c',width=8);dr.line((x+128,y+120,x+153,y+72),fill='#77926a',width=6)
 else:
  dr.polygon([(x,y+231),(x+85,y+119),(x+147,y+211),(x+255,y+141),(x+255,y+254),(x,y+254)],fill=col);dr.ellipse((x+170,y+75,x+215,y+120),fill='#d4ad66')
im.save(ART/'editorial-merchandise-atlas.png',optimize=True);atlas=material('V19_original_cover_packaging_atlas',(1,1,1),.72,texture='assets/v19/art/editorial-merchandise-atlas.png')
def face(x,y,z,w,h,index,reverse=False):
 col=index%4;row=index//4;u0=col/4;u1=(col+1)/4;v0=1-(row+1)/4;v1=1-row/4
 verts=[(x-w/2,y,z-h/2),(x+w/2,y,z-h/2),(x+w/2,y,z+h/2),(x-w/2,y,z+h/2)];uv=[(u0,v0),(u1,v0),(u1,v1),(u0,v1)];return mesh('Printed_original_cover_or_label',verts,[(3,2,1,0)]if reverse else[(0,1,2,3)],atlas,uv)
# Stocked book wall: visible spine titles, irregular heights and face-out editorial selection.
for x in[-1.48,1.48]:box('Library_gable',(x,0,1.18),(.055,.44,2.36),wood,.009)
box('Library_back',(0,.19,1.18),(2.95,.035,2.34),walnut,.005)
for z in[.15,.58,1.01,1.44,1.88,2.30]:box('Library_shelf',(0,0,z),(2.95,.43,.045),wood,.007)
for row,z in enumerate([.18,.61,1.04,1.47]):
 x=-1.39
 for j in range(29):
  w=.066+.01*(j%4);h=.245+.018*((j+row)%5);box('Printed_book_block',(x,0,z+h/2),(w,.22,h),paper,.001);face(x,-.116,z+h/2,w+.002,h,((j*3+row)%12));x+=w+.010
for j in range(5):box('Faceout_book',(-1.12+j*.56,-.11,2.10),(.40,.045,.37),paper,.005);face(-1.12+j*.56,-.136,2.10,.39,.36,j+4)
done('book_editorial_wall')
# Magazine ledges contain distinct covers and visible stacked edges.
for x in[-.75,.75]:box('Magazine_gable',(x,.05,.85),(.055,.62,1.7),wood,.012)
for row in range(4):
 z=.30+row*.39;box('Magazine_ledge',(0,-.13,z),(1.5,.53,.045),wood,.008)
 for j in range(4):
  x=-.57+j*.38;box('Magazine_stack',(x,0,z+.18),(.34,.065,.33),paper,.004);face(x,-.035,z+.18,.33,.32,(j+row*3)%12)
done('magazine_faceout')
# Grocery shelf departments: grains, tins, preserves and boxes, no store-neutral bottle grid.
box('Pantry_plinth',(0,0,.12),(2.2,1.05,.24),walnut,.018);box('Pantry_spine',(0,0,1.02),(2.2,.055,1.8),wood,.012)
for side in[-1,1]:
 for row,z in enumerate([.30,.68,1.06,1.44]):
  box('Commodity_shelf',(0,side*.27,z),(2.18,.51,.04),wood,.006)
  for j in range(7):
   x=-.90+j*.30;y=side*.29;kind=(row+j//3)%4;h=.21+(j%3)*.025
   if kind==0:box('Cereal_carton',(x,y,z+h/2+.03),(.235,.25,h),cream,.006)
   elif kind==1:lathe('Preserve_jar',[(0,0),(.09,0),(.094,.14),(.073,.17),(.073,.19),(0,.19)],clay,(x,y,z+.025),24);lathe('Jar_lid',[(0,0),(.079,0),(.079,.018),(0,.018)],brass,(x,y,z+.215),24);h=.18
   elif kind==2:lathe('Food_tin',[(0,0),(.095,0),(.095,.22),(.09,.225),(0,.225)],steel,(x,y,z+.025),24);h=.20
   else:
    verts=[(x-.115,y-.11,z+.03),(x+.115,y-.11,z+.03),(x+.105,y+.10,z+.03),(x-.105,y+.10,z+.03),(x-.085,y-.07,z+.31),(x+.085,y-.07,z+.31),(x+.075,y+.065,z+.31),(x-.075,y+.065,z+.31)];mesh('Folded_grain_pouch',verts,[(0,1,2,3),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0),(4,7,6,5)],linen);h=.25
   face(x,y+side*.137,z+.03+h/2,.17,h*.85,12+(j+row)%4,reverse=side>0)
done('pantry_gondola')
# Refrigeration differentiates milk, yoghurt tubs and cheese packs within the same protected footprint.
box('Insulated_case',(0,.29,1.12),(3.4,.22,2.24),cream,.035);box('Coldcase_base',(0,0,.12),(3.5,1.0,.24),metal,.025)
for x in[-1.7,1.7]:box('Coldcase_side',(x,0,1.15),(.10,.97,2.3),cream,.02)
box('Case_header',(0,0,2.27),(3.5,1.0,.14),sage,.02)
for row,z in enumerate([.30,.76,1.22,1.68]):
 box('Coldcase_shelf',(0,-.02,z),(3.3,.79,.04),steel,.006)
 for j in range(14):
  x=-1.48+j*.225
  if row%3==0:box('Chilled_carton',(x,-.12,z+.17),(.17,.22,.30),cream,.006);face(x,-.235,z+.17,.16,.28,12+j%4)
  elif row%3==1:lathe('Yoghurt_tub',[(0,0),(.075,0),(.094,.15),(.10,.15),(.10,.16),(0,.16)],cream,(x,-.12,z+.03),24);face(x,-.216,z+.105,.13,.105,14+j%2)
  else:box('Cheese_pack',(x,-.12,z+.10),(.18,.25,.14),linen,.012);face(x,-.247,z+.10,.17,.13,13+j%3)
for x in[-1.1,0,1.1]:box('Coldcase_glazing',(x,-.48,1.30),(1.08,.015,1.82),glass,.004);rail((x+.45,-.51,.99),(x+.45,-.51,1.47),.014,steel)
done('dairy_refrigerator')
# Product shoes: individual toe/vamp/heel surfaces, distinct materials and restrained lacing.
def shoe_product(x,y,z,col,variant=0):
 vs=[];fs=[];length=.26 if variant!=2 else .23;width=.10
 for k in range(11):
  t=k/10;ww=width/2*(.4+.6*math.sin(math.pi*t)**.5);height=.025+.025*math.sin(math.pi*t)+(.075*t**3 if variant==2 else .012*t);zz=z+.045
  for j in range(16):a=j*math.tau/16;vs.append((x+ww*math.sin(a),y-length/2+t*length,zz+height*math.cos(a)))
 for k in range(10):
  for j in range(16):a=k*16+j;b=k*16+(j+1)%16;fs.append((a,b,b+16,a+16))
 mesh('Designed_shoe_upper',vs,fs,col);box('Layered_sole',(x,y,z+.02),(.104,length,.035),rubber,.015)
 if variant==0:
  for k in range(4):rail((x-.025,y-.02+k*.018,z+.09),(x+.025,y-.02+k*.018,z+.09),.0014,linen)
for x in[-.85,.85]:box('Footwear_bay_side',(x,.15,1.1),(.065,.60,2.2),wood,.012)
box('Footwear_bay_back',(0,.42,1.1),(1.7,.04,2.2),sage,.01)
for row,z in enumerate([.24,.82,1.40]):
 box('Footwear_display_shelf',(0,.08,z),(1.7,.65,.05),wood,.01)
 for pair in range(3):
  for side in[-1,1]:shoe_product(-.55+pair*.55+side*.065,-.04,z+.04,fabrics[(pair+row)%5],(pair+row)%3)
box('Footwear_header',(0,.05,2.10),(1.7,.60,.20),cream,.015);done('shoe_wall_bay')
box('Try_on_bench_support',(0,0,.19),(1.6,.70,.38),wood,.025);box('Try_on_bench_cushion',(0,0,.45),(1.65,.74,.15),linen,.04);done('shoe_fitting_bench')
# Footwear arrival table and fitted mirror form the try-on department.
box('Footwear_table_base',(0,0,.40),(1.8,.82,.80),wood,.025);box('Footwear_table_stone',(0,0,.84),(1.90,.90,.08),stone,.02)
for i in range(3):
 for side in[-1,1]:shoe_product(-.57+i*.57+side*.06,0,.90,fabrics[i],i)
done('shoe_display_table')
box('Fitting_mirror_back',(0,.02,1.1),(.66,.08,2.2),wood,.012);box('Fitting_mirror_face',(0,-.026,1.12),(.59,.008,1.96),steel,.005);done('shoe_fitting_mirror')
# Anatomically plausible hanging garments: shaped shoulder seams, open cuffs and collar.
for x in[-.95,.95]:pole((x,0,.12),.025,1.65,brass)
rail((-.95,0,1.72),(.95,0,1.72),.025,brass);box('Apparel_lower_display',(0,.08,.15),(2.15,.48,.10),wood,.01)
for k in range(4):
 cx=-.72+k*.48;rail((cx,0,1.70),(cx,0,1.58),.003,metal);tube('Wooden_hanger',[(cx-.16,0,1.48),(cx,0,1.58),(cx+.16,0,1.48)],.008,wood)
 outline=[(-.18,1.48),(-.25,1.34),(-.28,1.12),(-.20,1.11),(-.145,1.32),(-.13,.82),(.13,.82),(.145,1.32),(.20,1.11),(.28,1.12),(.25,1.34),(.18,1.48),(.055,1.53),(-.055,1.53)];verts=[]
 for yy in[-.035,.035]:
  for xx,zz in outline:verts.append((cx+xx,yy+.008*math.sin(zz*33+k),zz))
 n=len(outline);faces=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]+[(j,(j+1)%n,(j+1)%n+n,j+n)for j in range(n)];o=mesh('Cut_and_sewn_hanging_blouse',verts,faces,fabrics[k%5]);mod=o.modifiers.new('Fabric_edge_rounding','BEVEL');mod.width=.004;mod.segments=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 tube('Visible_front_placket',[(cx,-.041,.85),(cx,-.041,1.45)],.0013,linen)
done('apparel_capsule')
# Same protected footprint as v18 lounge, with supported stems and layered leaf blades.
lathe('Lounge_planter',[(0,0),(.65,0),(.75,.12),(.75,.62),(.64,.67),(.55,.67),(.55,.58),(0,.58)],stone,(-1.25,0,0),40)
box('Lounge_seat_base',(.75,0,.22),(2.8,.82,.44),wood,.04);box('Lounge_seat_cushion',(.75,-.03,.47),(2.75,.78,.14),linen,.05);box('Lounge_back',(.75,.34,.79),(2.75,.13,.65),wood,.025)
tube('Rooted_ficus_trunk',[(-1.25,0,.60),(-1.22,.02,1.12),(-1.25,.025,1.55),(-1.23,.02,1.91)],.023,walnut)
for k in range(28):
 a=k*2.39996;h=.94+(k%9)*.115;r=.20+(k%4)*.055;base=np.array([-1.23,.02,h]);tip=base+np.array([r*math.cos(a),r*math.sin(a),.06]);tube('Supported_ficus_petiole',[base,(base+tip)/2,tip],.0045,leafm[0]);direction=np.array([math.cos(a),math.sin(a),.23]);side=np.array([-math.sin(a),math.cos(a),0.]);verts=[]
 for i in range(9):
  t=i/8;width=.105*math.sin(math.pi*t)**.7
  for j in range(5):
   u=j/4*2-1;point=tip+direction*(t*.25)+side*width*u+np.array([0,0,.025*(1-u*u)-.06*t*t]);verts.append(point.tolist())
 faces=[(i*5+j,i*5+j+1,(i+1)*5+j+1,(i+1)*5+j)for i in range(8)for j in range(4)];mesh('Veined_ficus_leaf',verts,faces,leafm[k%3])
done('integrated_lounge')
# Homeware wall departments: storage textiles, tableware, mugs and flower vases.
for x in[-1.3,1.3]:box('Homeware_gable',(x,.10,1.08),(.07,.59,2.16),wood,.012)
box('Homeware_back',(0,.38,1.08),(2.6,.055,2.16),cream,.01)
for row,z in enumerate([.15,.65,1.15,1.65]):
 box('Homeware_shelf',(0,.10,z),(2.6,.60,.05),wood,.01)
 for j in range(6):
  x=-1.04+j*.42
  if row==0:
   box('Woven_storage_box',(x,.04,z+.13),(.35,.36,.22),linen,.02)
   for k in range(3):box('Rolled_linen_fold',(x,.02,z+.27+k*.028),(.30,.27,.026),fabrics[(j+k)%5],.008)
  elif row==1:
   for k in range(3):lathe('Stacked_ceramic_plate',[(0,0),(.09,0),(.16,.025),(.16,.04),(.10,.02),(0,.02)],ceramics[j%3],(x,.04,z+.04+k*.028),28)
  elif row==2:
   lathe('Glazed_coffee_mug',[(0,0),(.072,0),(.078,.15),(.068,.16),(.06,.14),(.06,.02),(0,.02)],ceramics[j%3],(x,.04,z+.03),28);tube('Mug_joined_handle',[(x+.07,.04,z+.17),(x+.125,.04,z+.16),(x+.125,.04,z+.07),(x+.07,.04,z+.065)],.011,ceramics[j%3])
  else:lathe('Flower_vase',[(0,0),(.07,0),(.10,.09),(.055,.22),(.045,.28),(.035,.28),(.042,.22),(.085,.09),(.06,.02),(0,.02)],ceramics[j%3],(x,.04,z+.03),32)
done('homeware_category_wall')
# Cosmetics: distinct categories and tester trays. Original typographic packaging, no real brands.
ci=Image.new('RGB',(512,512),'#e5ded0');cd=ImageDraw.Draw(ci);cd.rectangle((0,0,512,64),fill='#4e6760');cd.text((256,100),'LUNE / SOIN',font=ImageFont.truetype(bold,46),fill='#4e6760',anchor='mt');cd.ellipse((160,195,352,387),outline='#af8b52',width=8);cd.line((256,206,256,375),fill='#af8b52',width=5);cd.text((256,425),'ESSENCE  /  TESTER',font=ImageFont.truetype(font,24),fill='#4e6760',anchor='mt');ci.save(ART/'cosmetic-label.png',optimize=True);cosmetic=material('V19_cosmetic_label',(1,1,1),.48,texture='assets/v19/art/cosmetic-label.png')
def cosmetic_front(x,y,z,w,h):mesh('Cosmetic_product_label',[(x-w/2,y,z-h/2),(x+w/2,y,z-h/2),(x+w/2,y,z+h/2),(x-w/2,y,z+h/2)],[(0,1,2,3)],cosmetic,[(0,0),(1,0),(1,1),(0,1)])
def cosmetic_product(x,y,z,kind):
 if kind==0:
  lathe('Essence_glass_flacon',[(0,0),(.042,0),(.043,.15),(.025,.18),(.025,.20),(0,.20)],clay,(x,y,z),24);lathe('Dropper_cap',[(0,0),(.027,0),(.027,.045),(0,.045)],metal,(x,y,z+.20),20);cosmetic_front(x,y-.044,z+.09,.062,.10)
 elif kind==1:
  lathe('Face_cream_jar',[(0,0),(.065,0),(.065,.07),(.061,.08),(0,.08)],cream,(x,y,z),24);lathe('Cream_metal_lid',[(0,0),(.069,0),(.069,.018),(0,.018)],brass,(x,y,z+.08),24);cosmetic_front(x,y-.066,z+.045,.075,.045)
 else:
  box('Fragrance_bottle',(x,y,z+.09),(.09,.065,.18),clay,.01);box('Fragrance_atomiser',(x,y,z+.19),(.035,.035,.025),brass,.004);box('Fragrance_cap',(x,y,z+.225),(.06,.05,.06),metal,.008);cosmetic_front(x,y-.034,z+.09,.08,.12)
for x in[-1.3,1.3]:box('Beauty_wall_gable',(x,.12,1.1),(.065,.55,2.2),cream,.012)
box('Beauty_wall_back',(0,.38,1.1),(2.6,.05,2.2),sage,.012)
for row,z in enumerate([.25,.70,1.15,1.60]):
 box('Illuminated_product_shelf',(0,.10,z),(2.6,.58,.045),stone,.007)
 for j in range(10):cosmetic_product(-1.10+j*.245,.06,z+.04,(row+j//4)%3)
 box('Shelf_light_diffuser',(0,-.16,z-.035),(2.5,.035,.025),linen,.004)
done('beauty_wall_testers')
# Electronics: a real work/demo station, supported screens, keyboards, headphones and tethers.
box('Electronics_demo_base',(0,0,.45),(2.7,.77,.90),walnut,.025);box('Electronics_demo_top',(0,0,.94),(2.85,.91,.08),stone,.025)
for x in[-.90,0,.90]:
 box('Display_foot',(x,.12,1.0),(.37,.23,.035),metal,.008);box('Display_stalk',(x,.17,1.19),(.055,.05,.37),metal,.007);box('Demo_monitor',(x,.18,1.49),(.72,.045,.43),metal,.012);face(x,.154,1.49,.68,.39,(int((x+.9)*10)+7)%12)
 box('Keyboard',(x,-.19,1.015),(.56,.20,.035),metal,.009)
 for row in range(4):
  for j in range(12):box('Individual_keycap',(x-.24+j*.043,-.26+row*.045,1.04),(.035,.032,.014),linen,.002)
 tube('Security_tether',[(x,.22,1.02),(x+.20,.25,1.04),(x+.25,.18,1.02)],.0025,metal)
done('electronics_demo_bar')
# Cafe production line: espresso heads, steaming wand, grinder, sink and a clear counter programme.
box('Cafe_cabinet',(0,.04,.46),(3.4,.78,.92),sage,.03);box('Cafe_worktop',(0,0,.96),(3.5,.91,.07),steel,.02);box('Cafe_opaque_splashback',(0,.44,1.36),(3.5,.045,.72),cream,.01)
box('Espresso_machine',(0.65,.05,1.22),(1.17,.56,.49),steel,.025);box('Espresso_control_face',(.65,-.24,1.27),(1.04,.025,.22),metal,.006);box('Drip_tray',(.65,-.25,1.01),(1.15,.36,.035),steel,.007)
for x in[.36,.94]:
 lathe('Group_head',[(0,0),(.067,0),(.067,.055),(0,.055)],metal,(x,-.17,1.11),24);rail((x,-.17,1.13),(x,-.43,1.13),.015,metal);lathe('Waiting_coffee_cup',[(0,0),(.045,0),(.052,.08),(.044,.09),(.036,.07),(.035,.01),(0,.01)],cream,(x,-.25,1.035),24)
tube('Steam_wand',[(1.18,-.16,1.18),(1.24,-.26,1.13),(1.24,-.28,1.05)],.007,steel)
lathe('Grinder_motor',[(0,0),(.12,0),(.12,.29),(.10,.34),(0,.34)],metal,(-.42,.12,.99),28);lathe('Bean_hopper',[(0,0),(.07,0),(.13,.22),(.14,.24),(0,.24)],clay,(-.42,.12,1.33),28)
box('Kitchen_sink_rim',(-1.08,0,1.01),(.68,.55,.035),steel,.01);box('Kitchen_sink_recess',(-1.08,0,1.02),(.54,.40,.009),metal,.01);tube('Cafe_sink_tap',[(-1.08,.20,1.02),(-1.08,.20,1.33),(-1.08,-.07,1.33),(-1.08,-.12,1.22)],.015,steel);done('cafe_kitchen_line')

print('V19_MODELS_COMPLETE')
