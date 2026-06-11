#!/usr/bin/env python3
"""致命修正#2 v2: 40MHz水晶(Y1=C5380316)+負荷C(C16/C17)をU2東側に追加
- XTAL_P/N は全F.Cu・via0本（y20.0/y20.3バンド→x17.4/x15.2降下）
- 部品6点移設(C5/C6/C8/R5/R6/R7) + +3.3VスパインをポケットAに新設
- バスy20.4撤去→Fダイブ(5.4→20.15@y18.05) / ミニウェブ撤去 / 動脈#2はvia-A(18.5,19.6)から再給電
- SDA: x15.5系撤去→x14.1降下+via(14.1,22.0)でU3.4再給電 / C7再給電
詳細座標: DESIGN.md「水晶実装プランv2・最終座標」
"""
import re, uuid

PCB = 'lte-m-cat-tracker.kicad_pcb'
s = open(PCB).read()

def fmt(v):
    return str(int(v)) if v == int(v) else repr(round(v, 6))

def seg_pat(sx, sy, ex, ey):
    return (r'\t\(segment\n\t\t\(start %s %s\)\n\t\t\(end %s %s\)\n'
            r'\t\t\(width [\d.]+\)\n\t\t\(layer "[FB]\.Cu"\)\n'
            r'\t\t\(net "[^"]*"\)\n\t\t\(uuid "[^"]*"\)\n\t\)\n'
            ) % tuple(re.escape(fmt(v)) for v in (sx, sy, ex, ey))

def del_seg(sx, sy, ex, ey):
    global s
    m = re.search(seg_pat(sx, sy, ex, ey), s) or re.search(seg_pat(ex, ey, sx, sy), s)
    assert m, f"seg not found: ({sx},{sy})->({ex},{ey})"
    s = s[:m.start()] + s[m.end():]

def repl_seg(sx, sy, ex, ey, nsx, nsy, nex, ney):
    global s
    m = re.search(seg_pat(sx, sy, ex, ey), s) or re.search(seg_pat(ex, ey, sx, sy), s)
    assert m, f"seg not found: ({sx},{sy})->({ex},{ey})"
    blk = m.group(0)
    blk = re.sub(r'\(start [\d.\-]+ [\d.\-]+\)', f'(start {fmt(nsx)} {fmt(nsy)})', blk)
    blk = re.sub(r'\(end [\d.\-]+ [\d.\-]+\)', f'(end {fmt(nex)} {fmt(ney)})', blk)
    s = s[:m.start()] + blk + s[m.end():]

def del_via(x, y):
    global s
    pat = (r'\t\(via\n\t\t\(at %s %s\)\n\t\t\(size [\d.]+\)\n\t\t\(drill [\d.]+\)\n'
           r'\t\t\(layers "F\.Cu" "B\.Cu"\)\n(?:\t\t\(net "[^"]*"\)\n)?\t\t\(uuid "[^"]*"\)\n\t\)\n'
           ) % (re.escape(fmt(x)), re.escape(fmt(y)))
    m = re.search(pat, s)
    assert m, f"via not found ({x},{y})"
    s = s[:m.start()] + s[m.end():]

def move_part(ref, nx, ny, rot=None):
    global s
    i = s.find(f'(property "Reference" "{ref}"')
    st = s.rfind('(footprint', 0, i)
    m = re.search(r'\(at ([\d.\-]+) ([\d.\-]+)(?: ([\d.\-]+))?\)', s[st:st+400])
    new = f'(at {fmt(nx)} {fmt(ny)}{" "+fmt(rot) if rot else ""})'
    s = s[:st] + s[st:st+400].replace(m.group(0), new, 1) + s[st+400:]

NEW = []
def add_seg(sx, sy, ex, ey, w, layer, net):
    NEW.append('\t(segment\n\t\t(start %s %s)\n\t\t(end %s %s)\n\t\t(width %s)\n'
               '\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'
               % (fmt(sx), fmt(sy), fmt(ex), fmt(ey), fmt(w), layer, net, uuid.uuid4()))
def add_via(x, y, net, size=0.5, drill=0.3):
    NEW.append('\t(via\n\t\t(at %s %s)\n\t\t(size %s)\n\t\t(drill %s)\n'
               '\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'
               % (fmt(x), fmt(y), fmt(size), fmt(drill), net, uuid.uuid4()))

