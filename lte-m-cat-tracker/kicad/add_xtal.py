#!/usr/bin/env python3
"""致命修正#2: 40MHz水晶(Y1=C5380316)+負荷C(C16/C17 18pF)追加
DESIGN.md「解確定（2026-06-11）」の完全トポロジーを実装する。
- +3.3V再配管: 動脈x7.75削除/バスy20.4ダイブ/西列北給電/pad11エンサークル
- via縮小0.6→0.4 ×4（中央ピンチに2線を通す）
- XTAL_N/XTAL_P 配線（全マージナル>=0.127）
"""
import re, sys, uuid

PCB = 'lte-m-cat-tracker.kicad_pcb'
s = open(PCB).read()
orig = s

def fmt(v):
    if v == int(v): return str(int(v))
    return repr(round(v, 6))

def seg_block(sx, sy, ex, ey):
    pat = (r'\t\(segment\n\t\t\(start %s %s\)\n\t\t\(end %s %s\)\n'
           r'\t\t\(width [\d.]+\)\n\t\t\(layer "[FB]\.Cu"\)\n'
           r'\t\t\(net "[^"]*"\)\n\t\t\(uuid "[^"]*"\)\n\t\)\n'
           ) % (re.escape(fmt(sx)), re.escape(fmt(sy)), re.escape(fmt(ex)), re.escape(fmt(ey)))
    m = re.search(pat, s)
    return m

def del_seg(sx, sy, ex, ey):
    global s
    m = seg_block(sx, sy, ex, ey) or seg_block(ex, ey, sx, sy)
    assert m, f"seg not found: ({sx},{sy})->({ex},{ey})"
    s = s[:m.start()] + s[m.end():]

def move_seg(sx, sy, ex, ey, nsx, nsy, nex, ney):
    global s
    m = seg_block(sx, sy, ex, ey) or seg_block(ex, ey, sx, sy)
    assert m, f"seg not found: ({sx},{sy})->({ex},{ey})"
    blk = m.group(0)
    # 元の向きを保ったまま座標置換
    blk2 = re.sub(r'\(start [\d.\-]+ [\d.\-]+\)', f'(start {fmt(nsx)} {fmt(nsy)})', blk)
    blk2 = re.sub(r'\(end [\d.\-]+ [\d.\-]+\)', f'(end {fmt(nex)} {fmt(ney)})', blk2)
    s = s[:m.start()] + blk2 + s[m.end():]

def via_block(x, y):
    pat = (r'\t\(via\n\t\t\(at %s %s\)\n\t\t\(size [\d.]+\)\n\t\t\(drill [\d.]+\)\n'
           r'\t\t\(layers "F\.Cu" "B\.Cu"\)\n(?:\t\t\(net "[^"]*"\)\n)?\t\t\(uuid "[^"]*"\)\n\t\)\n'
           ) % (re.escape(fmt(x)), re.escape(fmt(y)))
    return re.search(pat, s)

def del_via(x, y):
    global s
    m = via_block(x, y)
    assert m, f"via not found: ({x},{y})"
    s = s[:m.start()] + s[m.end():]

def shrink_via(x, y, new_size=0.4):
    global s
    m = via_block(x, y)
    assert m, f"via not found for shrink: ({x},{y})"
    blk = m.group(0).replace('(size 0.6)', f'(size {new_size})')
    s = s[:m.start()] + blk + s[m.end():]

def move_via(x, y, nx, ny):
    global s
    m = via_block(x, y)
    assert m, f"via not found for move: ({x},{y})"
    blk = m.group(0).replace(f'(at {fmt(x)} {fmt(y)})', f'(at {fmt(nx)} {fmt(ny)})')
    s = s[:m.start()] + blk + s[m.end():]

NEW = []
def add_seg(sx, sy, ex, ey, w, layer, net):
    NEW.append('\t(segment\n\t\t(start %s %s)\n\t\t(end %s %s)\n\t\t(width %s)\n'
               '\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'
               % (fmt(sx), fmt(sy), fmt(ex), fmt(ey), fmt(w), layer, net, uuid.uuid4()))
