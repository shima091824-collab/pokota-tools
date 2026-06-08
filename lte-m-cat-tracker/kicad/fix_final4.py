#!/usr/bin/env python3
"""
fix_final4.py: 残り3件の短絡 + crossing修正
1. PROG経路変更（R7.pad1[+3.3V]回避）
2. CC2経路変更（J2.Sマウントパッド回避）
3. LED_ANODE経路変更（R4.pad2[CHRG]回避）
"""
import re, uuid, shutil

PCB = 'kicad/lte-m-cat-tracker.kicad_pcb'
shutil.copy(PCB, PCB + '.bak_fix_final4')
with open(PCB) as f:
    content = f.read()

changes = []

def make_seg(x1, y1, x2, y2, width, layer, net):
    uid = str(uuid.uuid4())
    return f'\t(segment\n\t\t(start {x1} {y1})\n\t\t(end {x2} {y2})\n\t\t(width {width})\n\t\t(layer "{layer}")\n\t\t(net "{net}")\n\t\t(uuid "{uid}")\n\t)'

def make_via(x, y, net, size=0.6, drill=0.3):
    uid = str(uuid.uuid4())
    return f'\t(via\n\t\t(at {x} {y})\n\t\t(size {size})\n\t\t(drill {drill})\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "{net}")\n\t\t(uuid "{uid}")\n\t)'

def remove_seg(content, x1, y1, x2, y2, net):
    for sx,sy,ex,ey in [(x1,y1,x2,y2),(x2,y2,x1,y1)]:
        s1 = f'{sx} {sy}' if float(sx)==int(float(sx)) else str(sx)
        s2 = f'{ex} {ey}' if float(ex)==int(float(ex)) else str(ex)
        # float→intの両方試す
        for fmt in [f'{float(sx):.2f}',f'{float(sx):.3f}',str(sx)]:
            for fmt2 in [f'{float(ex):.2f}',f'{float(ex):.3f}',str(ex)]:
                pass
        pat = (r'\t\(segment\n\t\t\(start ' +
               re.escape(f'{float(x1)} {float(y1)}').replace(r'\.0\ ',r'(.0)? ').replace(r'\.0\)',r'(.0)?') +
               r'\)\n\t\t\(end ' +
               re.escape(f'{float(x2)} {float(y2)}') +
               r'\)\n\t\t\(width [^\)]+\)\n\t\t\(layer "[^"]+"\)\n\t\t\(net "' +
               re.escape(net) + r'"\)\n\t\t\(uuid "[^"]+"\)\n\t\)')
        new = re.sub(pat, '', content)
        if new != content:
            return new
    # 文字列完全一致で試す
    for sx,sy,ex,ey in [(str(x1),str(y1),str(x2),str(y2)),(str(x2),str(y2),str(x1),str(y1))]:
        search = f'\t(segment\n\t\t(start {sx} {sy})\n\t\t(end {ex} {ey})'
        idx = content.find(search)
        if idx >= 0:
            end_idx = content.find('\n\t)', idx) + 3
            new = content[:idx] + content[end_idx:]
            if new != content:
                return new
    return content

def remove_via_at(content, x, y, net):
    search = f'\t(via\n\t\t(at {x} {y})\n'
    idx = content.find(search)
    if idx >= 0:
        end_idx = content.find('\n\t)', idx) + 3
        return content[:idx] + content[end_idx:]
    return content

insert_mark = '\n\t(via'

# ======================================================
# 1. PROG経路修正: x=14.8経由（R7.pad1を回避）
# 削除: (15.99,24.5)→(15.99,21.865) + (15.99,21.865)→(19.025,21.865)
# 追加: (15.99,24.5)→(14.8,24.5)→(14.8,22.2)→(19.025,22.2)→(19.025,21.865)
# ======================================================
c1 = remove_seg(content, 15.99, 24.5, 15.99, 21.865, 'PROG')
c2 = remove_seg(c1, 15.99, 21.865, 19.025, 21.865, 'PROG')
if c2 != content:
    content = c2
    changes.append('PROG旧経路削除')
