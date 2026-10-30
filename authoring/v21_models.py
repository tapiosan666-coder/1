"""Original metric retail kit: separate fixtures and shape-distinct product SKUs. No character authoring."""
from pathlib import Path
import sys,math,json,random
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from v21_blender_common import *
from PIL import Image,ImageDraw,ImageFont
ART=P/'assets/v21/art';ART.mkdir(parents=True,exist_ok=True)
# New original package/cover atlas; not a borrowed brand or evidence image.
im=Image.new('RGB',(1024,1024),'#eee5d2');dr=ImageDraw.Draw(im);font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';bold='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc';titles=['都市と余白','小さな庭','珈琲の時間','旅する食卓','森の図鑑','光の記憶','週末の台所','海辺の物語','暮らしの道具','月と散歩','青の手紙','花と器','DAILY OAT','CITRUS TEA','PURE CARE','BOTANIC','FRESH MILK','NUTS & FRUIT','SAVON','GRANOLA','ROAST BEANS','OLIVE OIL','RICE NOODLES','HERB SOAP','SAKURA LIP','SILK POWDER','HYDRA CREAM','EAU VERTE','COLOR STUDIO','DAILY SERUM','PURE MIST','VOLUME 21']
cols=['#29473e','#aa694d','#32485f','#82705a','#465b44','#7d4d68','#ce9e57','#456e78']
for i,title in enumerate(titles):
 x=i%8*128;y=i//8*256;col=cols[i%8];dr.rectangle((x+2,y+2,x+125,y+253),fill='#f1e8d6');dr.rectangle((x+2,y+2,x+125,y+35),fill=col);dr.ellipse((x+21,y+65,x+110,y+153),fill=col);dr.line((x+22,y+145,x+105,y+75),fill='#dcc6a5',width=5);dr.text((x+64,y+178),title,font=ImageFont.truetype(bold,12),fill=col,anchor='mm');dr.text((x+64,y+212),'FIND / ORIGINAL',font=ImageFont.truetype(font,9),fill=col,anchor='mm');dr.text((x+64,y+234),'COLLECTION %02d'%i,font=ImageFont.truetype(font,8),fill=col,anchor='mm')
