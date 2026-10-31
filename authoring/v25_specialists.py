from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from v25_blender_common import *
from PIL import Image,ImageDraw,ImageFont
B=json.loads((P/'source/v25/model-bounds.json').read_text());C=json.loads((P/'source/v25/product-catalog.json').read_text());A=P/'assets/v25/art';font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';bold='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc';sage=material('V25_cafe_sage',(.10,.19,.14),.6);cream=material('V25_satin_ivory',(.78,.75,.67),.52);rose=material('V25_soft_rose',(.39,.21,.18),.57);navy=material('V25_arcade_navy',(.018,.035,.065),.5);fabric=material('V25_woven_twill',(.32,.39,.31),.92)
def lightmat(name,col,power=1.5):
 m=material(name,col,.32);s=m.node_tree.nodes.get('Principled BSDF');s.inputs['Emission Color'].default_value=(*col,1);s.inputs['Emission Strength'].default_value=power;return m
warm=lightmat('V25_opal_light',(.92,.80,.59),1.3);pink=lightmat('V25_neon_pink',(.68,.05,.23),2.);cyan=lightmat('V25_neon_cyan',(.03,.40,.65),2.)
def artwork(name,title,subtitle,bg='#203a35',fg='#f4ecd9',size=(1024,512)):
 im=Image.new('RGB',size,bg);d=ImageDraw.Draw(im);n=min(90,int(size[0]*.9/max(1,len(title))*1.5));d.text((size[0]/2,size[1]*.34),title,font=ImageFont.truetype(bold,n),fill=fg,anchor='mm');d.line((40,size[1]*.56,size[0]-40,size[1]*.56),fill=fg,width=2);d.text((size[0]/2,size[1]*.75),subtitle,font=ImageFont.truetype(font,28),fill=fg,anchor='mm');file=A/(name+'.png');im.save(file);return material(name,(1,1,1),.7,texture='assets/v25/art/'+file.name)
def plane(name,centre,w,h,mat):
 x,y,z=centre;mesh(name,[(x-w/2,y,z-h/2),(x+w/2,y,z-h/2),(x+w/2,y,z+h/2),(x-w/2,y,z+h/2)],[(0,1,2,3)],mat,[(0,0),(1,0),(1,1),(0,1)])
