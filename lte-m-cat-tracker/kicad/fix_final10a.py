#!/usr/bin/env python3
"""
fix_final10a.py: SCL B.Cu via位置を(13.5→12.5,24.6)に変更
pad3(12.738,24.75)へF.Cu迂回経路でpad8/9を完全回避
"""
import uuid, shutil

PCB = 'kicad/lte-m-cat-tracker.kicad_pcb'
shutil.copy(PCB, PCB + '.bak_ff10a')
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

# 削除: via(13.5,24.6) + B.Cu横(13.5,24.6→15.0) + F.Cu(13.5→12.738,24.75)
content,ok=find_remove(content,'\t(via\n\t\t(at 13.5 24.6)')
if ok: changes.append('SCL via(13.5,24.6)削除')
for p in [
    '\t(segment\n\t\t(start 13.5 24.6)\n\t\t(end 15.0 24.6)\n\t\t(width 0.2)\n\t\t(layer "B.Cu")',
    '\t(segment\n\t\t(start 13.5 24.6)\n\t\t(end 13.5 24.75)',
    '\t(segment\n\t\t(start 13.5 24.75)\n\t\t(end 12.738 24.75)',
]:
    content,ok=find_remove(content,p)
    if ok: changes.append('SCL旧タップ削除')

# 追加: via(12.5,24.6) + B.Cu横(12.5→15.0,24.6) + F.Cu縦下→横→縦でpad3へ
new_tap = [
    make_via(12.5, 24.6, 'I2C_SCL'),
    make_seg(12.5,24.6,15.0,24.6,0.2,'B.Cu','I2C_SCL'),  # B.Cu横
    make_seg(12.5,24.6,12.5,24.9,0.2,'F.Cu','I2C_SCL'),  # F.Cu縦上
    make_seg(12.5,24.9,12.738,24.9,0.2,'F.Cu','I2C_SCL'),# F.Cu横(pad5 x>12.738なので安全)
    make_seg(12.738,24.9,12.738,24.75,0.2,'F.Cu','I2C_SCL'),# F.Cu縦→pad3
]
content = content.replace(INSERT,'\n'+'\n'.join(new_tap)+INSERT,1)
changes.append('SCL新タップ: via(12.5,24.6)→B.Cu横→F.Cuでpad3接続')

with open(PCB,'w') as f: f.write(content)
print(f'修正完了({len(changes)}件):')
for c in changes: print(f'  ✓ {c}')
