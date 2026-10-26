"""Proposal-only lift/escalator details; no source architecture or runtime geometry writes."""
from pathlib import Path
import json,html
P=Path(__file__).resolve().parents[1];O=P/'source/vertical-review';d=json.load(open(O/'vertical-review.json'))
def begin(w=1100,h=650):return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><rect width="100%" height="100%" fill="#fff"/>']
def text(a,x,y,s,size=16,color='#223c36'):a.append(f'<text x="{x}" y="{y}" font-family="sans-serif" font-size="{size}" fill="{color}">{html.escape(str(s))}</text>')
def line(a,x,y,xx,yy,c='#536660',w=2):a.append(f'<path d="M{x},{y} L{xx},{yy}" fill="none" stroke="{c}" stroke-width="{w}"/>')
def rect(a,x,y,w,h,c,stroke='#444'):a.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{c}" stroke="{stroke}" stroke-width="1"/>')
def save(n,a):(O/n).write_text('\n'.join(a+['</svg>']))
a=begin();text(a,30,32,'TIME / 2F transfer plan: current vs stacked-bank proposal (NOT BUILT)',22)
for shift,kind in [(50,'old'),(620,'new')]:
 text(a,shift,70,'CURRENT'if kind=='old'else'PROPOSED: same-axis stacked pairs',18);scale=8 if kind=='new' else 6
 def xy(x,z):return shift+(x+460)*scale,110+(z-49)*scale
 for e in d['escalator_proposal']:
  cx,cz=e[kind+'_center'];x,y=xy(cx,cz);levels=e['levels'];col='#6eb8a9'if levels==[0,1]else'#d8a86a';rect(a,x-1.2*scale,y-7.4*scale,2.4*scale,14.8*scale,col)
  for sg in[-1,1]:rect(a,x-1.8*scale,y+(sg*8.9-1.5)*scale,3.6*scale,3*scale,'none','#777')

  if kind=='old' and e['direction']=='UP':text(a,x-25,y-65,('12 UP/DN'if levels==[0,1]else'23 UP/DN'),11)
  elif kind=='new' and levels==[0,1] and e['direction']=='UP':text(a,x-25,y-75,'12 + 23 UP/DN (stacked)',11)
 # Route rendered from separately verified plan nodes.
 route=next(q['points_world_xz'] for q in d['transfer_comparison'] if q['kind']==kind.upper())
 if route:
  pts=[xy(q[0],q[1])for q in route];a.append('<polyline points="'+' '.join(f'{x},{y}'for x,y in pts)+'" fill="none" stroke="#a92c29" stroke-width="3"/>')
 text(a,shift,380,('Old CAD route 50.89 m'if kind=='old'else'Proposed CAD route 20.06 m'),18)
 text(a,shift,410,'Run 11.8 / body 14.8 / width 2.4 m',13)
 text(a,shift,438,'Landing 3.0 x 3.6 m / no receiving-floor comb cut',13)
text(a,35,510,'1->2 pair stays. 2->3 pair moves above it. Same travel axis prevents bank collision at 2F.',15)
text(a,35,540,'CAD path is not an implemented walking result. Main atrium and public route remain protected.',15)
save('TIME-transfer-proposal-detail.svg',a)
a=begin();text(a,30,32,'TIME / stacked escalator longitudinal section (PROPOSAL ONLY)',22)
# Same-axis banks separated by a full floor, not intersecting opposite-axis ramps.
xs=180;sc=27;ys=lambda y:535-y*sc
for y,label in [(0,'1F +0.000'),(5.525,'2F +5.525'),(10.875,'3F +10.875')]:
 line(a,50,ys(y),125,ys(y),'#4b6159',4);line(a,717,ys(y),1030,ys(y),'#4b6159',4);
 if y==0:line(a,125,ys(y),717,ys(y),'#4b6159',4)
 text(a,770,ys(y)-10,label,17)
# use positive coordinate scaled from 0..14.8 so keep plot inbounds
xs=185
for low,hi,col in [(0,5.525,'#468c7c'),(5.525,10.875,'#b67a34')]:
 x0=xs;x1=xs+11.8*40
 line(a,x0,ys(low),x1,ys(hi),col,18);line(a,x0,ys(low+1),x1,ys(hi+1),'#536660',2)
 line(a,x0-60,ys(low),x0,ys(low),col,6);line(a,x1,ys(hi),x1+60,ys(hi),col,6)
text(a,35,585,'Upper receiving floor: ramp opening only. Lower floor and 1.5 m combs stay supported.',15)
text(a,35,614,'Nominal underside clearance 5.35 - 0.85 = 4.50 m; structure/headroom/fire safety NOT VERIFIED.',15)
save('TIME-stacked-section-proposal.svg',a)
a=begin();text(a,30,32,'Lift additions / five-level section and lobby (PROPOSAL ONLY)',22)
levels=[(-5.35,'B1'),(0,'1F'),(5.525,'2F'),(10.875,'3F'),(16.4,'RF')];y=lambda v:510-(v+5.35)*18
rect(a,190,y(17.8),140,y(-6.4)-y(17.8),'#e4efea')
for yy,lab in levels:
 line(a,60,y(yy),188,y(yy),'#4d665b',4);line(a,332,y(yy),550,y(yy),'#4d665b',4);text(a,580,y(yy)+5,f'{lab}  {yy:+.3f} m',16);rect(a,330,y(yy)-40,90,40,'none');text(a,430,y(yy)-16,'lobby',13)
rect(a,207,y(5.525)-47,105,47,'#96b8a5');text(a,218,y(5.525)-20,'CAR',15)
text(a,715,110,'Shaft: 4.0 x 4.0 m',17);text(a,715,145,'Lobby: 3.6 x 2.4 m',17);text(a,715,180,'Door target: 1.4 m',17);text(a,715,215,'Car target: 2.0 x 2.4 m',17)
text(a,715,275,'B1/RF access: unresolved',16,'#a43e2b');text(a,715,305,'No sales/stall/vehicle overlap',15);text(a,715,335,'Program redistribution pending',15);text(a,715,375,'Pit / overhead / manufacturer',15);text(a,715,402,'structure / controls: NOT VERIFIED',15)
text(a,35,585,'K4 central-west (-506.100, 70.208); K5 east (-235.000, 58.000). World X/Z metres.',15)
text(a,35,615,'All five landing openings align in plan. Drawings and Godot have NOT been changed.',15)
save('lift-five-level-section-proposal.svg',a)
print('PROPOSAL_DETAILS_WRITTEN')
