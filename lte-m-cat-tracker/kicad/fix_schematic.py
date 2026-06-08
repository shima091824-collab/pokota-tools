#!/usr/bin/env python3
"""
スキーマ修正スクリプト - BLOCK-1/2/5/6/8 対応
BLOCK-1: PROG ネット接続（U4.PROG ↔ R3.pin2）
BLOCK-2: CC1/CC2 ネット接続（R1/R2 ↔ J2 CC1/CC2 ピン）
BLOCK-5: U1 VBAT_SW デカップリング 100nF 追加
BLOCK-6: U5 VIN デカップリング 100nF 追加
BLOCK-8: LED_ANODE ネット接続（R4.pin2 ↔ LED1.anode）
"""

import re
import uuid

SCH_PATH = "/Users/m2mac/lte-m-cat-tracker/kicad/lte-m-cat-tracker.kicad_sch"

with open(SCH_PATH) as f:
    content = f.read()

# ---------------------------------------------------------------------------
# Helper: generate UUID
def new_uuid():
    return str(uuid.uuid4())

# Helper: net label
def make_label(name, x, y, angle=0):
    justify = "right" if angle == 180 else "left"
    return (f'  (label "{name}" (at {x} {y} {angle})\n'
            f'    (effects(font(size 1.27 1.27))(justify {justify}))\n'
            f'    (uuid "{new_uuid()}"))')

# Helper: GND power symbol
def make_gnd(x, y):
    ref_y = round(y + 2.54, 4)
    val_y = round(y + 1.27, 4)
    return (f'  (symbol (lib_id "power:GND") (at {x} {y} 0)(unit 1)\n'
            f'    (exclude_from_sim no)(in_bom no)(on_board no)(uuid "{new_uuid()}")\n'
            f'    (property "Reference" "#PWR"(at {x} {ref_y} 0)(effects(font(size 1.27 1.27))hide))\n'
            f'    (property "Value" "GND"(at {x} {val_y} 0)(effects(font(size 1.27 1.27))))\n'
            f'    (property "Footprint" ""(at {x} {y} 0)(effects(font(size 1.27 1.27))hide)))')

# Helper: 100nF 0402 capacitor
def make_cap_100nf(ref, x, y):
    ref_y = round(y - 3.5, 4)
    val_y = round(y - 2.0, 4)
    return (f'  (symbol (lib_id "Device:C") (at {x} {y} 0) (unit 1)\n'
            f'    (exclude_from_sim no)(in_bom yes)(on_board yes)\n'
            f'    (uuid "{new_uuid()}")\n'
            f'    (property "Reference" "{ref}" (at {x} {ref_y} 0)(effects(font(size 1.27 1.27))))\n'
            f'    (property "Value" "100nF" (at {x} {val_y} 0)(effects(font(size 1.27 1.27))))\n'
            f'    (property "Footprint" "Capacitor_SMD:C_0402_1005Metric" (at {x} {y} 0)(effects(font(size 1.27 1.27))hide))\n'
            f'    (property "LCSC" "C14663" (at {x} {y} 0)(effects(font(size 1.27 1.27))hide))\n'
            f'  )')

# ---------------------------------------------------------------------------
# BLOCK-2: CC1ピンへの直結GND削除（(27.94 48.26)のGNDシンボル除去）
# このGNDがCC1を直接GNDに落としている（5.1kΩ経由でなく）
gnd_cc1_block = (
    '  (symbol (lib_id "power:GND") (at 27.94 48.26 0)(unit 1)\n'
    '    (exclude_from_sim no)(in_bom no)(on_board no)(uuid "5b37706f-53d4-45fe-85a0-a2f9430d7b65")\n'
    '    (property "Reference" "#PWR"(at 27.94 50.8 0)(effects(font(size 1.27 1.27))hide))\n'
    '    (property "Value" "GND"(at 27.94 49.53 0)(effects(font(size 1.27 1.27))))\n'
    '    (property "Footprint" ""(at 27.94 48.26 0)(effects(font(size 1.27 1.27))hide)))'
)
if gnd_cc1_block in content:
    content = content.replace(gnd_cc1_block, '')
    print("✅ BLOCK-2: CC1直結GND削除")
