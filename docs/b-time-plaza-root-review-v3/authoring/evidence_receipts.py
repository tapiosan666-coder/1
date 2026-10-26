"""Bind comparison PNGs to source, camera, and actual Godot capture logs."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parents[1];E=P/'evidence';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();runtime=json.load(open(E/'after/render-results.json'));cam=json.load(open(P/'source/final-cameras.json'));cut=json.load(open(P/'source/cutaway-cameras.json'))
for key,n in [('main_script_sha256','main.gd'),('geometry_sha256','assets/geometry.json'),('player_script_sha256','player.gd'),('staff_script_sha256','staff_doors.gd')]:assert runtime[key]==sha(P/n),key
normal=[]
for c in cam:
 a=E/'after'/(c['id']+'.png');b=E/'before-v2'/(c['id']+'.png');assert a.exists()and b.exists();normal.append({'id':c['id'],'camera':c,'before_sha256':sha(b),'after_sha256':sha(a),'kind':'actual normal Godot Viewport; no repainting/generation','automated_staff_open':c.get('open_staff',False)})
technical=[]
for c in cut:
 a=E/'cutaway-after'/(c['id']+'.png');b=E/'cutaway-before'/(c['id']+'.png');assert a.exists()and b.exists();technical.append({'id':c['id'],'camera':c,'before_sha256':sha(b),'after_sha256':sha(a),'kind':'actual diagnostic Godot Viewport; 1.25m clip/orthographic; NOT ordinary gameplay graphics'})
receipt={'normal_count':len(normal),'diagnostic_count':len(technical),'runtime':runtime,'normal':normal,'technical':technical,'materials':{n:sha(P/n)for n in ['stone.gdshader','material_library.gd']},'limitations':['Not human operation','Software renderer llvmpipe, not RTX4060','B1/RF and 18 large/anchor plots are plan-only','Current elevator functional count zero; proposals not implemented']}
(E/'screenshot-provenance.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2));print('PROVENANCE',len(normal),len(technical))
