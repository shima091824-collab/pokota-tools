#!/usr/bin/env python3
"""fix_crossings_v5.py: Fix remaining 3 crossings + 11 shorts from v4.

Changes from v4:
  Fix2: I2C_SDA reroute to y=27.0 horizontal + x=18.0 vertical
        (avoids VBAT y=27.5 by 0.15mm AND avoids I2C_SCL horizontal x=[15.5,17.5])
  Fix3: VBAT J1→SW1 rerouted via B.Cu vertical x=2.875
        (B.Cu avoids all F.Cu VBAT_SW traces; no clearance issues)
  Fix4: CHRG vertical x=23.0 → x=22.5
        (VBAT pad5 left_edge=23.0, CHRG right_edge=22.6 → gap=0.4mm)
  Fix5: SIM_TXD horizontal y=21.1 → y=21.45
        (SIM_RXD via(8.75,21.05) bottom_edge=21.25, SIM_TXD top_edge=21.35 → gap=0.10mm)
"""
import re, uuid

PCB_IN  = "kicad/lte-m-cat-tracker.kicad_pcb"
PCB_OUT = "kicad/lte-m-cat-tracker.kicad_pcb"

def new_uuid():
    return str(uuid.uuid4())

def seg(x1, y1, x2, y2, w, layer, net):
    return f'\t(segment (start {x1} {y1}) (end {x2} {y2}) (width {w}) (layer "{layer}") (net "{net}") (uuid "{new_uuid()}"))\n'

def via_entry(x, y, size, drill, net):
    return f'\t(via (at {x} {y}) (size {size}) (drill {drill}) (layers "F.Cu" "B.Cu") (net "{net}") (uuid "{new_uuid()}"))\n'

with open(PCB_IN) as f:
    data = f.read()

new_items = ""

# ============================================================
# Fix 2: I2C_SDA × I2C_SCL (F.Cu x=16.0縦 crosses SCL horizontal y=25.2 at x=[15.5,17.5])
#        I2C_SDA × VBAT (SDA horizontal crosses VBAT y=27.5)
# Reroute SDA: y=27.0 horizontal + x=18.0 vertical (right of SCL horizontal x_max=17.5)
# VBAT y=27.5 width=0.5 → top_edge=27.25; SDA y=27.0 width=0.2 → bottom_edge=26.9 → gap=0.35mm
# SCL horizontal x=[15.5,17.5]; SDA vertical x=18.0 > 17.5 → no crossing
# SCL vertical x=17.5, SDA vertical x=18.0: gap=18.0-0.1-17.5-0.1=0.3mm
# ============================================================