# ============ 1) 撤去 ============
# バスy20.4
del_seg(9.6, 20.4, 5.3, 20.4)
del_seg(11.7, 20.4, 9.6, 20.4)
# ミニウェブ
for c in [(9.6,19.6,9.6,20.4),(11.7,19.6,11.7,20.4),(12.0,19.6,11.7,19.6),
          (12.0,20.3,12.0,19.6),(13.0,20.3,12.0,20.3),(13.0,19.6,13.0,20.3)]:
    del_seg(*c)
# 旧部品スタブ/給電縦線
for c in [(13.51,19.6,13.51,19.8),(12.49,20.3,12.49,21.0),(8.02,19.6,8.02,19.8),
          (10.02,19.6,10.02,19.8),(12.12,20.3,12.12,22.0),(14.02,19.6,14.02,22.0),
          (15.99,19.6,15.99,21.5)]:
    del_seg(*c)
# 旧C6 GNDスタブ
del_seg(10.73, 19.8, 10.73, 19.2)
del_seg(10.98, 19.8, 10.73, 19.8)
# SCL旧R7枝
for c in [(15.0,25.2,15.5,25.2),(15.5,25.2,17.5,25.2),(17.5,25.2,17.5,21.5),(17.5,21.5,17.01,21.5)]:
    del_seg(*c)
# SDA旧尾部(F+B)・R6枝
for c in [(15.2,20.5,15.2,21.3),(15.2,21.3,15.5,21.3),(15.5,21.3,15.5,23.3),
          (15.5,23.3,14.2625,23.3),(13.35,21.0,13.51,21.0),
          (15.35,19.45,15.35,20.1),(15.35,20.1,15.2,20.1),(15.2,20.1,15.2,20.5),
          (13.35,19.45,13.35,21.0)]:
    del_seg(*c)
# 動脈#2 (重複2本)
del_seg(11.8, 19.6, 11.8, 25.5)
del_seg(11.8, 19.6, 11.8, 25.5)
# トリム
repl_seg(5.3, 19.6, 8.3, 19.6, 5.3, 19.6, 7.0, 19.6)
repl_seg(7.75, 19.6, 7.75, 25.95, 7.75, 18.05, 7.75, 25.95)
repl_seg(12.28, 19.45, 15.35, 19.45, 12.28, 19.45, 14.1, 19.45)
# via削除
del_via(7.75, 19.6)
del_via(11.8, 19.6)
del_via(11.8, 19.6)
del_via(15.2, 20.5)
del_via(13.35, 21.0)

# ============ 2) +3.3V 再構成 ============
add_via(7.75, 18.05, '+3.3V')           # 動脈x7.75の新給電(ダイブ上)
# Fダイブ（西アイランド給電の幹線バイパス）
add_seg(5.4, 20.4, 5.4, 18.05, 0.25, 'F.Cu', '+3.3V')
add_seg(5.4, 18.05, 20.15, 18.05, 0.25, 'F.Cu', '+3.3V')
add_seg(20.15, 18.05, 20.15, 19.6, 0.25, 'F.Cu', '+3.3V')
# via-A + Bリンク（動脈#2再給電）
add_via(18.5, 19.6, '+3.3V')
add_seg(18.5, 19.6, 18.5, 23.1, 0.25, 'B.Cu', '+3.3V')
add_seg(18.5, 23.1, 11.8, 23.1, 0.25, 'B.Cu', '+3.3V')
add_seg(11.8, 23.1, 11.8, 25.5, 0.3, 'B.Cu', '+3.3V')
# C7 再給電（旧x12.12縦の代替）
add_seg(12.12, 22.3, 12.12, 23.0, 0.2, 'F.Cu', '+3.3V')
add_seg(12.12, 23.0, 11.8, 23.0, 0.2, 'F.Cu', '+3.3V')
add_seg(11.8, 23.0, 11.8, 25.4, 0.2, 'F.Cu', '+3.3V')
# ポケットAスパイン（C10.1から）
add_seg(26.55, 25.7, 26.55, 26.3, 0.3, 'F.Cu', '+3.3V')
add_seg(26.55, 26.3, 17.7, 26.3, 0.3, 'F.Cu', '+3.3V')

# ============ 3) SDA 再給電（U3.4） ============
add_seg(14.1, 19.45, 14.1, 22.0, 0.15, 'B.Cu', 'I2C_SDA')
add_via(14.1, 22.0, 'I2C_SDA')
add_seg(14.1, 22.0, 14.1, 23.3, 0.15, 'F.Cu', 'I2C_SDA')
add_seg(14.1, 23.3, 14.2625, 23.3, 0.15, 'F.Cu', 'I2C_SDA')

