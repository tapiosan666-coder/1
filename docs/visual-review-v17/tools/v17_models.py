"""Original specialist joinery and campaign products, not store-neutral scatter.
Metric ground origins. CG campaign photography is production artwork, never game evidence.
"""
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];src=(P/'authoring/retail_models_v10.py').read_text().split('def book(')[0];exec(src)
OUT=P/'assets/v17/models';OUT.mkdir(exist_ok=True);PH=P/'assets/v17/photos';PH.mkdir(exist_ok=True)
cream=material('V17_lacquer_chalk',(.69,.66,.58),.39);sage=material('V17_sage_enamel',(.12,.24,.19),.47,.18);terra=material('V17_terracotta',(.42,.19,.10),.72);clay=material('V17_ceramic_clay',(.58,.36,.21),.28);indigo=material('V17_indigo',(.028,.064,.11),.65);linen=material('V17_woven_linen',(.61,.55,.43),.91);leafm=[material('V17_botanical_'+str(i),c,.76)for i,c in enumerate([(.035,.12,.035),(.07,.19,.055),(.12,.25,.075)])]
def sphere(name,loc,scale,mat):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(mat)
 for f in o.data.polygons:f.use_smooth=True
 return o
def pole(p,r,h,mat):return lathe('Fabricated_support',[(0,0),(r,0),(r,h),(0,h)],mat,p,20)
def rail(a,b,r=.018,mat=metal):return tube('Connected_support',[a,b],r,mat)
def photograph(name):
 originals=set(bpy.context.scene.objects);scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=False;scene.render.resolution_x=640;scene.render.resolution_y=896;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='JPEG';scene.render.image_settings.quality=94
 coords=[o.matrix_world@Vector(v)for o in originals if o.type in['MESH','CURVE']for v in o.bound_box];lo=Vector([min(v[i]for v in coords)for i in range(3)]);hi=Vector([max(v[i]for v in coords)for i in range(3)]);c=(lo+hi)/2;size=max((hi-lo).x,(hi-lo).y,(hi-lo).z)
 box('Photo_cyclorama',(0,0,-.04),(200,200,.06),material('Photo_bg_'+name,(.48,.43,.35),.95),0)
 bpy.ops.object.camera_add(location=c+Vector((size*.95,-size*1.7,size*.70)));cam=bpy.context.object;cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=62;scene.camera=cam
 for loc,power,spread in[((-3,-4,5),900,4),((3,-1,3),600,3),((0,4,4),1100,3)]:
  bpy.ops.object.light_add(type='AREA',location=c+Vector(loc)*size);l=bpy.context.object;l.data.energy=power*size*size;l.data.shape='DISK';l.data.size=spread*size;l.rotation_euler=(c-l.location).to_track_quat('-Z','Y').to_euler()

 if scene.world is None:scene.world=bpy.data.worlds.new('V17_Studio_world')
 scene.world.color=(.06,.06,.06);scene.render.filepath=str(PH/(name+'.jpg'));bpy.ops.render.render(write_still=True)
 for o in list(set(bpy.context.scene.objects)-originals):bpy.data.objects.remove(o,do_unlink=True)
 scene.camera=None
finish_base=finish
def done(name,photo=False):
 bpy.context.view_layer.update()
 if photo:photograph(name)
 finish_base(name)
# Original campaign products; also used on actual shop displays.
# Tailored leather bag: rounded body, real folded gussets, straps and hardware.
box('Soft_leather_body',(0,0,.25),(.48,.19,.38),fabrics[1],.055);box('Structured_base',(0,0,.065),(.44,.17,.055),walnut,.018)
for y in[-.10,.10]:
 tube('Stitched_handle',[(-.15,y,.42),(-.13,y,.62),(.13,y,.62),(.15,y,.42)],.012,walnut)
 for x in[-.15,.15]:box('Brass_handle_loop',(x,y,.43),(.035,.025,.055),brass,.007)
