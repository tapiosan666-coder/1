"""Original low-poly swept hair clumps; Blender authoring only, no runtime dependency."""
import bpy, math
from mathutils import Vector

def build(add, material, xyz):
    def mesh(name, points, faces, uvs):
        data=bpy.data.meshes.new(name)
        data.from_pydata([xyz(p) for p in points],[],faces);data.update()
        layer=data.uv_layers.new(name='HairFlow')
        for loop in data.loops:layer.data[loop.index].uv=uvs[loop.vertex_index]
        obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj)
        add(obj,material)

    # A smaller scalp is covered by shaped clumps, without a straight bowl-cut hem.
    points=[];faces=[];uvs=[];n=48;rows=12
    for j in range(rows+1):
        for i in range(n):
            phi=math.tau*i/n;t=j/rows
            theta=(1.68+.08*math.cos(phi)+.07*math.sin(phi*3))*t
            points.append((.110*math.sin(theta)*math.sin(phi),
                           1.744+.135*math.cos(theta)+.012*max(0,math.cos(theta))**4+(.008*math.sin(phi)+.005*math.sin(phi*5))*math.sin(theta)**2,
                           .008+.135*math.sin(theta)*math.cos(phi)))
            uvs.append((i/n,t))
    for j in range(rows):
        for i in range(n):
            a=j*n+i;b=j*n+(i+1)%n;faces.append((a+n,b+n,b,a))
    mesh('Covered scalp',points,faces,uvs)

    def tuft(name,controls,width,steps=9):
        controls=[Vector(p) for p in controls]
        def point(t):
            return controls[0]*(1-t)**3+controls[1]*(3*t*(1-t)**2)+controls[2]*(3*t*t*(1-t))+controls[3]*t**3
        vs=[];fs=[];uv=[]
        # Closed, shallow diamond sections produce continuous top and edge planes.
        for j in range(steps+1):
            t=j/steps;p=point(t)
            tangent=(point(min(1,t+.005))-point(max(0,t-.005))).normalized()
            normal=Vector((p.x/.105**2,(p.y-1.744)/.135**2,(p.z-.008)/.122**2)).normalized()
            side=tangent.cross(normal).normalized()
            if side.length<.1:side=Vector((1,0,0))
            normal=side.cross(tangent).normalized()
            w=width*(.07+.93*math.sin(math.pi*(t*.92+.04))**.65)*(1-t**8)
            w=max(.0004,w)
            for x,depth,u in [(-1,0,0),(0,w*.44,.5),(1,0,1),(0,-w*.24,.5)]:
                vs.append(p+side*(x*w)+normal*depth);uv.append((u,t))
        for j in range(steps):
            for k in range(4):
                a=j*4+k;b=j*4+(k+1)%4;fs.append((a,b,b+4,a+4))
        fs.extend([(3,2,1,0),tuple(steps*4+k for k in range(4))])
        mesh(name,vs,fs,uv)

    tips=[1.731,1.715,1.704,1.723,1.711,1.733,1.718,1.728,1.744]
    for i in range(9):
        x=-.086+i*.0215
        tuft('Swept fringe',[(x*.42,1.875,.018),(x+.020,1.902,-.047),
                            (x+.027,1.799,-.139),(x+.011,tips[i],-.139+abs(x)*.04)],.025+(i%3)*.0015)
    # Irregular temple and nape tips read in profile as well as front.
    for side in [-1,1]:
        for i in range(4):
            z=-.032+i*.038
            tuft('Temple layer',[(side*.075,1.843,.015+i*.016),
                 (side*.119,1.846,z+.015),(side*.135,1.782,z),
                 (side*(.119+(i%2)*.008),[1.721,1.706,1.698,1.714][i],z-.009)],.022)
    for i in range(5):
        x=-.076+i*.038
        tuft('Nape layer',[(x*.45,1.860,.068),(x*.90,1.862,.130),
             (x*1.2,1.764,.152),(x*1.15,1.691+abs(x)*.16,.127+(i%2)*.009)],.023)
    print('HAIR_CLUMPS 22, closed directional sections and preserved flow UVs',flush=True)
