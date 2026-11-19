"""Fit freestanding feature cases into actual sales polygons; dimensions in metres.

Requires shapely >= 2.0 and the zstd CLI. Exclusions combine both legacy and
replacement plans, which deliberately errs on the side of a clear shop floor.
"""
from pathlib import Path
from collections import defaultdict, Counter
import json, math, subprocess, zlib
from shapely.geometry import Polygon, LineString, Point, shape
from shapely import STRtree
from shapely.prepared import prep

PROJECT = Path(__file__).resolve().parents[3]
def read(name):
    data = (PROJECT / name).read_bytes()
    if data[:4] == b'FYJZ':
        data = subprocess.run(['zstd', '-dc'], input=data[8:], stdout=subprocess.PIPE, check=True).stdout
    return json.loads(data)
def world_line(pts):
    return [(p[0],p[-1]) for p in pts]
def border_edges(region):
    polys = [region] if region.geom_type == 'Polygon' else region.geoms
    for poly in polys:
        points = list(poly.exterior.coords)
        for a,b in zip(points,points[1:]):
            length = math.dist(a,b)
            if length > 1.65:
                yield a,b,length
def rect(x,z,tx,tz,nx,nz,width,depth,extend=0):
    return Polygon([(x+a*width/2*tx+(b*depth/2+f)*nx,z+a*width/2*tz+(b*depth/2+f)*nz)
                    for a,b,f in ((-1,-1,0),(1,-1,0),(1,1,extend),(-1,1,extend))])
def clear(point,exclusions):
    return len(exclusions.query(point,predicate='intersects')) == 0
def layout(store, blocks, facing, protected):
    sales=shape(store['sales_world']).buffer(0)
    entry=Point(store['entry_world']); sid=store['id']; y=store['height']
    if sales.area < 4: return []
    cap=sales.buffer(-.06)
    safe=prep(cap)
    forbidden = list(blocks) + protected
    # Exact customer and rear access envelopes remain free of solids.
    mask=shape(store['protected_aisles_world']).buffer(.06)
    if not mask.is_empty: forbidden.append(mask)
    if store.get('backroom_world'): forbidden.append(shape(store['backroom_world']).buffer(.18))
    route=world_line(store.get('main_route_world',[]))
    if len(route)>1: forbidden.append(LineString(route).buffer(.66))
    forbidden.append(entry.buffer(1.8))
    exclusions=STRtree(forbidden)
    # Opportunistically scan the existing perimeter; no wall or access changes.
    candidates=[]
    for a,b,length in border_edges(sales):
        tx,tz=(b[0]-a[0])/length,(b[1]-a[1])/length
        mx,mz=(a[0]+b[0])/2,(a[1]+b[1])/2
        nx,nz=-tz,tx
        if not sales.contains(Point(mx+.12*nx,mz+.12*nz)): nx,nz=-nx,-nz
        for i in range(max(1,math.floor(length/1.45))):
            t=(i+.5)/max(1,math.floor(length/1.45))
            ox,oz=a[0]+tx*t*length,a[1]+tz*t*length
            distance=entry.distance(Point(ox,oz))
            # A rear display should face the accessible interior. Front displays
            # stand inside the showroom rather than obstruct the public threshold.
            for width in (2.62,1.88):
                for setback in (.76,1.04):
                    x,z=ox+setback*nx,oz+setback*nz
                    footprint=rect(x,z,tx,tz,nx,nz,width,.79)
                    browse=rect(x,z,tx,tz,nx,nz,width+.16,.83,1.03)
                    if not safe.covers(browse) or not clear(browse,exclusions): continue
                    # Require a direct line from the customer's own sales area
                    # to the frontage, with a choice of edge if a shelf occupies it.
                    view=(entry.x-x)*nx+(entry.y-z)*nz
                    candidates.append((x,z,nx,nz,width,distance,view,footprint,browse))
                    break
                else: continue
                break
    if not candidates:return []
    chosen=[]
    # Rear areas fitted by the authored v35/v36 designer keep their own collection.
    for role in (['arrival'] if sid=='A1F-051' else ['arrival','gallery']):
        valid=[c for c in candidates if all(c[8].distance(d[8])>2.25 for d in chosen)]
        if role=='gallery':
            valid=[c for c in valid if c[5]>4.5 and c[6]>-1.2]
        if not valid:continue
        if role=='arrival':
            viable=[c for c in valid if c[5]<16]
            if not viable:continue
            choice=min(viable,key=lambda c:abs(c[5]-4.4) + max(-c[6],0)*1.7 - .25*c[4])
        else:
            target=min(32,max(6, math.sqrt(sales.area)*.87))
            choice=min(valid,key=lambda c:abs(c[5]-target) - min(c[6],8)*.09 - .33*c[4])
        chosen.append((*choice,role))
    return [dict(role=c[9],p=[round(c[0],3),round(y+.031,3),round(c[1],3)],yaw=round(math.atan2(c[2],c[3]),5),
                 width=c[4],distance_to_entry=round(c[5],2)) for c in chosen]
