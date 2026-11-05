import sys,math,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'))
from v294_common import *
B={};sources=set()
def asset(model,x,y,z,height=None,width=None,turn=0):
 paths=list(P.glob('assets/v*/models/'+model+'.glb'));path=paths[-1];sources.add(str(path.relative_to(P)));before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(path));new=[o for o in bpy.data.objects if o not in before];objs=[o for o in new if o.type=='MESH']
 if model=='sku_v23_tablet':
  # Legacy tablet body was tilted but its screen label was not: upper half clipped inside.
  Q=Matrix.Translation(Vector((0,0,.10)))@Matrix.Rotation(.22,4,'X')@Matrix.Translation(Vector((0,0,-.10)))
  for o in objs:
   if any(m and m.name.startswith('V23_original_editorial')for m in o.data.materials):o.matrix_world=Q@o.matrix_world
 pts=[o.matrix_world@Vector(c)for o in objs for c in o.bound_box];lo=Vector([min(p[i]for p in pts)for i in range(3)]);hi=Vector([max(p[i]for p in pts)for i in range(3)]);k=height/(hi.z-lo.z)if height else 1
 if width:k=min(k,width/max(hi.x-lo.x,hi.y-lo.y))
 center=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z));T=Matrix.Translation(Vector((x,y,z)))@Matrix.Rotation(turn,4,'Z')@Matrix.Scale(k,4)@Matrix.Translation(-center)
 for o in objs:
  world=o.matrix_world.copy();o.parent=None;o.matrix_world=Matrix.Identity(4);o.data.transform(T@world)
 for o in new:
  if o.type!='MESH':bpy.data.objects.remove(o,do_unlink=True)
 return objs

