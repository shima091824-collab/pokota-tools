#!/usr/bin/env python3
"""致命修正#2 v4: 40MHz水晶 Y1=HD 7D040000M01(2016/C648974)+C16/C17をU2東側に追加
v3からの修正: Y1パッド0.9x0.8修正 / スパインはSCL-U3.1チェーン・VBAT x24.3縦・RST x24 B縦を回避し
Bリンク延長(18.5→21.5)から給電 / R7=(13.95,26.45) / C8=(25.5,25.78)r180(C10パッド重なり給電) /
R6給電はvia(14.8,25.9)+B縦 / GND via 4本削除+3本新設 / トランク西トリム→18.5
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
del_seg(9.6, 20.4, 5.3, 20.4)
del_seg(11.7, 20.4, 9.6, 20.4)
for c in [(9.6,19.6,9.6,20.4),(11.7,19.6,11.7,20.4),(12.0,19.6,11.7,19.6),
          (12.0,20.3,12.0,19.6),(13.0,20.3,12.0,20.3),(13.0,19.6,13.0,20.3)]:
    del_seg(*c)
for c in [(13.51,19.6,13.51,19.8),(12.49,20.3,12.49,21.0),(8.02,19.6,8.02,19.8),
          (10.02,19.6,10.02,19.8),(12.12,20.3,12.12,22.0),(14.02,19.6,14.02,22.0),
          (15.99,19.6,15.99,21.5)]:
    del_seg(*c)
del_seg(10.73, 19.8, 10.73, 19.2)
del_seg(10.98, 19.8, 10.73, 19.8)
for c in [(15.0,25.2,15.5,25.2),(15.5,25.2,17.5,25.2),(17.5,25.2,17.5,21.5),(17.5,21.5,17.01,21.5)]:
    del_seg(*c)
for c in [(15.2,20.5,15.2,21.3),(15.2,21.3,15.5,21.3),(15.5,21.3,15.5,23.3),
          (15.5,23.3,14.2625,23.3),(13.35,21.0,13.51,21.0),
          (15.35,19.45,15.35,20.1),(15.35,20.1,15.2,20.1),(15.2,20.1,15.2,20.5),
          (13.35,19.45,13.35,21.0)]:
    del_seg(*c)
del_seg(11.8, 19.6, 11.8, 25.5)
del_seg(11.8, 19.6, 11.8, 25.5)
# GNDステッチvia: 経路上4本削除 + スタブ
del_seg(16.86, 24.5, 16.86, 23.4)
del_seg(17.01, 24.5, 16.86, 24.5)
for c in [(16.86,23.4),(18.1,23.0),(26.6,26.5),(19.5,23.5)]:
    del_via(*c)
# トリム
repl_seg(5.3, 19.6, 8.3, 19.6, 5.3, 19.6, 6.7, 19.6)
repl_seg(7.75, 19.6, 7.75, 25.95, 7.75, 18.05, 7.75, 25.95)
repl_seg(12.28, 19.45, 15.35, 19.45, 12.28, 19.45, 14.1, 19.45)
repl_seg(28.0, 19.6, 13.0, 19.6, 28.0, 19.6, 18.5, 19.6)
# CHRG横線 y26.3→26.45
repl_seg(22.0, 26.3, 16.51, 26.3, 22.0, 26.45, 16.51, 26.45)
repl_seg(22.0, 21.865, 22.0, 26.3, 22.0, 21.865, 22.0, 26.45)
# via削除
del_via(7.75, 19.6)
del_via(11.8, 19.6)
del_via(11.8, 19.6)
del_via(15.2, 20.5)
del_via(13.35, 21.0)

# ============ 2) +3.3V 再構成 ============
add_via(7.75, 18.05, '+3.3V')
add_seg(5.4, 20.4, 5.4, 18.05, 0.25, 'F.Cu', '+3.3V')
add_seg(5.4, 18.05, 20.15, 18.05, 0.25, 'F.Cu', '+3.3V')
add_seg(20.15, 18.05, 20.15, 19.6, 0.25, 'F.Cu', '+3.3V')
add_via(18.5, 19.6, '+3.3V')                       # via-A（トランク上）
add_seg(18.5, 19.6, 18.5, 23.1, 0.25, 'B.Cu', '+3.3V')
add_seg(18.5, 23.1, 11.8, 23.1, 0.25, 'B.Cu', '+3.3V')
add_seg(11.8, 23.1, 11.8, 25.5, 0.3, 'B.Cu', '+3.3V')
# C7再給電
add_seg(12.12, 22.3, 12.12, 23.0, 0.2, 'F.Cu', '+3.3V')
add_seg(12.12, 23.0, 11.8, 23.0, 0.2, 'F.Cu', '+3.3V')
add_seg(11.8, 23.0, 11.8, 25.4, 0.2, 'F.Cu', '+3.3V')
# ポケットAスパイン（Bリンク延長から給電・SCLチェーン/CHRG/VBAT縦を回避）
add_seg(18.5, 23.1, 21.5, 23.1, 0.25, 'B.Cu', '+3.3V')   # リンク東延長
add_seg(21.5, 23.1, 21.5, 25.05, 0.25, 'B.Cu', '+3.3V')
add_via(21.5, 25.05, '+3.3V')
add_seg(21.5, 25.1, 15.4, 25.1, 0.3, 'F.Cu', '+3.3V')    # スパインF（西端はSCL縦x15.0の東）
# キャップ給電スタブ
add_seg(17.52, 25.47, 17.52, 25.175, 0.15, 'F.Cu', '+3.3V')   # C5.1
add_seg(19.12, 25.47, 19.12, 25.175, 0.15, 'F.Cu', '+3.3V')   # C6.1
# R6給電（S=+3.3V: via+B縦でBリンクへ）
add_via(14.8, 25.9, '+3.3V')
add_seg(14.8, 25.9, 14.8, 23.1, 0.2, 'B.Cu', '+3.3V')
# R7給電（pad1西=+3.3V → via(11.8,25.5)系へ）
add_seg(13.19, 26.45, 12.6, 26.45, 0.15, 'F.Cu', '+3.3V')
add_seg(12.6, 26.45, 12.6, 25.7, 0.15, 'F.Cu', '+3.3V')
add_seg(12.6, 25.7, 11.875, 25.7, 0.15, 'F.Cu', '+3.3V')
# R5給電（pad2西 → C10.pad1内へ）
add_seg(27.19, 26.4, 27.4, 26.4, 0.15, 'F.Cu', '+3.3V')
add_seg(27.4, 26.4, 27.4, 25.4, 0.15, 'F.Cu', '+3.3V')
add_seg(27.4, 25.4, 26.9, 25.4, 0.15, 'F.Cu', '+3.3V')

# ============ 3) SDA 再給電（U3.4 + R6タップ） ============
add_seg(14.1, 19.45, 14.1, 22.0, 0.15, 'B.Cu', 'I2C_SDA')
add_via(14.1, 22.0, 'I2C_SDA')
add_seg(14.1, 22.0, 14.1, 23.3, 0.15, 'F.Cu', 'I2C_SDA')
add_seg(14.1, 23.3, 14.7, 23.3, 0.15, 'F.Cu', 'I2C_SDA')      # U3.4(14.2625)を経由しR6側へ延長
add_seg(14.2625, 23.3, 14.2625, 23.75, 0.0, 'F.Cu', 'I2C_SDA') if False else None
add_seg(14.7, 23.3, 14.7, 24.4, 0.15, 'F.Cu', 'I2C_SDA')      # R6.pad2(N)へ

# ============ 4) SCLタップ（R7） ============
add_seg(14.71, 26.45, 14.9, 26.45, 0.15, 'F.Cu', 'I2C_SCL')
add_seg(14.9, 26.45, 14.9, 26.5, 0.15, 'F.Cu', 'I2C_SCL')
add_seg(14.9, 26.5, 15.0, 26.5, 0.15, 'F.Cu', 'I2C_SCL')

# ============ 5) 部品移設 ============
move_part('C5', 18.0, 25.78)
move_part('C6', 19.6, 25.78)
move_part('C8', 25.5, 25.78, 180)
move_part('R5', 27.7, 26.4, 180)
move_part('R6', 14.95, 25.0, 90)
move_part('R7', 13.95, 26.45)

# ============ 6) U2 pad29/30 ネット割当 ============
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

# ============ 7) Y1(2016)/C16/C17 フットプリント ============
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
    for num, px, py, net in [('1', -0.7, 0.55, 'XTAL_N'), ('2', -0.7, -0.55, 'GND'),
                             ('3', 0.7, -0.55, 'XTAL_P'), ('4', 0.7, 0.55, 'GND')]:
        pads += f'''\t\t(pad "{num}" smd roundrect
\t\t\t(at {fmt(px)} {fmt(py)})
\t\t\t(size 0.9 0.8)
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
\t\t\t(at 0 -1.8 0)
\t\t\t(layer "F.SilkS")
\t\t\t(uuid "{u()}")
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 0.8 0.8)
\t\t\t\t\t(thickness 0.12)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Value" "7D040000M01 40MHz 12pF"
\t\t\t(at 0 1.8 0)
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
\t\t\t(start -1.4 -1.2)
\t\t\t(end 1.4 1.2)
\t\t\t(stroke
\t\t\t\t(width 0.05)
\t\t\t\t(type solid)
\t\t\t)
\t\t\t(fill no)
\t\t\t(layer "F.CrtYd")
\t\t\t(uuid "{u()}")
\t\t)
\t\t(fp_rect
\t\t\t(start -1 -0.8)
\t\t\t(end 1 0.8)
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
NEW.append(xtal_fp(16.0, 21.8))
NEW.append(cap_fp('C16', '18pF', 17.6, 22.6, 270, 'GND', 'XTAL_N'))
NEW.append(cap_fp('C17', '18pF', 17.6, 20.9, 270, 'XTAL_P', 'GND'))

# ============ 8) XTAL 配線（全F.Cu w0.15） ============
add_seg(7.75, 20.65, 7.75, 19.7, 0.15, 'F.Cu', 'XTAL_P')
add_seg(7.75, 19.7, 17.6, 19.7, 0.15, 'F.Cu', 'XTAL_P')
add_seg(16.7, 19.7, 16.7, 20.85, 0.15, 'F.Cu', 'XTAL_P')
add_seg(17.6, 19.7, 17.6, 20.11, 0.15, 'F.Cu', 'XTAL_P')
add_seg(8.25, 20.65, 8.25, 19.98, 0.15, 'F.Cu', 'XTAL_N')
add_seg(8.25, 19.98, 16.0, 19.98, 0.15, 'F.Cu', 'XTAL_N')
add_seg(16.0, 19.98, 16.0, 22.35, 0.15, 'F.Cu', 'XTAL_N')
add_seg(16.0, 22.35, 15.5, 22.35, 0.15, 'F.Cu', 'XTAL_N')
add_seg(16.0, 22.35, 16.0, 23.45, 0.15, 'F.Cu', 'XTAL_N')
add_seg(16.0, 23.45, 17.6, 23.45, 0.15, 'F.Cu', 'XTAL_N')
add_seg(17.6, 23.45, 17.6, 23.39, 0.15, 'F.Cu', 'XTAL_N')
# GND via-in-pad（孤立対策 φ0.5）
add_via(15.3, 21.25, 'GND')   # Y1.2
add_via(16.7, 22.35, 'GND')   # Y1.4
add_via(17.6, 21.45, 'GND')   # C17.S
add_via(17.6, 22.05, 'GND')   # C16.N
add_via(17.2, 18.74, 'GND')   # U1.19
add_via(19.4, 18.74, 'GND')   # U1.21
add_via(6.98, 19.0, 'GND')    # C4.2
add_via(18.48, 25.78, 'GND')  # C5.2
add_via(20.08, 25.78, 'GND')  # C6.2
add_via(25.02, 25.78, 'GND')  # C8.2
# GNDステッチ新設（削除4本の代替・空き地）
add_via(13.45, 27.5, 'GND')
add_via(26.0, 27.3, 'GND')
add_via(28.8, 27.5, 'GND')

# ============ 挿入・保存 ============
tail = s.rfind('\t(embedded_fonts')
assert tail > 0
s = s[:tail] + ''.join(NEW) + s[tail:]
open(PCB, 'w').write(s)
print("OK: xtal v4 applied")
