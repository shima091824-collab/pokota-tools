#!/usr/bin/env python3
"""
fix_final2.py: パッドnet属性更新 + 正しい配線で全問題を解消
"""
import re, uuid, shutil

PCB = 'kicad/lte-m-cat-tracker.kicad_pcb'
shutil.copy(PCB, PCB + '.bak_fix_final2')
with open(PCB) as f:
    content = f.read()

changes = []

# ======================================================
# 1. パッドのnet属性追加（(thermal_bridge_angle 45) の後に挿入）
# ======================================================
pad_nets = {
    '22970d70-e5ab-4f33-ae94-38333e4b8f0a': 'PROG',       # R3.pad1
    '45168902-1e7f-4e34-a438-e4b7b1993849': 'PROG',       # U4.pad2
    '250a5c5e-3629-4cc0-a8bb-2fecc84dac10': 'CC1',        # R1.pad2
    '26c5cae5-d8af-4be5-87b5-156d0f131903': 'CC1',        # J2.A5
    'aa39630e-df85-47ac-b121-5d1dc31a9353': 'CC2',        # R2.pad2
    'dd1a113b-3d36-41f7-b4f6-7b838eec50c2': 'CC2',        # J2.B5
    '8006a722-4385-4a84-b2bd-7b4e67f65d69': 'LED_ANODE',  # R4.pad1
    'c5641ceb-f0e3-4d73-addc-c663e60fb2f9': 'LED_ANODE',  # LED1.pad2
}

for uid, net in pad_nets.items():
    # (thermal_bridge_angle 45)\n\t\t\t(uuid "UID") パターンを探して netを挿入
    pattern = r'(\(thermal_bridge_angle 45\)\n\t\t\t\(uuid "' + re.escape(uid) + r'"\))'
    replacement = f'(thermal_bridge_angle 45)\n\t\t\t(net "{net}")\n\t\t\t(uuid "{uid}")'
    new_content = re.sub(pattern, replacement, content)
    if new_content != content:
        content = new_content
        changes.append(f'pad uuid={uid[:8]}... → net="{net}"')
    else:
        # thermal_bridge_angleなしのパターン試行
        pattern2 = r'(\(layers[^\n]+\)\n\t+\(thermal_bridge_angle 45\)\n\t+\(uuid "' + re.escape(uid) + r'"\))'
        new_content2 = re.sub(pattern2,
            lambda m: m.group(0).replace(f'(uuid "{uid}")', f'(net "{net}")\n\t\t\t(uuid "{uid}")'),
            content)
        if new_content2 != content:
            content = new_content2
            changes.append(f'pad uuid={uid[:8]}... → net="{net}" (pattern2)')
        else:
            print(f'WARNING: パッドnet更新失敗 uuid={uid[:8]} net={net}')

# ======================================================
# 2. 配線追加
# ======================================================
def make_seg(x1, y1, x2, y2, width, layer, net):
    uid = str(uuid.uuid4())
    return f'\t(segment\n\t\t(start {x1} {y1})\n\t\t(end {x2} {y2})\n\t\t(width {width})\n\t\t(layer "{layer}")\n\t\t(net "{net}")\n\t\t(uuid "{uid}")\n\t)'

insert_mark = '\n\t(via'

new_segs = []

# PROG: R3.pad1(15.99,24.5) → U4.pad2(19.025,21.865)
# 経路: 縦(x=15.99) → 横(y=21.865)
# ※U4.pad3[GND](19.025,23.135)を縦線が通過しないよう、x=15.99で迂回
new_segs += [
    make_seg(15.99, 24.5, 15.99, 21.865, 0.2, 'F.Cu', 'PROG'),
    make_seg(15.99, 21.865, 19.025, 21.865, 0.2, 'F.Cu', 'PROG'),
]

# CC1: R1.pad2(13.51,30.2) → J2.A5(11.25,30.8)
# J2パッドはy=30.8の横一列なので横線は禁止。縦アクセスのみ。
# 経路: R1.pad2(13.51,30.2) → 左横y=30.2 → 縦x=11.25 → J2.A5(11.25,30.8)
new_segs += [
    make_seg(13.51, 30.2, 11.25, 30.2, 0.2, 'F.Cu', 'CC1'),
    make_seg(11.25, 30.2, 11.25, 30.8, 0.2, 'F.Cu', 'CC1'),
]

# CC2: R2.pad2(16.01,29.8) → J2.B5(11.25,34.2)
# J2.B列パッドはy=34.2の横一列。J2.S(15.5,34.1)もある。
# 経路: R2.pad2(16.01,29.8) → 左横y=29.8 → 縦x=11.25 → J2.B5(11.25,34.2)
# J2.S(15.5,34.1)はJ2の下外側パッド。縦線x=11.25はJ2.S x=15.5と4.25mm離れ→OK
new_segs += [
    make_seg(16.01, 29.8, 11.25, 29.8, 0.2, 'F.Cu', 'CC2'),
    make_seg(11.25, 29.8, 11.25, 34.2, 0.2, 'F.Cu', 'CC2'),
]