for x in[-.20,.20]:tube('Side_piping',[(x,-.10,.09),(x,-.105,.41)],.004,walnut)
box('Original_bag_badge',(0,-.104,.28),(.12,.008,.038),brass,.005);done('campaign_bag',True)
# Skincare vessel / dropper, no copied brand labels.
lathe('Amber_glass_bottle',[(0,0),(.055,0),(.065,.018),(.065,.18),(.035,.21),(.023,.22),(.023,.24),(0,.24)],clay,steps=40)
lathe('Threaded_metal_dropper',[(0,0),(.027,0),(.027,.04),(.020,.04),(.018,.092),(0,.10)],metal,(0,0,.235),32);box('Cream_product_label',(0,-.064,.115),(.080,.003,.09),cream,.003)
done('campaign_serum',True)
# Headphones: joined yokes, cushions and padded headband.
tube('Headphone_spring',[(-.16,0,.15),(-.19,0,.34),(-.12,0,.47),(.12,0,.47),(.19,0,.34),(.16,0,.15)],.017,metal)
tube('Padded_headband',[(-.15,0,.37),(-.08,0,.47),(.08,0,.47),(.15,0,.37)],.028,linen)
for sg in[-1,1]:
 sphere('Ear_shell',(sg*.17,0,.16),(.048,.075,.10),metal);sphere('Ear_cushion',(sg*.135,0,.16),(.025,.068,.085),rubber);rail((sg*.18,0,.29),(sg*.18,0,.19),.012,brass)
done('campaign_headphones',True)
# Editorial books are full bound objects, not bottles on a shelf.
for j in range(4):
 o=box('Paper_bookblock',(0,0,.035+j*.055),(.40-j*.025,.29,.048),paper,.004);box('Book_cover',(0,0,.009+j*.055),(.42-j*.025,.31,.004),bookmats[j],.001);box('Book_cover',(0,0,.061+j*.055),(.42-j*.025,.31,.004),bookmats[j],.001);box('Printed_spine',(0,-.154,.035+j*.055),(.42-j*.025,.008,.048),bookmats[j],.002)
box('Faceout_editorial',(0,.02,.48),(.34,.03,.46),bookmats[4],.01);box('Foil_editorial_rule',(0,-.0001,.52),(.21,.003,.008),brass,.001);done('campaign_books',True)
# Ceramic tea service / cafe plate.
lathe('Hand_thrown_cup',[(0,0),(.06,0),(.08,.025),(.083,.11),(.075,.13),(.063,.125),(.061,.026),(0,.026)],cream,steps=40)
tube('Ceramic_handle',[(.076,0,.105),(.13,0,.11),(.14,0,.045),(.078,0,.04)],.012,cream)
lathe('Tea_saucer',[(0,0),(.12,0),(.13,.018),(.10,.028),(0,.018)],clay,(0,0,-.005),40)
sphere('Laminated_pastry',(.24,0,.045),(.13,.075,.055),pastry)
for i in range(5):tube('Pastry_scoring',[(.15+i*.04,-.055,.06),(.15+i*.04,0,.099),(.15+i*.04,.055,.06)],.004,cream)
done('campaign_cafe',True)
# Glazed amphora: uneven hand-thrown profile, open lip, curved handles.
lathe('Glazed_craft_vase',[(0,0),(.12,0),(.15,.05),(.19,.23),(.16,.37),(.085,.46),(.09,.52),(.065,.52),(.06,.46),(.13,.36),(.15,.23),(.11,.05),(0,.04)],clay,steps=48)
for sg in[-1,1]:tube('Vase_loop',[(sg*.10,0,.44),(sg*.23,0,.40),(sg*.24,0,.24),(sg*.18,0,.20)],.022,clay)
done('campaign_ceramic',True)
# Connected outdoor cafe chairs fix the floating-back defect, same metric occupancy.
lathe('Table_pedestal',[(0,0),(.32,0),(.32,.06),(.06,.10),(.06,.73),(.53,.73),(.53,.78),(0,.78)],sage)
for a in[0,math.pi/2,math.pi,math.pi*1.5]:
 x,y=1.04*math.cos(a),1.04*math.sin(a)
 for dx in[-.17,.17]:
  for dy in[-.17,.17]:rail((x+dx,y+dy,.03),(x+dx,y+dy,.46),.017)
 lathe('Chair_seat',[(0,0),(.25,0),(.25,.045),(0,.045)],wood,(x,y,.46),24)
 for aa in[a-.95,a+.95]:rail((x+.23*math.cos(aa),y+.23*math.sin(aa),.46),(x+.25*math.cos(aa),y+.25*math.sin(aa),.90),.020,sage)
 tube('Chair_back',[(x+.25*math.cos(aa),y+.25*math.sin(aa),.90)for aa in np.linspace(a-math.pi*.45,a+math.pi*.45,12)],.03,sage)
