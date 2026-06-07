"""
VBAT_SW断線修正: F.Cu (1,28.5)→(2,28.5) セグメント追加
via(1,28.5)[VBAT_SW]とSW1.pad2からのF.Cu配線を接続する
"""
import uuid

PCB = "kicad/lte-m-cat-tracker.kicad_pcb"

with open(PCB) as f:
    data = f.read()

# 追加するセグメント
new_seg = f'\t(segment (start 1 28.5) (end 2 28.5) (width 0.5) (layer "F.Cu") (net "VBAT_SW") (uuid "{uuid.uuid4()}"))\n'

# GNDビア追加（GNDゾーン孤島解消用）
gnd_vias = ""
# C5.pad2[GND](8.98,19.8)付近にGNDビア → F.CuとB.CuのGNDゾーンを接続
# U3付近にGNDビア → LIS2DW12のGNDを接続
# 注意: 既存配線との干渉を避けた位置を選ぶ
# C5/C6エリア: x=9.8,y=18.5（ルーティング回避済みエリア）
# U3エリア: x=15.5,y=24.5（R3 pad2付近だが少し離す）

gnd_via_positions = [
    (9.8, 18.5),    # C5/C6 GND用
    (15.5, 26.5),   # U3/LED1 GND用  
    (20.0, 20.5),   # R3/U4 GND用
    (25.5, 11.5),   # U1.pad77 GND用（右上エリア）
]

for x, y in gnd_via_positions:
    gnd_vias += f'\t(via (at {x} {y}) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net "GND") (uuid "{uuid.uuid4()}"))\n'

# PCBファイルの (board_setup ... より前の末尾に追加
insert_pos = data.rfind('\n)', )
data = data[:insert_pos] + "\n" + new_seg + gnd_vias + data[insert_pos:]

with open(PCB, 'w') as f:
    f.write(data)

print("修正完了:")
print(f"  追加: VBAT_SW F.Cu segment (1,28.5)→(2,28.5)")
print(f"  追加: GNDビア {len(gnd_via_positions)}本")
