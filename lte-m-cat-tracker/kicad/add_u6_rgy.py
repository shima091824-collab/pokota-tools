#!/usr/bin/env python3
"""
レベルシフタ U6 (TXB0104RGYR, VQFN-14 RGY) + C18/C19 を追加し、UART/STATUSを電圧ドメイン分割

ランドパターン根拠（一次情報・2026-06-12確認）:
- TI データシート RGY0014A LAND PATTERN EXAMPLE: サイドパッド14X 0.24x0.6・ピッチ8X 0.5・
  外形スパン3.3・上下辺ピンオフセット±0.775・EP(2.05)
- EasyEDA C400708 実座標で照合: ピッチ0.5/EP 2.05x2.05/配列一致を確認済み
- ピン番号: 1=VCCA(上左) 2-6=A1-A4,NC(左上→下) 7=GND(下左) 8=OE(下右)
  9,10=NC,B4(右下→) 11-13=B3-B1(右) 14=VCCB(上右) 15=EP

配置: U6=(2.6,9.9) / C18,C19=U6直下 / C12を(2.5,13.0)→(2.5,14.5)へ移動して場所確保
ネット: 既存スクリプト同様 U2側を_33ネットへ付替・U2 pad6のSIM_RESETN撤去
"""
import re, sys

PCB = 'lte-m-cat-tracker.kicad_pcb'
U6X, U6Y = 2.6, 10.1

# (番号, x, y, w, h, net)  サイドパッドは横長0.6x0.24、上下辺は縦長0.24x0.6
PADS = [
    ('1',  -0.775, -1.35, 0.24, 0.60, 'VDD_EXT'),
    ('2',  -1.35,  -1.00, 0.60, 0.24, 'SIM_TXD'),
    ('3',  -1.35,  -0.50, 0.60, 0.24, 'SIM_RXD'),
    ('4',  -1.35,   0.00, 0.60, 0.24, 'SIM_STATUS'),
    ('5',  -1.35,   0.50, 0.60, 0.24, None),
    ('6',  -1.35,   1.00, 0.60, 0.24, None),
    ('7',  -0.775,  1.35, 0.24, 0.60, 'GND'),
    ('8',   0.775,  1.35, 0.24, 0.60, 'VDD_EXT'),   # OE→VCCA直結
    ('9',   1.35,   1.00, 0.60, 0.24, None),
    ('10',  1.35,   0.50, 0.60, 0.24, None),
    ('11',  1.35,   0.00, 0.60, 0.24, 'SIM_STATUS_33'),
    ('12',  1.35,  -0.50, 0.60, 0.24, 'SIM_RXD_33'),
    ('13',  1.35,  -1.00, 0.60, 0.24, 'SIM_TXD_33'),
    ('14',  0.775, -1.35, 0.24, 0.60, '+3.3V'),
    ('15',  0.0,    0.00, 1.70, 1.70, 'GND'),        # EP: 1.7に縮小(TI2.05だと隣接パッド間隙0.025<JLCPCB0.127で製造不可・GND接続=TIノートB準拠)
]
U2_RENAME = {'27': 'SIM_TXD_33', '28': 'SIM_RXD_33', '4': 'SIM_STATUS_33', '6': None}
CAPS = [('C18', 'VDD_EXT', 2.9, 12.8), ('C19', '+3.3V', 2.9, 13.9)]
C12_NEW = (2.5, 15.4)


def fp_u6():
    p = [f'\t(footprint "lte-m-custom:TXB0104_RGY14"',
         '\t\t(layer "F.Cu")',
         f'\t\t(at {U6X} {U6Y})',
         '\t\t(property "Reference" "U6" (at 0 -2.8 0) (layer "F.SilkS") (effects (font (size 0.7 0.7) (thickness 0.12))))',
         '\t\t(property "Value" "TXB0104RGYR" (at 0 2.8 0) (layer "F.Fab") (effects (font (size 0.7 0.7) (thickness 0.12))))',
         '\t\t(attr smd)',
         # courtyard
         '\t\t(fp_rect (start -2.05 -2.05) (end 2.05 2.05) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))',
         # silk: pin1マーク
         '\t\t(fp_circle (center -1.9 -1.9) (end -1.8 -1.9) (stroke (width 0.15) (type default)) (fill none) (layer "F.SilkS"))']
    for n, x, y, w, h, net in PADS:
        pt = 'smd rect'
        netl = f'\n\t\t\t(net "{net}")' if net else ''
        p.append(f'\t\t(pad "{n}" {pt}\n\t\t\t(at {x} {y})\n\t\t\t(size {w} {h})\n\t\t\t(layers "F.Cu" "F.Mask" "F.Paste"){netl}\n\t\t)')
    p.append('\t)')
    return '\n'.join(p) + '\n'