def main():
    plan=read('source/v294/retail-plan.json.zst')
    extras=read('source/v32/sales-design.json')
    blocks=defaultdict(list)
    for item in plan['fixtures']:
        if item.get('footprint'): blocks[item['store_id']].append(shape(item['footprint']).buffer(.15))
    for s in extras['stores']:
        for f in s['placements']:
            blocks[s['id']].append(shape(f['footprint']).buffer(.20))
        blocks[s['id']].append(shape(s['protected']).buffer(.05))
    for route in read('source/v21/store-walk-routes.json'):
        pts=world_line(route['points'])
        if len(pts)>1: blocks[route['store_id']].append(LineString(pts).buffer(.46))
    for sid,x,z in [('A1F-051',321.25,-67.05),('B1-022',-19.4,42.8)]:
        blocks[sid].append(Point(x,z).buffer(2.2))
    people=defaultdict(list)
    for npc in read('source/v19/shoppers.json')['people']:
        coords=[]
        for k in ('p','stand_point','home_point','seat_point'):
            if k in npc: coords.append(world_line([npc[k]])[0])
        for k in ('route','path'):
            if k in npc and isinstance(npc[k],list): coords.extend(world_line(npc[k]))
        if coords: people[(npc['wing'],npc['floor'])].append((LineString(coords) if len(coords)>1 else Point(coords[0])).buffer(.78))
    fronts={x['store_id']:x for x in read('source/brands-v11.json')}
    output=[]
    for s in plan['stores']:
        sid=s['id']; rows=layout(s,blocks[sid],fronts[sid],people[(s['wing'],s['floor'])])
        output.append(dict(id=sid,wing=s['wing'],floor=s['floor'],category=s['category'],original_category=s['original_category'],
            brand=s['brand'],variant=zlib.crc32(s['brand'].encode())%3,placements=rows))
    # The first-floor rebuild already occupies many entire wall lines. Refit
    # ordinary dated merchandise fixtures within their own envelope instead of
    # adding another stand in a customer aisle. Do not retire specialist cases,
    # functioning checkouts/fitting rooms or previously composed v35 counters.
    by_id={s["id"]:s for s in output}
    v34_replaced=read("source/v34/retail-edit.json")["replacements"]
    refits={}
    for store in extras["stores"]:
        row=by_id[store["id"]]
        entry=store["entry"]
        valid=[]
        for f in store["placements"]:
            if not f["role"].startswith(("wall_","central_")):continue
            if f["id"] in v34_replaced.get(store["id"],{}):continue
            if any(word in f["asset"] for word in ("chair","banquette","table_set","window_bar","vitrine","kitchen","cash","fitting","v34/","v32/models/wall_")):continue
            if store["id"]=="A1F-051" and f["id"][-3:].isdigit() and 5<=int(f["id"][-3:])<=14:continue
            b=f["bounds"];w,h,d=b["size"]
            if w<1.18 or d<.43 or h<.56:continue
            dist=math.hypot(f["p"][0]-entry[0],f["p"][2]-entry[2])
            valid.append((f,dist))
        chosen=[]
        for role in ("arrival","gallery"):
            if role in [r["role"] for r in row["placements"]]:continue
            if role=="gallery" and store["id"]=="A1F-051":continue
            eligible=[(f,d) for f,d in valid if f["id"] not in chosen and (f["role"].startswith("wall_") or role=="arrival") and
                      (d>5 if role=="gallery" else d<16)]
            if not eligible:continue
            f,d=min(eligible,key=lambda k:abs(k[1]-(min(29.,math.sqrt(store['sales_m2'])*.8) if role=="gallery" else 4.5)))
            chosen.append(f["id"]); b=f["bounds"];w,h,depth=b["size"]; bx,by,bz=b["p"]
            scale=[min(1.,(w-.025)/2.58), min(1.,(h-.008)/(2.27 if role=="gallery" else 1.52)),min(1.,(depth-.025)/.74)]
            if min(scale)<.40:continue
            dx=bx+w/2; dz=bz+depth/2; yaw=f["yaw"]
            py=float(next(s["height"] for s in plan["stores"] if s["id"]==store["id"]))+.018
            cx=f["p"][0]+math.cos(yaw)*dx+math.sin(yaw)*dz; cz=f["p"][2]-math.sin(yaw)*dx+math.cos(yaw)*dz
            local=[dx,py-f["p"][1],dz]
            uid=f["id"]
            refits[uid]={"mesh":row["category"]+"-"+role+"-"+str(row["variant"]),"scale":scale,"offset":local,
                         "old_asset":f["asset"],"role":role,"variant":row["variant"]}
            row["placements"].append({"role":role,"p":[round(cx,3),round(py,3),round(cz,3)],"yaw":yaw,"width":scale[0]*2.58,
                                      "distance_to_entry":round(d,2),"refit":uid})
    for store in extras["stores"]:
        if store["category"]!="restaurant":continue
        kitchens=[f for f in store["placements"] if f["asset"].endswith("fixture_v23_supported_kitchen")]
        if len(kitchens)<5:continue
        # Some old dining rooms have eleven contiguous identical kitchens. Keep
        # the service counter and cooking areas; convert selected existing bays
        # to banquette dining without touching the aisle or shop boundary.
        row=by_id[store["id"]]; center=store["entry"]; remaining=[f for f in kitchens if f["id"] not in refits]
        remaining.sort(key=lambda f:math.hypot(f["p"][0]-center[0],f["p"][2]-center[2]))
        for f in remaining[1:1+min(4,len(kitchens)-3)]:
            b=f["bounds"];w,h,d=b["size"]; bx,by,bz=b["p"]
            scale=[min(1.,(w-.025)/2.58),min(1.,(h-.01)/1.36),min(1.,(d-.025)/1.0)]
            dx=bx+w/2; dz=bz+d/2; yaw=f["yaw"]
            level=float(next(s["height"] for s in plan["stores"] if s["id"]==store["id"]))+.018
            cx=f["p"][0]+math.cos(yaw)*dx+math.sin(yaw)*dz; cz=f["p"][2]-math.sin(yaw)*dx+math.cos(yaw)*dz
            uid=f["id"]
            refits[uid]={"mesh":"restaurant-dining-"+str(row["variant"]),"scale":scale,"offset":[dx,level-f["p"][1],dz],
                         "old_asset":f["asset"],"role":"dining","variant":row["variant"]}
            row["placements"].append({"role":"dining","p":[round(cx,3),round(level,3),round(cz,3)],"yaw":yaw,"width":scale[0]*2.58,
                                      "distance_to_entry":round(math.hypot(cx-center[0],cz-center[2]),2),"refit":uid})
    (PROJECT/"source/v36/store-refits.json").write_text(json.dumps(refits,separators=(",",":"))+"\n")
    out=PROJECT/'source/v36/store-studios.json' 
    out.write_text(json.dumps(output,ensure_ascii=False,separators=(',',':'))+'\n')
    print('Stores',len(output),'stations',sum(len(s['placements']) for s in output),'by count',Counter(len(s['placements']) for s in output))
    print('No fit:',[s['id'] for s in output if not s['placements']])
if __name__=='__main__':main()
