import bpy,pathlib
P=pathlib.Path(__file__).resolve().parents[2];O=P/'assets/v32/models';bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def wood(name,colour):
 m=bpy.data.materials.new(name);m.diffuse_color=(*colour,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.48;t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(P/'assets/v25/models/fixture_v25_magazine_wood-oak.png'));m.node_tree.links.new(t.outputs['Color'],p.inputs['Base Color']);return m
base=wood('v32 CC0 oak veneer',(.48,.32,.19));metal=bpy.data.materials.new('v32 satin brass end frames');metal.diffuse_color=(.20,.18,.12,1);metal.use_nodes=True;metal.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value=.6;metal.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.35
shelf_heights=[.14,.52,.90]
def block(name,p,size,material,bevel=.009):
 bpy.ops.mesh.primitive_cube_add(size=1,location=(p[0],-p[2],p[1]));o=bpy.context.object;o.name=name;o.dimensions=(size[0],size[2],size[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material);b=o.modifiers.new('Machined eased shelf edge','BEVEL');b.width=bevel;b.segments=3;o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
for variant in [0,1]:
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);h=1.32 if variant==0 else 1.28
 block('Floor seated plinth',(0,.05,0),(1.80,.10,.78),base)
 block('Structural centre spine, both faces merchandised',(0,h*.5,0),(1.72,h,.035),base)
 for x in [-.87,.87]:
  for z in [-.355,.355]:block('Open end upright',(x,h*.5,z),(.045,h,.045),metal)
  for y in [.12,h-.035]:block('End cross rail',(x,y,0),(.045,.045,.75),metal)
 for side in [-1,1]:
  for y in shelf_heights:
   block('Three accessible shelves each side',(0,y-.016,side*.19),(1.72,.032,.35),base)
   block('Face-out book retaining lip',(0,y+.016,side*.355),(1.70,.032,.012),metal,.003)
 block('Top cap, below eye level',(0,h-.025,0),(1.74,.05,.10),base)
 bpy.ops.export_scene.gltf(filepath=str(O/f'double_book_{variant}.glb'),export_format='GLB',export_apply=True)
