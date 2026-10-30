"""Dedicated display products and fixtures. Original geometry; inherited CC0 timber only."""
from pathlib import Path
import sys,math,json
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from v24_blender_common import *
B={};C={};gold=material('V24_brushed_gold',(.60,.43,.18),.23,.84);silver=material('V24_brushed_silver',(.65,.68,.70),.22,.91);velvet=material('V24_velvet_blue',(.026,.06,.09),.93);ceramic=material('V24_warm_ceramic',(.82,.79,.70),.36);black=material('V24_satin_black',(.023,.028,.032),.39);cream=material('V24_cream',(.88,.78,.57),.84);crust=material('V24_golden_crust',(.45,.19,.055),.62);red=material('V24_strawberry',(.48,.016,.028),.38);green=material('V24_leaf',(.12,.25,.055),.69);linen=material('V24_greige_wool',(.34,.31,.27),.87);blue=material('V24_indigo_wool',(.026,.057,.085),.88);glass=material('V24_display_glass',(.69,.83,.88),.12);glass.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value=.18;glass.surface_render_method='DITHERED'
emissive=material('V24_warm_LED',(.95,.83,.61),.4);emissive.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value=(1,.85,.63,1);emissive.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=2.8

def done(name,category,role,shelves=None):
 bpy.context.view_layer.update();pts=[o.matrix_world@Vector(c)for o in bpy.context.scene.objects if o.type in['MESH','CURVE']for c in o.bound_box];lo=[min(p[i]for p in pts)for i in range(3)];hi=[max(p[i]for p in pts)for i in range(3)];B[name]={'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]],'unit':'metres'};C[name]={'category':category,'role':role,'source':'Original Blender v24 geometry','shelf_surfaces_m':shelves or[]};finish(name)
def cylinder(name,loc,r,depth,mat,rotation=(0,0,0)):
 bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=r,depth=depth,location=loc,rotation=rotation);o=bpy.context.object;o.name=name;o.data.materials.append(mat)
 for p in o.data.polygons:p.use_smooth=True
 return o
def sphere(name,loc,scale,mat):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(mat)
 for p in o.data.polygons:p.use_smooth=True
 return o
def ring(name,loc,major,minor,mat,rot=(0,0,0)):
 bpy.ops.mesh.primitive_torus_add(major_segments=40,minor_segments=8,location=loc,rotation=rot,major_radius=major,minor_radius=minor);o=bpy.context.object;o.name=name;o.data.materials.append(mat)
 return o
# Rounded, layered jewellery displays with real links, bezels, stands and velvet.
lathe('Velvet_bust',[(.10,0),(.11,.025),(.09,.13),(.07,.22),(.048,.27),(.045,.34),(.06,.38)],velvet)
for i in range(25):
 a=math.pi+i*math.pi/24;ring('Necklace_link',(.067*math.cos(a),-.058,.255+.065*math.sin(a)),.005,.0012,gold,(math.pi/2,0,0))
box('Pendant_bezel',(0,-.066,.17),(.021,.008,.031),gold,.007);sphere('Faceted_stone',(0,-.072,.171),(.007,.004,.012),ceramic);done('sku_v24_necklace','accessories','Necklace links, pendant and velvet bust')
box('Ring_tray',(0,0,.012),(.25,.16,.024),velvet,.018)
for x,r in[(-.075,.023),(0,.027),(.075,.024)]:
 ring('Ring_band',(x,0,.047),r,.0038,silver,(math.pi/2,0,0));sphere('Gem_setting',(x,-.026,.06),(.008,.007,.009),ceramic)
done('sku_v24_ring_set','accessories','Different ring sizes and gemstone settings on padded tray')
box('Watch_cushion',(0,0,.037),(.15,.12,.074),velvet,.035);ring('Watch_strap',(0,0,.085),.052,.008,linen,(math.pi/2,0,0));box('Watch_case',(0,-.047,.091),(.046,.014,.054),silver,.009);box('Watch_face',(0,-.056,.092),(.034,.003,.042),ceramic,.006)
for end in[(-.010,-.059,.092),(.012,-.059,.104)]:tube('Watch_hand',[(0,-.059,.092),end],.001,black)
done('sku_v24_watch','accessories','Watch case, face, hands, strap and soft display cushion')
# Detailed, shelf-sized personal care packaging.
box('Blister_card',(0,0,.003),(.15,.10,.006),silver,.005)
for x in[-.05,0,.05]:
 for y in[-.025,.025]:sphere('Tablet_dome',(x,y,.012),(.013,.019,.009),ceramic)
