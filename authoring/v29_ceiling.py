import sys,json,math
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from v29_blender_common import *
cream=material('V29_acoustic_plaster',(.72,.71,.65),.90)
glow=material('V29_recessed_opal',(.88,.83,.69),.40);pr=glow.node_tree.nodes.get('Principled BSDF');pr.inputs['Emission Color'].default_value=(1,.85,.65,1);pr.inputs['Emission Strength'].default_value=1.8
for wing in 'ABC':
 if wing=='A':
  box('Acoustic_raft',(0,0,-.08),(4.0,1.18,.16),cream,.05)
  for y in [-.56,.56]:
   box('Brass_shadow_reveal',(0,y,-.15),(3.9,.025,.04),brass,.005);box('Recessed_linear_diffuser',(0,y*.90,-.167),(3.72,.035,.018),glow,.004)
  for x in [-1.62,1.62]:
   for j in range(8):box('Linear_air_diffuser',(x,-.18+j*.05,-.168),(.26,.018,.018),metal,.003)
 elif wing=='B':
  # Smooth reflecting ellipse with raised edge, not a faceted primitive disk.
  v=[];f=[]
  for j,(r,z)in enumerate([(1,-.03),(.98,-.12),(.94,-.17),(.85,-.14),(0,-.14)]):
   for k in range(96):a=k*math.tau/96;v.append((1.8*r*math.cos(a),.92*r*math.sin(a),z))
  for j in range(4):
   for k in range(96):a=j*96+k;b=j*96+(k+1)%96;f.append((a,b,b+96,a+96))
  mesh('Elliptical_acoustic_reflector',v,f,cream)
  pts=[(1.7*math.cos(a*math.tau/48),.84*math.sin(a*math.tau/48),-.17)for a in range(49)];tube('Continuous_LED_cove',pts,.014,glow)
  for x in [-.9,.9]:
   for j in range(6):box('Radial_HVAC_grille',(x,-.16+j*.045,-.155),(.30,.018,.025),metal,.003)
 else:
  for x in range(-8,9):box('Outdoor_cedar_batten',(x*.19,0,-.13),(.065,2.65,.23),wood,.012)
  for x in [-1.4,1.4]:box('Exterior_sheltered_linear_light',(x,0,-.20),(.035,2.45,.025),glow,.004)
 for x in [-1.,1.]:
  lathe('Recessed_downlight_trim',[(.065,0),(.075,.015),(.075,.025),(.05,.03)],brass,(x,0,-.22))
  lathe('Downlight_opal_lens',[(.053,0),(.053,.015)],glow,(x,0,-.23))
 finish('ceiling_v29_'+wing)
