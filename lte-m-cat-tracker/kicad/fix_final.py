#!/usr/bin/env python3
"""
fix_final.py: 残り修正をまとめて適用
1. I2C_SCL × I2C_SDA crossing 解消
2. PROG/CC1/CC2/LED_ANODE 配線追加
3. C14/C15 フットプリント追加
4. ANT3移動（基板端クリアランス解消）
"""

import re, uuid, shutil

PCB = 'kicad/lte-m-cat-tracker.kicad_pcb'
shutil.copy(PCB, PCB + '.bak_fix_final')

with open(PCB) as f:
    content = f.read()

changes = []

def make_seg(x1, y1, x2, y2, width, layer, net):
    uid = str(uuid.uuid4())
    return f'\t(segment\n\t\t(start {x1} {y1})\n\t\t(end {x2} {y2})\n\t\t(width {width})\n\t\t(layer "{layer}")\n\t\t(net "{net}")\n\t\t(uuid "{uid}")\n\t)'

# 挿入先（最初のvia直前）
insert_mark = '\n\t(via'

# ======================================================
# 1. I2C crossing修正: SDA縦x=13.65をx=15.5に変更
# ======================================================
old_sda_horiz = '\t(segment\n\t\t(start 9.25 27)\n\t\t(end 13.65 27)\n\t\t(width 0.2)\n\t\t(layer "F.Cu")\n\t\t(net "I2C_SDA")'
old_sda_vert  = '\t(segment\n\t\t(start 13.65 27)\n\t\t(end 13.65 23.4)\n\t\t(width 0.2)\n\t\t(layer "F.Cu")\n\t\t(net "I2C_SDA")'

if old_sda_horiz in content:
    pat = re.escape(old_sda_horiz) + r'[^\)]*\)'
    content = re.sub(pat, make_seg(9.25,27,15.5,27,0.2,'F.Cu','I2C_SDA'), content, count=1)
    changes.append('SDA横 (9.25,27)→(15.5,27) に変更')
else:
    print('WARNING: SDA横セグメント not found')

if old_sda_vert in content:
    pat = re.escape(old_sda_vert) + r'[^\)]*\)'
    content = re.sub(pat, make_seg(15.5,27,15.5,23.4,0.2,'F.Cu','I2C_SDA'), content, count=1)
    changes.append('SDA縦 (15.5,27)→(15.5,23.4) に変更')
else:
    print('WARNING: SDA縦セグメント not found')

new_segs = [
    make_seg(15.5, 23.4, 13.65, 23.4, 0.2, 'F.Cu', 'I2C_SDA'),  # SDA接続補完
    # PROG
    make_seg(17.01, 24.5, 17.01, 21.865, 0.2, 'F.Cu', 'PROG'),
    make_seg(17.01, 21.865, 19.025, 21.865, 0.2, 'F.Cu', 'PROG'),
    # CC1
    make_seg(13.51, 30.2, 13.51, 30.8, 0.2, 'F.Cu', 'CC1'),
    make_seg(13.51, 30.8, 11.25, 30.8, 0.2, 'F.Cu', 'CC1'),
    # CC2
    make_seg(16.01, 29.8, 16.01, 34.2, 0.2, 'F.Cu', 'CC2'),
    make_seg(16.01, 34.2, 11.25, 34.2, 0.2, 'F.Cu', 'CC2'),
    # LED_ANODE
    make_seg(15.49, 26.3, 16.485, 26.3, 0.2, 'F.Cu', 'LED_ANODE'),
    make_seg(16.485, 26.3, 16.485, 27.5, 0.2, 'F.Cu', 'LED_ANODE'),
    # C14配線 (VBAT_SW)
    make_seg(24.35, 2.8, 24.35, 8.0, 0.3, 'F.Cu', 'VBAT_SW'),
    make_seg(24.35, 8.0, 25.02, 8.0, 0.3, 'F.Cu', 'VBAT_SW'),
    # C15配線 (VBAT_SW)
    make_seg(26.363, 21.05, 26.363, 21.5, 0.3, 'F.Cu', 'VBAT_SW'),
    make_seg(26.363, 21.5, 24.52, 21.5, 0.3, 'F.Cu', 'VBAT_SW'),
]

insert_all = '\n' + '\n'.join(new_segs)
content = content.replace(insert_mark, insert_all + insert_mark, 1)
changes.append('PROG/CC1/CC2/LED_ANODE/C14/C15配線追加 (13セグメント)')

