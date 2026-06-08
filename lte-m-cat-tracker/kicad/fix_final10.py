#!/usr/bin/env python3
"""
fix_final10.py: 残留セグメントを削除 + 不足viaを追加
"""
import re, uuid, shutil

PCB = 'kicad/lte-m-cat-tracker.kicad_pcb'
shutil.copy(PCB, PCB + '.bak_ff10')
with open(PCB) as f: content = f.read()
changes = []

def make_via(x,y,net,s=0.6,d=0.3):
    return f'\t(via\n\t\t(at {x} {y})\n\t\t(size {s})\n\t\t(drill {d})\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "{net}")\n\t\t(uuid "{uuid.uuid4()}")\n\t)'
def find_remove(c, p):
    i=c.find(p)
    if i<0: return c,False
    e=c.find('\n\t)',i)+3
    return c[:i]+c[e:],True

INSERT = '\n\t(via'

# 余分なSCLセグメント削除
for p in [
    '\t(segment\n\t\t(start 15.0 26.5)\n\t\t(end 15.0 24.6)',
    '\t(segment\n\t\t(start 15.0 26.5)\n\t\t(end 15.5 26.5)',
]:
    content,ok=find_remove(content,p)
    if ok: changes.append(f'SCL余分削除')

# 余分なLED_ANODE F.Cuセグメント削除
for p in [
    '\t(segment\n\t\t(start 15.49 25.8)\n\t\t(end 16.485 25.8)',
    '\t(segment\n\t\t(start 16.485 25.8)\n\t\t(end 17.5 25.8)',
]:
    content,ok=find_remove(content,p)
    if ok: changes.append('LED_ANODE余分F.Cu削除')

# LED_ANODE via(15.49,26.3)を追加
content = content.replace(INSERT, '\n'+make_via(15.49,26.3,'LED_ANODE')+INSERT, 1)
changes.append('LED_ANODE via(15.49,26.3)追加')

with open(PCB,'w') as f: f.write(content)
print(f'修正完了({len(changes)}件):')
for c in changes: print(f'  ✓ {c}')