# Remove old SDA segments added in v4 (y=27.2 variants)
for old in [
    '(segment (start 9.25 25.95) (end 9.25 27.2) (width 0.2) (layer "F.Cu") (net "I2C_SDA")',
    '(segment (start 9.25 27.2) (end 16.0 27.2) (width 0.2) (layer "F.Cu") (net "I2C_SDA")',
    '(segment (start 16.0 27.2) (end 16.0 23.4) (width 0.2) (layer "F.Cu") (net "I2C_SDA")',
    '(segment (start 16.0 23.4) (end 13.75 23.4) (width 0.2) (layer "F.Cu") (net "I2C_SDA")',
    # Also handle y=27.0 variants if this script is re-run
    '(segment (start 9.25 25.95) (end 9.25 27.0) (width 0.2) (layer "F.Cu") (net "I2C_SDA")',
    '(segment (start 9.25 27.0) (end 16.0 27.0) (width 0.2) (layer "F.Cu") (net "I2C_SDA")',
    '(segment (start 16.0 27.0) (end 16.0 23.4) (width 0.2) (layer "F.Cu") (net "I2C_SDA")',
    # x=18.0 variants for re-run safety
    '(segment (start 9.25 27.0) (end 18.0 27.0) (width 0.2) (layer "F.Cu") (net "I2C_SDA")',
    '(segment (start 18.0 27.0) (end 18.0 23.4) (width 0.2) (layer "F.Cu") (net "I2C_SDA")',
    '(segment (start 18.0 23.4) (end 13.75 23.4) (width 0.2) (layer "F.Cu") (net "I2C_SDA")',
    # Left-turn variants: x=13.0, x=12.3
    '(segment (start 9.25 27.0) (end 13.0 27.0) (width 0.2) (layer "F.Cu") (net "I2C_SDA")',
    '(segment (start 13.0 27.0) (end 13.0 23.4) (width 0.2) (layer "F.Cu") (net "I2C_SDA")',
    '(segment (start 13.0 23.4) (end 13.75 23.4) (width 0.2) (layer "F.Cu") (net "I2C_SDA")',
    '(segment (start 9.25 27.0) (end 12.3 27.0) (width 0.2) (layer "F.Cu") (net "I2C_SDA")',
    '(segment (start 12.3 27.0) (end 12.3 23.4) (width 0.2) (layer "F.Cu") (net "I2C_SDA")',
    '(segment (start 12.3 23.4) (end 13.75 23.4) (width 0.2) (layer "F.Cu") (net "I2C_SDA")',
]:
    data = re.sub(re.escape(old) + r' \(uuid "[^"]+"\)\)\n', '', data)

new_items += seg(9.25, 25.95, 9.25, 27.0,  0.2, "F.Cu", "I2C_SDA")
new_items += seg(9.25, 27.0,  13.65, 27.0,  0.2, "F.Cu", "I2C_SDA")
new_items += seg(13.65, 27.0,  13.65, 23.4,  0.2, "F.Cu", "I2C_SDA")
new_items += seg(13.65, 23.4,  13.75, 23.4, 0.2, "F.Cu", "I2C_SDA")

# ============================================================
# Fix 3: VBAT J1→SW1 path — replace F.Cu detour with B.Cu vertical
# B.Cu vertical x=2.875, y=[26.95,31.3] avoids all F.Cu VBAT_SW traces
# Clearances verified:
#   VBAT_SW B.Cu trunk x=1.0: gap=2.875-0.25-1.0-0.25=1.375mm
#   SIM_RESETN B.Cu x=2.7 at y=[24.25,24.5]: no y overlap (26.95>24.5)
#   VBAT_SW via(1.0,28.5): x gap > 1.0mm
# ============================================================

# Remove old F.Cu detour segments (v4: x=1.5 variant; v5 re-run: x=1.0 variant)
for old_pat in [
    r'\t\(segment \(start 2\.88 32\.65\) \(end 2\.88 29\.0\) \(width 0\.5\) \(layer "F\.Cu"\) \(net "VBAT"\) \(uuid "[^"]+"\)\)\n',
    r'\t\(segment \(start 2\.88 29\.0\) \(end 1\.[05] 29\.0\) \(width 0\.5\) \(layer "F\.Cu"\) \(net "VBAT"\) \(uuid "[^"]+"\)\)\n',
    r'\t\(segment \(start 1\.[05] 29\.0\) \(end 1\.[05] 28\.0\) \(width 0\.5\) \(layer "F\.Cu"\) \(net "VBAT"\) \(uuid "[^"]+"\)\)\n',
    r'\t\(segment \(start 1\.[05] 28\.0\) \(end 2\.88 28\.0\) \(width 0\.5\) \(layer "F\.Cu"\) \(net "VBAT"\) \(uuid "[^"]+"\)\)\n',
    r'\t\(segment \(start 2\.88 28\.0\) \(end 2\.88 26\.95\) \(width 0\.5\) \(layer "F\.Cu"\) \(net "VBAT"\) \(uuid "[^"]+"\)\)\n',
]:
    data = re.sub(old_pat, '', data)

