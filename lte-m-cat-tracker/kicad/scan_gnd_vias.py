#!/usr/bin/env python3
"""孤立GNDパッドごとにステッチングvia位置をグリッド探索する。
候補 = via(GND) + 必要ならパッド→viaのF.Cuスタブ(w0.2)。
check_routeで全銅要素（GND以外）との clearance>=0.2 を確認。ゾーンは充填し直すので無視してよい。
"""
import math
import check_route as cr

items = [it for it in cr.load(cr.PCB) if it[1] != 'GND']
print(f"非GND要素 {len(items)}")

targets = [
    ('C2.2',  4.68, 23.5),
    ('C6.2',  10.98, 19.8),
    ('R1.1',  12.49, 30.2),
    ('C9.2',  12.45, 28.5),
    ('U3.1',  12.7375, 23.75),
    ('U3.6',  13.75, 25.2625),
    ('U3.10', 14.2625, 23.75),
    ('C7.2',  13.08, 22.0),
    ('LED1.1',15.515, 27.5),
    ('U1.37', 16.1, 1.26),
    ('U1.36', 17.2, 1.26),
    ('R3.2',  17.01, 24.5),
    ('U4.3',  19.025, 23.135),
    ('U5.2',  26.3625, 22.0),
]

EDGE = 0.45  # 基板端から最低限離す(via半径0.3+0.15)

for name, px, py in targets:
    found = None
    # 距離順の候補グリッド（0.05mm步, 半径1.6mmまで）
    cands_pos = []
    for dxi in range(-32, 33):
        for dyi in range(-32, 33):
            dx, dy = dxi*0.05, dyi*0.05
            r = math.hypot(dx, dy)
            if r <= 1.6:
                cands_pos.append((r, round(px+dx, 3), round(py+dy, 3)))
    cands_pos.sort()
    for r, vx, vy in cands_pos:
        if not (EDGE <= vx <= 30-EDGE and EDGE <= vy <= 35-EDGE):
            continue
        c = [('via', 'GND', vx, vy)]
        if r > 0.01:
            c.append(('seg', 'GND', 'F.Cu', px, py, vx, vy, 0.2))
        if not cr.check(c, items):
            found = (vx, vy, r)
            break
    if found:
        print(f"{name} pad({px},{py}) → via({found[0]},{found[1]}) dist={found[2]:.2f}")
    else:
        print(f"{name} pad({px},{py}) → ❌ 候補なし（半径1.6mm内）")
