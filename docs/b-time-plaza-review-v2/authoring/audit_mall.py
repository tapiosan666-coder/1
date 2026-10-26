"""Independent full-wing/slice audit. Does not alter source plans or silently resize tenants."""
from pathlib import Path
import sys,json,csv,math,statistics,hashlib,collections,itertools
sys.path.insert(0,'/workspace/1/tools')
from site_v2_common import read,shape,box,Point,LineString,Polygon,unary_union,polys,lines,encode
P=Path(__file__).resolve().parents[1];R=Path('/workspace/1');OUT=P/'source/audit';OUT.mkdir(exist_ok=True)
D=read(R/'docs/site-correction-v3/geometry.json');crop=box(-512,-16,-349,124)
B=[f for f in D['floors']if f['wing']=='B'and f['level']in[0,1,2]]
rows=[];anchors=[];joints=[];classification=[];proposals=[];contact_stats=[]
def band(a):return '小型(<150㎡)'if a<150 else'中型(150〜500㎡)'if a<500 else'大型(500〜1500㎡)'if a<1500 else'核店舗(1500㎡以上)'
def write(name,v): (OUT/name).write_text(json.dumps(v,ensure_ascii=False,indent=2,default=encode))
for f in B:
 floor=f['level'];shops=f['stores'];occ=unary_union([s['polygon']for s in shops]);core=unary_union([c['outline']for c in f['cores']]);service=unary_union([z['polygon']for z in f['service_zones']]);unassigned=f['floor_plate'].intersection(crop).difference(f['public'].union(occ).union(core).union(service))
 cropped=[s for s in shops if s['polygon'].intersects(crop)];full=[s for s in cropped if crop.covers(s['polygon'])]
 overlaps=[]
 for a,b in itertools.combinations(shops,2):
  aa=a['polygon'].intersection(b['polygon']).area
  if aa>1e-7:overlaps.append({'a':a['id'],'b':b['id'],'area_m2':aa})
 # Segments near shop entrances are intentional recesses; preserve them.
 anomalies=[]
 for s in shops:
  poly=s['polygon'];area=poly.area;entry=Point(s['entry']);oldceil=[5.525,10.875,16.4][floor]-f['height']-.7
  if s.get('kind')=='anchor':
   anchors.append({'id':s['id'],'floor':f['label'],'use':s['category'],'area_m2':area,'sales_m2':s['sales'].area,'backroom_m2':s['backroom'].area,'frontage_parameter_m':s['frontage_m'],'depth_parameter_m':s['depth_m'],'door_clear_m':s['door_width_m'],'entry_world_xz':s['entry'],'polygon':poly,'main_route':s['main_route'],'in_validation_crop':poly.intersects(crop),'standard_generated_clear_height_m':oldceil,'separate_cinema_or_kitchen_layout_in_data':False})
  in_slice=poly.intersects(crop)
  rows.append({'id':s['id'],'floor':f['label'],'category':s['category'],'kind':s.get('kind'),'band':band(area),'area_m2':round(area,3),'plot_parts':len(polys(poly)),'sales_m2':round(s['sales'].area,3),'frontage_parameter_m':round(s['frontage_m'],3),'depth_parameter_m':round(s['depth_m'],3),'door_width_m':s['door_width_m'],'intersects_crop':in_slice,'fully_in_crop':crop.covers(poly),'entry_x':s['entry'][0],'entry_z':s['entry'][1]})
  parts=polys(poly)
  co=list(max(parts,key=lambda q:q.area).exterior.coords)[:-1]
  local=[]
  for i,b in enumerate(co):
   a=co[i-1];c=co[(i+1)%len(co)];v=(b[0]-a[0],b[1]-a[1]);w=(c[0]-b[0],c[1]-b[1]);l0=math.hypot(*v);l1=math.hypot(*w)
   if min(l0,l1)<1e-6:continue
   angle=math.degrees(math.acos(max(-1,min(1,(v[0]*w[0]+v[1]*w[1])/(l0*l1)))))
   back=Point(s.get('back_door',s['entry']));near_door=Point(b).distance(entry)<s['door_width_m']/2+.55 or Point(b).distance(back)<1.2
   if min(l0,l1)<.30 and angle>45 and not near_door:
    local.append({'point':b,'short_edge_m':min(l0,l1),'turn_deg':angle,'status':'PLAN_REVIEW_REQUIRED'if min(l0,l1)>.01 else'NUMERICAL_DETAIL'})
  if in_slice:anomalies.extend({'id':s['id'],**x}for x in local if crop.covers(Point(x['point'])))
  # Legacy glazing is a chord; remove the intended doorway before measuring off-boundary lengths.
  gl=unary_union(s.get('glazed_frontages',[]));u=s['u'];n=(-u[1],u[0]);e=s['entry'];dw=s['door_width_m']+.06
  door=Polygon([(e[0]+u[0]*a+n[0]*b,e[1]+u[1]*a+n[1]*b)for a,b in[(-dw/2,-.5),(dw/2,-.5),(dw/2,.5),(-dw/2,.5)]])
  rem=gl.difference(door);off=rem.difference(poly.buffer(.025)).length
  if in_slice:contact_stats.append({'id':s['id'],'legacy_glazing_off_plot_after_door_exclusion_m':off,'old_wall_ceiling_gap_m':oldceil-4.49,'new_wall_ceiling_gap_m':0,'old_glass_base_gap_m':.10,'new_glass_base_gap_m':0})
 # Retain natural plazas: residual areas are not automatically bad or filled.
 chunks=[]
 for q in polys(unassigned):
  if q.area>.5:chunks.append({'area_m2':q.area,'bounds':q.bounds,'polygon':q,'classification':'UNASSIGNED_CANDIDATE','note':'独自分類。外部床・搬入・設備余地を含む可能性。用途確定には設計確認が必要。'} )
 classification.append({'floor':f['label'],'full_B_stores':len(shops),'slice_intersections':len(cropped),'slice_full_tenants':len(full),'crop_box_m2':crop.area,'actual_slab_area_m2':f['floor_plate'].intersection(crop).area,'public_m2':f['public'].intersection(crop).area,'slice_tenant_area_m2':occ.intersection(crop).area,'bands_full_B':dict(collections.Counter(band(s['polygon'].area)for s in shops)),'categories_full_B':dict(collections.Counter(s['category']for s in shops)),'categories_slice':dict(collections.Counter(s['category']for s in cropped)),'overlap_pairs':overlaps,'unassigned_candidate_total_m2':unassigned.area,'unassigned_candidates':chunks,'short_corner_candidates':anomalies})
 # Explicit local joints only. Do not bridge public passages or legitimate two-metre service accesses.
 for a,b in itertools.combinations(cropped,2):
  dist=a['polygon'].distance(b['polygon'])
  if .001<dist<.35:
   narrow=a['polygon'].buffer(.18).intersection(b['polygon'].buffer(.18)).difference(a['polygon'].union(b['polygon'])).difference(f['public'].buffer(.01))
   if not narrow.is_empty:joints.append({'a':a['id'],'b':b['id'],'floor':floor,'gap_m':dist,'local_joint_candidate':narrow,'area_m2':narrow.area,'status':'NOT_APPLIED_REQUIRES_BOUNDARY_CLASSIFICATION','note':'公共通路を除外した候補のみ。機械的な隙間充填はしていない。'})
 # Select real contiguous units for a central size-variety proposal; actual plan remains frozen.
 cand=[s for s in cropped if crop.covers(s['polygon'])and s['polygon'].area<500]
 edges={s['id']:[]for s in cand}
 for a,b in itertools.combinations(cand,2):
  shared=a['polygon'].boundary.intersection(b['polygon'].boundary).length
  if shared>1.5:edges[a['id']].append(b['id']);edges[b['id']].append(a['id'])
 byid={s['id']:s for s in cand};seen=set()
 for start in sorted(byid):
  if start in seen:continue
  component=[];stack=[start]
  while stack:
   q=stack.pop()
   if q in seen:continue
   seen.add(q);component.append(q);stack.extend(edges[q])
  if len(component)<3:continue
  chosen=component[:4];union=unary_union([byid[q]['polygon']for q in chosen])
  if union.geom_type=='Polygon' and union.area>500:
   proposals.append({'id':f'CENTRAL-MERGE-{f["label"]}-{len(proposals)+1}','stores':chosen,'combined_area_m2':union.area,'polygon':union,'intent':'中央専門店街の連続区画を統合し、500㎡以上の中核的な専門店候補とする。既存大区画6店・広場・公共通路は維持。','status':'NOT_APPLIED_PENDING_USER_APPROVAL','checks':'共有境界長1.5m超の連結のみ選択。入口・内部壁・用途の詳細再設計は未実施。'})
