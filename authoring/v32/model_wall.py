import bpy,math,pathlib,json
P=pathlib.Path(__file__).resolve().parents[2]/'assets/v32/models';P.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def mat(n,c,r=.5,m=0):
 a=bpy.data.materials.new(n);a.diffuse_color=(*c,1);a.use_nodes=True;q=a.node_tree.nodes.get('Principled BSDF');q.inputs['Base Color'].default_value=(*c,1);q.inputs['Roughness'].default_value=r;q.inputs['Metallic'].default_value=m;return a
wood=mat('v32 walnut joinery',(.30,.19,.115));edge=mat('v32 warm oak shelf',(.60,.43,.25));metal=mat('v32 satin bronze',(.23,.19,.12),.3,.6);white=mat('v32 ceramic white',(.82,.79,.70),.4)
def block(n,loc,size,ma,bevel=.012):
 # Input x,y-height,z-depth -> Blender x,-z,y for glTF Y-up.
 bpy.ops.mesh.primitive_cube_add(size=1,location=(loc[0],-loc[2],loc[1]));o=bpy.context.object;o.name=n;o.dimensions=(size[0],size[2],size[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(ma)
 mod=o.modifiers.new('Joinery eased edges','BEVEL');mod.width=bevel;mod.segments=3;mod=o.modifiers.new('Weighted cabinet normals','WEIGHTED_NORMAL');return o
for variant in ['wide','narrow']:
 for kind in ['book','beauty','shoes','home','apparel','cafe','electronics','food','sports']:
  W=1.0 if variant=='narrow'else 2.0
  bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
  block('Closed back, seated against existing opaque boundary',(0,1.18,-.085),(W,2.32,.028),wood)
  for x in [-W/2+.015,W/2-.015]:block('Outer stile',(x,1.18,0),(.03,2.32,.19),wood)
  for y in [.03,2.325]:block('Bottom / crown',(0,y,0),(W,.06,.20),edge)
  if kind in ['apparel','sports']:
   block('Hanging rail',(0,2.10,.05),(W-.10,.025,.025),metal,.008);heights=[.18]
  else:heights={'book':[.32,.83,1.34,1.85],'beauty':[.34,.88,1.42,1.96],'shoes':[.30,.85,1.40,1.95],'home':[.30,.90,1.50,2.10],'cafe':[.32,.91,1.50],'electronics':[.35,1.12,1.89],'food':[.3,.85,1.4,1.95]}.get(kind,[.3,.9,1.5,2.1])
  for y in heights:
   block('Load-bearing shelf',(0,y-.018,0),(W-.06,.036,.17),edge)
   for x in [-W/2+.10,W/2-.10]:block('Shelf bracket',(x,y-.075,-.04),(.025,.10,.08),metal,.004)
  # recessed luminous header with actual mesh, not floating text-board.
  block('Integrated light diffuser',(0,2.25,.07),(W-.13,.027,.055),white,.005)
  bpy.ops.export_scene.gltf(filepath=str(P/('wall_'+kind+('_narrow'if variant=='narrow'else'')+'.glb')),export_format='GLB',export_apply=True)
json.dump({'creator':'Original FIND YOURSELF v32 Blender joinery','commercial_use':True,'third_party':False,'dimensions_m':[2,2.355,.20],'categories':9},open(P/'license.json','w'))
