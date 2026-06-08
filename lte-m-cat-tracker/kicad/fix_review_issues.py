#!/usr/bin/env python3
"""
5専門家レビュー後の修正スクリプト（2026-06-08）
修正内容:
  1. WIFI_ANT配線幅 0.2mm → 1.52mm（50Ω整合）
  2. R8(10kΩ) GPIO2プルダウン追加
"""

import re, uuid

PCB_IN  = "kicad/lte-m-cat-tracker.kicad_pcb"
PCB_OUT = "kicad/lte-m-cat-tracker.kicad_pcb"

with open(PCB_IN) as f:
    content = f.read()

# ─────────────────────────────────────────────
# FIX 1: WIFI_ANT配線幅を1.52mmに変更し経路最適化
# 旧: (6.05,21.75)→(5.8,21.75)→(5.8,20.87)→(1,20.87)→(1,19) 幅0.2mm
# 新: (6.05,21.75)→(6.05,21.6)→(1.0,21.6)→(1.0,19.0) 幅1.52mm
#   上端y=20.84(+3.3V下端y≈20.55からgap=0.29mm ✓)
#   下端y=22.36(GND禁止ゾーン下端y=22.5から0.14mm ✓)
# ─────────────────────────────────────────────

# 旧WIFI_ANT 4セグメントを削除
old_wifi_segments = [
    r'\s*\(segment\s*\(start 1 20\.87\)\s*\(end 1 19\)\s*\(width 0\.2\)\s*\(layer "F\.Cu"\)\s*\(net "WIFI_ANT"\)\s*\(uuid "[^"]+"\)\s*\)',
    r'\s*\(segment\s*\(start 5\.8 20\.87\)\s*\(end 1 20\.87\)\s*\(width 0\.2\)\s*\(layer "F\.Cu"\)\s*\(net "WIFI_ANT"\)\s*\(uuid "[^"]+"\)\s*\)',
    r'\s*\(segment\s*\(start 6\.05 21\.75\)\s*\(end 5\.8 21\.75\)\s*\(width 0\.2\)\s*\(layer "F\.Cu"\)\s*\(net "WIFI_ANT"\)\s*\(uuid "[^"]+"\)\s*\)',
    r'\s*\(segment\s*\(start 5\.8 21\.75\)\s*\(end 5\.8 20\.87\)\s*\(width 0\.2\)\s*\(layer "F\.Cu"\)\s*\(net "WIFI_ANT"\)\s*\(uuid "[^"]+"\)\s*\)',
]

removed = 0
for pat in old_wifi_segments:
    new_content, n = re.subn(pat, '', content, flags=re.DOTALL)
    if n > 0:
        content = new_content
        removed += n
print(f"旧WIFI_ANT segments削除: {removed}件")

# 新WIFI_ANT 3セグメント (幅1.52mm)
new_wifi_segs = ""
wifi_routes = [
    ((6.05, 21.75), (6.05, 21.6)),   # 縦: U2.pad1から下へ
    ((6.05, 21.6),  (1.0,  21.6)),   # 横: 左へ
    ((1.0,  21.6),  (1.0,  19.0)),   # 縦: ANT3.pad1へ
]
for (sx, sy), (ex, ey) in wifi_routes:
    uid = str(uuid.uuid4())
    new_wifi_segs += f"""
\t(segment
\t\t(start {sx} {sy})
\t\t(end {ex} {ey})
\t\t(width 1.52)
\t\t(layer "F.Cu")
\t\t(net "WIFI_ANT")
\t\t(uuid "{uid}")
\t)"""

# ─────────────────────────────────────────────
# FIX 2: R8(10kΩ 0402)追加 – GPIO2プルダウン
# 配置: (9.5, 20.0) pad1=SIM_TXD, pad2=GND
# pad1(9.02,20.0) → U2.pad27(9.25,21.05) をF.Cuで接続
# pad2(9.98,20.0) → GNDゾーンへスタブ（ゾーン充填で接続）
# ─────────────────────────────────────────────

