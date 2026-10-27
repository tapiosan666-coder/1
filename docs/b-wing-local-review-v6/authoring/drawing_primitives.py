def page(title, sub='', w=1190, h=842):
    p = doc.new_page(width=w, height=h)
    p.insert_font(fontname='JP', fontfile=str(fontfile))
    p.draw_rect(p.rect, fill=(0.99, 0.99, 0.97), color=None)
    text(p, 35, 25, w - 70, 45, title, 22)
    text(p, 35, 72, w - 70, 42, sub, 10)
    text(p, 35, h - 30, w - 70, 20, f'FIND YOURSELF | B館 街区再構成 v5 | 2026-10-27 | 独立検証・未統合 | {len(doc)}', 8)
    return p

def text(p, x, y, w, h, s, size=11, color=ink):
    r = p.insert_textbox(fitz.Rect(x, y, x + w, y + h), str(s), fontname='JP', fontsize=size, color=color, lineheight=1.35)
    while r < 0 and size > 5.5:
        size -= 0.25
        r = p.insert_textbox(fitz.Rect(x, y, x + w, y + h), str(s), fontname='JP', fontsize=size, color=color, lineheight=1.3)
    if r < 0:
        print('TEXT_OVERFLOW', str(s)[:90], size, r)
    return r

def paragraphs(title, ps):
    p = page(title, '設計・生成ルールと未検証事項を区別して記載')
    y = 135
    for heading, body in ps:
        text(p, 40, y, 1110, 35, heading, 16, green)
        y += 38
        h = max(52, math.ceil(len(body) / 77) * 18)
        text(p, 40, y, 1110, h, body, 12)
        y += h + 22
    return p

def table(title, headers, rows, widths=None, rowsper=26, notes=''):
    w = 1190
    cols = len(headers)
    widths = widths or [(w - 80) / cols] * cols
    for start in range(0, len(rows), rowsper):
        p = page(title + f'  {start + 1}–{min(len(rows), start + rowsper)} / {len(rows)}', notes)
        y = 128
        x = 40
        for head, cw in zip(headers, widths):
            p.draw_rect(fitz.Rect(x, y, x + cw, y + 35), fill=(0.15, 0.28, 0.25), color=None)
            text(p, x + 5, y + 5, cw - 10, 30, head, 9, (1, 1, 1))
            x += cw
        y += 35
        for ri, row in enumerate(rows[start:start + rowsper]):
            x = 40
            hh = min(32, (690 - y) / max(1, len(rows[start:start + rowsper]) - ri))
            for val, cw in zip(row, widths):
                p.draw_rect(fitz.Rect(x, y, x + cw, y + hh), fill=(0.94, 0.96, 0.94) if ri % 2 == 0 else (1, 1, 1), color=(0.77, 0.81, 0.79), width=0.25)
                text(p, x + 4, y + 3, cw - 8, hh - 3, val, 8)
                x += cw
            y += hh