def emit(name,role):
 if name.endswith('_room_v294'):
  span,back,top=(2.6,1.95,2.52)if name.startswith('cinema')else(2.55,1.95,2.42)if name.startswith('kitchen')else(2.,1.60,2.18)
  for x in [-span,span]:
   box('Exhibit_floor_anchor_plate',(x,back,-.015),(.24,.24,.01),metal,.004)
   box('Exhibit_backboard_support',(x,back+.04,(top-.01)/2),(.04,.06,top+.01),metal,.004)
   for dx in [-.07,.07]:
    for dy in [-.07,.07]:box('Anchor_bolt_head',(x+dx,back+dy,-.006),(.022,.022,.008),steel,.003)
 bpy.context.view_layer.update();pts=[o.matrix_world@Vector(c)for o in bpy.context.scene.objects if o.type in ['MESH','CURVE']for c in o.bound_box];lo=[min(q[i]for q in pts)for i in range(3)];hi=[max(q[i]for q in pts)for i in range(3)];B[name]={'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]],'role':role,'sources':sorted(sources)};finish(name);sources.clear()



felt=material('V294_Acoustic_felt',(.15,.21,.22),.93)
rug=material('V294_Woven_rug',(.29,.34,.32),.96)
def counter():
 box('Compact_recessed_toe',(0,0,.06),(1.72,.65,.12),metal,.02)
 box('Compact_joinery',(0,0,.46),(1.82,.74,.72),walnut,.025)
 box('Compact_worktop',(0,0,.85),(1.90,.80,.06),stone,.018)
 for x in [-.5,.5]:box('Compact_product_label',(x,-.38,.93),(.30,.055,.16),paper,.008)

counter()
asset('sku_laptop',-0.5,0,.89,height=0.3,width=.62)
asset('sku_laptop',0.5,0,.89,height=0.3,width=.62)
emit('compact_pc_v294','compact_pc_experience')

counter()
asset('sku_phone',-0.5,0,.89,height=0.25,width=.62)
asset('sku_v23_tablet',0.5,0,.89,height=0.25,width=.62)
emit('compact_mobile_v294','compact_mobile_experience')

counter()
asset('sku_v23_headphones',-0.5,0,.89,height=0.25,width=.62)
asset('sku_speaker',0.5,0,.89,height=0.25,width=.62)
emit('compact_audio_v294','compact_audio_experience')

counter()
asset('sku_v24_watch',-0.5,0,.89,height=0.08,width=.62)
asset('sku_v23_headphones',0.5,0,.89,height=0.25,width=.62)
emit('compact_accessory_v294','compact_accessory_experience')

box('TV_compact_console',(0,0,.33),(1.88,.78,.65),walnut,.022)
asset('sku_tv',0,.10,.67,height=.92,width=1.70)
box('TV_specification_holder',(0,-.399,.34),(.42,.015,.22),paper,.006)
emit('compact_tv_v294','compact_tv_comparison')

# An open demonstration living room. Backboard is retail joinery, not new building wall.
box('Cinema_rug',(0,0,-.012),(5.8,4.6,.016),rug,.002)
box('Cinema_backboard',(0,1.95,1.27),(5.55,.12,2.5),felt,.025)
for x in [-2.7,-2.5,-2.3,2.3,2.5,2.7]:box('Oak_acoustic_strip',(x,1.87,1.27),(.065,.06,2.45),wood,.009)
box('Media_console',(0,1.28,.37),(3.4,.70,.73),walnut,.025)
asset('sku_tv',0,1.30,.76,height=1.25,width=2.25)
for x in [-2.15,2.15]:asset('sku_speaker',x,1.25,-.004,height=1.05,width=.40)
asset('lounge_sofa',0,-1.35,-.004,height=.94,width=2.75,turn=math.pi)
box('Low_coffee_table',(0,-.13,.43),(1.3,.65,.07),wood,.035)
for x in [-.51,.51]:
 for y in [-.21,.21]:tube('Coffee_table_leg',[(x,y,.02),(x,y,.40)],.025,metal)
asset('sku_cup',.25,-.10,.47,height=.10,width=.14)
emit('cinema_room_v294','home_cinema_experience')

box('Kitchen_rug',(0,0,-.012),(5.8,4.6,.016),rug,.002)
box('Kitchen_display_back',(0,1.95,1.22),(5.5,.09,2.4),stone,.02)
box('Kitchen_joinery',(0,1.25,.48),(3.30,.80,.94),walnut,.025)
for x in [-1.2,-.4,.4,1.2]:
 box('Kitchen_cabinet_front',(x,.835,.47),(.74,.025,.80),wood,.012)
 tube('Kitchen_drawer_pull',[(x-.16,.81,.81),(x+.16,.81,.81)],.012,metal)
box('Kitchen_worktop',(0,1.25,.985),(3.42,.88,.06),stone,.02)
asset('sku_fridge',-2.15,1.18,-.004,height=1.92,width=.82)
asset('sku_espresso_machine',-.95,1.21,1.02,height=.53,width=.73)
asset('sku_kettle',.65,1.23,1.02,height=.30,width=.30)
box('Dining_island',(.2,-.65,.48),(2.2,.83,.94),wood,.035)
box('Island_stone_top',(.2,-.65,.985),(2.30,.92,.06),stone,.025)
for x in [-.4,.65]:asset('sku_chair',x,-1.55,-.004,height=.89,width=.50,turn=math.pi)
asset('sku_cup',.55,-.62,1.02,height=.12,width=.16)
emit('kitchen_room_v294','kitchen_and_coffee_experience')

box('Workspace_rug',(0,0,-.012),(4.6,3.8,.016),rug,.002)
box('Workspace_acoustic_back',(0,1.60,1.10),(4.30,.09,2.16),felt,.025)
box('Workdesk_top',(0,.65,.77),(2.70,.90,.065),wood,.025)
for x in [-1.22,1.22]:
 for y in [.31,.99]:tube('Desk_leg',[(x,y,.02),(x,y,.735)],.028,metal)
asset('sku_laptop',-.55,.66,.81,height=.32,width=.66)
asset('sku_v23_tablet',.55,.65,.81,height=.27,width=.35)
asset('sku_chair',0,-.45,-.004,height=.98,width=.65,turn=math.pi)
asset('sku_v23_desk_lamp',1.03,.72,.81,height=.54,width=.35)
box('Notebook',(0,.45,.825),(.25,.19,.025),paper,.005)
emit('workspace_room_v294','home_office_experience')
(P/'source/v294/model-bounds.json').write_text(json.dumps(B,ensure_ascii=False,indent=2))
