"""Build one complete source-project ZIP; generated caches and local evidence stay out."""
from pathlib import Path
import argparse,hashlib,json,zipfile

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('output',type=Path)
args=parser.parse_args()
excluded_dirs={'.git','.godot','__pycache__','.venv','evidence'}
excluded_files={'audit_v26.gd','audit_v26.gd.uid','probe_v26.gd','probe_v26.gd.uid'}
paths=[]
for path in sorted(root.rglob('*')):
    rel=path.relative_to(root)
    if any(part in excluded_dirs for part in rel.parts) or str(rel)in excluded_files or str(rel)=='PACKAGE-MANIFEST-v27.json':continue
    if path.is_symlink():raise RuntimeError('Unexpected symlink: '+str(rel))
    if path.is_file():paths.append(path)
baseline=json.loads((root/'PACKAGE-MANIFEST-v26.json').read_text())
missing=[r['path']for r in baseline['files']if not(root/r['path']).is_file()]
if missing:raise RuntimeError('Missing v26 base files: '+str(missing))
rows=[{'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in paths]
changed=[r['path']for r in baseline['files']if hashlib.sha256((root/r['path']).read_bytes()).hexdigest()!=r['sha256']]
manifest={'version':27,'standalone':True,'split':False,'main_game_integration':False,'baseline':'v26 published Godot 8b1f0f0c8fcb3b3c343c2a708c1401750eee15ea','baseline_files_missing':missing,'changed_baseline_files':changed,'files':rows}
args.output.parent.mkdir(parents=True,exist_ok=True)
temporary=args.output.with_suffix('.zip.part')
with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
    for p in paths:z.write(p,'FIND_YOURSELF-v27-Godot/'+str(p.relative_to(root)))
    z.writestr('FIND_YOURSELF-v27-Godot/PACKAGE-MANIFEST-v27.json',json.dumps(manifest,ensure_ascii=False,indent=2))
with zipfile.ZipFile(temporary)as z:
    if z.testzip()is not None:raise RuntimeError('ZIP CRC failure')
temporary.replace(args.output)
result={'file':args.output.name,'bytes':args.output.stat().st_size,'sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),'files':len(paths)+1,'CRC_pass':True,'changed_baseline_files':changed,'baseline_files_missing':missing}
print(json.dumps(result,ensure_ascii=False))
