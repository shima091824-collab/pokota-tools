#!/usr/bin/env python3
"""fix_crossings_v3.py: Fix all 5 tracks_crossing violations without touching I2C cluster issue."""
import re, uuid

PCB_IN  = "kicad/lte-m-cat-tracker.kicad_pcb"
PCB_OUT = "kicad/lte-m-cat-tracker.kicad_pcb"

def new_uuid():
    return str(uuid.uuid4())

def seg(x1,y1,x2,y2,w,layer,net):
    return f'\t(segment (start {x1} {y1}) (end {x2} {y2}) (width {w}) (layer "{layer}") (net "{net}") (uuid "{new_uuid()}"))\n'

def via_entry(x,y,size,drill,net):
    return f'\t(via (at {x} {y}) (size {size}) (drill {drill}) (layers "F.Cu" "B.Cu") (net "{net}") (uuid "{new_uuid()}"))\n'

with open(PCB_IN) as f:
    data = f.read()

orig = data

# ============================================================
# Fix 1: SIM_RESETN × +3.3V縦 (F.Cu x=3.5, y=24.5)
# +3.3V F.Cu縦がx=3.5, y=21.5-26.5を占有。SIM_RESETNのF.Cu横y=24.5が交差。
# 修正: SIM_RESETNの横走を全てB.Cuに変更 + via(2.7,24.25)を削除 + via(6.05,24.25)を追加
# ============================================================

# Remove via at (2.7,24.25) SIM_RESETN
data = re.sub(
    r'\t\(via \(at 2\.7 24\.25\) \(size 0\.4\) \(drill 0\.2\) \(layers "F\.Cu" "B\.Cu"\) \(net "SIM_RESETN"\) \(uuid "[^"]+"\)\)\n',
    '', data
)

# Change F.Cu (2.7,24.25)→(2.7,24.5) to B.Cu
data = data.replace(
    '(segment (start 2.7 24.25) (end 2.7 24.5) (width 0.2) (layer "F.Cu") (net "SIM_RESETN")',
    f'(segment (start 2.7 24.25) (end 2.7 24.5) (width 0.2) (layer "B.Cu") (net "SIM_RESETN")',
)
# Change F.Cu (2.7,24.5)→(6.05,24.5) to B.Cu
data = data.replace(
    '(segment (start 2.7 24.5) (end 6.05 24.5) (width 0.2) (layer "F.Cu") (net "SIM_RESETN")',
    f'(segment (start 2.7 24.5) (end 6.05 24.5) (width 0.2) (layer "B.Cu") (net "SIM_RESETN")',
)
# Change F.Cu (6.05,24.5)→(6.05,24.25) to B.Cu
data = data.replace(
    '(segment (start 6.05 24.5) (end 6.05 24.25) (width 0.2) (layer "F.Cu") (net "SIM_RESETN")',
    f'(segment (start 6.05 24.5) (end 6.05 24.25) (width 0.2) (layer "B.Cu") (net "SIM_RESETN")',
)
# Add via at (6.05,24.25) to connect B.Cu trace to U2.pad6 (F.Cu)
data += via_entry(6.05, 24.25, 0.4, 0.2, "SIM_RESETN")

# ============================================================
# Fix 2: I2C_SCL × I2C_SDA (F.Cu y=26.5共有、x=15.0縦重複)
# SDAをy=27.2横 + x=16.0縦 経由に迂回
# ============================================================

# Remove old SDA segments
for old in [
    '(segment (start 9.25 25.95) (end 9.25 26.5) (width 0.2) (layer "F.Cu") (net "I2C_SDA")',
    '(segment (start 9.25 26.5) (end 15.0 26.5) (width 0.2) (layer "F.Cu") (net "I2C_SDA")',
    '(segment (start 15.0 26.5) (end 15.0 23.4) (width 0.2) (layer "F.Cu") (net "I2C_SDA")',
    '(segment (start 15.0 23.4) (end 13.75 23.4) (width 0.2) (layer "F.Cu") (net "I2C_SDA")',
]:
    # Find and remove the whole line
    data = re.sub(re.escape(old) + r' \(uuid "[^"]+"\)\)\n', '', data)

# Add new SDA segments: U2.pad14(9.25,25.95) → y=27.2 → x=16.0 → y=23.4 → U3.pad11 region
data += seg(9.25, 25.95, 9.25, 27.2,  0.2, "F.Cu", "I2C_SDA")
data += seg(9.25, 27.2,  16.0, 27.2,  0.2, "F.Cu", "I2C_SDA")
data += seg(16.0, 27.2,  16.0, 23.4,  0.2, "F.Cu", "I2C_SDA")
data += seg(16.0, 23.4,  13.75, 23.4, 0.2, "F.Cu", "I2C_SDA")

