import bpy,math,pathlib,json
P=pathlib.Path(__file__).resolve().parents[2]/'assets/v32/models';bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def mat(n,c,r=.5,m=0):
 a=bpy.data.materials.new(n);a.diffuse_color=(*c,1);a.use_nodes=True;q=a.node_tree.nodes.get('Principled BSDF');q.inputs['Base Color'].default_value=(*c,1);q.inputs['Roughness'].default_value=r;q.inputs['Metallic'].default_value=m;return a
cream=mat('Original woven awning canvas',(.78,.71,.55),.88);green=mat('Original forest canvas',(.13,.24,.21),.88);metal=mat('Satin dark aluminium',(.12,.14,.14),.36,.65);wood=mat('Oiled timber',(.30,.17,.09),.64)
def block(n,p,size,m):
 bpy.ops.mesh.primitive_cube_add(size=1,location=(p[0],-p[2],p[1]));o=bpy.context.object;o.name=n;o.dimensions=(size[0],size[2],size[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);b=o.modifiers.new('Rounded folded edge','BEVEL');b.width=.018;b.segments=3;o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');return o
for variant in ['canvas','louvre','glass']:
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 for x in [-2.25,2.25]:
  block('Wall bearing connection plate',(x,3.11,-.035),(.18,.50,.08),metal)
  block('Cantilever rib',(x,3.32,.64),(.10,.12,1.34),metal)
  o=block('Triangular knee bracket',(x,3.06,.35),(.07,.075,.84),metal);o.rotation_euler.x=math.radians(-32)
 block('Front fascia',(0,3.32,1.30),(4.70,.18,.085),wood if variant=='louvre'else metal)
 if variant=='canvas':
  for j in range(16):
   x=-2.35+(j+.5)*4.7/16;block('Tailored alternating canvas strip',(x,3.38,.67),(4.7/16+.002,.025,1.36),cream if j%2 else green)
 elif variant=='louvre':
  for j in range(13):block('Timber sun-control slat',(0,3.40,j*.105),(4.70,.075,.065),wood)
 else:
  glass=mat('Smoked translucent polycarbonate',(.46,.64,.66),.16,.08);glass.surface_render_method='DITHERED';glass.node_tree.nodes.get('Principled BSDF').inputs['Transmission Weight'].default_value=.65
  for j in range(4):block('Tinted canopy panel',(-1.76+j*1.175,3.39,.66),(1.15,.022,1.30),glass)
 bpy.ops.export_scene.gltf(filepath=str(P/('canopy_'+variant+'.glb')),export_format='GLB',export_apply=True)
