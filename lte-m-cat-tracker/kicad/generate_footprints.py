#!/usr/bin/env python3
"""
LTE-M 猫GPSトラッカー カスタムフットプリント生成スクリプト
出力先: kicad/lte-m-custom.pretty/

作成するフットプリント:
  1. SIM7080GM_LCC77   - SIM7080G-M LCC+LGA 77pin (17.6×15.7mm)
  2. SIM_SMN-305       - nano SIM ホルダー (XUNPU SMN-305)
  3. SW_MSK12C02       - 電源スライドスイッチ
  4. ChipAntenna_2x1.25mm - 2.4GHz チップアンテナ
  5. USB_C_GCT_16P     - USB-C 16pin SMD receptacle

⚠️ SIM7080G-Mは発注前にHardware Design v1.02で必ずパッド座標を確認する
"""

import uuid, math, os

OUT_DIR = "/Users/m2mac/lte-m-cat-tracker/kicad/lte-m-custom.pretty"
os.makedirs(OUT_DIR, exist_ok=True)

def uu(): return str(uuid.uuid4())

def mod_header(name, descr, tags, layer="F.Cu"):
    return f'''(footprint "{name}"
  (version 20241012)
  (generator "custom_script")
  (generator_version "1.0")
  (layer "{layer}")
  (descr "{descr}")
  (tags "{tags}")
  (attr smd)
'''

def pad_smd(num, x, y, w, h, angle=0, layers='"F.Cu" "F.Paste" "F.Mask"', shape="rect"):
    return f'''  (pad "{num}" smd {shape}
    (at {x:.4f} {y:.4f}{f" {angle}" if angle else ""})
    (size {w:.4f} {h:.4f})
    (layers {layers})
    (uuid "{uu()}")
  )'''

def courtyard(x1, y1, x2, y2, layer="F.CrtYd", w=0.05):
    return f'''  (fp_rect
    (start {x1:.4f} {y1:.4f})
    (end {x2:.4f} {y2:.4f})
    (stroke (width {w}) (type default))
    (fill no)
    (layer "{layer}")
    (uuid "{uu()}")
  )'''

def fab_rect(x1, y1, x2, y2, w=0.1):
    return courtyard(x1, y1, x2, y2, "F.Fab", w)

def silk_line(x1, y1, x2, y2, w=0.12):
    return f'''  (fp_line
    (start {x1:.4f} {y1:.4f}) (end {x2:.4f} {y2:.4f})
    (stroke (width {w}) (type default))
    (layer "F.SilkS")
    (uuid "{uu()}")
  )'''

def ref_text(x, y, a=0):
    return f'''  (fp_text reference "REF**"
    (at {x:.4f} {y:.4f} {a})
    (layer "F.SilkS")
    (uuid "{uu()}")
    (effects (font (size 1 1) (thickness 0.15)))
  )'''

def val_text(x, y):
    return f'''  (fp_text value "VAL**"
    (at {x:.4f} {y:.4f})
    (layer "F.Fab")
    (uuid "{uu()}")
    (effects (font (size 1 1) (thickness 0.15)))
  )'''

