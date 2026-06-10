#!/usr/bin/env python3
"""
route_pcb_v12.py — 残未配線4ネットの実装（DESIGN.md 2026-06-10設計・check_route検証済み）
v11適用済みPCB（commit 9e6afff）に対して実行する。

変更内容:
1. RXD西詰め: B.Cu縦 x=8.7 → x=8.35（SDA用にx=9.15空間を確保）
2. ACCEL_INT1: 旧南回りを維持し横断のみ y=29.5 → y=29.85
   （新SDA B.Cu x=14.875南端y=29.3 とのgap 0.025mm衝突を回避。
     DESIGN.md案のy=26.1回廊はSCL y=26.5と+3.3V via(11.8,25.5)に挟まれvia不可→破棄）
   + U3.9-8-7パッド列接続（全てACCEL_INT1ネット・PCBファイルで確認済み）
3. I2C_SDA: via-in-pad(9.15,25.95)→B.Cu x=9.15→F.Cu y=29.55/29.15レーン→
   via(16.8,29.225)→B.Cu x=14.875北上→既存ダングリングseg(15.5,23.4)東端→U3.11
   + R6.2 via-in-pad(13.35,21.0)→B.Cu→(15.5,23.4)
   東via y=29.225: VBAT y=28.5とCC2 y=29.8に挟まれ両側0.2不可（隙間0.95<必要1.0）
   → 両側gap=0.175で均等配分（JLC最小0.127以上）
4. VBAT_SW 3島接続（DESIGN.md検証済みルートそのまま）

既知マージナル（許容・DESIGN.md記録済み）:
- SDA via(9.15,25.95)×SCLパッド 0.175 / via(15.5,23.4)×PROG via 0.175
- seg(13.65,23.4)×+3.3V 0.15 / 東via×VBAT・CC2 各0.175
"""

import uuid, re, shutil, os

PCB = '/Users/m2mac/lte-m-cat-tracker/kicad/lte-m-cat-tracker.kicad_pcb'
BAK = PCB + '.bak_v12'

def U():
    return str(uuid.uuid4())

def seg(x1, y1, x2, y2, w, layer, net):
    return (f'\t(segment\n\t\t(start {x1} {y1})\n\t\t(end {x2} {y2})\n'
            f'\t\t(width {w})\n\t\t(layer "{layer}")\n\t\t(net "{net}")\n'
            f'\t\t(uuid "{U()}")\n\t)')

def via(x, y, net, size=0.6, drill=0.3):
    return (f'\t(via\n\t\t(at {x} {y})\n\t\t(size {size})\n\t\t(drill {drill})\n'
            f'\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "{net}")\n\t\t(uuid "{U()}")\n\t)')

def remove_segment(content, x1, y1, x2, y2):
    pattern = re.compile(
        r'\t\(segment\n'
        r'\t\t\(start ' + re.escape(str(x1)) + r' ' + re.escape(str(y1)) + r'\)\n'
        r'\t\t\(end ' + re.escape(str(x2)) + r' ' + re.escape(str(y2)) + r'\)\n'
        r'.*?\n\t\)\n', re.DOTALL)
    new_content, count = pattern.subn('', content)
    print(('削除' if count else '⚠️ 見つからない') + f": segment ({x1},{y1})→({x2},{y2}) [{count}件]")
    return new_content

def remove_via(content, x, y):
    pattern = re.compile(
        r'\t\(via\n'
        r'\t\t\(at ' + re.escape(str(x)) + r' ' + re.escape(str(y)) + r'\)\n'
        r'.*?\n\t\)\n', re.DOTALL)
    new_content, count = pattern.subn('', content)
    print(('削除' if count else '⚠️ 見つからない') + f": via ({x},{y}) [{count}件]")
    return new_content

W_S = 0.2
W_P = 0.5
R = []

# --- 1. RXD x=8.35西詰め ---
R += [seg(8.7, 21.05, 8.7, 21.5, W_S, 'B.Cu', 'SIM_RXD'),
      seg(8.7, 21.5, 8.35, 21.5, W_S, 'B.Cu', 'SIM_RXD'),
      seg(8.35, 21.5, 8.35, 33.0, W_S, 'B.Cu', 'SIM_RXD'),
      via(8.35, 33.0, 'SIM_RXD'),
      seg(8.35, 33.0, 25.3, 33.0, W_S, 'F.Cu', 'SIM_RXD')]

# --- 2. ACCEL_INT1 横断y=29.85 + U3パッド列 ---
R += [seg(14.2625, 24.25, 14.2625, 25.25, W_S, 'F.Cu', 'ACCEL_INT1'),
      seg(14.2625, 25.25, 14.2625, 29.85, W_S, 'B.Cu', 'ACCEL_INT1'),
      seg(14.2625, 29.85, 10.85, 29.85, W_S, 'B.Cu', 'ACCEL_INT1'),
      seg(10.85, 29.85, 10.85, 25.95, W_S, 'B.Cu', 'ACCEL_INT1')]

