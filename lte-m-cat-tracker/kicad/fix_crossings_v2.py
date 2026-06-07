#!/usr/bin/env python3
"""
tracks_crossing 4件修正（crossing2はGUI手動のため除外）

修正対象:
1. +3.3V × SIM_RESETN (F.Cu) → SIM_RESETNにB.Cuブリッジ挿入
3. VBAT × VBAT_SW (F.Cu) → VBAT_SW F.Cu直線をB.Cu経由に変更
4. SIM_RXD × SIM_TXD (B.Cu) → SIM_TXDにF.Cuブリッジ挿入
5. VBAT × CHRG (F.Cu) → CHRGにB.Cuブリッジ挿入

スキップ:
2. I2C_SCL × I2C_SDA (F.Cu) → SCL/SDA が x=15.0 と y=26.5 を共有する
   構造的問題。KiCad GUIで手動修正が必要。
"""

import re
import uuid

PCB_FILE = '/Users/m2mac/lte-m-cat-tracker/kicad/lte-m-cat-tracker.kicad_pcb'

def U():
    return str(uuid.uuid4())

def seg(x1, y1, x2, y2, w, layer, net):
    return f'\t(segment (start {x1} {y1}) (end {x2} {y2}) (width {w}) (layer "{layer}") (net "{net}") (uuid "{U()}"))'

def via(x, y, net, size=0.6, drill=0.3):
    return f'\t(via (at {x} {y}) (size {size}) (drill {drill}) (layers "F.Cu" "B.Cu") (net "{net}") (uuid "{U()}"))'

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

changes = 0

# =============================================================================
# 交差1: +3.3V × SIM_RESETN (F.Cu, x=3.5, y=24.5)
# +3.3V F.Cu縦線 x=3.5 (y=23.5-25.5) × SIM_RESETN F.Cu横線 y=24.5 (x=2.7-6.05)
#
# 修正: SIM_RESETNの横線をB.Cuブリッジで+3.3V縦線を跨ぐ
# F.Cu (2.7,24.5)→(3.0,24.5): +3.3V x_left=3.5-0.15=3.35 から gap=3.0+0.1=3.1→gap=0.25mm ✅
# B.Cu (3.0,24.5)→(4.0,24.5): +3.3V は F.Cuのみ → B.Cuは干渉なし ✅
# F.Cu (4.0,24.5)→(6.05,24.5): +3.3V x_right=3.5+0.15=3.65 から gap=4.0-0.1=3.9→gap=0.25mm ✅
# Via (3.0,24.5): SIM_PWRKEY B.Cu x=2.2 x_right=2.3 → gap=3.0-0.2-2.3=0.5mm ✅
# Via (4.0,24.5): SIM_STATUS via (5.35,24.0) 別位置 ✅
# =============================================================================
new_segs_1 = [
    seg(2.7, 24.5, 3.0, 24.5, 0.2, 'F.Cu', 'SIM_RESETN'),
    via(3.0, 24.5, 'SIM_RESETN', 0.4, 0.2),
    seg(3.0, 24.5, 4.0, 24.5, 0.2, 'B.Cu', 'SIM_RESETN'),
    via(4.0, 24.5, 'SIM_RESETN', 0.4, 0.2),
    seg(4.0, 24.5, 6.05, 24.5, 0.2, 'F.Cu', 'SIM_RESETN'),
]
content, ok = replace_seg(content, 2.7, 24.5, 6.05, 24.5, 'SIM_RESETN', new_segs_1)
if ok:
    print("✅ 交差1修正: SIM_RESETN B.Cuブリッジ")
    changes += 1
else:
    print("❌ 交差1: セグメント見つからず")

# =============================================================================
# 交差3: VBAT × VBAT_SW (F.Cu, x=2.88, y=28.5)
# VBAT F.Cu縦線 x=2.88 (y=26.95-32.65) × VBAT_SW F.Cu横線 y=28.5 (x=2.0-10.55)
#
# 修正: VBAT_SW横線(2.0→10.55)を削除し、via(1.0,28.5)[既存]経由B.Cuに変更
# 経路: SW1.2(2.0,28.85) → F.Cu left to (1.0,28.5) → via(1.0,28.5)[既存] →
#        B.Cu right to (10.55,28.5) → via(10.55,28.5) → C9.pad1
# F.Cu(2.0→1.0): x=2.88 VBATは右側 → 通過しない ✅
# B.Cu(1.0→10.55): VBAT はF.Cuのみ → B.Cu干渉なし ✅
# via(10.55,28.5) size=0.6: C9.pad1(10.55,28.5)に直接接触 ✅
# =============================================================================
new_segs_3 = [
    seg(2.0, 28.5, 1.0, 28.5, 0.5, 'F.Cu', 'VBAT_SW'),
    seg(1.0, 28.5, 10.55, 28.5, 0.5, 'B.Cu', 'VBAT_SW'),
    via(10.55, 28.5, 'VBAT_SW'),
]
content, ok = replace_seg(content, 2.0, 28.5, 10.55, 28.5, 'VBAT_SW', new_segs_3)
if ok:
    print("✅ 交差3修正: VBAT_SW B.Cu経由でVBAT縦線回避")
    changes += 1
