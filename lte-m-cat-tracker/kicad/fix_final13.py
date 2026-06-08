#!/usr/bin/env python3
"""fix_final13: SCL縦x=12.2→x=12.4 (via+3.3V(11.8,25.5)との0mm gapを解消)"""
import uuid, shutil

PCB = 'kicad/lte-m-cat-tracker.kicad_pcb'
shutil.copy(PCB, PCB + '.bak_ff13')
with open(PCB) as f: content = f.read()

def make_seg(x1,y1,x2,y2,w,layer,net):
    return f'\t(segment\n\t\t(start {x1} {y1})\n\t\t(end {x2} {y2})\n\t\t(width {w})\n\t\t(layer "{layer}")\n\t\t(net "{net}")\n\t\t(uuid "{uuid.uuid4()}")\n\t)'
def find_remove(c,p):
    i=c.find(p)
    if i<0: return c,False
    return c[:i]+c[c.find('\n\t)',i)+3:],True

INSERT='\n\t(via'
for p in ['\t(segment\n\t\t(start 12.2 26.5)\n\t\t(end 12.2 24.75)',
          '\t(segment\n\t\t(start 12.2 24.75)\n\t\t(end 12.738 24.75)']:
    content,_=find_remove(content,p)

new=[make_seg(12.4,26.5,12.4,24.75,0.2,'F.Cu','I2C_SCL'),
     make_seg(12.4,24.75,12.738,24.75,0.2,'F.Cu','I2C_SCL')]
content=content.replace(INSERT,'\n'+'\n'.join(new)+INSERT,1)

with open(PCB,'w') as f: f.write(content)
print('✓ SCL縦タップ x=12.2→12.4')
