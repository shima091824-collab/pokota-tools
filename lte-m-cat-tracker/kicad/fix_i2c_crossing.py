#!/usr/bin/env python3
"""
I2C_SCL × I2C_SDA crossing を解消する

問題:
  I2C_SCL水平 (9.75,26.5)→(15,26.5), 縦(15,26.5)→(15,24.85), (15.5,24.85)→(15.5,25.2)
  I2C_SDA縦(13.65,27)→(13.65,23.4) が SCL水平y=26.5と x=13.65で交差

修正:
  SDA縦をx=18.0に移動
  x=18.0はSCL縦x=17.5右端17.6からgap=0.3mm ✅
  SCL水平y=24.85右端x=15.6からgap大 ✅
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

# 削除: x=15.5で追加したトレース（fix_i2c_crossing.py前回分）
# および元のx=13.65トレース（もし残っていれば）
patterns_to_remove = [
    # x=15.5で追加したトレース
    r'\t\(segment\n\t\t\(start 9\.25 27\)\n\t\t\(end 15\.5 27\)\n\t\t\(width 0\.2\)\n\t\t\(layer "F\.Cu"\)\n\t\t\(net "I2C_SDA"\)\n\t\t\(uuid "[^"]+"\)\n\t\)\n',
    r'\t\(segment\n\t\t\(start 15\.5 27\)\n\t\t\(end 15\.5 23\.4\)\n\t\t\(width 0\.2\)\n\t\t\(layer "F\.Cu"\)\n\t\t\(net "I2C_SDA"\)\n\t\t\(uuid "[^"]+"\)\n\t\)\n',
    r'\t\(segment\n\t\t\(start 15\.5 23\.4\)\n\t\t\(end 13\.75 23\.4\)\n\t\t\(width 0\.2\)\n\t\t\(layer "F\.Cu"\)\n\t\t\(net "I2C_SDA"\)\n\t\t\(uuid "[^"]+"\)\n\t\)\n',
    # 念のため x=13.65版も
    r'\t\(segment\n\t\t\(start 9\.25 27\)\n\t\t\(end 13\.65 27\)\n\t\t\(width 0\.2\)\n\t\t\(layer "F\.Cu"\)\n\t\t\(net "I2C_SDA"\)\n\t\t\(uuid "[^"]+"\)\n\t\)\n',
    r'\t\(segment\n\t\t\(start 13\.65 27\)\n\t\t\(end 13\.65 23\.4\)\n\t\t\(width 0\.2\)\n\t\t\(layer "F\.Cu"\)\n\t\t\(net "I2C_SDA"\)\n\t\t\(uuid "[^"]+"\)\n\t\)\n',
    r'\t\(segment\n\t\t\(start 13\.65 23\.4\)\n\t\t\(end 13\.75 23\.4\)\n\t\t\(width 0\.2\)\n\t\t\(layer "F\.Cu"\)\n\t\t\(net "I2C_SDA"\)\n\t\t\(uuid "[^"]+"\)\n\t\)\n',
]

removed = 0
for pat in patterns_to_remove:
    new_content, n = re.subn(pat, '', content)
    if n:
        content = new_content
        removed += n
        print(f'削除 {n}件')

# 新しいルート: x=18.0経由
# SDA: U2.pad14(9.25,25.95)→下→(9.25,27)→右→(18.0,27)→上→(18.0,23.4)→左→(13.75,23.4)
new_traces = (
    new_seg(9.25, 27, 18.0, 27, 0.2, 'F.Cu', 'I2C_SDA') +
    new_seg(18.0, 27, 18.0, 23.4, 0.2, 'F.Cu', 'I2C_SDA') +
    new_seg(18.0, 23.4, 13.75, 23.4, 0.2, 'F.Cu', 'I2C_SDA')
)

first_seg = content.find('\t(segment\n')
if first_seg >= 0:
    content = content[:first_seg] + new_traces + content[first_seg:]
    print(f'新トレース3本追加(x=18.0) ✅')

with open(PCB_FILE, 'w') as f:
    f.write(content)

print(f'完了 (removed={removed}, added=3)')
