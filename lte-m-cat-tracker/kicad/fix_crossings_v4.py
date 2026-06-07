#!/usr/bin/env python3
"""fix_crossings_v4.py: Fix all 6 tracks_crossing violations.
Key fix vs v3: new segments/vias are inserted BEFORE the closing ) of the kicad_pcb block.
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

new_items = ""   # All new segments/vias go here, inserted before closing ) later

# ============================================================
# Fix 1: SIM_RESETN × +3.3V縦 (F.Cu x=3.5, y=24.5)
# +3.3V F.Cu縦がx=3.5, y=21.5-26.5。SIM_RESETN F.Cu横y=24.5が交差。
# 修正: SIM_RESETN横をB.Cuに変更。via(2.7,24.25)削除→via(6.05,24.25)追加。
# ============================================================

# Remove old via at (2.7,24.25)
data = re.sub(
    r'\t\(via \(at 2\.7 24\.25\) \(size 0\.4\) \(drill 0\.2\) \(layers "F\.Cu" "B\.Cu"\) \(net "SIM_RESETN"\) \(uuid "[^"]+"\)\)\n',
    '', data
)
# Change F.Cu segments to B.Cu
data = data.replace(
    '(segment (start 2.7 24.25) (end 2.7 24.5) (width 0.2) (layer "F.Cu") (net "SIM_RESETN")',
    '(segment (start 2.7 24.25) (end 2.7 24.5) (width 0.2) (layer "B.Cu") (net "SIM_RESETN")',
)
data = data.replace(
    '(segment (start 2.7 24.5) (end 6.05 24.5) (width 0.2) (layer "F.Cu") (net "SIM_RESETN")',
    '(segment (start 2.7 24.5) (end 6.05 24.5) (width 0.2) (layer "B.Cu") (net "SIM_RESETN")',
)
data = data.replace(
    '(segment (start 6.05 24.5) (end 6.05 24.25) (width 0.2) (layer "F.Cu") (net "SIM_RESETN")',
    '(segment (start 6.05 24.5) (end 6.05 24.25) (width 0.2) (layer "B.Cu") (net "SIM_RESETN")',
)
# Add via at (6.05,24.25) to connect B.Cu → U2.pad6 F.Cu
new_items += via_entry(6.05, 24.25, 0.4, 0.2, "SIM_RESETN")

# ============================================================
# Fix 2: I2C_SCL × I2C_SDA (F.Cu y=26.5共有/x=15.0縦重複)
# SDAをy=27.2横 + x=16.0縦経由に迂回
# ============================================================

for old in [
    '(segment (start 9.25 25.95) (end 9.25 26.5) (width 0.2) (layer "F.Cu") (net "I2C_SDA")',
    '(segment (start 9.25 26.5) (end 15.0 26.5) (width 0.2) (layer "F.Cu") (net "I2C_SDA")',
    '(segment (start 15.0 26.5) (end 15.0 23.4) (width 0.2) (layer "F.Cu") (net "I2C_SDA")',
    '(segment (start 15.0 23.4) (end 13.75 23.4) (width 0.2) (layer "F.Cu") (net "I2C_SDA")',
]:
    data = re.sub(re.escape(old) + r' \(uuid "[^"]+"\)\)\n', '', data)

new_items += seg(9.25, 25.95, 9.25, 27.2,  0.2, "F.Cu", "I2C_SDA")
new_items += seg(9.25, 27.2,  16.0, 27.2,  0.2, "F.Cu", "I2C_SDA")
new_items += seg(16.0, 27.2,  16.0, 23.4,  0.2, "F.Cu", "I2C_SDA")
new_items += seg(16.0, 23.4,  13.75, 23.4, 0.2, "F.Cu", "I2C_SDA")

# ============================================================
# Fix 3: VBAT × VBAT_SW (F.Cu x=2.88, y=28.5)
# VBAT縦F.Cu x=2.88がVBAT_SW横y=28.5を交差。
# 修正: x=1.5を経由するF.Cu迂回（B.Cu化はC13 F.Cuタップを切断するため不可）
# ============================================================

# Remove long F.Cu vertical
data = re.sub(
    r'\t\(segment \(start 2\.88 32\.65\) \(end 2\.88 26\.95\) \(width 0\.5\) \(layer "F\.Cu"\) \(net "VBAT"\) \(uuid "[^"]+"\)\)\n',
    '', data
)
# Add F.Cu detour via x=1.5 (below y=29.0, VBAT_SW doesn't reach x=1.5)
new_items += seg(2.88, 32.65, 2.88, 29.0, 0.5, "F.Cu", "VBAT")
new_items += seg(2.88, 29.0,  1.5,  29.0, 0.5, "F.Cu", "VBAT")
new_items += seg(1.5,  29.0,  1.5,  28.0, 0.5, "F.Cu", "VBAT")
new_items += seg(1.5,  28.0,  2.88, 28.0, 0.5, "F.Cu", "VBAT")
new_items += seg(2.88, 28.0,  2.88, 26.95, 0.5, "F.Cu", "VBAT")

# ============================================================
# Fix 4: VBAT × CHRG (F.Cu x=25.0, y=26.3)
# CHRG縦x=25.5→x=24.3に移動（VBATのx=25.0より左側）
# ============================================================

for old in [
    '(segment (start 23.975 21.865) (end 25.5 21.865) (width 0.2) (layer "F.Cu") (net "CHRG")',
    '(segment (start 25.5 21.865) (end 25.5 26.3) (width 0.2) (layer "F.Cu") (net "CHRG")',
    '(segment (start 25.5 26.3) (end 16.51 26.3) (width 0.2) (layer "F.Cu") (net "CHRG")',
]:
    data = re.sub(re.escape(old) + r' \(uuid "[^"]+"\)\)\n', '', data)

new_items += seg(23.975, 21.865, 24.3, 21.865, 0.2, "F.Cu", "CHRG")
new_items += seg(24.3, 21.865, 24.3, 26.3, 0.2, "F.Cu", "CHRG")
new_items += seg(24.3, 26.3, 16.51, 26.3, 0.2, "F.Cu", "CHRG")

# ============================================================
# Fix 5: SIM_RXD縦 × SIM_TXD横 (B.Cu x=8.75, y=13.0)
# SIM_RXD縦x=8.75がy=12.0-14.0でx=9.75に迂回するS字を追加
# ============================================================

data = re.sub(
    r'\t\(segment \(start 8\.75 6\.4\) \(end 8\.75 20\.0\) \(width 0\.2\) \(layer "B\.Cu"\) \(net "SIM_RXD"\) \(uuid "[^"]+"\)\)\n',
    '', data
)
new_items += seg(8.75, 6.4,  8.75, 12.0, 0.2, "B.Cu", "SIM_RXD")
new_items += seg(8.75, 12.0, 9.75, 12.0, 0.2, "B.Cu", "SIM_RXD")
new_items += seg(9.75, 12.0, 9.75, 14.0, 0.2, "B.Cu", "SIM_RXD")
new_items += seg(9.75, 14.0, 8.75, 14.0, 0.2, "B.Cu", "SIM_RXD")
new_items += seg(8.75, 14.0, 8.75, 20.0, 0.2, "B.Cu", "SIM_RXD")

# ============================================================
# Fix 6: ACCEL_INT1 × I2C_SCL (F.Cu x=10.25, y=26.5)
# ACCEL_INT1 F.Cu縦がSCL横y=26.5を交差。
# 修正: via(10.25,27.0)削除→B.Cu縦→via(10.25,25.95)でU2.pad16接続
# ============================================================

data = re.sub(
    r'\t\(via \(at 10\.25 27\.0\) \(size 0\.4\) \(drill 0\.2\) \(layers "F\.Cu" "B\.Cu"\) \(net "ACCEL_INT1"\) \(uuid "[^"]+"\)\)\n',
    '', data
)
data = data.replace(
    '(segment (start 10.25 27.0) (end 10.25 25.95) (width 0.2) (layer "F.Cu") (net "ACCEL_INT1")',
    '(segment (start 10.25 27.0) (end 10.25 25.95) (width 0.2) (layer "B.Cu") (net "ACCEL_INT1")',
)
new_items += via_entry(10.25, 25.95, 0.4, 0.2, "ACCEL_INT1")

# ============================================================
# Insert all new items BEFORE the final closing ) of the kicad_pcb block
# ============================================================
stripped = data.rstrip()
assert stripped.endswith(')'), "PCB file does not end with ')' as expected"
data = stripped[:-1] + new_items + ')\n'

with open(PCB_OUT, 'w') as f:
    f.write(data)

print("Done:", PCB_OUT)
print("  Fix1: SIM_RESETN → B.Cu (avoid +3.3V縦 x=3.5)")
print("  Fix2: I2C_SDA → y=27.2 + x=16.0 迂回")
print("  Fix3: VBAT → F.Cu x=1.5迂回 (avoid VBAT_SW横 y=28.5)")
print("  Fix4: CHRG縦 x=25.5→x=24.3 (avoid VBAT縦 x=25.0)")
print("  Fix5: SIM_RXD S字迂回 x=9.75 (avoid SIM_TXD横 y=13.0)")
print("  Fix6: ACCEL_INT1 → B.Cu縦 (avoid I2C_SCL横 y=26.5)")