def emit(name,cat):
 bpy.context.view_layer.update();pts=[o.matrix_world@Vector(c)for o in bpy.context.scene.objects if o.type in['MESH','CURVE']for c in o.bound_box];lo=[min(q[i]for q in pts)for i in range(3)];hi=[max(q[i]for q in pts)for i in range(3)];B[name]={'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]]};C[name]={'category':cat,'source':'Original v25 dedicated Blender retail design and fictional artwork; inherited CC0 wood and OFL type'};finish(name)
booklogo=artwork('orienne-logo','ORIENNE BOOKS','本と、暮らしのつづき。')
# Bookshop wall cabinetry: six proper supported levels, joinery, cornice and lighting.
box('Back',(0,.41,1.65),(1.98,.06,3.26),wood,.008)
for x in[-.97,.97]:box('Stile',(x,0,1.65),(.055,.88,3.26),wood,.008)
for z in[.33,.79,1.25,1.71,2.17,2.63]:box('Library_shelf',(0,0,z),(1.93,.87,.035),wood,.008)
box('Cornice',(0,0,3.18),(1.98,.88,.12),wood,.012);box('Reading_strip',(0,-.40,3.10),(1.80,.018,.018),warm,.003);plane('Brand',(0,-.446,2.98),1.72,.24,booklogo);emit('fixture_v25_library_wall','book_wall_fixture')
# Double-face central book gondola, lower sightline, endcaps with genre signage.
box('Recessed_plinth',(0,0,.06),(1.86,1.40,.12),sage,.018);box('Centre_spine',(0,0,.98),(1.86,.06,1.90),wood,.008)
for side in[-1,1]:
 for z in[.33,.79,1.25,1.71]:box('Double_shelf',(0,side*.35,z),(1.82,.68,.035),wood,.007)
for x in[-.91,.91]:box('End_cheek',(x,0,.98),(.05,1.41,1.90),wood,.014)
box('Top_cap',(0,0,1.93),(1.88,1.43,.06),sage,.016);emit('fixture_v25_genre_gondola','book_genre_fixture')
# Magazine bays use inclined display ledges rather than a generic wall shelf.
box('Magazine_back',(0,.30,1.1),(1.8,.055,2.15),sage,.015)
for z in[.43,.93,1.43]:
 shelf=box('Raked_ledge',(0,.0,z),(1.74,.59,.035),wood,.01);shelf.rotation_euler.x=math.radians(14);box('Front_lip',(0,-.29,z+.03),(1.74,.035,.08),brass,.006)
box('Magazine_header',(0,.18,2.04),(1.79,.30,.23),wood,.01);plane('Magazine_sign',(0,.023,2.04),1.62,.20,artwork('magazine-sign','MAGAZINES','雑誌・写真集'));emit('fixture_v25_magazine','magazine_fixture')
# Book discovery terminal with a recessed touch screen and actual pedestal.
box('Terminal_foot',(0,0,.035),(.61,.51,.07),metal,.02);box('Terminal_column',(0,.06,.65),(.12,.12,1.24),wood,.02);panel=box('Angled_touchscreen',(0,0,1.32),(.56,.08,.42),metal,.025);panel.rotation_euler.x=math.radians(20);plane('Search_screen',(0,-.071,1.34),.49,.30,artwork('book-search','本をさがす','ジャンル / 新刊 / おすすめ',bg='#dbe5d7',fg='#243c36'));emit('fixture_v25_book_terminal','book_search_terminal')
# Sculpted reading chair with continuous curved back, thick seat and tapered legs.
def chair(x=0,y=0,rotation=0):
 before=set(bpy.data.objects);box('Upholstered_seat',(0,0,.46),(.68,.65,.14),fabric,.055)
 points=[(-.36,.15,.53),(-.34,.29,.87),(0,.34,.94),(.34,.29,.87),(.36,.15,.53)];tube('Curved_upholstered_back',points,.09,fabric)
 for side in[-1,1]:tube('Armrest',[(side*.34,-.25,.54),(side*.36,-.11,.64),(side*.34,.21,.70)],.045,wood)
 for a in[-1,1]:
  for b in[-1,1]:tube('Tapered_leg',[(a*.27,b*.24,.03),(a*.23,b*.20,.41)],.022,wood)
 for o in set(bpy.data.objects)-before:o.rotation_euler.z=rotation;o.location=Vector((x,y,0))+Matrix.Rotation(rotation,4,'Z')@o.location
chair();emit('fixture_v25_reading_chair','reading_seat')
# Café lounge group: a pair of curved chairs and a low stone table, not repeated dining chairs.
chair(-.68,.0,-.20);chair(.68,.0,.20);lathe('Stone_coffee_table',[(.35,.29),(.40,.32),(.40,.37),(.35,.40)],stone,(0,-.75,0),48);lathe('Pedestal',[(.24,0),(.17,.05),(.11,.29)],brass,(0,-.75,0),40);emit('fixture_v25_cafe_lounge','lounge_seating')
# Window counter with three stools, foot rail and solid wooden top.
box('Window_counter',(0,0,1.03),(2.80,.48,.07),wood,.025)
for x in[-1.22,1.22]:tube('Bar_leg',[(x,0,.02),(x,0,.99)],.025,brass)
tube('Footrail',[(-1.28,-.34,.23),(1.28,-.34,.23)],.017,brass)
for x in[-.90,0,.90]:
 lathe('Stool_seat',[(.22,.68),(.25,.70),(.25,.76),(.21,.79)],fabric,(x,-.73,0),40)
 for a in[-1,1]:
  for b in[-1,1]:tube('Stool_leg',[(x+a*.18,-.73+b*.18,.02),(x+a*.14,-.73+b*.14,.68)],.015,metal)
emit('fixture_v25_window_bar','counter_seating')
# Tray return and separated bins, an operational service zone.
box('Return_cabinet',(0,0,.48),(1.40,.65,.94),sage,.025);box('Stone_return_top',(0,0,.97),(1.46,.69,.045),stone,.012)
for x in[-.38,.38]:
 lathe('Bin_liner',[(.18,.30),(.18,.84),(.19,.88)],metal,(x,0,0),32)
 box('Open_bin_mouth',(x,-.331,.73),(.43,.012,.20),metal,.035)
for z in[1.015,1.04,1.065]:box('Tray_stack',(-.38,0,z),(.50,.34,.018),wood,.018)
plane('Return_sign',(0,-.334,.45),1.15,.18,artwork('tray-return','TRAY RETURN','返却口 / 分別にご協力ください'));emit('fixture_v25_tray_return','cafe_service')
# Pendant cluster with blown-glass profiles and curved brass rods.
for x,y,z in[(-.78,-.38,-.12),(.60,.25,-.28),(-.12,.52,-.52)]:
 lathe('Opal_glass_shade',[(.05,.12),(.25,.05),(.33,-.07),(.30,-.24),(.08,-.35)],warm,(x,y,z),48);tube('Curved_brass_stem',[(x,y,z+.12),(x,y,.35)],.008,brass)
box('Pendant_ceiling_plate',(0,0,.37),(2.10,1.30,.05),metal,.015);emit('finish_v25_cafe_pendants','cafe_ceiling')
# Beauty-specific illuminated display, preserving the old shelf levels for retained merchandise.
beautylogo=artwork('veloria-logo','VELORIA COLLECTIVE','BOTANICAL BEAUTY / 肌と、向き合う。',bg='#d8dcd0',fg='#29483c')
box('Beauty_back',(0,.405,1.30),(1.96,.055,2.55),cream,.018)
for z in[.33,.79,1.25,1.71]:box('Glass_front_shelf',(0,0,z),(1.94,.86,.035),cream,.012)
for x in[-.95,.95]:
 box('Gold_stile',(x,0,1.30),(.035,.84,2.55),brass,.006);box('Vertical_diffuser',(x,-.423,1.32),(.018,.014,2.20),warm,.004)
box('Illuminated_header',(0,0,2.36),(1.96,.84,.30),cream,.02);plane('Beauty_logo',(0,-.426,2.36),1.78,.25,beautylogo);emit('fixture_v25_beauty_wall','beauty_wall')
# Dedicated test island has mirror, organised trays and hidden storage; retained support elevations.
box('Test_island_base',(0,0,.34),(1.84,.82,.68),sage,.025)
for z in[.33,.79,.93,1.25,1.71]:box('Tester_deck',(0,0,z),(1.96,.87,.035),cream,.016)
for x in[-.94,.94]:tube('Champagne_rail',[(x,.30,.02),(x,.30,1.94)],.016,brass)
box('Mirror_frame',(0,.34,1.53),(.60,.05,.78),brass,.025);mirror=material('V25_mirror_polished',(.82,.85,.83),.035,1.);box('Polished_mirror',(0,.309,1.53),(.54,.012,.71),mirror,.02);emit('fixture_v25_beauty_tester','beauty_tester')
# Curved scent showcase, not a generic shelf.
lathe('Scent_pedestal',[(0,0),(.44,0),(.46,.06),(.30,.73),(.45,.82),(.45,.88),(0,.88)],cream,steps=56)
for x in[-.30,.30]:tube('Scent_frame',[(x,.10,.89),(x,.10,1.65)],.01,brass)
box('Scent_light',(0,.10,1.66),(.68,.10,.04),warm,.012);emit('fixture_v25_scent_podium','perfume_display')
# Open compact and faceted fragrance are dedicated merchandise shapes.
case=lathe('Compact_body',[(.055,0),(.066,.012),(.065,.03),(.053,.038)],brass,steps=48);lathe('Pressed_powder',[(.050,.038),(.050,.044)],material('V25_powder',(.62,.40,.28),.92),steps=40)
box('Compact_hinge',(0,.063,.034),(.030,.020,.020),brass,.005);lid=lathe('Open_compact_lid',[(.055,0),(.065,.008),(.065,.017),(.052,.022)],brass,steps=48);lid.rotation_euler.x=math.radians(73);lid.location=(0,.063,.038);emit('sku_v25_compact','beauty_cosmetics')
lathe('Faceted_fragrance_glass',[(.043,0),(.057,.02),(.054,.12),(.035,.145)],glass,steps=12);lathe('Liquid',[(.040,.013),(.047,.025),(.045,.105)],material('V25_amber_perfume',(.56,.30,.10),.17),steps=12);lathe('Gold_neck',[(.022,.14),(.023,.165)],brass,steps=32);box('Cut_cap',(0,0,.185),(.065,.043,.04),metal,.012);emit('sku_v25_fragrance','beauty_perfume')
# Elliptical beauty ceiling light, slender construction rather than an apparel raft.
for scale,z in[(1.,0),(.60,-.22)]:
 pts=[(math.cos(i*math.tau/48)*1.40*scale,math.sin(i*math.tau/48)*.90*scale,z)for i in range(49)];tube('Gold_oval',pts,.025,brass);tube('Oval_diffuser',[(x,y,zz-.03)for x,y,zz in pts],.018,warm)
emit('finish_v25_beauty_oval','beauty_ceiling')
# Original arcade screen artwork; no borrowed game screenshots or logos.
def screen_art(name,kind):
 im=Image.new('RGB',(512,512),'#081323');d=ImageDraw.Draw(im)
 if kind=='race':
  d.polygon([(35,512),(220,190),(292,190),(477,512)],fill='#334452');d.polygon([(250,220),(258,220),(281,512),(230,512)],fill='#e8c35d');d.ellipse((335,40,420,125),fill='#fa8467');d.text((40,32),'VELOCITY / 01',font=ImageFont.truetype(bold,28),fill='#66c9db')
 else:
  for k in range(5):d.line((58+k*95,70,58+k*95,445),fill='#235b70',width=5)
  for k in range(14):x=58+(k*3%5)*95;y=90+k*22;d.rounded_rectangle((x-18,y-7,x+18,y+7),radius=6,fill='#ed74ad'if k%2 else'#83e3de')
  d.text((30,18),'PULSE / ORIGINAL MIX',font=ImageFont.truetype(bold,26),fill='#f0e3c5')
 f=A/(name+'.png');im.save(f);m=material(name,(1,1,1),.25,texture='assets/v25/art/'+f.name);node=m.node_tree.nodes.get('Principled BSDF');tex=next(n for n in m.node_tree.nodes if n.type=='TEX_IMAGE');m.node_tree.links.new(tex.outputs['Color'],node.inputs['Emission Color']);node.inputs['Emission Strength'].default_value=.8;return m
race=screen_art('original-racing-screen','race');music=screen_art('original-music-screen','music');arcadelogo=artwork('terrune-logo','TERRUNE PLAY','MUSIC / RACING / PRIZE / PHOTO',bg='#122438',fg='#e9c3df')
# Music cabinet: sculpted side profiles, tilted screen, illuminated controls and speakers.
verts=[(-.60,-.35,0),(.60,-.35,0),(.60,.30,0),(-.60,.30,0),(-.58,-.14,1.78),(.58,-.14,1.78),(.58,.27,1.78),(-.58,.27,1.78)];mesh('Tapered_music_shell',verts,[(0,1,2,3),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0),(4,7,6,5)],navy)
plane('Music_game_screen',(0,-.255,1.34),.96,.72,music);box('Control_shelf',(0,-.20,.91),(1.23,.68,.08),metal,.025)
for x in[-.43,-.21,0,.21,.43]:lathe('Lit_game_button',[(.055,0),(.055,.018)],pink if x<0 else cyan,(x,-.36,.96),24)
for x in[-.55,.55]:tube('Lit_music_cheek',[(x,-.37,.05),(x,-.37,.87),(x,-.15,1.85)],.015,cyan)
emit('fixture_v25_music_cabinet','arcade_music')
# Racing cockpit: separate seat, steering wheel, pedals, screen and sculpted fairing.
box('Cockpit_floor',(0,0,.07),(1.05,1.85,.14),navy,.045);box('Display_pillar',(0,.62,.91),(.89,.37,1.60),navy,.08);plane('Racing_screen',(0,.419,1.35),.84,.65,race)
box('Bucket_seat',(0,-.47,.48),(.63,.58,.16),fabric,.06);back=box('Reclined_racing_back',(0,-.77,.83),(.66,.16,.78),fabric,.075);back.rotation_euler.x=-.18
pts=[(math.cos(i*math.tau/40)*.23,-.04+math.sin(i*math.tau/40)*.03,.96+math.sin(i*math.tau/40)*.23)for i in range(41)];tube('Steering_wheel',pts,.025,rubber);tube('Steering_column',[(0,.23,.73),(0,-.02,.96)],.035,metal)
for x in[-.13,.13]:ped=box('Pedal',(x,.28,.18),(.12,.23,.04),steel,.008);ped.rotation_euler.x=.35
for x in[-.49,.49]:tube('Cockpit_neon',[(x,-.86,.18),(x,.75,.18),(x,.76,1.65)],.012,pink)
emit('fixture_v25_racing_cockpit','arcade_racing')
# Prize crane: visible claw trolley, glass, prizes and a shaped console.
box('Crane_plinth',(0,0,.21),(.96,.80,.42),navy,.045)
for x in[-.46,.46]:
 for y in[-.38,.38]:box('Prize_frame',(x,y,1.18),(.045,.045,1.70),cream,.009)