def add_via(x, y, net, size=0.4, drill=0.3):
    NEW.append('\t(via\n\t\t(at %s %s)\n\t\t(size %s)\n\t\t(drill %s)\n'
               '\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'
               % (fmt(x), fmt(y), fmt(size), fmt(drill), net, uuid.uuid4()))

# ============== 1) +3.3V 再配管 ==============
# 動脈削除
del_seg(7.75, 19.6, 7.75, 25.95)
del_via(7.75, 19.6)
# 旧西枝削除（エンサークル化）
del_seg(7.75, 26.5, 3.5, 26.5)
# 旧C5.1スタブ削除（C5移設）
del_seg(8.02, 19.6, 8.02, 19.8)
# y19.6西segトリム (5.3->8.3) -> (5.3->7.0)
move_seg(5.3, 19.6, 8.3, 19.6, 5.3, 19.6, 7.0, 19.6)
# バスy20.4西部 (9.6->5.3) -> 西延長 (7.1->3.3)
move_seg(9.6, 20.4, 5.3, 20.4, 7.1, 20.4, 3.3, 20.4)
# ダイブ（F.Cuのまま w0.25）+ 東再接続
add_seg(7.1, 20.4, 7.1, 18.1, 0.25, 'F.Cu', '+3.3V')
add_seg(7.1, 18.1, 8.85, 18.1, 0.25, 'F.Cu', '+3.3V')
add_seg(8.85, 18.1, 8.85, 20.4, 0.25, 'F.Cu', '+3.3V')
add_seg(8.85, 20.4, 9.6, 20.4, 0.3, 'F.Cu', '+3.3V')
# 西列北給電: via(3.3,20.4)->B->via(3.3,21.5)（C1.1パッドに半重なり）
add_via(3.3, 20.4, '+3.3V')
add_seg(3.3, 20.4, 3.3, 21.5, 0.2, 'B.Cu', '+3.3V')
add_via(3.3, 21.5, '+3.3V')
# U2.2/3給電horizトリム + 新動脈
move_seg(6.05, 22.5, 7.75, 22.5, 6.05, 22.5, 6.6, 22.5)
add_seg(6.5, 21.2, 6.5, 22.5, 0.2, 'B.Cu', '+3.3V')
# エンサークル（pad11+西列の給電）
add_seg(3.5, 26.5, 3.5, 31.5, 0.3, 'B.Cu', '+3.3V')
add_seg(3.5, 31.5, 7.75, 31.5, 0.3, 'B.Cu', '+3.3V')
add_seg(7.75, 31.5, 7.75, 26.5, 0.3, 'B.Cu', '+3.3V')
# via縮小 0.6->0.4（ピンチ拡幅）
for (vx, vy) in [(6.5, 21.0), (6.05, 22.5), (7.75, 25.95), (6.5, 19.6)]:
    shrink_via(vx, vy)

# ============== 2) VBAT_SW y28.5 -> 28.35（水晶クリアランス） ==============
move_seg(2.0, 28.85, 2.0, 28.5, 2.0, 28.85, 2.0, 28.35)
move_seg(2.0, 28.5, 10.55, 28.5, 2.0, 28.35, 10.55, 28.35)

# ============== 3) GNDステッチングvia移設（降下レーン上） ==============
move_via(7.0, 23.3, 2.5, 25.0)

# ============== 4) C5 移設 (8.5,19.8)->(16.55,22.5) + 給電 ==============
i = s.find('(property "Reference" "C5"')
st = s.rfind('(footprint', 0, i)
at_m = re.compile(r'\(at 8\.5 19\.8\)')
seg_c5 = s[st:st+400]
assert '(at 8.5 19.8)' in seg_c5, "C5 at not found"
s = s[:st] + s[st:st+400].replace('(at 8.5 19.8)', '(at 16.55 22.5)', 1) + s[st+400:]
add_seg(15.99, 21.6, 15.99, 22.5, 0.15, 'F.Cu', '+3.3V')   # R7.1から
add_seg(15.99, 22.5, 16.07, 22.5, 0.15, 'F.Cu', '+3.3V')   # C5.1へ

