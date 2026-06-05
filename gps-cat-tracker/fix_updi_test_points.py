#!/usr/bin/env python3
"""
Fix TP2/TP3 test point placement:
- Remove duplicate via at (18.6, 17.0) - already existed
- Remove TP3 at (13.5, 18.5) - conflicts with C4.pad1
- Remove TP3 via at (13.5, 17.0) - too close to existing via at (12.9, 17.0)
- Remove TP3 trace (13.5, 17.0) -> (13.5, 18.5)
- Add TP3 at (20.5, 18.5) with via at (20.5, 17.0) and F.Cu trace
"""

import uuid

PCB_FILE = "/Users/m2mac/gps-cat-tracker/lora-30x35-v3n.kicad_pcb"


def gen_uuid():
    return str(uuid.uuid4())


with open(PCB_FILE, "r") as f:
    content = f.read()

# ---- Remove duplicate via at (18.6, 17.0) ----
# The UUID of the one I added: b3e3694f-9a99-4a6d-b556-431f74c74d2f
DUPE_VIA = """\n\t(via
\t\t(at 18.6 17.0)
\t\t(size 0.8)
\t\t(drill 0.4)
\t\t(layers "F.Cu" "B.Cu")
\t\t(net "")
\t\t(uuid "b3e3694f-9a99-4a6d-b556-431f74c74d2f")
\t)\n"""

# ---- Remove TP3 footprint at (13.5, 18.5) ----
TP3_OLD_FP = """\n\t(footprint "TestPoint"
\t\t(layer "F.Cu")
\t\t(uuid "c5e68118-53f3-4494-8513-704f8d6a5bbe")
\t\t(at 13.5 18.5)
\t\t(property "Reference" "TP3"
\t\t\t(at 0 -1.5 0)
\t\t\t(layer "F.SilkS")
\t\t\t(hide yes)
\t\t\t(uuid "8b82b4ff-eb71-423a-8707-d3c4e1164040")
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
\t\t\t(uuid "0db45564-67af-403a-96da-216d9a66d9f9")
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
\t\t\t(uuid "08e9fe9b-aad2-4ea9-b353-372045a47497")
\t\t)
\t\t(embedded_fonts no)
\t)\n"""

# ---- Remove TP3 via at (13.5, 17.0) ----
TP3_OLD_VIA = """\n\t(via
\t\t(at 13.5 17.0)
\t\t(size 0.8)
\t\t(drill 0.4)
\t\t(layers "F.Cu" "B.Cu")
\t\t(net "")
\t\t(uuid "119f254f-c5e2-47b4-9706-767d6f7e05c4")
\t)\n"""

# ---- Remove TP3 old trace (13.5,17.0) -> (13.5,18.5) ----
TP3_OLD_TRACE = """\n\t(segment
\t\t(start 13.5 17.0)
\t\t(end 13.5 18.5)
\t\t(width 0.2)
\t\t(layer "F.Cu")
\t\t(net "")
\t\t(uuid "1bffbe98-5de8-498b-a374-976c3b7ad444")
\t)\n"""

# ---- New TP3 footprint at (20.5, 18.5) ----
TP3_NEW_FP_UUID = gen_uuid()
TP3_NEW_REF_UUID = gen_uuid()
TP3_NEW_VAL_UUID = gen_uuid()
TP3_NEW_PAD_UUID = gen_uuid()

TP3_NEW_FP = f"""
\t(footprint "TestPoint"
\t\t(layer "F.Cu")
\t\t(uuid "{TP3_NEW_FP_UUID}")
\t\t(at 20.5 18.5)
\t\t(property "Reference" "TP3"
\t\t\t(at 0 -1.5 0)
\t\t\t(layer "F.SilkS")
\t\t\t(hide yes)
\t\t\t(uuid "{TP3_NEW_REF_UUID}")
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
\t\t\t(uuid "{TP3_NEW_VAL_UUID}")
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
\t\t\t(uuid "{TP3_NEW_PAD_UUID}")
\t\t)
\t\t(embedded_fonts no)
\t)
"""

# Via at (20.5, 17.0) → B.Cu GND zone  (y=17.0 is above RF band at y=17.95)
TP3_NEW_VIA_UUID = gen_uuid()
TP3_NEW_VIA = f"""
\t(via
\t\t(at 20.5 17.0)
\t\t(size 0.8)
\t\t(drill 0.4)
\t\t(layers "F.Cu" "B.Cu")
\t\t(net "")
\t\t(uuid "{TP3_NEW_VIA_UUID}")
\t)
"""

# F.Cu trace: via(20.5,17.0) → TP3(20.5,18.5)
TP3_NEW_TRACE_UUID = gen_uuid()
TP3_NEW_TRACE = f"""
\t(segment
\t\t(start 20.5 17.0)
\t\t(end 20.5 18.5)
\t\t(width 0.2)
\t\t(layer "F.Cu")
\t\t(net "")
\t\t(uuid "{TP3_NEW_TRACE_UUID}")
\t)
"""

# Apply removals
for label, old_str in [
    ("duplicate via at (18.6,17.0)", DUPE_VIA),
    ("TP3 footprint at (13.5,18.5)", TP3_OLD_FP),
    ("TP3 via at (13.5,17.0)", TP3_OLD_VIA),
    ("TP3 trace (13.5,17.0)->(13.5,18.5)", TP3_OLD_TRACE),
]:
    if old_str in content:
        content = content.replace(old_str, "\n")
        print(f"Removed: {label}")
    else:
        print(f"WARNING: Could not find '{label}' to remove")

# Insert new TP3 content before final ')'
additions = TP3_NEW_FP + TP3_NEW_VIA + TP3_NEW_TRACE
idx = content.rfind("\n)")
if idx == -1:
    print("ERROR: Could not find insertion point")
    exit(1)
content = content[:idx] + additions + content[idx:]

with open(PCB_FILE, "w") as f:
    f.write(content)

print()
print("Added:")
print("  TP3 (GND) pad at (20.5, 18.5) on F.Cu")
print("  via at (20.5, 17.0) to B.Cu GND zone")
print("  F.Cu trace (20.5,17.0)→(20.5,18.5)")
print()
print("Final test point layout:")
print("  TP1(UPDI) x=16.0 --- TP2(VCC) x=18.5 --- TP3(GND) x=20.5  @ y=18.5")
print("  Spacing: 2.5mm center-to-center, 1.0mm gap between 1.5mm pads")