for x in[-.445,.445]:box('Side_glass',(x,0,1.19),(.010,.74,1.38),glass,.002)
box('Rear_glass',(0,.375,1.19),(.88,.012,1.38),glass,.002);box('Front_glass',(0,-.375,1.23),(.88,.012,1.13),glass,.002);box('Prize_deck',(0,0,.54),(.88,.74,.05),cream,.015)
for i,(x,y)in enumerate([(-.24,.08),(.13,.13),(.20,-.15)]):
 lathe('Plush_prize_body',[(0,0),(.07,.01),(.10,.12),(.07,.23),(0,.26)],material('V25_prize_'+str(i),[(.57,.36,.37),(.33,.48,.45),(.65,.55,.30)][i],.9),(x,y,.57),24)
box('Claw_trolley',(0,0,1.83),(.16,.14,.06),metal,.01);tube('Claw_cable',[(0,0,1.80),(0,0,1.45)],.008,steel)
for a in[0,math.tau/3,math.tau*2/3]:tube('Claw_finger',[(0,0,1.45),(.11*math.cos(a),.11*math.sin(a),1.34),(.05*math.cos(a),.05*math.sin(a),1.26)],.008,steel)
box('Play_console',(0,-.42,.85),(.89,.26,.12),navy,.035);lathe('Joystick',[(.024,0),(.024,.09),(.04,.11)],pink,(-.20,-.46,.92),24);lathe('Play_button',[(.06,0),(.06,.025)],cyan,(.20,-.46,.93),24);box('Prize_header',(0,0,1.99),(.96,.80,.19),pink,.025);emit('fixture_v25_prize_crane','arcade_prize')
# Capsule machine with transparent globe and a handwheel/coin slot.
box('Capsule_base',(0,0,.40),(.59,.50,.80),cream,.045);lathe('Clear_capsule_globe',[(.18,.78),(.27,.89),(.29,1.09),(.22,1.29),(.08,1.35)],glass,steps=48)
for i in range(12):
 a=i*2.399;r=.12+.05*(i%2);lathe('Toy_capsule',[(0,0),(.045,.015),(.05,.04),(.035,.075),(0,.085)],pink if i%2 else cyan,(math.cos(a)*r,math.sin(a)*r,.84+(i%3)*.07),20)