# ============== 5) U2 pad29/30 にネット割当 ==============
def set_pad_net(ref, padnum, net):
    global s
    i = s.find(f'(property "Reference" "{ref}"')
    st = s.rfind('(footprint', 0, i)
    d = 0; j = st
    while True:
        if s[j] == '(': d += 1
        elif s[j] == ')':
            d -= 1
            if d == 0: break
        j += 1
    blk = s[st:j]
    pat = re.compile(r'(\(pad "%s" smd \w+\n(?:.*\n)*?)(\t\t\t\(uuid )' % padnum)
    m2 = pat.search(blk)
    assert m2, f"{ref} pad {padnum} not found"
    assert f'(net ' not in m2.group(1), f"{ref}.{padnum} already has net"
    nb = blk[:m2.end(1)] + f'\t\t\t(net "{net}")\n' + blk[m2.end(1):]
    s = s[:st] + nb + s[j:]

set_pad_net('U2', '29', 'XTAL_N')
set_pad_net('U2', '30', 'XTAL_P')

# ============== 6) 新規フットプリント Y1 / C16 / C17 ==============
def cap_fp(ref, val, x, y, net1, net2):
    u = uuid.uuid4
    return f'''\t(footprint ""
\t\t(layer "F.Cu")
\t\t(uuid "{u()}")
\t\t(at {fmt(x)} {fmt(y)})
\t\t(property "Reference" "{ref}"
\t\t\t(at 0 -1.2 0)
\t\t\t(layer "F.SilkS")
\t\t\t(uuid "{u()}")
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 0.8 0.8)
\t\t\t\t\t(thickness 0.12)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Value" "{val}"
\t\t\t(at 0 1.2 0)
\t\t\t(layer "F.Fab")
\t\t\t(uuid "{u()}")
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 0.8 0.8)
\t\t\t\t\t(thickness 0.12)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(fp_rect
\t\t\t(start -0.91 -0.46)
\t\t\t(end 0.91 0.46)
\t\t\t(stroke
\t\t\t\t(width 0.05)
\t\t\t\t(type solid)
\t\t\t)
\t\t\t(fill no)
\t\t\t(layer "F.CrtYd")
\t\t\t(uuid "{u()}")
\t\t)
\t\t(pad "1" smd roundrect
\t\t\t(at -0.48 0)
\t\t\t(size 0.56 0.62)
\t\t\t(layers "F.Cu" "F.Mask" "F.Paste")
\t\t\t(roundrect_rratio 0.25)
\t\t\t(net "{net1}")
\t\t\t(uuid "{u()}")
\t\t)
\t\t(pad "2" smd roundrect
\t\t\t(at 0.48 0)
\t\t\t(size 0.56 0.62)
\t\t\t(layers "F.Cu" "F.Mask" "F.Paste")
\t\t\t(roundrect_rratio 0.25)
\t\t\t(net "{net2}")
\t\t\t(uuid "{u()}")
\t\t)
\t)
'''

