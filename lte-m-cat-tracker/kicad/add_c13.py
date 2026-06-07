#!/usr/bin/env python3
"""
C13 (100μF 6.3V Polymer Al, 1210) をPCBに追加するスクリプト

配置場所: (9.0, 32.0)
- J1右側・J1 CrtYd(x_max=6.98)との重なりなし
- SW1 CrtYd(y_max=30.65)との重なりなし
- C9 CrtYd(x=[10.5,12.5])との重なりなし

接続:
- pad1(VBAT): x=2.88 VBATバス縦線からタップ
- pad2(GND): GNDゾーンで自動接続

1210フットプリント (Capacitor_SMD:C_1210_3225Metric 相当):
- pad: ±1.475mm オフセット, サイズ 1.15×2.7mm, roundrect
- CrtYd: ±1.6×±1.25mm
"""

import uuid

PCB_FILE = '/Users/m2mac/lte-m-cat-tracker/kicad/lte-m-cat-tracker.kicad_pcb'

CX, CY = 9.0, 33.3  # C13 center
# (9.0, 32.0)はJ2.A4 VUSB(10.75,31.3) size=0.3x0.8 y_bottom=31.7 と
# C13.pad2 size=1.15x2.7 y_top=30.65 が重なるため33.3に移動
# C13.pad2 at (10.475, 33.3): y_top=33.3-1.35=31.95mm, J2.A4 y_bottom=31.7mm → gap=0.25mm ✅
# J1 CrtYd x_max=6.98 < C13 CrtYd x_min=7.4 → 重なりなし ✅

def new_uuid():
    return str(uuid.uuid4())

# C13フットプリントブロック（1210パッケージ）
c13_footprint = f"""\t(footprint "Capacitor_SMD:C_1210_3225Metric"
\t\t(layer "F.Cu")
\t\t(uuid "{new_uuid()}")
\t\t(at {CX} {CY})
\t\t(property "Reference" "C13"
\t\t\t(at 0 -2.3 0)
\t\t\t(layer "F.SilkS")
\t\t\t(uuid "{new_uuid()}")
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 0.8 0.8)
\t\t\t\t\t(thickness 0.12)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Value" "100uF_6.3V_PolymerAl"
\t\t\t(at 0 2.3 0)
\t\t\t(layer "F.Fab")
\t\t\t(uuid "{new_uuid()}")
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 0.8 0.8)
\t\t\t\t\t(thickness 0.12)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Datasheet" ""
\t\t\t(at 0 0 0)
\t\t\t(layer "F.Fab")
\t\t\t(hide yes)
\t\t\t(uuid "{new_uuid()}")
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "LCSC" "要LCSC確認"
\t\t\t(at 0 0 0)
\t\t\t(layer "F.Fab")
\t\t\t(hide yes)
\t\t\t(uuid "{new_uuid()}")
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(duplicate_pad_numbers_are_jumpers no)
\t\t(fp_line
\t\t\t(start -0.825 -1.35)
\t\t\t(end 0.825 -1.35)
\t\t\t(stroke (width 0.12) (type solid))
\t\t\t(layer "F.SilkS")
\t\t\t(uuid "{new_uuid()}")
\t\t)
\t\t(fp_line
\t\t\t(start -0.825 1.35)
\t\t\t(end 0.825 1.35)
\t\t\t(stroke (width 0.12) (type solid))
\t\t\t(layer "F.SilkS")
\t\t\t(uuid "{new_uuid()}")
\t\t)
\t\t(fp_rect
\t\t\t(start -1.6 -1.25)
\t\t\t(end 1.6 1.25)
\t\t\t(stroke (width 0.05) (type solid))
\t\t\t(fill no)
\t\t\t(layer "F.CrtYd")
\t\t\t(uuid "{new_uuid()}")
\t\t)
\t\t(fp_rect
\t\t\t(start -1.6 -1.25)
\t\t\t(end 1.6 1.25)
\t\t\t(stroke (width 0.1) (type solid))
\t\t\t(fill no)
\t\t\t(layer "F.Fab")
\t\t\t(uuid "{new_uuid()}")
\t\t)
\t\t(fp_text user "${{REFERENCE}}"
\t\t\t(at 0 0 0)
\t\t\t(layer "F.Fab")
\t\t\t(uuid "{new_uuid()}")
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 0.5 0.5)
\t\t\t\t\t(thickness 0.08)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(pad "1" smd roundrect
\t\t\t(at -1.475 0)
\t\t\t(size 1.15 2.7)
\t\t\t(layers "F.Cu" "F.Mask" "F.Paste")
\t\t\t(roundrect_rratio 0.217391)
\t\t\t(net "VBAT")
\t\t\t(thermal_bridge_angle 45)
\t\t\t(uuid "{new_uuid()}")
\t\t)
\t\t(pad "2" smd roundrect
\t\t\t(at 1.475 0)
\t\t\t(size 1.15 2.7)
\t\t\t(layers "F.Cu" "F.Mask" "F.Paste")
\t\t\t(roundrect_rratio 0.217391)
\t\t\t(net "GND")
\t\t\t(thermal_bridge_angle 45)
\t\t\t(uuid "{new_uuid()}")
\t\t)
\t\t(embedded_fonts no)
\t)
"""

