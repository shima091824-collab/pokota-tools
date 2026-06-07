"""
GNDビア位置修正:
- (9.8,18.5) → U1.pad27[no net](10.33,18.4)に接触 → 削除
- (15.5,26.5) → R4.pad1[no net](15.49,26.3)に接触 → 削除  
- (20.0,20.5) → U4.pad1[no net](19.025,20.595)に接触 → 削除
- (25.5,11.5) → 問題なし → 維持

新しい安全位置:
- C5/C6 GND用: (4.0,18.5) - U1左端(x=5.65)の外側・C1より上
- U3/LED1 GND用: (17.5,27.5) - SCL/SDA/VBAT配線を避けた場所
- R3/U4 GND用: (19.5,23.5) - U4中央付近の空き空間
"""
import re, uuid

PCB = "kicad/lte-m-cat-tracker.kicad_pcb"

with open(PCB) as f:
    data = f.read()

# 干渉するGNDビア3本を削除
for bad_via in ['9.8 18.5', '15.5 26.5', '20.0 20.5']:
    x, y = bad_via.split()
    pattern = rf'\t\(via \(at {re.escape(x)} {re.escape(y)}\)[^\)]*\(layers "F\.Cu" "B\.Cu"\) \(net "GND"\) \(uuid "[^"]+"\)\)\n'
    data = re.sub(pattern, '', data)

# 安全な位置に新GNDビア追加
new_vias = ""
safe_positions = [
    (4.0, 18.5),   # U1左外側・上方（C5/C6 GND連結用）
    (17.5, 27.5),  # LED1右側空きスペース（U3/LED1 GND用）
    (19.5, 23.5),  # U4 thermal pad付近空きスペース（R3 GND用）
]
for x, y in safe_positions:
    new_vias += f'\t(via (at {x} {y}) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net "GND") (uuid "{uuid.uuid4()}"))\n'

# ファイル末尾に追加
insert_pos = data.rfind('\n)')
data = data[:insert_pos] + "\n" + new_vias + data[insert_pos:]

with open(PCB, 'w') as f:
    f.write(data)

print("GNDビア位置修正完了")
for x, y in safe_positions:
    print(f"  追加: GNDビア ({x},{y})")