# ═══════════════════════════════════════════════════════════════
# 1. SIM7080G-M LCC+LGA 77pin
# ═══════════════════════════════════════════════════════════════
def make_sim7080g():
    """
    SIM7080G-M パッケージ: LCC+LGA 77pin
    モジュール外形: 17.6 × 15.7 mm

    ⚠️ パッド座標はHW Design v1.02の実寸で確認必須
    以下はSIMCom標準LCCパッケージの一般的な配置に基づく近似値

    ピン配置（推定）:
    - 右辺(1-9): 短辺方向、ピッチ1.8mm
    - 上辺(10-16): 長辺方向、ピッチ2.3mm
    - 左辺(17-25): 短辺方向、ピッチ1.8mm
    - 下辺(26-32): 長辺方向、ピッチ2.3mm
    - LGAパッド(33-77): 内部グリッド
    """
    W = 17.60   # モジュール幅
    H = 15.70   # モジュール高さ

    # LCCパッド寸法（SIMCom標準）
    PAD_SIDE_W = 1.00   # 短辺パッド幅（X方向）
    PAD_SIDE_H = 1.50   # 短辺パッド高さ（Y方向）

    # 外縁からランド中心までのオフセット（カステレーション）
    # 基板エッジ内に0.3mm + 外側に0.65mm のランド
    OUTER = 0.55   # モジュール外縁からのランド中心

    lines = [mod_header("SIM7080GM_LCC77",
                        "SIM7080G-M LTE-M+GNSS module, LCC+LGA-77, 17.6x15.7mm. "
                        "VERIFY PAD COORDS AGAINST HW DESIGN v1.02 BEFORE ORDERING!",
                        "SIM7080G SIMCom LTE-M GNSS cellular")]
    lines.append(ref_text(0, -9.5))
    lines.append(val_text(0, 9.5))

    # F.Fab アウトライン（モジュール本体）
    lines.append(fab_rect(-W/2, -H/2, W/2, H/2))

    # F.Courtyard（実装余裕 0.5mm）
    lines.append(courtyard(-W/2-0.5, -H/2-0.5, W/2+0.5, H/2+0.5))

    # F.SilkS アウトライン（モジュール外形）
    lines.append(silk_line(-W/2, -H/2, W/2, -H/2))
    lines.append(silk_line(W/2, -H/2, W/2, H/2))
    lines.append(silk_line(W/2, H/2, -W/2, H/2))
    lines.append(silk_line(-W/2, H/2, -W/2, -H/2))
    # ピン1マーカー（右下隅）
    lines.append(silk_line(W/2-1.5, H/2, W/2, H/2-1.5))

    pad_num = 1

    # ─── 右辺 (East): パッド1-9, y方向 ───
    # 右辺: 9パッド、中心y=-7.20〜+7.20、ピッチ1.80mm
    # ランドはモジュール外縁（x=W/2）の外側に突き出す
    rx = W/2 + OUTER
    right_pads_y = [-7.20 + i*1.80 for i in range(9)]
    for y in right_pads_y:
        lines.append(pad_smd(pad_num, rx, y, PAD_SIDE_H, PAD_SIDE_W))
        pad_num += 1

    # ─── 上辺 (North): パッド10-16, x方向 ───
    # 上辺: 7パッド（y=-H/2の外側）
    ty = -(H/2 + OUTER)
    # 上辺パッド: x=+7.0〜-7.0, ピッチ=2.33mm
    top_pads_x = [7.00 - i*2.33 for i in range(7)]
    for x in top_pads_x:
        lines.append(pad_smd(pad_num, x, ty, PAD_SIDE_W, PAD_SIDE_H))
        pad_num += 1

    # ─── 左辺 (West): パッド17-25, y方向 ───
    lx = -(W/2 + OUTER)
    left_pads_y = [7.20 - i*1.80 for i in range(9)]
    for y in left_pads_y:
        lines.append(pad_smd(pad_num, lx, y, PAD_SIDE_H, PAD_SIDE_W))
        pad_num += 1

    # ─── 下辺 (South): パッド26-32, x方向 ───
    by = H/2 + OUTER
    bot_pads_x = [-7.00 + i*2.33 for i in range(7)]
    for x in bot_pads_x:
        lines.append(pad_smd(pad_num, x, by, PAD_SIDE_W, PAD_SIDE_H))
        pad_num += 1

    # ─── LGAパッド (33-77): 内部グリッド ───
    # LGAパッドは底面、内部グリッド配置
    # 推定: 5x9 = 45パッド（行×列）で45パッドが内部
    # 実際は77-32=45パッドが内部LGA
    LGA_PAD_W = 0.80
    LGA_PAD_H = 0.80
    # グリッド: X方向5列、Y方向9行
    # X: -4.8〜+4.8 (ピッチ2.4mm), Y: -7.2〜+7.2 (ピッチ1.8mm)
    lga_num = 33
    for row in range(9):  # Y: -7.2〜+7.2
        y = -7.20 + row*1.80
        for col in range(5):  # X: -4.8〜+4.8
            x = -4.80 + col*2.40
            lines.append(pad_smd(lga_num, x, y, LGA_PAD_W, LGA_PAD_H))
            lga_num += 1

    print(f"SIM7080G-M: {lga_num-1}パッド生成 (目標77)")
    lines.append(")")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# 2. SMN-305 nano SIM ホルダー (XUNPU)
