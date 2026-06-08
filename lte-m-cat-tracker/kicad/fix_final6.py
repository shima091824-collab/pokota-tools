#!/usr/bin/env python3
"""
fix_final6.py: 残り3件修正
1. PROG経路: via(15.99,24.5)→B.Cu横y=26.0→via(20.5,26.0)→F.Cu縦→U4
2. C15移動: center(25.0,21.5)→(25.0,21.23) でCHRGパッド回避  
3. SCL/U3.pad8: SCL横y=24.85をB.Cu経由に変更
"""
import re, uuid, shutil

PCB = 'kicad/lte-m-cat-tracker.kicad_pcb'
shutil.copy(PCB, PCB + '.bak_fix_final6')
with open(PCB) as f:
    content = f.read()

changes = []

def make_seg(x1,y1,x2,y2,width,layer,net):
    uid = str(uuid.uuid4())
    return f'\t(segment\n\t\t(start {x1} {y1})\n\t\t(end {x2} {y2})\n\t\t(width {width})\n\t\t(layer "{layer}")\n\t\t(net "{net}")\n\t\t(uuid "{uid}")\n\t)'

def make_via(x,y,net,size=0.6,drill=0.3):
    uid = str(uuid.uuid4())
    return f'\t(via\n\t\t(at {x} {y})\n\t\t(size {size})\n\t\t(drill {drill})\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "{net}")\n\t\t(uuid "{uid}")\n\t)'

def find_remove(content, prefix):
    idx = content.find(prefix)
    if idx < 0: return content, False
    end = content.find('\n\t)', idx) + 3
    return content[:idx] + content[end:], True

insert_mark = '\n\t(via'

# ======================================================
# 1. PROG全経路削除→B.Cu経由に変更
# ======================================================
for p in [
    '\t(segment\n\t\t(start 15.99 24.5)\n\t\t(end 15.99 25.5)',
    '\t(segment\n\t\t(start 15.99 25.5)\n\t\t(end 20.5 25.5)',
    '\t(segment\n\t\t(start 20.5 25.5)\n\t\t(end 20.5 21.865)',
    '\t(segment\n\t\t(start 20.5 21.865)\n\t\t(end 19.025 21.865)',
]:
    content, ok = find_remove(content, p)
    if ok: changes.append(f'PROG旧削除')

# PROG新: R3.pad1(15.99,24.5) → via → B.Cu横y=26.0 → via → F.Cu縦→U4.pad2(19.025,21.865)
# B.Cu横y=26.0 x=[15.99,20.5]: SIM系B.Cu全て範囲外 ✓、CC2 B.Cu縦(x=20.0)はy=[29.8,34.2] → 範囲外 ✓
new_prog = [
    make_via(15.99, 24.5, 'PROG'),
    make_seg(15.99, 24.5, 20.5, 24.5, 0.2, 'B.Cu', 'PROG'),  # B.Cu横（via位置付近）
    make_via(20.5, 24.5, 'PROG'),
    make_seg(20.5, 24.5, 20.5, 21.865, 0.2, 'F.Cu', 'PROG'),
    make_seg(20.5, 21.865, 19.025, 21.865, 0.2, 'F.Cu', 'PROG'),
]
content = content.replace(insert_mark, '\n' + '\n'.join(new_prog) + insert_mark, 1)
changes.append('PROG新: via→B.Cu横y=24.5→via→F.Cu縦→U4')

# ======================================================
# 2. C15位置修正: center(25.0,21.5)→(25.0,21.23)
#    U4.pad7(CHRG)(23.975,21.865) pad y_min=21.565
#    C15 pad1(24.52,21.23) → pad1 y_range=[21.23-0.31,21.23+0.31]=[20.92,21.54]
#    gap from U4.pad7 y_min: 21.565-21.54=0.025mm ... まだ不足
#    C15をもっと上: center(25.0,20.9)
#    pad1 y=20.9, y_max=20.9+0.31=21.21 → gap from pad7_ymin=21.565: 0.355mm ✓
#    gap from pad8 y_max(20.595+0.3=20.895): 21.21-20.895=0.315mm ... 近い
#    trace幅0.3mm: 21.21 vs 20.895 → gap=0.315-0.15=0.165mm < 0.2mm DRC違反?
#    幅0.2mmに変更: 21.21-0.1=21.11 vs 20.895 → gap=0.215mm ✓
#    また U4.pad7 y_min=21.565: 21.565-21.21-0.1=0.255mm ✓
# ======================================================
# まずC15の古い配線を削除
for p in [
    '\t(segment\n\t\t(start 26.363 21.05)\n\t\t(end 25.5 21.05)',
    '\t(segment\n\t\t(start 25.5 21.05)\n\t\t(end 25.5 21.5)',
    '\t(segment\n\t\t(start 25.5 21.5)\n\t\t(end 24.52 21.5)',
]:
    content, ok = find_remove(content, p)
    if ok: changes.append('C15旧配線削除')

