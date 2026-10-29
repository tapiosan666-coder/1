"""Extend the existing Noto JP subset for new Japanese review/UI text; preserve every original glyph outline and advance."""
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter,Options
from fontTools.pens.recordingPen import RecordingPen
import hashlib,json
P=Path(__file__).resolve().parents[1];path=P/'assets/NotoSansCJKjp-Regular.otf';old=TTFont(path);full=TTFont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',fontNumber=0);a=old.getBestCmap();b=full.getBestCmap();assert 'JP'in full['name'].getDebugName(4)
old_glyphs=old.getGlyphSet();new_glyphs=full.getGlyphSet()
for cp,name in a.items():
 if cp not in b:raise RuntimeError('Missing original codepoint')
 assert old['hmtx'][name]==full['hmtx'][b[cp]],cp
 pen=RecordingPen();old_glyphs[name].draw(pen);other=RecordingPen();new_glyphs[b[cp]].draw(other);assert pen.value==other.value,cp
chars=set(a)
for f in list(P.glob('*.gd'))+[P/'README.md']+list((P/'authoring').glob('v17_*.py')):
 chars.update(ord(c)for c in f.read_text())
for f in(P/'source/v17').glob('*.json'):chars.update(ord(c)for c in f.read_text())
chars={c for c in chars if c in b};before=hashlib.sha256(path.read_bytes()).hexdigest();options=Options();options.layout_features=['*'];sub=Subsetter(options=options);sub.populate(unicodes=chars);sub.subset(full);full.save(path);result={'before_sha256':before,'after_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'original_codepoints':len(a),'new_codepoints':len(chars),'all_original_outlines_and_advances_preserved':True,'source':'System Noto Sans CJK JP, existing project font family; existing OFL license retained','only_adds_glyphs':True};(P/'source/v17/font-extension.json').write_text(json.dumps(result,indent=2));print('V17_FONT',result)
