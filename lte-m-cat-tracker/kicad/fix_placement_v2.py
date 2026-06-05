#!/usr/bin/env python3
"""
LTE-M Cat Tracker PCB: 配置修正v2 + F.Cu GNDゾーン追加
- C5: y=19.0 → y=19.8  (U1 pad26との0mm重複解消、U2コートヤードクリア)
- C6: y=19.0 → y=19.8  (U1 pad27との0mm重複解消)
- R5: y=19.5 → y=19.8  (U1 pad28との0.03mm違反解消)
- C4: 移動なし (元々DRC違反なし)
- GND F.Cu ゾーン: 新規追加 (B.Cuは既存)
"""
import re, uuid, shutil

PCB_FILE = "/Users/m2mac/lte-m-cat-tracker/kicad/lte-m-cat-tracker.kicad_pcb"

shutil.copy2(PCB_FILE, PCB_FILE + ".bak_v1")
print("バックアップ完了")

with open(PCB_FILE, encoding="utf-8") as f:
    content = f.read()

# ── 部品移動 ──────────────────────────────────────────────────────────────
def find_and_move(text, ref, old_x, old_y, new_x, new_y):
    idx = text.find(f'(property "Reference" "{ref}"')
    if idx < 0:
        print(f"  {ref}: 見つからない")
        return text
    block_start = text.rfind("(footprint", 0, idx)
    block_end = text.find("\n\t(footprint", block_start + 50)
    if block_end < 0:
        block_end = len(text)
    block = text[block_start:block_end]

    # "(at X.XXXX Y.XXXX" または "(at X.XXXX Y.XXXX ROT" を置換
    old_at = f"(at {old_x:.4f} {old_y:.4f}"
    new_at = f"(at {new_x:.4f} {new_y:.4f}"
    if old_at in block:
        new_block = block.replace(old_at, new_at, 1)
        print(f"  {ref}: ({old_x}, {old_y}) → ({new_x}, {new_y}) ✓")
        return text[:block_start] + new_block + text[block_end:]
    else:
        print(f"  {ref}: '{old_at}' が見つからない (変更なし)")
        return text

print("\n■ 配置修正:")
content = find_and_move(content, "C5", 8.5,  19.0, 8.5,  19.8)
content = find_and_move(content, "C6", 10.5, 19.0, 10.5, 19.8)
content = find_and_move(content, "R5", 13.0, 19.5, 13.0, 19.8)

# ── F.Cu GND ゾーン追加 ───────────────────────────────────────────────────
# B.Cuのゾーンはすでに存在するため F.Cuのみ追加
# ボード境界: (0,0)〜(30,35) マージン0.25mm
ZX1, ZY1 = 0.25, 0.25
ZX2, ZY2 = 29.75, 34.75

gnd_zone_fcu = f"""
\t(zone
\t\t(net 21)
\t\t(net_name "GND")
\t\t(layer "F.Cu")
\t\t(uuid "{uuid.uuid4()}")
\t\t(hatch edge 0.508)
\t\t(connect_pads (clearance 0.2))
\t\t(min_thickness 0.2)
\t\t(filled_areas_thickness no)
\t\t(fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3))
\t\t(polygon
\t\t\t(pts
\t\t\t\t(xy {ZX1} {ZY1}) (xy {ZX2} {ZY1}) (xy {ZX2} {ZY2}) (xy {ZX1} {ZY2})
\t\t\t)
\t\t)
\t)"""

# ファイル末尾の ) の直前に挿入
last_paren = content.rfind(")")
content = content[:last_paren] + gnd_zone_fcu + "\n" + content[last_paren:]
print("\n■ F.Cu GNDゾーン追加 ✓")

with open(PCB_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"\n✅ 保存完了: {PCB_FILE}")
