"""Dimensioned 2D equipment studies inside actual 18 large-store plots. Not Godot construction."""
from pathlib import Path
import sys,json,csv,collections
sys.path.insert(0,'/workspace/1/tools');from site_v2_common import *
import numpy as np
P=Path(__file__).resolve().parents[1];O=P/'source/program-review-v3';studies=read(O/'large-store-studies.json');D=read(R/'docs/site-correction-v3/geometry.json');result=[]
def svgpath(g):return' '.join(' '.join('M'+' L'.join(f'{x:.3f},{z:.3f}'for x,z in ring.coords)+' Z'for ring in [p.exterior,*p.interiors])for p in polys(g))
for study in studies:
 s=next(s for f in D['floors']if f['wing']=='B'and f['label']==study['floor']for s in f['stores']if s['id']==study['id']);u=np.array(s['u']);n=np.array(s['n']);e=np.array(s['entry']);category=study['category'];fixtures=[];dimensions={}
 for zone in study['zones']:
  if zone['id']in ['STOCK','CINEMA-LOBBY']:continue
  poly=zone['polygon'];kind='retail_display';length,depth=1.8,.8
  if zone['id'].startswith('HALL-'):
   c=np.array(poly.centroid.coords[0]);count=0
   for row in range(10):
    for col in [-3.1,-2.5,-1.9,-1.3,1.3,1.9,2.5,3.1]:
     p=c+u*col+n*((row-4.5)*1.05);fp=rect(p,u,.58,.65);fixtures.append({'zone':zone['id'],'kind':'cinema_seat','polygon':fp,'length_m':.58,'depth_m':.65});count+=1
   fixtures.append({'zone':zone['id'],'kind':'screen_6_4m','polygon':rect(c-n*7.5,u,6.4,.2),'length_m':6.4,'depth_m':.2});continue
  z=int(zone['id'][1:])-1
  if category=='家電・生活大型店':kind,length,depth=[('hands_on_demo',2.4,1.0),('TV_audio_demo',2.8,.7),('appliance_island',1.8,1.6),('service_counter',2.4,1.)][z]
  elif category=='食品大型店':kind,length,depth=[('produce_table',1.8,1.2),('ambient_gondola',5.5,.9),('cold_case',3.6,.9),('fresh_prep_workline',2.4,1.2)][z]
  elif category in['書店・生活大型店','書籍・雑貨']:kind,length,depth=[('editorial_table',1.8,1.1),('book_gondola',2.,.7),('kids_low_display',1.8,1.),('reading_worktable',1.8,1.2)][z]
  elif category in['大型衣料','生活・服飾']:kind,length,depth=[('styled_feature_plinth',2.,1.2),('garment_rail',1.8,.7),('fitting_booth',1.8,1.8),('checkout_counter',2.4,1.)][z]
  elif category=='フードホール':kind,length,depth=[('kitchen_and_servery_unit',6.,5.5),('seated_dining_table_reservation',2.8,2.5),('family_table_reservation',4.,3.),('tray_return_station',3.,1.2)][z]
  elif category=='カフェ':kind,length,depth=[('order_pickup_counter',3.4,2.2),('cafe_prep_workline',3.6,1.6),('lounge_seating_reservation',2.8,2.2),('two_person_table_reservation',1.8,1.8)][z]
  elif category=='レストラン':kind,length,depth=[('reception_waiting',2.4,1.8),('dining_table_reservation',2.8,2.5),('group_dining_reservation',3.5,2.8),('kitchen_workline',3.,1.4)][z]
  pts=[np.array(c)for p in polys(poly)for c in p.exterior.coords]
  if not pts:continue
  aa=[np.dot(p-e,u)for p in pts];bb=[np.dot(p-e,n)for p in pts];placed=[]
  for b in np.arange(min(bb)+depth/2+.4,max(bb),depth+1.8):
   for a in np.arange(min(aa)+length/2+.4,max(aa),length+1.8):
    fp=rect(e+u*a+n*b,u,length,depth)
    if poly.buffer(-.3).covers(fp):fixtures.append({'zone':zone['id'],'kind':kind,'polygon':fp,'length_m':length,'depth_m':depth});placed.append(fp)
    if len(placed)>=32:break
   if len(placed)>=32:break
  dimensions[kind]=[length,depth]
 outside=sum(q['polygon'].difference(s['polygon']).area for q in fixtures);overlap=sum(q['polygon'].area for q in fixtures)-unary_union([q['polygon']for q in fixtures]).area
 item={'id':s['id'],'category':category,'fixtures':fixtures,'module_dimensions_m':dimensions,'fixture_counts':dict(collections.Counter(q['kind']for q in fixtures)),'outside_plot_m2':outside,'fixture_overlap_m2':overlap,'geometry_check':outside<1e-6 and overlap<1e-6,'status':'DIMENSIONED 2D STUDY ONLY; staff paths, customer approach to every fixture, egress, utilities, structure, sound isolation and Godot movement are not verified'};result.append(item)
 x0,z0,x1,z1=s['polygon'].bounds;parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0-2} {z0-2} {x1-x0+4} {z1-z0+4}" width="1600" height="1000"><path d="{svgpath(s["polygon"])}" fill="#f5f1e7" stroke="#45574b" stroke-width=".14"/><path d="{svgpath(s["backroom"])}" fill="#b2c0cd"/>']
 for i,z in enumerate(study['zones']):
  if z['id']=='STOCK':continue
  parts.append(f'<path d="{svgpath(z["polygon"])}" fill="{["#ddd9c6","#e4cfb8","#cad9d0","#d4ccd8"][i%4]}" stroke="#637469" stroke-width=".08"/>')
 for q in fixtures:parts.append(f'<path d="{svgpath(q["polygon"])}" fill="#7e877a" stroke="#495e51" stroke-width=".07"/>')
 parts.append(f'<path d="{svgpath(study["main_spine"])}" fill="#fafaf3" stroke="#597b68" stroke-width=".13"/>');x,z=s['entry'];parts.append(f'<circle cx="{x}" cy="{z}" r=".6" fill="#bb5542"/></svg>');(O/(s['id']+'-functional.svg')).write_text(''.join(parts))
