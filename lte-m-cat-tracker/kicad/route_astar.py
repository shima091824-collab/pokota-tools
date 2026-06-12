#!/usr/bin/env python3
"""グリッドA*ミニルーター。
ルール: 銅↔銅 0.2mm（0.2丁度=適合）/ 穴↔銅・穴↔穴 0.25mm / 基板端 0.3mm
使い方: route_astar.py NET x1 y1 x2 y2 [--via-dia 0.45 --width 0.2]
出力: 経路セグメントとビアのリスト（適用は別スクリプト）
"""
import sys, re, math, heapq

RES = 0.05  # グリッド解像度mm
W, H = 30.0, 35.0
NX, NY = int(W/RES)+1, int(H/RES)+1
TRACK_W = 0.2
CLR = 0.2
HOLE_CLR = 0.25
VIA_DIA = 0.45
VIA_DRILL = 0.3
EDGE = 0.3

def load_all(path):
    s = open(path).read()
    items = []  # (kind,net,layer,geom...)
    holes = []
    for m in re.finditer(r'\(segment\s+\(start ([\d.-]+) ([\d.-]+)\)\s+\(end ([\d.-]+) ([\d.-]+)\)\s+\(width ([\d.]+)\)\s+\(layer "([^"]+)"\)\s+\(net "([^"]*)"\)', s):
        x1,y1,x2,y2,w = map(float, m.groups()[:5])
        items.append(('seg', m.group(7), m.group(6), x1,y1,x2,y2,w))
    for m in re.finditer(r'\(via\s+\(at ([\d.-]+) ([\d.-]+)\)\s+\(size ([\d.]+)\)\s+\(drill ([\d.]+)\)[\s\S]{0,400}?\(net "([^"]*)"\)', s):
        x,y,d,dr = map(float, m.groups()[:4])
        items.append(('via', m.group(5), '*', x,y,d))
        holes.append((x,y,dr))
    for fp in re.split(r'\n\t\(footprint ', s)[1:]:
        mat = re.search(r'\n\t\t\(at ([\d.-]+) ([\d.-]+)(?: ([\d.-]+))?\)', fp)
        if not mat: continue
        fx,fy,frot = float(mat.group(1)), float(mat.group(2)), float(mat.group(3) or 0)
        for pm in re.finditer(r'\(pad "([^"]*)" (smd|thru_hole|np_thru_hole) \w+\s+\(at ([\d.-]+) ([\d.-]+)(?: ([\d.-]+))?\)\s+\(size ([\d.-]+) ([\d.-]+)\)(?:\s+\(drill ([\d.]+)\))?', fp):
            typ = pm.group(2)
            px,py,prot,sw,sh = (float(pm.group(i)) if pm.group(i) else 0.0 for i in (3,4,5,6,7))
            r = math.radians(frot)
            gx = fx + px*math.cos(r) + py*math.sin(r)
            gy = fy - px*math.sin(r) + py*math.cos(r)
            tot = (frot + prot) % 180
            if abs(tot-90) < 1: sw, sh = sh, sw
            nxt = fp.find('(pad "', pm.end())
            blk = fp[pm.start(): nxt if nxt!=-1 else pm.start()+1500]
            lay = re.search(r'\(layers "([^"]+)"', blk)
            nm = re.search(r'\(net "([^"]*)"\)', blk)
            net = nm.group(1) if nm else ''
            if typ == 'smd':
                layer = 'F.Cu' if (lay and 'F.Cu' in lay.group(1)) else 'B.Cu'
                items.append(('pad', net, layer, gx,gy,sw,sh))
            else:
                items.append(('pad', net, 'F.Cu', gx,gy,sw,sh))
                items.append(('pad', net, 'B.Cu', gx,gy,sw,sh))
                if pm.group(8): holes.append((gx,gy,float(pm.group(8))))
    return items, holes

def idx(ix,iy): return iy*NX+ix

def paint_circle(grid, cx, cy, r):
    if r <= 0: return
    ix0=max(0,int((cx-r)/RES)); ix1=min(NX-1,int((cx+r)/RES)+1)
    iy0=max(0,int((cy-r)/RES)); iy1=min(NY-1,int((cy+r)/RES)+1)
    r2=r*r
    for iy in range(iy0,iy1+1):
        dy=iy*RES-cy
        for ix in range(ix0,ix1+1):
            dx=ix*RES-cx
            if dx*dx+dy*dy < r2-1e-9:
                grid[idx(ix,iy)]=1

