#!/usr/bin/env python3
"""
fix_final7.py
1. PROG B.Cu横: y=24.5→y=24.0 (VUSB B.Cu縦x=19.025を回避)
2. C15: center(25,20.9)→(25,20.5) (U4.pad8+3.3V回避)
3. SCL迂回: (9.75,26.5)→(15.5,26.5)→(15.5,25.2) で接続
4. LED_ANODE縦: x=15.49→x=14.5 (SCL縦x=15.5との干渉回避)
"""
import re, uuid, shutil

PCB = 'kicad/lte-m-cat-tracker.kicad_pcb'
shutil.copy(PCB, PCB + '.bak_fix_final7')
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

# 1. PROG B.Cu横 y=24.5→y=24.0
for p in [
    '\t(segment\n\t\t(start 15.99 24.5)\n\t\t(end 20.5 24.5)\n\t\t(width 0.2)\n\t\t(layer "B.Cu")',
]:
    content,ok = find_remove(content,p)
    if ok: changes.append('PROG B.Cu横 y=24.5削除')
# via(15.99,24.5)もF.Cu-B.Cu viaが存在する
# PROG via(15.99,24.5): F.Cu→B.Cuのvia。B.Cu横をy=24.0に変更なので via位置も調整
# via(15.99,24.5)を削除してvia(15.99,24.0)に変更
content,ok = find_remove(content, '\t(via\n\t\t(at 15.99 24.5)')
if ok: changes.append('PROG via(15.99,24.5)削除')
# via(20.5,24.5)も削除してy=24.0に
content,ok = find_remove(content, '\t(via\n\t\t(at 20.5 24.5)')
if ok: changes.append('PROG via(20.5,24.5)削除')

new_prog = [
    make_via(15.99, 24.0, 'PROG'),
    make_seg(15.99, 24.0, 20.5, 24.0, 0.2, 'B.Cu', 'PROG'),
    make_via(20.5, 24.0, 'PROG'),
    # F.Cu縦(20.5,24.0→21.865)はすでにfix_final5で(20.5,24.5→21.865)があるが、y=24.5→24.0に変更
]
# F.Cu縦(20.5,24.5)→(20.5,21.865)を削除して(20.5,24.0→21.865)に変更
content,ok=find_remove(content,'\t(segment\n\t\t(start 20.5 24.5)\n\t\t(end 20.5 21.865)')
if ok: changes.append('PROG F.Cu縦削除')
new_prog.append(make_seg(20.5,24.0,20.5,21.865,0.2,'F.Cu','PROG'))

# R3.pad1(15.99,24.5) → via(15.99,24.0) の縦接続を追加
new_prog.append(make_seg(15.99,24.5,15.99,24.0,0.2,'F.Cu','PROG'))
content = content.replace(INSERT, '\n'+'\n'.join(new_prog)+INSERT, 1)
changes.append('PROG: via y=24.0に変更')

# 2. C15 center→(25,20.5)
# 旧配線削除
for p in [
    '\t(segment\n\t\t(start 26.363 21.05)\n\t\t(end 25.5 21.05)',
    '\t(segment\n\t\t(start 25.5 21.05)\n\t\t(end 25.5 20.9)',
    '\t(segment\n\t\t(start 25.5 20.9)\n\t\t(end 24.52 20.9)',
]:
    content,ok=find_remove(content,p)
    if ok: changes.append('C15旧削除')
content = content.replace('(at 25 20.9)\n','(at 25 20.5)\n')
changes.append('C15 (25,20.9)→(25,20.5)')
new_c15=[
    make_seg(26.363,21.05,25.5,21.05,0.2,'F.Cu','VBAT_SW'),
    make_seg(25.5,21.05,25.5,20.5,0.2,'F.Cu','VBAT_SW'),
    make_seg(25.5,20.5,24.52,20.5,0.2,'F.Cu','VBAT_SW'),
]
content = content.replace(INSERT,'\n'+'\n'.join(new_c15)+INSERT,1)
changes.append('C15新配線: y=20.5')

# 3. SCL接続修正: (15.5,26.5)→(15.5,25.2) 経由
# 既存の(9.75,26.5)→(15.0,26.5)を(9.75,26.5)→(15.5,26.5)に延長
# → 既存横を削除して新横を追加
content,ok=find_remove(content,'\t(segment\n\t\t(start 9.75 26.5)\n\t\t(end 15 26.5)')
if ok: changes.append('SCL旧横(9.75,26.5→15,26.5)削除')
# 追加した迂回も削除
for p in [
    '\t(segment\n\t\t(start 15 26.5)\n\t\t(end 15.5 26.5)',
    '\t(segment\n\t\t(start 15.5 26.5)\n\t\t(end 15.5 25.2)',
]:
    content,ok=find_remove(content,p)
    if ok: changes.append('SCL旧迂回削除')

new_scl=[
    make_seg(9.75,26.5,15.5,26.5,0.2,'F.Cu','I2C_SCL'),
    make_seg(15.5,26.5,15.5,25.2,0.2,'F.Cu','I2C_SCL'),
]
content = content.replace(INSERT,'\n'+'\n'.join(new_scl)+INSERT,1)
changes.append('SCL: (9.75,26.5)→(15.5,26.5)→(15.5,25.2)')

# 4. LED_ANODE: 縦x=15.49→x=14.5
# 削除: (15.49,26.3)→(15.49,25.8)縦
content,ok=find_remove(content,'\t(segment\n\t\t(start 15.49 26.3)\n\t\t(end 15.49 25.8)')
if ok: changes.append('LED_ANODE縦削除')
# 追加: (15.49,26.3)→(14.5,26.3)横 + (14.5,26.3)→(14.5,25.8)縦 + (14.5,25.8)→(17.5,25.8)は既存のまま
new_led=[
    make_seg(15.49,26.3,14.5,26.3,0.2,'F.Cu','LED_ANODE'),
    make_seg(14.5,26.3,14.5,25.8,0.2,'F.Cu','LED_ANODE'),
]
content = content.replace(INSERT,'\n'+'\n'.join(new_led)+INSERT,1)
changes.append('LED_ANODE: x=14.5経由でSCL縦回避')

with open(PCB,'w') as f: f.write(content)
print(f'修正完了({len(changes)}件):')
for c in changes: print(f'  ✓ {c}')