done('sku_v24_blister','pharmacy','Individual blister pockets, sealed foil and card')
lathe('Ointment_tube',[(.018,0),(.022,.014),(.021,.045),(.018,.12),(.009,.14)],white);cylinder('Screw_cap',(0,0,.153),.012,.025,black);box('Crimped_seal',(0,0,.004),(.052,.012,.008),silver,.002);done('sku_v24_ointment','pharmacy','Crimped soft tube and screw cap')
box('Care_carton',(0,0,.065),(.065,.04,.13),white,.003);box('Colour_band',(0,-.0208,.085),(.059,.001,.025),green,.0003)
for i in range(4):box('Printed_rule',(0,-.021,.04+i*.008),(.045-i*.005,.001,.002),black,.0003)
done('sku_v24_care_box','pharmacy','Labelled care carton, colour band and information lines')
# Musical instrument silhouettes on the existing appropriate display stands.
for name,typ,mat in [('electric_bass','bass',blue),('ukulele','ukulele',wood),('acoustic_guitar','acoustic',walnut)]:
 scale=.72 if typ=='ukulele'else 1.;levels=[]
 outline=[(-.075,0),(-.14,.05),(-.16,.15),(-.095,.24),(-.13,.31),(-.09,.37),(-.032,.34),(.032,.34),(.09,.37),(.13,.31),(.095,.24),(.16,.15),(.14,.05),(.075,0)]
 if typ=='bass':outline=[(-.07,0),(-.13,.06),(-.12,.19),(-.05,.28),(-.08,.4),(-.025,.36),(.025,.34),(.09,.42),(.065,.23),(.12,.16),(.115,.05),(.06,0)]
 verts=[(x*scale,y,z*scale+.02)for y in[-.045,.045]for x,z in outline];n=len(outline);faces=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)];mesh('Contoured_body',verts,faces,mat)
 neck=.70 if typ=='bass'else .57;box('Neck',(0,0,(.34+neck/2)*scale),(.050*scale,.045,neck*scale),wood,.005);box('Fingerboard',(0,-.025,(.34+neck/2)*scale),(.044*scale,.008,neck*scale),black,.002);box('Headstock',(0,0,(.38+neck)*scale),(.07*scale,.038,.11*scale),mat,.009)
 if typ!='bass':cylinder('Sound_hole',(0,-.046,.25*scale),.052*scale,.004,black,(math.pi/2,0,0))
 else:
  for z in[.16,.25]:box('Pickup',(0,-.048,z),(.085,.014,.022),black,.004)
 for i in range(18):box('Fret',(0,-.031,(.38+i*neck/19)*scale),(.045*scale,.002,.0015),silver)
 for i in range(4 if typ in['bass','ukulele']else 6):
  x=(i-(1.5 if typ in['bass','ukulele']else 2.5))*.007*scale;tube('String',[(x,-.055,.10*scale),(x,-.035,(.45+neck)*scale)],.00055,silver)
  cylinder('Tuning_key',((-.042 if i%2==0 else .042)*scale,0,(.37+neck+i*.008)*scale),.008,.025,silver,(0,math.pi/2,0))
 box('Bridge',(0,-.051,.105*scale),(.08*scale,.012,.022),black,.003);done('sku_v24_'+name,'music','Instrument-specific body, strings, frets, bridge and tuners')
# Foods use curved surfaces, layered ingredients and recognisable profiles.
v=[];faces=[]
for i in range(29):
 t=i/28;a=-1.15+2.3*t;centre=Vector((.09*math.sin(a),.045*math.cos(a),.025+.018*math.sin(math.pi*t)));r=.004+.025*math.sin(math.pi*t)**.7
 for j in range(16):
  b=j*math.tau/16;v.append(tuple(centre+Vector((math.cos(a)*r*math.cos(b),-math.sin(a)*r*math.cos(b),r*.72*math.sin(b)))))
for i in range(28):
 for j in range(16):k=i*16+j;faces.append((k,i*16+(j+1)%16,(i+1)*16+(j+1)%16,k+16))
