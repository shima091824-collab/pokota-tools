#!/usr/bin/env python3
"""
LTE-M 猫GPSトラッカー PCBレイアウト生成スクリプト
- ネットリストを読み込んでフットプリントを配置
- DESIGN.mdの配置ゾーン設計に従う:
    上段(y=0-18mm):  SIM7080G-M中央 + U.FL両端 + SIM1
    中段(y=18-28mm): ESP32-C3 + LIS2DW12 + TP4056 + XC6220 + 受動部品
    下段(y=28-35mm): JST + USB-C + SW1 + LED
- 板サイズ: 30×35mm  2層  0.8mm FR4
"""

import re, uuid, os, math

NETLIST = "/Users/m2mac/lte-m-cat-tracker/kicad/lte-m-cat-tracker.net"
TEMPLATE_PCB = "/Users/m2mac/gps-cat-tracker/lora-30x22-routed.kicad_pcb"
OUT = "/Users/m2mac/lte-m-cat-tracker/kicad/lte-m-cat-tracker.kicad_pcb"
FPDIR_KICAD = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"
FPDIR_CUSTOM = "/Users/m2mac/lte-m-cat-tracker/kicad/lte-m-custom.pretty"

def uu(): return str(uuid.uuid4())

# ─────────────────────────────────────────────
# 1. ネットリスト解析
# ─────────────────────────────────────────────

def parse_netlist(path):
    with open(path) as f:
        content = f.read()

    # コンポーネント
    comp_re = re.compile(
        r'\(comp\s+\(ref\s+"([^"]+)"\)\s+\(value\s+"([^"]+)"\)\s+\(footprint\s+"([^"]+)"\)',
        re.DOTALL
    )
    components = {}
    for ref, val, fp in comp_re.findall(content):
        components[ref] = {'value': val, 'footprint': fp, 'nets': {}}

    # ネット
    nets_start = content.find('\t(nets')
    nets_content = content[nets_start:]
    net_re = re.compile(r'\(net\s+\(code\s+"(\d+)"\)\s+\(name\s+"([^"]+)"\)', re.DOTALL)
    node_re = re.compile(r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)')

    positions = [m.start() for m in net_re.finditer(nets_content)]
    positions.append(len(nets_content))

    nets = {}
    for i in range(len(positions)-1):
        block = nets_content[positions[i]:positions[i+1]]
        nm = net_re.match(block)
        if nm:
            code, name = nm.group(1), nm.group(2)
            nodes = node_re.findall(block)
            nets[name] = nodes
            for ref, pin in nodes:
                if ref in components:
                    components[ref]['nets'][pin] = name

    return components, nets

# ─────────────────────────────────────────────
# 2. フットプリント読み込み
# ─────────────────────────────────────────────

def load_footprint(fp_id):
    """lib:name形式のフットプリントを読み込む"""
    lib, name = fp_id.split(':', 1)
    custom_path = os.path.join(FPDIR_CUSTOM, f"{name}.kicad_mod")
    std_path = os.path.join(FPDIR_KICAD, f"{lib}.pretty", f"{name}.kicad_mod")
    for path in [custom_path, std_path]:
        if os.path.exists(path):
            with open(path) as f:
                return f.read()
    return None

def extract_pads(fp_content):
    """フットプリントからパッド情報を抽出"""
    pad_re = re.compile(
        r'\(pad\s+"([^"]*)"\s+\w+\s+\w+\s*\(at\s+([\d.+-]+)\s+([\d.+-]+)(?:\s+[\d.+-]+)?\)\s*\(size\s+([\d.]+)\s+([\d.]+)\)',
        re.DOTALL
    )
    pads = {}
    for num, x, y, w, h in pad_re.findall(fp_content):
        if num:  # 番号付きパッドのみ
            pads[num] = {'x': float(x), 'y': float(y), 'w': float(w), 'h': float(h)}
    return pads

# ─────────────────────────────────────────────
# 3. 配置設計（DESIGN.md準拠）
# ─────────────────────────────────────────────

