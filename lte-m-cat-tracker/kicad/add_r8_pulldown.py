#!/usr/bin/env python3
"""
R8(10kΩ 0402) GPIO2プルダウン追加
配置: (11.5, 21.5)
  pad1(11.02,21.5)[SIM_TXD] → U2.pad27(9.25,21.05)へ配線
  pad2(11.98,21.5)[GND] → GNDゾーンへスタブ（充填時に接続）
"""

import uuid

PCB_PATH = "kicad/lte-m-cat-tracker.kicad_pcb"

with open(PCB_PATH) as f:
    content = f.read()

R8_X, R8_Y = 11.5, 21.5
PAD1_X = R8_X - 0.48   # 11.02 [SIM_TXD]
PAD2_X = R8_X + 0.48   # 11.98 [GND]

FP_UID   = str(uuid.uuid4())
REF_UID  = str(uuid.uuid4())
VAL_UID  = str(uuid.uuid4())
FAB_UID  = str(uuid.uuid4())
PAD1_UID = str(uuid.uuid4())
PAD2_UID = str(uuid.uuid4())
SEG1_UID = str(uuid.uuid4())
SEG2_UID = str(uuid.uuid4())

r8_block = f"""
\t(footprint "0402"
\t\t(layer "F.Cu")
\t\t(uuid "{FP_UID}")
\t\t(at {R8_X} {R8_Y})
\t\t(property "Reference" "R8"
\t\t\t(at 0 -1 0)
\t\t\t(layer "F.SilkS")
\t\t\t(uuid "{REF_UID}")
\t\t\t(effects (font (size 0.8 0.8) (thickness 0.12)))
\t\t)
\t\t(property "Value" "10k"
\t\t\t(at 0 1 0)
\t\t\t(layer "F.Fab")
\t\t\t(uuid "{VAL_UID}")
\t\t\t(effects (font (size 0.8 0.8) (thickness 0.12)))
\t\t)
\t\t(fp_rect
\t\t\t(start -0.5 -0.35) (end 0.5 0.35)
\t\t\t(layer "F.Fab") (width 0.1)
\t\t\t(uuid "{FAB_UID}")
\t\t)
\t\t(pad "1" smd rect
\t\t\t(at -0.48 0)
\t\t\t(size 0.56 0.62)
\t\t\t(layers "F.Cu" "F.Mask" "F.Paste")
\t\t\t(net "SIM_TXD")
\t\t\t(thermal_bridge_angle 45)
\t\t\t(uuid "{PAD1_UID}")
\t\t)
\t\t(pad "2" smd rect
\t\t\t(at 0.48 0)
\t\t\t(size 0.56 0.62)
\t\t\t(layers "F.Cu" "F.Mask" "F.Paste")
\t\t\t(net "GND")
\t\t\t(thermal_bridge_angle 45)
\t\t\t(uuid "{PAD2_UID}")
\t\t)
\t)
\t(segment
\t\t(start {PAD1_X:.2f} {R8_Y})
\t\t(end {PAD1_X:.2f} 21.05)
\t\t(width 0.2)
\t\t(layer "F.Cu")
\t\t(net "SIM_TXD")
\t\t(uuid "{SEG1_UID}")
\t)
\t(segment
\t\t(start {PAD1_X:.2f} 21.05)
\t\t(end 9.25 21.05)
\t\t(width 0.2)
\t\t(layer "F.Cu")
\t\t(net "SIM_TXD")
\t\t(uuid "{SEG2_UID}")
\t)"""

content = content.rstrip()
if content.endswith(')'):
    content = content[:-1] + r8_block + "\n)"
else:
    content += r8_block

with open(PCB_PATH, 'w') as f:
    f.write(content)

print(f"R8(10kΩ) 追加: center({R8_X},{R8_Y})")
print(f"  pad1({PAD1_X:.2f},{R8_Y})[SIM_TXD] → U2.pad27(9.25,21.05)")
print(f"  pad2({PAD2_X:.2f},{R8_Y})[GND] → GNDゾーン(充填時接続)")