mesh('Laminated_croissant',v,faces,crust)
for i in range(8):
 t=(i+1)/9;a=-1.15+2.3*t;r=.004+.025*math.sin(math.pi*t)**.7;tube('Pastry_lamination',[(.09*math.sin(a)+r*math.cos(a)*math.cos(b),.045*math.cos(a)-r*math.sin(a)*math.cos(b),.025+.018*math.sin(math.pi*t)+r*.73*math.sin(b))for b in[0,.4,.8,1.2,1.6,2.,2.5,3.1]],.0013,cream)
done('sku_v24_croissant','food','Curved tapered crescent with visible laminated dough ridges')
lathe('Tart_shell',[(.055,0),(.065,.01),(.066,.023),(.058,.028)],crust);lathe('Custard',[(.055,.02),(.055,.029),(.045,.034)],cream)
for i in range(7):
 a=i*math.tau/7;sphere('Strawberry',(.035*math.cos(a),.035*math.sin(a),.045),(.012,.012,.021),red)
 for j in range(3):tube('Calyx',[(.035*math.cos(a),.035*math.sin(a),.063),(.035*math.cos(a)+.011*math.cos(j*2.1),.035*math.sin(a)+.011*math.sin(j*2.1),.065)],.0018,green)
done('sku_v24_fruit_tart','food','Fluted pastry shell, custard and individual strawberries')
for z,mat in[(.012,cream),(.023,green),(.030,red),(.037,cream)]:mesh('Sandwich_layer',[(-.075,-.05,z),(.075,-.05,z),(0,.08,z),(-.075,-.05,z+.009),(.075,-.05,z+.009),(0,.08,z+.009)],[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],mat)
done('sku_v24_sandwich','food','Layered sliced sandwich: bread, salad and filling')
# Toys are products, not replacement NPCs.
for name,col in[('bear',material('Toy_ochre',(.53,.30,.11),.96)),('rabbit',material('Toy_linen',(.72,.64,.52),.96))]:
 sphere('Stitched_body',(0,0,.08),(.057,.043,.07),col);sphere('Head',(0,-.002,.16),(.048,.042,.047),col)
 for side in[-1,1]:
  sphere('Ear',(side*.034,0,.205 if name=='bear'else .235),(.018,.012,.02 if name=='bear'else .051),col);sphere('Arm',(side*.059,0,.105),(.018,.023,.04),col);sphere('Foot',(side*.031,-.015,.026),(.027,.031,.02),col);sphere('Button_eye',(side*.017,-.041,.17),(.004,.002,.004),black)
 sphere('Snout',(0,-.044,.151),(.021,.011,.014),cream);tube('Chest_seam',[(0,-.043,.04),(0,-.044,.10),(0,-.035,.14)],.0008,walnut);done('sku_v24_plush_'+name,'toy','Soft product silhouette, ears, eyes, stitched panels and feet')
box('Wooden_train_body',(0,0,.044),(.17,.065,.07),green,.01);box('Cab',(0,.015,.105),(.06,.06,.065),crust,.006);cylinder('Chimney',(-.04,-.01,.105),.012,.04,black)
for x in[-.054,.054]:
 for y in[-.043,.043]:cylinder('Wheels',(x,y,.024),.024,.012,wood,(math.pi/2,0,0))