for i in range(2):lathe('Cup',[(0,0),(.045,0),(.055,.09),(.045,.095),(.04,.02),(0,.02)],white,(-.18+i*.32,0,.79),20)
done('outdoor_table_connected')
# Thick upholstered lounge, exposed frame and planting bay are a coherent rest facility.
for x in[-1.55,1.55]:box('Seat_frame',(x,0,.23),(.09,1.24,.46),metal,.018)
box('Suspended_seat_frame',(0,0,.38),(3.6,1.24,.09),metal,.025)
for i in range(3):box('Deep_seat_cushion',(-1.15+i*1.15,0,.53),(1.11,1.1,.25),linen,.095);o=box('Back_cushion',(-1.15+i*1.15,.45,.94),(1.11,.25,.76),linen,.08);o.rotation_euler.x=-.12
for x in[-1.77,1.77]:box('Solid_arm',(x,0,.68),(.16,1.2,.58),wood,.04)
done('lounge_sofa')
# Window and wall merchandising: purpose-built backlit niches / display fixtures.
box('Window_plinth',(0,0,.12),(2.5,1.05,.24),stone,.025)
for x in[-1.18,1.18]:box('Showcase_jamb',(x,.43,1.30),(.10,.12,2.5),walnut,.014)
box('Showcase_crown',(0,.43,2.53),(2.46,.12,.10),walnut,.014)
for z in[.80,1.60]:box('Floating_display_shelf',(0,.30,z),(2.34,.32,.045),wood,.008)
box('Niche_back',(0,.49,1.37),(2.25,.025,2.28),cream,.01)
done('lit_display_niche')
# Apparel capsule: hanging rail, carefully shaped cloth and shelf for folded pieces.
for x in[-1.12,1.12]:pole((x,.15,0),.025,1.82,brass);box('Rack_foot',(x,.15,.025),(.26,.65,.05),metal,.012)
rail((-1.12,.15,1.80),(1.12,.15,1.80),.022,brass)
for j in range(7):
 x=-.84+j*.28;tube('Clothes_hanger',[(x-.16,.15,1.54),(x,.15,1.67),(x+.16,.15,1.54),(x-.16,.15,1.54)],.006,wood)
 verts=[(x-.19,-.02,1.53),(x+.19,-.02,1.53),(x+.26,-.04,.70),(x-.26,-.04,.70),(x-.19,.20,1.53),(x+.19,.20,1.53),(x+.26,.18,.70),(x-.26,.18,.70)]
 mesh('Tailored_long_garment',verts,[(0,1,2,3),(4,7,6,5),(0,3,7,4),(1,5,6,2),(3,2,6,7)],fabrics[j%5]);tube('Visible_tailoring_seam',[(x,-.024,1.51),(x,-.044,.72)],.0025,bookmats[0])
