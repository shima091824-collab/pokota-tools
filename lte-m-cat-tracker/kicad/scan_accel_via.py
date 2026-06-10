#!/usr/bin/env python3
"""残課題1: ACCEL_INT1 via位置の再探索。
候補ルート: U3.9(14.2625,24.25)→F.Cu縦→(14.2625,25.25)→B.Cu縦→y=H→B.Cu西→via(X,H)→F.Cu→U2.16(10.25,25.95)
+3.3V F.Cu枝 (11.8,25.5)→(10.95,25.5)→(10.95,25.25) を回避するviaの(X,H)を全探索する。
"""
import check_route as cr

items = cr.load(cr.PCB)
print(f"loaded {len(items)} items")

# 旧ACCEL要素（削除予定）は照合から除外: B.Cu x=14.2625/y=29.5/x=10.85, via(14.2625,25.25), via(10.85,25.95), F.Cuスタブ
def is_old_accel(it):
    if it[1] != 'ACCEL_INT1':
        return False
    return True  # ACCEL_INT1ネットの既存要素は全て差し替え対象なので除外

items = [it for it in items if not is_old_accel(it)]

results = []
for Xi in range(1060, 1200, 5):       # X = 10.60 .. 11.95
    X = Xi / 100
    for Hi in range(2580, 2680, 5):   # H = 25.80 .. 26.75
        H = Hi / 100
        cands = [
            ('seg', 'ACCEL_INT1', 'F.Cu', 14.2625, 24.25, 14.2625, 25.25, 0.2),
            ('via', 'ACCEL_INT1', 14.2625, 25.25),
            ('seg', 'ACCEL_INT1', 'B.Cu', 14.2625, 25.25, 14.2625, H, 0.15),
            ('seg', 'ACCEL_INT1', 'B.Cu', 14.2625, H, X, H, 0.15),
            ('via', 'ACCEL_INT1', X, H),
            ('seg', 'ACCEL_INT1', 'F.Cu', X, H, 10.25, 25.95, 0.2),
        ]
        bad = cr.check(cands, items, f'X={X},H={H}')
        # U2パッドはネット未割当(no-net)のDRC偽陽性 → U2.16(10.25,25.95)タッチのみ許容
        bad = [b for b in bad if 'U2.16' not in b]
        if not bad:
            results.append((X, H))

print(f"違反なし候補: {len(results)}件")
for X, H in results[:40]:
    print(f"  via({X},{H})")