# VBATバスからC13.pad1へのタップ配線
# J1.pad2 GND (4.125, 32.65), size=0.6x1.7 → y_range=[31.80,33.50]
# 直線(y=33.3)はJ1.pad2と短絡するため、y=31.0経由で迂回
# VBATバス縦線はx=2.875を通る（J1.1からSW1.1まで）
# タップ: (2.875, 31.0) → (7.525, 31.0) → (7.525, 33.3)
# 検証:
#   (2.875,31.0)→(7.525,31.0) y=31.0±0.25: J1.pad2 y_top=31.80 → gap=31.80-31.25=0.55mm ✅
#   (7.525,31.0)→(7.525,33.3) x=7.525±0.25: J1.pad2 x_right=4.425 → gap=3.1mm ✅
c13_vbat_tap = f"""\t(segment
\t\t(start 2.875 31.0)
\t\t(end 7.525 31.0)
\t\t(width 0.5)
\t\t(layer "F.Cu")
\t\t(net "VBAT")
\t\t(uuid "{new_uuid()}")
\t)
\t(segment
\t\t(start 7.525 31.0)
\t\t(end 7.525 33.3)
\t\t(width 0.5)
\t\t(layer "F.Cu")
\t\t(net "VBAT")
\t\t(uuid "{new_uuid()}")
\t)
"""

with open(PCB_FILE, 'r') as f:
    content = f.read()

# GNDゾーン定義の直前に挿入（他のrouteスクリプトと同じ位置）
insert_marker = '\t(zone\n\t\t(net "GND")\n\t\t(layer "F.Cu")'
pos = content.find(insert_marker)
if pos == -1:
    pos = content.rfind('\n)')
    print("⚠️ GNDゾーンマーカーが見つからないためファイル末尾に挿入")

new_content = content[:pos] + c13_footprint + c13_vbat_tap + content[pos:]

with open(PCB_FILE, 'w') as f:
    f.write(new_content)

pad1_abs = (CX - 1.475, CY)
pad2_abs = (CX + 1.475, CY)
crtydb = (CX - 1.6, CY - 1.25, CX + 1.6, CY + 1.25)

print(f"✅ C13追加完了")
print(f"   配置: ({CX}, {CY})")
print(f"   pad1 VBAT abs: {pad1_abs}")
print(f"   pad2 GND  abs: {pad2_abs}")
print(f"   CrtYd abs: x=[{crtydb[0]:.2f},{crtydb[2]:.2f}], y=[{crtydb[1]:.2f},{crtydb[3]:.2f}]")
print(f"   VBATタップ配線: (2.875,31.0)→(7.525,31.0)→(7.525,{CY})")
print()
print("次のステップ:")
print("  python3 -c \"...DRCフロー...\" でDRC確認")