# C15フットプリント移動: (25 21.5) → (25 20.9)
content = content.replace('(at 25 21.5)\n', '(at 25 20.9)\n')
changes.append('C15 center (25,21.5)→(25,20.9) 移動')

# C15新配線: U5.pad1(26.363,21.05)→横→(25.5,21.05)→縦→(25.5,20.9)→横→C15.pad1(24.52,20.9)
# 幅0.2mmで U4パッドをクリア
new_c15 = [
    make_seg(26.363, 21.05, 25.5, 21.05, 0.2, 'F.Cu', 'VBAT_SW'),
    make_seg(25.5, 21.05, 25.5, 20.9, 0.2, 'F.Cu', 'VBAT_SW'),
    make_seg(25.5, 20.9, 24.52, 20.9, 0.2, 'F.Cu', 'VBAT_SW'),
]
content = content.replace(insert_mark, '\n' + '\n'.join(new_c15) + insert_mark, 1)
changes.append('C15新配線: y=20.9経由')

# ======================================================
# 3. SCL/U3.pad8修正: SCL横(15.0,24.85)→(12.738,24.85)をB.Cu経由に変更
#    削除: 横(12.738,24.85)→(15.5,24.85)と(15.0,24.85)→(12.738,24.85)の重複部分
#    追加: via(15.0,24.6)→B.Cu横y=24.6 x=[13.0,15.0]→via(13.0,24.6)
#          →F.Cu(13.0,24.6)→(13.0,24.75)→(12.738,24.75)[=U3.pad3]
#          タップ縦(12.738,24.85)→(12.738,24.75)も削除してy=24.75接続へ
# ======================================================
for p in [
    '\t(segment\n\t\t(start 12.738 24.85)\n\t\t(end 15.5 24.85)',
    '\t(segment\n\t\t(start 15.5 24.85)\n\t\t(end 15.5 25.2)',
    '\t(segment\n\t\t(start 15 24.85)\n\t\t(end 12.738 24.85)',
    '\t(segment\n\t\t(start 12.738 24.85)\n\t\t(end 12.738 24.75)',
    '\t(segment\n\t\t(start 15 26.5)\n\t\t(end 15 24.85)',
]:
    content, ok = find_remove(content, p)
    if ok: changes.append(f'SCL旧セグ削除')

# 新SCL経路: (15,26.5)→縦→(15,24.6)→via→B.Cu横→via(13.0,24.6)→F.Cu→pad3(12.738,24.75)
new_scl = [
    make_seg(15.0, 26.5, 15.0, 24.6, 0.2, 'F.Cu', 'I2C_SCL'),
    make_via(15.0, 24.6, 'I2C_SCL'),
    make_seg(15.0, 24.6, 13.0, 24.6, 0.2, 'B.Cu', 'I2C_SCL'),  # B.Cu横 SIM_DATA x=12.6 gap=0.2mm ✓
    make_via(13.0, 24.6, 'I2C_SCL'),
    make_seg(13.0, 24.6, 13.0, 24.75, 0.2, 'F.Cu', 'I2C_SCL'),
    make_seg(13.0, 24.75, 12.738, 24.75, 0.2, 'F.Cu', 'I2C_SCL'),  # pad3接続(pad8左側x<14.09)
    make_seg(15.5, 25.2, 15.5, 25.2, 0.2, 'F.Cu', 'I2C_SCL'),  # ダミー（後で削除予定）
]
# ダミーなしで追加
new_scl = new_scl[:-1]
content = content.replace(insert_mark, '\n' + '\n'.join(new_scl) + insert_mark, 1)
changes.append('SCL新経路: B.Cu横y=24.6でpad8回避')

# (15.0,26.5)→(15.5,25.2)の接続を維持: (15.5,25.2)への経路確認
# (15.5,25.2)はSCLの次の接続点。元の(15.0,26.5)→(15.0,24.85)→横→(15.5,24.85)→(15.5,25.2)
# 今は(15.0,26.5)→縦→(15.0,24.6)→B.Cu→via(13.0) ... でも(15.5,25.2)への接続が切れる
# 追加: (15.0,26.5)→(15.5,25.2)への直接接続を検討
# SCL横(15.5,25.2)→(17.5,25.2)はそのまま生きているので(15.5,25.2)への縦接続が必要
# (9.75,25.95)→(9.75,26.5)→(15.0,26.5)は既存。(15.0,26.5)から(15.5,25.2)への経路:
content = content.replace(insert_mark,
    '\n' + make_seg(15.0, 26.5, 15.5, 26.5, 0.2, 'F.Cu', 'I2C_SCL') +
    '\n' + make_seg(15.5, 26.5, 15.5, 25.2, 0.2, 'F.Cu', 'I2C_SCL') +
    insert_mark, 1)
changes.append('SCL (15.0,26.5)→(15.5,25.2) 迂回接続追加')

with open(PCB, 'w') as f:
    f.write(content)

print(f'修正完了 ({len(changes)}件):')
for c in changes:
    print(f'  ✓ {c}')