else:
    print('WARNING: PROG旧経路削除失敗')

new_prog = [
    make_seg(15.99, 24.5, 14.8, 24.5, 0.2, 'F.Cu', 'PROG'),
    make_seg(14.8, 24.5, 14.8, 22.2, 0.2, 'F.Cu', 'PROG'),
    make_seg(14.8, 22.2, 19.025, 22.2, 0.2, 'F.Cu', 'PROG'),
    make_seg(19.025, 22.2, 19.025, 21.865, 0.2, 'F.Cu', 'PROG'),
]
content = content.replace(insert_mark, '\n' + '\n'.join(new_prog) + insert_mark, 1)
changes.append('PROG新経路追加 (x=14.8→y=22.2経由)')

# ======================================================
# 2. CC2経路修正: x=17.0経由（J2.Sマウントパッド右端x=16.7を回避）
# 削除: F.Cu縦(16.01,29.8)→(16.01,34.2) + via(16.01,34.2)
# 追加: 横(16.01,29.8)→(17.5,29.8) + via(17.5,29.8) + B.Cu縦→(17.5,34.2) + B.Cu横→(11.25,34.2) + via(11.25,34.2)
# ======================================================
c3 = remove_seg(content, 16.01, 29.8, 16.01, 34.2, 'CC2')
c4 = remove_via_at(c3, 16.01, 34.2, 'CC2')
if c4 != content:
    content = c4
    changes.append('CC2旧F.Cu縦+via削除')
else:
    print('WARNING: CC2旧配線削除失敗')

new_cc2 = [
    make_seg(16.01, 29.8, 17.5, 29.8, 0.2, 'F.Cu', 'CC2'),   # 横
    make_via(17.5, 29.8, 'CC2'),
    make_seg(17.5, 29.8, 17.5, 34.2, 0.2, 'B.Cu', 'CC2'),    # B.Cu縦（J2.Sはf.cuのみ）
    make_seg(17.5, 34.2, 11.25, 34.2, 0.2, 'B.Cu', 'CC2'),   # B.Cu横（既存と差し替え）
    make_via(11.25, 34.2, 'CC2'),
]
content = content.replace(insert_mark, '\n' + '\n'.join(new_cc2) + insert_mark, 1)
changes.append('CC2新経路追加 (x=17.5 B.Cu経由)')

# 既存のB.Cu横(16.01,34.2)→(11.25,34.2)も削除（重複回避）
content = remove_seg(content, 16.01, 34.2, 11.25, 34.2, 'CC2')

# ======================================================
# 3. LED_ANODE経路修正: x=17.5経由（R4.pad2[CHRG]を右側で回避）
# 削除: (16.485,25.8)→(16.485,27.5)縦
# 追加: (16.485,25.8)→(17.5,25.8)→(17.5,27.5)→(16.485,27.5)
# ======================================================
c5 = remove_seg(content, 16.485, 25.8, 16.485, 27.5, 'LED_ANODE')
if c5 != content:
    content = c5
    changes.append('LED_ANODE旧縦削除')
else:
    print('WARNING: LED_ANODE旧縦削除失敗')

new_led = [
    make_seg(16.485, 25.8, 17.5, 25.8, 0.2, 'F.Cu', 'LED_ANODE'),
    make_seg(17.5, 25.8, 17.5, 27.5, 0.2, 'F.Cu', 'LED_ANODE'),
    make_seg(17.5, 27.5, 16.485, 27.5, 0.2, 'F.Cu', 'LED_ANODE'),
]
content = content.replace(insert_mark, '\n' + '\n'.join(new_led) + insert_mark, 1)
changes.append('LED_ANODE新経路追加 (x=17.5経由)')

with open(PCB, 'w') as f:
    f.write(content)

print(f'修正完了 ({len(changes)}件):')
for c in changes:
    print(f'  ✓ {c}')