def xtal_fp(x, y):
    u = uuid.uuid4
    pads = ''
    for num, px, py, net in [('1', -1.1, 0.8, 'XTAL_P'), ('2', 1.1, 0.8, 'GND'),
                             ('3', 1.1, -0.8, 'XTAL_N'), ('4', -1.1, -0.8, 'GND')]:
        pads += f'''\t\t(pad "{num}" smd roundrect
\t\t\t(at {fmt(px)} {fmt(py)})
\t\t\t(size 1.4 1.2)
\t\t\t(layers "F.Cu" "F.Mask" "F.Paste")
\t\t\t(roundrect_rratio 0.15)
\t\t\t(net "{net}")
\t\t\t(uuid "{u()}")
\t\t)
'''
    return f'''\t(footprint ""
\t\t(layer "F.Cu")
\t\t(uuid "{u()}")
\t\t(at {fmt(x)} {fmt(y)})
\t\t(property "Reference" "Y1"
\t\t\t(at 0 -2.2 0)
\t\t\t(layer "F.SilkS")
\t\t\t(uuid "{u()}")
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 0.8 0.8)
\t\t\t\t\t(thickness 0.12)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Value" "40MHz 12pF 3225"
\t\t\t(at 0 2.2 0)
\t\t\t(layer "F.Fab")
\t\t\t(uuid "{u()}")
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 0.8 0.8)
\t\t\t\t\t(thickness 0.12)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(fp_rect
\t\t\t(start -1.85 -1.5)
\t\t\t(end 1.85 1.5)
\t\t\t(stroke
\t\t\t\t(width 0.05)
\t\t\t\t(type solid)
\t\t\t)
\t\t\t(fill no)
\t\t\t(layer "F.CrtYd")
\t\t\t(uuid "{u()}")
\t\t)
\t\t(fp_rect
\t\t\t(start -1.6 -1.25)
\t\t\t(end 1.6 1.25)
\t\t\t(stroke
\t\t\t\t(width 0.1)
\t\t\t\t(type solid)
\t\t\t)
\t\t\t(fill no)
\t\t\t(layer "F.Fab")
\t\t\t(uuid "{u()}")
\t\t)
{pads}\t)
'''

NEW.append(xtal_fp(5.1, 30.2))
NEW.append(cap_fp('C16', '18pF', 7.95, 29.4, 'XTAL_N', 'GND'))
NEW.append(cap_fp('C17', '18pF', 8.05, 31.0, 'XTAL_P', 'GND'))

# ============== 7) XTAL 配線 ==============
W = 0.15
# XTAL_N: pad29(8.25,21.05) -> Y1.3(6.2,29.4) + C16.1
add_seg(8.25, 20.65, 8.25, 19.1, W, 'F.Cu', 'XTAL_N')
add_via(8.25, 19.0, 'XTAL_N')
add_seg(8.25, 19.0, 8.25, 19.55, W, 'B.Cu', 'XTAL_N')
add_seg(8.25, 19.55, 6.98, 19.55, W, 'B.Cu', 'XTAL_N')
add_seg(6.98, 19.55, 6.98, 29.4, W, 'B.Cu', 'XTAL_N')
add_seg(6.98, 29.4, 6.85, 29.4, W, 'B.Cu', 'XTAL_N')
add_via(6.85, 29.4, 'XTAL_N')
add_seg(6.85, 29.4, 6.2, 29.4, W, 'F.Cu', 'XTAL_N')    # Y1.3へ
add_seg(6.85, 29.4, 7.55, 29.4, W, 'F.Cu', 'XTAL_N')   # C16.1へ
# XTAL_P: pad30(7.75,21.05) -> Y1.1(4.0,31.0) + C17.1
add_seg(7.75, 20.65, 7.75, 20.1, W, 'F.Cu', 'XTAL_P')
add_via(7.75, 20.0, 'XTAL_P')
add_seg(7.75, 20.0, 7.75, 20.45, W, 'B.Cu', 'XTAL_P')
add_seg(7.75, 20.45, 7.27, 20.45, W, 'B.Cu', 'XTAL_P')
add_seg(7.27, 20.45, 7.27, 31.0, W, 'B.Cu', 'XTAL_P')
add_via(7.27, 31.0, 'XTAL_P')
add_seg(7.27, 31.0, 7.45, 31.0, W, 'F.Cu', 'XTAL_P')   # C17.1へ
add_seg(7.27, 31.0, 5.1, 31.0, W, 'B.Cu', 'XTAL_P')    # pad2の下を潜る
add_via(5.1, 31.0, 'XTAL_P')
add_seg(5.1, 31.0, 4.0, 31.0, W, 'F.Cu', 'XTAL_P')     # パッド1/2間ギャップ経由でY1.1へ

# ============== 挿入・保存 ==============
tail = s.rfind('\t(embedded_fonts')
assert tail > 0
s = s[:tail] + ''.join(NEW) + s[tail:]
open(PCB, 'w').write(s)
print("OK: edits applied.")
print("  deleted/moved/added: artery, branch, bus-dive, encircle, C5->16.55/22.5, Y1+C16+C17, XTAL routes")
