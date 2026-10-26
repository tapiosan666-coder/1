"""Read-only C-wing area reconciliation. Creates new audit polygons/docs, never changes v1 geometry."""
from pathlib import Path
import sys,json,csv,hashlib,collections,math
sys.path.append('/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
import shapely
from shapely.geometry import shape,mapping,Polygon,Point,LineString,box
from shapely.ops import unary_union
R=Path(__file__).resolve().parents[1];B=R/'docs/c-detailed-design-v1';O=R/'docs/c-area-audit-v2';O.mkdir(exist_ok=True);EPS=1e-8
source_path=B/'geometry.json';source_bytes=source_path.read_bytes();SOURCE_SHA=hashlib.sha256(source_bytes).hexdigest();RAW=json.loads(source_bytes)
def dec(v):
 if isinstance(v,dict):return shapely.set_precision(shape(v),1e-12)if'type'in v and('coordinates'in v or'geometries'in v)else{k:dec(x)for k,x in v.items()}
 if isinstance(v,list):return[dec(x)for x in v]
 return v
D=dec(RAW)
def enc(v):
 if hasattr(v,'geom_type'):return mapping(v)
 raise TypeError(type(v))
def polys(g):return[]if g.is_empty else[g]if g.geom_type=='Polygon'else[p for p in getattr(g,'geoms',[])if p.geom_type=='Polygon']
CHECKS=[]
def ck(kind,id,ok,value=None,level=None):CHECKS.append(dict(kind=kind,id=id,pass_=bool(ok),value=value,level=level))
CATALOG=[
 ('A01','階段・EV・機械開口','床として数えない開口。6棟内の階段/EVと、棟外のエスカレーター開口/機器間を含む。',(.94,.90,.87)),
 ('A02','専用バックルーム','店舗/施設区画内。店舗区画面積へ内包されるため店舗総面積と重複加算しない。',(.83,.59,.30)),
 ('A03','店舗・施設区画（裏室除く）','専用バックルームを除いた区画投影。壁/什器を含む名目区画で、純売場有効面積ではない。',(.60,.76,.88)),
 ('A04','共用設備核床（開口除く）','トイレ・EV前室・階段前等。開口を除いた床投影。publicにも入る。',(.83,.58,.65)),
 ('A05','6棟投影内の前廊床','B1は屋内、1～3Fは庇下前廊、RFは露天屋上回廊。同じ位置でも階で屋内外を混同しない。',(.87,.78,.42)),
 ('A06','6棟投影外の前廊接続帯','名目前廊が躯体投影を越える接続帯。B1は地下内、1Fは屋外、上階はデッキ接続帯。庇下面積へ混ぜない。',(.96,.62,.24)),
 ('A07','地下屋内連絡ホール','B1のpublicのうち前廊・設備核を除く屋内ホール。地上の屋外通路とは別用途。',(.72,.72,.85)),
 ('A08','屋内共用の残り','元indoor_publicのうち既に前廊/設備核へ配分したものを除く。該当0でも基準を保持。',(.83,.82,.92)),
 ('A09','地上広場・庭の歩行床','1F publicのうち6棟外・前廊外で、3広場の形状に入る床。非公開の植栽床ではない。',(.72,.86,.52)),
 ('A10','地上屋外通路','1F publicのうち設備核/前廊/広場歩行床を除く通路。',(.63,.86,.85)),
 ('A11','上階の棟間デッキ','2F/3F/RF publicのうち6棟投影外。既配分の前廊接続帯を除く。地面・中庭の空中抜けではない。',(.49,.72,.71)),
 ('A12','屋上庭園の露天歩行床','RF publicのうち6棟投影内で、設備核・小施設・前廊投影を除いた露天の床。',(.68,.81,.38)),
 ('A13','非公開の植栽床','1Fの地上緑地とRFの植栽床。立入り用publicに入らない。地上は構造床板外、RFは構造床板内。',(.32,.56,.29)),
 ('A14','閉鎖搬入ヤード','B1のloading_yard。public・他区分との交差を除いた専用部分。',(.58,.58,.60)),
 ('A15','管理・搬入用の専用通路','B1 staff_corridorのうち既配分public/ヤードを除く専用床。共用部との重複は二重加算しない。',(.68,.51,.39)),
 ('A16','残余躯体・境界調整帯','上記以外の既設計投影。外壁/区画境界・閉鎖予約を含む。設備割付が完成したと扱わない。',(.81,.80,.75))]
META={k:dict(name=n,definition=d,color=c)for k,n,d,c in CATALOG};PAV=unary_union([v['footprint']for v in D['pavilions']]);PLAZA=unary_union([p['court']for p in D['plazas']]);FLOORS=[];UNITS=[];CORES=[];NOMINAL=[]
for f in D['floors']:
 lev=f['level'];pub=f['public'];plate=f['floor_plate'];shell=f['shell'];front=unary_union([p['front_corridor']for p in f['pavilions']]);core=unary_union([c['outline']for c in f['cores']]);store=unary_union([s['polygon']for s in f['stores']]);back=unary_union([s['backroom'].intersection(s['polygon'])for s in f['stores']]);garden=unary_union([x['geom']for x in f['landscape']]);yard=f.get('loading_yard',Polygon());staff=f.get('staff_corridor',Polygon())
 # Audit domain includes only actually designed surfaces/reservations, never the entire site bounding box or sky void.
 domain=unary_union([PAV,shell,plate,pub,front,core,store,back,garden,f['shafts'],yard,staff]);assigned=Polygon();zones=[]
 def put(code,candidate):
  global assigned
  candidate=unary_union(polys(candidate));clipped=candidate;q=unary_union(polys(clipped.difference(assigned)));zones.append(dict(code=code,name=META[code]['name'],geom=q,area_m2=q.area,public_m2=q.intersection(pub).area,pavilion_projection_m2=q.intersection(PAV).area,floor_plate_m2=q.intersection(plate).area,opening_m2=q.intersection(f['shafts']).area));assigned=assigned.union(q)
 put('A01',f['shafts']);put('A02',back);put('A03',store);put('A04',core)
 put('A05',pub.intersection(front).intersection(PAV));put('A06',pub.intersection(front).difference(PAV))
 put('A07',pub if lev==-1 else Polygon());put('A08',f['indoor_public']if lev in[0,1,2]else Polygon())
 put('A09',pub.intersection(PLAZA).difference(PAV)if lev==0 else Polygon());put('A10',pub if lev==0 else Polygon())
 put('A11',pub.difference(PAV)if lev>0 else Polygon());put('A12',pub.intersection(PAV)if lev==3 else Polygon())
 put('A13',garden);put('A14',yard);put('A15',staff);put('A16',domain)
 # Independent reconciliation on the delivered construction, not just the sum printed by the allocator.
 union=unary_union([q['geom']for q in zones]);sum_area=sum(z['area_m2']for z in zones)
 ck('exclusive_sum_equals_union',f['label'],abs(sum_area-union.area)<EPS,sum_area-union.area,lev)
 ck('partition_covers_domain',f['label'],domain.symmetric_difference(union).area<EPS,domain.symmetric_difference(union).area,lev)
 ck('public_reconstructed',f['label'],abs(sum(z['public_m2']for z in zones)-pub.area)<EPS,sum(z['public_m2']for z in zones)-pub.area,lev)
 ck('pavilion_projection_reconstructed',f['label'],abs(sum(z['pavilion_projection_m2']for z in zones)-PAV.area)<EPS,sum(z['pavilion_projection_m2']for z in zones)-PAV.area,lev)
 ck('floor_plate_reconstructed',f['label'],abs(sum(z['floor_plate_m2']for z in zones)-plate.area)<EPS,sum(z['floor_plate_m2']for z in zones)-plate.area,lev)
 ck('public_not_in_other_reserve',f['label'],next(z for z in zones if z['code']=='A16')['public_m2']<EPS,next(z for z in zones if z['code']=='A16')['public_m2'],lev)
 for i,z in enumerate(zones):
  ck('zone_valid',f['label']+'/'+z['code'],z['geom'].is_valid,None,lev)
  for w in zones[i+1:]:ck('zone_pair_no_overlap',f['label']+'/'+z['code']+'/'+w['code'],z['geom'].intersection(w['geom']).area<EPS,z['geom'].intersection(w['geom']).area,lev)
 # Original metrics are separate projections and must not be added as independent areas.
 reconstruction=PAV.union(pub).difference(f['shafts'])
 base_formula_gap=plate.symmetric_difference(reconstruction).area
 if lev!=-1:ck('floor_plate_formula',f['label'],base_formula_gap<EPS,base_formula_gap,lev)
 record=dict(level=lev,label=f['label'],height=f['height'],zones=zones,audit_domain=domain,audit_domain_m2=domain.area,six_pavilion_projection_m2=PAV.area,original_shell_m2=shell.area,original_public_m2=pub.area,original_walkable_m2=f['walkable'].area,original_floor_plate_m2=plate.area,original_outdoor_ground_m2=f['outdoor_ground'].area,original_outdoor_deck_m2=f['outdoor_deck'].area,original_indoor_public_m2=f['indoor_public'].area,public_inside_six_pavilions_m2=pub.intersection(PAV).area,public_outside_six_pavilions_m2=pub.difference(PAV).area,six_pavilions_not_public_m2=PAV.difference(pub).area,public_minus_pavilion_area_m2=pub.area-PAV.area,full_union_pav_public_m2=PAV.union(pub).area,core_openings_inside_pavilions_m2=f['shafts'].intersection(PAV).area,original_front_corridor_m2=front.area,front_inside_pavilions_m2=front.intersection(PAV).area,front_outside_pavilions_m2=front.difference(PAV).area,front_and_core_overlap_m2=front.intersection(core).area,garden_raw_m2=garden.area,garden_in_public_m2=garden.intersection(pub).area,garden_in_floor_plate_m2=garden.intersection(plate).area,garden_outside_floor_plate_m2=garden.difference(plate).area,plate_formula_residual_m2=base_formula_gap,plate_outside_pav_public_m2=plate.difference(PAV.union(pub)).area,public_not_walkable_m2=pub.difference(f['walkable']).area)
 FLOORS.append(record)
 for s in f['stores']:
  gross=s['polygon'];bk=s['backroom'].intersection(gross);net=gross.difference(bk);unit=dict(level=lev,label=f['label'],id=s['id'],pavilion=s['pavilion'],category=s['category'],kind=s['kind'],gross_m2=gross.area,backroom_m2=bk.area,excluding_backroom_m2=net.area,inside_pavilion_m2=gross.intersection(PAV).area,public_intersection_m2=gross.intersection(pub).area,area_zone_backroom_m2=gross.intersection(next(z['geom']for z in zones if z['code']=='A02')).area,area_zone_front_m2=gross.intersection(next(z['geom']for z in zones if z['code']=='A03')).area,legacy_id=s['legacy_id']);UNITS.append(unit)
  ck('unit_gross_equals_back_plus_front',s['id'],abs(gross.area-bk.area-net.area)<EPS,gross.area-bk.area-net.area,lev)
  ck('unit_partition_reconstructed',s['id'],abs(gross.area-unit['area_zone_backroom_m2']-unit['area_zone_front_m2'])<EPS,gross.area-unit['area_zone_backroom_m2']-unit['area_zone_front_m2'],lev)
 for c in f['cores']:
  CORES.append(dict(label=f['label'],id=c['id'],footprint_m2=c['outline'].area,shaft_m2=c['outline'].intersection(f['shafts']).area,floor_m2=c['outline'].difference(f['shafts']).area,public_m2=c['outline'].intersection(pub).area,nominal_front_overlap_m2=c['outline'].intersection(front).area))
 # Detailed nominal overlaps are reported, not silently fixed in the source.
 NOMINAL.append(dict(label=f['label'],front_outside_pavilion_geom=front.difference(PAV),front_and_core_geom=front.intersection(core),staff_and_public_geom=staff.intersection(pub),source_indoor_public_forehall_geom=f['indoor_public'].intersection(front),source_indoor_public_not_net_walkable_geom=f['indoor_public'].difference(f['walkable'])))
# Keep unnormalized source numbers alongside derived precision-normalized audit areas.
NORMALIZATION=[];raw_pav=unary_union([shape(p['footprint'])for p in RAW['pavilions']])
for raw_f,derived_f in zip(RAW['floors'],D['floors']):
 for key in['shell','public','walkable','floor_plate','shafts','residual','void','indoor_public','outdoor_ground','outdoor_deck']:
  original=shape(raw_f[key]);normal=derived_f[key];delta=normal.area-original.area
  NORMALIZATION.append(dict(floor=raw_f['label'],field=key,original_area_m2=original.area,audit_area_m2=normal.area,area_delta_m2=delta))
  ck('audit_precision_area_delta_within_epsilon',raw_f['label']+'/'+key,abs(delta)<EPS,delta,raw_f['level'])
 NORMALIZATION.append(dict(floor=raw_f['label'],field='six_pavilion_projection_union',original_area_m2=raw_pav.area,audit_area_m2=PAV.area,area_delta_m2=PAV.area-raw_pav.area))
 ck('audit_precision_area_delta_within_epsilon',raw_f['label']+'/six_pavilions',abs(PAV.area-raw_pav.area)<EPS,PAV.area-raw_pav.area,raw_f['level'])
(O/'raw-source-vs-audit-precision.json').write_text(json.dumps(NORMALIZATION,ensure_ascii=False,indent=2))

# Record all known areas; categories are polygons and the declared order is auditable.
DATA=dict(version='C area audit v2',design_only=True,source_geometry_sha256=SOURCE_SHA,coordinate_system='World XZ metres',area_unit='m²',numeric_area_epsilon_m2=EPS,audit_precision_grid_m=1e-12,method='Priority-based exclusive partition of actual v1 designed surfaces. No source geometry changes; audit-only 1e-12m precision normalization to stabilize GEOS boundary overlays; no whole-site bbox floor. Intersections with public/footprint/plate are cross-tabulated, never added twice.',priority=[k for k,_,_,_ in CATALOG],catalog=META,six_pavilion_projection=PAV,floors=FLOORS)
(O/'area-polygons.json').write_text(json.dumps(DATA,default=enc,ensure_ascii=False,indent=2));(O/'nominal-overlaps.json').write_text(json.dumps(NOMINAL,default=enc,ensure_ascii=False,indent=2));(O/'unit-area-ledger.json').write_text(json.dumps(UNITS,ensure_ascii=False,indent=2))
features=[]
for f in FLOORS:
 for z in f['zones']:
  features.append(dict(type='Feature',geometry=mapping(z['geom']),properties={**{k:v for k,v in z.items()if k!='geom'},'level':f['level'],'floor':f['label'],'source_geometry_sha256':SOURCE_SHA}))
(O/'exclusive-area-zones.geojson').write_text(json.dumps(dict(type='FeatureCollection',name='C_v1_exclusive_area_audit_World_XZ_metres',features=features),ensure_ascii=False,indent=2))
with(O/'exclusive-area-ledger.csv').open('w',encoding='utf-8-sig',newline='')as fp:
 w=csv.writer(fp);w.writerow(['階','区分ID','排他的用途区分','区分面積㎡','うち元public㎡','うち6棟投影内㎡','うち構造床板内㎡','うち開口㎡','定義'])
 for f in FLOORS:
  for z in f['zones']:w.writerow([f['label'],z['code'],z['name'],z['area_m2'],z['public_m2'],z['pavilion_projection_m2'],z['floor_plate_m2'],z['opening_m2'],META[z['code']]['definition']])
with(O/'all-floor-metrics.csv').open('w',encoding='utf-8-sig',newline='')as fp:
 w=csv.writer(fp);w.writerow(['階','高さm','6棟投影㎡','元shell㎡','元public㎡','元walkable㎡','publicの6棟内㎡','publicの6棟外㎡','元floor_plate㎡','元indoor_public㎡','元outdoor_ground㎡','元outdoor_deck㎡','非公開植栽㎡','植栽の床板内㎡','監査対象投影和集合㎡'])
 for f in FLOORS:w.writerow([f['label'],f['height'],f['six_pavilion_projection_m2'],f['original_shell_m2'],f['original_public_m2'],f['original_walkable_m2'],f['public_inside_six_pavilions_m2'],f['public_outside_six_pavilions_m2'],f['original_floor_plate_m2'],f['original_indoor_public_m2'],f['original_outdoor_ground_m2'],f['original_outdoor_deck_m2'],f['garden_raw_m2'],f['garden_in_floor_plate_m2'],f['audit_domain_m2']])
with(O/'all-unit-area-ledger.csv').open('w',encoding='utf-8-sig',newline='')as fp:
 w=csv.writer(fp);w.writerow(['階','区画ID','棟','用途','商業/施設','区画全体㎡','うち専用裏室㎡','裏室除外㎡','6棟投影内㎡','元publicとの数値交差㎡','A02寄与㎡','A03寄与㎡','旧ID'])
 for u in UNITS:w.writerow([u['label'],u['id'],u['pavilion'],u['category'],u['kind'],u['gross_m2'],u['backroom_m2'],u['excluding_backroom_m2'],u['inside_pavilion_m2'],u['public_intersection_m2'],u['area_zone_backroom_m2'],u['area_zone_front_m2'],u['legacy_id']or''])
with(O/'core-area-ledger.csv').open('w',encoding='utf-8-sig',newline='')as fp:
 w=csv.writer(fp);w.writerow(['階','設備核','投影全体㎡','階段EV開口㎡','開口以外の床㎡','元public㎡','名目前廊との交差㎡'])
 for c in CORES:w.writerow([c['label'],c['id'],c['footprint_m2'],c['shaft_m2'],c['floor_m2'],c['public_m2'],c['nominal_front_overlap_m2']])
# Serialized output is checked again: never trust only the allocator's in-memory precision context.
read=dec(json.loads((O/'area-polygons.json').read_text()))
for f in read['floors']:
 union=unary_union([z['geom']for z in f['zones']]);ck('serialized_union_equals_domain',f['label'],union.symmetric_difference(f['audit_domain']).area<EPS,union.symmetric_difference(f['audit_domain']).area,f['level'])
 for i,z in enumerate(f['zones']):
  ck('serialized_area_matches_ledger',f['label']+'/'+z['code'],abs(z['geom'].area-z['area_m2'])<EPS,z['geom'].area-z['area_m2'],f['level'])
  for q in f['zones'][i+1:]:ck('serialized_zone_no_overlap',f['label']+'/'+z['code']+'/'+q['code'],z['geom'].intersection(q['geom']).area<EPS,z['geom'].intersection(q['geom']).area,f['level'])
ck('source_geometry_bytes_unchanged','C-v1',source_path.read_bytes()==source_bytes)
failed=[x for x in CHECKS if not x['pass_']];(O/'checks.json').write_text(json.dumps(CHECKS,ensure_ascii=False,indent=2));v=dict(source_geometry_sha256=SOURCE_SHA,source_unchanged=True,unit_count=len(UNITS),floor_count=len(FLOORS),category_count=len(CATALOG),checks=len(CHECKS),passed=len(CHECKS)-len(failed),failed=failed,numeric_epsilon_m2=EPS,not_a_game_test=True,geometry_modified=False,audit_precision_grid_m=1e-12,maximum_audit_normalization_area_delta_m2=max(abs(x['area_delta_m2'])for x in NORMALIZATION),source_input_metrics_preserved_separately=True)
(O/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2));print(json.dumps(v,ensure_ascii=False,indent=2));assert not failed,failed[:10]
print('1F exclusive zones',[(z['code'],round(z['area_m2'],6),round(z['public_m2'],6))for z in FLOORS[1]['zones']])