summary={'basis':'B v4.1 / site v3 immutable','definitions':'面積帯はゲーム分析用仮区分。実在施設の正式分類ではない。frontage/depthは既存台帳パラメータで、最小離隔や実測天井高ではない。','reference':{'file':'AEON_LAKETOWN_OFFICIAL_FLOOR_GUIDE_202610.pdf','sha256':hashlib.sha256(next(Path('/workspace/attachments').rglob('AEON_LAKETOWN_OFFICIAL_FLOOR_GUIDE_202610.pdf')).read_bytes()).hexdigest(),'mori_pages':[4,5,6],'method':'目視。縮尺・実測面積・店舗総数は未確定のため数値比較していない。','observations':['専門店が連続し、幅の広い区画が途中にも混在する。','核店舗と広場への接続が通路の方向と景観をつくる。','現モデルは核店が切出し外、全専門店入口2.4m、看板幅8m上限・同一ガラス仕様が同じ外観を強める。']},'floors':classification,'anchors':anchors,'construction_causes':contact_stats,'local_joint_candidates':joints,'proposals_not_applied':proposals,'overall_status':'CONSTRUCTION_REPAIR_CHECKED_SEPARATELY; ARCHITECTURAL_REVIEW_PENDING'}
write('full-audit.json',summary)
with open(OUT/'all-B-store-ledger.csv','w',newline='',encoding='utf-8-sig')as out:
 w=csv.DictWriter(out,list(rows[0]));w.writeheader();w.writerows(rows)
