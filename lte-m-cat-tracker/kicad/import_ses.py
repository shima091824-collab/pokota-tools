#!/usr/bin/env python3
"""Freerouting SESを.kicad_pcbへ直接取り込む（pcbnew ImportSpecctraSESがヘッドレス不可のため）。
- 座標: SES値/10000 = mm・yは符号反転
- 対象ネットを限定し、既存セグメント/ビアと重複する形状はスキップ
使い方: python3 import_ses.py <board.ses> <board.kicad_pcb> [net1 net2 ...]
ネット指定なし = SES内全ネット
"""
import re, sys

def blocks(s, tag):
    i = 0
    while True:
        i = s.find('(' + tag, i)
        if i < 0:
            return
        # タグ名の完全一致確認（例: net vs network）
        nxt = s[i + 1 + len(tag)]
        if nxt not in ' \n\t("':
            i += 1
            continue
        depth = 0
        j = i
        while True:
            if s[j] == '(':
                depth += 1
            elif s[j] == ')':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        yield s[i:j + 1]
        i = j + 1

def main():
    ses_path, pcb_path = sys.argv[1], sys.argv[2]
    target_nets = set(sys.argv[3:])
    ses = open(ses_path).read()
    pcb = open(pcb_path).read()

    # 既存形状の収集（重複防止）
    existing_segs = set()
    for m in re.finditer(r'\(segment\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)', pcb):
        a = (round(float(m.group(1)), 3), round(float(m.group(2)), 3))
        b = (round(float(m.group(3)), 3), round(float(m.group(4)), 3))
        existing_segs.add((a, b)); existing_segs.add((b, a))
    existing_vias = set()
    for m in re.finditer(r'\(via\s*\(at ([-\d.]+) ([-\d.]+)\)', pcb):
        existing_vias.add((round(float(m.group(1)), 3), round(float(m.group(2)), 3)))

    # routes セクションのみ対象
    routes = ses[ses.find('(routes'):]
    new_segs, new_vias = [], []
    for nb in blocks(routes, 'net'):
        nm = re.match(r'\(net\s+("?)([^"\s)]+)\1', nb)
        if not nm:
            continue
        net = nm.group(2)
        if target_nets and net not in target_nets:
            continue
        for wb in blocks(nb, 'wire'):
            pm = re.search(r'\(path\s+(\S+)\s+([-\d.]+)((?:\s+[-\d.]+)+)\)', wb)
            if not pm:
                continue
            layer = pm.group(1)
            width = float(pm.group(2)) / 10000
            coords = [float(x) for x in pm.group(3).split()]
            pts = [(round(coords[i] / 10000, 4), round(-coords[i + 1] / 10000, 4))
                   for i in range(0, len(coords), 2)]
            for a, b in zip(pts, pts[1:]):
                ka = (round(a[0], 3), round(a[1], 3)); kb = (round(b[0], 3), round(b[1], 3))
                if (ka, kb) in existing_segs or ka == kb:
                    continue
                existing_segs.add((ka, kb)); existing_segs.add((kb, ka))
                new_segs.append(
                    f'\t(segment\n\t\t(start {a[0]} {a[1]})\n\t\t(end {b[0]} {b[1]})\n'
                    f'\t\t(width {width})\n\t\t(layer "{layer}")\n\t\t(net "{net}")\n\t)\n')
        for vm in re.finditer(r'\(via\s+"?([^"\s]+)"?\s+([-\d.]+)\s+([-\d.]+)\s*\)', nb):
            size_m = re.search(r'(\d+):(\d+)', vm.group(1))
            size, drill = (float(size_m.group(1)) / 1000, float(size_m.group(2)) / 1000) if size_m else (0.6, 0.3)
            x, y = round(float(vm.group(2)) / 10000, 4), round(-float(vm.group(3)) / 10000, 4)
            k = (round(x, 3), round(y, 3))
            if k in existing_vias:
                continue
            existing_vias.add(k)
            new_vias.append(
                f'\t(via\n\t\t(at {x} {y})\n\t\t(size {size})\n\t\t(drill {drill})\n'
                f'\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "{net}")\n\t)\n')

    # 挿入位置: 最後のsegmentブロックの直後
    last = pcb.rfind('(segment')
    d = 0; j = last
    while True:
        if pcb[j] == '(':
            d += 1
        elif pcb[j] == ')':
            d -= 1
            if d == 0:
                break
        j += 1
    ins = j + 2
    pcb = pcb[:ins] + ''.join(new_segs) + ''.join(new_vias) + pcb[ins:]
    open(pcb_path, 'w').write(pcb)
    print(f"取り込み: segment {len(new_segs)}本 / via {len(new_vias)}個")

if __name__ == '__main__':
    main()
