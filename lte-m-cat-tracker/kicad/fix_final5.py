#!/usr/bin/env python3
"""
fix_final5.py: crossings 2件を修正
1. PROG経路変更: SCL縦x=17.5を回避（y=25.5経由→x=20.5→U4）
2. CC2経路変更: VUSB B.Cu横y=30.5を回避（x=20.0 B.Cu縦へ）
"""
import re, uuid, shutil

PCB = 'kicad/lte-m-cat-tracker.kicad_pcb'
shutil.copy(PCB, PCB + '.bak_fix_final5')
with open(PCB) as f:
    content = f.read()

changes = []

def make_seg(x1, y1, x2, y2, width, layer, net):
    uid = str(uuid.uuid4())
    return f'\t(segment\n\t\t(start {x1} {y1})\n\t\t(end {x2} {y2})\n\t\t(width {width})\n\t\t(layer "{layer}")\n\t\t(net "{net}")\n\t\t(uuid "{uid}")\n\t)'

def make_via(x, y, net, size=0.6, drill=0.3):
    uid = str(uuid.uuid4())
    return f'\t(via\n\t\t(at {x} {y})\n\t\t(size {size})\n\t\t(drill {drill})\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "{net}")\n\t\t(uuid "{uid}")\n\t)'

def find_and_remove(content, search_prefix):
    idx = content.find(search_prefix)
    if idx < 0:
        return content, False
    end = content.find('\n\t)', idx) + 3
    return content[:idx] + content[end:], True

insert_mark = '\n\t(via'

# ======================================================
# 1. PROG経路全削除・再追加
# ======================================================
# 削除: 4セグメント（(15.99,24.5)→(14.8,24.5)など）
for seg_prefix in [
    '\t(segment\n\t\t(start 15.99 24.5)\n\t\t(end 14.8 24.5)',
    '\t(segment\n\t\t(start 14.8 24.5)\n\t\t(end 14.8 22.2)',
    '\t(segment\n\t\t(start 14.8 22.2)\n\t\t(end 19.025 22.2)',
    '\t(segment\n\t\t(start 19.025 22.2)\n\t\t(end 19.025 21.865)',
]:
    content, ok = find_and_remove(content, seg_prefix)
    if ok:
        changes.append(f'PROG旧セグ削除: {seg_prefix[30:60]}...')

# 追加: (15.99,24.5)→(15.99,25.5)→(20.5,25.5)→(20.5,21.865)→(19.025,21.865)
new_prog = [
    make_seg(15.99, 24.5, 15.99, 25.5, 0.2, 'F.Cu', 'PROG'),
    make_seg(15.99, 25.5, 20.5, 25.5, 0.2, 'F.Cu', 'PROG'),
    make_seg(20.5, 25.5, 20.5, 21.865, 0.2, 'F.Cu', 'PROG'),
    make_seg(20.5, 21.865, 19.025, 21.865, 0.2, 'F.Cu', 'PROG'),
]
content = content.replace(insert_mark, '\n' + '\n'.join(new_prog) + insert_mark, 1)
changes.append('PROG新経路: y=25.5横→x=20.5縦→U4')

# ======================================================
# 2. CC2: F.Cu横(16.01,29.8)→(17.5,29.8) + via(17.5,29.8) + B.Cu縦(17.5,29.8→34.2) + B.Cu横(17.5,34.2→11.25,34.2)
#    を削除して x=20.0 経由に変更
# ======================================================
for seg_prefix in [
    '\t(segment\n\t\t(start 16.01 29.8)\n\t\t(end 17.5 29.8)',
    '\t(segment\n\t\t(start 17.5 29.8)\n\t\t(end 17.5 34.2)',
    '\t(segment\n\t\t(start 17.5 34.2)\n\t\t(end 11.25 34.2)',
]:
    content, ok = find_and_remove(content, seg_prefix)
    if ok:
        changes.append(f'CC2旧セグ削除: {seg_prefix[30:60]}...')

# via(17.5,29.8)削除
content, ok = find_and_remove(content, '\t(via\n\t\t(at 17.5 29.8)')
if ok: changes.append('CC2旧via(17.5,29.8)削除')

# 追加: (16.01,29.8)→(20.0,29.8)→via→B.Cu縦(20.0,34.2)→B.Cu横(11.25,34.2)
new_cc2 = [
    make_seg(16.01, 29.8, 20.0, 29.8, 0.2, 'F.Cu', 'CC2'),
    make_via(20.0, 29.8, 'CC2'),
    make_seg(20.0, 29.8, 20.0, 34.2, 0.2, 'B.Cu', 'CC2'),
    make_seg(20.0, 34.2, 11.25, 34.2, 0.2, 'B.Cu', 'CC2'),
]
content = content.replace(insert_mark, '\n' + '\n'.join(new_cc2) + insert_mark, 1)
changes.append('CC2新経路: x=20.0 B.Cu縦経由')

with open(PCB, 'w') as f:
    f.write(content)

print(f'修正完了 ({len(changes)}件):')
for c in changes:
    print(f'  ✓ {c}')