# PCBボードサイズ: 30×35mm
# 原点: 左上(0,0) → 右下(30,35)
# 中心: (15, 17.5)

PLACEMENTS = {
    # ─── 上段: SIM7080G-M (courtyard x=[5.7,24.3] y=[1.65,18.35]) ───
    'U1':   (15.0,  10.0, 0,  'SIM7080G-M 中央'),
    'ANT1': (28.0,  4.5,  0,  'U.FL LTE'),
    'ANT2': (28.0,  13.5, 0,  'U.FL GNSS'),
    'C11':  (2.5,   7.0,  0,  'VBAT bypass 10μF 左上'),
    'C12':  (2.5,   13.0, 0,  'VBAT bypass 10μF 左下'),

    # ─── 中段左 (y=19-27, x=0-16): ESP32-C3 + センサー ───
    # ANT3 courtyard ~x=[0.5,3.5] y=[21.25,23.75]
    'ANT3': (2.0,   22.5, 0,  'WiFi チップアンテナ'),
    # U2 ESP32-C3 courtyard ~x=[5,12] y=[20,27]
    'U2':   (8.5,   23.5, 0,  'ESP32-C3'),
    # C1-C3: x=4.2 → ANT3 x_max=3.5をクリア、U2 x_min=5未満
    'C1':   (4.2,   21.5, 0,  'ESP32 bypass'),
    'C2':   (4.2,   23.5, 0,  'ESP32 bypass'),
    'C3':   (4.2,   25.5, 0,  'ESP32 bypass'),   # y=25.5 → SW1 y_min=26.25をクリア
    # C4-C6: y=19 → U2 courtyard y_min≈20をクリア
    'C4':   (6.5,   19.0, 0,  'ESP32 bypass'),
    'C5':   (8.5,   19.0, 0,  'ESP32 bypass'),
    'C6':   (10.5,  19.0, 0,  'ESP32 bypass'),
    'R5':   (13.0,  19.5, 0,  'CHIP_EN pullup'),
    'R6':   (13.0,  21.0, 0,  'I2C SDA pullup'),
    'R7':   (16.5,  21.5, 0,  'I2C SCL pullup'),  # x=16.5 → C8(x=14.5) courtyard外
    # U3 LIS2DW12 courtyard ~x=[12,15] y=[23,26]
    'U3':   (13.5,  24.5, 0,  'LIS2DW12'),
    # C7: x=12.5 → U2 courtyard x_max≈11.5をクリア (gap=0.13mm)
    # C8: 2.0mm間隔 → パッド短絡解消
    'C7':   (12.5,  22.0, 0,  'LIS bypass'),
    'C8':   (14.5,  22.0, 0,  'LIS bypass'),

    # ─── 中段右 (y=19-27, x=17-30): TP4056 + XC6220 ───
    # U4 TP4056 SOIC-8 courtyard ~x=[18.1,24.9] y=[19.5,25.5]
    # x=21.5に移動 → U5 x_min=25.6との隙間0.7mm確保
    'U4':   (21.5,  22.5, 0,  'TP4056'),
    # U5 XC6220 SOT-23-5 courtyard ~x=[25.5,29.5] y=[20.5,23.5]
    'U5':   (27.5,  22.0, 0,  'XC6220 LDO'),
    # C9/C10: y=19.5, x=2.5mm間隔
    # U4 courtyard x_max=24.9 < C9 x_min=25.13 ✓, U5 courtyard y_min=20.7 > y_max=20.16 ✓
    'C9':   (26.0,  19.5, 0,  'XC6220 VIN bypass'),
    'C10':  (28.5,  19.5, 0,  'XC6220 VOUT bypass'),
    # R3: x=16.5 → U4 VUSB pad (x=19.025) との距離2mm確保、短絡解消
    'R3':   (16.5,  24.5, 0,  'PROG 3.3kΩ'),
    # R4/LED1: x<17.2 → SIM1 courtyard外
    'R4':   (16.0,  26.3, 0,  'LED 1kΩ'),
    'LED1': (16.0,  27.5, 0,  'Charge LED'),

    # ─── SW1 左側中段 (スライドスイッチ・左辺アクセス可) ───
    # y=28.85 → U2 courtyard y_max≈26.5をクリア(gap=0.35), J2 y_min=31をクリア(gap=0.1)
    'SW1':  (4.5,   28.85, 0, 'Power SW'),

    # ─── SIM1 右下端 (右辺からカード挿入) ───
    # courtyard x=[17.2,30.0] y=[26.7,35.0] ← ボード内に収まる
    'SIM1': (23.6,  31.3, 0,  'nano SIM'),

    # ─── 下段 (y=30-35): コネクタ・CC抵抗 ───
    # J1 JST: 左端
    'J1':   (3.5,   33.5, 0,  'JST LiPo'),
    # J2 USB-C: x=[6.7,16.3] → SIM1 x_min=17.2をクリア
    'J2':   (11.5,  33.0, 0,  'USB-C'),
    # R1/R2 CC1/CC2: 2.5mm間隔 → パッド短絡解消, SW1 x_max=9をクリア
    'R1':   (13.0,  30.5, 0,  'CC1 pulldown'),
    'R2':   (15.5,  30.5, 0,  'CC2 pulldown'),
}

