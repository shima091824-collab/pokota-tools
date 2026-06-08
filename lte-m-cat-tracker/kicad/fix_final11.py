#!/usr/bin/env python3
"""
fix_final11.py: SCL B.Cu複雑経路を削除→シンプルF.Cu縦タップに変更
SCL横y=26.5からF.Cu縦でpad3(12.738,24.75)に直接タップ
"""
import uuid, shutil

PCB = 'kicad/lte-m-cat-tracker.kicad_pcb'
shutil.copy(PCB, PCB + '.bak_ff11')
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

# B.Cu経路を全削除
for p in [
    '\t(via\n\t\t(at 12.5 24.6)',
    '\t(via\n\t\t(at 15.0 24.6)',
    '\t(segment\n\t\t(start 12.5 24.6)\n\t\t(end 15.0 24.6)\n\t\t(width 0.2)\n\t\t(layer "B.Cu")',
    '\t(segment\n\t\t(start 12.5 24.6)\n\t\t(end 12.5 24.9)',
    '\t(segment\n\t\t(start 12.5 24.9)\n\t\t(end 12.738 24.9)',
    '\t(segment\n\t\t(start 12.738 24.9)\n\t\t(end 12.738 24.75)',
    '\t(segment\n\t\t(start 15.0 26.5)\n\t\t(end 15.0 24.6)',
]:
    content,ok=find_remove(content,p)
    if ok: changes.append(f'SCL B.Cu経路削除')

# 代替: SCL横y=26.5からF.Cu縦でpad3直接タップ
# (12.738,26.5)→(12.738,24.75) [F.Cu縦]
new_tap = make_seg(12.738,26.5,12.738,24.75,0.2,'F.Cu','I2C_SCL')
content = content.replace(INSERT,'\n'+new_tap+INSERT,1)
changes.append('SCL F.Cu縦タップ: (12.738,26.5)→pad3(12.738,24.75)')

with open(PCB,'w') as f: f.write(content)
print(f'修正完了({len(changes)}件):')
for c in changes: print(f'  ✓ {c}')
