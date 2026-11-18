"""Build the original v34 high-touch displays in Blender 4.x.

Run blender -b -t 2 -P authoring/v34/build_retail.py from the project root.
No external geometry, materials, or textures are used.
"""
import math
import random
import sys
from pathlib import Path

import bpy

DEST = Path.cwd() / "assets/v34/models"
DEST.mkdir(parents=True, exist_ok=True)


def material(name, color, rough=.56, metal=0):
    item = bpy.data.materials.get(name)
    if item:
        return item
    item = bpy.data.materials.new(name)
    item.diffuse_color = (*color, 1)
    item.use_nodes = True
    shader = item.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = rough
    shader.inputs["Metallic"].default_value = metal
    return item


# Studio palette uses linear values. Products keep recognisable colour at mall distance.
OAK = material("Honey oak", (.36, .19, .075))
OAK_EDGE = material("Oak end grain", (.48, .29, .135))
OLIVE = material("Rivora olives", (.14, .205, .078))
CREAM = material("Bone ceramic", (.72, .61, .46))
IVORY = material("Porcelain white", (.72, .73, .69))
WALNUT = material("Terrune smoked walnut", (.135, .069, .029))
PLASTER = material("Warm limestone", (.45, .39, .29))
BLACK = material("Powder-coated steel", (.022, .027, .031), .51, .35)
ALLOY = material("Suvel anodised aluminium", (.26, .35, .40), .38, .6)
BLUE = material("Suvel ink blue", (.036, .107, .177))
VIOLET = material("Harbor lavender", (.30, .39, .66))
GLAZED = material("Celadon ceramic", (.12, .305, .27), .29)
COPPER = material("Brushed bronze", (.47, .21, .069), .4, .57)
KRAFT = material("Recycled kraft", (.47, .31, .13))
GILT = material("Marigold label", (.76, .35, .023))
RED = material("Red apple skin", (.49, .044, .018), .37)
ORANGE = material("Satsuma skin", (.74, .235, .015), .59)
GREEN = material("Green apple skin", (.24, .41, .05), .42)
LEAF = material("Fresh leaf", (.12, .27, .038))
DARK_RED = material("Ruby label", (.36, .049, .03))
SEA = material("Deep lake", (.024, .16, .29))
SKY = material("Sunlit clouds", (.23, .47, .72))
SCREEN = material("Display glass black", (.015, .019, .032), .22)
BREAD = material("Rye crust", (.49, .197, .044))
FLOUR = material("Floured scoring", (.78, .54, .30))


def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)


def paint(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj


def box(name, x, y, z, w, d, h, mat, radius=.014):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x, y, z))
    obj = bpy.context.object
    obj.name = name
    obj.scale = (w / 2, d / 2, h / 2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if radius:
        bevel = obj.modifiers.new("Machined edges", "BEVEL")
        bevel.width = radius
        bevel.segments = 2
    paint(obj, mat)
    return obj


def cylinder(name, x, y, z, rad, height, mat, upper=None, verts=16):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=rad, radius2=rad if upper is None else upper,
                                   depth=height, location=(x, y, z))
    obj = bpy.context.object
    obj.name = name
    paint(obj, mat)
    for polygon in obj.data.polygons:
        polygon.use_smooth = len(polygon.vertices) == 4
    return obj


def spheroid(name, x, y, z, sx, sy, sz, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, location=(x, y, z))
    obj = bpy.context.object
    obj.name = name
    obj.scale = (sx, sy, sz)
    paint(obj, mat)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def table(w, d, top=.67, base=OAK, trim=BLACK):
    for x in (-w*.40, w*.40):
        for y in (-d*.36, d*.36):
            box("Seated steel leg", x, y, (top-.06)*.5, .07, .07, top-.06, trim, .009)
    box("Longitudinal stretcher", 0, 0, .21, w*.80, .06, .09, trim)
    for x in (-w*.40, w*.40):
        box("End tie to both legs", x, 0, .21, .062, d*.72, .085, trim, .008)
    box("Face grain worktop", 0, 0, top-.032, w, d, .064, base, .021)
    for y in (-d/2 + .017, d/2 - .017):
        box("Edge band", 0, y, top-.065, w-.045, .029, .019, base, .004)


