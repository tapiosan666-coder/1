"""Original asset portraits for in-world posters, never submitted as Godot screenshots."""
from pathlib import Path
import bpy,math
from mathutils import Vector
P=Path(__file__).resolve().parents[1];A=P/'assets/v24/art';A.mkdir(exist_ok=True)
items={'apparel':'v24/models/sku_v24_blazer','shoes':'v23/models/sku_v23_sneaker','beauty':'v23/models/sku_v23_perfume','home':'v23/models/sku_v23_tea_pot','book':'v23/models/sku_v23_book_0','food':'v24/models/sku_v24_fruit_tart','electronics':'v24/models/sku_v24_washer','toy':'v24/models/sku_v24_plush_bear','accessories':'v24/models/sku_v24_necklace','sports':'v22/models/sku_racket','music':'v24/models/sku_v24_electric_bass'}
for name,asset in items.items():
 if "--only-apparel"in __import__("sys").argv and name!="apparel":continue
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'assets'/f'{asset}.glb'));bpy.context.view_layer.update();objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];points=[o.matrix_world@Vector(c)for o in objects for c in o.bound_box];lo=Vector([min(q[i]for q in points)for i in range(3)]);hi=Vector([max(q[i]for q in points)for i in range(3)]);centre=(lo+hi)/2;scale=2.1/max(hi-lo)
 bpy.ops.object.empty_add();anchor=bpy.context.object;anchor.name='Poster_product_only'
 for o in [o for o in bpy.context.scene.objects if o!=anchor and o.parent is None]:o.parent=anchor
 anchor.scale=Vector((scale,)*3);anchor.location=-centre*scale+Vector((0,0,1.25))
 bpy.ops.object.camera_add(location=(2.7,-4.8,2.6));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,1.25))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.9;bpy.context.scene.camera=cam
 for loc,power,size in[((-2,-3,5),400,4),((3,1,3),250,3),((0,2,4),300,2)]:
  bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.data.energy=power;l.data.shape='DISK';l.data.size=size;l.rotation_euler=(Vector((0,0,1.2))-l.location).to_track_quat('-Z','Y').to_euler()
 s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=False;s.render.film_transparent=True;s.render.resolution_x=512;s.render.resolution_y=640;s.render.resolution_percentage=100;s.world=bpy.data.worlds.new('Original_product_studio');s.world.color=(.25,.25,.25);s.render.image_settings.file_format='PNG';s.render.filepath=str(A/f'product-portrait-{name}.png');bpy.ops.render.render(write_still=True);print('V24_POSTER_ART',name,flush=True)
