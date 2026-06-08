#!/usr/bin/env python3
"""
残り問題を全解消する

修正1: GNDビア(16.5,26.5)削除
  - R4.pad2[CHRG](16.51,26.3)と近接で短絡
  - 他のGNDビア(29.5系)でF.Cu/B.Cu接続は維持される

修正2: I2C_SDA水平をB.Cu経由で SCL縦との交差解消
  現在: (18.0,23.4)→(13.75,23.4) F.Cu がSCL縦x=17.5(y=21.5→25.2)と交差
  変更: F.Cu削除 → via(18.0,23.4) + B.Cu(18.0,23.4)→(13.75,23.4) + via(13.75,23.4) + F.Cu(13.75,23.4)→(13.75,23.738)
"""

import re, uuid

PCB_FILE = '/Users/m2mac/lte-m-cat-tracker/kicad/lte-m-cat-tracker.kicad_pcb'

with open(PCB_FILE) as f:
    content = f.read()

def U():
    return str(uuid.uuid4())

def new_seg(x1, y1, x2, y2, w, layer, net):
    return (f'\t(segment\n'
            f'\t\t(start {x1} {y1})\n'
            f'\t\t(end {x2} {y2})\n'
            f'\t\t(width {w})\n'
            f'\t\t(layer "{layer}")\n'
            f'\t\t(net "{net}")\n'
            f'\t\t(uuid "{U()}")\n'
            f'\t)\n')

def new_via(x, y, net, size=0.6, drill=0.3):
    return (f'\t(via\n'
            f'\t\t(at {x} {y})\n'
            f'\t\t(size {size})\n'
            f'\t\t(drill {drill})\n'
            f'\t\t(layers "F.Cu" "B.Cu")\n'
            f'\t\t(net "{net}")\n'
            f'\t\t(uuid "{U()}")\n'
            f'\t)\n')

# --- 修正1: GNDビア(16.5,26.5)削除 ---
old_via = ('\t\t(at 16.5 26.5)\n'
           '\t\t(size 0.6)\n'
           '\t\t(drill 0.3)\n'
           '\t\t(layers "F.Cu" "B.Cu")\n'
           '\t\t(net "GND")')
# viaブロック全体を削除
via_pattern = (r'\t\(via\n'
               r'\t\t\(at 16\.5 26\.5\)\n'
               r'\t\t\(size 0\.6\)\n'
               r'\t\t\(drill 0\.3\)\n'
               r'\t\t\(layers "F\.Cu" "B\.Cu"\)\n'
               r'\t\t\(net "GND"\)\n'
               r'(?:\t\t\(uuid "[^"]+"\)\n)?'
               r'\t\)\n')
content, n = re.subn(via_pattern, '', content)
print(f'修正1: GNDビア(16.5,26.5)削除 {"✅" if n else "❌"} ({n}件)')

# --- 修正2: I2C_SDA水平をB.Cu経由に変更 ---
# 削除: F.Cu水平 (18.0,23.4)→(13.75,23.4)
pat_fcuH = (r'\t\(segment\n'
            r'\t\t\(start 18 23\.4\)\n'
            r'\t\t\(end 13\.75 23\.4\)\n'
            r'\t\t\(width 0\.2\)\n'
            r'\t\t\(layer "F\.Cu"\)\n'
            r'\t\t\(net "I2C_SDA"\)\n'
            r'(?:\t\t\(uuid "[^"]+"\)\n)?'
            r'\t\)\n')
content, n2 = re.subn(pat_fcuH, '', content)
print(f'修正2a: SDA F.Cu水平削除 {"✅" if n2 else "❌"} ({n2}件)')

# 追加: via(18.0,23.4) + B.Cu水平 + via(13.75,23.4) + F.Cu縦→U3.pad11
new_items = (
    new_via(18.0, 23.4, 'I2C_SDA') +
    new_seg(18.0, 23.4, 13.75, 23.4, 0.2, 'B.Cu', 'I2C_SDA') +
    new_via(13.75, 23.4, 'I2C_SDA') +
    new_seg(13.75, 23.4, 13.75, 23.738, 0.2, 'F.Cu', 'I2C_SDA')
)

# 既存のF.Cu縦 (13.75,23.4)→(13.75,23.738)が既にある場合は追加しない
already_exists = re.search(
    r'\(start 13\.75 23\.4\).*?\(end 13\.75 23\.738\).*?I2C_SDA', content, re.DOTALL)

if already_exists:
    # via×2とB.Cu水平のみ追加
    new_items = (
        new_via(18.0, 23.4, 'I2C_SDA') +
        new_seg(18.0, 23.4, 13.75, 23.4, 0.2, 'B.Cu', 'I2C_SDA') +
        new_via(13.75, 23.4, 'I2C_SDA')
    )
    print('  注: F.Cu縦(13.75→23.738)は既存なのでskip')

first_seg = content.find('\t(segment\n')
if first_seg >= 0:
    content = content[:first_seg] + new_items + content[first_seg:]
    print(f'修正2b: SDA B.Cu経由トレース追加 ✅')

with open(PCB_FILE, 'w') as f:
    f.write(content)
print('PCBファイル更新完了')
