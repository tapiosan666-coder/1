from pathlib import Path
import sys,json,math,collections,hashlib,shutil,csv
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'))
from site_v2_common import *
OUT=Path('/workspace/v17-review');(OUT/'source').mkdir(exist_ok=True);(OUT/'plans').mkdir(exist_ok=True)
F=read(P/'source/v11/floors-updated.json');D=read(P/'source/v17/scene-design.json');V=Path('/workspace/FIND_YOURSELF-Site-v16')
protected=[]
for item in read(P/'source/v15/pack-manifest.json'):
 p=item['path'];protected.append(dict(path=p,sha256=sha(P/p),unchanged=(P/p).read_bytes()==(V/p).read_bytes()))
for p in ['player.gd','escalator_v2.gd','elevators_v11.gd','source/v15/C-outlet-proposal.json','source/v15/ES-site-proposal.json','source/v13/map-data.json.zst','source/v15/map-data-C-option.json.zst','source/v15/map-data-ES-option.json.zst','source/physical-routes-v11.json']:
 protected.append(dict(path=p,sha256=sha(P/p),unchanged=(P/p).read_bytes()==(V/p).read_bytes()))
write(OUT/'source/preservation.json',{'protected':protected,'all_unchanged':all(p['unchanged']for p in protected),'game_integration':False,'baseline_zip_sha256':'d914c8d3cd6c0956b4a7c6732d1e8148d1c20f8374eda95e32dccf2b479ca6a9','scope':'Data hashes are preservation evidence, not proof of architectural quality'})
for name in ['scene-design','brands','model-bounds','font-extension']:
 shutil.copy2(P/'source/v17'/(name+'.json'),OUT/'source'/(name+'.json'))
rows=[]
for f in F:
 front=[d for d in D['frontages']if d['wing']==f['wing']and d['floor']==f['label']];items=[d for d in D['instances']if d['wing']==f['wing']and d['floor']==f['label']];count=len({d['id']for d in front});state='店舗正面の仕上げと広告を更新'if front else'開放型屋上のため正面造作なし・既存構造維持';rows.append([f['wing'],f['label'],len(f['stores']),count,len(front),len(items),state,'全域の内装仕上げは未完成'])
csvwrite(OUT/'source/全15層の改善範囲.csv',['館','階','保持店舗ID数','正面更新店舗数','実境界の造作辺数','新モデル配置数','今回の更新','未完成'],rows)
csvwrite(OUT/'source/店舗正面と寸法.csv',['店舗ID','館','階','間口辺長m','始点X','始点Z','終点X','終点Z','仕上げ'],[[r['id'],r['wing'],r['floor'],round(r['length_m'],3),*r['edge'][0],*r['edge'][1],r['material']]for r in D['frontages']])
csvwrite(OUT/'source/什器と施設の配置.csv',['ID','館','階','店舗ID','モデル','X','Y','Z','用途','催事条件','親什器'],[[r['id'],r['wing'],r['floor'],r['store_id'],r['model'],*r['p'],r['role'],r['activation'],r['host']]for r in D['instances']])
csvwrite(OUT/'source/広告と看板の配置.csv',['ID','X','Y','Z','幅m','高さm','画像','催事条件','取り付け先'],[[r['id'],*r['p'],r['w'],r['h'],r['tile'],r['activation'],r['host']]for r in D['boards']])
# Inspection categories remain separate; no human/Windows-GPU results are fabricated.
write(OUT/'source/design-checks.json',{'480_ids_preserved':len(D['preserved_shop_ids'])==480,'unique_ids':len(set(D['preserved_shop_ids'])),'protected_architecture_unchanged':all(p['unchanged']for p in protected),'fitted_bay_design_checks':D['fixture_checks'],'rejected_placements':D['rejected'],'wall_mount_method':'60 accepted existing opaque planes / 198 native rays per bay. Four coarse-pass candidates removed after dense inspection. No cladding used to bridge an unassigned void. Ray sampling is not an exact topological proof.','human_playtest':False,'architectural_quality_is_not_test_count':True})
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as PP
from matplotlib.backends.backend_pdf import PdfPages
with PdfPages(OUT/'plans/v17-15-floor-improvement-map.pdf')as pdf:
 for f in F:
  fig,ax=plt.subplots(figsize=(12,9));world=lambda g:affinity.translate(g,429,-46)
  def draw(g,color,edge='#777',lw=.25):
   for po in polys(g):ax.add_patch(PP(list(po.exterior.coords),facecolor=color,edgecolor=edge,linewidth=lw))
  draw(world(f['floor_plate']),'#e2e3de');draw(world(f['public']),'#f1eadb')
  for s in f['stores']:draw(world(s['polygon']),'#b9c0b3')
  for c in f['cores']:draw(world(c['outline']),'#9e8b80')
  for r in D['frontages']:
   if r['wing']==f['wing']and r['floor']==f['label']:ax.plot(*zip(*r['edge']),color='#316b91',lw=2)
  for r in D['instances']:
   if r['wing']==f['wing']and r['floor']==f['label']and r['host']is None:draw(r['footprint'],'#c36d4e',lw=.5)
  ax.set_aspect('equal');ax.autoscale_view();ax.set_xlabel('Godot world X / m');ax.set_ylabel('Godot world Z / m');ax.set_title('v17 '+f['wing']+' '+f['label']+' / blue: actual frontage finishes / orange: new fitted bays\nOriginal plans, cores, voids and circulation retained; no new structural approval',fontsize=10);fig.tight_layout();pdf.savefig(fig);fig.savefig(OUT/'plans'/(f['wing']+'-'+f['label']+'.svg'));plt.close(fig)
print('REVIEW_DATA',len(protected),'protected',len(rows),'floors',len(D['instances']),'model instances')