box('Garment_low_shelf',(0,.15,.14),(2.15,.50,.05),wood,.01);done('apparel_capsule')
# Beauty consultation island and dedicated counter lighting.
box('Sculpted_beauty_island',(0,0,.49),(2.8,.96,.98),cream,.09);box('Stone_countertop',(0,0,1.01),(2.92,1.03,.065),stone,.035)
for x in[-.94,0,.94]:
 box('Brand_tester_tray',(x,-.15,1.055),(.78,.55,.025),brass,.012)
 for j in range(4):lathe('Serum_tester',[(0,0),(.036,0),(.036,.13),(.018,.15),(0,.15)],clay,(x-.24+j*.16,-.18,1.07),20)
 pole((x,.30,1.04),.015,.24,brass);box('Illuminated_mirror',(x,.31,1.57),(.58,.035,.56),metal,.08);box('Mirror_surface',(x,.284,1.57),(.51,.008,.49),steel,.07)
done('beauty_consultation_island')
# Book editorial wall: face-out ledges above fully stocked bound spines.
for x in[-1.48,1.48]:box('Book_wall_gable',(x,0,1.18),(.055,.44,2.36),wood,.009)
box('Book_wall_back',(0,.19,1.18),(2.95,.035,2.34),walnut,.005)
for zz in[.15,.58,1.01,1.44,1.88,2.30]:box('Book_ledge',(0,0,zz),(2.95,.43,.045),wood,.007)
for row,z in enumerate([.18,.61,1.04,1.47]):
 x=-1.38
 for j in range(31):
  w=.065+.012*(j%4);h=.24+.025*((j+row)%5);box('Bound_bookblock',(x,0,z+h/2),(w,.22,h),paper,.001);box('Printed_book_spine',(x,-.116,z+h/2),(w+.002,.012,h+.012),bookmats[(j+row)%6],.002);x+=w+.008
for j in range(5):box('Faceout_cover',(-1.12+j*.56,-.11,2.10),(.40,.045,.37),bookmats[j],.008)
done('book_editorial_wall')
# Hands-on electronics fixtures: supported screens, keyboard detail and security tethers.
box('Demo_table_base',(0,0,.45),(2.7,.77,.90),walnut,.025);box('Demo_table_top',(0,0,.94),(2.85,.91,.08),stone,.025)
for i in range(3):
 x=-.88+i*.88;box('Laptop_base',(x,-.09,1.01),(.56,.39,.025),metal,.018);o=box('Laptop_screen',(x,.07,1.22),(.56,.022,.37),metal,.018);o.rotation_euler.x=-.16;box('Display_content',(x,.048,1.22),(.50,.006,.30),indigo,.008)
 for a in range(5):
  for b in range(11):box('Keycap',(x-.22+b*.044,-.20+a*.052,1.025),(.032,.037,.008),cream,.003)
 tube('Security_tether',[(x,.30,.99),(x+.2,.37,.97),(x+.26,.28,.98)],.004,metal)
done('electronics_demo_bar')
# Bakery / deli case: opaque rear preparation, hygiene glass and trays.
box('Bakery_carcass',(0,0,.47),(3.4,.90,.94),wood,.035);box('Food_safe_top',(0,0,.97),(3.5,.99,.05),stone,.018)
for x in[-1.65,1.65]:box('Case_end',(x,0,1.36),(.055,.97,.80),brass,.009)
box('Hygiene_glass',(0,-.44,1.38),(3.3,.012,.70),glass,.004);box('Case_top',(0,0,1.77),(3.45,.96,.05),brass,.01)
for row,z in enumerate([1.04,1.39]):
 box('Food_tray_shelf',(0,0,z),(3.26,.82,.035),wood,.008)
 for j in range(8):
  x=-1.42+j*.40;sphere('Baked_roll',(x,-.10,z+.10),(.15,.11,.09),pastry)
  for s in[-1,0,1]:tube('Bread_score',[(x-.08+s*.04,-.14,z+.15),(x-.06+s*.04,-.06,z+.18)],.003,cream)