im.save(ART/'product-atlas.png',optimize=True);atlas=material('FY21_original_packaging',(1,1,1),.63,texture='assets/v21/art/product-atlas.png')
cream=material('FY21_chalk_lacquer',(.75,.72,.65),.4);sage=material('FY21_sage',(.12,.27,.23),.5);navy=material('FY21_navy',(.025,.065,.11),.48);pink=material('FY21_rose',(.48,.24,.28),.58);screen=material('FY21_display_screen',(.025,.10,.17),.19);leaf=material('FY21_fresh_leaf',(.12,.31,.065),.71);red=material('FY21_tomato',(.55,.065,.025),.4);carrot=material('FY21_carrot',(.72,.28,.045),.6)
BOUNDS={};CAT={};base_finish=finish
category='fixture'
def done(name,role):
 bpy.context.view_layer.update();pts=[o.matrix_world@Vector(c)for o in bpy.context.scene.objects if o.type in['MESH','CURVE']for c in o.bound_box];lo=[min(v[i]for v in pts)for i in range(3)];hi=[max(v[i]for v in pts)for i in range(3)];BOUNDS[name]={'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]],'unit':'metres'};CAT[name]={'category':category,'role':role,'source':'Original Blender authored geometry; CC0 wood textures inherited with project licences','repeated_colour_is_not_a_new_shape':True};base_finish(name);(P/'source/v21/model-bounds.json').write_text(json.dumps(BOUNDS,indent=2));(P/'source/v21/product-catalog.json').write_text(json.dumps(CAT,indent=2))
def pole(p,r,h,mat=metal):return lathe('Machined_profile',[(0,0),(r,0),(r,h),(0,h)],mat,p,24)
def label(x,y,z,w,h,index):
 u=index%8/8;v=1-(index//8+1)/4;return mesh('Printed_original_label',[(x-w/2,y,z-h/2),(x+w/2,y,z-h/2),(x+w/2,y,z+h/2),(x-w/2,y,z+h/2)],[(0,1,2,3)],atlas,[(u,v),(u+.125,v),(u+.125,v+.25),(u,v+.25)])
def ell(name,p,scale,mat):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=p);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(mat)
 for f in o.data.polygons:f.use_smooth=True
 return o
# Furniture is empty; products are separate instances assigned by store/department/SKU.
for variant in ['table','low_island','wall_bay','library_bay','beauty_island','checkout','cold_case','produce_bin']:
 w=2.0;d=.9;h=.78 if variant in ['table','produce_bin']else 1.15 if variant in ['low_island','beauty_island','checkout']else 2.05
 for x in[-.86,.86]:box('Recessed_support',(x,.05,.13),(.09,.65,.26),metal,.012)
 box('Finished_plinth',(0,.05,.23),(w,.82,.20),wood,.014)
 if variant in ['wall_bay','library_bay','cold_case']:box('Opaque_back',(0,.37,h/2),(w,.065,h),sage if variant=='cold_case'else walnut,.012)
 levels=[.78]if variant=='table'else [.92]if variant in ['checkout','beauty_island']else [.32,.78,1.24,1.70]if h>2 else [.35,.80]
 for z in levels:box('Shelf_with_edge_lip',(0,0,z),(w,.88,.055),cream if variant in ['beauty_island','cold_case']else wood,.012)
 if variant=='checkout':box('Accessible_counter',(-.7,0,.79),(.6,.95,.08),stone,.012);box('Till_stand',(.5,.12,1.03),(.10,.15,.24),metal,.008);o=box('POS_terminal',(.5,.08,1.20),(.38,.08,.24),screen,.015);o.rotation_euler.x=-.2
 if variant=='beauty_island':box('Mirror_frame',(0,.30,1.45),(1.0,.06,1.0),brass,.025);box('Mirror',(0,.263,1.45),(.92,.008,.90),steel,.004)
 if variant=='cold_case':
  for x in[-.96,.96]:box('Insulated_gable',(x,0,1.05),(.09,.94,2.1),cream,.018)
  box('Condenser_header',(0,0,2.12),(2.0,.94,.18),sage,.014)
  for i in range(9):box('Vent_slot',(-.8+i*.20,-.48,2.12),(.12,.012,.018),metal,.002)
 if variant=='produce_bin':
  for x in[-.5,.5]:box('Angled_crate',(x,0,.88),(.89,.77,.09),walnut,.008)
 done('fixture_'+variant,'dedicated empty fixture')
# Apparel rails and changing booth.
category='apparel'
for x in[-.9,.9]:tube('Rack_foot',[(x,-.30,.025),(x,0,.035),(x,.30,.025)],.025,metal);pole((x,0,.02),.022,1.7)
tube('Garment_rail',[(-.9,0,1.70),(.9,0,1.70)],.023,brass);done('fixture_apparel_rail','hanging garments')
# True different silhouette meshes: short sleeve, long sleeve, coat, skirt, trousers.
for variant in ['short_sleeve','long_sleeve','coat','skirt','trousers']:
 mat=fabrics[['short_sleeve','long_sleeve','coat','skirt','trousers'].index(variant)];verts=[];faces=[]
 if variant=='trousers':
  for side in[-1,1]:
   start=len(verts)
   for j in range(12):
    t=j/11;z=.75-t*.72;rx=.115-.045*t
    for k in range(20):a=k*math.tau/20;verts.append((side*.10+math.cos(a)*rx,math.sin(a)*.055,z))
   for j in range(11):
    for k in range(20):a=start+j*20+k;b=start+j*20+(k+1)%20;faces.append((a,b,b+20,a+20))
 else:
  length=.92 if variant=='coat'else .58 if variant=='skirt'else .64
  for j in range(20):
   t=j/19;rx=(.13+.18*t)if variant=='skirt'else .09+.14*min(t/.18,1);ry=.045+.025*math.sin(t*math.pi)
   for k in range(24):a=k*math.tau/24;fold=.006*t*math.sin(k*math.tau*7/24+t);verts.append((math.cos(a)*(rx+fold),math.sin(a)*(ry+fold),length*(1-t)))
  for j in range(19):
   for k in range(24):a=j*24+k;b=j*24+(k+1)%24;faces.append((a,b,b+24,a+24))
  if variant in ['short_sleeve','long_sleeve','coat']:
   for side in[-1,1]:
    st=len(verts);sl=.20 if variant=='short_sleeve'else .49
    for j in range(10):
     t=j/9
     for k in range(16):a=k*math.tau/16;r=.078-.038*t;verts.append((side*(.2+.14*t)+math.cos(a)*r*.55,math.sin(a)*r,length-.12-sl*t))
    for j in range(9):
     for k in range(16):a=st+j*16+k;b=st+j*16+(k+1)%16;faces.append((a,b,b+16,a+16))
 o=mesh('Shaped_cloth_'+variant,verts,faces,mat);sol=o.modifiers.new('Fabric_thickness','SOLIDIFY');sol.thickness=.002
 if variant=='coat':
  for z in[.35,.50,.65]:pole((0,-.071,z),.008,.004,brass)
 tube('Hanger',[(-.20,0,.80),(.0,0,.94),(.20,0,.80),(-.20,0,.80)],.006,wood);tube('Hook',[(0,0,.94),(0,0,1.01),(.03,0,1.05),(.05,0,1.02)],.003,metal);done('sku_'+variant,'shape-distinct garment')
# Folded garments are cloth surfaces with a collar/seam, not hanging models floating above a table.
for kind in ['knit','trousers']:
 verts=[];faces=[]
 for j in range(17):
  y=-.16+j*.02
  for i in range(23):
   x=-.22+i*.02;z=.045+.004*math.sin(i*.7+j*.15)+.003*math.sin(j*.6);verts.append((x,y,z))
 for j in range(16):
  for i in range(22):a=j*23+i;faces.append((a,a+1,a+24,a+23))
 o=mesh('Folded_cloth_surface',verts,faces,fabrics[1]if kind=='knit'else fabrics[0]);sol=o.modifiers.new('Folded_fabric_thickness','SOLIDIFY');sol.thickness=.035
 tube('Folded_hem',[(-.21,-.15,.052),(0,-.15,.054),(.21,-.15,.052)],.003,cream)
 if kind=='knit':tube('Folded_neckline',[(-.07,.10,.06),(-.05,.055,.06),(0,.04,.06),(.05,.055,.06),(.07,.10,.06)],.007,fabrics[1])
 else:tube('Trouser_crease',[(0,-.14,.055),(0,0,.056),(0,.14,.055)],.003,brass)
 done('sku_folded_'+kind,'folded garment with cloth seams')
for x in[-.8,.8]:box('Fitting_partition',(x,0,1.15),(.06,1.60,2.30),cream,.012)
box('Fitting_back',(0,.77,1.15),(1.60,.06,2.30),cream,.012);box('Fitting_mirror',(0,.73,1.25),(.65,.008,1.6),steel,.004)
for j in range(7):tube('Curtain_fold',[(.28+j*.07,-.73,.10),(.28+j*.07,-.76,1.2),(.28+j*.07,-.73,2.2)],.043,fabrics[2])
done('fixture_fitting','fitting booth with open entrance')
# Home: glazed vessels with actual inner surfaces, kitchen tools, folded textiles, lamps.
category='home'
for variant in ['cup','bowl','vase']:
 r=.09 if variant=='cup'else .16;h=.13 if variant=='cup'else .10 if variant=='bowl'else .29
 lathe('Open_ceramic_'+variant,[(0,0),(r*.65,0),(r,.03),(r*.9,h),(r*.78,h),(r*.75,.03),(0,.03)],ceramics[['cup','bowl','vase'].index(variant)],steps=32)
 if variant=='cup':tube('Cup_handle',[(.08,0,.11),(.14,0,.12),(.15,0,.04),(.08,0,.04)],.012,ceramics[0])
 done('sku_'+variant,'ceramic houseware')
for i in range(3):box('Folded_towel',(0,0,.035+i*.065),(.42,.29,.06),fabrics[i],.025)
done('sku_towels','soft home textile')
lathe('Lamp_base',[(0,0),(.12,0),(.12,.03),(.018,.05),(.018,.36),(0,.36)],brass);lathe('Open_lamp_shade',[(.16,.28),(.10,.48),(.09,.48),(.15,.28)],cream);done('sku_lamp','table lamp')
for y in[-.32,.32]:box('Chair_stretcher',(0,y,.25),(.42,.045,.045),wood,.008)
for x in[-.24,.24]:
 for y in[-.24,.24]:tube('Chair_leg',[(x,y,0),(x*.9,y*.9,.45)],.025,wood)
box('Chair_seat',(0,0,.46),(.56,.57,.10),fabrics[1],.045);box('Chair_back',(0,.25,.78),(.56,.10,.55),fabrics[1],.05);done('sku_chair','model room seating')
# Beauty: packaging shape differs, with lipstick, compact, perfume, tube and brush.
category='beauty'
for variant in ['serum','lipstick','perfume','compact','cream','brush']:
 if variant=='lipstick':pole((0,0,0),.025,.07,metal);pole((0,0,.07),.018,.04,pink)
 elif variant=='compact':lathe('Powder_case',[(0,0),(.065,0),(.065,.018),(.058,.025),(0,.025)],brass);lathe('Powder_pan',[(0,0),(.052,0),(.052,.008),(0,.008)],cream,(0,0,.025));label(0,-.067,.017,.10,.03,25)
 elif variant=='perfume':box('Perfume_glass',(0,0,.08),(.105,.055,.16),glass,.012);pole((0,0,.16),.018,.035,brass);label(0,-.029,.08,.08,.10,27)
 elif variant=='brush':pole((0,0,0),.008,.14,metal);ell('Soft_brush',(0,0,.16),(.026,.023,.045),fabrics[1])
 else:
  r=.04 if variant=='serum'else .06;h=.18 if variant=='serum'else .075;lathe('Product_vessel',[(0,0),(r,0),(r,h),(r*.85,h+.01),(0,h+.01)],cream);pole((0,0,h+.01),r*.7,.025,brass);label(0,-r-.001,h/2,r*1.6,h*.65,29 if variant=='serum'else 26)
 done('sku_'+variant,'cosmetic '+variant)
# Electronics: each appliance is a different model, not one box rescaled.
category='electronics'
for variant in ['tv','laptop','phone','fridge','washer','vacuum','speaker','kettle']:
 if variant=='tv':box('Television_bezel',(0,0,.65),(1.35,.055,.80),metal,.018);box('Television_screen',(0,-.031,.65),(1.30,.006,.75),screen,.006);tube('TV_stand',[(-.42,-.12,0),(0,0,.23),(.42,-.12,0)],.025,metal)
 elif variant=='laptop':box('Notebook_keyboard',(0,0,.015),(.36,.25,.03),steel,.009);o=box('Notebook_screen',(0,.11,.15),(.36,.02,.28),metal,.01);o.rotation_euler.x=-.13;label(0,.092,.15,.33,.23,31)
 elif variant=='phone':o=box('Phone_chassis',(0,0,.073),(.072,.012,.146),metal,.01);box('Phone_display',(0,-.007,.073),(.065,.003,.132),screen,.008)
 elif variant=='fridge':
  box('Fridge_body',(0,0,.90),(.70,.67,1.80),steel,.035)
  for z,h in[(.48,.88),(1.36,.82)]:box('Independent_fridge_door',(0,-.35,z),(.68,.055,h),cream,.018);tube('Recessed_handle',[(.24,-.39,z-.18),(.24,-.39,z+.18)],.014,metal)
 elif variant=='washer':box('Appliance_cabinet',(0,0,.43),(.62,.62,.86),cream,.025);o=lathe('Washer_round_door',[(0,0),(.24,0),(.26,.04),(.22,.07),(.18,.06),(0,.06)],steel,steps=40);o.rotation_euler.x=math.pi/2;o.location=(0,-.32,.43);box('Control_panel',(0,-.322,.76),(.55,.015,.11),metal,.008)
 elif variant=='vacuum':tube('Vacuum_wand',[(0,0,.05),(0,.04,.70),(0,.15,1.04)],.025,steel);box('Vacuum_motor',(0,.10,.87),(.12,.20,.20),navy,.025);box('Floor_head',(0,0,.05),(.32,.18,.09),metal,.02)
 elif variant=='speaker':box('Audio_cabinet',(0,0,.30),(.24,.22,.60),walnut,.018);o=lathe('Speaker_cone',[(0,0),(.08,0),(.09,.02),(.06,.04),(0,.05)],metal,steps=32);o.rotation_euler.x=math.pi/2;o.location=(0,-.12,.27)
 else:lathe('Kettle_body',[(0,0),(.10,0),(.11,.12),(.07,.22),(.045,.24),(0,.24)],steel);tube('Kettle_handle',[(.08,0,.20),(.17,0,.22),(.17,0,.05),(.10,0,.04)],.016,metal);tube('Pour_spout',[(-.07,0,.15),(-.16,0,.19),(-.18,0,.22)],.026,steel)
 done('sku_'+variant,'appliance '+variant)
# Full-height original spine typography, separate from the cover atlas.
spine_image=Image.new('RGB',(576,512),'#e8dfc8');spinedraw=ImageDraw.Draw(spine_image)
for i in range(12):
 x=i*48;spinedraw.rectangle((x,0,x+47,511),fill=cols[i%8]);spinedraw.rectangle((x+5,26,x+42,34),fill='#ddc89a')
 for j,ch in enumerate(titles[i][:8]):spinedraw.text((x+24,62+j*42),ch,font=ImageFont.truetype(bold,24),fill='#f3edde',anchor='mt')
 spinedraw.text((x+24,456),'%02d'%i,font=ImageFont.truetype(font,15),fill='#f3edde',anchor='mt')
spine_image.save(ART/'book-spines-original.png',optimize=True);spine_print=material('FY21_original_spines',(1,1,1),.72,texture='assets/v21/art/book-spines-original.png')
# Books: format, thickness and full cover artwork differ, each independent SKU.
category='book'
for k,(w,h,t)in enumerate([(.105,.15,.022),(.14,.21,.030),(.20,.28,.008),(.13,.18,.017),(.23,.25,.025),(.27,.32,.035)]):
 for edition in range(2):
  box('Bound_pageblock',(0,0,h/2),(w*.94,t*.9,h*.96),paper,.001)
  for y in[-t/2,t/2]:box('Book_cover',(0,y,h/2),(w,t*.08,h),bookmats[k],.001)
  label(0,-t*.55,h/2,w*.96,h*.96,k*2+edition);box('Book_spine',(-w/2,0,h/2),(.003,t,h),bookmats[(k+edition)%6],.001);tile=(k*2+edition)/12;mesh('Original_printed_spine',[(-w/2-.002,t/2,0),(-w/2-.002,-t/2,0),(-w/2-.002,-t/2,h),(-w/2-.002,t/2,h)],[(0,1,2,3)],spine_print,[(tile,0),(tile+1/12,0),(tile+1/12,1),(tile,1)]);done('sku_book_'+str(k)+'_'+str(edition),'paperback/hardback/magazine/comic/children/photo')
# Food departments: recognisable products with separate equipment assignment.
category='food'
for variant in ['tomatoes','cabbage','carrots','fish','meat','deli','bread','drink','frozen','snack']:
 if variant=='tomatoes':
  for x,y in[(-.12,-.08),(.09,-.07),(-.06,.10),(.14,.10)]:ell('Ripe_tomato',(x,y,.08),(.08,.08,.075),red);tube('Tomato_stem',[(x,y,.15),(x+.025,y,.17)],.007,leaf)
 elif variant=='cabbage':
  ell('Cabbage_heart',(0,0,.13),(.14,.13,.13),leaf)
  for k in range(6):a=k*math.tau/6;o=ell('Cabbage_leaf',(.07*math.cos(a),.07*math.sin(a),.14),(.11,.065,.13),leaf);o.rotation_euler.z=a
 elif variant=='carrots':
  for k in range(3):o=lathe('Tapered_carrot',[(0,0),(.008,0),(.032,.18),(.025,.24),(0,.24)],carrot,(-.08+k*.08,0,0),24);o.rotation_euler.x=.6;tube('Carrot_greens',[(-.08+k*.08,-.13,.18),(-.08+k*.08,-.17,.30)],.012,leaf)
 elif variant=='fish':box('Fish_tray',(0,0,.015),(.36,.20,.03),cream,.012);ell('Whole_fish_body',(0,0,.065),(.14,.047,.045),steel);mesh('Fish_tail',[(.10,0,.05),(.20,-.06,.05),(.20,.06,.05)],[(0,1,2)],steel);ell('Fish_eye',(-.10,-.04,.08),(.007,.004,.007),metal)
 elif variant=='meat':box('Meat_tray',(0,0,.018),(.33,.24,.036),metal,.012);ell('Fresh_cut',(0,0,.05),(.14,.095,.035),pink);tube('Fat_marbling',[(-.10,0,.08),(-.04,.02,.086),(.02,-.02,.086),(.10,0,.08)],.006,cream)
 elif variant=='deli':box('Lunch_tray',(0,0,.02),(.30,.23,.04),metal,.01);box('Rice_portion',(-.065,0,.06),(.13,.18,.05),paper,.016);ell('Prepared_cutlet',(.07,.02,.06),(.06,.08,.028),pastry);ell('Greens',(.08,-.07,.06),(.045,.03,.035),leaf)
 elif variant=='bread':ell('Baguette',(0,0,.07),(.24,.065,.065),pastry)
 elif variant=='drink':lathe('Bottle_with_neck',[(0,0),(.04,0),(.04,.17),(.023,.20),(.017,.21),(.017,.24),(0,.24)],glass);label(0,-.041,.11,.065,.10,13)
 else:box('Branded_food_pack',(0,0,.13),(.16,.09,.26),cream,.006);label(0,-.047,.13,.15,.24,17 if variant=='snack'else 22)
 done('sku_'+variant,'food department '+variant)
# Restaurant/kitchen and amusement equipment.
category='dining'
box('Kitchen_line',(0,0,.46),(2.1,.72,.92),steel,.018)
for x in[-.60,0,.60]:pole((x,0,.93),.18,.018,metal)
box('Extraction_hood',(0,.12,2.0),(2.2,.9,.30),steel,.04);done('fixture_kitchen','closed preparation equipment, not a working cooking simulation')
lathe('Cafe_table',[(0,0),(.28,0),(.28,.04),(.05,.08),(.05,.72),(.52,.72),(.52,.77),(0,.77)],wood);done('fixture_cafe_table','cafe customer table')
# Dedicated bistro meal and barista equipment distinguish dining from cafe furniture.
lathe('Porcelain_dinner_plate',[(0,0),(.18,0),(.27,.025),(.28,.045),(.25,.055),(.16,.045),(0,.04)],cream,steps=40)
for i in range(5):
 tube('Pasta_ribbon',[(-.13+i*.045,-.10,.07),(-.10+i*.04,.02,.095),(-.12+i*.04,.12,.065)],.012,pastry)
for x,y in[(-.12,.08),(.13,-.06),(.08,.13)]:ell('Herb_garnish',(x,y,.10),(.035,.018,.008),leaf)
tube('Fork_handle',[(.24,-.15,.065),(.24,.02,.065)],.008,steel)
for off in[-.018,0,.018]:tube('Fork_tine',[(.24+off,.01,.065),(.24+off,.08,.065)],.003,steel)
done('sku_bistro_plate','plated restaurant meal, not a cafe bread display')
lathe('Coffee_saucer',[(0,0),(.13,0),(.14,.02),(.11,.035),(0,.025)],cream,steps=32);lathe('Coffee_cup',[(0,0),(.06,0),(.08,.10),(.07,.12),(.055,.11),(.05,.02),(0,.02)],cream,(0,0,.03),32);tube('Cup_handle',[(.07,0,.13),(.13,0,.14),(.13,0,.07),(.075,0,.06)],.012,cream);lathe('Coffee_surface',[(0,0),(.061,0),(.061,.003),(0,.003)],walnut,(0,0,.13),32);done('sku_coffee_service','cafe service')
box('Espresso_body',(0,.08,.23),(.68,.40,.46),steel,.025);box('Espresso_drip_tray',(0,-.17,.05),(.66,.27,.06),metal,.009)
for x in[-.18,.18]:pole((x,-.15,.28),.045,.04,steel);tube('Portafilter_handle',[(x,-.12,.30),(x,-.33,.30)],.018,metal)
tube('Steam_wand',[(.30,-.08,.34),(.36,-.16,.28),(.36,-.17,.13)],.009,steel);done('sku_espresso_machine','barista machine with portafilters and steam wand')
category='arcade'
for variant in ['crane','rhythm','capsule','photobooth']:
 if variant=='crane':
  box('Crane_plinth',(0,0,.40),(1.0,.85,.80),cream,.025)
  for x in[-.47,.47]:pole((x,.35,.8),.024,1.15,brass)
  box('Prize_back',(0,.40,1.25),(.96,.04,.90),pink,.01);box('Crane_glass',(0,-.40,1.28),(.96,.012,.92),glass,.004);box('Control_deck',(0,-.48,.83),(1.0,.22,.12),navy,.02);tube('Claw_cable',[(0,0,1.9),(0,0,1.5)],.008,metal)
  for i in range(5):ell('Original_plush_prize',(-.32+i*.16,.10,.91),(.07,.065,.10),fabrics[i])
 elif variant=='rhythm':box('Rhythm_base',(0,0,.50),(1.30,.75,1.0),navy,.025);box('Rhythm_screen',(0,.20,1.55),(1.18,.08,.75),screen,.02);label(0,.15,1.55,1.1,.64,31);box('Key_deck',(0,-.31,1.0),(1.25,.4,.09),metal,.015)
 elif variant=='capsule':
  box('Capsule_base',(0,0,.45),(.65,.55,.90),cream,.018);ell('Capsule_dome',(0,0,1.12),(.30,.25,.32),glass)
  for j in range(10):a=j*2.4;ell('Prize_capsule',(.17*math.cos(a),.14*math.sin(a),1.00+(j%3)*.09),(.045,.045,.045),fabrics[j%5])
 else:
  for x in[-1.1,1.1]:box('Photo_booth_side',(x,0,1.15),(.08,1.65,2.3),pink,.02)
  box('Photo_booth_back',(0,.78,1.15),(2.2,.08,2.3),cream,.02);box('Camera_console',(0,.66,1.3),(.8,.18,.7),metal,.025);pole((0,.52,1.45),.045,.04,steel);label(0,-.85,2.10,2.15,.32,31)
  for j in range(6):tube('Entry_curtain',[(.45+j*.10,-.78,.15),(.45+j*.10,-.81,1.1),(.45+j*.10,-.78,2.0)],.06,fabrics[1])
 done('fixture_'+variant,'arcade '+variant+'; photo function not implemented')
(P/'licenses/v21/original-retail-assets.md').write_text('# v21 original retail kit\nOriginal fixture, product and packaging geometry/art authored in Blender/Python for FIND YOURSELF. No real store brands or game assets copied. Existing CC0 oak/walnut texture provenance and Noto OFL are retained in the project licenses. Character assets are unchanged and retain their separate licenses. These models are a procedural production kit; AAA quality is not asserted.\n')
print('V21_MODELS',len(BOUNDS))
