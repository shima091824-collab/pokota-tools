#!/usr/bin/env python3
"""v12実装前の一括検証。
- RXD: x=8.7縦→x=8.35縦に西詰め（SDA x=9.15用の空間確保）
- ACCEL_INT1: 旧南回り維持・横断のみ y=29.5→29.85（新SDA x=14.875 南端y=29.3との衝突回避）
- I2C_SDA: DESIGN.md確定ルート + via(16.8,29.3)→(16.8,29.25)微調整（CC2 y=29.8回避）
- VBAT_SW 3島: DESIGN.md検証済みルート
除外（削除予定の既存要素）: RXD x=8.7系, ACCEL横断y=29.5系
"""
import math
import check_route as cr

items = cr.load(cr.PCB)
print(f"loaded {len(items)} items")


def removed(it):
    kind, net = it[0], it[1]
    if net == 'SIM_RXD' and kind == 'seg':
        x1, y1, x2, y2 = it[3], it[4], it[5], it[6]
        # 旧: (8.7,21.05)-(8.7,33.0)B.Cu, (25.3,33.0)-(8.7,33.0)F.Cu, (8.7,21.05)-(8.75,21.05)F.Cu
        if abs(x1 - 8.7) < 0.01 or abs(x2 - 8.7) < 0.01:
            return True
    if net == 'SIM_RXD' and kind == 'via':
        if abs(it[3] - 8.7) < 0.01:  # via(8.7,33.0), via(8.7,21.05)
            return True
    if net == 'ACCEL_INT1' and kind == 'seg':
        y1, y2 = it[4], it[6]
        if abs(y1 - 29.5) < 0.01 or abs(y2 - 29.5) < 0.01:  # 横断と両縦の南半分
            return True
    return False


kept = [it for it in items if not removed(it)]
print(f"除外 {len(items)-len(kept)} 要素")

S, V = 'seg', 'via'
W = 0.2
cands = []

# --- RXD差し替え（x=8.35縦） ---
cands += [
    (S, 'SIM_RXD', 'B.Cu', 8.7, 21.05, 8.7, 21.5, W),
    (S, 'SIM_RXD', 'B.Cu', 8.7, 21.5, 8.35, 21.5, W),
    (S, 'SIM_RXD', 'B.Cu', 8.35, 21.5, 8.35, 33.0, W),
    (V, 'SIM_RXD', 8.35, 33.0),
    (S, 'SIM_RXD', 'F.Cu', 8.35, 33.0, 25.3, 33.0, W),
    (V, 'SIM_RXD', 8.7, 21.05),
    (S, 'SIM_RXD', 'F.Cu', 8.7, 21.05, 8.75, 21.05, W),
]

# --- ACCEL_INT1: 旧南回り・横断y=29.85 ---
cands += [
    (S, 'ACCEL_INT1', 'B.Cu', 14.2625, 25.25, 14.2625, 29.85, W),
    (S, 'ACCEL_INT1', 'B.Cu', 14.2625, 29.85, 10.85, 29.85, W),
    (S, 'ACCEL_INT1', 'B.Cu', 10.85, 29.85, 10.85, 25.95, W),
]

# --- I2C_SDA（DESIGN.md確定ルート・via(16.8,29.25)に微調整） ---
cands += [
    (V, 'I2C_SDA', 9.15, 25.95),
    (S, 'I2C_SDA', 'B.Cu', 9.15, 25.95, 9.15, 29.55, W),
    (V, 'I2C_SDA', 9.15, 29.55),
    (S, 'I2C_SDA', 'F.Cu', 9.15, 29.55, 13.3, 29.55, W),
    (S, 'I2C_SDA', 'F.Cu', 13.3, 29.55, 13.3, 29.15, W),
    (S, 'I2C_SDA', 'F.Cu', 13.3, 29.15, 16.8, 29.15, W),
    (S, 'I2C_SDA', 'F.Cu', 16.8, 29.15, 16.8, 29.25, W),
    (V, 'I2C_SDA', 16.8, 29.25),
    (S, 'I2C_SDA', 'B.Cu', 16.8, 29.25, 14.875, 29.25, W),
    (S, 'I2C_SDA', 'B.Cu', 14.875, 29.25, 14.875, 23.4, W),
    (S, 'I2C_SDA', 'B.Cu', 14.875, 23.4, 15.5, 23.4, W),
    (V, 'I2C_SDA', 15.5, 23.4),
    (S, 'I2C_SDA', 'F.Cu', 13.65, 23.4, 13.75, 23.4, W),
    (S, 'I2C_SDA', 'F.Cu', 13.75, 23.4, 13.75, 23.7375, W),
    (V, 'I2C_SDA', 13.35, 21.0),
    (S, 'I2C_SDA', 'F.Cu', 13.35, 21.0, 13.51, 21.0, W),
    (S, 'I2C_SDA', 'B.Cu', 13.35, 21.0, 13.35, 21.6, W),
    (S, 'I2C_SDA', 'B.Cu', 13.35, 21.6, 15.5, 21.6, W),
    (S, 'I2C_SDA', 'B.Cu', 15.5, 21.6, 15.5, 23.4, W),
]

# --- VBAT_SW 3島 ---
cands += [
    (S, 'VBAT_SW', 'F.Cu', 17.2, 5.05, 18.3, 5.05, 0.5),
    (S, 'VBAT_SW', 'F.Cu', 18.3, 5.05, 18.3, 1.26, 0.5),
    (S, 'VBAT_SW', 'F.Cu', 10.6, 6.7, 8.4, 6.7, 0.5),
    (S, 'VBAT_SW', 'F.Cu', 8.4, 6.7, 8.4, 2.6, 0.5),
    (S, 'VBAT_SW', 'F.Cu', 8.4, 2.6, 2.2, 2.6, 0.5),
    (S, 'VBAT_SW', 'F.Cu', 2.2, 2.6, 2.2, 7.0, 0.5),
    (S, 'VBAT_SW', 'F.Cu', 2.2, 7.0, 1.55, 7.0, 0.5),
    (S, 'VBAT_SW', 'F.Cu', 26.3625, 22.95, 27.4, 22.95, 0.3),
    (S, 'VBAT_SW', 'F.Cu', 27.4, 22.95, 27.4, 21.05, 0.3),
]

bad = cr.check(cands, kept, 'v12')
print(f"\n違反 {len(bad)} 件:")
for b in sorted(set(bad)):
    print(' ', b)
