"""Actual Godot captures, sequential isolated software-renderer reference measurement."""
from pathlib import Path
import subprocess,os,json,hashlib,shutil
P=Path(__file__).resolve().parents[1];env=dict(os.environ,DISPLAY=':99',XDG_DATA_HOME='/workspace/.local/share',XDG_CONFIG_HOME='/workspace/.config',XDG_CACHE_HOME='/workspace/.cache')
def run(name,args):
 with open('/tmp/time-v3-'+name+'.log','w')as o:subprocess.run(['godot','--path',str(P),*args],env=env,stdout=o,stderr=subprocess.STDOUT,check=True,cwd=P)
 print('FINISHED',name,flush=True)
run('inspection-final',['--script','res://authoring/capture_inspection.gd','--','--camera-file=res://source/final-cameras.json','--output=res://evidence/after'])
run('cutaway-final',['--script','res://authoring/capture_cutaway.gd','--','--camera-file=res://source/cutaway-cameras.json','--output=res://evidence/cutaway-after'])
run('profile-final',['--script','res://authoring/profile_selected.gd'])
render=P/'evidence/after/render-results.json';b=json.load(open(P/'evidence/profile-results.json'));a=b.copy()
for k in ['geometry_sha256','main_script_sha256','staff_script_sha256','player_script_sha256','animation_script_sha256']:assert a[k]==hashlib.sha256((P/{'geometry_sha256':'assets/geometry.json','main_script_sha256':'main.gd','staff_script_sha256':'staff_doors.gd','player_script_sha256':'player.gd','animation_script_sha256':'escalator_v2.gd'}[k]).read_bytes()).hexdigest(),k
logs=P/'evidence/capture-logs';logs.mkdir(exist_ok=True)
for name in ['inspection-final','cutaway-final','profile-final']:
 q=Path('/tmp/time-v3-'+name+'.log')
 if q.exists():shutil.copy2(q,logs/q.name)
a['capture_run']=str(len(json.load(open(P/'source/final-cameras.json'))))+' final camera captures through capture_inspection.gd; first eight poses unchanged; separate final-version measurement';a['screenshot_kind']='actual Godot 3D viewport; no image generation or retouch';a['npc_count']=0;a['camera_contract']='source/final-cameras.json';render.write_text(json.dumps(a,ensure_ascii=False,indent=2))
receipt={'geometry_sha256':a['geometry_sha256'],'main_script_sha256':a['main_script_sha256'],'cameras':json.load(open(P/'source/final-cameras.json')),'images':[{'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in sorted((P/'evidence/after').glob('*.png'))]}
(P/'evidence/after/viewport-capture-results.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2));print('CAPTURE_PIPELINE_COMPLETE',flush=True)
