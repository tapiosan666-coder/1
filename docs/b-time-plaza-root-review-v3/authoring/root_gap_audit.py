"""Whole B-wing ownership audit and conservative NOT-APPROVED enclosure proposals.
No source file is changed. Named public, service, vehicle, garden and staff spaces stay protected.
"""
from pathlib import Path
import sys,json,math,csv,itertools,collections,hashlib
sys.path.insert(0,'/workspace/1/tools');from site_v2_common import *
from shapely import maximum_inscribed_circle
P=Path(__file__).resolve().parents[1];O=P/'source/root-gap-review';O.mkdir(exist_ok=True)
D=read(R/'docs/site-correction-v3/geometry.json');B=[f for f in D['floors']if f['wing']=='B'];CROP=box(-512,-16,-349,124)
rows=[];details=[];summaries=[];changes=[];protected_routes=[]
def put(name,data):(O/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,default=encode))
def add(f,kind,g,ids,cause,policy,**extra):
 p=g.representative_point()if hasattr(g,'geom_type')else Point(g);id=f"B-{f['label']}-ISSUE-{sum(q['floor']==f['label']for q in rows)+1:04}";r={'issue_id':id,'floor':f['label'],'level':f['level'],'world_x_m':p.x,'world_y_m':f['height'],'world_z_m':p.y,'store_ids':' / '.join(ids),'kind':kind,'area_m2':g.area if hasattr(g,'area')else 0,'cause':cause,'policy':policy,'status':'DESIGN_REVIEW_REQUIRED','within_current_3D_crop':CROP.covers(p),**extra};rows.append(r);details.append({**r,'geometry':g});return id