# ======================================================
# C14/C15 フットプリント追加
# ======================================================
def make_cap_0402(ref, cx, cy, net_p1, net_p2, value='100nF', lcsc='C14663'):
    u = [str(uuid.uuid4()) for _ in range(10)]
    return f'''
\t(footprint ""
\t\t(layer "F.Cu")
\t\t(uuid "{u[0]}")
\t\t(at {cx} {cy})
\t\t(property "Reference" "{ref}"
\t\t\t(at 0 -3.5 0)
\t\t\t(layer "F.SilkS")
\t\t\t(uuid "{u[1]}")
\t\t\t(effects (font (size 0.8 0.8)(thickness 0.12)))
\t\t)
\t\t(property "Value" "{value}"
\t\t\t(at 0 3.5 0)
\t\t\t(layer "F.Fab")
\t\t\t(uuid "{u[2]}")
\t\t\t(effects (font (size 0.8 0.8)(thickness 0.12)))
\t\t)
\t\t(property "LCSC" "{lcsc}"
\t\t\t(at 0 0 0)
\t\t\t(layer "F.Fab")
\t\t\t(hide yes)
\t\t\t(uuid "{u[3]}")
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(duplicate_pad_numbers_are_jumpers no)
\t\t(fp_line (start -0.107836 -0.36)(end 0.107836 -0.36)
\t\t\t(stroke (width 0.12)(type solid))
\t\t\t(layer "F.SilkS")(uuid "{u[4]}")
\t\t)
\t\t(fp_line (start -0.107836 0.36)(end 0.107836 0.36)
\t\t\t(stroke (width 0.12)(type solid))
\t\t\t(layer "F.SilkS")(uuid "{u[5]}")
\t\t)
\t\t(fp_rect (start -0.91 -0.46)(end 0.91 0.46)
\t\t\t(stroke (width 0.05)(type solid))
\t\t\t(fill no)(layer "F.CrtYd")(uuid "{u[6]}")
\t\t)
\t\t(pad "1" smd rect
\t\t\t(at -0.48 0)
\t\t\t(size 0.56 0.62)
\t\t\t(layers "F.Cu" "F.Mask" "F.Paste")
\t\t\t(net "{net_p1}")
\t\t\t(thermal_bridge_angle 45)
\t\t\t(uuid "{u[7]}")
\t\t)
\t\t(pad "2" smd rect
\t\t\t(at 0.48 0)
\t\t\t(size 0.56 0.62)
\t\t\t(layers "F.Cu" "F.Mask" "F.Paste")
\t\t\t(net "{net_p2}")
\t\t\t(thermal_bridge_angle 45)
\t\t\t(uuid "{u[8]}")
\t\t)
\t\t(embedded_fonts no)
\t)'''

c14_fp = make_cap_0402('C14', 25.5, 8.0, 'VBAT_SW', 'GND')
c15_fp = make_cap_0402('C15', 25.0, 21.5, 'VBAT_SW', 'GND')

content = content.rstrip()
if content.endswith(')'):
    content = content[:-1] + c14_fp + '\n' + c15_fp + '\n)'
    changes.append('C14/C15フットプリント追加')

# ======================================================
# ANT3移動: (1.8,19) → (2.2,19)、パッド端x=0.9で端クリアランス確保
# ======================================================
content = content.replace('(at 1.8 19)\n', '(at 2.2 19)\n')
changes.append('ANT3 center (1.8,19)→(2.2,19) 移動')

# WIFI_ANT配線末端更新
old_wifi1 = '\t(segment\n\t\t(start 5.8 20.87)\n\t\t(end 0.5 20.87)\n\t\t(width 0.2)\n\t\t(layer "F.Cu")\n\t\t(net "WIFI_ANT")'
old_wifi2 = '\t(segment\n\t\t(start 0.5 20.87)\n\t\t(end 0.5 19)\n\t\t(width 0.2)\n\t\t(layer "F.Cu")\n\t\t(net "WIFI_ANT")'

if old_wifi1 in content:
    pat = re.escape(old_wifi1) + r'[^\)]*\)'
    content = re.sub(pat, make_seg(5.8,20.87,0.9,20.87,0.2,'F.Cu','WIFI_ANT'), content, count=1)
    changes.append('WIFI_ANT横セグメント end 0.5→0.9')
if old_wifi2 in content:
    pat = re.escape(old_wifi2) + r'[^\)]*\)'
    content = re.sub(pat, make_seg(0.9,20.87,0.9,19.0,0.2,'F.Cu','WIFI_ANT'), content, count=1)
    changes.append('WIFI_ANT縦セグメント 0.5→0.9')

with open(PCB, 'w') as f:
    f.write(content)

print(f'修正完了 ({len(changes)}件):')
for c in changes:
    print(f'  ✓ {c}')