def fruit(name, w, d, seed, colors):
    rng = random.Random(seed)
    top = .49 if name.endswith('_large') else .61
    table(w, d, top, OAK, OLIVE)
    depth = d*.77
    for basket in range(3):
        cx = (basket - 1) * w*.318
        span = w*.30
        box("Crate deck", cx, 0, top+.02, span, depth, .04, OAK_EDGE, .012)
        for xx in (cx-span*.47, cx+span*.47):
            box("Crate side", xx, 0, top+.078, .028, depth, .115, OAK_EDGE, .006)
        for yy in (-depth*.47, depth*.47):
            box("Crate front", cx, yy, top+.067, span, .027, .096, OAK_EDGE, .006)
            box("Label rail", cx, yy*1.034, top+.061, span*.6, .009, .036, OLIVE, .002)
        rad = min(.062, span*.096)
        for ii in range(4):
            for jj in range(4):
                x = cx+span*(ii-1.5)*.195+rng.uniform(-.012,.012)
                y = depth*(jj-1.5)*.196+rng.uniform(-.012,.012)
                r = rad*rng.uniform(.88,1.08)
                color = colors[basket]
                spheroid("Market fruit", x, y, top+.04+r, r, r, r*.96, color)
                if color != ORANGE or jj == 0:
                    cylinder("Fruit stem", x, y, top+.04+r*1.96, .006, .022, WALNUT, .004, 7)
                if (ii + 2*jj + basket) % 7 == 0:
                    leaf = spheroid("Fruit leaf", x+.024, y, top+.04+r*2, .037,.014,.006,LEAF)
                    leaf.rotation_euler.y=.3
    return 48


def preserve(name, w, d, seed, _):
    table(w,d,.66,OAK,OLIVE)
    for i in range(5):
        for j in range(3):
            x=(i-2)*w*.16
            y=(j-1)*d*.235
            mat = (LEAF, GILT, DARK_RED, CREAM, GLAZED)[i]
            cylinder("Farm preserve bottle",x,y,.66+.092,.06,.184,mat,.052)
            cylinder("Paper label",x,y,.66+.083,.062,.075,KRAFT,.059)
            cylinder("Lid",x,y,.66+.191,.055,.018,BLACK)
            box("Print block",x,y-.06,.66+.082,.055,.008,.024,mat,.002)
    for x in (-w*.40,w*.40):
        box("Bottled pantry table end",x,0,.76,.070,d*.66,.23,OLIVE,.01)
    return 15


def bakery(name, w, d, seed, _):
    rng = random.Random(seed)
    table(w,d,.59,OAK,OLIVE)
    for j in range(3):
        x=(j-1)*w*.305
        box("Baked goods tray",x,0,.62,w*.285,d*.80,.045,OAK_EDGE,.017)
        for i in range(4):
            y=(i-1.5)*d*.158
            bread=spheroid("Rustic loaf",x+rng.uniform(-.018,.018),y,.685,w*.101,d*.075,.052,BREAD)
            bread.rotation_euler.z=rng.uniform(-.14,.14)
            for n in range(-1,2):
                slash=box("Bread slash",x+n*.05,y,.734,.010,.036,.004,FLOUR,.002)
                slash.rotation_euler.z=-.3
        box("Bakery tag",x,-d*.405,.66,w*.16,.021,.075,OLIVE,.004)
    return 12


def picture(x, y, z, w, h, landscape=True):
    box("Screen casing", x,y,z,w,.043,h,SCREEN,.022)
    layer=y-.024
    box("Display image",x,layer,z,w-.044,.004,h-.044,SKY if landscape else SEA,.001)
    box("Display horizon",x,layer-.003,z-h*.21,w*.95,.004,h*.26,SEA if landscape else VIOLET,.002)
    for i in range(3):
        box("Interface band",x+(i-1)*w*.27,layer-.004,z+h*.27-i*.061,w*.18,.004,h*.025,IVORY,.001)
    box("Low mass pedestal",x,y,.94,w*.22,.22,.065,ALLOY)
    box("Vertical display foot",x,y,.94+(z-h*.5-.94)*.5,.067,.052,max(.03,z-h*.5-.94),BLACK)


