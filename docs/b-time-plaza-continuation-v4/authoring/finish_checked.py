"""Resume final checks after an already completed rebuild/AO; no writes to baseline projects."""
from pathlib import Path
import subprocess,json,hashlib,os
P=Path(__file__).resolve().parents[1];env=dict(os.environ,XDG_DATA_HOME='/workspace/.local/share',XDG_CONFIG_HOME='/workspace/.config',XDG_CACHE_HOME='/workspace/.cache')
def run(name,args):
 with open('/tmp/find-v4-final-'+name+'.log','w')as log:subprocess.run(args,cwd=P,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 print('FINAL_DONE',name,flush=True)
run('service',['godot','--headless','--fixed-fps','60','--path',str(P),'--script','res://authoring/service_qa.gd'])
run('walk',['godot','--headless','--fixed-fps','60','--path',str(P),'--','--walk-test'])
run('captures',['python',str(P/'authoring/capture_followup.py')])
run('independent',['python',str(P/'authoring/verify_followup.py')]);run('privacy',['python',str(P/'authoring/check_stock_glass.py')]);print('FINAL_REBUILD_AND_CHECK_COMPLETE',flush=True)