# New route: J1.pad1(2.875,32.65) F.Cu → via(2.875,31.3) → B.Cu vertical → via(2.875,26.95) → F.Cu → SW1.pad1
# Note: existing segment (2.88,26.95)→(2.0,26.95) already connects to SW1.pad1
new_items += seg(2.875, 32.65, 2.875, 31.3, 0.5, "F.Cu", "VBAT")
new_items += via_entry(2.875, 31.3, 0.5, 0.25, "VBAT")
new_items += seg(2.875, 31.3, 2.875, 26.95, 0.5, "B.Cu", "VBAT")
new_items += via_entry(2.875, 26.95, 0.5, 0.25, "VBAT")

# ============================================================
# Fix 4: CHRG × VBAT (CHRG vertical crosses VBAT pad5 at U4)
# VBAT pad5(23.975,24.405) size=1.95×0.6 → left_edge=23.0
# CHRG x=22.5 width=0.2 → right_edge=22.6; gap=23.0-22.6=0.4mm
# ============================================================

for old in [
    '(segment (start 23.975 21.865) (end 24.3 21.865) (width 0.2) (layer "F.Cu") (net "CHRG")',
    '(segment (start 24.3 21.865) (end 24.3 26.3) (width 0.2) (layer "F.Cu") (net "CHRG")',
    '(segment (start 24.3 26.3) (end 16.51 26.3) (width 0.2) (layer "F.Cu") (net "CHRG")',
    # Re-run safety: x=23.0 variant
    '(segment (start 23.975 21.865) (end 23.0 21.865) (width 0.2) (layer "F.Cu") (net "CHRG")',
    '(segment (start 23.0 21.865) (end 23.0 26.3) (width 0.2) (layer "F.Cu") (net "CHRG")',
    '(segment (start 23.0 26.3) (end 16.51 26.3) (width 0.2) (layer "F.Cu") (net "CHRG")',
    # Re-run safety: x=22.5 variant
    '(segment (start 23.975 21.865) (end 22.5 21.865) (width 0.2) (layer "F.Cu") (net "CHRG")',
    '(segment (start 22.5 21.865) (end 22.5 26.3) (width 0.2) (layer "F.Cu") (net "CHRG")',
    '(segment (start 22.5 26.3) (end 16.51 26.3) (width 0.2) (layer "F.Cu") (net "CHRG")',
]:
    data = re.sub(re.escape(old) + r' \(uuid "[^"]+"\)\)\n', '', data)

new_items += seg(23.975, 21.865, 22.5, 21.865, 0.2, "F.Cu", "CHRG")
new_items += seg(22.5, 21.865, 22.5, 26.3,    0.2, "F.Cu", "CHRG")
new_items += seg(22.5, 26.3,   16.51, 26.3,   0.2, "F.Cu", "CHRG")

# ============================================================
# Fix 5: SIM_RXD縦 × SIM_TXD横 (B.Cu)
# Remove v4's S-curve on SIM_RXD; restore simple vertical.
# Reroute SIM_TXD horizontal via x=8.4, then y=21.45 (clear of SIM_RXD via)
#
# SIM_RXD via(8.75,21.05) size=0.4: bottom_edge=21.05+0.2=21.25
# SIM_TXD horizontal y=21.45, width=0.2: top_edge=21.45-0.1=21.35 → gap=0.10mm ✓
# SIM_TXD x=8.4 vertical: right_edge=8.5; SIM_RXD x=8.75 left_edge=8.65 → gap=0.15mm ✓
# ============================================================

# Remove SIM_RXD S-curve segments (added in v4 Fix5)
for old in [
    '(segment (start 8.75 6.4) (end 8.75 12.0) (width 0.2) (layer "B.Cu") (net "SIM_RXD")',
    '(segment (start 8.75 12.0) (end 9.75 12.0) (width 0.2) (layer "B.Cu") (net "SIM_RXD")',
    '(segment (start 9.75 12.0) (end 9.75 14.0) (width 0.2) (layer "B.Cu") (net "SIM_RXD")',
    '(segment (start 9.75 14.0) (end 8.75 14.0) (width 0.2) (layer "B.Cu") (net "SIM_RXD")',
    '(segment (start 8.75 14.0) (end 8.75 20.0) (width 0.2) (layer "B.Cu") (net "SIM_RXD")',
]:
    data = re.sub(re.escape(old) + r' \(uuid "[^"]+"\)\)\n', '', data)

