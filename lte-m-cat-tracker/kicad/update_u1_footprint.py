#!/usr/bin/env python3
"""
U1 (SIM7080G-M) フットプリントをPCBの正しい座標に更新するスクリプト

- 旧フットプリント: 推定値で全パッド位置が誤り
- 新フットプリント: HW Design V1.04 + EasyEDA C18548266確認済み
"""
import re, uuid, shutil, os

PCB = "/Users/m2mac/lte-m-cat-tracker/kicad/lte-m-cat-tracker.kicad_pcb"
BAK = PCB + ".bak_update_u1"

# ──────────────────────────────────────────────────────────────
# 1. 新フットプリントのパッド座標 (generate_footprints.py と同じ)
# ──────────────────────────────────────────────────────────────
PITCH = 1.10
SIDE_X = 8.75
TB_Y   = 8.74
SIDE_W, SIDE_H = 0.80, 0.90   # ピッチ方向0.90mm (0.20mmクリアランス)
TB_W,   TB_H   = 0.90, 0.80
LGA_SZ = 0.90

side_ys = [-5.5 * PITCH + i * PITCH for i in range(12)]
tb_xs   = [-4.0 * PITCH + i * PITCH for i in range(9)]

pad_coords = {}  # pad_num → (x, y, w, h)

# 左辺 (1-12, top→bottom)
for i, y in enumerate(side_ys):
    pad_coords[i + 1] = (-SIDE_X, round(y,4), SIDE_W, SIDE_H)

# 下辺 (13-21, left→right)
for i, x in enumerate(tb_xs):
    pad_coords[13 + i] = (round(x,4), +TB_Y, TB_W, TB_H)

# 右辺 (22-33, bottom→top)
for i, y in enumerate(reversed(side_ys)):
    pad_coords[22 + i] = (+SIDE_X, round(y,4), SIDE_W, SIDE_H)

# 上辺 (34-42, right→left)
for i, x in enumerate(reversed(tb_xs)):
    pad_coords[34 + i] = (round(x,4), -TB_Y, TB_W, TB_H)

# 内部LGA (5×7グリッド)
lga_cols = [-4.40, -2.20, 0.00, +2.20, +4.40]
lga_rows = [-4.95, -3.30, -1.65, 0.00, +1.65, +3.30, +4.95]
lga_grid = [
    [43, 44, 45, 46, 68],
    [47, 48, 49, 50, 51],
    [52, 53, 54, 55, 56],
    [57, 58, 59, 60, 61],
    [62, 63, 64, 65, 66],
    [67, 69, 70, 71, 72],
    [73, 74, 75, 76, 77],
]
for r, row in enumerate(lga_grid):
    for c, pin in enumerate(row):
        pad_coords[pin] = (lga_cols[c], lga_rows[r], LGA_SZ, LGA_SZ)

# ──────────────────────────────────────────────────────────────
# 2. スキーマから導出したパッド→ネット対応
# ──────────────────────────────────────────────────────────────
pad_nets = {
    # VBAT (上辺 + NC内部LGA)
    34: "VBAT_SW", 35: "VBAT_SW",
    46: "VBAT_SW", 47: "VBAT_SW",
    # GND (各辺のGNDピン)
    8:  "GND",   # 左辺 GND
    13: "GND",   # 下辺 GND
    19: "GND",   # 下辺 GND
    21: "GND",   # 下辺 GND
    27: "GND",   # 右辺 GND
    30: "GND",   # 右辺 GND (NC_CTS → 30=GND in module)
    31: "GND",   # 右辺 GND
    33: "GND",   # 右辺 GND (end pad)
    36: "GND",   # 上辺 GND
    37: "GND",   # 上辺 GND
    # 内部LGA GND
    45: "GND", 63: "GND", 66: "GND", 67: "GND",
    69: "GND", 70: "GND", 71: "GND", 72: "GND",
    73: "GND", 74: "GND", 75: "GND", 76: "GND", 77: "GND",
    # 制御信号
    39: "SIM_PWRKEY",
    42: "SIM_STATUS",
    28: "SIM_RESETN",   # NC on module, but has schematic net
    # UART2
    22: "SIM_TXD",
    23: "SIM_RXD",
    # SIMカード
    18: "SIM_VDD",
    15: "SIM_DATA",
    16: "SIM_CLK",
    17: "SIM_RST",
    # RF/GNSS
    32: "LTE_ANT",
    68: "GNSS_ANT",
}