def fp_cap(ref, net, x, y):
    # C_0402_1005Metric 相当: pads 0.59x0.64 at ±0.485（KiCad公式寸法）
    p = [f'\t(footprint "lte-m-custom:C_0402"',
         '\t\t(layer "F.Cu")',
         f'\t\t(at {x} {y})',
         f'\t\t(property "Reference" "{ref}" (at 0 -1.1 0) (layer "F.SilkS") (effects (font (size 0.6 0.6) (thickness 0.1))))',
         '\t\t(property "Value" "100nF" (at 0 1.1 0) (layer "F.Fab") (effects (font (size 0.6 0.6) (thickness 0.1))))',
         '\t\t(attr smd)',
         '\t\t(fp_rect (start -0.93 -0.47) (end 0.93 0.47) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))',
         f'\t\t(pad "1" smd roundrect\n\t\t\t(at -0.485 0)\n\t\t\t(size 0.59 0.64)\n\t\t\t(layers "F.Cu" "F.Mask" "F.Paste")\n\t\t\t(roundrect_rratio 0.25)\n\t\t\t(net "{net}")\n\t\t)',
         '\t\t(pad "2" smd roundrect\n\t\t\t(at 0.485 0)\n\t\t\t(size 0.59 0.64)\n\t\t\t(layers "F.Cu" "F.Mask" "F.Paste")\n\t\t\t(roundrect_rratio 0.25)\n\t\t\t(net "GND")\n\t\t)',
         '\t)']
    return '\n'.join(p) + '\n'


lines = open(PCB).readlines()
if any('"Reference" "U6"' in l for l in lines):
    sys.exit('U6 already present; abort')

starts = [i for i, l in enumerate(lines) if l.strip().startswith('(footprint')]

def block_range(ref):
    r = next(i for i, l in enumerate(lines) if f'"Reference" "{ref}"' in l)
    bs = max(i for i in starts if i < r)
    be = min((i for i in starts if i > r), default=len(lines))
    return bs, be

log = []

# --- C12 移動 ---
bs, be = block_range('C12')
for i in range(bs, min(bs + 6, be)):
    m = re.match(r'(\s*)\(at ([\d.-]+) ([\d.-]+)((?: [\d.-]+)?)\)\s*$', lines[i])
    if m:
        lines[i] = f'{m.group(1)}(at {C12_NEW[0]} {C12_NEW[1]}{m.group(4)})\n'
        log.append(f'C12 moved ({m.group(2)},{m.group(3)}) -> {C12_NEW}')
        break

# --- U2 ネット付替（パッドブロック厳密走査） ---
bs, be = block_range('U2')
i = bs
while i < be:
    m = re.match(r'\s*\(pad "(\d+)" ', lines[i])
    if m and m.group(1) in U2_RENAME:
        new = U2_RENAME[m.group(1)]
        j = i + 1
        while j < be and not re.match(r'\t\t\)\s*$', lines[j]):
            nm = re.match(r'(\s*)\(net "([^"]+)"\)', lines[j])
            if nm:
                if new is None:
                    del lines[j]
                    be -= 1
                    j -= 1
                    log.append(f'U2 pad{m.group(1)}: {nm.group(2)} -> (none)')
                else:
                    lines[j] = f'{nm.group(1)}(net "{new}")\n'
                    log.append(f'U2 pad{m.group(1)}: {nm.group(2)} -> {new}')
                break
            j += 1
    i += 1

# --- C12旧位置周辺のVBAT_SW/GNDセグメントはそのまま（再配線フェーズで処理） ---

# --- 挿入 ---
blocks = [fp_u6()] + [fp_cap(*c[0:2], c[2], c[3]) for c in CAPS]
last = max(i for i, l in enumerate(lines) if l.strip() == ')')
lines[last:last] = blocks

open(PCB, 'w').writelines(lines)
print('\n'.join(log))
print('U6/C18/C19 inserted')
