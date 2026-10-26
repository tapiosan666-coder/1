"""Independent measurement of shipped collision triangles against frozen site-v3 floor polygons."""
from pathlib import Path
import sys,json,hashlib,math
sys.path.append('/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
from shapely.geometry import shape,box,Polygon
from shapely.ops import unary_union
P=Path(__file__).resolve().parents[1];R=Path('/workspace/1');m=json.load(open(P/'source/scene-manifest.json'));d=json.load(open(R/'docs/site-correction-v3/geometry.json'));g=json.load(open(P/'assets/geometry.json'))
checks=[]
def check(id,condition,**detail):checks.append({'id':id,'pass':bool(condition),**detail})
check('frozen-source-sha256',hashlib.sha256((R/'docs/site-correction-v3/geometry.json').read_bytes()).hexdigest()==m['source_sha256'])
old=json.load(open(P/'source/protected-originals.json'));changed=[p for p,h in old.items() if not (R/p).exists()or hashlib.sha256((R/p).read_bytes()).hexdigest()!=h]
check('all-original-tracked-files-unchanged',not changed,files=len(old),changed=changed)
raw=g['colliders']['stone'];triangles=[raw[i:i+9]for i in range(0,len(raw),9)]
for lev,y in[(0,0),(1,5.525),(2,10.875)]:
 f=next(f for f in d['floors']if f['wing']=='B'and f['level']==lev);orig=shape(f['floor_plate']).intersection(box(*m['crop_world_xz']))
 additions=[shape(x['polygon'])for x in m.get('isolated_slab_additions',[])if x['level']==lev]
 original_area=orig.area;orig=unary_union([orig,*additions])
 ts=[]
 for t in triangles:
  if max(abs(t[i]-y)for i in[1,4,7])<1e-5:
   pts=[(t[i]+m['world_origin_xz'][0],t[i+2]+m['world_origin_xz'][1])for i in[0,3,6]];ts.append(Polygon(pts))
 built=unary_union(ts);xor=orig.symmetric_difference(built).area;overlap=sum(t.area for t in ts)-built.area
 check(f'{lev}-slab-collider-vs-original-footprint',xor<.001,source_original_m2=original_area,isolated_scene_with_departure_underfloor_m2=orig.area,mesh_union_m2=built.area,symmetric_difference_m2=xor,tolerance_m2=.001,triangles=len(ts))
 check(f'{lev}-slab-no-duplicate-overlapping-triangles',overlap<.000001,overlap_m2=overlap)
 # 3D source plate already excludes actual atrium void/shafts, except bridges.
 void=shape(f['void']);check(f'{lev}-no-collider-in-designed-void',built.intersection(void).area<.01,intersection_m2=built.intersection(void).area)
for s in m['shops']:
 check(s['id']+'-clear-opening-dimension',s['clear_width_m']>=1.2,width_m=s['clear_width_m'])
check('3D-generated-route-targets-no-unreachable-fallback',not m['routing_failures'],unreachable=m['routing_failures'])
walk_path=P/'evidence/walk-results.json'
if walk_path.exists():
 w=json.load(open(walk_path));check('runtime-uses-shipped-geometry',w.get('geometry_sha256')==hashlib.sha256((P/'assets/geometry.json').read_bytes()).hexdigest());check('runtime-uses-shipped-main-script',w.get('main_script_sha256')==hashlib.sha256((P/'main.gd').read_bytes()).hexdigest());check('runtime-uses-shipped-player-script',w.get('player_script_sha256')==hashlib.sha256((P/'player.gd').read_bytes()).hexdigest());check('runtime-tests-finished',w['total']>80,total=w['total']);check('runtime-tests-no-failure',w['failed']==0,passed=w['passed'],failed=w['failed'])
result={'kind':'independent frozen-original vs generated 3D collider geometry check','checks':checks,'total':len(checks),'passed':sum(c['pass']for c in checks),'failed':sum(not c['pass']for c in checks),'tolerance_note':'頂点は小数点5桁mで出力。面積許容0.001㎡は切出し全床の境界量子化差。設計原本は変更しない。'}
(P/'evidence/geometry-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({k:result[k]for k in['total','passed','failed']},ensure_ascii=False))
for c in checks:
 if not c['pass']:print(c)
