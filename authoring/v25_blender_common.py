"""Original retail assets modelled in Blender. Curved profiles, garment surfaces, bevelled joinery.
Exported models are original project assets; CC0 wood image attribution retained separately.
"""
import bpy,math,random,json,sys
from mathutils import Vector,Matrix
import bmesh
from pathlib import Path
P=Path(__file__).resolve().parents[1];OUT=P/'assets/v25/models';OUT.mkdir(parents=True,exist_ok=True);rng=random.Random(10104)
bpy.ops.wm.read_factory_settings(use_empty=True)
def material(name,col,rough=.5,metal=0,texture=None):
 m=bpy.data.materials.new(name);m.use_nodes=True;s=m.node_tree.nodes.get('Principled BSDF');s.inputs['Base Color'].default_value=(*col,1);s.inputs['Roughness'].default_value=rough;s.inputs['Metallic'].default_value=metal
 if texture:
  im=bpy.data.images.load(str(P/texture),check_existing=True);tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;m.node_tree.links.new(tex.outputs['Color'],s.inputs['Base Color'])
 return m
wood=material('CC0_Oak_veneer',(.40,.25,.11),.43,texture='assets/v10/wood-oak.png');walnut=material('CC0_Smoked_walnut',(.23,.13,.07),.40,texture='assets/v10/wood-walnut.png');metal=material('Anodised_graphite',(.038,.043,.044),.30,.75);brass=material('Satin_champagne',(.49,.34,.15),.28,.76);stone=material('Honed_solid_surface',(.72,.70,.64),.31);white=material('Warm_white_coating',(.77,.75,.70),.6);paper=material('Paper_page_edges',(.79,.77,.69),.85);skin=material('Display_mannequin_porcelain',(.72,.70,.65),.48);rubber=material('Grip_rubber',(.012,.015,.014),.8)
fabrics=[material('Woven_'+str(i),c,.88)for i,c in enumerate([(.075,.11,.14),(.59,.54,.43),(.23,.30,.23),(.37,.14,.10),(.57,.59,.56)])]
bookmats=[material('Book_jacket_'+str(i),c,.63)for i,c in enumerate([(.06,.13,.15),(.35,.12,.07),(.58,.48,.30),(.13,.18,.25),(.28,.31,.23),(.56,.54,.47)])]
glass=material('Shop_display_glass',(.8,.88,.88),.06);gs=glass.node_tree.nodes.get('Principled BSDF');gs.inputs['Transmission Weight'].default_value=.85;gs.inputs['IOR'].default_value=1.46;gs.inputs['Alpha'].default_value=.18;glass.surface_render_method='DITHERED'
ceramics=[material('Glazed_ceramic_'+str(i),c,.24)for i,c in enumerate([(.73,.72,.65),(.13,.24,.19),(.42,.19,.09)])];pastry=material('Laminated_pastry',(.53,.25,.075),.64);steel=material('Brushed_stainless',(.49,.52,.54),.28,.9)
spine=material('Original_book_spine_atlas',(1,1,1),.75,texture='assets/v8/book-spines.png')
def box(name,loc,size,mat,b=.007):
 sx,sy,sz=[v/2 for v in size];vv=[(-sx,-sy,-sz),(sx,-sy,-sz),(sx,sy,-sz),(-sx,sy,-sz),(-sx,-sy,sz),(sx,-sy,sz),(sx,sy,sz),(-sx,sy,sz)];ff=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
 me=bpy.data.meshes.new(name);me.from_pydata(vv,[],ff);me.update()
 if b:
  bm=bmesh.new();bm.from_mesh(me);bmesh.ops.bevel(bm,geom=list(bm.edges),offset=min(b,min(size)*.25),segments=2,affect='EDGES',clamp_overlap=True);bm.to_mesh(me);bm.free()
 o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.location=loc;me.materials.append(mat)
 uv=me.uv_layers.new(name='UVMap')
 for face in me.polygons:
  axis=max(range(3),key=lambda i:abs(face.normal[i]));axes=[i for i in range(3)if i!=axis]
  for li,vi in zip(face.loop_indices,face.vertices):uv.data[li].uv=(me.vertices[vi].co[axes[0]]+size[axes[0]]/2,me.vertices[vi].co[axes[1]]+size[axes[1]]/2)
 return o

def mesh(name,verts,faces,mat,uv=None):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.data.materials.append(mat)
 for f in me.polygons:f.use_smooth=True
 if uv:
  layer=me.uv_layers.new(name='UVMap')
  for poly in me.polygons:
   for li,vi in zip(poly.loop_indices,poly.vertices):layer.data[li].uv=uv[vi]
 return o
def tube(name,points,r,mat):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=8;cu.bevel_depth=r;cu.bevel_resolution=3;cu.use_fill_caps=True;sp=cu.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
 for p,co in zip(sp.bezier_points,points):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
 o=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(o);o.data.materials.append(mat);return o
def lathe(name,profile,mat,loc=(0,0,0),steps=32):
 v=[];uv=[];f=[]
 for j,(r,z)in enumerate(profile):
  for i in range(steps):a=i*math.tau/steps;v.append((loc[0]+math.cos(a)*r,loc[1]+math.sin(a)*r,loc[2]+z));uv.append((i/steps,j/(len(profile)-1)))
 for j in range(len(profile)-1):
  for i in range(steps):k=j*steps+i;nx=j*steps+(i+1)%steps;f.append((k,nx,nx+steps,k+steps))
 return mesh(name,v,f,mat,uv)
def move_all(offset):
 for o in bpy.context.scene.objects:o.location+=Vector(offset)
def clear():
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def finish(name):
 # Convert curves and consolidate by material: complex merchandise does not create thousands of draw calls.
 bpy.ops.object.select_all(action='SELECT');bpy.context.view_layer.objects.active=next(iter(bpy.context.scene.objects));bpy.ops.object.convert(target='MESH');objects=list(bpy.context.scene.objects)
 for o in objects:
  if o.type!='MESH':continue
  bpy.context.view_layer.objects.active=o;o.select_set(True)
  if len(o.data.materials)>1:bpy.ops.mesh.separate(type='MATERIAL')
  o.select_set(False)
 groups={}
 for o in list(bpy.context.scene.objects):
  if o.type=='MESH'and len(o.data.vertices):groups.setdefault(o.data.materials[0].name if o.data.materials else'plain',[]).append(o)
 for key,group in groups.items():
  bpy.ops.object.select_all(action='DESELECT')
  for o in group:o.select_set(True)
  bpy.context.view_layer.objects.active=group[0];bpy.ops.object.join();group[0].name=name+'_'+key
 bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.gltf(filepath=str(OUT/(name+'.glb')),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_animations=False,export_cameras=False,export_lights=False,export_image_format='AUTO')
 print('RETAIL_ASSET',name,flush=True);clear()
