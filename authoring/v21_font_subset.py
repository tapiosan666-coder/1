from pathlib import Path
import os
from fontTools import subset
from fontTools.ttLib import TTFont
P=Path(__file__).resolve().parents[1];target=P/'assets/NotoSansCJKjp-Regular.otf';old=TTFont(target);codes=set(old.getBestCmap());text=''
for pattern in ['*v21.gd','main.gd','ui_v7.gd','source/v21/*.json']:
 for f in P.glob(pattern):text+=f.read_text()
codes.update(map(ord,text));font=TTFont(os.environ.get('FY_FULL_NOTO_FONT','/workspace/FIND_YOURSELF-Site-v10/assets/NotoSansCJKjp-Regular.otf'));opt=subset.Options();opt.layout_features=['*'];s=subset.Subsetter(options=opt);s.populate(unicodes=codes);s.subset(font)
for r in font['name'].names:
 if r.nameID in[1,4,6,16,17]:r.string=('FYValidationUIv21'if r.nameID==6 else'FY Validation UI v21'if r.nameID in[1,4,16]else'Regular').encode(r.getEncoding())
font.save(target);print('FY21_FONT',len(font.getBestCmap()),target.stat().st_size)
