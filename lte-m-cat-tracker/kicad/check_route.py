#!/usr/bin/env python3
"""候補ルート（seg/via）を kicad_pcb の全銅要素と照合し、
異ネット間の clearance<0.2mm / 交差を報告する。
使い方: route_pcb_v11.py 実行後のPCBに対して candidates を検証。
"""
import re, math, sys

PCB = 'lte-m-cat-tracker.kicad_pcb'
CLR = 0.2  # 最小クリアランス

def load(path):
    pcb = open(path).read()
    items = []  # (kind, net, layer, geom...)
    for m in re.finditer(r'\(segment\s+\(start ([\d.-]+) ([\d.-]+)\)\s+\(end ([\d.-]+) ([\d.-]+)\)\s+\(width ([\d.]+)\)\s+\(layer "([^"]+)"\)\s+\(net "([^"]*)"\)', pcb):
        x1,y1,x2,y2,w = map(float, m.groups()[:5])
        items.append(('seg', m.group(7), m.group(6), x1,y1,x2,y2,w))
    for m in re.finditer(r'\(via\s+\(at ([\d.-]+) ([\d.-]+)\)\s+\(size ([\d.]+)\)(?:.|\n)*?\(net "([^"]*)"\)', pcb):
        x,y,d = map(float, m.groups()[:3])
        items.append(('via', m.group(4), '*', x,y,d))
    # SMD pads (global coords, footprint rotation considered)
    for fp in re.split(r'\n\t\(footprint ', pcb)[1:]:
        mat = re.search(r'\n\t\t\(at ([\d.-]+) ([\d.-]+)(?: ([\d.-]+))?\)', fp)
        if not mat: continue
        fx,fy,frot = float(mat.group(1)), float(mat.group(2)), float(mat.group(3) or 0)
        ref = re.search(r'\(property "Reference" "([^"]+)"', fp).group(1)
        for pm in re.finditer(r'\(pad "([^"]*)" smd \w+\s+\(at ([\d.-]+) ([\d.-]+)(?: ([\d.-]+))?\)\s+\(size ([\d.-]+) ([\d.-]+)\)', fp):
            px,py,prot,sw,sh = (float(pm.group(i)) if pm.group(i) else 0.0 for i in (2,3,4,5,6))
            blk = fp[pm.start():pm.start()+1500]
            lay = re.search(r'\(layers "([^"]+)"', blk)
            nm = re.search(r'\(net "([^"]*)"\)', blk)
            r = math.radians(frot)
            gx = fx + px*math.cos(r) + py*math.sin(r)
            gy = fy - px*math.sin(r) + py*math.cos(r)
            tot = (frot + prot) % 180
            if abs(tot-90) < 1: sw, sh = sh, sw
            layer = 'F.Cu' if (lay and 'F.Cu' in lay.group(1)) else 'B.Cu'
            items.append(('pad', nm.group(1) if nm else '', layer, gx,gy,sw,sh, f'{ref}.{pm.group(1)}'))
    return items

def seg_pt_dist(x1,y1,x2,y2,px,py):
    dx,dy = x2-x1, y2-y1
    L2 = dx*dx+dy*dy
    t = 0 if L2==0 else max(0,min(1,((px-x1)*dx+(py-y1)*dy)/L2))
    cx,cy = x1+t*dx, y1+t*dy
    return math.hypot(px-cx, py-cy)

def seg_seg_dist(a,b):
    (x1,y1,x2,y2),(x3,y3,x4,y4) = a,b
    d1=(x2-x1,y2-y1); d2=(x4-x3,y4-y3)
    den = d1[0]*d2[1]-d1[1]*d2[0]
    if abs(den) > 1e-9:
        t = ((x3-x1)*d2[1]-(y3-y1)*d2[0])/den
        u = ((x3-x1)*d1[1]-(y3-y1)*d1[0])/den
        if 0<=t<=1 and 0<=u<=1: return 0.0
    return min(seg_pt_dist(*a,x3,y3), seg_pt_dist(*a,x4,y4),
               seg_pt_dist(*b,x1,y1), seg_pt_dist(*b,x2,y2))

def seg_rect_dist(seg, cx,cy,w,h):
    # 近似: 矩形の4辺との距離の最小
    hw,hh = w/2,h/2
    corners=[(cx-hw,cy-hh),(cx+hw,cy-hh),(cx+hw,cy+hh),(cx-hw,cy+hh)]
    best=float('inf')
    for i in range(4):
        e=(corners[i][0],corners[i][1],corners[(i+1)%4][0],corners[(i+1)%4][1])
        best=min(best,seg_seg_dist(seg,e))
    # seg端点が矩形内
    for px,py in ((seg[0],seg[1]),(seg[2],seg[3])):
        if cx-hw<=px<=cx+hw and cy-hh<=py<=cy+hh: return 0.0
    return best

def check(cands, items, label=''):
    """cands: list of ('seg',net,layer,x1,y1,x2,y2,w) or ('via',net,x,y) (d=0.6)"""
    bad=[]
    for c in cands:
        if c[0]=='seg':
            _,net,lay,x1,y1,x2,y2,w = c
            cseg=(x1,y1,x2,y2)
            for it in items:
                if it[1]==net or it[1]=='': pass
                if it[1]==net: continue
                if it[0]=='seg':
                    if it[2]!=lay: continue
                    d=seg_seg_dist(cseg,(it[3],it[4],it[5],it[6]))-w/2-it[7]/2
                elif it[0]=='via':
                    d=seg_pt_dist(*cseg,it[3],it[4])-w/2-it[5]/2
                else:
                    if it[2]!=lay: continue
                    d=seg_rect_dist(cseg,it[3],it[4],it[5],it[6])-w/2
                if d<CLR-1e-9:
                    tag = it[7] if it[0]=='pad' else ''
                    bad.append(f"{label} seg{cseg}{lay} vs {it[0]} [{it[1]}] {tag} {tuple(it[3:7])} gap={d:.3f}")
        else:
            _,net,x,y = c
            for it in items:
                if it[1]==net: continue
                if it[0]=='seg':
                    d=seg_pt_dist(it[3],it[4],it[5],it[6],x,y)-0.3-it[7]/2
                elif it[0]=='via':
                    d=math.hypot(x-it[3],y-it[4])-0.6
                else:
                    d=seg_rect_dist((x,y,x,y),it[3],it[4],it[5],it[6])-0.3
                if d<CLR-1e-9:
                    tag = it[7] if it[0]=='pad' else ''
                    bad.append(f"{label} via({x},{y})[{net}] vs {it[0]} [{it[1]}] {tag} {tuple(it[3:7])} gap={d:.3f}")
    return bad

if __name__ == '__main__':
    items = load(PCB)
    print(f"loaded {len(items)} items")
