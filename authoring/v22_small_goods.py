from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from v22_blender_common import *
B=json.loads((P/'source/v22/model-bounds.json').read_text());C=json.loads((P/'source/v22/product-catalog.json').read_text());green=material('Herb_leaf',(.14,.32,.075),.72);clay=material('Terracotta',(.46,.21,.105),.81);soil=material('Potting_mix',(.055,.041,.02),.96);sage=material('Garden_enamel',(.16,.31,.25),.40,.30);ink=material('Journal_ink',(.09,.20,.23),.72)
def done(name,role):
 bpy.context.view_layer.update();pts=[o.matrix_world@Vector(c)for o in bpy.context.scene.objects for c in o.bound_box];lo=[min(p[i]for p in pts)for i in range(3)];hi=[max(p[i]for p in pts)for i in range(3)];B[name]={'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]]};C[name]={'role':role,'provenance':'Original Blender v22 small merchandise geometry'};finish(name)
lathe('Rimmed_herb_pot',[(.060,0),(.075,.012),(.095,.14),(.105,.15),(.105,.17),(.085,.17),(.083,.15)],clay,steps=32);lathe('Soil',[(0,.155),(.083,.155)],soil,steps=24)
for j in range(12):
 a=math.tau*j/12;length=.15+.055*math.sin(j*3.1);root=Vector((math.cos(a)*.025,math.sin(a)*.025,.16));tip=root+Vector((math.cos(a)*length*.65,math.sin(a)*length*.65,length));tube('Herb_stalk',[root,root+Vector((0,0,.05)),tip],.003,green);u=Vector((-math.sin(a),math.cos(a),0));mid=root.lerp(tip,.6);verts=[root,mid+u*.025,tip,mid-u*.025,mid+Vector((0,0,.010))];mesh('Curved_herb_leaf',verts,[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],green)
done('sku_herb_plant','Potted herbs')
lathe('Watering_can_body',[(0,0),(.075,0),(.09,.025),(.09,.15),(.075,.17),(.04,.17),(.04,.16)],sage,steps=32);tube('Curved_handle',[(-.06,.03,.14),(-.16,.03,.20),(-.18,.03,.08),(-.08,.03,.045)],.009,sage);tube('Spout',[(.075,0,.025),(.13,0,.10),(.21,0,.18)],.014,sage);lathe('Watering_rose',[(0,0),(.026,0),(.026,.010),(0,.010)],sage,(.21,0,.18),24);done('sku_watering_can','Gardening tools')
lathe('Timber_handle',[(0,0),(.018,0),(.021,.11),(.016,.14),(0,.15)],wood,steps=20);mesh('Stainless_trowel',[(0,-.008,.33),(-.037,-.004,.24),(-.03,0,.15),(.03,0,.15),(.037,-.004,.24),(0,.009,.22)],[(0,1,5),(1,2,5),(2,3,5),(3,4,5),(4,0,5)],steel);done('sku_garden_trowel','Gardening hand tools')
box('Notebook_page_block',(0,0,.10),(.14,.025,.20),paper,.002);box('Front_cover',(0,-.015,.10),(.147,.004,.208),ink,.001);box('Back_cover',(0,.015,.10),(.147,.004,.208),ink,.001);tube('Elastic',[(.05,-.018,0),(.05,-.018,.20)],.0015,rubber)
for y in [.05,.10,.15]:box('Ruled_note_detail',(0,-.018,y),(.09,.002,.001),white,.0002)
done('sku_notebook','Stationery notebook')
lathe('Pen_stand',[(0,0),(.037,0),(.041,.07),(.034,.07),(.032,.005)],steel,steps=24)
for j in range(5):
 a=j*math.tau/5;x,y=math.cos(a)*.018,math.sin(a)*.018;lathe('Pen',[(0,0),(.003,.015),(.004,.14),(.005,.15),(.004,.17),(0,.17)],fabrics[j],(x,y,.015),12)
done('sku_pen_set','Stationery writing instruments')
(P/'source/v22/model-bounds.json').write_text(json.dumps(B,indent=2));(P/'source/v22/product-catalog.json').write_text(json.dumps(C,indent=2))
