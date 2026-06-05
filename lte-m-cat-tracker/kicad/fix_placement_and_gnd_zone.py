#!/usr/bin/env python3
"""
LTE-M Cat Tracker PCB: 配置修正 + GNDゾーン追加
- C5, C6: y=19.0 → y=20.5 (U1パッド26/27との0mm重複を解消)
- C4: y=19.0 → y=20.5 (予防的移動)
- R5: y=19.5 → y=20.0 (U1パッド28との0.03mm違反を解消)
- GNDカッパーフィル: F.Cu + B.Cu に追加 (GND配線を自動処理)
"""
import re, shutil, uuid, os

PCB_FILE = "/Users/m2mac/lte-m-cat-tracker/kicad/lte-m-cat-tracker.kicad_pcb"

# バックアップ
backup = PCB_FILE + ".bak_placement"
shutil.copy2(PCB_FILE, backup)
print(f"バックアップ: {backup}")

with open(PCB_FILE, encoding="utf-8") as f:
    content = f.read()

# ── 部品位置修正 ────────────────────────────────────────────────────────
moves = {
    "C4": (6.5,  19.0, 6.5,  20.5),
    "C5": (8.5,  19.0, 8.5,  20.5),
    "C6": (10.5, 19.0, 10.5, 20.5),
    "R5": (13.0, 19.5, 13.0, 20.0),
}

def move_component(text, ref, old_x, old_y, new_x, new_y):
    """footprintブロック内の (at X Y) を書き換える"""
    idx = text.find(f'(property "Reference" "{ref}"')
    if idx < 0:
        print(f"  WARNING: {ref} が見つからない")
        return text
    block_start = text.rfind("(footprint", 0, idx)
    block_end = text.find("\n\t(footprint", block_start + 10)
    if block_end < 0:
        block_end = len(text)

    block = text[block_start:block_end]

    # footprint の最初の (at X Y [rot]) を置換
    pattern = rf'\(at {re.escape(f"{old_x:.4f}")} {re.escape(f"{old_y:.4f}")}((?:\s+[\d.-]+)?)\)'
    replacement = f"(at {new_x:.4f} {new_y:.4f}\\1)"
    new_block, n = re.subn(pattern, replacement, block, count=1)

    if n == 0:
        # 小数点桁数が違う場合も試す
        old_x_str = f"{old_x}"
        old_y_str = f"{old_y}"
        pattern2 = rf'\(at {re.escape(old_x_str)} {re.escape(old_y_str)}((?:\s+[\d.-]+)?)\)'
        new_block, n = re.subn(pattern2, replacement, block, count=1)

    if n == 0:
        # さらにフォールバック
        old_pat = f"(at {old_x:.4f} {old_y:.4f}"
        if old_pat in block:
            new_block = block.replace(old_pat, f"(at {new_x:.4f} {new_y:.4f}", 1)
            n = 1

    if n > 0:
        print(f"  {ref}: ({old_x}, {old_y}) → ({new_x}, {new_y}) ✓")
        return text[:block_start] + new_block + text[block_end:]
    else:
        print(f"  WARNING: {ref} の at が見つからない (old: {old_x:.4f},{old_y:.4f})")
        return text

print("\n■ 部品位置修正:")
for ref, (ox, oy, nx, ny) in moves.items():
    content = move_component(content, ref, ox, oy, nx, ny)

# ── GND カッパーフィルゾーン追加 ────────────────────────────────────────
# ボードエリア: 0,0 〜 30,35 (mm)
# Edge.Cuts から確認済み (generate_pcb.py と一致)
BOARD_X1, BOARD_Y1 = 0.0,  0.0
BOARD_X2, BOARD_Y2 = 30.0, 35.0
# マージン 0.25mm 内側に入れる
M = 0.25
ZX1, ZY1 = BOARD_X1 + M, BOARD_Y1 + M
ZX2, ZY2 = BOARD_X2 - M, BOARD_Y2 - M

def make_zone(layer: str, net: int = 21, net_name: str = "GND") -> str:
    uid = str(uuid.uuid4())
    return f"""
\t(zone
\t\t(net {net})
\t\t(net_name "{net_name}")
\t\t(layer "{layer}")
\t\t(uuid "{uid}")
\t\t(hatch edge 0.508)
\t\t(connect_pads (clearance 0.2))
\t\t(min_thickness 0.2)
\t\t(filled_areas_thickness no)
\t\t(fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3))
\t\t(polygon
\t\t\t(pts
\t\t\t\t(xy {ZX1:.3f} {ZY1:.3f}) (xy {ZX2:.3f} {ZY1:.3f}) (xy {ZX2:.3f} {ZY2:.3f}) (xy {ZX1:.3f} {ZY2:.3f})
\t\t\t)
\t\t)
\t)"""

print("\n■ GNDゾーン追加: F.Cu + B.Cu")
gnd_zones = make_zone("F.Cu") + make_zone("B.Cu")

# ファイル末尾の ) の直前に挿入
insert_pos = content.rfind(")")
content = content[:insert_pos] + gnd_zones + "\n" + content[insert_pos:]

with open(PCB_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"\n✅ 保存完了: {PCB_FILE}")
print("\n次のステップ:")
print("  kicad-cli pcb fill-zones で銅箔を充填してからDRCを実行")