def electronics(name, w, d, seed, _):
    # Compact exhibit island with two distinct demonstration bays, open backed to preserve sightlines.
    table(w*.92,d*.80,.90,IVORY,ALLOY)
    if name=="suvel_audio":
        picture(0, .26, 1.45, w*.34, .69)
        for x in [-w*.318,w*.318]:
            box("Bookshelf speaker",x,-d*.22,1.10,.335,.266,.40,BLUE,.028)
            for z,r in ((1.03,.094),(1.22,.045)):
                cone=cylinder("Speaker face",x,-d*.22-.141,z,r,.014,BLACK,verts=24)
                cone.rotation_euler.x=math.pi*.5
                dust=cylinder("Dust cap",x,-d*.22-.151,z,r*.34,.018,ALLOY,verts=20)
                dust.rotation_euler.x=math.pi*.5
        box("Brushed receiver",0,-d*.20,.96,.47,.26,.118,ALLOY)
        knob=cylinder("Receiver knob",.159,-d*.20-.147,.96,.04,.028,BLACK)
        knob.rotation_euler.x=math.pi/2
        return 4
    for k in (-1,1):
        x=k*w*.23
        picture(x,.166,1.36,w*.353,.61,landscape=k<0)
        box("Keyboard deck",x,-d*.22,.93,.51,.20,.05,BLUE)
        for i in range(9):
            for j in range(3):
                box("Keycap",x+(i-4)*.047,-d*.22+(j-1)*.052,.959,.038,.041,.008,IVORY,.002)
        box("Portable SSD sample",x+.38,-d*.23,.93,.113,.15,.047,VIOLET,.01)
    return 6


def terrace(name,w,d,seed,_):
    # Clean and repair tools are displayed on an apothecary-style low bench, not generic shelving.
    compact = name.endswith("_small")
    shift = -.18 if compact else 0
    table(w,d,.69 + shift,WALNUT,COPPER)
    box("Coopered shelf tray",0,0,.735 + shift,w*.83,d*.71,.084,PLASTER,.018)
    for i in range(4):
        x=(i-1.5)*w*.21
        cylinder("Studio ceramic",x,0,.822+shift+.04*(i%2),.10-(i%2)*.03,.18+.08*(i%2),CREAM if i%2 else GLAZED,.08,20)
        cylinder("Inset rim",x,0,.91+shift+.08*(i%2),.081,.025,WALNUT,.081)
    for k in range(2):
        p=box("Linen weave sample",w*.28,-d*.23,.791+shift+k*.021,w*.22,d*.31,.022,PLASTER if k==0 else CREAM,.007)
        p.rotation_euler.z=.05 if k==0 else -.05
    return 6


def save(name, fun, w, d, seed, arg=None):
    clear()
    count = fun(name,w,d,seed,arg)
    # Join like materials before exporting to keep each installation to one GLB mesh node.
    for obj in list(bpy.context.scene.objects):
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active=obj
        for mod in list(obj.modifiers):
            bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.object.select_all(action="SELECT")
    bpy.context.view_layer.objects.active=bpy.context.selected_objects[0]
    bpy.ops.object.join()
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    bpy.context.object.name=name
    bpy.ops.export_scene.gltf(filepath=str(DEST/f"{name}.glb"),export_format="GLB",export_yup=True)
    print("V34_ASSET",name,count)


for name, fn, w, d, seed, arg in [
    ("rivora_orchard_large",fruit,2.08,.84,11,(ORANGE,GREEN,RED)),
    ("rivora_orchard_small",fruit,1.72,.73,24,(GREEN,RED,ORANGE)),
    ("rivora_citrus",fruit,1.72,.73,83,(ORANGE,RED,ORANGE)),
    ("rivora_pantry",preserve,1.72,.73,99,None),
    ("rivora_bakery",bakery,1.72,.73,43,None),
    ("suvel_audio",electronics,4.35,3.15,46,None),
    ("suvel_photo",electronics,3.50,2.35,42,None),
    ("terrune_studio",terrace,1.70,.72,99,None),
    ("terrune_studio_small",terrace,1.08,.62,22,None),
]:
    requested = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not requested or name in requested:
        save(name,fn,w,d,seed,arg)