# ═══════════════════════════════════════════════════════════════
def make_smn305():
    """
    XUNPU SMN-305 nano SIM ホルダー (フリップ型)
    全体サイズ: ~12.5 × 11.0mm
    nano SIM: 12.3 × 8.8mm

    パッド配置（典型的なnano SIMホルダー）:
    - 接点パッド: 6個（SIMの6接点に対応）
    - 機械的固定: 4個
    """
    lines = [mod_header("SIM_SMN-305",
                        "XUNPU SMN-305 Nano SIM card holder, SMD flip type",
                        "SIM nano SIM holder SMN-305")]
    lines.append(ref_text(0, -7.0))
    lines.append(val_text(0, 7.0))

    # 接点パッド寸法
    CP_W = 1.10  # 接点パッド幅
    CP_H = 1.50  # 接点パッド高さ

    # nano SIM接点は6個: 2行×3列
    # VCC, CLK, RST / GND, DATA, NC の典型配置
    # 参考: nano SIM ISO 7816-3 接触配置
    # C1(VCC), C2(RST), C3(CLK) / C5(GND), C6(VPP), C7(DATA)

    # 接点パッドのX座標（ピッチ 2.54mm, 3列）
    cx_list = [-2.54, 0, 2.54]
    # 接点パッドのY座標（上下2行, ピッチ 2.54mm）
    cy_upper = -2.00   # 上行（VCC, RST, CLK）
    cy_lower =  0.54   # 下行（GND, VPP, DATA）

    # 上行: VCC(1), DATA(2), CLK(3)... 実際はSMN-305データシート確認
    contact_pads = [
        (1, cx_list[0], cy_upper, "VCC"),
        (2, cx_list[1], cy_upper, "DATA"),
        (3, cx_list[2], cy_upper, "CLK"),
        (4, cx_list[0], cy_lower, "RST"),
        (5, cx_list[2], cy_lower, "GND"),
        (6, -5.80,       0.00,    "CD"),   # カード検出（右側）
    ]
    for num, x, y, name in contact_pads:
        lines.append(pad_smd(num, x, y, CP_W, CP_H))

    # 機械的固定パッド（4隅）
    MT_W = 1.20
    MT_H = 1.80
    mount_pads = [
        (-4.80, -3.20), (4.80, -3.20),  # 上側
        (-4.80,  2.40), (4.80,  2.40),  # 下側
    ]
    for i, (mx, my) in enumerate(mount_pads):
        lines.append(f'''  (pad "" smd rect
    (at {mx:.4f} {my:.4f})
    (size {MT_W} {MT_H})
    (layers "F.Cu" "F.Paste" "F.Mask")
    (uuid "{uu()}")
  )''')

    # アウトライン
    lines.append(fab_rect(-6.25, -4.40, 6.25, 3.50))
    lines.append(courtyard(-6.40, -4.60, 6.40, 3.70))
    # SilkS: カード挿入方向の矢印
    lines.append(silk_line(-5.50, -4.20, 5.50, -4.20))
    lines.append(silk_line(-5.50, -4.20, -5.50, 3.30))
    lines.append(silk_line( 5.50, -4.20,  5.50, 3.30))
    lines.append(")")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# 3. MSK12C02 電源スライドスイッチ
