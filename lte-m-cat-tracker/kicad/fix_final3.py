#!/usr/bin/env python3
"""
fix_final3.py: fix_final2の誤配線を修正
- CC1/CC2: via+B.Cu経由に変更
- LED_ANODE: 経路修正（CHRG/LED1.pad1を回避）
- ANT3: x=2.3に移動（pad1 edge 0.2mm確保）
"""
import re, uuid, shutil

PCB = 'kicad/lte-m-cat-tracker.kicad_pcb'
shutil.copy(PCB, PCB + '.bak_fix_final3')
with open(PCB) as f:
    content = f.read()

changes = []

def make_seg(x1, y1, x2, y2, width, layer, net):
    uid = str(uuid.uuid4())
    return f'\t(segment\n\t\t(start {x1} {y1})\n\t\t(end {x2} {y2})\n\t\t(width {width})\n\t\t(layer "{layer}")\n\t\t(net "{net}")\n\t\t(uuid "{uid}")\n\t)'

def make_via(x, y, net, size=0.6, drill=0.3):
    uid = str(uuid.uuid4())
    return f'\t(via\n\t\t(at {x} {y})\n\t\t(size {size})\n\t\t(drill {drill})\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "{net}")\n\t\t(uuid "{uid}")\n\t)'

def remove_seg(content, x1, y1, x2, y2, net):
    """指定セグメントを削除（どちらの順でもOK）"""
    for sx,sy,ex,ey in [(x1,y1,x2,y2),(x2,y2,x1,y1)]:
        pat = r'\t\(segment\n\t\t\(start ' + re.escape(f'{sx} {sy}') + r'\)\n\t\t\(end ' + re.escape(f'{ex} {ey}') + r'\)\n\t\t\(width [^\)]+\)\n\t\t\(layer "[^"]+"\)\n\t\t\(net "' + re.escape(net) + r'"\)\n\t\t\(uuid "[^"]+"\)\n\t\)'
        new = re.sub(pat, '', content)
        if new != content:
            return new
    return content

# ======================================================
# 1. fix_final2の誤配線を削除
# ======================================================
# CC1の誤経路（横y=30.2の後x=11.25縦）
content = remove_seg(content, 13.51,30.2, 11.25,30.2, 'CC1')
content = remove_seg(content, 11.25,30.2, 11.25,30.8, 'CC1')
changes.append('CC1誤配線削除')

# CC2の誤経路
content = remove_seg(content, 16.01,29.8, 11.25,29.8, 'CC2')
content = remove_seg(content, 11.25,29.8, 11.25,34.2, 'CC2')
changes.append('CC2誤配線削除')

# LED_ANODEの誤経路
content = remove_seg(content, 15.49,26.3, 15.49,27.5, 'LED_ANODE')
content = remove_seg(content, 15.49,27.5, 16.485,27.5, 'LED_ANODE')
changes.append('LED_ANODE誤配線削除')

# WIFI_ANTの誤末端（0.9経由）
content = remove_seg(content, 5.8,20.87, 0.9,20.87, 'WIFI_ANT')
content = remove_seg(content, 0.9,20.87, 0.9,19.0, 'WIFI_ANT')
changes.append('WIFI_ANT誤末端削除')

# ======================================================
# 2. ANT3をx=2.2→2.3に移動（pad1左端が基板端から0.2mm確保）
# ======================================================
content = content.replace('(at 2.2 19)\n', '(at 2.3 19)\n')
changes.append('ANT3 (2.2,19)→(2.3,19) 移動')

# ======================================================
# 3. 正しい配線を挿入
# ======================================================
insert_mark = '\n\t(via'
new_items = []

# CC1: R1.pad2(13.51,30.2) → via(13.51,32.0) → B.Cu横y=32 → via(11.25,32.0) → F.Cu縦→J2.A5(11.25,30.8)
new_items += [
    make_seg(13.51, 30.2, 13.51, 32.0, 0.2, 'F.Cu', 'CC1'),  # F.Cu縦
    make_via(13.51, 32.0, 'CC1'),
    make_seg(13.51, 32.0, 11.25, 32.0, 0.2, 'B.Cu', 'CC1'),  # B.Cu横
    make_via(11.25, 32.0, 'CC1'),
    make_seg(11.25, 32.0, 11.25, 30.8, 0.2, 'F.Cu', 'CC1'),  # F.Cu縦
]

# CC2: R2.pad2(16.01,29.8) → F.Cu縦 → via(16.01,34.2) → B.Cu横 → via(11.25,34.2) → J2.B5
new_items += [
    make_seg(16.01, 29.8, 16.01, 34.2, 0.2, 'F.Cu', 'CC2'),  # F.Cu縦
    make_via(16.01, 34.2, 'CC2'),
    make_seg(16.01, 34.2, 11.25, 34.2, 0.2, 'B.Cu', 'CC2'),  # B.Cu横
    make_via(11.25, 34.2, 'CC2'),
]
# J2.B5はSMDパッドなのでviaから直接接続（viaのF.Cuがパッドに接触）

# LED_ANODE: R4.pad1(15.49,26.3) → 縦y=25.8 → 横x=16.485 → 縦→LED1.pad2(16.485,27.5)
# y=25.8はCHRG横y=26.3から0.45mm離れている（幅0.2mm考慮でgap=0.35mm）✓
new_items += [
    make_seg(15.49, 26.3, 15.49, 25.8, 0.2, 'F.Cu', 'LED_ANODE'),
    make_seg(15.49, 25.8, 16.485, 25.8, 0.2, 'F.Cu', 'LED_ANODE'),
    make_seg(16.485, 25.8, 16.485, 27.5, 0.2, 'F.Cu', 'LED_ANODE'),
]

# WIFI_ANT: ANT3が(2.3,19)に移動したのでpad1=(1.0,19.0)
# (5.8,20.87)→(1.0,20.87)→(1.0,19.0)
new_items += [
    make_seg(5.8, 20.87, 1.0, 20.87, 0.2, 'F.Cu', 'WIFI_ANT'),
    make_seg(1.0, 20.87, 1.0, 19.0, 0.2, 'F.Cu', 'WIFI_ANT'),
]

insert_all = '\n' + '\n'.join(new_items)
content = content.replace(insert_mark, insert_all + insert_mark, 1)
changes.append(f'CC1/CC2/LED_ANODE/WIFI_ANT 正しい配線追加 ({len(new_items)}要素)')

with open(PCB, 'w') as f:
    f.write(content)

print(f'修正完了 ({len(changes)}件):')
for c in changes:
    print(f'  ✓ {c}')
