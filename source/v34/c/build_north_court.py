"""Build original North Garden hardscape/planting. Blender: blender -b -t 2 -P source/v34/c/build_north_court.py"""
from collections import defaultdict
from math import cos, sin, pi
from pathlib import Path
from random import Random

import bpy
from mathutils import Vector

BASE = Path(__file__).resolve().parents[3]
rng = Random(340515)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
pieces = defaultdict(lambda: ([], [], []))

def base_colour(hex_code):
    def srgb(value):
        return value / 12.92 if value < .04045 else ((value + .055) / 1.055) ** 2.4
    return tuple(srgb(int(hex_code[i:i+2], 16)/255) for i in (0,2,4))

def face(material, points, color=None):
    coords, faces, colors = pieces[material]
    faces.append(tuple(range(len(coords), len(coords)+len(points))))
    coords.extend(points)
    colors.extend([color] * len(points))

def flat(material, ring, y, color=None, upward=True):
    order = ring[::-1] if upward else ring
    face(material, [(x, y, z) for x, z in order], color)

def round_rect(cx, cz, width, depth, radius, count=5):
    pts = []
    for x, z, quadrant in [(1,1,0),(-1,1,1),(-1,-1,2),(1,-1,3)]:
        for k in range(count+1):
            a=(quadrant+k/count)*pi/2
            pts.append((cx+x*(width/2-radius)+cos(a)*radius, cz+z*(depth/2-radius)+sin(a)*radius))
    return pts

def loft(material, levels, close=False, colour=None):
    for (old, bottom), (new, top) in zip(levels, levels[1:]):
        for i, (x,z) in enumerate(old):
            j=(i+1)%len(old)
            face(material, [(x,bottom,z),old[j][:1]+(bottom,)+old[j][1:],new[j][:1]+(top,)+new[j][1:],new[i][:1]+(top,)+new[i][1:]][::-1],colour)
    if close:
        flat(material, levels[-1][0], levels[-1][1], colour)

def slab(material, x, z, w, d, bottom, top, radius=.014, colour=None):
    bevel=min(.012, (top-bottom)*.35, w*.12, d*.12)
    outside=round_rect(x,z,w,d,radius,2)
    inset=round_rect(x,z,w-2*bevel,d-2*bevel,max(radius-bevel, .001),2)
    loft(material, [(inset,bottom),(outside,bottom+bevel),(outside,top-bevel),(inset,top)],True,colour)

def tube(material, p, q, radius, end_radius, sides=7, colour=None):
    p,q = Vector(p),Vector(q)
    up=(q-p).normalized()
    cross=up.cross(Vector((0,0,1)))
    if cross.length < .1:
        cross=up.cross(Vector((1,0,0)))
    cross.normalize()
    ray=up.cross(cross).normalized()
    old=[]; new=[]
    for j in range(sides):
        a=j*2*pi/sides
        direction=cross*cos(a)+ray*sin(a)
        old.append(p+direction*radius)
        new.append(q+direction*end_radius)
    for j in range(sides):
        k=(j+1)%sides
        face(material,[old[j],old[k],new[k],new[j]],colour)

def leaf(root, length, width, azimuth, lift, material, color):
    root=Vector(root)
    forward=Vector((cos(azimuth), lift, sin(azimuth))).normalized()
    side=Vector((-sin(azimuth),0,cos(azimuth)))
    flare=root+forward*length*.45
    end=root+forward*length
    # The folded midrib catches a second tone in direct sunlight.
    spine=flare+Vector((0,1,0))*width*.17
    left=flare+side*width*.5
    right=flare-side*width*.5
    face(material,[root,left,spine],color)
    face(material,[left,end,spine],color)
    darker=tuple(v*.84 for v in color)
    face(material,[root,spine,right],darker)
    face(material,[right,spine,end],darker)

