#!/usr/bin/env python3
"""GNDステッチング: 孤立GNDパッドにvia/スタブを追加（check_route検証済み座標・2026-06-10）。
適用後に add_gnd_zones 同様の refill が必要（refill_zones.py）。
"""
import uuid, re, shutil, os

PCB = '/Users/m2mac/lte-m-cat-tracker/kicad/lte-m-cat-tracker.kicad_pcb'

def U():
    return str(uuid.uuid4())

def seg(x1, y1, x2, y2, w, layer, net):
    return (f'\t(segment\n\t\t(start {x1} {y1})\n\t\t(end {x2} {y2})\n'
            f'\t\t(width {w})\n\t\t(layer "{layer}")\n\t\t(net "{net}")\n'
            f'\t\t(uuid "{U()}")\n\t)')

def via(x, y, net, size=0.6, drill=0.3):
    return (f'\t(via\n\t\t(at {x} {y})\n\t\t(size {size})\n\t\t(drill {drill})\n'
            f'\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "{net}")\n\t\t(uuid "{U()}")\n\t)')

W = 0.2
G = 'GND'
R = []

# via+スタブ（オフセットvia）
R += [seg(10.98, 19.8, 10.73, 19.8, W, 'F.Cu', G),   # C6.2
      seg(10.73, 19.8, 10.73, 19.2, W, 'F.Cu', G),
      via(10.73, 19.2, G)]
R += [seg(12.49, 30.2, 12.49, 31.25, W, 'F.Cu', G),   # R1.1
      via(12.49, 31.25, G)]
R += [seg(12.45, 28.5, 11.95, 28.5, W, 'F.Cu', G),    # C9.2
      via(11.95, 28.5, G)]
R += [seg(17.01, 24.5, 16.86, 24.5, W, 'F.Cu', G),    # R3.2
      seg(16.86, 24.5, 16.86, 23.4, W, 'F.Cu', G),
      via(16.86, 23.4, G)]
# LED1.1: 周囲密集でオフセット不可 → via-in-pad（0402・v1試作で許容）
R += [via(15.515, 27.5, G)]
# スタブのみ（隣接ベタポケットへ接続・ゾーン再充填で導通）
R += [seg(26.3625, 22.0, 25.7, 22.0, W, 'F.Cu', G)]       # U5.2 西
R += [seg(12.7375, 23.75, 12.2, 23.75, W, 'F.Cu', G)]     # U3.1 西
R += [seg(14.2625, 23.75, 14.95, 23.75, W, 'F.Cu', G)]    # U3.10 東（SDA y=23.4とgap0.15マージナル）
R += [seg(13.75, 25.2625, 13.75, 25.9, W, 'F.Cu', G)]     # U3.6 南（ACCEL via gap0.113・既存0.025箇所）

with open(PCB) as f:
    content = f.read()

BAK = PCB + '.bak_pre_stitch'
if not os.path.exists(BAK):
    shutil.copy2(PCB, BAK)
    print(f"バックアップ: {BAK}")

insert_pos = content.rfind('\n)')
content = content[:insert_pos] + '\n' + '\n'.join(R) + '\n' + content[insert_pos:]
with open(PCB, 'w') as f:
    f.write(content)
print(f"✅ GNDステッチング {len(R)}要素追加（via×5, seg×11）")
