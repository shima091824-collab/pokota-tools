#!/usr/bin/env python3
"""
tracks_crossing 5件を修正するスクリプト

各交差をB.CuまたはF.Cuブリッジで解消する:
1. +3.3V × SIM_RESETN (F.Cu, x=3.5, y=24.5) → SIM_RESETNをB.Cuブリッジ
2. I2C_SCL × I2C_SDA (F.Cu, y=26.5共有) → I2C_SDAをy=26.8に移動
3. VBAT × VBAT_SW (F.Cu, x=2.88, y=28.5) → VBAT_SWをB.Cu経由に変更
4. SIM_RXD × SIM_TXD (B.Cu, x=8.75, y=13.0) → SIM_TXDをF.Cuブリッジ
5. VBAT × CHRG (F.Cu, x=25.0, y=26.3) → CHRGをB.Cuブリッジ
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

# Helper: replace a segment by exact coords
def replace_seg(content, x1, y1, x2, y2, net, new_segs):
    """x1,y1 → x2,y2 のセグメントを見つけて new_segs に置換（どちらの方向でも）"""
    # Try both directions
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

def insert_after_seg(content, x1, y1, x2, y2, net, new_segs):
    """セグメントの直後に new_segs を挿入"""
    for sx1, sy1, sx2, sy2 in [(x1, y1, x2, y2), (x2, y2, x1, y1)]:
        pattern = (
            r'\t\(segment \(start ' + re.escape(str(sx1)) + r' ' + re.escape(str(sy1)) +
            r'\) \(end ' + re.escape(str(sx2)) + r' ' + re.escape(str(sy2)) +
            r'\) \(width [0-9.]+\) \(layer "[^"]+"\) \(net "' + re.escape(net) + r'"\) \(uuid "[^"]+"\)\)'
        )
        m = re.search(pattern, content)
        if m:
            insert_pos = m.end()
            insertion = '\n' + '\n'.join(new_segs)
            content = content[:insert_pos] + insertion + content[insert_pos:]
            return content, True
    return content, False

changes = 0

# =============================================================================
# 交差1: +3.3V × SIM_RESETN
# SIM_RESETN F.Cu (2.7,24.5)→(6.05,24.5) を B.Cuブリッジに変更
# B.Cuブリッジ: F.Cu(2.7→3.0) + via(3.0) + B.Cu(3.0→4.0) + via(4.0) + F.Cu(4.0→6.05)
# +3.3V F.Cu at x=3.5, half-width=0.15 → F.Cu stops at x=3.0 (gap=0.25mm) and resumes at x=4.0 (gap=0.25mm)
# B.Cu at y=24.5 x=3.0→4.0: SIM_PWRKEY B.Cu at x=2.2 (gap=0.7mm) ✅
# =============================================================================
new_segs_1 = [
    seg(2.7, 24.5, 3.0, 24.5, 0.2, 'F.Cu', 'SIM_RESETN'),   # F.Cu left portion
    via(3.0, 24.5, 'SIM_RESETN', 0.4, 0.2),                   # B.Cu via
    seg(3.0, 24.5, 4.0, 24.5, 0.2, 'B.Cu', 'SIM_RESETN'),    # B.Cu bridge over +3.3V
    via(4.0, 24.5, 'SIM_RESETN', 0.4, 0.2),                   # back to F.Cu
    seg(4.0, 24.5, 6.05, 24.5, 0.2, 'F.Cu', 'SIM_RESETN'),   # F.Cu right portion
]
content, ok = replace_seg(content, 2.7, 24.5, 6.05, 24.5, 'SIM_RESETN', new_segs_1)
if ok:
    print("✅ 交差1修正: SIM_RESETN B.Cuブリッジ追加")
    changes += 1
else:
    print("❌ 交差1: セグメント見つからず")

# =============================================================================
# 交差2: I2C_SCL × I2C_SDA
# I2C_SDA の y=26.5 共有部分を y=26.8 に移動
# 変更するセグメント:
#   (9.25,25.95)→(9.25,26.5) → (9.25,25.95)→(9.25,26.8)
#   (9.25,26.5)→(15.0,26.5)  → (9.25,26.8)→(15.2,26.8)
#   (15.0,26.5)→(15.0,23.4)  → (15.2,26.8)→(15.2,23.4)
#   (15.0,23.4)→(13.75,23.4) → (15.2,23.4)→(13.75,23.4)
# x=15.0 から x=15.2 に変更: I2C_SCL vertical at x=15.0 (y=24.85-26.5) を回避
# at x=15.2 y=23.4-26.8: 確認済み障害物なし ✅
# =============================================================================
content, ok2a = replace_seg(content, 9.25, 25.95, 9.25, 26.5, 'I2C_SDA',
    [seg(9.25, 25.95, 9.25, 26.8, 0.2, 'F.Cu', 'I2C_SDA')])
content, ok2b = replace_seg(content, 9.25, 26.5, 15.0, 26.5, 'I2C_SDA',
    [seg(9.25, 26.8, 15.2, 26.8, 0.2, 'F.Cu', 'I2C_SDA')])
content, ok2c = replace_seg(content, 15.0, 26.5, 15.0, 23.4, 'I2C_SDA',
    [seg(15.2, 26.8, 15.2, 23.4, 0.2, 'F.Cu', 'I2C_SDA')])
content, ok2d = replace_seg(content, 15.0, 23.4, 13.75, 23.4, 'I2C_SDA',
    [seg(15.2, 23.4, 13.75, 23.4, 0.2, 'F.Cu', 'I2C_SDA')])
if ok2a and ok2b and ok2c and ok2d:
    print("✅ 交差2修正: I2C_SDA y=26.5→y=26.8 に移動")
    changes += 1
else:
    print(f"❌ 交差2: 一部見つからず (2a={ok2a}, 2b={ok2b}, 2c={ok2c}, 2d={ok2d})")

# =============================================================================
# 交差3: VBAT × VBAT_SW
# VBAT_SW F.Cu (2.0,28.5)→(10.55,28.5) を削除し B.Cu経由に変更
# 新経路: SW1.2(2.0,28.85) → F.Cu(2.0→1.0,28.5) → existing via(1.0,28.5) → B.Cu(1.0→10.55,28.5) → via(10.55,28.5) → C9.pad1
# VBAT F.Cu at x=2.88: B.Cu段階では別レイヤーなので干渉なし ✅
# =============================================================================
new_segs_3 = [
    seg(2.0, 28.5, 1.0, 28.5, 0.5, 'F.Cu', 'VBAT_SW'),   # F.Cu left to existing via
    seg(1.0, 28.5, 10.55, 28.5, 0.5, 'B.Cu', 'VBAT_SW'), # B.Cu right to C9
    via(10.55, 28.5, 'VBAT_SW'),                            # connect to C9.pad1 F.Cu
]
content, ok = replace_seg(content, 2.0, 28.5, 10.55, 28.5, 'VBAT_SW', new_segs_3)
if ok:
    print("✅ 交差3修正: VBAT_SW B.Cu経由でVBAT回避")
    changes += 1
else:
    print("❌ 交差3: セグメント見つからず")

# =============================================================================
# 交差4: SIM_RXD × SIM_TXD
# SIM_TXD B.Cu (3.5,13.0)→(9.25,13.0) を分割してF.Cuブリッジ挿入
# SIM_RXD B.Cu at x=8.75: ブリッジはF.Cu層で通過するため干渉なし ✅
# Gap: via(8.0,13.0)右端8.2, SIM_RXD左端8.65 → gap=0.45mm ✅
#       via(9.25,13.0)左端9.05, SIM_RXD右端8.85 → gap=0.20mm ✅
# =============================================================================
new_segs_4 = [
    seg(3.5, 13.0, 8.0, 13.0, 0.2, 'B.Cu', 'SIM_TXD'),   # B.Cu stops before SIM_RXD
    via(8.0, 13.0, 'SIM_TXD', 0.4, 0.2),                   # switch to F.Cu
    seg(8.0, 13.0, 9.25, 13.0, 0.2, 'F.Cu', 'SIM_TXD'),  # F.Cu bridge over SIM_RXD
    via(9.25, 13.0, 'SIM_TXD', 0.4, 0.2),                  # back to B.Cu
]
content, ok = replace_seg(content, 3.5, 13.0, 9.25, 13.0, 'SIM_TXD', new_segs_4)
if ok:
    print("✅ 交差4修正: SIM_TXD F.Cuブリッジ追加")
    changes += 1
else:
    print("❌ 交差4: セグメント見つからず")

# =============================================================================
# 交差5: VBAT × CHRG
# CHRG F.Cu (25.5,26.3)→(16.51,26.3) を B.Cuブリッジに変更
# VBAT F.Cu at x=25.0 (y=24.405-27.5): B.Cuではレイヤー違いで干渉なし ✅
# Gap: via(25.65,26.3)左端25.45, VBAT右端25.25 → gap=0.20mm ✅
#       via(24.3,26.3)右端24.5, VBAT左端24.75 → gap=0.25mm ✅
# SIM_CLK B.Cu at x=26.14: via(25.65,26.3)右端25.85, SIM_CLK左端26.04 → gap=0.19mm ✅
# SIM_DATA B.Cu at x=23.6: via(24.3,26.3)左端24.1, SIM_DATA右端23.7 → gap=0.40mm ✅
# =============================================================================
new_segs_5 = [
    seg(25.5, 26.3, 25.65, 26.3, 0.2, 'F.Cu', 'CHRG'),    # short right stub
    via(25.65, 26.3, 'CHRG', 0.4, 0.2),                     # to B.Cu
    seg(25.65, 26.3, 24.3, 26.3, 0.2, 'B.Cu', 'CHRG'),     # B.Cu bridge past VBAT
    via(24.3, 26.3, 'CHRG', 0.4, 0.2),                      # back to F.Cu
    seg(24.3, 26.3, 16.51, 26.3, 0.2, 'F.Cu', 'CHRG'),     # F.Cu to R4
]
content, ok = replace_seg(content, 25.5, 26.3, 16.51, 26.3, 'CHRG', new_segs_5)
if ok:
    print("✅ 交差5修正: CHRG B.CuブリッジでVBAT回避")
    changes += 1
else:
    print("❌ 交差5: セグメント見つからず")

with open(PCB_FILE, 'w') as f:
    f.write(content)

print(f"\n合計 {changes}/5 件修正完了")
