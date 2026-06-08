#!/usr/bin/env python3
"""
Dangling via 2件を削除してDRC違反を解消する

対象:
  1. VBAT via at (17.5, 27.5) - F.Cu両側にトレースがあり不要なビア
  2. VBAT_SW via at (27.5, 1.0) - B.Cu幹線の角にあり F.Cu側接続なし
"""

import re

PCB_FILE = '/Users/m2mac/lte-m-cat-tracker/kicad/lte-m-cat-tracker.kicad_pcb'

with open(PCB_FILE) as f:
    content = f.read()

original_len = len(content)

# via ブロック全体にマッチするパターン
# 形式:
# \t(via
# \t\t(at X Y)
# \t\t(size ...)
# \t\t(drill ...)
# \t\t(layers "F.Cu" "B.Cu")
# \t\t(net "NETNAME")
# \t\t(uuid "...")
# \t)

def remove_via(text, x, y, net):
    # at座標とnetが一致するviaブロックを1件削除
    pattern = (
        r'\t\(via\n'
        r'\t\t\(at ' + re.escape(str(x)) + r' ' + re.escape(str(y)) + r'\)\n'
        r'\t\t\(size [^\)]+\)\n'
        r'\t\t\(drill [^\)]+\)\n'
        r'\t\t\(layers "F\.Cu" "B\.Cu"\)\n'
        r'\t\t\(net "' + re.escape(net) + r'"\)\n'
        r'(?:\t\t\(uuid "[^"]+"\)\n)?'
        r'\t\)\n'
    )
    new_text, count = re.subn(pattern, '', text, count=1)
    return new_text, count

# 1. VBAT via (17.5, 27.5)
content, n1 = remove_via(content, 17.5, 27.5, 'VBAT')
print(f'VBAT via (17.5,27.5): {"削除済み ✅" if n1 else "見つからず ❌"}')

# 2. VBAT_SW via (27.5, 1) - KiCad saves integer as "1" not "1.0"
content, n2 = remove_via(content, 27.5, 1, 'VBAT_SW')
print(f'VBAT_SW via (27.5,1.0): {"削除済み ✅" if n2 else "見つからず ❌"}')

if n1 or n2:
    with open(PCB_FILE, 'w') as f:
        f.write(content)
    print(f'\nPCBファイル更新完了 ({original_len}→{len(content)} chars, -{original_len-len(content)})')
else:
    print('\nPCBファイル変更なし')