# ──────────────────────────────────────────────────────────────
# 3. PCB内のネット番号マッピング取得
# ──────────────────────────────────────────────────────────────
def get_net_numbers(content):
    """PCBから net名 → net番号 のマッピングを取得"""
    net_map = {}
    for m in re.finditer(r'\(net (\d+) "([^"]+)"\)', content):
        net_map[m.group(2)] = int(m.group(1))
    return net_map

# ──────────────────────────────────────────────────────────────
# 4. 新しいパッドブロックを生成
# ──────────────────────────────────────────────────────────────
def make_pad_block(pad_num, x, y, w, h, net_name, net_num=None):
    # KiCad 10 format: (net "NETNAME") without number
    net_line = f'\n\t\t\t(net "{net_name}")' if net_name else ""
    return f'''\t\t(pad "{pad_num}" smd rect
\t\t\t(at {x:.4f} {y:.4f})
\t\t\t(size {w:.4f} {h:.4f})
\t\t\t(layers "F.Cu" "F.Mask" "F.Paste"){net_line}
\t\t\t(thermal_bridge_angle 45)
\t\t\t(uuid "{uuid.uuid4()}")
\t\t)'''

# ──────────────────────────────────────────────────────────────
# 5. 更新実行
# ──────────────────────────────────────────────────────────────
print("PCBを読み込み中...")
with open(PCB) as f:
    content = f.read()

# バックアップ
shutil.copy2(PCB, BAK)
print(f"バックアップ: {BAK}")

lines = content.split('\n')

# U1フットプリントの開始・終了行を特定
u1_start = None
for i, l in enumerate(lines):
    if '(footprint ""' in l and i > 1810 and i < 1830:
        u1_start = i
        break

assert u1_start is not None, "U1 start not found"

# 終了行を探す（括弧の深さで判定）
depth = 0
u1_end = u1_start
for i in range(u1_start, min(u1_start + 3000, len(lines))):
    depth += lines[i].count('(') - lines[i].count(')')
    if depth <= 0:
        u1_end = i
        break

print(f"U1フットプリント: 行{u1_start+1}〜{u1_end+1}")

# パッド開始行（最初の (pad "1" が現れる行）
pad_start = None
for i in range(u1_start, u1_end + 1):
    if '(pad "' in lines[i] and 'smd' in lines[i]:
        pad_start = i
        break

assert pad_start is not None, "pad start not found"
print(f"パッド開始行: {pad_start+1}")

# ネット番号マッピング
net_nums = get_net_numbers(content)
print(f"利用可能ネット: {list(net_nums.keys())[:10]}...")

# フットプリント本体(〜pad_start-1まで)にコートヤードの更新を含める
# courtyard: 旧 ±9.30 → 新 ±9.40
header_lines = lines[u1_start:pad_start]
header_text = '\n'.join(header_lines)
# Update courtyard dimensions
header_text = header_text.replace('-9.3 -8.35', '-9.40 -9.40')
header_text = header_text.replace('9.3 8.35',   '9.40 9.40')
# Also update fab outline
header_text = header_text.replace('-8.8 -7.85', '-8.80 -7.85')
header_text = header_text.replace('8.8 -7.85',  '8.80 -7.85')
header_text = header_text.replace('8.8 7.85',   '8.80 7.85')
header_text = header_text.replace('-8.8 7.85',  '-8.80 7.85')

# 新しいパッドブロックを生成
pad_blocks = []
for num in sorted(pad_coords.keys()):
    x, y, w, h = pad_coords[num]
    net_name = pad_nets.get(num)
    net_num = net_nums.get(net_name) if net_name else None
    pad_blocks.append(make_pad_block(num, x, y, w, h, net_name, net_num))

new_pads = '\n'.join(pad_blocks)

# フットプリント末尾 (")" で閉じる行)
footer = '\t)'

# 新しいPCBコンテンツを組み立て
new_content = (
    '\n'.join(lines[:u1_start]) + '\n' +
    header_text + '\n' +
    new_pads + '\n' +
    footer + '\n' +
    '\n'.join(lines[u1_end + 1:])
)

with open(PCB, 'w') as f:
    f.write(new_content)

print(f"✅ U1フットプリント更新完了: {len(pad_coords)}パッド")

# 確認
updated_content = open(PCB).read()
updated_lines = updated_content.split('\n')
print(f"元の行数: {len(lines)}, 更新後: {len(updated_lines)}")

# 主要パッドの確認
test_pads = [34, 35, 39, 42, 32, 68, 22, 23]
for tp in test_pads:
    x, y, w, h = pad_coords[tp]
    net = pad_nets.get(tp, "unconnected")
    print(f"  pad{tp:2d}: ({x:.2f},{y:.2f}) {net}")
