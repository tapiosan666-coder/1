from pathlib import Path
import sys,csv
sys.path.insert(0,str(Path(__file__).resolve().parent));from site_v2_common import *
P=Path(__file__).resolve().parents[1];D=read(P/'source/design-v6.json');A=read(P/'source/annex-v6.json');levels=[A['basement'],*D['floors'],A['roof']];rows=[]
for f in levels:
 for q in f['vertical_devices']:
  ref=next(g for g in D['floors'][0]['vertical_devices']if g['core']==q['core']);rows.append({'floor':f['label'],'core':q['core'],'height_m':f['height'],'lift_opening_offset_m2':q['lift_opening'].symmetric_difference(ref['lift_opening']).area,'stair_opening_offset_m2':q['stair_opening'].symmetric_difference(ref['stair_opening']).area,'stair_flight_projection_offset_m2':q['lower_flight_projection'].symmetric_difference(ref['lower_flight_projection']).area,'stair_base_note':'B1 lowest floor has no downwards stair opening; upward flight and landing compared'if f['label']=='B1'else'upper-floor opening compared','lift_opening_filled_m2':q['lift_opening'].intersection(f['floor_plate']).area,'stair_opening_filled_m2':q['stair_opening'].intersection(f['floor_plate']).area,'CAD_alignment_pass':q['lift_opening'].symmetric_difference(ref['lift_opening']).area<1e-4 and q['lower_flight_projection'].symmetric_difference(ref['lower_flight_projection']).area<1e-4 and(q['stair_opening'].is_empty if f['label']=='B1'else q['stair_opening'].symmetric_difference(ref['stair_opening']).area<1e-4),'implemented_operating_elevator':False,'B1_RF_stair_walk_implemented':False})
with open(P/'source/vertical-interface-15-checks.csv','w',encoding='utf-8-sig',newline='')as f:w=csv.DictWriter(f,rows[0].keys());w.writeheader();w.writerows(rows)
print('VERTICAL',rows)
with open(P/'source/roof-support-reservations.csv','w',encoding='utf-8-sig',newline='')as f:
 fields=['id','area_m2','maximum_overhang_depth_m','column_centres','column_size_m','base_y','beam_underside_y','beam_depth_m','geometry_clear_of_customer_and_store_basement','capacity_verified','foundation_verified','status'];w=csv.DictWriter(f,fields);w.writeheader();w.writerows([{k:q.get(k,'')for k in fields}for q in A['support_reservations']])
write(P/'evidence/interface-results.json',{'vertical_checks':rows,'CAD_alignment_passed':sum(q['CAD_alignment_pass']for q in rows),'capacity_verified':False,'B1_RF_vertical_traversal_tested':False})