else:
    print("⚠️ BLOCK-2: CC1 GNDブロックが見つからない - 手動確認要")

# ---------------------------------------------------------------------------
# 新規要素を追加（ファイル末尾の閉じ括弧の前に挿入）
new_elements = []

# BLOCK-1: PROG ネット
# U4.PROG ピン位置: U4(86.36, 55.88) + TP4056 PROG offset(10.16, -2.54) = (96.52, 53.34)
# R3.pin2位置: R3(96.52, 62.23) + Device:R pin(0, -3.81) = (96.52, 58.42)
new_elements.append(make_label("PROG", 96.52, 53.34, 0))
new_elements.append(make_label("PROG", 96.52, 58.42, 0))
print("✅ BLOCK-1: PROGラベル追加 (96.52,53.34) と (96.52,58.42)")

# BLOCK-2: CC1/CC2 ネット
# J2.CC1 = (40.64-12.70, 50.8-2.54) = (27.94, 48.26)
# R1.pin(右) = (24.13+3.81, 53.34) = (27.94, 53.34)
# J2.CC2 = (27.94, 50.8) — R2.pin(右)=(27.94,50.8)と同座標（共有）
new_elements.append(make_label("CC1", 27.94, 48.26, 0))
new_elements.append(make_label("CC1", 27.94, 53.34, 0))
new_elements.append(make_label("CC2", 27.94, 50.8, 0))
print("✅ BLOCK-2: CC1ラベル×2, CC2ラベル×1 追加")

# BLOCK-8: LED_ANODE ネット
# R4.pin2 = (72.39-3.81, 55.88) = (68.58, 55.88)
# LED1.anode = (64.77+3.81, 55.88) = (68.58, 55.88) ← 同座標
new_elements.append(make_label("LED_ANODE", 68.58, 55.88, 0))
print("✅ BLOCK-8: LED_ANODEラベル追加 (68.58, 55.88)")

# BLOCK-5: U1 VBAT_SW 100nF デカップリング追加
# C12(248.92, 53.34)の右隣に配置
C14_X, C14_Y = 263.52, 53.34
new_elements.append(make_cap_100nf("C14", C14_X, C14_Y))
# top pin (0,-3.81) at (263.52, 49.53) → VBAT_SW ラベル
new_elements.append(make_label("VBAT_SW", C14_X, round(C14_Y - 3.81, 4), 270))
# bottom pin (0,+3.81) at (263.52, 57.15) → GND シンボル
new_elements.append(make_gnd(C14_X, round(C14_Y + 3.81, 4)))
print(f"✅ BLOCK-5: C14 100nF追加 ({C14_X}, {C14_Y})")

# BLOCK-6: U5 VIN 100nF デカップリング追加
# C9(93.98, 93.98)の上に配置
C15_X, C15_Y = 93.98, 76.2
new_elements.append(make_cap_100nf("C15", C15_X, C15_Y))
# top pin at (93.98, 72.39) → VBAT_SW ラベル
new_elements.append(make_label("VBAT_SW", C15_X, round(C15_Y - 3.81, 4), 270))
# bottom pin at (93.98, 80.01) → GND シンボル
new_elements.append(make_gnd(C15_X, round(C15_Y + 3.81, 4)))
print(f"✅ BLOCK-6: C15 100nF追加 ({C15_X}, {C15_Y})")

# ---------------------------------------------------------------------------
# ファイルの末尾閉じ括弧の前に挿入
insert_str = "\n".join(new_elements) + "\n"

# The file ends with \n) - insert before the final closing paren
if content.rstrip().endswith(')'):
    # Find the last ) that closes the kicad_sch
    last_close = content.rstrip().rfind(')')
    content = content[:last_close] + insert_str + content[last_close:]
    print(f"\n合計 {len(new_elements)} 要素を追加")
else:
    print("ERROR: ファイル末尾形式が想定外")
    import sys; sys.exit(1)

with open(SCH_PATH, 'w') as f:
    f.write(content)

print("\n✅ スキーマファイル書き込み完了")
print("次: KiCadで開いてERC確認 → Update PCB from Schematic → PCBレイアウト修正")
