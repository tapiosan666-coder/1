import sys,math,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'))
from v293_common import *
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
 bpy.context.view_layer.update();pts=[o.matrix_world@Vector(c)for o in bpy.context.scene.objects if o.type in ['MESH','CURVE']for c in o.bound_box];lo=[min(q[i]for q in pts)for i in range(3)];hi=[max(q[i]for q in pts)for i in range(3)];B[name]={'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]],'role':role,'sources':sorted(sources)};finish(name);sources.clear()


# mobile_experience: dedicated fixtures and equipment at full scale.
box('Recessed_toe',(0,0,.07),(2.48,1.22,.14),metal,.025)
box('Oak_service_joinery',(0,0,.46),(2.72,1.44,.73),walnut,.04)
box('Honed_demonstration_surface',(0,0,.865),(2.80,1.52,.075),stone,.03)
asset('sku_phone',-0.9,-.05,.91,height=0.25,width=.65)
box('Angled_spec_card',(-0.9,-.54,.96),(.26,.06,.14),paper,.012)
asset('sku_v23_tablet',0.0,-.05,.91,height=0.25,width=.65)
box('Angled_spec_card',(0.0,-.54,.96),(.26,.06,.14),paper,.012)
asset('sku_v23_headphones',0.9,-.05,.91,height=0.25,width=.65)
box('Angled_spec_card',(0.9,-.54,.96),(.26,.06,.14),paper,.012)
emit('mobile_experience_v293','mobile_experience')

# computer_experience: dedicated fixtures and equipment at full scale.
box('Recessed_toe',(0,0,.07),(2.48,1.22,.14),metal,.025)
box('Oak_service_joinery',(0,0,.46),(2.72,1.44,.73),walnut,.04)
box('Honed_demonstration_surface',(0,0,.865),(2.80,1.52,.075),stone,.03)
asset('sku_laptop',-0.9,-.05,.91,height=0.3,width=.65)
box('Angled_spec_card',(-0.9,-.54,.96),(.26,.06,.14),paper,.012)
asset('sku_laptop',0.0,-.05,.91,height=0.3,width=.65)
box('Angled_spec_card',(0.0,-.54,.96),(.26,.06,.14),paper,.012)
asset('sku_v23_tablet',0.9,-.05,.91,height=0.25,width=.65)
box('Angled_spec_card',(0.9,-.54,.96),(.26,.06,.14),paper,.012)
emit('computer_experience_v293','computer_experience')

# audio_listening: dedicated fixtures and equipment at full scale.
box('Recessed_toe',(0,0,.07),(2.48,1.22,.14),metal,.025)
box('Oak_service_joinery',(0,0,.46),(2.72,1.44,.73),walnut,.04)
box('Honed_demonstration_surface',(0,0,.865),(2.80,1.52,.075),stone,.03)
asset('sku_v23_headphones',-0.9,-.05,.91,height=0.25,width=.65)
box('Angled_spec_card',(-0.9,-.54,.96),(.26,.06,.14),paper,.012)
asset('sku_v23_headphones',0.0,-.05,.91,height=0.25,width=.65)
box('Angled_spec_card',(0.0,-.54,.96),(.26,.06,.14),paper,.012)
asset('sku_v23_headphones',0.9,-.05,.91,height=0.25,width=.65)
box('Angled_spec_card',(0.9,-.54,.96),(.26,.06,.14),paper,.012)
tube('Listening_sanitiser_rail',[(-1.3,.55,1.10),(1.3,.55,1.10)],.018,brass)
emit('audio_listening_v293','audio_listening')

# screen_compare: dedicated fixtures and equipment at full scale.
box('Acoustic_back',(0,.39,1.20),(2.75,.10,2.32),walnut,.035)
box('Display_console',(0,0,.32),(2.75,1.32,.60),metal,.035)
asset('sku_tv',-0.68,0,.64,height=.92,width=1.28)
asset('sku_tv',0.68,0,.64,height=.92,width=1.28)
emit('screen_compare_v293','screen_compare')

# Dedicated accessories wall, separate from the mobile try-out counter.
box('Accessory_toe',(0,0,.07),(2.48,1.22,.14),metal,.025)
box('Accessory_joinery',(0,0,.46),(2.72,1.44,.73),white,.04)
box('Accessory_surface',(0,0,.865),(2.80,1.52,.075),wood,.03)
box('Perforated_display_back',(0,.53,1.43),(2.70,.07,1.04),metal,.018)
for x in [-1.,-.50,0.,.50,1.]:
 for z in [1.10,1.35,1.60,1.85]:box('Pegboard_horizontal_slot',(x,.484,z),(.12,.008,.018),white,.004)
asset('sku_v24_watch',-.92,-.12,.91,height=.08,width=.13)
asset('sku_speaker',0,-.06,.91,height=.36,width=.29)
asset('sku_v23_headphones',.88,-.09,.91,height=.29,width=.30)
for x in [-.92,0,.88]:box('Accessory_info_card',(x,-.54,.98),(.27,.06,.14),paper,.01)
emit('accessory_consult_v293','wearables_speakers_and_headphones')
(P/'source/v293/model-bounds.json').write_text(json.dumps(B,ensure_ascii=False,indent=2))