# ─────────────────────────────────────────────
# 4. PCB要素生成
# ─────────────────────────────────────────────

def generate_footprint_instance(ref, comp, x, y, angle, fp_content, nets_map):
    """フットプリントインスタンスを生成（パッドにネット割り当て）"""
    value = comp['value']
    fp_id = comp['footprint']
    lib, name = fp_id.split(':', 1)

    # パッド情報抽出
    pads = extract_pads(fp_content)

    # パッドにネット割り当て
    pad_net_lines = []
    for pad_num, pad_info in pads.items():
        net_name = nets_map.get(pad_num, '')
        if net_name:
            # ネット名からスラッシュを除去（ローカルラベルは/付き）
            clean_net = net_name.lstrip('/')
            pad_net_lines.append(f'      (net "{clean_net}")')

    # フットプリントのボディ（パッド以外のグラフィックス）を抽出
    fp_body = extract_fp_graphics(fp_content)

    # パッドブロック生成
    pad_blocks = generate_pad_blocks(pads, nets_map, x, y, angle)

    # KiCad PCBフォーマット: footprintIDは空文字、名前はDescriptionプロパティに格納
    return f'''\t(footprint ""
\t\t(layer "F.Cu")
\t\t(uuid "{uu()}")
\t\t(at {x:.4f} {y:.4f}{f" {angle}" if angle else ""})
\t\t(property "Reference" "{ref}"
\t\t\t(at 0 -3.5 0)
\t\t\t(layer "F.SilkS")
\t\t\t(uuid "{uu()}")
\t\t\t(effects (font (size 0.8 0.8) (thickness 0.12)))
\t\t)
\t\t(property "Value" "{value}"
\t\t\t(at 0 3.5 0)
\t\t\t(layer "F.Fab")
\t\t\t(uuid "{uu()}")
\t\t\t(effects (font (size 0.8 0.8) (thickness 0.12)))
\t\t)
\t\t(property "Footprint" "{fp_id}"
\t\t\t(at 0 5 0)
\t\t\t(layer "F.Fab")
\t\t\t(hide yes)
\t\t\t(uuid "{uu()}")
\t\t\t(effects (font (size 0.8 0.8) (thickness 0.12)))
\t\t)
\t\t(duplicate_pad_numbers_are_jumpers no)
{fp_body}
{pad_blocks}
\t\t(embedded_fonts no)
\t)'''

def normalize_fp_content(content):
    """
    kicad_modのS式を正規化:
    - (start ...) (end ...) を別行に分離
    - 各要素を適切にインデント
    """
    import re as re2
    # (start x y) と (end x y) が同一行の場合に分離
    content = re2.sub(
        r'\(start\s+([\d.+-]+\s+[\d.+-]+)\)\s+\(end\s+([\d.+-]+\s+[\d.+-]+)\)',
        r'(start \1)\n\t\t\t(end \2)',
        content
    )
    return content

