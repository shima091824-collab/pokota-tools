#!/usr/bin/env python3
"""SW1 MSK12C02 フットプリント修正（3件目のフットプリントバグ）+ VBAT/VBAT_SW再配線
データシート(SHOU HAN MSK12C02-HB)封装尺寸:
- 信号端子3本 0.6×1.3 ピッチ1.5（rel x=-1.5/0/+1.5, y=+1.75）
- 位置決めNPTH Ø0.85 ×2 (rel ±1.5, 0)
- 四隅タブ: 上 1.05×0.7 (rel ±3.675,-1.45) / 下 1.05×1.1 (rel ±3.675,+1.55)
ネット: 1=VBAT / 2=VBAT_SW(COM) / 3=NC
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

def repl_seg(sx, sy, ex, ey, nsx, nsy, nex, ney, nw=None):
    global s
    m = re.search(seg_pat(sx, sy, ex, ey), s) or re.search(seg_pat(ex, ey, sx, sy), s)
    assert m, f"seg not found: ({sx},{sy})->({ex},{ey})"
    blk = m.group(0)
    blk = re.sub(r'\(start [\d.\-]+ [\d.\-]+\)', f'(start {fmt(nsx)} {fmt(nsy)})', blk)
    blk = re.sub(r'\(end [\d.\-]+ [\d.\-]+\)', f'(end {fmt(nex)} {fmt(ney)})', blk)
    if nw: blk = re.sub(r'\(width [\d.]+\)', f'(width {fmt(nw)})', blk)
    s = s[:m.start()] + blk + s[m.end():]

def del_via(x, y):
    global s
    pat = (r'\t\(via\n\t\t\(at %s %s\)\n\t\t\(size [\d.]+\)\n\t\t\(drill [\d.]+\)\n'
           r'\t\t\(layers "F\.Cu" "B\.Cu"\)\n(?:\t\t\(net "[^"]*"\)\n)?\t\t\(uuid "[^"]*"\)\n\t\)\n'
           ) % (re.escape(fmt(x)), re.escape(fmt(y)))
    m = re.search(pat, s)
    assert m, f"via not found ({x},{y})"
    s = s[:m.start()] + s[m.end():]

NEW = []
def add_seg(sx, sy, ex, ey, w, layer, net):
    NEW.append('\t(segment\n\t\t(start %s %s)\n\t\t(end %s %s)\n\t\t(width %s)\n'
               '\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'
               % (fmt(sx), fmt(sy), fmt(ex), fmt(ey), fmt(w), layer, net, uuid.uuid4()))
def add_via(x, y, net, size=0.4, drill=0.3):
    NEW.append('\t(via\n\t\t(at %s %s)\n\t\t(size %s)\n\t\t(drill %s)\n'
               '\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'
               % (fmt(x), fmt(y), fmt(size), fmt(drill), net, uuid.uuid4()))

# ============ 1) SW1フットプリント差し替え ============
i = s.find('(property "Reference" "SW1"')
st = s.rfind('(footprint', 0, i)
d = 0; j = st
while True:
    if s[j] == '(': d += 1
    elif s[j] == ')':
        d -= 1
        if d == 0: break
    j += 1
# 末尾の改行まで含めて削除
end = j + 1
if s[end] == '\n': end += 1

u = uuid.uuid4
def smd_pad(num, x, y, w, h, net=None):
    netline = f'\t\t\t(net "{net}")\n' if net else ''
    return (f'\t\t(pad "{num}" smd roundrect\n'
            f'\t\t\t(at {fmt(x)} {fmt(y)})\n'
            f'\t\t\t(size {fmt(w)} {fmt(h)})\n'
            f'\t\t\t(layers "F.Cu" "F.Mask" "F.Paste")\n'
            f'\t\t\t(roundrect_rratio 0.2)\n'
            f'{netline}'
            f'\t\t\t(uuid "{u()}")\n\t\t)\n')
def npth(x, y, dia):
    return (f'\t\t(pad "" np_thru_hole circle\n'
            f'\t\t\t(at {fmt(x)} {fmt(y)})\n'
            f'\t\t\t(size {fmt(dia)} {fmt(dia)})\n'
            f'\t\t\t(drill {fmt(dia)})\n'
            f'\t\t\t(layers "*.Cu" "*.Mask")\n'
            f'\t\t\t(uuid "{u()}")\n\t\t)\n')

sw1 = f'''\t(footprint ""
\t\t(layer "F.Cu")
\t\t(uuid "{u()}")
\t\t(at 4.5 28.85)
\t\t(property "Reference" "SW1"
\t\t\t(at 0 -2.6 0)
\t\t\t(layer "F.SilkS")
\t\t\t(uuid "{u()}")
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 0.8 0.8)
\t\t\t\t\t(thickness 0.12)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Value" "MSK12C02-HB"
\t\t\t(at 0 3.2 0)
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
\t\t\t(start -4.45 -2.05)
\t\t\t(end 4.45 2.65)
\t\t\t(stroke
\t\t\t\t(width 0.05)
\t\t\t\t(type solid)
\t\t\t)
\t\t\t(fill no)
\t\t\t(layer "F.CrtYd")
\t\t\t(uuid "{u()}")
\t\t)
\t\t(fp_rect
\t\t\t(start -4 -1.4)
\t\t\t(end 4 1.4)
\t\t\t(stroke
\t\t\t\t(width 0.1)
\t\t\t\t(type solid)
\t\t\t)
\t\t\t(fill no)
\t\t\t(layer "F.Fab")
\t\t\t(uuid "{u()}")
\t\t)
{smd_pad('1', -1.5, 1.75, 0.6, 1.3, 'VBAT')}{smd_pad('2', 0, 1.75, 0.6, 1.3, 'VBAT_SW')}{smd_pad('3', 1.5, 1.75, 0.6, 1.3)}{smd_pad('MP1', -3.675, -1.45, 1.05, 0.7)}{smd_pad('MP2', 3.675, -1.45, 1.05, 0.7)}{smd_pad('MP3', -3.675, 1.55, 1.05, 1.1)}{smd_pad('MP4', 3.675, 1.55, 1.05, 1.1)}{npth(-1.5, 0, 0.85)}{npth(1.5, 0, 0.85)}\t)
'''
s = s[:st] + sw1 + s[end:]

# ============ 2) VBAT 再配線 ============
# 旧 x1.2チェーン削除（西コーナータブ[0.3,1.35]と重なるため）
del_seg(2.875, 32.65, 1.2, 32.65)
del_seg(1.2, 32.65, 1.2, 26.95)
del_seg(1.2, 26.95, 2.0, 26.95)
del_seg(2.0, 26.95, 2.0, 27.2)
# J1.1 → pin1 直行
add_seg(2.875, 32.65, 2.88, 32.65, 0.5, 'F.Cu', 'VBAT')
add_seg(2.88, 32.65, 2.88, 30.9, 0.5, 'F.Cu', 'VBAT')   # pin1パッド(2.7-3.3, 29.95-31.25)に進入
# pin1 → トランク(y27.2)タップ: 横y30.3(w0.4) + 縦x2.1(w0.3)
add_seg(2.7, 30.3, 2.1, 30.3, 0.4, 'F.Cu', 'VBAT')
add_seg(2.1, 30.3, 2.1, 27.2, 0.3, 'F.Cu', 'VBAT')
# トランク東コーナータブ(MP2)回避ジョグ: x7.32南下→y28.2→x9.15復帰
repl_seg(2.0, 27.2, 14.5, 27.2, 2.1, 27.2, 7.32, 27.2)
add_seg(7.32, 27.2, 7.32, 28.2, 0.3, 'F.Cu', 'VBAT')
add_seg(7.32, 28.2, 9.15, 28.2, 0.3, 'F.Cu', 'VBAT')
add_seg(9.15, 28.2, 9.15, 27.2, 0.4, 'F.Cu', 'VBAT')
add_seg(9.15, 27.2, 14.5, 27.2, 0.5, 'F.Cu', 'VBAT')

# ============ 3) VBAT_SW 再配線 ============
# 旧 pad2(2.0,28.85)系の削除
del_via(2.0, 28.85)
del_seg(1.55, 28.85, 2.0, 28.85)
del_seg(2.0, 28.85, 2.0, 28.5)
del_seg(2.0, 28.5, 10.55, 28.5)
# C9.1ライン: y28.85。NPTH穴(3.0)西端x4.3・穴(6.0)は北ジョグで回避（放射0.254以上確認済み）
add_seg(4.3, 28.85, 5.05, 28.85, 0.5, 'F.Cu', 'VBAT_SW')
add_seg(5.05, 28.85, 5.05, 27.95, 0.3, 'F.Cu', 'VBAT_SW')
add_seg(5.05, 27.95, 6.85, 27.95, 0.3, 'F.Cu', 'VBAT_SW')
add_seg(6.85, 27.95, 6.85, 28.85, 0.3, 'F.Cu', 'VBAT_SW')
add_seg(6.85, 28.85, 7.0, 28.85, 0.3, 'F.Cu', 'VBAT_SW')
add_seg(7.0, 28.85, 10.55, 28.85, 0.5, 'F.Cu', 'VBAT_SW')
# pin2 → ライン合流 縦x4.5 w0.4
add_seg(4.5, 29.95, 4.5, 28.85, 0.4, 'F.Cu', 'VBAT_SW')
# pin2 → Bトランク(x1.55, C11/C12/U1系): via(4.5,31.4) + B南回り
add_via(4.5, 31.4, 'VBAT_SW', size=0.5)
add_seg(4.5, 31.4, 1.55, 31.4, 0.5, 'B.Cu', 'VBAT_SW')
add_seg(1.55, 31.4, 1.55, 28.85, 0.5, 'B.Cu', 'VBAT_SW')   # 既存Bトランク(13.0→28.85)に接続

# ============ 挿入・保存 ============
tail = s.rfind('\t(embedded_fonts')
assert tail > 0
s = s[:tail] + ''.join(NEW) + s[tail:]
open(PCB, 'w').write(s)
print("OK: SW1 footprint replaced + VBAT/VBAT_SW rerouted")