# ============ 4) 部品移設 ============
move_part('C5', 18.3, 26.85, 270)
move_part('C6', 20.5, 26.85, 270)
move_part('C8', 21.6, 26.85, 270)
move_part('R5', 24.3, 27.5)
move_part('R6', 17.3, 26.85, 270)
move_part('R7', 19.4, 26.85, 270)
# R6 SDAタップ
add_seg(17.3, 27.62, 17.3, 28.1, 0.15, 'F.Cu', 'I2C_SDA')
add_seg(17.3, 28.1, 14.95, 28.1, 0.15, 'F.Cu', 'I2C_SDA')
add_via(14.78, 28.1, 'I2C_SDA')
# R7 SCLタップ
add_via(14.35, 26.5, 'I2C_SCL')
add_seg(14.35, 26.5, 14.35, 29.85, 0.15, 'B.Cu', 'I2C_SCL')
add_seg(14.35, 29.85, 19.4, 29.85, 0.15, 'B.Cu', 'I2C_SCL')
add_seg(19.4, 29.85, 19.4, 27.55, 0.15, 'B.Cu', 'I2C_SCL')
add_via(19.4, 27.55, 'I2C_SCL')

# ============ 5) U2 pad29/30 ネット割当 ============
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
    assert '(net ' not in m2.group(1), f"{ref}.{padnum} already has net"
    nb = blk[:m2.end(1)] + f'\t\t\t(net "{net}")\n' + blk[m2.end(1):]
    s = s[:st] + nb + s[j:]
set_pad_net('U2', '29', 'XTAL_N')
set_pad_net('U2', '30', 'XTAL_P')

# ============ 6) Y1/C16/C17 フットプリント ============
u = uuid.uuid4
def cap_fp(ref, val, x, y, rot, net1, net2):
    return f'''\t(footprint ""
\t\t(layer "F.Cu")
\t\t(uuid "{u()}")
\t\t(at {fmt(x)} {fmt(y)}{" "+fmt(rot) if rot else ""})
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
    pads = ''
    for num, px, py, net in [('1', -1.1, 0.8, 'XTAL_N'), ('2', 1.1, 0.8, 'GND'),
                             ('3', 1.1, -0.8, 'XTAL_P'), ('4', -1.1, -0.8, 'GND')]:
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
NEW.append(xtal_fp(16.3, 22.0))
NEW.append(cap_fp('C16', '18pF', 17.8, 24.5, 270, 'XTAL_N', 'GND'))   # pad1=N(タップ側)
NEW.append(cap_fp('C17', '18pF', 16.6, 21.76, 270, 'XTAL_P', 'GND'))  # pad1=N(Y1.3重なり)

# ============ 7) XTAL 配線（全F.Cu w0.15） ============
add_seg(7.75, 20.65, 7.75, 20.0, 0.15, 'F.Cu', 'XTAL_P')
add_seg(7.75, 20.0, 17.4, 20.0, 0.15, 'F.Cu', 'XTAL_P')
add_seg(17.4, 20.0, 17.4, 20.7, 0.15, 'F.Cu', 'XTAL_P')      # Y1.pad3直入
add_seg(8.25, 20.65, 8.25, 20.3, 0.15, 'F.Cu', 'XTAL_N')
add_seg(8.25, 20.3, 15.2, 20.3, 0.15, 'F.Cu', 'XTAL_N')
add_seg(15.2, 20.3, 15.2, 22.3, 0.15, 'F.Cu', 'XTAL_N')      # Y1.pad1直入
# C16タップ (XTAL_N: pad1下端→y23.62横→C16.1)
add_seg(15.2, 23.35, 15.2, 23.62, 0.15, 'F.Cu', 'XTAL_N')
add_seg(15.2, 23.62, 17.8, 23.62, 0.15, 'F.Cu', 'XTAL_N')
add_seg(17.8, 23.62, 17.8, 24.1, 0.15, 'F.Cu', 'XTAL_N')     # C16.1(N)パッドへ
# C17はパッド重なりでタップ（配線不要）

# ============ 挿入・保存 ============
tail = s.rfind('\t(embedded_fonts')
assert tail > 0
s = s[:tail] + ''.join(NEW) + s[tail:]
open(PCB, 'w').write(s)
print("OK: xtal v2 applied")