box('Coin_slot',(.17,-.257,.62),(.055,.012,.012),metal,.003);tube('Turning_handle',[(-.11,-.28,.52),(.11,-.28,.52)],.025,brass);box('Prize_hatch',(0,-.259,.24),(.31,.015,.20),navy,.025);emit('fixture_v25_capsule','arcade_capsule')
# Photo booth: open front entry, side curtain, camera column, seat and light canopy.
box('Photo_back',(0,.75,1.14),(2.12,.07,2.28),sage,.02)
for x in[-1.025,1.025]:box('Photo_side',(x,.04,1.14),(.07,1.42,2.28),rose,.025)
box('Portrait_bench',(0,.49,.47),(1.76,.43,.12),cream,.04)
for x in[-.74,.74]:box('Bench_leg',(x,.49,.23),(.06,.23,.46),brass,.008)
box('Camera_column',(0,.62,1.25),(.35,.18,1.44),navy,.04);lathe('Camera_lens',[(.04,0),(.05,.025),(.04,.04)],metal,(0,.51,1.48),32)
box('Photo_ceiling',(0,.03,2.25),(2.13,1.48,.10),cream,.025);box('Portrait_light',(0,-.45,2.17),(1.72,.12,.04),warm,.015)
plane('Photo_header',(0,-.718,2.15),1.90,.22,artwork('lumi-photo','LUMI PHOTO','撮影 → 編集 → 出口',bg='#705b66'))
for k in range(10):tube('Side_curtain',[(.76+k*.025,-.63,.11),(.76+k*.025,-.63,1.96)],.020,fabric)
emit('fixture_v25_photo_booth','photo_booth')
box('Edit_counter',(0,0,.92),(1.55,.56,.10),cream,.03)
for x in[-.64,.64]:tube('Editor_leg',[(x,0,.02),(x,0,.87)],.025,brass)
for x in[-.40,.40]:
 box('Edit_screen',(x,.12,1.20),(.54,.055,.40),navy,.025);plane('Editing_UI',(x,.087,1.20),.48,.34,artwork('photo-editor','PHOTO EDIT','背景 / フレーム / スタンプ',bg='#d9c6d7',fg='#372638'))
