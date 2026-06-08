#!/usr/bin/env python3
"""
ドリル径修正 BLOCK-9 対応
全ビアのdrill < 0.3mmをdrill=0.3mmに拡大 → JLCPCB Standard PCB対応
- drill=0.25mm size=0.5mm × 13個 → drill=0.3mm size=0.5mm（annular 0.10mm ✅）
- drill=0.2mm  size=0.4mm × 7個  → drill=0.3mm size=0.4mm（annular 0.05mm ✅）
- drill=0.15mm size=0.3mm × 2個  → drill=0.3mm size=0.4mm（annular 0.05mm ✅, size拡大）
"""

import re

PCB_PATH = "/Users/m2mac/lte-m-cat-tracker/kicad/lte-m-cat-tracker.kicad_pcb"

with open(PCB_PATH) as f:
    content = f.read()

count = {"0.15": 0, "0.2": 0, "0.25": 0}

def fix_via(m):
    at_x, at_y, size, drill = m.group(1), m.group(2), m.group(3), m.group(4)
    d = float(drill)
    if d >= 0.3:
        return m.group(0)  # 変更不要

    new_drill = "0.3"
    s = float(size)
    # annular_ring = (size - drill) / 2 ≥ 0.05mm → size ≥ drill + 0.1 = 0.4mm
    new_size = f"{max(s, 0.4):.1f}"
    count[drill] += 1
    return f"(via\n\t\t(at {at_x} {at_y})\n\t\t(size {new_size})\n\t\t(drill {new_drill})"

pattern = r'\(via\s*\(at\s*([-\d.]+)\s+([-\d.]+)\)\s*\(size\s*([\d.]+)\)\s*\(drill\s*([\d.]+)\)'
new_content = re.sub(pattern, fix_via, content)

total = sum(count.values())
print(f"✅ ドリル拡大: {total}件")
for d, n in sorted(count.items()):
    if n > 0:
        new_s = "0.4" if float(d) <= 0.2 else "0.5"
        print(f"  drill={d}mm → 0.3mm, size→{new_s}mm × {n}個")

# 確認: 残存する < 0.3mm ドリル
remaining = re.findall(r'\(drill\s+(0\.[12]\d*)\)', new_content)
if remaining:
    print(f"⚠️ まだ残存: {remaining}")
else:
    print("✅ drill < 0.3mm: 0件")

with open(PCB_PATH, 'w') as f:
    f.write(new_content)

print("\n✅ PCBファイル書き込み完了")
print("BLOCK-9: JLCPCB Standard PCB（$2〜5）で発注可能")