# ═══════════════════════════════════════════════════════════════
def make_msk12c02():
    """
    MSK12C02 電源スライドスイッチ
    外形: 8.5 × 3.6 × 1.8mm
    ピン配置: 3+3 (左右対称), ピッチ1.9mm
    端子ピッチ（長辺方向）: 2.5mm
    """
    lines = [mod_header("SW_MSK12C02",
                        "MSK12C02 slide switch, SMD",
                        "switch slide SPDT MSK12C02")]
    lines.append(ref_text(0, -3.5))
    lines.append(val_text(0, 3.5))

    # パッド寸法
    PW = 0.80
    PH = 1.20

    # パッド配置
    # 左側3パッド: x=-2.5, y=-1.9, 0, +1.9
    # 右側3パッド: x=+2.5, y=-1.9, 0, +1.9
    # ※ MSK12C02はSPDTなので実際は2×3または3×2
    # 標準配置: 左3端子(A,COM,B), 右3端子(機械固定)
    pad_defs = [
        # ピン番号, x, y
        (1,  -2.50, -1.90),  # A
        (2,  -2.50,  0.00),  # COM
        (3,  -2.50,  1.90),  # B (NC or GND)
    ]
    for num, x, y in pad_defs:
        lines.append(pad_smd(num, x, y, PW, PH))

    # 機械固定パッド（右側）
    mount_defs = [
        (2.50, -1.90),
        (2.50,  0.00),
        (2.50,  1.90),
    ]
    for mx, my in mount_defs:
        lines.append(f'''  (pad "" smd rect
    (at {mx:.4f} {my:.4f})
    (size {PW} {PH})
    (layers "F.Cu" "F.Paste" "F.Mask")
    (uuid "{uu()}")
  )''')

    # アウトライン（本体: 8.5×3.6mm）
    BW, BH = 8.50, 3.60
    lines.append(fab_rect(-BW/2, -BH/2, BW/2, BH/2))
    lines.append(courtyard(-BW/2-0.25, -BH/2-0.25, BW/2+0.25, BH/2+0.25))
    lines.append(silk_line(-BW/2, -BH/2, BW/2, -BH/2))
    lines.append(silk_line(-BW/2,  BH/2, BW/2,  BH/2))
    lines.append(silk_line(-BW/2, -BH/2, -BW/2, BH/2))
    lines.append(")")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# 4. チップアンテナ 2.4GHz (2×1.25mm)
# ═══════════════════════════════════════════════════════════════
def make_chip_antenna():
    """
    Murata 2450AT18A100 / 2450AT42A100 などの
    2.4GHz チップアンテナ 2×1.25mm
    パッドピッチ: 2.0mm（パッド中心間）
    """
    lines = [mod_header("ChipAntenna_2x1.25mm",
                        "2.4GHz chip antenna 2.0x1.25mm, e.g. Murata 2450AT18A100",
                        "antenna chip 2.4GHz WiFi BLE")]
    lines.append(ref_text(0, -1.5))
    lines.append(val_text(0, 1.5))

    # パッド: 2個、中心間距離1.0mm (2mm幅チップのパッドは中心から±0.5mm外側)
    # ランドパッド: 0.8 × 1.25mm
    PW, PH = 0.80, 1.25
    GAP = 1.00   # パッド中心間距離

    lines.append(pad_smd(1, -GAP/2, 0, PW, PH))   # RF端子
    lines.append(pad_smd(2,  GAP/2, 0, PW, PH))   # GND端子

    # アウトライン
    lines.append(fab_rect(-1.00, -0.625, 1.00, 0.625))
    lines.append(courtyard(-1.20, -0.80, 1.20, 0.80))
    lines.append(silk_line(-0.20, -0.60, -0.20, 0.60))  # 区切り線
    lines.append(")")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# 5. USB-C SMD 16pin receptacle