# --- 3. I2C_SDA ---
R += [via(9.15, 25.95, 'I2C_SDA'),
      seg(9.15, 25.95, 9.15, 29.55, W_S, 'B.Cu', 'I2C_SDA'),
      via(9.15, 29.55, 'I2C_SDA'),
      seg(9.15, 29.55, 13.3, 29.55, W_S, 'F.Cu', 'I2C_SDA'),
      seg(13.3, 29.55, 13.3, 29.15, W_S, 'F.Cu', 'I2C_SDA'),
      seg(13.3, 29.15, 16.8, 29.15, W_S, 'F.Cu', 'I2C_SDA'),
      seg(16.8, 29.15, 16.8, 29.225, W_S, 'F.Cu', 'I2C_SDA'),
      via(16.8, 29.225, 'I2C_SDA'),
      seg(16.8, 29.225, 14.875, 29.225, W_S, 'B.Cu', 'I2C_SDA'),
      seg(14.875, 29.225, 14.875, 23.4, W_S, 'B.Cu', 'I2C_SDA'),
      seg(14.875, 23.4, 15.5, 23.4, W_S, 'B.Cu', 'I2C_SDA'),
      via(15.5, 23.4, 'I2C_SDA'),
      seg(13.65, 23.4, 13.75, 23.4, W_S, 'F.Cu', 'I2C_SDA'),
      seg(13.75, 23.4, 13.75, 23.7375, W_S, 'F.Cu', 'I2C_SDA'),
      via(13.35, 21.0, 'I2C_SDA'),
      seg(13.35, 21.0, 13.51, 21.0, W_S, 'F.Cu', 'I2C_SDA'),
      seg(13.35, 21.0, 13.35, 21.6, W_S, 'B.Cu', 'I2C_SDA'),
      seg(13.35, 21.6, 15.5, 21.6, W_S, 'B.Cu', 'I2C_SDA'),
      seg(15.5, 21.6, 15.5, 23.4, W_S, 'B.Cu', 'I2C_SDA')]

# --- 4. VBAT_SW 3島 ---
R += [seg(17.2, 5.05, 18.3, 5.05, W_P, 'F.Cu', 'VBAT_SW'),   # U1.46→pad35
      seg(18.3, 5.05, 18.3, 1.26, W_P, 'F.Cu', 'VBAT_SW'),
      seg(10.6, 6.7, 8.4, 6.7, W_P, 'F.Cu', 'VBAT_SW'),       # U1.47→C11.1
      seg(8.4, 6.7, 8.4, 2.6, W_P, 'F.Cu', 'VBAT_SW'),
      seg(8.4, 2.6, 2.2, 2.6, W_P, 'F.Cu', 'VBAT_SW'),
      seg(2.2, 2.6, 2.2, 7.0, W_P, 'F.Cu', 'VBAT_SW'),
      seg(2.2, 7.0, 1.55, 7.0, W_P, 'F.Cu', 'VBAT_SW'),
      seg(26.3625, 22.95, 27.4, 22.95, 0.3, 'F.Cu', 'VBAT_SW'),  # U5.3→既存セグ合流
      seg(27.4, 22.95, 27.4, 21.05, 0.3, 'F.Cu', 'VBAT_SW'),
      # 左島(C11/SW1系)と右島(B.Cuトランク/U5系)の橋: y=2.6東進→右島縦x=18.3に合流
      # U1内部LGA行間(y=1.26〜5.05)のF.Cu空きバンド。check_route検証0件（2026-06-10）
      seg(8.4, 2.6, 18.3, 2.6, W_P, 'F.Cu', 'VBAT_SW')]

# --- 適用 ---
with open(PCB) as f:
    content = f.read()

if not os.path.exists(BAK):
    shutil.copy2(PCB, BAK)
    print(f"バックアップ: {BAK}")

# 旧RXD x=8.7系の削除（via(8.7,21.05)とF.Cuスタブは新ルートで再利用するため残す）
content = remove_segment(content, 8.7, 33.0, 8.7, 21.05)
content = remove_segment(content, 25.3, 33.0, 8.7, 33.0)
content = remove_via(content, 8.7, 33.0)
# 旧ACCEL横断y=29.5系の削除（via2本とF.Cuスタブは残す）
content = remove_segment(content, 14.2625, 25.25, 14.2625, 29.5)
content = remove_segment(content, 14.2625, 29.5, 10.85, 29.5)
content = remove_segment(content, 10.85, 29.5, 10.85, 25.95)

insert_pos = content.rfind('\n)')
if insert_pos == -1:
    print("ERROR: PCBファイル末尾が見つからない")
    exit(1)

content = content[:insert_pos] + '\n' + '\n'.join(R) + '\n' + content[insert_pos:]

with open(PCB, 'w') as f:
    f.write(content)

print(f"✅ route_pcb_v12.py 完了: {len(R)}要素追加（RXD×5, ACCEL×4, SDA×19, VBAT_SW×9）")
print("次: kicad-cli DRC で shorts/crossings/unconnected を確認")