(O/'large-store-equipment.json').write_text(json.dumps(result,default=encode,ensure_ascii=False,indent=2))
# Strengthen unapproved merger review: actual sales-to-sales interface and wider entrance feasibility.
mergers=read(O/'merger-review.json')
for m in mergers:
 f=next(f for f in D['floors']if f['wing']=='B'and f['label']==('2F'if'2F'in m['id']else'3F'));ss=[next(s for s in f['stores']if s['id']==id)for id in m['stores']];main=next(s for s in ss if s['id']==m['primary_entry_store']);domain=m['polygon'].union(f['public']);m['entry_width_studies']=[]
 for width in[4.8,3.6,2.4]:
  cut=rect(main['entry'],main['u'],width,.6);m['entry_width_studies'].append({'proposed_width_m':width,'outside_merged_plot_or_public_m2':cut.difference(domain).area,'fits_2D_aperture_footprint':cut.difference(domain).area<.001})
 m['internal_sales_connection_studies']=[]
 for a in ss:
  for b in ss:
   if a['id']>=b['id']:continue
   shared=a['sales'].boundary.intersection(b['sales'].boundary)
   segs=lines(shared)
   m['internal_sales_connection_studies'].append({'a':a['id'],'b':b['id'],'sales_shared_boundary_m':shared.length,'candidate_portal_center':list(max(segs,key=lambda l:l.length).interpolate(.5,normalized=True).coords[0])if segs else None,'status':'SALES_SHARED_EDGE_EXISTS; proposed opening still needs wall and route verification'if shared.length>1.5 else'NO_DIRECT_SALES_CONNECTION; stock/layout redesign required'})
 m['store_count_before']=len(f['stores']);m['store_count_after_if_approved']=len(f['stores'])-len(ss)+1;m['proposed_id_not_applied']='B2-M01-STUDY'if f['label']=='2F'else'B3-M01-STUDY'
(O/'merger-review.json').write_text(json.dumps(mergers,default=encode,ensure_ascii=False,indent=2))
print('LARGE_EQUIPMENT_STUDIES',len(result),'geometric placement passes',sum(q['geometry_check']for q in result),'not operational passes')
