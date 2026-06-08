#!/usr/bin/env python3
"""
fix_final9.py: 最終統合修正
1. SCL横を(9.75,26.5)→(15.0,26.5)に戻す（R4.pad1 x=15.49の左側で止める）
   + (15.0,26.5)→縦(15.0,25.2)→横(15.5,25.2) で迂回
2. LED_ANODEをB.Cu経由（F.CuのSCLと完全分離）
3. SCL B.Cu via位置: (13.0,24.6)→(13.5,24.6) で+3.3V配線との干渉解消
4. C15横y=19.9: U4.pad8との短絡解消確認
"""
import re, uuid, shutil

PCB = 'kicad/lte-m-cat-tracker.kicad_pcb'
shutil.copy(PCB, PCB + '.bak_fix_final9')
with open(PCB) as f: content = f.read()
changes = []

def make_seg(x1,y1,x2,y2,w,layer,net):
    return f'\t(segment\n\t\t(start {x1} {y1})\n\t\t(end {x2} {y2})\n\t\t(width {w})\n\t\t(layer "{layer}")\n\t\t(net "{net}")\n\t\t(uuid "{uuid.uuid4()}")\n\t)'
def make_via(x,y,net,s=0.6,d=0.3):
    return f'\t(via\n\t\t(at {x} {y})\n\t\t(size {s})\n\t\t(drill {d})\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "{net}")\n\t\t(uuid "{uuid.uuid4()}")\n\t)'
def find_remove(c, p):
    i=c.find(p)
    if i<0: return c,False
    e=c.find('\n\t)',i)+3
    return c[:i]+c[e:],True

INSERT = '\n\t(via'

# ======================================================
# 1. SCL横/縦の修正
# ======================================================
# 削除: (9.75,26.5)→(15.5,26.5) 横と (15.5,26.5)→(15.5,25.2) 縦
for p in [
    '\t(segment\n\t\t(start 9.75 26.5)\n\t\t(end 15.5 26.5)',
    '\t(segment\n\t\t(start 15.5 26.5)\n\t\t(end 15.5 25.2)',
]:
    content,ok=find_remove(content,p)
    if ok: changes.append(f'SCL旧削除')

# 追加: (9.75,26.5)→(15.0,26.5)横 + (15.0,26.5)→(15.0,25.2)縦 + (15.0,25.2)→(15.5,25.2)横
new_scl_conn = [
    make_seg(9.75,26.5,15.0,26.5,0.2,'F.Cu','I2C_SCL'),
    make_seg(15.0,26.5,15.0,25.2,0.2,'F.Cu','I2C_SCL'),
    make_seg(15.0,25.2,15.5,25.2,0.2,'F.Cu','I2C_SCL'),
]
content = content.replace(INSERT,'\n'+'\n'.join(new_scl_conn)+INSERT,1)
changes.append('SCL新: (15.0,26.5)→縦→(15.0,25.2)→(15.5,25.2)')

# ======================================================
# 2. LED_ANODE: F.Cu→B.Cu経由
# 削除: F.Cu配線全て
for p in [
    '\t(segment\n\t\t(start 15.49 26.3)\n\t\t(end 16.0 26.3)',
    '\t(segment\n\t\t(start 16.0 26.3)\n\t\t(end 16.0 28.0)',
    '\t(segment\n\t\t(start 16.0 28.0)\n\t\t(end 16.485 28.0)',
    '\t(segment\n\t\t(start 16.485 28.0)\n\t\t(end 16.485 27.5)',
]:
    content,ok=find_remove(content,p)
    if ok: changes.append('LED_ANODE F.Cu削除')

# 追加: via(15.49,26.3)→B.Cu→via(16.485,27.5)
# B.Cu横y=26.3 x=[15.49,16.485]: SIM系B.Cu縦は全て範囲外 ✓
# B.Cu縦x=16.485 y=[26.3,27.5]: 同上 ✓
new_led_b = [
    make_via(15.49, 26.3, 'LED_ANODE'),
    make_seg(15.49,26.3,16.485,26.3,0.2,'B.Cu','LED_ANODE'),
    make_seg(16.485,26.3,16.485,27.5,0.2,'B.Cu','LED_ANODE'),
    make_via(16.485, 27.5, 'LED_ANODE'),
]
content = content.replace(INSERT,'\n'+'\n'.join(new_led_b)+INSERT,1)
changes.append('LED_ANODE: B.Cu経由に変更')

# ======================================================
# 3. SCL B.Cu via位置修正: (13.0,24.6)→(13.5,24.6)
# ======================================================
# 削除: 旧via(13.0,24.6), B.Cu横, F.Cu接続
content,ok=find_remove(content,'\t(via\n\t\t(at 13.0 24.6)')
if ok: changes.append('SCL旧via(13.0,24.6)削除')
for p in [
    '\t(segment\n\t\t(start 15.0 24.6)\n\t\t(end 13.0 24.6)\n\t\t(width 0.2)\n\t\t(layer "B.Cu")',
    '\t(segment\n\t\t(start 13.0 24.6)\n\t\t(end 13.0 24.75)',
    '\t(segment\n\t\t(start 13.0 24.75)\n\t\t(end 12.738 24.75)',
]:
    content,ok=find_remove(content,p)
    if ok: changes.append('SCL旧B.Cu接続削除')

# 追加: via(15.0,24.6)→B.Cu横→via(13.5,24.6)→F.Cu→pad3
new_scl_tap = [
    make_via(13.5, 24.6, 'I2C_SCL'),
    make_seg(13.5,24.6,15.0,24.6,0.2,'B.Cu','I2C_SCL'),  # B.Cu横(SIM_DATA x=12.6から+0.9mm)
    make_seg(13.5,24.6,13.5,24.75,0.2,'F.Cu','I2C_SCL'),
    make_seg(13.5,24.75,12.738,24.75,0.2,'F.Cu','I2C_SCL'),  # pad3左側(pad8 x_min=14.09の外)
]
content = content.replace(INSERT,'\n'+'\n'.join(new_scl_tap)+INSERT,1)
changes.append('SCL B.Cuタップ: via(13.5,24.6)に更新')

with open(PCB,'w') as f: f.write(content)
print(f'修正完了({len(changes)}件):')
for c in changes: print(f'  ✓ {c}')
