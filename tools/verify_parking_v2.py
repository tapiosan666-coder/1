"""Independent checks of delivered parking JSON/PDF. Does not read or modify game resources."""
from pathlib import Path
import sys,json,hashlib,csv,collections,math
sys.path.append('/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
import fitz
from shapely.geometry import shape,Point,LineString,Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree
R=Path(__file__).resolve().parents[1];O=R/'docs/parking-blocks-v2';P=R/'downloads/FIND_YOURSELF-Parking-Blocks-v2.pdf';G=json.loads((O/'geometry.json').read_text());C=json.loads((O/'checks.json').read_text());EPS=1e-8;CHECK=[];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def ck(k,id,ok,v=None):CHECK.append(dict(kind=k,id=id,pass_=bool(ok),value=v))
seen=set()
def valid(o,path=''):
 if isinstance(o,dict):
  if'type'in o and('coordinates'in o or'geometries'in o):
   h=hashlib.sha256(json.dumps(o,sort_keys=True).encode()).hexdigest()
   if h not in seen:seen.add(h);ck('delivered_geometry_valid',path,shape(o).is_valid)
  else:
   for k,v in o.items():valid(v,path+'/'+k)
 elif isinstance(o,list):
  for i,v in enumerate(o):valid(v,path+'/'+str(i))
valid(G)
ALL=[];CATEGORIES=collections.Counter();FACILITY=[]
for fac in G['facilities']:
 states={f['level']for f in fac['floors']};edges=collections.defaultdict(set)
 for r in fac['ramps']:edges[r['from_level']].add(r['to_level'])
 seenlevels={0};todo=[0]
 while todo:
  n=todo.pop()
  for q in edges[n]-seenlevels:seenlevels.add(q);todo.append(q)
 ck('vehicle_all_real_decks_reachable_from_ground',fac['id'],seenlevels==states,sorted(seenlevels));ck('no_phantom_deck_edge',fac['id'],all(q in states for n,e in edges.items()for q in e))
 for f in fac['floors']:
  id=fac['id']+'/'+str(f['level']);shell=shape(f['shell']);plate=shape(f['floor_plate']);veh=shape(f['vehicle_aisles']);ped=shape(f['pedestrian']);cross=shape(f['crossings']);openings=shape(f['ramp_openings']).union(shape(f['vertical_shafts']));terminal=shape(f['ramp_terminal_barriers']);columns=shape(f['columns']);CATEGORIES.update(s['category']for s in f['stalls'])
  for k,a in [('vehicle_inside_shell',veh.difference(shell).area),('pedestrian_inside_shell',ped.difference(shell).area),('vehicle_supported',veh.difference(plate).area),('pedestrian_supported',ped.difference(plate).area),('plate_not_in_openings',plate.intersection(openings).area),('ped_crossing_only',ped.intersection(veh).difference(cross).area),('pedestrian_not_in_ramp',ped.intersection(shape(f['ramp_openings'])).area),('vehicle_not_in_terminal_barrier',veh.intersection(terminal).area)]:ck(k,id,a<EPS,a)
  for st in f['stalls']:
   ALL.append(st['id']);p=shape(st['polygon']);ck('delivered_stall_dimensions',st['id'],abs((p.bounds[2]-p.bounds[0])-st['width_m'])<1e-8 and abs((p.bounds[3]-p.bounds[1])-st['length_m'])<1e-8);ck('delivered_stall_entry_on_front',st['id'],p.boundary.distance(Point(st['vehicle_entry']))<1e-8);ck('delivered_stall_vehicle_connection',st['id'],veh.distance(Point(st['vehicle_entry']))<.01);ck('delivered_stall_rear_ped_connection',st['id'],ped.distance(Point(st['pedestrian_entry']))<=.81);ck('delivered_stall_column_clear',st['id'],p.intersection(columns).area<EPS)
  for c in f['cores']:
   ck('delivered_stair_port_on_connected_ped',id+'/'+c['id'],ped.distance(Point(c['stair_entry']))<.01)
   if c['elevator_entry']:ck('delivered_EV_port_on_connected_ped',id+'/'+c['id'],ped.distance(Point(c['elevator_entry']))<.01)
  for port in fac['portals']:
   if port['level']!=f['level']:continue
   px,pz=port['point'];n=port['normal'];u=(-n[1],n[0]);w=port['width_m'];span=LineString([(px-u[0]*w/2,pz-u[1]*w/2),(px+u[0]*w/2,pz+u[1]*w/2)])
   ck('portal_full_width_floor_supported',port['id'],plate.buffer(1e-8).covers(span));surface=veh if port['type'].startswith('vehicle')else ped;ck('portal_connected_to_appropriate_network',port['id'],surface.distance(Point(port['point']))<.01)
  if fac['kind']=='garage'and f['level']in[0,6]:
   for lane in fac['ramp_lanes']:
    shaft=shape(lane['shaft']);a,b,c,d=shaft.bounds;zz=(b-.1)if f['level']==6 else(d+.1);span=LineString([(a,zz),(c,zz)]);ck('terminal_nonexistent_ramp_mouth_fully_closed',id+'/'+lane['direction'],terminal.buffer(1e-8).covers(span))
  if fac['kind']=='garage':
   mm=f['ramp_mouth_rules'];ck('roof_ground_active_mouth_rules',id,all((m['lower_role'].startswith('closed')if f['level']==6 else not m['lower_role'].startswith('closed'))and(m['upper_role'].startswith('closed')if f['level']==0 else not m['upper_role'].startswith('closed'))for m in mm))
 FACILITY.append({'id':fac['id'],'levels':len(fac['floors']),'count':sum(len(f['stalls'])for f in fac['floors']),'roof_spaces':len(fac['floors'][-1]['stalls'])if fac['kind']=='garage'else 0})
ck('global_stall_ID_unique','all',len(ALL)==len(set(ALL)),len(ALL));cap=json.loads((O/'capacity.json').read_text());ck('capacity_matches_actual_polygons','all',sum(q['count']for q in cap)==len(ALL))
with(O/'stall-ledger.csv').open(encoding='utf-8-sig',newline='')as fp:ledger=list(csv.DictReader(fp))
ck('ledger_IDs_match_exactly','all',{q['id']for q in ledger}==set(ALL)and len(ledger)==len(ALL))
# PDF provenance and label lookup: the full ID = deck prefix + 4-digit bay number on the page.
pv=json.loads((O/'pdf-source.json').read_text());ck('PDF_current_geometry','all',pv['geometry_sha256']==sha(O/'geometry.json'));ck('PDF_current_checks','all',pv['checks_sha256']==sha(O/'checks.json'));ck('PDF_current_bytes','all',pv['pdf_sha256']==sha(P));doc=fitz.open(P);pages=json.loads((O/'pdf-deck-pages.json').read_text());ck('all_seventeen_decks_have_a_plan','all',len(pages)==17)
for rec in pages:
 text=doc[rec['page']-1].get_text();ck('PDF_deck_prefix',rec['prefix'],rec['prefix']in text);floor=next(f for fac in G['facilities']if fac['id']==rec['facility']for f in fac['floors']if f['level']==rec['level'])
 for st in floor['stalls']:ck('PDF_bay_number_present',st['id'],st['id'].split('-')[-1]in text)
preview=Path('/tmp/parking-v2-preview');preview.mkdir(exist_ok=True);contact=fitz.open();pp=contact.new_page(width=1200,height=((len(doc)+3)//4)*210);pagechecks=[]
for i,p in enumerate(doc):
 pix=p.get_pixmap(matrix=fitz.Matrix(.26,.26));pix.save(preview/f'{i+1:02}.png');x=(i%4)*300;y=(i//4)*210;pp.insert_image(fitz.Rect(x,y,x+295,y+185),pixmap=pix);pp.insert_text((x+4,y+202),str(i+1),fontsize=12);bad=[]
 for b in p.get_text('dict')['blocks']:
  if b['type']!=0:continue
  for line in b['lines']:
   for s in line['spans']:
    r=fitz.Rect(s['bbox'])
    if r.x0<0 or r.y0<0 or r.x1>p.rect.width or r.y1>p.rect.height:bad.append(s['text'])
 ck('PDF_text_within_page',str(i+1),not bad,bad);pagechecks.append({'page':i+1,'rendered':True,'text_within_page':not bad})
pp.get_pixmap().save('/tmp/parking-v2-contact.png')
for i in[2,10,16,18,22,25,31]:doc[i].get_pixmap(matrix=fitz.Matrix(.8,.8)).save(preview/f'{i+1:02}-large.png')
warnings=fitz.TOOLS.mupdf_warnings();ck('PDF_render_no_warnings','all',not warnings,warnings);ck('PDF_TOC_complete','all',len(doc.get_toc())==len(doc))
fail=[q for q in C+CHECK if not q['pass_']];proof={'design_only':True,'game_modified':False,'mall_designs_modified':False,'geometry_sha256':sha(O/'geometry.json'),'checks_sha256':sha(O/'checks.json'),'pdf_sha256':sha(P),'pdf_pages':len(doc),'parking_decks':17,'total_spaces':len(ALL),'facility_summary':FACILITY,'category_summary':dict(CATEGORIES),'source_checks':len(C),'independent_checks':len(CHECK),'all_checks':len(C)+len(CHECK),'failed':fail,'area_epsilon_m2':EPS,'runtime_walk_or_vehicle_tests':0,'actual_structural_validation':False,'bay_labels_in_PDF':'Deck prefix in header + 4-digit individual bay number; exact full IDs in CSV/JSON.','page_checks':pagechecks,'independent_results':CHECK};(O/'verification.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2));print({k:proof[k]for k in['pdf_pages','total_spaces','source_checks','independent_checks','all_checks','failed']});assert not fail,fail[:12]
