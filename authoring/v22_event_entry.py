from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from v22_blender_common import *
for x in [-5.8,5.8]:
 box('Weighted_plinth',(x,0,.06),(.52,.60,.12),metal,.025);tube('Event_mast',[(x,0,.1),(x,0,4.0)],.045,steel);tube('Banner_tie',[(x,0,3.80),(x*.8,0,3.80)],.018,brass)
tube('Demountable_banner_rail',[(-5.8,0,3.9),(5.8,0,3.9)],.045,steel);finish('event_entry_portal')