for f in B:
 stores=f['stores'];core=unary_union([q['outline']for q in f['cores']]);shop=unary_union([s['polygon']for s in stores]);services=unary_union([q['polygon']for q in f.get('service_zones',[])]);program=unary_union([q['polygon']for q in f.get('program',[])]);gardens=unary_union([q['polygon']for q in f.get('gardens',[])]);staff=unary_union([q['line'].buffer(q['width_m']/2,cap_style=2)for q in f.get('staff_routes',[])]);parking=f.get('parking')or{};vehicle=parking.get('vehicle_aisles',Polygon());stalls=unary_union([q['polygon']for q in parking.get('stalls',[])]);protected=unary_union([f['public'],f['void'],f['shafts'],core,services,program,gardens,staff,vehicle,stalls,f.get('egress',Polygon())]);used=protected.union(shop);unallocated=f['floor_plate'].difference(used);role_polys=polys(unallocated);large_parts=sorted([q for q in role_polys if q.area>.5],key=lambda q:-q.area);small=unallocated.difference(unary_union(large_parts));plan_changed=[]
 for r in f.get('staff_routes',[]):protected_routes.append({'floor':f['label'],'id':r['id'],'width_m':r['width_m'],'role':r['role'],'geometry':r['line'],'rule':'Named staff route protected from gap annexation. Geometry alone does not certify operational access.'})
 for q in large_parts:
  near=sorted([(q.distance(s['polygon']),s)for s in stores],key=lambda a:a[0]);ids=[s['id']for dist,s in near if dist<.05];diam=maximum_inscribed_circle(q,tolerance=.025).length*2;public_contact=q.boundary.intersection(f['public'].buffer(.005)).length
  issue=add(f,'UNALLOCATED_ENVELOPE_REMAINDER',q,ids,'外郭BODYと店舗・共用部等の差分。個別の用途・入口・設備仕様を持たない。','必要な既存機能への帰属・店舗外郭の一体化・外郭縮減を先に設計。余剰形状を廊下や機械室と自動命名しない。',max_inscribed_diameter_m=diam,public_contact_length_m=public_contact)
  # Repair study: only a small single connected pocket adjoining an existing stock enclosure.
  stockshares=sorted([(q.boundary.intersection(s['backroom'].buffer(.005)).length,s)for s in stores if s.get('backroom')is not None],key=lambda a:-a[0]);eligible=bool(stockshares)and .5<q.area<100 and public_contact<6 and stockshares[0][0]>.75
  if not eligible:continue
  share,s=stockshares[0];old=next((c['new_polygon']for c in reversed(changes)if c['store']==s['id']),s['polygon']);new=old.union(q)
  if new.geom_type!='Polygon'or not new.is_valid:continue
  # Never reclassify a protected service/access/vehicle/plaza polygon.
  invasion=q.intersection(protected).area
  if invasion>1e-7:continue
  oldstock=next((c['new_backroom']for c in reversed(changes)if c['store']==s['id']),s['backroom']);allowance=diam<1.2;newstock=oldstock if allowance else oldstock.union(q)
  change={'issue_id':issue,'floor':f['label'],'level':f['level'],'store':s['id'],'old_polygon':old,'new_polygon':new,'old_backroom':oldstock,'new_backroom':newstock,'nonoccupiable_enclosure_allowance':q if allowance else Polygon(),'assigned_pocket':q,'added_plot_m2':q.area,'added_usable_stock_m2':0 if allowance else q.area,'shared_stock_boundary_m':share,'public_invaded_m2':invasion,'old_entry':s['entry'],'old_back_door':s['back_door'],'new_entry':s['entry'],'new_back_door':s['back_door'],'in_current_3D':q.intersects(CROP),'rule':'帰属先の既存区画そのものを拡張し、共有境界から外壁を再生成。旧外壁への継ぎ足しはしない。1.2m未満のふところは有効倉庫面積に算入しない。','status':'UNAPPROVED_DESIGN_PROPOSAL; applied only in separate v3 review draft'};changes.append(change);plan_changed.append(change)
 if not small.is_empty:add(f,'SUB_0_5_M2_FRAGMENTS_AGGREGATE',small,[],'差演算・量子化で生じた0.5㎡以下の小領域。','各領域を部屋や通路に数えない。帰属・納まりを確定するまで完成出図を止める。',fragment_count=len(polys(small)))
 # Every lot: disconnected islands, acute/short raw polygon corners, inconsistent plot/program boundaries.
 for s in stores:
  pp=polys(s['polygon']);entry=Point(s['entry'])
  for poly in pp:
   if poly.distance(entry)>.05 and poly.area>.001:add(f,'DISCONNECTED_TENANT_COMPONENT',poly,[s['id']],'入口を持つ主区画から離れた多角形が同一店舗IDに残る。','離れた片を売場・倉庫として計上しない。隣接領域との帰属を設計し直す。')
   coords=list(poly.exterior.coords)[:-1];sign=1 if poly.exterior.is_ccw else -1
   for i,b in enumerate(coords):
    a,c=coords[i-1],coords[(i+1)%len(coords)];v=(b[0]-a[0],b[1]-a[1]);w=(c[0]-b[0],c[1]-b[1]);l0,l1=math.hypot(*v),math.hypot(*w)
    if min(l0,l1)<1e-7:continue
    turn=math.degrees(math.atan2(v[0]*w[1]-v[1]*w[0],v[0]*w[0]+v[1]*w[1]));interior=180-sign*turn;near_open=min(Point(b).distance(Point(s[key]))for key in['entry','back_door']if key in s)<1.6
    if near_open:continue
    if(min(l0,l1)<.30 and abs(turn)>45)or interior<40 or interior>320:
     add(f,'RAW_POLYGON_SHORT_OR_ACUTE_CORNER',Point(b),[s['id']],'通路・設備核・他区画を順次差し引いた輪郭の微小辺/鋭角を、そのまま壁バッファへ使う。','入口セットバック・曲線・柱型は別属性で保持。不要な短辺は共有トポロジー上で両側同時に修正し、単独simplifyは禁止。',short_edge_m=min(l0,l1),interior_angle_deg=interior)
  stock=s.get('backroom',Polygon());sales=s.get('sales',Polygon());coverage=sales.union(stock).union(s.get('aisles',Polygon())).intersection(s['polygon']);missing=s['polygon'].difference(coverage)
  if missing.area>.5:add(f,'INTERNAL_PROGRAM_COVERAGE_GAP',missing,[s['id']],'店舗区画と売場・バックヤード等の区分が一致していない。','内装や棚で覆わず、床の用途区分と壁・入口を同じデータから生成する。')
 # Internal roles require their OWN door connection, not just one entrance somewhere in the lot.
 for st in stores:
  for role,key,anchor in [('BACKROOM','backroom','back_door'),('SALES','sales','entry')]:
   geom=st.get(key,Polygon());parts=[p for p in polys(geom)if p.area>.01]
   if len(parts)<=1:continue
   doors=[Point(st[anchor])]if st.get(anchor)else[]
   if role=='SALES'and st.get('secondary_entry'):doors.append(Point(st['secondary_entry']))
   for part in parts:
    if any(part.distance(p)<.04 for p in doors):continue
    add(f,role+'_COMPONENT_WITHOUT_OWN_ACCESS',part,[st['id']],'区画全体の入口検査だけでは、分離した売場/在庫片の入口欠落を検出できない。','有効な専用開口を持つ連結部分だけを用途面積に算入。別室として必要なら扉と到達経路を明示し、不要な片は納まり領域へ再設計。',program_component_m2=part.area)
 if f['level']in[0,1,2]:
  targets=[Point(st['entry']).buffer(2)for st in stores]+[Point(z['entry']).buffer(2)for z in f.get('service_zones',[])]+[q['outline'].buffer(1)for q in f['cores']]+[q['geom'].buffer(1)for q in f.get('furniture',[])]+[staff]
  thin=f['public'].difference(f['public'].buffer(-.60).buffer(.60)).difference(unary_union(targets))
  for part in polys(thin):
   if part.area>3 and part.length>8:add(f,'NARROW_PUBLIC_SPUR_CANDIDATE',part,[],'幅1.2mの形態検査で残り、近くに店舗入口・設備・家具・命名済み保守経路がない細い共用床候補。','数値だけで撤去しない。通路役割と見通しを設計評価し、用途がなければ隣接区画の外郭から共同で再設計。')
 # Full-wing between-lot passages. Named/public circulation is explicitly exempt, never filled.
 gaps=0;legit=0
 for a,b in itertools.combinations(stores,2):
  dist=a['polygon'].distance(b['polygon'])
  if not(.001<dist<1.5):continue
  q=a['polygon'].buffer(dist/2+.05).intersection(b['polygon'].buffer(dist/2+.05)).difference(shop)
  unowned=q.intersection(unallocated)
  if unowned.area>.05:
   add(f,'BETWEEN_STORE_UNOWNED_GAP',unowned,[a['id'],b['id']],'別々の区画輪郭に距離があり、その間に役割のない床が残る。','公開/搬入/保守と根拠づけられた道だけを保護。その他は区画の共有境界と外郭を再設計。',minimum_plot_distance_m=dist);gaps+=1
  elif q.intersection(protected).area>.05:legit+=1
 remaining=unallocated.difference(unary_union([q['assigned_pocket']for q in plan_changed]));summaries.append({'floor':f['label'],'level':f['level'],'unallocated_before_m2':unallocated.area,'unallocated_after_proposed_small_annex_m2':remaining.area,'unallocated_components_gt_0_5_m2':len(large_parts),'small_fragments_m2':small.area,'named_staff_routes':len(f.get('staff_routes',[])),'protected_near_store_corridor_pairs':legit,'unowned_near_store_gap_pairs':gaps,'proposed_annexations':len(plan_changed),'issues':sum(q['floor']==f['label']for q in rows),'all_floor_3D_status':'Only 1F–3F cropped scene exists. B1/RF are drawing audits, NOT Godot walked.'})
 # Compact whole-floor role map, keeping original named programs and movement.
 from program_review_v3 import svgpath
 x0,z0,x1,z1=f['shell'].bounds;elements=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0-8} {z0-8} {x1-x0+16} {z1-z0+16}" width="1800" height="800"><path d="{svgpath(f["shell"])}" fill="#f4f3ed" stroke="#57675d" stroke-width=".3"/><path d="{svgpath(protected.intersection(f["floor_plate"]))}" fill="#d2e4da"/>']
 for s in stores:elements.append(f'<path d="{svgpath(s["polygon"])}" fill="#d6d8d1" stroke="#647565" stroke-width=".15"/>')
 elements.append(f'<path d="{svgpath(unallocated)}" fill="#df9d79" stroke="#b26145" stroke-width=".15"/>')
 for q in plan_changed:elements.append(f'<path d="{svgpath(q["assigned_pocket"])}" fill="#668eaf"/>')
 elements.append('</svg>');(O/f'B-{f["label"]}-ownership.svg').write_text(''.join(elements))
put('full-B-root-audit.json',{'source_sha256':hashlib.sha256((R/'docs/site-correction-v3/geometry.json').read_bytes()).hexdigest(),'summaries':summaries,'issues':details,'named_staff_routes':protected_routes,'interpretation':'nav_free is the common-floor mask, not a ban on every off-nav area. Unallocated is computed after subtracting explicit programs, parking and named staff access. Numerical candidates are not automatically architectural defects.'})
with open(O/'issue-register.csv','w',newline='',encoding='utf-8-sig')as o:
 fields=sorted(set(k for q in rows for k in q));w=csv.DictWriter(o,fields,lineterminator='\n');w.writeheader();w.writerows(rows)
put('enclosure-proposals.json',{'status':'NOT_APPROVED; independent review scene only','original_source_modified':False,'changes':changes,'unresolved_after_proposal':summaries,'no_blanket_completion':True})
print('WHOLE_B_ROOT_AUDIT',len(rows),'issues/candidates;',len(changes),'small enclosure proposals')
for q in summaries:print(q['floor'],'unallocated',round(q['unallocated_before_m2'],2),'->',round(q['unallocated_after_proposed_small_annex_m2'],2),'issues',q['issues'])