# ============================================================
# Fix 3: VBAT × VBAT_SW (F.Cu x=2.88, y=28.5)
# VBAT縦F.Cu (2.88,32.65)→(2.88,26.95) がVBAT_SW横F.Cu y=28.5を交差。
# 修正: VBAT縦をB.Cu経由に変更（J1.pad1付近にvia, SW1.pad1付近にvia）
# ============================================================

# Remove F.Cu (2.88,32.65)→(2.88,26.95)
data = re.sub(
    r'\t\(segment \(start 2\.88 32\.65\) \(end 2\.88 26\.95\) \(width 0\.5\) \(layer "F\.Cu"\) \(net "VBAT"\) \(uuid "[^"]+"\)\)\n',
    '', data
)
# Add via at (2.88,32.65) VBAT — top (near J1.pad1)
data += via_entry(2.88, 32.65, 0.6, 0.3, "VBAT")
# B.Cu bridge
data += seg(2.88, 32.65, 2.88, 26.95, 0.5, "B.Cu", "VBAT")
# Add via at (2.88,26.95) VBAT — bottom (near SW1.pad1)
data += via_entry(2.88, 26.95, 0.6, 0.3, "VBAT")

# ============================================================
# Fix 4: VBAT × CHRG (F.Cu x=25.0, y=26.3)
# CHRG縦x=25.5がVBAT縦x=25.0より右にあり、横走y=26.3でVBATを交差。
# 修正: CHRG縦をx=24.3に移動（VBATのx=25.0より左）
# ============================================================

# Remove old CHRG segments
for old in [
    '(segment (start 23.975 21.865) (end 25.5 21.865) (width 0.2) (layer "F.Cu") (net "CHRG")',
    '(segment (start 25.5 21.865) (end 25.5 26.3) (width 0.2) (layer "F.Cu") (net "CHRG")',
    '(segment (start 25.5 26.3) (end 16.51 26.3) (width 0.2) (layer "F.Cu") (net "CHRG")',
]:
    data = re.sub(re.escape(old) + r' \(uuid "[^"]+"\)\)\n', '', data)

# Add new CHRG route via x=24.3 (left of VBAT x=25.0)
data += seg(23.975, 21.865, 24.3, 21.865, 0.2, "F.Cu", "CHRG")
data += seg(24.3, 21.865, 24.3, 26.3, 0.2, "F.Cu", "CHRG")
data += seg(24.3, 26.3, 16.51, 26.3, 0.2, "F.Cu", "CHRG")

# ============================================================
# Fix 5: SIM_RXD縦 × SIM_TXD横 (B.Cu x=8.75, y=13.0)
# SIM_RXD縦x=8.75がSIM_TXD横y=13.0と交差。
# 修正: SIM_RXD縦がy=12.0-14.0の間でx=9.75に迂回するS字を追加
# ============================================================

# Remove old long SIM_RXD vertical
data = re.sub(
    r'\t\(segment \(start 8\.75 6\.4\) \(end 8\.75 20\.0\) \(width 0\.2\) \(layer "B\.Cu"\) \(net "SIM_RXD"\) \(uuid "[^"]+"\)\)\n',
    '', data
)
# Add S-bend detour around y=13.0
data += seg(8.75, 6.4,   8.75, 12.0,  0.2, "B.Cu", "SIM_RXD")  # down to y=12.0
data += seg(8.75, 12.0,  9.75, 12.0,  0.2, "B.Cu", "SIM_RXD")  # right to x=9.75
data += seg(9.75, 12.0,  9.75, 14.0,  0.2, "B.Cu", "SIM_RXD")  # down past y=13.0
data += seg(9.75, 14.0,  8.75, 14.0,  0.2, "B.Cu", "SIM_RXD")  # back left
data += seg(8.75, 14.0,  8.75, 20.0,  0.2, "B.Cu", "SIM_RXD")  # continue down

if data == orig:
    print("WARNING: No changes made - check segment strings")
else:
    with open(PCB_OUT, 'w') as f:
        f.write(data)
    print("Done. Changes applied to", PCB_OUT)
    print("  Fix1: SIM_RESETN → B.Cu (avoid +3.3V縦 at x=3.5)")
    print("  Fix2: I2C_SDA → y=27.2 + x=16.0 迂回 (avoid SCL x=15.0共有)")
    print("  Fix3: VBAT → B.Cu bridge (avoid VBAT_SW横 y=28.5)")
    print("  Fix4: CHRG縦 x=25.5→x=24.3 (avoid VBAT縦 x=25.0)")
    print("  Fix5: SIM_RXD S字迂回 x=9.75 (avoid SIM_TXD横 y=13.0)")