def tree(x, z, height, autumn=False):
    base=Vector((x,.45,z))
    fork=base+Vector((-.08,height*.38,.08))
    middle=base+Vector((.16,height*.69,.1))
    top=base+Vector((.06,height,-.08))
    tube("bark",base,fork,.115,.082,12)
    tube("bark",fork,middle,.082,.041,11)
    tube("bark",middle,top,.042,.009,9)
    greens=list(map(base_colour,["4d6e34","6f8740","7b934c","8c9b50","5f792d","93ae5b","597735","a6ab54"]))
    if autumn:
        greens=list(map(base_colour,["867b3f","926733","ac7739","ad8548","c69453","9c633a","926340","a6a052"]))
    for j in range(24):
        rhythm=j*.381966*2*pi
        along=.2+j*.031
        stem=fork.lerp(top,along)
        span=(.85+.43*sin(j/24*pi))*rng.uniform(.75,1.16)
        if j>16:
            span*=1.-(j-16)*.073
        elbow=stem+Vector((cos(rhythm)*span*.52,rng.uniform(.13,.28),sin(rhythm)*span*.52))
        tip=stem+Vector((cos(rhythm)*span,rng.uniform(.32,.54),sin(rhythm)*span))
        tube("bark",stem,elbow,.033*(1.-j/31),.014,7)
        tube("bark",elbow,tip,.015,.004,6)
        for k in range(4):
            a=rhythm+(-1 if k%2 else 1)*rng.uniform(.58,1.27)
            bud=elbow.lerp(tip,.11+k*.255)
            endpoint=bud+Vector((cos(a)*rng.uniform(.17,.5),rng.uniform(.08,.25),sin(a)*rng.uniform(.17,.5)))
            tube("bark",bud,endpoint,.0065,.0023,5)
            for l in range(13):
                angle=a+l*2.39996
                center=bud.lerp(endpoint,rng.uniform(.42,1.11))+Vector((rng.uniform(-.16,.16),rng.uniform(-.09,.14),rng.uniform(-.17,.17)))
                amount=rng.uniform(.14,.29)
                leaf(center,amount,amount*.7,angle,rng.uniform(-.36,.4),"leaves",rng.choice(greens))
        for k in range(7):
            leaf(tip+rng.uniform(0,.3)*Vector((cos(k),.4,sin(k))),rng.uniform(.16,.27),.15,rhythm+k*.9,.14,"leaves",rng.choice(greens))

def tuft(x,z,scale,flowers=False):
    olive=list(map(base_colour,["667f36","415b2e","728447","516930","798459","4c6737"]))
    if flowers:
        pollen=base_colour("d0aa79")
        tones=list(map(base_colour,["897eaa","9b88b7","c2999e","c5a9ce","7f638a"]))
        for k in range(16):
            a=k*2.399963
            reach=rng.uniform(.04,.23)*scale
            height=rng.uniform(.26,.57)*scale
            root=Vector((x+cos(a)*reach*.35,.434,z+sin(a)*reach*.35))
            end=root+Vector((cos(a)*reach,height,sin(a)*reach))
            tube("plant",root,end,.0065,.0035,5,rng.choice(olive))
            for j in range(2):
                leaf(root.lerp(end,.30+j*.31),.18*scale,.075*scale,a+j*2.6,.17,"plant",rng.choice(olive))
            for petal in range(5):
                leaf(end,.041*scale,.037*scale, petal*2*pi/5,.04,"flowers",rng.choice(tones))
            tube("flowers",end,end+Vector((0,.011,0)),.014*scale,.009*scale,5,pollen)
    else:
        for k in range(28):
            a=k*2.399963+rng.uniform(-.14,.14)
            reach=rng.uniform(.22,.42)*scale
            height=rng.uniform(.28,.49)*scale
            width=rng.uniform(.016,.037)*scale
            foot=Vector((x+cos(a)*.032,.43,z+sin(a)*.032))
            middle=foot+Vector((cos(a)*reach*.38,height*.83,sin(a)*reach*.38))
            end=foot+Vector((cos(a)*reach,height*.75,sin(a)*reach))
            side=Vector((-sin(a),0,cos(a)))*width
            c=rng.choice(olive)
            face("plant",[foot,middle-side,middle+side],c)
            face("plant",[middle-side,end,middle+side],c)

def groundcover(cx,cz,w,d):
    shades=list(map(base_colour,["465d30","566f43","546d39","657647","779158"]))
    for i in range(int(w*d*19)):
        x=rng.uniform(-w/2+.22,w/2-.22)
        z=rng.uniform(-d/2+.17,d/2-.17)
        if (abs(x)>w/2-.55 and abs(z)>d/2-.28) or rng.random()<.1:
            continue
        c=Vector((cx+x, .443+rng.uniform(0,.045), cz+z))
        for j in range(6):
            leaf(c, rng.uniform(.12,.23),.049,j*pi/3+rng.uniform(-.2,.2),rng.uniform(.16,.42),"plant",rng.choice(shades))