done('sku_v24_train','toy','Wooden train cab, chassis, wheels and chimney')
box('Kit_box',(0,0,.045),(.18,.12,.09),cream,.005)
for i in range(4):box('Illustrated_blocks',(-.06+i*.039,-.061,.045),(.027,.002,.022+i*.009),[green,red,blue,crust][i],.003)
done('sku_v24_building_kit','toy','Building kit packaging and differentiated block illustration')
# Appliance casing, controls, rim and transparent drum.
box('Washer_body',(0,0,.43),(.62,.60,.86),white,.025);box('Control_fascia',(0,-.308,.77),(.57,.018,.12),ceramic,.012);ring('Steel_door_rim',(0,-.319,.39),.208,.027,silver,(math.pi/2,0,0));cylinder('Drum_window',(0,-.325,.39),.186,.012,black,(math.pi/2,0,0));ring('Inner_drum',(0,-.336,.39),.14,.008,metal,(math.pi/2,0,0));cylinder('Selector',(-.13,-.33,.78),.035,.026,silver,(math.pi/2,0,0));box('Digital_panel',(.14,-.33,.78),(.15,.008,.05),black,.006)
for i in range(3):box('Display_digit',(.09+i*.035,-.336,.78),(.015,.001,.022),emissive,.001)
done('sku_v24_washer','electronics','Rounded casing, dial, fascia and concentric front drum')
box('Fridge_body',(0,0,.88),(.70,.68,1.76),silver,.025)
for z,h in[(1.18,1.07),(.31,.52)]:box('Door',(0,-.35,z),(.67,.035,h),white,.018)
for z in[.52,1.22]:tube('Vertical_handle',[(.25,-.38,z-.14),(.25,-.41,z-.12),(.25,-.41,z+.12),(.25,-.38,z+.14)],.012,silver)
box('Display',(0,-.371,1.42),(.10,.008,.14),black,.006);done('sku_v24_fridge','electronics','Separate doors, gaskets, shaped handles and control display')
# Functional retail fixtures; no merchandise baked into shelf models.
box('Showcase_plinth',(0,0,.43),(1.7,.68,.86),ceramic,.04);box('Velvet_display_deck',(0,0,.883),(1.61,.60,.04),velvet,.015)
for x in[-.83,.83]:box('Case_end',(x,0,1.09),(.012,.66,.39),glass,.002)
for y in[-.33,.33]:box('Case_front_back',(0,y,1.09),(1.66,.012,.39),glass,.002)
box('Case_lid',(0,0,1.292),(1.68,.66,.012),glass,.002);done('fixture_v24_jewellery_case','fixture','Marble and velvet case with transparent cover',[.903])
# A proper two-sided book gondola: two imported empty bays back to back.
for side in[-1,1]:
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(P/'assets/v21/models/fixture_library_bay.glb'));objects=[o for o in bpy.data.objects if o not in before];roots=[o for o in objects if o.parent not in objects]
 for o in roots:o.location.y=side*.29;o.rotation_euler.z=math.pi if side>0 else 0
# Import transforms may be nested, bounds evaluated below.
done('fixture_v24_double_library','fixture','Back-to-back empty library gondola, two accessible reading faces',[.3475,.8075,1.2675,1.7275])
box('Pedestal_base',(0,0,.065),(.75,.65,.13),metal,.025);lathe('Sculpted_column',[(.27,.13),(.23,.2),(.19,.7),(.26,.81)],ceramic);box('Display_top',(0,0,.825),(1.2,.7,.03),ceramic,.06);done('fixture_v24_sculpted_table','fixture','Sculpted ceramic pedestal with rounded display top',[.84])
box('Locker_base',(0,0,.06),(2.2,.6,.12),metal,.015)
for j in range(4):
 for i in range(4):
  x=-.825+i*.55;z=.31+j*.43;box('Parcel_door',(x,0,z),(.53,.56,.41),white,.015);box('Pull_handle',(x+.18,-.29,z),(.018,.02,.10),metal,.004);box('Number_plate',(x-.12,-.29,z+.11),(.12,.003,.04),black,.002)
done('fixture_v24_parcel_lockers','fixture','Individual parcel lockers with handles and number plates')
box('Workbench',(0,0,.84),(1.8,.75,.07),wood,.025)
for x in[-.73,.73]:box('Workbench_leg',(x,0,.405),(.08,.60,.81),metal,.02)
box('Pegboard',(0,.29,1.35),(1.75,.04,.93),black,.02)
for i in range(5):tube('Tool_hook',[(-.6+i*.3,.25,1.32),(-.6+i*.3,.15,1.32),(-.6+i*.3,.15,1.40)],.008,silver)
done('fixture_v24_repair_bench','fixture','Service assessment workbench, pegboard and tool hooks',[.875])
# Track lighting has physical brackets and articulated spot housings.
box('Powered_track',(0,0,.035),(2.6,.055,.07),metal,.015)
for x in[-.95,0,.95]:
 box('Track_adapter',(x,0,-.025),(.12,.08,.04),black,.01);tube('Articulated_yoke',[(x-.055,0,-.02),(x-.055,0,-.1),(x+.055,0,-.1),(x+.055,0,-.02)],.008,metal);cylinder('Spot_housing',(x,0,-.14),.068,.13,metal);cylinder('Recessed_lens',(x,0,-.208),.058,.007,emissive)
done('finish_v24_track','finish','Track, yokes, housings and LED lenses; suspended only from verified ceiling')
(P/'source/v24/model-bounds.json').write_text(json.dumps(B,indent=2));(P/'source/v24/product-catalog.json').write_text(json.dumps(C,ensure_ascii=False,indent=2));print('V24_MODELS_DONE',len(B))
