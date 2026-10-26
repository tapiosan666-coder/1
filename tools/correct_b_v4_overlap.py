"""Design-only v4.1 correction. Never modifies approved sources or any Godot resource."""
from pathlib import Path
import sys,json,copy,hashlib,csv,math
sys.path.append('/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
import shapely
from shapely.geometry import shape,mapping,Point,LineString,Polygon
from shapely.ops import unary_union
R=Path(__file__).resolve().parents[1];B=R/'docs/b-purpose-review-v4';O=R/'docs/b-v4-overlap-correction';O.mkdir(exist_ok=True)
old=json.loads((B/'geometry.json').read_text());new=copy.deepcopy(old);EPS=1e-8
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def polygons(g):return[]if g.is_empty else[g]if g.geom_type=='Polygon'else[p for p in getattr(g,'geoms',[])if p.geom_type=='Polygon']
changes=[];metrics=[];components=[];additions=[];patch=[]
for before,after in zip(old['floors'],new['floors']):
 level=before['floor'];pub=shape(before['public']);void=shape(before['void']);shafts=shape(before['shafts']);res=shape(before['residual']);plate=shape(before['floor_plate'])
 obstacles={'public':pub,'void':void,'shafts':shafts,'stores':unary_union([shape(s['polygon'])for s in before['stores']]),'cores':unary_union([shape(c['outline'])for c in old['cores']])}
 # Exact overlay in the serialized input coordinates: do not set a new precision grid or buffer the clear floor.
 forbidden=unary_union(list(obstacles.values()));trimmed=res.difference(forbidden);cutplate=plate.union(pub).difference(void.union(shafts))
 assert trimmed.is_valid and cutplate.is_valid
 assert trimmed.difference(res).area<EPS and cutplate.difference(plate).difference(pub).area<EPS
 for key,result,original in [('residual',trimmed,res),('floor_plate',cutplate,plate)]:
  after[key]=mapping(result);removed=original.difference(result);added=result.difference(original)
  assert removed.difference(forbidden if key=='residual'else void.union(shafts)).area<EPS
  assert added.difference(pub).area<EPS
  patch.append({'op':'replace','path':f"/floors/{level-1}/{key}",'value':mapping(result)})
  changes.append({'floor':level,'field':key,'before_area_m2':original.area,'after_area_m2':result.area,'removed_area_m2':removed.area,'added_area_m2':result.difference(original).area,'removed_geometry':mapping(removed),'added_geometry':mapping(added)})
  for i,p in enumerate(polygons(removed),1):
   components.append({'id':f'F{level}-{key}-{i:03}','floor':level,'field':key,'area_m2':p.area,'bounds_local':list(p.bounds),'bounds_world':[p.bounds[0]-714,p.bounds[1]-30,p.bounds[2]-714,p.bounds[3]-30],'geometry':mapping(p)})
  for i,p in enumerate(polygons(added),1):
   additions.append({'id':f'F{level}-{key}-ADD-{i:03}','floor':level,'field':key,'area_m2':p.area,'bounds_local':list(p.bounds),'geometry':mapping(p)})
 metrics.append({'floor':level,'store_count':len(before['stores']),'residual_public_before_m2':res.intersection(pub).area,'residual_public_after_m2':trimmed.intersection(pub).area,'residual_forbidden_before_m2':res.intersection(forbidden).area,'residual_forbidden_after_m2':trimmed.intersection(forbidden).area,'residual_removed_m2':res.difference(trimmed).area,'floor_plate_void_before_m2':plate.intersection(void).area,'floor_plate_void_after_m2':cutplate.intersection(void).area,'floor_plate_shaft_before_m2':plate.intersection(shafts).area,'floor_plate_shaft_after_m2':cutplate.intersection(shafts).area,'floor_plate_removed_m2':plate.difference(cutplate).area,'floor_plate_added_m2':cutplate.difference(plate).area,'public_without_plate_before_m2':pub.difference(plate).area,'public_without_plate_after_m2':pub.difference(cutplate).area,'residual_against_before':{k:res.intersection(v).area for k,v in obstacles.items()},'residual_against_after':{k:trimmed.intersection(v).area for k,v in obstacles.items()}})
 # All fields except the two explicitly corrected polygons must stay identical, not just have similar bounds.
 assert {k:v for k,v in before.items()if k not in['residual','floor_plate']}=={k:v for k,v in after.items()if k not in['residual','floor_plate']}
assert {k:v for k,v in old.items()if k!='floors'}=={k:v for k,v in new.items()if k!='floors'}
(O/'geometry.json').write_text(json.dumps(new,ensure_ascii=False,indent=2))
# Re-read delivered JSON; check actual delivered geometry rather than un-serialized in-memory results.
delivered=json.loads((O/'geometry.json').read_text())
for f in delivered['floors']:
 for other in['public','void','shafts']:assert shape(f['residual']).intersection(shape(f[other])).area<EPS
 assert shape(f['floor_plate']).intersection(shape(f['void']).union(shape(f['shafts']))).area<EPS
(O/'geometry.patch.json').write_text(json.dumps(patch,ensure_ascii=False,indent=2))
(O/'changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2));(O/'removed-components.geojson').write_text(json.dumps({'type':'FeatureCollection','name':'B_v4_1_removed_slivers_local_XZ_metres','features':[{'type':'Feature','geometry':c['geometry'],'properties':{k:v for k,v in c.items()if k!='geometry'}}for c in components]},ensure_ascii=False,indent=2))
(O/'added-components.geojson').write_text(json.dumps({'type':'FeatureCollection','name':'B_v4_1_added_slab_local_XZ_metres','features':[{'type':'Feature','geometry':c['geometry'],'properties':{k:v for k,v in c.items()if k!='geometry'}}for c in additions]},ensure_ascii=False,indent=2))
with(O/'added-components.csv').open('w',encoding='utf-8-sig',newline='')as fp:
 w=csv.writer(fp);w.writerow(['局所ID','階','対象','補完面積㎡','Local xmin','Local zmin','Local xmax','Local zmax'])
 for c in additions:w.writerow([c['id'],c['floor'],c['field'],c['area_m2'],*c['bounds_local']])
(O/'comparison.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2))
with(O/'comparison.csv').open('w',encoding='utf-8-sig',newline='')as fp:
 w=csv.writer(fp);w.writerow(['階','店舗数','共用床/閉鎖帯_前㎡','共用床/閉鎖帯_後㎡','閉鎖帯全削除㎡','床板/機械開口_前㎡','床板/機械開口_後㎡','公開床下の床板欠け_前㎡','公開床下の床板欠け_後㎡','床板補完㎡','変更フィールド'])
 for m in metrics:w.writerow([m['floor'],m['store_count'],m['residual_public_before_m2'],m['residual_public_after_m2'],m['residual_removed_m2'],m['floor_plate_shaft_before_m2'],m['floor_plate_shaft_after_m2'],m['public_without_plate_before_m2'],m['public_without_plate_after_m2'],m['floor_plate_added_m2'],'residual / floor_plate'])
with(O/'removed-components.csv').open('w',encoding='utf-8-sig',newline='')as fp:
 w=csv.writer(fp);w.writerow(['局所ID','階','対象フィールド','削除面積㎡','Local xmin','Local zmin','Local xmax','Local zmax','World xmin','World zmin','World xmax','World zmax'])
 for c in components:w.writerow([c['id'],c['floor'],c['field'],c['area_m2'],*c['bounds_local'],*c['bounds_world']])
(O/'revision.json').write_text(json.dumps({'revision':'B-v4.1-overlap-correction','design_only':True,'game_implemented':False,'source_commit':'38a6391c4383fc7a91f3dc4b8fa570208d8996f9','source_geometry_sha256':sha(B/'geometry.json'),'corrected_geometry_sha256':sha(O/'geometry.json'),'changed_fields':['floors/0/residual','floors/0/floor_plate','floors/1/residual','floors/1/floor_plate','floors/2/residual','floors/2/floor_plate'],'method':'Serialized source coordinates, difference overlay without snapping, global offsets, buffering, or runtime auto-correction. Public, shops, court, openings and routes unchanged. Slab micro-gaps filled only under existing public floor.','numerical_area_epsilon_m2':EPS,'python':sys.version.split()[0],'shapely':shapely.__version__,'geos':shapely.geos_version_string,'original_internal_version_field_retained':True,'rendered_3d_views_regenerated':False},ensure_ascii=False,indent=2))
print(json.dumps(metrics,ensure_ascii=False,indent=2))