# Full wing vector maps with actual anchors and the unchanged validation crop.
def svg_path(g):
 paths=[]
 for p in polys(g):
  chunks=[]
  for ring in[p.exterior,*p.interiors]:chunks.append('M'+' L'.join(f'{x:.3f},{z:.3f}'for x,z in ring.coords)+' Z')
  paths.append(' '.join(chunks))
 return ' '.join(paths)
for f in B:
 x0,z0,x1,z1=f['shell'].bounds;parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0-12} {z0-25} {x1-x0+24} {z1-z0+50}" width="1600" height="700"><rect x="{x0-12}" y="{z0-25}" width="{x1-x0+24}" height="{z1-z0+50}" fill="#fafaf6"/>']
 parts.append(f'<path d="{svg_path(f["public"])}" fill="#dce9e7" stroke="#667b77" stroke-width=".4"/>')
 for s in f['stores']:
  anchor=s.get('kind')=='anchor';col='#d1a464'if anchor else'#d9d9ce';parts.append(f'<path d="{svg_path(s["polygon"])}" fill="{col}" stroke="#4d5853" stroke-width=".3"/>')
  if anchor:
   q=s['polygon'].representative_point();parts.append(f'<text x="{q.x}" y="{q.y}" font-size="5" text-anchor="middle">{s["id"]}</text>')
 parts.append(f'<rect x="-512" y="-16" width="163" height="140" stroke="#be4a35" stroke-width="1.4" fill="none"/>')
 parts.append(f'<text x="{x0}" y="{z0-12}" font-size="8">B {f["label"]} / AMBER: ANCHORS / RED: VALIDATION CROP</text></svg>');(OUT/f'B-{f["label"]}-full-map.svg').write_text(''.join(parts))
print('AUDIT',len(rows),'units',len(anchors),'anchors',len(joints),'joint candidates',len(proposals),'not-applied proposals')
for f in classification:print(f['floor'],f['slice_full_tenants'],f['bands_full_B'],'unassigned candidates',round(f['unassigned_candidate_total_m2'],1),'short corners',len(f['short_corner_candidates']))