def planter(cx, cz, w, d, wood_side, amber, tufts):
    make=lambda dw,dd,rr:round_rect(cx,cz,w+dw,d+dd,rr,9)
    loft("kerb",[(make(-.15,-.15,.63),.009),(make(-.12,-.12,.67),.07),(make(-.05,-.05,.70),.093),(make(0,0,.72),.43)])
    outer=make(.027,.027,.74)
    top_inner=make(-.20,-.20,.63)
    # A honed closed cap returns down on the inner face of the planter.
    loft("coping",[(make(0,0,.72),.43),(outer,.45),(outer,.49),(make(-.01,-.01,.72),.507),(top_inner,.507),(top_inner,.441)])
    flat("earth",top_inner,.441)
    groundcover(cx,cz,w-.23,d-.27)
    tree(cx+w*.20,cz-.08,2.5 if amber else 2.74,amber)
    for x,z,s,flower in tufts:
        tuft(cx+x,cz+z,s,flower)
    bench_z=cz+wood_side*(d/2+.22)
    bench_w=w-1.18
    for j in range(5):
        zz=bench_z+(.10*j-.2)
        c=tuple(c*rng.uniform(.93,1.08) for c in base_colour("976842"))
        slab("seat",cx,zz,bench_w,.084,.443,.493,.032,c)
    for x in [-bench_w*.36,bench_w*.36]:
        slab("steel",cx+x,bench_z,.16,.41,.055,.445,.025)
        slab("steel",cx+x,bench_z,.24,.33,.016,.057,.025)
    # A central grab rail splits the long seat, leaving outer space open.
    p=(cx,.484,bench_z-wood_side*.158)
    q=(cx,.665,bench_z-wood_side*.158)
    r=(cx,.665,bench_z+wood_side*.132)
    s=(cx,.484,bench_z+wood_side*.132)
    for a,b in [(p,q),(q,r),(r,s)]:
        tube("steel",a,b,.022,.022,10)

def pave():
    palette=list(map(base_colour,["adab9e","b3b0a2","b6b2a4","a9a699","bebaaa","b9b5a7"]))
    # Insets end before the storefront routes and leave the original surface and collision intact.
    xb,xe,zb,ze=-6.5,10.6,7.58,12.78
    flat("joints",[(xb,zb),(xe,zb),(xe,ze),(xb,ze)],.027)
    for line in range(10):
        z=zb+.52*line
        x=xb-.71*(line%2)
        while x<xe:
            a=max(x,xb)+.007
            b=min(x+1.43,xe)-.007
            if a<b:
                flat("paving",[(a,z+.007),(b,z+.007),(b,z+.513),(a,z+.513)],.0305,rng.choice(palette))
            x+=1.43
    for edge in [zb+.02,ze-.048]:
        flat("steel",[(xb,edge),(xe,edge),(xe,edge+.029),(xb,edge+.029)],.0315)

pave()
planter(-2.75,9.04,5.75,2.0,1,False,[(-1.92,.0,1.0,True),(-.7,.54,.9,False),( .63,-.52,.83,False),(1.76,.46,.91,True),(-1.2,-.50,1.0,False)])
planter(6.60,10.81,6.13,2.16,-1,True,[(-2.12,.28,1.13,False),(-1.1,-.55,1.05,True),(.17,.54,.96,True),(1.95,.07,1.05,False),(2.2,-.34,.95,True)])

specs={
    "kerb":("a3a092",.80,0), "coping":("c6c1af",.58,0), "earth":("3b3729",.98,0),
    "bark":("6f5949",.9,0), "leaves":("ffffff",.78,0), "plant":("ffffff",.88,0),
    "flowers":("ffffff",.64,0), "seat":("ffffff",.50,0), "steel":("50534a",.55,.55),
    "paving":("ffffff",.83,0), "joints":("514f45",.92,0),
}
materials=[]
for label,(hex_code,roughness,metal) in specs.items():
    mat=bpy.data.materials.new("NorthGarden_" + label)
    mat.use_nodes=True
    pbr=mat.node_tree.nodes.get("Principled BSDF")
    pbr.inputs["Base Color"].default_value=(*base_colour(hex_code),1)
    pbr.inputs["Metallic"].default_value=metal
    pbr.inputs["Roughness"].default_value=roughness
    if hex_code=="ffffff":
        colors=mat.node_tree.nodes.new("ShaderNodeVertexColor")
        colors.layer_name="Tints"
        mat.node_tree.links.new(colors.outputs["Color"],pbr.inputs["Base Color"])
    mat.use_backface_culling=label not in {"leaves","plant","flowers"}
    materials.append(mat)
    points,faces,colours=pieces[label]
    mesh=bpy.data.meshes.new(label)
    # Blender Z-up and glTF Y-up. Keep local world-facing Z direction intact.
    mesh.from_pydata([(x,-z,y) for x,y,z in points], [],faces)
    mesh.validate()
    mesh.update()
    # Lathed hardscape and bark share continuous normals around surfaces.
    if label=="bark":
        for polygon in mesh.polygons:
            polygon.use_smooth=True
    if hex_code=="ffffff":
        attr=mesh.color_attributes.new(name="Tints",type="FLOAT_COLOR",domain="POINT")
        for datum,colour in zip(attr.data,colours):
            datum.color=(*(colour or (.5,.5,.5)),1)
    object=bpy.data.objects.new("North Garden / "+label,mesh)
    object.data.materials.append(mat)
    bpy.context.scene.collection.objects.link(object)
    object.select_set(True)

export = BASE/"assets/v34/c/north_court.glb"
bpy.ops.export_scene.gltf(filepath=str(export), export_format="GLB", export_yup=True, export_apply=True, export_vertex_color="ACTIVE")
print("NORTH_GARDEN_EXPORT",export, sum(len(p[1]) for p in pieces.values()))
