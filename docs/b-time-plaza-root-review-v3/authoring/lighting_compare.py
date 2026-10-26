"""Image-code luminance comparison, not photometry or a comfort pass."""
from pathlib import Path
import json,sys,hashlib
sys.path.insert(0,'/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];rows=[]
for id in ['01-1F-arrival','03-2F-gallery','05-3F-gallery','27-3F-daylight-corridor']:
 # Resolve standard basic names by prefix rather than inventing alternate names.
 prefix=id[:2]+'-';file=next(p.name for p in(P/'evidence/after').glob(prefix+'*.png'))
 r={'id':file,'measurement':'sRGB code-value luma, central y=100..650; NOT nits/lux; no HDR photometry','camera_resolution_quality_fixed':True}
 for key,folder in [('before','before-v2'),('after','after')]:
  p=P/'evidence'/folder/file;a=np.asarray(Image.open(p).convert('RGB'),dtype=float)[100:650,:,:]/255.;y=a@np.array([.2126,.7152,.0722]);r[key]={'mean_srgb_luma':float(y.mean()),'median_srgb_luma':float(np.median(y)),'p95_srgb_luma':float(np.quantile(y,.95)),'near_white_percent':float(np.all(a>.98,axis=2).mean()*100),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 rows.append(r)
d={'comparisons':rows,'limitations':'Not isolated lighting-only experiment: some shops/geometry also changed. Same camera/quality; no physical luminance or human discomfort pass.','light_settings':{'sun_before':.65,'sun_after':.12,'ambient_before':.78,'ambient_after':.70,'exposure_both':.90,'filmic_both':True,'floor_min_roughness_after':.58,'floor_specular_after':.26}}
(P/'evidence/lighting-comparison.json').write_text(json.dumps(d,ensure_ascii=False,indent=2));print(json.dumps(rows[-1],indent=2))