def plan(p, f, rect, bounds=None, before=False, detail=False):
    x0, z0, x1, z1 = bounds or f['old_floor_plate'].union(f['floor_plate']).bounds if not before else bounds or f['floor_plate'].bounds
    box0 = fitz.Rect(rect)
    pad = 20
    sc = min((box0.width - 2 * pad) / (x1 - x0), (box0.height - 2 * pad) / (z1 - z0))
    ox = box0.x0 + (box0.width - (x1 - x0) * sc) / 2
    oz = box0.y0 + (box0.height - (z1 - z0) * sc) / 2
    clip = box(x0, z0, x1, z1)

    def pt(q):
        return fitz.Point(ox + (q[0] - x0) * sc, oz + (q[1] - z0) * sc)

    def geom(g, fill=None, color=None, width=0.5):
        g = unary_union(polys(g.intersection(clip)))
        sh = p.new_shape()
        for a in polys(g):
            if a.area < 1e-06:
                continue
            for ring in [a.exterior, *a.interiors]:
                sh.draw_polyline([pt(q) for q in ring.coords])
        sh.finish(color=color, fill=fill, width=width, even_odd=True, closePath=True)
        sh.commit()
    geom(f['floor_plate'], (0.94, 0.93, 0.88), (0.4, 0.42, 0.4), 0.4)
    geom(f['public'], (0.98, 0.965, 0.9), None)
    if before:
        assigned = unary_union([f['public'], f['void'], f['shafts'], f.get('egress', Polygon()), *[q['outline'] for q in f['cores']], *[s['polygon'] for s in f['stores']], *[q['polygon'] for q in f['service_zones']]])
        geom(f['floor_plate'].difference(assigned), (0.94, 0.65, 0.6), (0.72, 0.32, 0.26), 0.4)
    else:
        geom(f['old_floor_plate'].difference(f['floor_plate']), None, (0.72, 0.44, 0.4), 0.5)
    for c in f['cores']:
        geom(c['outline'], (0.78, 0.82, 0.84), (0.31, 0.36, 0.39), 0.6)
    for room in f['service_zones']:
        geom(room['polygon'], (0.8, 0.79, 0.73), (0.36, 0.36, 0.33), 0.7)
    for s in f['stores']:
        if not s['polygon'].intersects(clip):
            continue
        geom(s['sales'], (0.79, 0.88, 0.82), (0.25, 0.39, 0.33), 0.65)
        geom(s['backroom'], (0.89, 0.81, 0.65), (0.43, 0.36, 0.25), 0.6)
        if not before:
            geom(s['work_rectangle'], None, (0.18, 0.42, 0.68), 0.65)
            if detail:
                for fp in SCENE.get('fixture_footprints', {}).get(s['id'], []):
                    geom(fp, (0.71, 0.66, 0.56), None)
                pts = s.get('main_route', [])
                for aa, bb in zip(pts, pts[1:]):
                    if clip.covers(LineString([aa, bb])):
                        p.draw_line(pt(aa), pt(bb), color=(0.2, 0.43, 0.65), width=0.5)
        for key, uk, wk in [('entry', 'u', 'door_width_m'), ('back_door', 'back_door_u', 'back_door_width_m')]:
            if key not in s:
                continue
            e = s[key]
            u = s.get(uk, s['u'])
            ww = s.get(wk, 2.4 if key == 'entry' else 1.5)
            a = [e[0] - u[0] * ww / 2, e[1] - u[1] * ww / 2]
            b = [e[0] + u[0] * ww / 2, e[1] + u[1] * ww / 2]
            if clip.covers(Point(e)):
                p.draw_line(pt(a), pt(b), color=(1, 1, 1), width=2.5)
                p.draw_line(pt(a), pt(b), color=(0.12, 0.42, 0.31) if key == 'entry' else (0.39, 0.25, 0.12), width=0.6)
        center = s['sales'].intersection(clip).representative_point()
        if center.is_empty:
            continue
        pp = pt((center.x, center.y))
        size = 7 if detail else 5.5
        label = s['id'] + (' 新' if '-N' in s['id'] else '')
        bw = s['sales'].intersection(clip).bounds
        label_w = min(98, max(38, (bw[2] - bw[0]) * sc * 0.8))
        if detail and s['polygon'].area > 220:
            label += '\n売 %.0f / 裏 %.0f㎡' % (s['sales'].area, s['backroom'].area)
        text(p, pp.x - label_w / 2, pp.y - 6, label_w, 35, label, size)
    geom(f['void'], (0.82, 0.91, 0.96), (0.22, 0.42, 0.54), 0.7)
    for e in f['escalators']:
        g = rect_fn(e['c'], e['u'], e['run_m'], 2.4)
        geom(g, (0.57, 0.65, 0.65), (0.22, 0.3, 0.3), 0.6)
        c = pt(e['c'])
        text(p, c.x - 30, c.y - 5, 60, 24, e['direction'], 5.5)
    for obj in f.get('furniture', []):
        geom(obj['geom'], (0.45, 0.59, 0.43), None)
    if not before:
        geom(f['floor_openings_v5'].difference(f['void']), (0.83, 0.91, 0.96), (0.19, 0.39, 0.58), 0.6)
    if not before and 'other_wing_preview_floor' in f:
        geom(f['other_wing_preview_floor'], (.86, .94, .98), (.18, .42, .62), .7)
    for conn in f.get('connectors', []):
        pts = [(a[0] - 714, a[1] - 30) for a in conn['route']]
        for aa, bb in zip(pts, pts[1:]):
            if clip.covers(LineString([aa, bb])):
                p.draw_line(pt(aa), pt(bb), color=(0.19, 0.4, 0.59), width=1)
        if clip.covers(Point(pts[-1])):
            cc = pt(pts[-1])
            text(p, cc.x - 45, cc.y - 15, 90, 35, conn['id'] + ' / 他館側未施工', 6)
    p.draw_rect(box0, color=(0.64, 0.69, 0.67), width=0.4)
    text(p, box0.x0 + 8, box0.y0 + 5, box0.width - 16, 20, f'World X[{x0:.2f}, {x1:.2f}] / Z[{z0:.2f}, {z1:.2f}]m\u3000|\u3000縮尺 1:{2834.64567 / sc:.0f}（表示倍率100%時）', 8)
    text(p, ox, oz + (z1 - z0) * sc + 2, max(160, (x1 - x0) * sc), 17, f'幅 {x1 - x0:.2f}m × 奥行 {z1 - z0:.2f}m\u3000N = −Z', 8)
    scale = 10 if detail else 50
    a = fitz.Point(box0.x0 + 12, box0.y1 - 20)
    p.draw_line(a, a + fitz.Point(scale * sc, 0), color=ink, width=2)
    text(p, a.x, a.y - 16, 120, 18, f'{scale} m', 8)
    return sc