def extract_fp_graphics(fp_content):
    """フットプリントからグラフィックス要素を抽出（fp_rect, fp_line, fp_arc等）"""
    fp_content = normalize_fp_content(fp_content)
    lines = fp_content.split('\n')
    result = []
    depth = 0
    in_graphic = False
    graphic_types = ('fp_rect', 'fp_line', 'fp_arc', 'fp_circle', 'fp_poly', 'fp_text')

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # グラフィック要素の開始
        if any(line.startswith(f'({gt}') for gt in graphic_types):
            # fp_textのreferenceとvalueはスキップ（個別に生成）
            if line.startswith('(fp_text reference') or line.startswith('(fp_text value'):
                depth_skip = line.count('(') - line.count(')')
                i += 1
                while depth_skip > 0 and i < len(lines):
                    depth_skip += lines[i].count('(') - lines[i].count(')')
                    i += 1
                continue
            in_graphic = True
            depth = 0
            block = []

        if in_graphic:
            block.append('\t\t' + line)
            depth += line.count('(') - line.count(')')
            if depth <= 0 and len(block) > 1:
                result.append('\n'.join(block))
                in_graphic = False
                block = []

        i += 1
    return '\n'.join(result)

def rotate_point(px, py, angle_deg):
    """点を回転（KiCad Y-down系, CCW正）"""
    a = math.radians(angle_deg)
    return px*math.cos(a) - py*math.sin(a), px*math.sin(a) + py*math.cos(a)

def generate_pad_blocks(pads, nets_map, sx, sy, angle):
    """パッドブロックを生成（KiCad PCB形式準拠）"""
    lines = []
    for pad_num, pad_info in pads.items():
        net_name = nets_map.get(pad_num, '')
        clean_net = net_name.lstrip('/') if net_name else ''
        net_part = f'\n\t\t\t(net "{clean_net}")' if clean_net else ''
        px, py = pad_info['x'], pad_info['y']
        pw, ph = pad_info['w'], pad_info['h']
        lines.append(f'''\t\t(pad "{pad_num}" smd rect
\t\t\t(at {px:.4f} {py:.4f})
\t\t\t(size {pw:.4f} {ph:.4f})
\t\t\t(layers "F.Cu" "F.Mask" "F.Paste"){net_part}
\t\t\t(thermal_bridge_angle 45)
\t\t\t(uuid "{uu()}")
\t\t)''')
    return '\n'.join(lines)

# ─────────────────────────────────────────────
# 5. PCBファイル生成
# ─────────────────────────────────────────────

