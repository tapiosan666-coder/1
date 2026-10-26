"""Blender design-model render; no Godot resources imported or written."""
import bpy,json,hashlib,math,gzip
from pathlib import Path
from mathutils import Vector
R=Path('/workspace/1');O=R/'docs/ac-detailed-design-v1';(O/'views').mkdir(exist_ok=True);data=json.loads(gzip.decompress((O/'view-model.json.gz').read_bytes()))
def material(name,c):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);return m
for model in data['models']:
 bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.studio_light='basic.sl';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=False;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.background_type='WORLD';scene.display.shading.background_color=(.88,.91,.93);scene.display.render_aa='16';scene.view_settings.view_transform='Standard';scene.render.resolution_x=1500;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.world=bpy.data.worlds.new('World');scene.world.color=(.92,.94,.95)
 colors={'ground':(.71,.69,.64),'slab':(.77,.79,.77),'public':(.87,.85,.78),'paving':(.79,.80,.73),'wall0':(.81,.78,.69),'wall1':(.73,.76,.74),'wall2':(.72,.66,.57),'wall3':(.85,.84,.79),'metal':(.22,.29,.31),'fascia':(.18,.29,.32),'closed':(.70,.69,.64),'fixture':(.52,.39,.26),'steps':(.17,.23,.25),'wood':(.45,.28,.12),'stone':(.54,.54,.47),'grass':(.34,.49,.29)}
 mats={k:material(k,v)for k,v in colors.items()};leaf=material('Leaf',(.12,.28,.1));personmat=material('Scale figure',(.35,.40,.43));white=material('Letters',(.95,.94,.87))
 for kind,g in model['groups'].items():
  mesh=bpy.data.meshes.new(kind);mesh.from_pydata(g['vertices'],[],g['faces']);mesh.update();obj=bpy.data.objects.new(kind,mesh);scene.collection.objects.link(obj);obj.data.materials.append(mats[kind])
 def ball(pos,scale,mat):
  bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,location=pos);o=bpy.context.object;o.scale=scale;o.data.materials.append(mat)
 for prop in model['props']:
  x,z,y=prop['p']
  if prop['kind']=='plant':ball((x,z,y),(.8,.7,.6),leaf)
  elif prop['kind']=='person':
   ball((x,z,y+1.05),(.20,.14,.43),personmat);ball((x,z,y+1.63),(.12,.12,.13),personmat)
   for dx in[-.09,.09]:ball((x+dx,z,y+.39),(.075,.075,.4),personmat)
 for label in model['labels']:
  cu=bpy.data.curves.new('Shop label','FONT');cu.body=label['text'];cu.size=.30;cu.align_x='CENTER';o=bpy.data.objects.new('Label',cu);scene.collection.objects.link(o);o.location=label['p'];o.rotation_euler=(math.pi/2,0,math.atan2(label['u'][1],label['u'][0]));cu.materials.append(white)
 camdata=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',camdata);scene.collection.objects.link(cam);scene.camera=cam
 for c in model['cameras']:
  cam.location=c['p'];direction=Vector(c['target'])-cam.location;cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler();camdata.clip_end=500
  if c['orthographic']:camdata.type='ORTHO';camdata.ortho_scale=c['ortho_scale']
  else:camdata.type='PERSP';camdata.lens=c['lens']
  scene.render.filepath=str(O/'views'/f"{model['id']}-{c['id']}.png");bpy.ops.render.render(write_still=True);print('RENDERED',scene.render.filepath,flush=True)
 (O/'views'/f"{model['id']}-manifest.json").write_text(json.dumps({'model_sha256':hashlib.sha256(json.dumps(model,sort_keys=True).encode()).hexdigest(),'source_geometry_sha256':model['source_sha256'],'render_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'design_only':True,'not_game_screenshot':True,'engine':'BLENDER_WORKBENCH','glass_omitted':True,'roof_and_structure_simplified':True}))