done('bakery_display')
# Cafe preparation backbar; dispenser, espresso equipment and crockery, clear customer side.
box('Cafe_backbar',(0,0,.47),(3.6,.68,.94),walnut,.03);box('Cafe_worktop',(0,0,.97),(3.7,.76,.05),stone,.018)
box('Espresso_machine',( -.65,0,1.25),(1.05,.48,.51),steel,.06)
for x in[-.95,-.65,-.35]:pole((x,-.28,1.09),.012,.12,metal);tube('Coffee_group_handle',[(x,-.28,1.09),(x,-.43,1.09)],.015,metal)
for x in[.45,.88,1.31]:lathe('Canister',[(0,0),(.14,0),(.14,.34),(.13,.37),(0,.37)],glass,(x,0,1.01),28);lathe('Canister_lid',[(0,0),(.15,0),(.15,.035),(0,.035)],wood,(x,0,1.38),28)
for j in range(12):lathe('Stacked_cups',[(0,0),(.045,0),(.055,.075),(0,.075)],white,(-1.5+(j%3)*.13,-.08,1.01+(j//3)*.07),20)
done('cafe_backbar')
# Curved cut-metal sculptural landmark, anchored to an accessible dry plinth.
lathe('Sculpture_plinth',[(0,0),(.95,0),(1.02,.06),(1.02,.18),(0,.18)],stone,steps=48)
for j in range(3):tube('Sculpture_loop',[(.65*math.sin(t+j*.7),.40*math.cos(t+j*.7),.35+1.65*(math.sin(t*.5)**2))for t in np.linspace(0,math.tau,44)],.055,[brass,metal,sage][j])
done('plaza_loop_sculpture')
# Soft awning / event banner holder. Fabric is tensioned with visible hems.
for x in[-1.5,1.5]:pole((x,0,0),.025,2.7,metal);box('Banner_base',(x,0,.025),(.42,.42,.05),metal,.015)
rail((-1.5,0,2.68),(1.5,0,2.68),.025)
box('Tensioned_banner',(0,0,2.02),(2.82,.012,1.15),cream,.004);done('event_banner_frame')
# Food-truck trading vignette: supported menu easel, trays and ordering counter.
for x in[-.42,.42]:
 for y in[-.25,.25]:rail((x,y,0),(x*.8,y*.8,1.15),.02,sage)
box('Menu_frame',(0,0,.96),(.85,.05,.83),wood,.025);box('Menu_board',(0,-.032,.96),(.74,.008,.72),indigo,.008);done('menu_easel')
box('Bakery_side_counter',(0,0,.45),(1.5,.66,.90),wood,.035);box('Vendor_top',(0,0,.93),(1.6,.73,.06),steel,.018)
for i in range(3):box('Bread_pickup_tray',(-.45+i*.45,0,1.0),(.40,.50,.045),brass,.01)
box('Compact_POS',(.49,.20,1.15),(.25,.12,.29),metal,.018);done('food_order_counter')
# Planting masses use individually curved leaves and a connected branching shrub.
for variant in range(3):
 for j in range(18):
  a=j*2.39996;rad=.15+.03*(j%5);h=.55+.08*(j%7);tip=(rad*math.cos(a),rad*math.sin(a),h);tube('Shrub_branch',[(0,0,0),(.06*math.cos(a),.06*math.sin(a),h*.5),tip],.008,walnut)
  for k in range(8):
   aa=a+k*.8;cx=tip[0]+.14*math.cos(aa);cy=tip[1]+.14*math.sin(aa);cz=tip[2]-.10+k*.018;v=[(cx,cy,cz),(cx+.10*math.cos(aa+.7),cy+.10*math.sin(aa+.7),cz+.02),(cx+.25*math.cos(aa),cy+.25*math.sin(aa),cz+.03),(cx+.10*math.cos(aa-.7),cy+.10*math.sin(aa-.7),cz+.02)];mesh('Curved_broadleaf',v,[(0,1,2),(0,2,3)],leafm[(j+k+variant)%3])
 done('botanical_shrub_'+str(variant))
print('V17_MODELS_DONE',flush=True)
