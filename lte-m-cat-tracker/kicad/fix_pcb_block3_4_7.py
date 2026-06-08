#!/usr/bin/env python3
"""
PCB修正スクリプト - BLOCK-3/4/7 対応
BLOCK-3: J2(USB-C)を基板内側0.5mm移動（copper_edge_clearance解消）
BLOCK-4: C13をJ2から1.5mm以上離す（courtyard_overlap解消）
BLOCK-7: ANT3(WiFiアンテナ)周囲にGND禁止ゾーン追加（全レイヤー、3mm以上）
"""

import re
import uuid

PCB_PATH = "/Users/m2mac/lte-m-cat-tracker/kicad/lte-m-cat-tracker.kicad_pcb"

with open(PCB_PATH) as f:
    content = f.read()

original = content  # バックアップ用

def new_uuid():
    return str(uuid.uuid4())

# ---------------------------------------------------------------------------
# BLOCK-3: J2を(12, 33)から(12, 32.5)へ移動（0.5mm基板内側）
# 現在: B1-B8, A11-A12パッドがy=34.7 → 0.4mm幅パッドでedge(35)に接触
# 修正後: パッドがy=34.2 → bottom_edge=34.6, gap=0.4mm ✓
old_j2_pos = "(at 12 33)"
new_j2_pos = "(at 12 32.5)"

# J2フットプリントのat座標のみ変更（ピン相対座標は変わらない）
# まずJ2フットプリントブロックを特定して変更
idx_j2 = content.find('"J2"')
if idx_j2 > 0:
    fp_start = content.rfind('\n\t(footprint', 0, idx_j2)
    # フットプリントの(at ...)を変更
    fp_at_match = re.search(r'\(at 12 33\)', content[fp_start:fp_start+200])
    if fp_at_match:
        abs_pos = fp_start + fp_at_match.start()
        content = content[:abs_pos] + new_j2_pos + content[abs_pos + len(old_j2_pos):]
        print("✅ BLOCK-3: J2を(12,33)→(12,32.5)に移動")
    else:
        print(f"⚠️ BLOCK-3: J2のat座標が想定外: {content[fp_start:fp_start+100]}")
else:
    print("⚠️ BLOCK-3: J2が見つからない")

# ---------------------------------------------------------------------------
# BLOCK-4: C13を(9, 33.3)から(4.5, 33.3)へ移動
# 目的: J2のcourtyard左端(7.2)から1.69mm以上の間隔を確保
# C13 pad2 right_edge = 4.5+0.508+0.5 = 5.508 → J2との間隔: 7.2-5.508=1.692mm ✓
idx_c13 = content.find('"C13"')
if idx_c13 > 0:
    fp_start = content.rfind('\n\t(footprint', 0, idx_c13)
    fp_at_match = re.search(r'\(at 9 33\.3\)', content[fp_start:fp_start+200])
    if fp_at_match:
        abs_pos = fp_start + fp_at_match.start()
        old_c13 = "(at 9 33.3)"
        new_c13 = "(at 4.5 33.3)"
        content = content[:abs_pos] + new_c13 + content[abs_pos + len(old_c13):]
        print("✅ BLOCK-4: C13を(9,33.3)→(4.5,33.3)に移動（J2から1.69mm確保）")
    else:
        print(f"⚠️ BLOCK-4: C13のat座標が想定外")
else:
    print("⚠️ BLOCK-4: C13が見つからない")

# ---------------------------------------------------------------------------
# BLOCK-7: ANT3(WiFiチップアンテナ, (1.8,19))周囲にGND禁止ゾーン追加
# GND fill(copper pour)のみ禁止、トレース/ビアは通過可
# ゾーン範囲: x(-0.5〜6.5), y(15.5〜22.5) — アンテナから3mm以上確保
# F.CuとB.Cuの両方に追加

def make_keepout_zone(layer, x_min, y_min, x_max, y_max):
    return f"""
\t(zone
\t\t(net 0)
\t\t(net_name "")
\t\t(layer "{layer}")
\t\t(uuid "{new_uuid()}")
\t\t(hatch edge 0.508)
\t\t(keepout
\t\t\t(tracks allowed)
\t\t\t(vias allowed)
\t\t\t(pads allowed)
\t\t\t(copperpour not_allowed)
\t\t\t(footprints allowed)
\t\t)
\t\t(polygon
\t\t\t(pts
\t\t\t\t(xy {x_min} {y_min})
\t\t\t\t(xy {x_max} {y_min})
\t\t\t\t(xy {x_max} {y_max})
\t\t\t\t(xy {x_min} {y_max})
\t\t\t)
\t\t)
\t)"""

# ANT3 at (1.8, 19), zone: 3mm以上の余白
x_min, y_min = -0.5, 15.5
x_max, y_max = 6.5, 22.5

zone_fcu = make_keepout_zone("F.Cu", x_min, y_min, x_max, y_max)
zone_bcu = make_keepout_zone("B.Cu", x_min, y_min, x_max, y_max)

# ファイル末尾の閉じ括弧の前に挿入
last_close = content.rstrip().rfind(')')
content = content[:last_close] + zone_fcu + zone_bcu + "\n" + content[last_close:]
print(f"✅ BLOCK-7: ANT3 GND禁止ゾーン追加 F.Cu+B.Cu ({x_min},{y_min})〜({x_max},{y_max})")

# ---------------------------------------------------------------------------
# 書き込み
with open(PCB_PATH, 'w') as f:
    f.write(content)

print("\n✅ PCBファイル書き込み完了")
print("次: KiCad PCB Editor で確認:")
print("  1. B キー (ゾーン再充填) でGND禁止ゾーンを確認")
print("  2. Update PCB from Schematic (Tools > Update PCB from Schematic)")
print("  3. 新規ネット (PROG/CC1/CC2/LED_ANODE/C14/C15) のルーティング")
print("  4. DRC実行で BLOCK-3/4/7 解消を確認")
