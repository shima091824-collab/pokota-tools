#!/usr/bin/env python3
"""
Add TP2 (VCC) and TP3 (GND) test points for UPDI programming access.

Test point row at y=18.5:
  TP3(GND) x=13.5 --- TP1(UPDI) x=16.0 --- TP2(VCC) x=18.5

TP2 (VCC): via(18.6, 17.0) taps B.Cu VCC trace endpoint → F.Cu to TP2 pad
TP3 (GND): via(13.5, 17.0) to B.Cu GND zone → F.Cu to TP3 pad
"""

import re
import uuid

PCB_FILE = "/Users/m2mac/gps-cat-tracker/lora-30x35-v3n.kicad_pcb"


def gen_uuid():
    return str(uuid.uuid4())


TP2_FOOTPRINT = f"""
\t(footprint "TestPoint"
\t\t(layer "F.Cu")
\t\t(uuid "{gen_uuid()}")
\t\t(at 18.5 18.5)
\t\t(property "Reference" "TP2"
\t\t\t(at 0 -1.5 0)
\t\t\t(layer "F.SilkS")
\t\t\t(hide yes)
\t\t\t(uuid "{gen_uuid()}")
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.0 1.0)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Value" "VCC"
\t\t\t(at 0 1.5 0)
\t\t\t(layer "F.SilkS")
\t\t\t(hide yes)
\t\t\t(uuid "{gen_uuid()}")
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.0 1.0)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(pad "1" smd circle
\t\t\t(at 0 0)
\t\t\t(size 1.5 1.5)
\t\t\t(layers "F.Cu" "F.Mask")
\t\t\t(thermal_bridge_angle 45)
\t\t\t(uuid "{gen_uuid()}")
\t\t)
\t\t(embedded_fonts no)
\t)
"""

TP3_FOOTPRINT = f"""
\t(footprint "TestPoint"
\t\t(layer "F.Cu")
\t\t(uuid "{gen_uuid()}")
\t\t(at 13.5 18.5)
\t\t(property "Reference" "TP3"
\t\t\t(at 0 -1.5 0)
\t\t\t(layer "F.SilkS")
\t\t\t(hide yes)
\t\t\t(uuid "{gen_uuid()}")
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.0 1.0)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Value" "GND"
\t\t\t(at 0 1.5 0)
\t\t\t(layer "F.SilkS")
\t\t\t(hide yes)
\t\t\t(uuid "{gen_uuid()}")
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.0 1.0)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(pad "1" smd circle
\t\t\t(at 0 0)
\t\t\t(size 1.5 1.5)
\t\t\t(layers "F.Cu" "F.Mask")
\t\t\t(thermal_bridge_angle 45)
\t\t\t(uuid "{gen_uuid()}")
\t\t)
\t\t(embedded_fonts no)
\t)
"""

# Via at (18.6, 17.0): tap B.Cu VCC trace endpoint → F.Cu
TP2_VIA = f"""
\t(via
\t\t(at 18.6 17.0)
\t\t(size 0.8)
\t\t(drill 0.4)
\t\t(layers "F.Cu" "B.Cu")
\t\t(net "")
\t\t(uuid "{gen_uuid()}")
\t)
"""

# Via at (13.5, 17.0): F.Cu → B.Cu GND zone
TP3_VIA = f"""
\t(via
\t\t(at 13.5 17.0)
\t\t(size 0.8)
\t\t(drill 0.4)
\t\t(layers "F.Cu" "B.Cu")
\t\t(net "")
\t\t(uuid "{gen_uuid()}")
\t)
"""

# F.Cu traces for VCC: via(18.6,17.0) → (18.5,17.0) → TP2(18.5,18.5)
TP2_TRACE_H = f"""
\t(segment
\t\t(start 18.6 17.0)
\t\t(end 18.5 17.0)
\t\t(width 0.2)
\t\t(layer "F.Cu")
\t\t(net "")
\t\t(uuid "{gen_uuid()}")
\t)
"""

TP2_TRACE_V = f"""
\t(segment
\t\t(start 18.5 17.0)
\t\t(end 18.5 18.5)
\t\t(width 0.2)
\t\t(layer "F.Cu")
\t\t(net "")
\t\t(uuid "{gen_uuid()}")
\t)
"""

# F.Cu trace for GND: via(13.5,17.0) → TP3(13.5,18.5)
TP3_TRACE_V = f"""
\t(segment
\t\t(start 13.5 17.0)
\t\t(end 13.5 18.5)
\t\t(width 0.2)
\t\t(layer "F.Cu")
\t\t(net "")
\t\t(uuid "{gen_uuid()}")
\t)
"""

INSERT_BEFORE = "\n)"  # Insert before the final closing paren of the file

additions = (
    TP2_FOOTPRINT
    + TP3_FOOTPRINT
    + TP2_VIA
    + TP3_VIA
    + TP2_TRACE_H
    + TP2_TRACE_V
    + TP3_TRACE_V
)

with open(PCB_FILE, "r") as f:
    content = f.read()

if "TP2" in content:
    print("ERROR: TP2 already exists in PCB file. Aborting.")
    exit(1)

# Insert before the last closing ')' of the file
idx = content.rfind("\n)")
if idx == -1:
    print("ERROR: Could not find insertion point.")
    exit(1)

new_content = content[:idx] + additions + content[idx:]

with open(PCB_FILE, "w") as f:
    f.write(new_content)

print("Added:")
print("  TP2 (VCC) pad at (18.5, 18.5) on F.Cu")
print("  TP3 (GND) pad at (13.5, 18.5) on F.Cu")
print("  via at (18.6, 17.0) tapping B.Cu VCC trace")
print("  via at (13.5, 17.0) to B.Cu GND zone")
print("  F.Cu traces: TP2 route from (18.6,17.0)→(18.5,17.0)→(18.5,18.5)")
print("  F.Cu traces: TP3 route from (13.5,17.0)→(13.5,18.5)")
print()
print("Test point row at y=18.5:")
print("  TP3(GND) x=13.5 --- TP1(UPDI) x=16.0 --- TP2(VCC) x=18.5")
print("  Spacing: 2.5mm center-to-center, 1.0mm gap between 1.5mm pads")
