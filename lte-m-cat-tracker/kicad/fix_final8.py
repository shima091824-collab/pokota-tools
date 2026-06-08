#!/usr/bin/env python3
"""
fix_final8.py
1. LED_ANODE経路完全変更: SCL横y=26.5の範囲外(x>15.5)を通る
   (15.49,26.3)→(16.0,26.3)→(16.0,28.0)→(16.485,28.0)→(16.485,27.5)
2. C15: center(25,20.5)→(25,19.9) でU4.pad8[+3.3V]回避
"""
import re, uuid, shutil

PCB = 'kicad/lte-m-cat-tracker.kicad_pcb'
shutil.copy(PCB, PCB + '.bak_fix_final8')
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

# 1. LED_ANODE全配線削除・再追加
for p in [
    '\t(segment\n\t\t(start 15.49 26.3)\n\t\t(end 14.5 26.3)',
    '\t(segment\n\t\t(start 14.5 26.3)\n\t\t(end 14.5 25.8)',
    '\t(segment\n\t\t(start 14.5 25.8)\n\t\t(end 17.5 25.8)',
    '\t(segment\n\t\t(start 17.5 25.8)\n\t\t(end 17.5 27.5)',
    '\t(segment\n\t\t(start 17.5 27.5)\n\t\t(end 16.485 27.5)',
]:
    content,ok=find_remove(content,p)
    if ok: changes.append('LED_ANODE旧削除')

# 新経路: x=16.0縦(SCL横x=[9.75,15.5]の外)でy=26.5を回避
new_led = [
    make_seg(15.49,26.3,16.0,26.3,0.2,'F.Cu','LED_ANODE'),  # 短横(CHRG左端16.51の左)
    make_seg(16.0,26.3,16.0,28.0,0.2,'F.Cu','LED_ANODE'),   # 縦下(SCL横y=26.5をx=16.0で回避)
    make_seg(16.0,28.0,16.485,28.0,0.2,'F.Cu','LED_ANODE'), # 横右
    make_seg(16.485,28.0,16.485,27.5,0.2,'F.Cu','LED_ANODE'), # 縦上
]
content = content.replace(INSERT,'\n'+'\n'.join(new_led)+INSERT,1)
changes.append('LED_ANODE新: x=16.0→y=28→LED1.pad2')

# 2. C15 center移動 + 配線更新
for p in [
    '\t(segment\n\t\t(start 26.363 21.05)\n\t\t(end 25.5 21.05)',
    '\t(segment\n\t\t(start 25.5 21.05)\n\t\t(end 25.5 20.5)',
    '\t(segment\n\t\t(start 25.5 20.5)\n\t\t(end 24.52 20.5)',
]:
    content,ok=find_remove(content,p)
    if ok: changes.append('C15旧削除')
content = content.replace('(at 25 20.5)\n','(at 25 19.9)\n')
changes.append('C15 (25,20.5)→(25,19.9)')
new_c15=[
    make_seg(26.363,21.05,25.5,21.05,0.2,'F.Cu','VBAT_SW'),
    make_seg(25.5,21.05,25.5,19.9,0.2,'F.Cu','VBAT_SW'),
    make_seg(25.5,19.9,24.52,19.9,0.2,'F.Cu','VBAT_SW'),
]
content = content.replace(INSERT,'\n'+'\n'.join(new_c15)+INSERT,1)
changes.append('C15新配線: y=19.9')

with open(PCB,'w') as f: f.write(content)
print(f'修正完了({len(changes)}件):')
for c in changes: print(f'  ✓ {c}')