R8_X, R8_Y = 9.5, 20.0
R8_PAD1_X = R8_X - 0.48  # 9.02
R8_PAD2_X = R8_X + 0.48  # 9.98
PAD_SIZE  = "0.56 0.62"
PAD_UID1  = str(uuid.uuid4())
PAD_UID2  = str(uuid.uuid4())
FP_UID    = str(uuid.uuid4())
REF_UID   = str(uuid.uuid4())
VAL_UID   = str(uuid.uuid4())
FAB_UID   = str(uuid.uuid4())

r8_footprint = f"""
\t(footprint "0402"
\t\t(layer "F.Cu")
\t\t(uuid "{FP_UID}")
\t\t(at {R8_X} {R8_Y})
\t\t(property "Reference" "R8"
\t\t\t(at 0 -1 0)
\t\t\t(layer "F.SilkS")
\t\t\t(uuid "{REF_UID}")
\t\t\t(effects (font (size 0.8 0.8) (thickness 0.12)))
\t\t)
\t\t(property "Value" "10k"
\t\t\t(at 0 1 0)
\t\t\t(layer "F.Fab")
\t\t\t(uuid "{VAL_UID}")
\t\t\t(effects (font (size 0.8 0.8) (thickness 0.12)))
\t\t)
\t\t(fp_rect
\t\t\t(start -0.5 -0.35) (end 0.5 0.35)
\t\t\t(layer "F.Fab") (width 0.1)
\t\t\t(uuid "{FAB_UID}")
\t\t)
\t\t(pad "1" smd rect
\t\t\t(at -0.48 0)
\t\t\t(size {PAD_SIZE})
\t\t\t(layers "F.Cu" "F.Mask" "F.Paste")
\t\t\t(net "SIM_TXD")
\t\t\t(thermal_bridge_angle 45)
\t\t\t(uuid "{PAD_UID1}")
\t\t)
\t\t(pad "2" smd rect
\t\t\t(at 0.48 0)
\t\t\t(size {PAD_SIZE})
\t\t\t(layers "F.Cu" "F.Mask" "F.Paste")
\t\t\t(net "GND")
\t\t\t(thermal_bridge_angle 45)
\t\t\t(uuid "{PAD_UID2}")
\t\t)
\t)"""

# R8.pad1 → U2.pad27 接続配線
# pad1絶対座標: (9.02, 20.0)
# U2.pad27: (9.25, 21.05)
seg_r8_uid1 = str(uuid.uuid4())
seg_r8_uid2 = str(uuid.uuid4())
r8_routing = f"""
\t(segment
\t\t(start {R8_PAD1_X:.2f} {R8_Y})
\t\t(end {R8_PAD1_X:.2f} 21.05)
\t\t(width 0.2)
\t\t(layer "F.Cu")
\t\t(net "SIM_TXD")
\t\t(uuid "{seg_r8_uid1}")
\t)
\t(segment
\t\t(start {R8_PAD1_X:.2f} 21.05)
\t\t(end 9.25 21.05)
\t\t(width 0.2)
\t\t(layer "F.Cu")
\t\t(net "SIM_TXD")
\t\t(uuid "{seg_r8_uid2}")
\t)"""

# ─────────────────────────────────────────────
# PCBファイルの末尾（）の直前に挿入
# ─────────────────────────────────────────────

insert_block = new_wifi_segs + r8_footprint + r8_routing

# PCBの最後の閉じ括弧の前に挿入
content = content.rstrip()
if content.endswith(')'):
    content = content[:-1] + insert_block + "\n)"
else:
    content += insert_block

with open(PCB_OUT, 'w') as f:
    f.write(content)

print("WIFI_ANT配線 → 1.52mm幅 (3セグメント) 追加完了")
print("R8(10kΩ) GPIO2プルダウン追加完了")
print(f"出力: {PCB_OUT}")