# LED_ANODE: R4.pad1(15.49,26.3) → LED1.pad2(16.485,27.5)
# CHRG横線y=26.3があるので、横線を使わず縦線のみで接続
# 経路: R4.pad1(15.49,26.3) → 縦x=15.49 → (15.49,27.5) → 横→ LED1.pad2(16.485,27.5)
new_segs += [
    make_seg(15.49, 26.3, 15.49, 27.5, 0.2, 'F.Cu', 'LED_ANODE'),
    make_seg(15.49, 27.5, 16.485, 27.5, 0.2, 'F.Cu', 'LED_ANODE'),
]

# I2C crossing修正: SDA縦 x=13.65 → x=15.5 に迂回
# (詳細は変更のため後述)

# C14配線 (VBAT_SW): U1.pad4(24.35,8.2) → C14.pad1(25.02,8.0)
# U1.pad1-4はVBAT_SW端子(x=24.35, y=2.8/4.6/6.4/8.2)
# C14を(25.5,8.0)に配置するので pad1=(25.02,8.0)
new_segs += [
    make_seg(24.35, 8.2, 25.02, 8.0, 0.3, 'F.Cu', 'VBAT_SW'),
]

# C15配線 (VBAT_SW): U5.pad1(26.363,21.05) → C15.pad1(24.52,21.5)
# U4.pad7(CHRG)(23.975,21.865)を避けるため U5→右迂回→C15
# 経路: (26.363,21.05)→(25.5,21.05)→(25.5,21.5)→(24.52,21.5)
# U4.pad8(23.975,20.595)とU4.pad7(23.975,21.865)の右(x=24.62)をクリア
new_segs += [
    make_seg(26.363, 21.05, 25.5, 21.05, 0.3, 'F.Cu', 'VBAT_SW'),
    make_seg(25.5, 21.05, 25.5, 21.5, 0.3, 'F.Cu', 'VBAT_SW'),
    make_seg(25.5, 21.5, 24.52, 21.5, 0.3, 'F.Cu', 'VBAT_SW'),
]

insert_all = '\n' + '\n'.join(new_segs)
content = content.replace(insert_mark, insert_all + insert_mark, 1)
changes.append(f'配線セグメント追加: {len(new_segs)}本')

# ======================================================
# 3. I2C crossing修正: SDA縦 x=13.65 → x=15.5
# ======================================================
old_sda_horiz = '\t(segment\n\t\t(start 9.25 27)\n\t\t(end 13.65 27)\n\t\t(width 0.2)\n\t\t(layer "F.Cu")\n\t\t(net "I2C_SDA")'
old_sda_vert  = '\t(segment\n\t\t(start 13.65 27)\n\t\t(end 13.65 23.4)\n\t\t(width 0.2)\n\t\t(layer "F.Cu")\n\t\t(net "I2C_SDA")'

if old_sda_horiz in content:
    pat = re.escape(old_sda_horiz) + r'[^\)]*\)'
    content = re.sub(pat, make_seg(9.25,27,15.5,27,0.2,'F.Cu','I2C_SDA'), content, count=1)
    changes.append('SDA横 13.65→15.5')
if old_sda_vert in content:
    pat = re.escape(old_sda_vert) + r'[^\)]*\)'
    content = re.sub(pat, make_seg(15.5,27,15.5,23.4,0.2,'F.Cu','I2C_SDA'), content, count=1)
    changes.append('SDA縦 15.5へ変更')
# SDA補完: (15.5,23.4)→(13.65,23.4)
content = content.replace(insert_mark,
    '\n' + make_seg(15.5,23.4,13.65,23.4,0.2,'F.Cu','I2C_SDA') + insert_mark, 1)
changes.append('SDA接続補完セグメント追加')

# ======================================================
# 4. C14/C15 フットプリント追加
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

content = content.rstrip()
if content.endswith(')'):
    content = content[:-1] + make_cap_0402('C14',25.5,8.0,'VBAT_SW','GND') + '\n' + make_cap_0402('C15',25.0,21.5,'VBAT_SW','GND') + '\n)'
    changes.append('C14/C15フットプリント追加')

# ======================================================
# 5. ANT3移動: (1.8,19) → (2.2,19)、pad1 edge=0.9mm確保
# ======================================================
content = content.replace('(at 1.8 19)\n', '(at 2.2 19)\n')
changes.append('ANT3 (1.8,19)→(2.2,19) 移動')

old_wifi1 = '\t(segment\n\t\t(start 5.8 20.87)\n\t\t(end 0.5 20.87)\n\t\t(width 0.2)\n\t\t(layer "F.Cu")\n\t\t(net "WIFI_ANT")'
old_wifi2 = '\t(segment\n\t\t(start 0.5 20.87)\n\t\t(end 0.5 19)\n\t\t(width 0.2)\n\t\t(layer "F.Cu")\n\t\t(net "WIFI_ANT")'
if old_wifi1 in content:
    pat = re.escape(old_wifi1) + r'[^\)]*\)'
    content = re.sub(pat, make_seg(5.8,20.87,0.9,20.87,0.2,'F.Cu','WIFI_ANT'), content, count=1)
    changes.append('WIFI_ANT横→0.9')
if old_wifi2 in content:
    pat = re.escape(old_wifi2) + r'[^\)]*\)'
    content = re.sub(pat, make_seg(0.9,20.87,0.9,19.0,0.2,'F.Cu','WIFI_ANT'), content, count=1)
    changes.append('WIFI_ANT縦→0.9')

with open(PCB, 'w') as f:
    f.write(content)

print(f'修正完了 ({len(changes)}件):')
for c in changes:
    print(f'  ✓ {c}')