else:
    print("❌ 交差3: セグメント見つからず")

# =============================================================================
# 交差4: SIM_RXD × SIM_TXD (B.Cu, x=8.75, y=13.0)
# SIM_RXD B.Cu縦線 x=8.75 (y=6.4-20.0) × SIM_TXD B.Cu横線 y=13.0 (x=3.5-9.25)
#
# 修正: SIM_TXD横線をF.Cuブリッジで SIM_RXD縦線を跨ぐ
# B.Cu (3.5,13.0)→(8.0,13.0): x=8.0+0.1=8.1 < SIM_RXD x_left=8.65 → gap=0.55mm ✅
# Via (8.0,13.0) size=0.4: x_right=8.2 < 8.65 → gap=0.45mm ✅
# F.Cu (8.0,13.0)→(9.25,13.0): 確認済み F.Cu障害物なし ✅
# Via (9.25,13.0) size=0.4: x_left=9.05 > SIM_RXD x_right=8.85 → gap=0.20mm ✅
# 既存 B.Cu (9.25,13.0)→(9.25,21.05) はそのまま接続 ✅
# =============================================================================
new_segs_4 = [
    seg(3.5, 13.0, 8.0, 13.0, 0.2, 'B.Cu', 'SIM_TXD'),
    via(8.0, 13.0, 'SIM_TXD', 0.4, 0.2),
    seg(8.0, 13.0, 9.25, 13.0, 0.2, 'F.Cu', 'SIM_TXD'),
    via(9.25, 13.0, 'SIM_TXD', 0.4, 0.2),
]
content, ok = replace_seg(content, 3.5, 13.0, 9.25, 13.0, 'SIM_TXD', new_segs_4)
if ok:
    print("✅ 交差4修正: SIM_TXD F.Cuブリッジ")
    changes += 1
else:
    print("❌ 交差4: セグメント見つからず")

# =============================================================================
# 交差5: VBAT × CHRG (F.Cu, x=25.0, y=26.3)
# VBAT F.Cu縦線 x=25.0 (y=24.405-27.5) × CHRG F.Cu横線 y=26.3 (x=16.51-25.5)
#
# 修正: CHRG横線をB.Cuブリッジで VBAT縦線を跨ぐ
# F.Cu (25.5,26.3)→(25.65,26.3): 短スタブ右へ
# Via (25.65,26.3) size=0.4: x_left=25.45, VBAT x_right=25.25 → gap=0.20mm ✅
#                             x_right=25.85, SIM_CLK B.Cu x_left=26.04 → gap=0.19mm ✅
# B.Cu (25.65→24.3,26.3): VBAT はF.Cuのみ → B.Cu干渉なし ✅
#                          SIM_DATA B.Cu x=23.6: via(24.3) x_left=24.1 → gap=0.40mm ✅
# Via (24.3,26.3) size=0.4: x_right=24.5, VBAT x_left=24.75 → gap=0.25mm ✅
# F.Cu (24.3,26.3)→(16.51,26.3): R4.pad2(16.51,26.3)まで ✅
# =============================================================================
new_segs_5 = [
    seg(25.5, 26.3, 25.65, 26.3, 0.2, 'F.Cu', 'CHRG'),
    via(25.65, 26.3, 'CHRG', 0.4, 0.2),
    seg(25.65, 26.3, 24.3, 26.3, 0.2, 'B.Cu', 'CHRG'),
    via(24.3, 26.3, 'CHRG', 0.4, 0.2),
    seg(24.3, 26.3, 16.51, 26.3, 0.2, 'F.Cu', 'CHRG'),
]
content, ok = replace_seg(content, 25.5, 26.3, 16.51, 26.3, 'CHRG', new_segs_5)
if ok:
    print("✅ 交差5修正: CHRG B.CuブリッジでVBAT縦線回避")
    changes += 1
else:
    print("❌ 交差5: セグメント見つからず")

with open(PCB_FILE, 'w') as f:
    f.write(content)

print(f"\n合計 {changes}/4 件修正完了（crossing2はGUI手動修正が必要）")
