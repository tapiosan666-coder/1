"""Original ground-supported water/deck composition, independent of the C roof. No borrowed architectural assets."""
from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from v22_blender_common import *
from mathutils.geometry import tessellate_polygon
concrete=material('Landmark_warm_limestone',(.78,.77,.72),.70,texture='assets/v10/materials/paving-albedo.webp');waterbed=material('Landmark_reflection_basin',(.11,.19,.18),.48);gl=material('Landmark_laminated_guard',(.72,.86,.84),.10);nd=gl.node_tree.nodes.get('Principled BSDF');nd.inputs['Transmission Weight'].default_value=.8;nd.inputs['Alpha'].default_value=.15;gl.surface_render_method='DITHERED'
def outline(offset=0):
 out=[]
 for i in range(128):
  t=math.tau*i/128;r=1+.12*math.cos(3*t+.4)+.065*math.sin(2*t);out.append(((11*r+offset)*math.cos(t),(17*r+offset)*math.sin(t)))
 return out
def slab(name,loop,z,h,mat):
 n=len(loop);v=[(x,y,z)for x,y in loop]+[(x,y,z+h)for x,y in loop];top=tessellate_polygon([[Vector((x,y,z+h))for x,y in loop]]);index={(round(x,7),round(y,7)):i for i,(x,y)in enumerate(loop)};faces=[]
 for tri in top:faces.append(tuple(n+(p if isinstance(p,int)else min(range(len(loop)),key=lambda k:(loop[k][0]-p.x)**2+(loop[k][1]-p.y)**2))for p in tri))
 faces+=[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)];return mesh(name,v,faces,mat,[(q[0]*.45,q[1]*.45)for q in v])
# Ground finish stops at the actual basin outline; no opaque pavement crosses the water.
slab('Ground_foundation',[(23*math.cos(math.tau*i/128),26*math.sin(math.tau*i/128))for i in range(128)],-.42,.12,concrete)
inner=outline(0);outer=[(23*math.cos(math.tau*i/128),26*math.sin(math.tau*i/128))for i in range(128)];vv=[(x,y,0.)for x,y in inner+outer];mesh('Public_plaza_annulus',vv,[(i,(i+1)%128,(i+1)%128+128,i+128)for i in range(128)],concrete,[(x*.45,y*.45)for x,y,z in vv])
# Boardwalk is a true annular surface with an open central basin, not an opaque slab covering the water.
a=outline(0);b=outline(3.3);n=len(a);v=[(x,y,.18)for x,y in a]+[(x,y,.18)for x,y in b];mesh('Curved_public_boardwalk',v,[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)],wood,[(i*.38,0.)for i in range(n)]+[(i*.38,3.3)for i in range(n)])
slab('Shallow_basin',a,-.12,.10,waterbed)
# Continuous coping follows the same metric reference curve as the safety barrier.
for i in range(n):
 p=a[i];q=a[(i+1)%n];tube('Stone_coping',[(p[0],p[1],.20),(q[0],q[1],.20)],.065,concrete)
 if i%4==0:
  x,y=p;tube('Guard_post',[(x,y,.20),(x,y,1.35)],.025,steel)
 # Laminated panels, metal shoe, continuous top cap.
 mesh('Glass_guard',[(p[0],p[1],.28),(q[0],q[1],.28),(q[0],q[1],1.28),(p[0],p[1],1.28)],[(0,1,2,3)],gl)
tube('Continuous_guard_cap',[(x,y,1.33)for x,y in a+[a[0]]],.022,steel)
# Public paths join the boardwalk at three broad, shallow ramps (no stairs needed).
for angle in [-math.pi/2,.55,2.65]:
 d=Vector((math.cos(angle),math.sin(angle),0));u=Vector((-d.y,d.x,0));r=1+.12*math.cos(3*angle+.4)+.065*math.sin(2*angle);near=Vector(((11*r+3.3)*math.cos(angle),(17*r+3.3)*math.sin(angle),0))-d*.25;far=near+d*4;vv=[near-u*2+Vector((0,0,.18)),near+u*2+Vector((0,0,.18)),far+u*2,far-u*2];mesh('Accessible_approach',vv,[(0,1,2,3)],concrete)
# Separate curved viewing bays and purpose-built seating.
for j,angle in enumerate([-.25,1.2,2.5,3.8,5.1]):
 r=20.;x,y=r*math.cos(angle),r*math.sin(angle);u=Vector((-math.sin(angle),math.cos(angle),0));centre=Vector((x,y,.05))
 for k in range(7):
  p=centre+Vector((math.cos(angle),math.sin(angle),0))*(k*.065-.20);o=box('Bench_oak_slat',(p.x,p.y,.48),(2.35,.052,.045),wood,.007);o.rotation_euler.z=angle+math.pi/2
 for side in [-.8,.8]:
  p=centre+u*side;box('Bench_cast_support',(p.x,p.y,.23),(.12,.48,.46),metal,.015)
# Planting curbs define real tree pits, not trunks sprouting from an unbroken plaza finish.
soil=material('Landmark_planting_soil',(.075,.065,.035),.97)
for ang in [.35,2.45,4.65]:
 x,y=21*math.cos(ang),21*math.sin(ang);lathe('Planter_curved_rim',[(.85,0),(.97,0),(.97,.36),(.91,.40),(.84,.36),(.85,0)],concrete,(x,y,0),48);lathe('Tree_pit_soil',[(0,.30),(.85,.30),(.85,.31),(0,.31)],soil,(x,y,0),40)
# Three slender shade masts with shaped ribs and a porous timber canopy, leaving the basin open to the sky.
for j,ang in enumerate([.35,2.45,4.65]):
 x,y=19*math.cos(ang),19*math.sin(ang);tube('Mast',[(x,y,0),(x-.25,y,4.2)],.085,steel)
 for side in [-1,1]:
  points=[(x-.25+side*t*.9,y-t*.12,4.2+.12*math.sin(math.pi*t/4))for t in [0,1,2,3,4]];tube('Canopy_rib',points,.035,steel)
 for i in range(13):
  dx=(i-6)*.48;box('Open_canopy_slat',(x+dx,y,4.24),(.12,2.4,.065),wood,.009)
finish('water_landmark_structure')
(P/'source/v22/water-landmark-design.json').write_text(json.dumps({'status':'INDEPENDENT_DESIGN_SCENE_ONLY','roof_integration':False,'original_design':True,'water_depth_m':.10,'approx_basin_m2':math.pi*11*17,'minimum_water_dead_load_kPa':.981,'additional_glass_finish_live_loads':'NOT_ENGINEERED','structural_capacity_foundation_drainage_waterproofing_egress':'UNVERIFIED','basin_outline_xy':a,'public_boardwalk_width_m':3.3,'glass_guard_height_m':1.15,'walkability_tested':False},ensure_ascii=False,indent=2))