# ═══════════════════════════════════════════════════════════════
def make_usbc():
    """
    USB-C 16P SMD レセプタクル (C2765186 相当)
    GCT USB4085シリーズ互換サイズ
    外形: 9.0 × 3.4mm
    パッド: 上下各8ピン + シェルド4個
    """
    lines = [mod_header("USB_C_16P_SMD",
                        "USB-C 16P SMD receptacle, GCT USB4085/USB4135 compatible",
                        "USB-C USB Type-C receptacle 16P")]
    lines.append(ref_text(0, -3.5))
    lines.append(val_text(0, 3.5))

    # USB-C 16ピン配列（LCSC C2765186標準）
    # 信号ピン: 上下各8ピン、ピッチ0.5mm
    # 上辺ピン（A列）: y=-1.7mm
    # 下辺ピン（B列）: y=+1.7mm
    PITCH = 0.50
    SIGNAL_Y = 1.70
    PW, PH = 0.30, 0.80

    # 信号ピン（中心付近8本×2列）
    # A列（上辺, y=-SIGNAL_Y）: A1(GND), A4(VBUS), A5(CC1), A6(D+), A7(D-), A8(SBU1)...
    # USB-C 16P pinout:
    pins_A = ['A1', 'A4', 'A5', 'A6', 'A7', 'A8', 'B11', 'B12']  # 上辺8本
    pins_B = ['B1', 'B4', 'B5', 'B6', 'B7', 'B8', 'A11', 'A12']  # 下辺8本

    # x座標: 8ピン、0.5mmピッチ、中心は-1.75〜+1.75mm
    xs = [-1.75 + i*0.50 for i in range(8)]

    pad_map = {
        'A1':'A1', 'A4':'A4', 'A5':'A5', 'A6':'A6',
        'A7':'A7', 'A8':'A8', 'B11':'B11', 'B12':'B12',
        'B1':'B1', 'B4':'B4', 'B5':'B5', 'B6':'B6',
        'B7':'B7', 'B8':'B8', 'A11':'A11', 'A12':'A12',
    }

    for i, (pin, x) in enumerate(zip(pins_A, xs)):
        lines.append(pad_smd(pin, x, -SIGNAL_Y, PW, PH))
    for i, (pin, x) in enumerate(zip(pins_B, xs)):
        lines.append(pad_smd(pin, x,  SIGNAL_Y, PW, PH))

    # シールドパッド（4隅）
    SH_W, SH_H = 2.40, 1.20
    for sx, sy in [(-3.50, -1.60), (3.50, -1.60),
                   (-3.50,  1.60), (3.50,  1.60)]:
        lines.append(f'''  (pad "S" smd rect
    (at {sx:.4f} {sy:.4f})
    (size {SH_W} {SH_H})
    (layers "F.Cu" "F.Paste" "F.Mask")
    (uuid "{uu()}")
  )''')

    # アウトライン
    BW, BH = 9.00, 3.40
    lines.append(fab_rect(-BW/2, -BH/2, BW/2, BH/2))
    lines.append(courtyard(-BW/2-0.3, -BH/2-0.3, BW/2+0.3, BH/2+0.3))
    lines.append(silk_line(-BW/2, -BH/2, BW/2, -BH/2))
    lines.append(silk_line(-BW/2,  BH/2, BW/2,  BH/2))
    lines.append(silk_line(-BW/2, -BH/2, -BW/2, BH/2))
    lines.append(")")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# 生成実行
# ═══════════════════════════════════════════════════════════════
footprints = {
    "SIM7080GM_LCC77.kicad_mod": make_sim7080g,
    "SIM_SMN-305.kicad_mod": make_smn305,
    "SW_MSK12C02.kicad_mod": make_msk12c02,
    "ChipAntenna_2x1.25mm.kicad_mod": make_chip_antenna,
    "USB_C_16P_SMD.kicad_mod": make_usbc,
}

for fname, func in footprints.items():
    content = func()
    path = os.path.join(OUT_DIR, fname)
    with open(path, "w") as f:
        f.write(content)
    print(f"✅ {fname}")

print(f"\n出力先: {OUT_DIR}")
