from pathlib import Path
import subprocess,os,json,hashlib
P=Path(__file__).resolve().parents[1];env=dict(os.environ,DISPLAY=':99',XDG_DATA_HOME='/workspace/.local/share',XDG_CONFIG_HOME='/workspace/.config',XDG_CACHE_HOME='/workspace/.cache')
for name,args in [('after',['--script','res://authoring/capture_inspection.gd','--','--camera-file=res://source/followup-all-cameras.json','--output=res://evidence/after']),('profile',['--script','res://authoring/profile_selected.gd'])]:
 with open('/tmp/find-v4-'+name+'.log','w')as log:subprocess.run(['godot','--path',str(P),*args],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 print('DONE',name,flush=True)
(P/'evidence/after/render-results.json').write_text((P/'evidence/profile-results.json').read_text())
print('CAPTURE_COMPLETE',flush=True)