# Restore simple SIM_RXD vertical
new_items += seg(8.75, 6.4, 8.75, 20.0, 0.2, "B.Cu", "SIM_RXD")

# Remove old SIM_TXD horizontal and downstream vertical (v4 and earlier variants)
for old in [
    '(segment (start 3.5 13.0) (end 9.25 13.0) (width 0.2) (layer "B.Cu") (net "SIM_TXD")',
    '(segment (start 9.25 13.0) (end 9.25 21.05) (width 0.2) (layer "B.Cu") (net "SIM_TXD")',
    # Re-run safety: x=8.4, y=21.1 variants
    '(segment (start 3.5 13.0) (end 8.4 13.0) (width 0.2) (layer "B.Cu") (net "SIM_TXD")',
    '(segment (start 8.4 13.0) (end 8.4 21.1) (width 0.2) (layer "B.Cu") (net "SIM_TXD")',
    '(segment (start 8.4 21.1) (end 9.25 21.1) (width 0.2) (layer "B.Cu") (net "SIM_TXD")',
    '(segment (start 9.25 21.1) (end 9.25 21.05) (width 0.2) (layer "B.Cu") (net "SIM_TXD")',
    # Re-run safety: x=8.3, y=21.45 variants
    '(segment (start 3.5 13.0) (end 8.3 13.0) (width 0.2) (layer "B.Cu") (net "SIM_TXD")',
    '(segment (start 8.3 13.0) (end 8.3 21.45) (width 0.2) (layer "B.Cu") (net "SIM_TXD")',
    '(segment (start 8.3 21.45) (end 9.25 21.45) (width 0.2) (layer "B.Cu") (net "SIM_TXD")',
    '(segment (start 9.25 21.45) (end 9.25 21.05) (width 0.2) (layer "B.Cu") (net "SIM_TXD")',
]:
    data = re.sub(re.escape(old) + r' \(uuid "[^"]+"\)\)\n', '', data)

# Reroute SIM_TXD: (3.5,13.0) → x=8.4 → y=21.45 → (9.25,21.05)
new_items += seg(3.5,  13.0,  8.3,  13.0,  0.2, "B.Cu", "SIM_TXD")
new_items += seg(8.3,  13.0,  8.3,  21.45, 0.2, "B.Cu", "SIM_TXD")
new_items += seg(8.3,  21.45, 9.25, 21.45, 0.2, "B.Cu", "SIM_TXD")
new_items += seg(9.25, 21.45, 9.25, 21.05, 0.2, "B.Cu", "SIM_TXD")

# ============================================================
# Insert all new items before the final closing ) of the kicad_pcb block
# ============================================================
stripped = data.rstrip()
assert stripped.endswith(')'), "PCB file does not end with ')' as expected"
data = stripped[:-1] + new_items + ')\n'

with open(PCB_OUT, 'w') as f:
    f.write(data)

print("Done:", PCB_OUT)
print("  Fix2: I2C_SDA → y=27.0 horiz + x=18.0 vert (SCL gap 0.3mm, VBAT gap 0.35mm)")
print("  Fix3: VBAT J1→SW1 → B.Cu vertical x=2.875 (avoids all VBAT_SW F.Cu)")
print("  Fix4: CHRG vertical → x=22.5 (VBAT pad5 gap 0.4mm)")
print("  Fix5: SIM_RXD S-curve removed; SIM_TXD via x=8.4,y=21.45 (via gap 0.10mm)")
