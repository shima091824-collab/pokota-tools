#!/usr/bin/env python3
"""
I2C crossing 根本解決 v2

問題: I2C_SCL水平(9.75,26.5)→(15,26.5) F.Cu × I2C_SDA縦(13.65,27→23.4) F.Cu が交差

戦略: SCL水平をB.Cu経由でブリッジ（F.Cu→B.Cu→F.Cuのサンドイッチ）
  F.Cu SCL水平を削除 → via(9.75,26.5) + B.Cu水平 + via(15.0,26.5)

同時に: SDA縦をx=18.0から元のx=13.65に戻す（x=18.0はCHRGと交差するため）

手順:
  1. SDA x=18.0関連トレースを全削除（F.Cu水平, F.Cu縦, B.Cu水平, via×2）
  2. SDA元ルートx=13.65を復元
  3. SCL水平F.Cu削除 → B.Cu経由に変更
"""

import re, uuid

PCB_FILE = '/Users/m2mac/lte-m-cat-tracker/kicad/lte-m-cat-tracker.kicad_pcb'

with open(PCB_FILE) as f:
    content = f.read()

def U():
    return str(uuid.uuid4())

def new_seg(x1, y1, x2, y2, w, layer, net):
    return (f'\t(segment\n'
            f'\t\t(start {x1} {y1})\n'
            f'\t\t(end {x2} {y2})\n'
            f'\t\t(width {w})\n'
            f'\t\t(layer "{layer}")\n'
            f'\t\t(net "{net}")\n'
            f'\t\t(uuid "{U()}")\n'
            f'\t)\n')

def new_via(x, y, net, size=0.6, drill=0.3):
    return (f'\t(via\n'
            f'\t\t(at {x} {y})\n'
            f'\t\t(size {size})\n'
            f'\t\t(drill {drill})\n'
            f'\t\t(layers "F.Cu" "B.Cu")\n'
            f'\t\t(net "{net}")\n'
            f'\t\t(uuid "{U()}")\n'
            f'\t)\n')

def remove_segs(c, specs):
    """specs: list of (x1,y1,x2,y2,layer,net) tuples to remove"""
    removed = 0
    for x1,y1,x2,y2,layer,net in specs:
        pat = (r'\t\(segment\n'
               rf'\t\t\(start {re.escape(str(x1))} {re.escape(str(y1))}\)\n'
               rf'\t\t\(end {re.escape(str(x2))} {re.escape(str(y2))}\)\n'
               r'\t\t\(width [^)]+\)\n'
               rf'\t\t\(layer "{re.escape(layer)}"\)\n'
               rf'\t\t\(net "{re.escape(net)}"\)\n'
               r'(?:\t\t\(uuid "[^"]+"\)\n)?'
               r'\t\)\n')
        c, n = re.subn(pat, '', c)
        removed += n
    return c, removed

def remove_vias(c, coords_nets):
    """coords_nets: list of (x,y,net)"""
    removed = 0
    for x,y,net in coords_nets:
        pat = (r'\t\(via\n'
               rf'\t\t\(at {re.escape(str(x))} {re.escape(str(y))}\)\n'
               r'\t\t\(size [^)]+\)\n'
               r'\t\t\(drill [^)]+\)\n'
               r'\t\t\(layers "F\.Cu" "B\.Cu"\)\n'
               rf'\t\t\(net "{re.escape(net)}"\)\n'
               r'(?:\t\t\(uuid "[^"]+"\)\n)?'
               r'\t\)\n')
        c, n = re.subn(pat, '', c)
        removed += n
    return c, removed

print('=== STEP 1: SDA x=18.0 変更を全て削除 ===')

# 削除するSDAトレース（x=18.0経由の全ルート）
sda_segs_to_remove = [
    (9.25, 27, 18.0, 27, 'F.Cu', 'I2C_SDA'),   # SDA水平延長
    (18.0, 27, 18.0, 23.4, 'F.Cu', 'I2C_SDA'), # SDA縦x=18.0
    (18.0, 23.4, 13.75, 23.4, 'B.Cu', 'I2C_SDA'), # SDA B.Cu水平
    (13.75, 23.4, 13.75, 23.738, 'F.Cu', 'I2C_SDA'), # SDA F.Cu縦→U3
]
content, n = remove_segs(content, sda_segs_to_remove)
print(f'  SDAトレース削除: {n}件')

# 削除するvias（x=18.0, x=13.75 SDA）
sda_vias_to_remove = [
    (18.0, 23.4, 'I2C_SDA'),
    (13.75, 23.4, 'I2C_SDA'),
]
content, n = remove_vias(content, sda_vias_to_remove)
print(f'  SDA via削除: {n}件')

print('=== STEP 2: SDA元ルート(x=13.65)を復元 ===')
# 元ルート: (9.25,27)→(13.65,27)水平 + (13.65,27)→(13.65,23.4)縦 + (13.65,23.4)→(13.75,23.4)橋渡し
new_sda = (
    new_seg(9.25, 27, 13.65, 27, 0.2, 'F.Cu', 'I2C_SDA') +
    new_seg(13.65, 27, 13.65, 23.4, 0.2, 'F.Cu', 'I2C_SDA') +
    new_seg(13.65, 23.4, 13.75, 23.4, 0.2, 'F.Cu', 'I2C_SDA')
)
# 既存の (9.25,27)→... があるか確認
if '(start 9.25 27)' not in content or '(end 13.65 27)' not in content:
    first_seg = content.find('\t(segment\n')
    content = content[:first_seg] + new_sda + content[first_seg:]
    print('  SDA元ルート追加 ✅')
else:
    print('  SDA元ルート既存 skip')

print('=== STEP 3: SCL水平F.CuをB.Cu経由に変更 ===')
# 削除: SCL水平F.Cu (9.75,26.5)→(15,26.5)
scl_to_remove = [(9.75, 26.5, 15, 26.5, 'F.Cu', 'I2C_SCL')]
content, n = remove_segs(content, scl_to_remove)
print(f'  SCL F.Cu水平削除: {n}件')

# 追加: via(9.75,26.5) + B.Cu水平 + via(15,26.5)
new_scl = (
    new_via(9.75, 26.5, 'I2C_SCL') +
    new_seg(9.75, 26.5, 15, 26.5, 0.2, 'B.Cu', 'I2C_SCL') +
    new_via(15, 26.5, 'I2C_SCL')
)
first_seg = content.find('\t(segment\n')
content = content[:first_seg] + new_scl + content[first_seg:]
print('  SCL B.Cu経由追加 ✅')

with open(PCB_FILE, 'w') as f:
    f.write(content)
print('\nPCBファイル更新完了')
