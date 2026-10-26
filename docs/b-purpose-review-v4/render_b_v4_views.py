"""Blender standalone architectural illustrations. Never reads/writes Godot scene files."""
import bpy,json,math,sys,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path('/workspace/1');OUT=ROOT/'docs/b-purpose-review-v4';data=json.loads((OUT/'view-model.json').read_text());(OUT/'views').mkdir(exist_ok=True)
def material(name,color,metal=0,alpha=1):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,alpha);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,alpha);bs.inputs['Roughness'].default_value=.48;bs.inputs['Metallic'].default_value=metal;bs.inputs['Alpha'].default_value=alpha
 return m
for court in data['courts']:
 bpy.ops.wm.read_factory_settings(use_empty=True)
 scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.studio_light='basic.sl';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=False;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.background_type='WORLD';scene.display.shading.background_color=(.9,.92,.94);scene.display.render_aa='16';scene.view_settings.view_transform='Standard';scene.cycles.device='CPU';scene.cycles.samples=48;scene.cycles.use_denoising=False;scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.05;scene.cycles.max_bounces=3;scene.cycles.transparent_max_bounces=3
 scene.render.resolution_x=1400;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.world=bpy.data.worlds.new('World');scene.world.color=(.92,.94,.96);scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.76,.83,.95,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.75
 mats={'floor1':material('Ground terrazzo',(.80,.76,.67)),'floor2':material('Middle terrazzo',(.68,.73,.77)),'floor3':material('Upper terrazzo',(.84,.84,.81)),'plaster':material('Warm wall',(.78,.77,.71)),'glass':material('Storefront glazing',(.50,.68,.71),.05,.18),'fascia':material('Shop fascia',(.20,.28,.30)),'furniture':material('Shelf blocks',(.45,.35,.25)),'railglass':material('Guard glazing',(.55,.74,.78),.08,.20),'metal':material('Brushed metal',(.24,.29,.31),.65),'wood':material('Oak seating',(.45,.28,.13)),'stone':material('Planter stone',(.44,.43,.39)),'roof':material('Roof frame',(.32,.38,.42),.5),'steps':material('Escalator tread',(.12,.15,.16),.7)}
 green=material('Foliage',(.12,.28,.11));personmat=material('Scale figures',(.35,.39,.41));clockmat=material('Clock face',(.88,.86,.77))
 for mat,g in court['groups'].items():
  if mat in ['glass','railglass']:continue
  mesh=bpy.data.meshes.new(mat);mesh.from_pydata(g['vertices'],[],g['faces']);mesh.update();o=bpy.data.objects.new(mat,mesh);scene.collection.objects.link(o);o.data.materials.append(mats[mat])
 def uvball(pos,scale,mat):
  bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,location=pos);o=bpy.context.object;o.scale=scale;o.data.materials.append(mat);return o
 for prop in court['props']:
  x,y,z=prop['p']
  if prop['kind']=='plant':
   uvball((x,y,z+.10),(.75,.65,.45),green);uvball((x+.15,y+.1,z+.20),(.48,.45,.40),green)
  elif prop['kind']=='person':
   uvball((x,y,z+1.02),(.20,.14,.45),personmat);uvball((x,y,z+1.62),(.12,.12,.13),personmat)
   for dx in[-.09,.09]:uvball((x+dx,y,z+.38),(.075,.08,.39),personmat)
  elif prop['kind']=='board':
   bpy.ops.mesh.primitive_cube_add(size=1,location=(x,y,z+.4));o=bpy.context.object;o.scale=(2.4,.12,.8);o.rotation_euler[2]=math.atan2(prop['u'][1],prop['u'][0]);o.data.materials.append(mats['fascia'])
   cu=bpy.data.curves.new('direction board','FONT');cu.body=prop['text'];cu.size=.22;cu.align_x='CENTER';o=bpy.data.objects.new('INFO',cu);scene.collection.objects.link(o);o.location=(x,y-.08,z+.3);o.rotation_euler=(math.pi/2,0,math.atan2(prop['u'][1],prop['u'][0]));cu.materials.append(clockmat)
  elif prop['kind']=='clock':
   bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.55,depth=.09,location=(x,y,z),rotation=(math.pi/2,0,0));bpy.context.object.data.materials.append(clockmat)
   for ang,l in[(math.pi/2,.36),(.2,.27)]:
    bpy.ops.mesh.primitive_cube_add(size=1,location=(x+math.cos(ang)*l/2,y-.06,z+math.sin(ang)*l/2));o=bpy.context.object;o.scale=(l,.025,.035);o.rotation_euler[1]=-ang;o.data.materials.append(mats['metal'])
  elif prop['kind']=='wing':
   for sign in[-1,1]:o=uvball((x+sign*.35,y,z+1.1),(.20,.36,1.1),mats['metal']);o.rotation_euler[1]=sign*.35
  else:
   bpy.ops.mesh.primitive_torus_add(major_segments=20,minor_segments=6,location=(x,y,z),major_radius=.8,minor_radius=.04);bpy.context.object.rotation_euler=(.3,.5,.2);bpy.context.object.data.materials.append(mats['metal'])
 for label in court['labels']:
  cu=bpy.data.curves.new('tenant label','FONT');cu.body=label['text'];cu.size=.28;cu.align_x='CENTER';o=bpy.data.objects.new('label',cu);scene.collection.objects.link(o);o.location=label['p'];o.rotation_euler=(math.pi/2,0,math.atan2(label['u'][1],label['u'][0]));o.data.materials.append(clockmat)
 light=bpy.data.lights.new('Skylight','AREA');light.energy=16000;light.shape='DISK';light.size=45;o=bpy.data.objects.new('Skylight',light);scene.collection.objects.link(o);o.location=(0,0,25)
 sun=bpy.data.lights.new('Sun','SUN');sun.energy=1.4;o=bpy.data.objects.new('Sun',sun);scene.collection.objects.link(o);o.rotation_euler=(.35,-.35,.4)
 camdata=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',camdata);scene.collection.objects.link(cam);scene.camera=cam
 for camera in court['cameras']:
  bpy.data.objects['roof'].hide_render=(camera['id']=='axon')
  cam.location=camera['p'];direction=Vector(camera['target'])-cam.location;cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler();camdata.lens=camera['lens'];camdata.clip_end=400
  scene.render.filepath=str(OUT/'views'/f"{court['id']}-{camera['id']}.png");bpy.ops.render.render(write_still=True);print('RENDERED',scene.render.filepath,flush=True)
 (OUT/'views'/f"{court['id']}-manifest.json").write_text(json.dumps(dict(model_sha256=hashlib.sha256(json.dumps(court,sort_keys=True).encode()).hexdigest(),render_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),engine='BLENDER_WORKBENCH',design_only=True,not_game_screenshot=True,glass_omitted=True,roof_omitted_in_axon=True)))

