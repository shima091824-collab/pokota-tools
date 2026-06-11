#!/usr/bin/env python3
"""
レベルシフタ U6 (TXB0104PWR) + パスコン C18/C19 を追加し、UART/STATUSを電圧ドメイン分割する

根拠:
- TXB0104 データシート(SCES650F) PWパッケージ: 1=VCCA 2=A1 3=A2 4=A3 5=A4 6=NC 7=GND
  8=OE 9=NC 10=B4 11=B3 12=B2 13=B1 14=VCCB / VCCA≤VCCB / OEはVCCA基準
- フットプリント: KiCad公式 TSSOP-14_4.4x5mm_P0.65mm（TI PW=4.4x5.0mm 0.65mmピッチと一致確認済み）
- VCCA=VDD_EXT(1.8V, U1 pad40) / VCCB=+3.3V / OE→VCCA直結（モデムOFF時に自動Hi-Z）

ネット分割:
- 1.8V側(U1側): SIM_TXD, SIM_RXD, SIM_STATUS（既存名を維持）
- 3.3V側(U2側): SIM_TXD_33, SIM_RXD_33, SIM_STATUS_33（U2のパッドを付替）
- U2 pad6 の SIM_RESETN は撤去（GPIO解放）
"""
import re, sys

PCB = 'lte-m-cat-tracker.kicad_pcb'
LIB = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'

U6_POS = (float(sys.argv[1]), float(sys.argv[2])) if len(sys.argv) > 3 else (3.0, 12.0)
U6_ROT = int(sys.argv[3]) if len(sys.argv) > 3 else 90

U6_NETS = {'1': 'VDD_EXT', '2': 'SIM_TXD', '3': 'SIM_RXD', '4': 'SIM_STATUS',
           '7': 'GND', '8': 'VDD_EXT',
           '11': 'SIM_STATUS_33', '12': 'SIM_RXD_33', '13': 'SIM_TXD_33', '14': '+3.3V'}
U2_RENAME = {'27': 'SIM_TXD_33', '28': 'SIM_RXD_33', '4': 'SIM_STATUS_33', '6': None}

CAPS = [  # (ref, net+, x, y) GNDはpad2
    ('C18', 'VDD_EXT', U6_POS[0], U6_POS[1] - 4.5),
    ('C19', '+3.3V',   U6_POS[0], U6_POS[1] + 4.5),
]


def load_fp(path, ref, value, pos, rot, nets):
    src = open(path).read()
    # 外殻の (footprint "name" を (footprint "name" のままインライン化し、(at)とプロパティを差し込む
    src = re.sub(r'\(version \d+\)\s*', '', src)
    src = re.sub(r'\(generator "[^"]*"\)\s*', '', src)
    src = src.replace('REF**', ref, 1)
    # Value プロパティを書き換え
    src = re.sub(r'(\(property "Value" ")[^"]*(")', r'\g<1>' + value + r'\g<2>', src, count=1)
    # (layer "F.Cu") の直後に (at x y rot) を挿入
    src = src.replace('(layer "F.Cu")', f'(layer "F.Cu")\n\t(at {pos[0]} {pos[1]} {rot})', 1)
    # 各パッドにネットを付与し、(at x y) を (at x y rot) に
    out = []
    for line in src.split('\n'):
        m = re.match(r'(\s*)\(pad "([^"]+)" smd', line)
        out.append(line)
        if m and m.group(2) in nets:
            out.append(f'{m.group(1)}\t(net "{nets[m.group(2)]}")')
    src = '\n'.join(out)
    if rot:
        src = re.sub(r'(\(pad "[^"]+" smd \w+\s*\n\s*\(at [-\d. ]+)\)',
                     r'\g<1> ' + str(rot) + ')', src)
    # インデントをタブ1段下げ
    return '\t' + src.replace('\n', '\n\t').rstrip('\t')


lines = open(PCB).readlines()
text = ''.join(lines)
if '"Reference" "U6"' in text:
    sys.exit('U6 already present; abort')

# --- U2のネット付替 ---
starts = [i for i, l in enumerate(lines) if l.strip().startswith('(footprint')]
u2 = next(i for i, l in enumerate(lines) if '"Reference" "U2"' in l)
bs = max(i for i in starts if i < u2)
be = min((i for i in starts if i > u2), default=len(lines))
i = bs
log = []
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
                    log.append(f'U2 pad{m.group(1)}: {nm.group(2)} -> (none)')
                    j -= 1
                else:
                    lines[j] = f'{nm.group(1)}(net "{new}")\n'
                    log.append(f'U2 pad{m.group(1)}: {nm.group(2)} -> {new}')
                break
            j += 1
        i = j
    i += 1

# --- U6 + C18/C19 を末尾の閉じ括弧前に挿入 ---
blocks = [load_fp(f'{LIB}/Package_SO.pretty/TSSOP-14_4.4x5mm_P0.65mm.kicad_mod',
                  'U6', 'TXB0104PWR', U6_POS, U6_ROT, U6_NETS)]
for ref, netp, x, y in CAPS:
    blocks.append(load_fp(f'{LIB}/Capacitor_SMD.pretty/C_0402_1005Metric.kicad_mod',
                          ref, '100nF', (x, y), 0, {'1': netp, '2': 'GND'}))

# ファイル末尾の最後の ')' の前に挿入
last = max(i for i, l in enumerate(lines) if l.strip() == ')')
lines[last:last] = [b + '\n' for b in blocks]

open(PCB, 'w').writelines(lines)
print('\n'.join(log))
print(f'U6 placed at {U6_POS} rot{U6_ROT}, C18/C19 added')
