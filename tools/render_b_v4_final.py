"""Render addendum cameras in a separate model; no Godot imports or scene changes."""
from pathlib import Path
ROOT=Path('/workspace/1');p=ROOT/'tools/render_b_v4_views.py';s=p.read_text()
s=s.replace("OUT=ROOT/'docs/b-purpose-review-v4'","OUT=ROOT/'docs/b-v4-final-confirmation'")
s=s.replace('resolution_x=1400','resolution_x=1100').replace('resolution_y=900','resolution_y=720').replace("render_aa='16'","render_aa='8'")
s=s.replace("'plaster':material('Warm wall'","'closed':material('Closed band wall',(.79,.77,.71)),'staff':material('Staff door',(.56,.58,.57)),'finish':material('Flush finish',(.65,.70,.68)),'finish_panels':material('Management information',(.28,.40,.43)),'plaster':material('Warm wall'")
s=s.replace("o.data.materials.append(clockmat)\n light=", "o.data.materials.append(clockmat);o['finish_only']=label.get('finish_only',False)\n light=")
s=s.replace("bpy.data.objects['roof'].hide_render=(camera['id']=='axon')", "bpy.data.objects['roof'].hide_render=False\n  for obj in scene.objects:\n   if obj.name.startswith('finish')or obj.get('finish_only',False):obj.hide_render=(camera['phase']=='before')")
s=s.replace('roof_omitted_in_axon=True','roof_omitted_in_axon=False')
exec(compile(s,str(p),'exec'),{'__file__':str(Path(__file__).resolve())})