def paint_rect(grid, cx, cy, w, h, margin):
    x0,x1=cx-w/2-margin, cx+w/2+margin
    y0,y1=cy-h/2-margin, cy+h/2+margin
    ix0=max(0,int(x0/RES)); ix1=min(NX-1,int(x1/RES)+1)
    iy0=max(0,int(y0/RES)); iy1=min(NY-1,int(y1/RES)+1)
    # 角は丸め（margin半径）: 簡略化のため矩形＋4隅円弧の代わりに、辺帯は矩形・角は距離判定
    for iy in range(iy0,iy1+1):
        py=iy*RES
        for ix in range(ix0,ix1+1):
            px=ix*RES
            ddx=max(cx-w/2-px, px-(cx+w/2), 0)
            ddy=max(cy-h/2-py, py-(cy+h/2), 0)
            if ddx*ddx+ddy*ddy < margin*margin-1e-9:
                grid[idx(ix,iy)]=1

def paint_seg(grid, x1,y1,x2,y2, r):
    n=max(1,int(math.hypot(x2-x1,y2-y1)/ (RES/2)))
    for k in range(n+1):
        t=k/n
        paint_circle(grid, x1+(x2-x1)*t, y1+(y2-y1)*t, r)

def build_grids(items, holes, net):
    tr = {'F.Cu': bytearray(NX*NY), 'B.Cu': bytearray(NX*NY)}
    via = bytearray(NX*NY)
    half = TRACK_W/2
    for it in items:
        if it[1] == net: continue
        if it[0]=='seg':
            r_t = it[7]/2 + CLR + half
            r_v = it[7]/2 + CLR + VIA_DIA/2
            paint_seg(tr[it[2]], it[3],it[4],it[5],it[6], r_t)
            paint_seg(via, it[3],it[4],it[5],it[6], r_v)
        elif it[0]=='via':
            r_t = it[5]/2 + CLR + half
            paint_circle(tr['F.Cu'], it[3],it[4], r_t)
            paint_circle(tr['B.Cu'], it[3],it[4], r_t)
            paint_circle(via, it[3],it[4], it[5]/2 + CLR + VIA_DIA/2)
        else:
            _,_,lay,gx,gy,sw,sh = it[:7]
            paint_rect(tr[lay], gx,gy,sw,sh, CLR+half)
            paint_rect(via, gx,gy,sw,sh, CLR+VIA_DIA/2)
    # 穴ルール: 既存穴 vs 新銅(0.25) / 新穴 vs 既存銅(0.25) / 穴↔穴(0.25)
    for hx,hy,hd in holes:
        paint_circle(tr['F.Cu'], hx,hy, hd/2 + HOLE_CLR + half)
        paint_circle(tr['B.Cu'], hx,hy, hd/2 + HOLE_CLR + half)
        paint_circle(via, hx,hy, hd/2 + HOLE_CLR + VIA_DRILL/2)
    for it in items:
        # 新ビアの穴 vs 既存銅（同ネット含む・ただし開始/終了パッド上は呼び出し側で許可）
        if it[0]=='seg':
            paint_seg(via, it[3],it[4],it[5],it[6], it[7]/2 + HOLE_CLR + VIA_DRILL/2)
        elif it[0]=='via':
            pass
        else:
            _,_,lay,gx,gy,sw,sh = it[:7]
            if it[1]:  # 自ネットのパッドにはin-padビア許可のため塗らない→呼び出し側制御
                pass
    # 基板端
    m = EDGE + half
    for iy in range(NY):
        for ix in range(NX):
            x,y=ix*RES,iy*RES
            if x<m or x>W-m or y<m or y>H-m:
                tr['F.Cu'][idx(ix,iy)]=1; tr['B.Cu'][idx(ix,iy)]=1; via[idx(ix,iy)]=1
    return tr, via

def los_free(grid, x1,y1,x2,y2):
    n=max(1,int(math.hypot(x2-x1,y2-y1)/(RES/2)))
    for k in range(n+1):
        t=k/n
        ix,iy=round((x1+(x2-x1)*t)/RES),round((y1+(y2-y1)*t)/RES)
        if grid[idx(ix,iy)]: return False
    return True