def build_pcb():
    # ネットリスト読み込み
    components, nets = parse_netlist(NETLIST)
    print(f"コンポーネント数: {len(components)}, ネット数: {len(nets)}")

    # テンプレートPCBのヘッダー取得
    with open(TEMPLATE_PCB) as f:
        template = f.read()
    cut_pos = template.find('\n\t(footprint')
    header = template[:cut_pos]

    # タイトルブロック書き換え
    import re as re2
    header = re2.sub(r'\(title "[^"]*"', '(title "LTE-M 猫GPSトラッカー")', header)
    header = re2.sub(r'\(date "[^"]*"', '(date "2026-06-05")', header)
    header = re2.sub(r'\(rev "[^"]*"', '(rev "v1.0")', header)
    header = re2.sub(r'\(company "[^"]*"', '(company "Personal")', header)
    header = header.replace('(thickness 1.6)', '(thickness 0.8)')
    # コメント行書き換え
    header = re2.sub(r'\(comment 1 "[^"]*"\)', '(comment 1 "30x35mm 2Layer 0.8mm FR4 JLCPCB PCBA")', header)
    header = re2.sub(r'\(comment 2 "[^"]*"\)', '(comment 2 "SIM7080G-M+ESP32-C3+LIS2DW12+TP4056+XC6220")', header)
    header = re2.sub(r'\(comment 3 "[^"]*"\)', '(comment 3 "⚠️SIM7080G-Mフットプリントは発注前にHW Design v1.02確認必須")', header)
    for n in range(4, 10):
        header = re2.sub(rf'\(comment {n} "[^"]*"\)', '', header)

    # ネット定義
    net_lines = '\t(net 0 "")\n'
    net_index = {}
    for i, name in enumerate(sorted(nets.keys()), 1):
        clean = name.lstrip('/')
        net_lines += f'\t(net {i} "{clean}")\n'
        net_index[name] = i
        net_index[clean] = i

    # フットプリントインスタンス生成
    fp_blocks = []
    placed = 0
    not_placed = []

    for ref, (x, y, angle, comment) in PLACEMENTS.items():
        if ref not in components:
            not_placed.append(f"{ref}(not in netlist)")
            continue

        comp = components[ref]
        fp_id = comp['footprint']
        fp_content = load_footprint(fp_id)
        if not fp_content:
            not_placed.append(f"{ref}(fp not found: {fp_id})")
            continue

        nets_map = comp['nets']  # pin→net_name
        fp_block = generate_footprint_instance(ref, comp, x, y, angle, fp_content, nets_map)
        fp_blocks.append(fp_block)
        placed += 1
        print(f"  ✅ {ref:6s} @ ({x:5.1f},{y:5.1f}) {angle:3d}° — {comment}")

    for ref in not_placed:
        print(f"  ❌ {ref}")

    # Edge.Cuts
    edge = f'''
\t(gr_rect
\t\t(start 0 0) (end 30 35)
\t\t(stroke (width 0.05) (type default))
\t\t(fill no)
\t\t(layer "Edge.Cuts")
\t\t(uuid "{uu()}")
\t)
\t(gr_text "LTE-M Cat Tracker 30x35mm"
\t\t(at 15 -2.5 0)
\t\t(layer "Dwgs.User")
\t\t(uuid "{uu()}")
\t\t(effects (font (size 0.8 0.8) (thickness 0.12)))
\t)'''

    # GNDベタゾーン（B.Cu全面）
    gnd_zone = f'''
\t(zone
\t\t(net 1)
\t\t(net_name "GND")
\t\t(layer "B.Cu")
\t\t(uuid "{uu()}")
\t\t(hatch edge 0.508)
\t\t(connect_pads (clearance 0.2))
\t\t(min_thickness 0.25)
\t\t(filled_areas_thickness no)
\t\t(fill yes (thermal_gap 0.5) (thermal_bridge_width 0.3))
\t\t(polygon
\t\t\t(pts
\t\t\t\t(xy 0 0) (xy 30 0) (xy 30 35) (xy 0 35)
\t\t\t)
\t\t)
\t)'''

    # コメント（設計ノート）
    notes = f'''
\t(gr_text "⚠️ SIM7080G-Mフットプリント: HW Design v1.02要確認"
\t\t(at 0.5 -1.5 0)
\t\t(layer "Dwgs.User")
\t\t(uuid "{uu()}")
\t\t(effects (font (size 0.6 0.6) (thickness 0.09)))
\t)
\t(gr_text "電源: 0.5mm  信号: 0.2mm  RF: 50Ω整合必要"
\t\t(at 0.5 -0.8 0)
\t\t(layer "Dwgs.User")
\t\t(uuid "{uu()}")
\t\t(effects (font (size 0.6 0.6) (thickness 0.09)))
\t)'''

    pcb = header + '\n' + net_lines + '\n' + '\n'.join(fp_blocks) + '\n' + edge + '\n' + gnd_zone + '\n' + notes + '\n)\n'

    with open(OUT, 'w') as f:
        f.write(pcb)

    print(f"\n配置完了: {placed}/{len(PLACEMENTS)}コンポーネント")
    print(f"出力: {OUT} ({len(pcb):,} bytes)")
    return placed

if __name__ == '__main__':
    build_pcb()
