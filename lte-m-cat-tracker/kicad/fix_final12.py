#!/usr/bin/env python3
"""
fix_final12.py: SCL縦タップのx座標修正
x=12.738→x=12.2に変更してU3.pad4[+3.3V]を回避
"""
import uuid, shutil

PCB = 'kicad/lte-m-cat-tracker.kicad_pcb'
shutil.copy(PCB, PCB + '.bak_ff12')
with open(PCB) as f: content = f.read()
changes = []

def make_seg(x1,y1,x2,y2,w,layer,net):
    return f'\t(segment\n\t\t(start {x1} {y1})\n\t\t(end {x2} {y2})\n\t\t(width {w})\n\t\t(layer "{layer}")\n\t\t(net "{net}")\n\t\t(uuid "{uuid.uuid4()}")\n\t)'
def find_remove(c, p):
    i=c.find(p)
    if i<0: return c,False
    e=c.find('\n\t)',i)+3
    return c[:i]+c[e:],True

INSERT = '\n\t(via'

# 旧タップ削除
content,ok=find_remove(content,'\t(segment\n\t\t(start 12.738 26.5)\n\t\t(end 12.738 24.75)')
if ok: changes.append('SCL旧縦タップ削除')

# 新タップ: x=12.2経由（pad4 x_min=12.563より左）
new_tap = [
    make_seg(12.2,26.5,12.2,24.75,0.2,'F.Cu','I2C_SCL'),
    make_seg(12.2,24.75,12.738,24.75,0.2,'F.Cu','I2C_SCL'),
]
content = content.replace(INSERT,'\n'+'\n'.join(new_tap)+INSERT,1)
changes.append('SCL新タップ: x=12.2縦→横→pad3(12.738,24.75)')

with open(PCB,'w') as f: f.write(content)
print(f'修正完了({len(changes)}件):')
for c in changes: print(f'  ✓ {c}')