def smooth(layer_grid, pts):
    out=[pts[0]]; i=0
    while i<len(pts)-1:
        j=len(pts)-1
        while j>i+1 and not los_free(layer_grid,pts[i][0],pts[i][1],pts[j][0],pts[j][1]):
            j-=1
        out.append(pts[j]); i=j
    return out

def astar(tr, via_grid, sx, sy, gx, gy, slayer='F.Cu', glayer='F.Cu', via_cost=40):
    six,siy=round(sx/RES),round(sy/RES)
    gix,giy=round(gx/RES),round(gy/RES)
    L={'F.Cu':0,'B.Cu':1}
    grids=[tr['F.Cu'],tr['B.Cu']]
    start=(six,siy,L[slayer]); goal=(gix,giy,L[glayer])
    def h(n): return math.hypot(n[0]-gix,n[1]-giy)
    dirs=[(1,0,1),(0,1,1),(-1,0,1),(0,-1,1),(1,1,1.414),(1,-1,1.414),(-1,1,1.414),(-1,-1,1.414)]
    openq=[(h(start),0,start,None)]
    came={}; gsc={start:0}
    while openq:
        f,g,node,par=heapq.heappop(openq)
        if node in came: continue
        came[node]=par
        if node==goal:
            path=[node]
            while came[path[-1]] is not None: path.append(came[path[-1]])
            return path[::-1]
        ix,iy,lz=node
        for dx,dy,c in dirs:
            nx_,ny_=ix+dx,iy+dy
            if not(0<=nx_<NX and 0<=ny_<NY): continue
            if grids[lz][idx(nx_,ny_)] and (nx_,ny_,lz)!=goal: continue
            nn=(nx_,ny_,lz)
            ng=g+c
            if nn not in gsc or ng<gsc[nn]:
                gsc[nn]=ng
                heapq.heappush(openq,(ng+h(nn),ng,nn,node))
        # via
        if not via_grid[idx(ix,iy)] or node==start:
            nn=(ix,iy,1-lz)
            ng=g+via_cost
            if nn not in gsc or ng<gsc[nn]:
                gsc[nn]=ng
                heapq.heappush(openq,(ng+h(nn),ng,nn,node))
    return None

def simplify(path):
    """直線区間をマージし (layer, [(x,y)...]) と via位置を返す"""
    out=[]; vias=[]
    cur=[(path[0][0]*RES,path[0][1]*RES)]; lz=path[0][2]
    def flush(layer,pts):
        if len(pts)>1:
            # collinear merge
            merged=[pts[0]]
            for p in pts[1:]:
                if len(merged)>=2:
                    ax,ay=merged[-2]; bx,by=merged[-1]
                    if abs((bx-ax)*(p[1]-by)-(by-ay)*(p[0]-bx))<1e-9:
                        merged[-1]=p; continue
                merged.append(p)
            out.append(('F.Cu' if layer==0 else 'B.Cu', merged))
    for n in path[1:]:
        x,y=n[0]*RES,n[1]*RES
        if n[2]!=lz:
            flush(lz,cur); vias.append((x,y))
            cur=[(x,y)]; lz=n[2]
        else:
            cur.append((x,y))
    flush(lz,cur)
    return out, vias

if __name__=='__main__':
    net=sys.argv[1]
    sx,sy,gx,gy=map(float,sys.argv[2:6])
    items,holes=load_all('lte-m-cat-tracker.kicad_pcb')
    print(f"items={len(items)} holes={len(holes)}; grid {NX}x{NY}")
    tr,via=build_grids(items,holes,net)
    sl = sys.argv[6] if len(sys.argv)>6 else 'F.Cu'
    gl = sys.argv[7] if len(sys.argv)>7 else 'F.Cu'
    path=astar(tr,via,sx,sy,gx,gy,sl,gl)
    if not path:
        print("経路なし"); sys.exit(1)
    segs,vias=simplify(path)
    for lay,pts in segs:
        pts=smooth(tr[lay],pts)
        for a,b in zip(pts,pts[1:]):
            print(f"SEG {lay} ({a[0]:.3f},{a[1]:.3f}) -> ({b[0]:.3f},{b[1]:.3f})")
    for vx,vy in vias:
        print(f"VIA ({vx:.3f},{vy:.3f})")