emit('fixture_v25_photo_editor','photo_editing')
# Medal game with visible sloped table and coin banks.
box('Medal_pedestal',(0,0,.45),(1.40,.96,.90),navy,.05);box('Coin_playfield',(0,0,.94),(1.32,.89,.05),steel,.02)
for i in range(30):lathe('Display_medal',[(.022,0),(.022,.003)],brass,(-.52+(i%10)*.115,-.25+(i//10)*.22,.97),16)
box('Medal_back',(0,.45,1.28),(1.40,.06,.68),cream,.025);plane('Medal_score',(0,.415,1.31),1.18,.40,artwork('medal-score','COIN GARDEN','MEDAL / ORIGINAL PLAY',bg='#143d39'));emit('fixture_v25_medal','arcade_medal')
# Arcade-specific overhead luminous polygon, not a timber ceiling reused from apparel.
pts=[(-1.50,-.80,0),(-.85,-1.10,0),(.85,-1.10,0),(1.50,-.80,0),(1.50,.80,0),(.85,1.10,0),(-.85,1.10,0),(-1.50,.80,0),(-1.50,-.80,0)];tube('Arcade_hex_frame',pts,.035,navy);tube('Arcade_diffuser',[(x,y,z-.03)for x,y,z in pts],.018,cyan);emit('finish_v25_arcade_hex','arcade_ceiling')
(P/'source/v25/model-bounds.json').write_text(json.dumps(B,indent=2));(P/'source/v25/product-catalog.json').write_text(json.dumps(C,indent=2));print('V25_SPECIALIST_ASSETS',len(B))
