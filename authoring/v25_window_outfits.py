from pathlib import Path
import sys,json,math,bmesh
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from v25_blender_common import *
B=json.loads((P/'source/v25/model-bounds.json').read_text());C=json.loads((P/'source/v25/product-catalog.json').read_text());ceramic=material('V25_porcelain_display',(.74,.72,.67),.48);cream=material('V25_linen_outfit',(.65,.61,.51),.88,texture='assets/v24/art/cloth-oat.png');navy=material('V25_navy_outfit',(.048,.075,.10),.89,texture='assets/v24/art/cloth-navy.png')
box('Raised_window_plinth',(0,0,.045),(1.8,.85,.09),stone,.035)
for person,x in enumerate([-.46,.46]):
 # Dedicated display form, not an animated NPC or borrowed commercial character.
 for side in[-1,1]:
  lathe('Trouser_or_leg',[(.05,.14),(.055,.30),(.065,.53),(.07,.72),(.08,.96)],navy if person==0 else ceramic,(x+side*.075,0,0),32)
  box('Soft_loafer',(x+side*.075,-.04,.14),(.13,.29,.10),metal,.04)
  tube('Relaxed_arm',[(x+side*.18,0,1.46),(x+side*.22,0,1.18),(x+side*.25,-.01,.99)],.043,ceramic)
  lathe('Hand_display',[(.018,0),(.035,.025),(.037,.085),(.015,.12)],ceramic,(x+side*.25,-.01,.91),24)
 lathe('Neck',[(.043,1.42),(.043,1.63)],ceramic,(x,0,0),32)
 lathe('Sculpted_display_head',[(.035,1.58),(.070,1.61),(.094,1.66),(.099,1.72),(.085,1.78),(.044,1.82),(0,1.83)],ceramic,(x,0,0),40)
 # Reuse our own v24 tailored shell; remove only hanger vertices before assembling the outfit.
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(P/'assets/v24/models/sku_v24_blazer.glb'));imported=[o for o in bpy.data.objects if o not in before];meshes=[o for o in imported if o.type=='MESH'];empties=[o for o in imported if o.type!='MESH']
 for o in meshes:
  # glTF imported axis conversion is preserved by baking world coordinates into mesh.
  world=o.matrix_world.copy();o.parent=None;o.matrix_world=Matrix.Identity(4);o.data.transform(world);bm=bmesh.new();bm.from_mesh(o.data);remove=[v for v in bm.verts if v.co.z>.755];bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(o.data);bm.free()
  if not len(o.data.vertices):bpy.data.objects.remove(o,do_unlink=True);continue
  if any('Oak'in m.name for m in o.data.materials):bpy.data.objects.remove(o,do_unlink=True);continue
  for k,m in enumerate(o.data.materials):
   if'Woven'in m.name:o.data.materials[k]=cream if person==0 else navy
  o.parent=None;o.location=(x,0,.83)
 for o in empties:bpy.data.objects.remove(o,do_unlink=True)
 if person==1:
  verts=[];faces=[]
  for j in range(13):
   t=j/12;z=.48+t*.50;radius=.24-.11*t
   for k in range(48):a=k*math.tau/48;rr=radius+.012*math.cos(a*12)*(1-t);verts.append((x+rr*math.cos(a),rr*math.sin(a)*.65,z))
  for j in range(12):
   for k in range(48):a=j*48+k;b=j*48+(k+1)%48;faces.append((a,b,b+48,a+48))
  mesh('Pleated_midi_skirt',verts,faces,cream,[(i%48/48,i//48/12)for i in range(len(verts))])
name='fixture_v25_window_outfits';bpy.context.view_layer.update();points=[o.matrix_world@Vector(c)for o in bpy.context.scene.objects if o.type in['MESH','CURVE']for c in o.bound_box];lo=[min(q[i]for q in points)for i in range(3)];hi=[max(q[i]for q in points)for i in range(3)];B[name]={'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]]};C[name]={'category':'window_display','source':'Original v25 sculpted display forms and coordinated outfits assembled with our own v24 tailoring; not an NPC character'};finish(name);(P/'source/v25/model-bounds.json').write_text(json.dumps(B,indent=2));(P/'source/v25/product-catalog.json').write_text(json.dumps(C,indent=2))
