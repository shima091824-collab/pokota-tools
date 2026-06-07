#!/usr/bin/env python3
"""
I2C_SDA の変更を元に戻すスクリプト（y=26.8移動でACCEL_INT1と新たな交差が発生したため）
crossing2 (I2C_SCL × I2C_SDA) はKiCad GUIでの手動修正が必要
"""

import re
import uuid

PCB_FILE = '/Users/m2mac/lte-m-cat-tracker/kicad/lte-m-cat-tracker.kicad_pcb'

def U():
    return str(uuid.uuid4())

def seg(x1, y1, x2, y2, w, layer, net):
    return f'\t(segment (start {x1} {y1}) (end {x2} {y2}) (width {w}) (layer "{layer}") (net "{net}") (uuid "{U()}"))'

with open(PCB_FILE, 'r') as f:
    content = f.read()

def replace_seg(content, x1, y1, x2, y2, net, new_segs):
    for sx1, sy1, sx2, sy2 in [(x1, y1, x2, y2), (x2, y2, x1, y1)]:
        pattern = (
            r'\t\(segment \(start ' + re.escape(str(sx1)) + r' ' + re.escape(str(sy1)) +
            r'\) \(end ' + re.escape(str(sx2)) + r' ' + re.escape(str(sy2)) +
            r'\) \(width [0-9.]+\) \(layer "[^"]+"\) \(net "' + re.escape(net) + r'"\) \(uuid "[^"]+"\)\)'
        )
        m = re.search(pattern, content)
        if m:
            replacement = '\n'.join(new_segs)
            content = content[:m.start()] + replacement + content[m.end():]
            return content, True
    return content, False

# Revert I2C_SDA changes (y=26.8 → y=26.5, x=15.2 → x=15.0)
content, ok1 = replace_seg(content, 9.25, 25.95, 9.25, 26.8, 'I2C_SDA',
    [seg(9.25, 25.95, 9.25, 26.5, 0.2, 'F.Cu', 'I2C_SDA')])
content, ok2 = replace_seg(content, 9.25, 26.8, 15.2, 26.8, 'I2C_SDA',
    [seg(9.25, 26.5, 15.0, 26.5, 0.2, 'F.Cu', 'I2C_SDA')])
content, ok3 = replace_seg(content, 15.2, 26.8, 15.2, 23.4, 'I2C_SDA',
    [seg(15.0, 26.5, 15.0, 23.4, 0.2, 'F.Cu', 'I2C_SDA')])
content, ok4 = replace_seg(content, 15.2, 23.4, 13.75, 23.4, 'I2C_SDA',
    [seg(15.0, 23.4, 13.75, 23.4, 0.2, 'F.Cu', 'I2C_SDA')])

print(f"I2C_SDA revert: ok1={ok1}, ok2={ok2}, ok3={ok3}, ok4={ok4}")

with open(PCB_FILE, 'w') as f:
    f.write(content)

print("I2C_SDA変更を元に戻しました（crossing2はGUI手動修正が必要）")
