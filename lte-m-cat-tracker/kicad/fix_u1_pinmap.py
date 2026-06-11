#!/usr/bin/env python3
"""
U1 (SIM7080G-M) ピン割当の致命的バグ修正（2026-06-11）

根拠: EasyEDA C18548266 正式ピン表 + SIM7080G HW Design V1.03
  - AT通信はUART1（pin1=UART1_TXD, pin2=UART1_RXD）。UART2(22,23)はDAM用でAT不可
  - PWRKEY=39（現38=ADCは誤り）/ STATUS=42（現41=NETLIGHTは誤り）
  - SIM_DATA=15（現14=GPIO5は誤り）/ VDD_EXT=40（レベルシフタVCCA用に新設）
  - pad28/46/47はNC → ネット撤去（SIM_RESETN・VBAT_SW誤接続）
変更対象ネットの既存配線セグメントも削除（再配線対象）
"""
import re, sys

PCB = 'lte-m-cat-tracker.kicad_pcb'

# pad番号 → 新ネット（None=ネット撤去）
REASSIGN = {
    '1':  'SIM_TXD',     # UART1_TXD (module out)
    '2':  'SIM_RXD',     # UART1_RXD (module in)
    '22': None,          # UART2_TXD 誤接続撤去
    '23': None,          # UART2_RXD 誤接続撤去
    '39': 'SIM_PWRKEY',
    '38': None,          # ADV誤接続撤去
    '42': 'SIM_STATUS',
    '41': None,          # NETLIGHT誤接続撤去
    '15': 'SIM_DATA',
    '14': None,          # GPIO5誤接続撤去
    '40': 'VDD_EXT',     # レベルシフタVCCA電源（新設）
    '28': None,          # NC: SIM_RESETN撤去（モジュールにRESET入力なし）
    '46': None,          # NC: VBAT_SW誤接続撤去
    '47': None,          # NC: VBAT_SW誤接続撤去
}
DEAD_NETS = {'SIM_TXD', 'SIM_RXD', 'SIM_PWRKEY', 'SIM_STATUS', 'SIM_DATA', 'SIM_RESETN'}

lines = open(PCB).readlines()

# --- U1ブロック特定 ---
u1 = next(i for i, l in enumerate(lines) if '"Reference" "U1"' in l)
starts = [i for i, l in enumerate(lines) if l.strip().startswith('(footprint')]
bs = max(i for i in starts if i < u1)
be = min((i for i in starts if i > u1), default=len(lines))

# --- U1内のパッドネット付替え ---
changed = []
i = bs
while i < be:
    m = re.match(r'\s*\(pad "(\d+)" ', lines[i])
    if m and m.group(1) in REASSIGN:
        pad, new = m.group(1), REASSIGN[m.group(1)]
        # padブロック終端（インデント深さ2のタブ+閉じ括弧）を探す
        j = i + 1
        net_line = None
        while j < be and not re.match(r'\t\t\)\s*$', lines[j]):
            if re.match(r'\s*\(net "', lines[j]):
                net_line = j
            j += 1
        old = (re.search(r'\(net "([^"]+)"\)', lines[net_line]).group(1)
               if net_line is not None else '(none)')
        if new is None:
            if net_line is not None:
                del lines[net_line]
                be -= 1
        else:
            new_text = f'\t\t\t(net "{new}")\n'
            if net_line is not None:
                lines[net_line] = new_text
            else:
                lines.insert(i + 1, new_text)
                be += 1
        changed.append(f'pad{pad}: {old} -> {new or "(none)"}')
        i = j
    i += 1

# --- 変更対象ネットのsegment/via削除（全域） ---
out, i, removed = [], 0, 0
while i < len(lines):
    s = lines[i].strip()
    if s.startswith('(segment') or s.startswith('(via'):
        j = i + 1
        blk = [lines[i]]
        depth = lines[i].count('(') - lines[i].count(')')
        while j < len(lines) and depth > 0:
            blk.append(lines[j])
            depth += lines[j].count('(') - lines[j].count(')')
            j += 1
        body = ''.join(blk)
        nm = re.search(r'\(net "([^"]+)"\)', body)
        if nm and nm.group(1) in DEAD_NETS:
            removed += 1
            i = j
            continue
        out.extend(blk)
        i = j
    else:
        out.append(lines[i])
        i += 1

open(PCB, 'w').writelines(out)
print('\n'.join(changed))
print(f'segments/vias removed: {removed}')
